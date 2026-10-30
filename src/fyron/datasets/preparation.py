"""Dataset preparation helpers for nnU-Net v2 and YOLO workflows."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence

import numpy as np
import pandas as pd
import SimpleITK as sitk

from fyron.imaging import get_dicom_series_ids, read_dicom_series, read_nifti, write_nifti

SplitName = Literal["train", "val", "test"]
CopyMode = Literal["copy", "symlink", "move"]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
NIFTI_SUFFIXES = (".nii.gz", ".nii")


def _pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError('Image conversion requires matplotlib; install "fyron[visualization]".') from exc
    return plt


def prepare_nnunetv2_dataset(
    manifest: pd.DataFrame | str | Path,
    output_dir: str | Path,
    dataset_id: int,
    dataset_name: str,
    image_col: str = "image_path",
    label_col: str = "label_path",
    case_id_col: str = "case_id",
    split_col: str = "split",
    channel_names: dict[int | str, str] | Sequence[str] | None = None,
    labels: dict[int | str, str] | None = None,
    copy_mode: CopyMode = "copy",
    overwrite: bool = False,
    validate: bool = True,
) -> pd.DataFrame:
    """Prepare an nnU-Net v2 segmentation dataset from a tabular manifest.

    The output follows the nnU-Net v2 dataset convention: images are written as
    ``case_id_0000.nii.gz`` for channel 0 and labels as ``case_id.nii.gz``.
    Training and validation rows both go into ``imagesTr``/``labelsTr``;
    test rows go into ``imagesTs`` and may omit labels.
    """

    df = _read_manifest(manifest)
    _require_columns(df, [image_col, case_id_col, split_col])
    _validate_copy_mode(copy_mode)
    case_ids = df[case_id_col].map(_sanitize_token)
    if case_ids.duplicated().any():
        raise ValueError("Case identifiers must be unique after filename sanitization.")
    channels = ({str(k): v for k, v in channel_names.items()} if isinstance(channel_names, dict)
                else {str(i): v for i, v in enumerate(channel_names or ["CT"])})
    if set(channels) != {"0"}:
        raise ValueError("This preparation helper writes exactly one channel, indexed 0.")
    if dataset_id < 0 or dataset_id > 999:
        raise ValueError("dataset_id must be between 0 and 999.")
    dataset_label = f"Dataset{int(dataset_id):03d}_{_sanitize_token(dataset_name)}"
    root = Path(output_dir) / dataset_label
    if (root / "dataset.json").exists() and not overwrite:
        raise FileExistsError("dataset.json exists; explicit overwrite is required.")
    # Validate all pairs before a move can remove any original input.
    for _, row in df.iterrows():
        split = _normalize_split(row[split_col])
        source = _path_from_value(row[image_col], "image path")
        label = _optional_path(row[label_col]) if label_col in df else None
        if split in {"train", "val"} and label is None:
            raise ValueError("Training/validation case requires a label path.")
        if validate and split != "test" and label is not None:
            _require_same_image_size(source, label, case_id=_sanitize_token(row[case_id_col]))
    images_tr = root / "imagesTr"
    labels_tr = root / "labelsTr"
    images_ts = root / "imagesTs"
    for folder in [images_tr, labels_tr, images_ts]:
        folder.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        split = _normalize_split(row[split_col])
        case_id = _sanitize_token(row[case_id_col])
        image_source = _path_from_value(row[image_col], "image path")
        label_value = row[label_col] if label_col in df.columns else None
        label_source = _optional_path(label_value)
        if split in {"train", "val"} and label_source is None:
            raise ValueError(f"Training/validation case {case_id!r} requires a label path.")

        image_target = (images_ts if split == "test" else images_tr) / f"{case_id}_0000.nii.gz"
        label_target = labels_tr / f"{case_id}.nii.gz" if split != "test" and label_source is not None else None

        try:
            _write_or_copy_nifti(image_source, image_target, copy_mode=copy_mode, overwrite=overwrite)
            if label_source is not None and label_target is not None:
                _write_or_copy_nifti(label_source, label_target, copy_mode=copy_mode, overwrite=overwrite, integer=True)
                if validate:
                    _require_same_image_size(image_target, label_target, case_id=case_id)
            rows.append(
                {
                    "case_id": case_id,
                    "split": split,
                    "source_image": str(image_source),
                    "source_label": str(label_source) if label_source else pd.NA,
                    "image_path": str(image_target),
                    "label_path": str(label_target) if label_target else pd.NA,
                    "status": "written",
                    "error": "",
                }
            )
        except Exception as exc:  # noqa: BLE001
            if validate:
                raise
            rows.append(
                {
                    "case_id": case_id,
                    "split": split,
                    "source_image": str(image_source),
                    "source_label": str(label_source) if label_source else pd.NA,
                    "image_path": str(image_target),
                    "label_path": str(label_target) if label_target else pd.NA,
                    "status": "error",
                    "error": str(exc),
                }
            )

    dataset_json = _nnunet_dataset_json(
        dataset_name=dataset_name,
        channel_names=channel_names,
        labels=labels,
        manifest_rows=rows,
    )
    with _atomic_output(root / "dataset.json", overwrite=overwrite) as target:
        target.write_text(json.dumps(dataset_json, indent=2), encoding="utf-8")
    result = pd.DataFrame(rows)
    if validate:
        validation = validate_nnunetv2_dataset(root)
        failed = validation[validation["status"] != "ok"]
        if not failed.empty:
            raise ValueError(f"nnU-Net dataset validation failed: {failed.to_dict(orient='records')}")
    return result


def prepare_yolo_classification_dataset(
    manifest: pd.DataFrame | str | Path,
    output_dir: str | Path,
    image_col: str = "image_path",
    class_col: str = "class",
    split_col: str = "split",
    sample_id_col: str | None = None,
    image_format: str = "png",
    copy_mode: CopyMode = "copy",
    dicom_window: tuple[float, float] | None = None,
    nifti_slice: int | Literal["middle", "all"] = "middle",
    overwrite: bool = False,
    validate: bool = True,
) -> pd.DataFrame:
    """Prepare a YOLO classification dataset from images, DICOM, or NIfTI."""

    df = _read_manifest(manifest)
    _require_columns(df, [image_col, class_col, split_col])
    _require_columns(df, [sample_id_col])
    _class_names(df[class_col])
    _validate_copy_mode(copy_mode)
    image_format = _normalize_image_format(image_format)
    out = Path(output_dir)
    rows: list[dict[str, Any]] = []
    targets = set()
    for index, (_, row) in enumerate(df.iterrows()):
        source = _path_from_value(row[image_col], "image path")
        key = (_normalize_split(row[split_col]), _sanitize_token(row[class_col]),
               _sample_id(row, sample_id_col, source, index))
        if key in targets:
            raise ValueError("Duplicate classification output identifier.")
        targets.add(key)
    for index, (_, row) in enumerate(df.iterrows()):
        split = _normalize_split(row[split_col])
        class_name = _sanitize_token(row[class_col])
        source = _path_from_value(row[image_col], "image path")
        sample_id = _sample_id(row, sample_id_col, source, index)
        target_dir = out / split / class_name
        target_dir.mkdir(parents=True, exist_ok=True)
        written = _write_yolo_images(
            source,
            target_dir,
            sample_id=sample_id,
            image_format=image_format,
            copy_mode=copy_mode,
            dicom_window=dicom_window,
            nifti_slice=nifti_slice,
            overwrite=overwrite,
        )
        for item in written:
            rows.append(
                {
                    "source_image": str(source),
                    "output_image": str(item["path"]),
                    "split": split,
                    "class": class_name,
                    "slice_index": item["slice_index"],
                    "status": "written",
                    "error": "",
                }
            )
    result = pd.DataFrame(rows)
    if validate:
        failed = validate_yolo_dataset(out, task="classify")
        failed = failed[failed["status"] != "ok"]
        if not failed.empty:
            raise ValueError(f"YOLO classification dataset validation failed: {failed.to_dict(orient='records')}")
    return result


def prepare_yolo_detection_dataset(
    manifest: pd.DataFrame | str | Path,
    output_dir: str | Path,
    image_col: str = "image_path",
    split_col: str = "split",
    class_col: str = "class",
    bbox_cols: Sequence[str] = ("x_min", "y_min", "x_max", "y_max"),
    image_width_col: str | None = None,
    image_height_col: str | None = None,
    coord_format: Literal["xyxy_pixels"] = "xyxy_pixels",
    sample_id_col: str | None = None,
    image_format: str = "png",
    copy_mode: CopyMode = "copy",
    dicom_window: tuple[float, float] | None = None,
    nifti_slice: int | Literal["middle", "all"] = "middle",
    overwrite: bool = False,
    validate: bool = True,
) -> pd.DataFrame:
    """Prepare an Ultralytics-compatible YOLO object-detection dataset."""

    if coord_format != "xyxy_pixels":
        raise ValueError("Only coord_format='xyxy_pixels' is supported in this pass.")
    if len(bbox_cols) != 4:
        raise ValueError("bbox_cols must contain four columns: x_min, y_min, x_max, y_max.")
    df = _read_manifest(manifest)
    _require_columns(df, [image_col, split_col, class_col])
    _require_columns(df, list(bbox_cols))
    _validate_copy_mode(copy_mode)
    image_format = _normalize_image_format(image_format)
    out = Path(output_dir)
    classes = _class_names(df[class_col].dropna())
    class_to_id = {name: idx for idx, name in enumerate(sorted(classes))}
    group_key = sample_id_col or image_col
    _require_columns(df, [group_key])
    _require_columns(df, [image_width_col, image_height_col])
    if df[group_key].isna().any():
        raise ValueError("Annotation group identifiers must be nonmissing.")
    if nifti_slice == "all":
        raise ValueError("Detection annotations require one selected slice per source.")
    if (out / "data.yaml").exists() and not overwrite:
        raise FileExistsError("data.yaml exists; explicit overwrite is required.")
    targets = set()
    for group_value, group in df.groupby(group_key, dropna=False):
        sources = {_path_from_value(v, "image path").resolve() for v in group[image_col]}
        splits = {_normalize_split(v) for v in group[split_col]}
        if len(sources) != 1 or len(splits) != 1:
            raise ValueError("Annotation groups must use a consistent source image and split.")
        for dimension in (image_width_col, image_height_col):
            if dimension and (group[dimension].isna().any() or group[dimension].nunique() != 1):
                raise ValueError("Annotation groups must use consistent image dimensions.")
        sample_id = _sanitize_token(group_value if sample_id_col else next(iter(sources)).stem)
        key = (next(iter(splits)), sample_id)
        if key in targets:
            raise ValueError("Duplicate detection output identifier after sanitization.")
        targets.add(key)
        for _, box in group.iterrows():
            empty = _row_has_empty_box(box, bbox_cols)
            if not empty and pd.isna(box[class_col]):
                raise ValueError("Bounding boxes require a class label.")
    rows: list[dict[str, Any]] = []

    for group_value, group in df.groupby(group_key, dropna=False):
        first = group.iloc[0]
        split = _normalize_split(first[split_col])
        source = _path_from_value(first[image_col], "image path")
        sample_id = _sanitize_token(group_value if sample_id_col else source.stem)
        image_dir = out / "images" / split
        label_dir = out / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        written = _write_yolo_images(
            source,
            image_dir,
            sample_id=sample_id,
            image_format=image_format,
            copy_mode=copy_mode,
            dicom_window=dicom_window,
            nifti_slice=nifti_slice,
            overwrite=overwrite,
        )
        if len(written) != 1:
            raise ValueError("YOLO detection currently writes one image per source; use nifti_slice='middle' or an integer.")
        image_info = written[0]
        image_path = Path(image_info["path"])
        width = int(first[image_width_col]) if image_width_col else int(image_info["width"])
        height = int(first[image_height_col]) if image_height_col else int(image_info["height"])
        if (width, height) != (image_info["width"], image_info["height"]):
            raise ValueError("Declared image dimensions must match the output image.")
        label_path = label_dir / f"{image_path.stem}.txt"
        label_lines = []
        box_rows = group.dropna(subset=[class_col])
        for _, box in box_rows.iterrows():
            if _row_has_empty_box(box, bbox_cols):
                continue
            class_name = _sanitize_token(box[class_col])
            class_id = class_to_id[class_name]
            label_lines.append(_yolo_box_line(box, bbox_cols, width=width, height=height, class_id=class_id))
        if label_path.exists() and not overwrite:
            raise FileExistsError(f"Output label exists and overwrite=False: {label_path}")
        with _atomic_output(label_path, overwrite=overwrite) as target:
            target.write_text("\n".join(label_lines) + ("\n" if label_lines else ""), encoding="utf-8")
        rows.append(
            {
                "source_image": str(source),
                "output_image": str(image_path),
                "output_label": str(label_path),
                "split": split,
                "bbox_count": len(label_lines),
                "status": "written",
                "error": "",
            }
        )
    _write_yolo_data_yaml(out, class_to_id, overwrite=overwrite)
    result = pd.DataFrame(rows)
    if validate:
        failed = validate_yolo_dataset(out, task="detect")
        failed = failed[failed["status"] != "ok"]
        if not failed.empty:
            raise ValueError(f"YOLO detection dataset validation failed: {failed.to_dict(orient='records')}")
    return result


def validate_nnunetv2_dataset(dataset_dir: str | Path) -> pd.DataFrame:
    """Validate the expected files and names in an nnU-Net v2 dataset folder."""

    root = Path(dataset_dir)
    rows = []
    for rel in ["imagesTr", "labelsTr", "imagesTs", "dataset.json"]:
        path = root / rel
        ok = path.exists()
        rows.append({"path": str(path), "check": f"exists:{rel}", "status": "ok" if ok else "missing", "message": "" if ok else f"Missing {rel}"})
    for image in sorted((root / "imagesTr").glob("*.nii.gz")) + sorted((root / "imagesTs").glob("*.nii.gz")):
        ok = image.name.endswith("_0000.nii.gz")
        rows.append({"path": str(image), "check": "nnunet_image_name", "status": "ok" if ok else "error", "message": "" if ok else "Image must end with _0000.nii.gz"})
    for label in sorted((root / "labelsTr").glob("*.nii.gz")):
        ok = not label.name.endswith("_0000.nii.gz")
        rows.append({"path": str(label), "check": "nnunet_label_name", "status": "ok" if ok else "error", "message": "" if ok else "Label must not include channel suffix"})
    return pd.DataFrame(rows)


def validate_yolo_dataset(dataset_dir: str | Path, task: Literal["detect", "classify"] = "detect") -> pd.DataFrame:
    """Validate a prepared YOLO classification or detection dataset."""

    root = Path(dataset_dir)
    rows = []
    if task == "classify":
        for split in ["train", "val", "test"]:
            split_dir = root / split
            if not split_dir.exists():
                continue
            images = [p for p in split_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
            rows.append({"path": str(split_dir), "check": f"classify_images:{split}", "status": "ok" if images else "missing", "message": "" if images else "No images found"})
    elif task == "detect":
        data_yaml = root / "data.yaml"
        rows.append({"path": str(data_yaml), "check": "data_yaml", "status": "ok" if data_yaml.exists() else "missing", "message": "" if data_yaml.exists() else "Missing data.yaml"})
        for split in ["train", "val", "test"]:
            image_dir = root / "images" / split
            if not image_dir.exists():
                continue
            label_dir = root / "labels" / split
            images = [p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
            for image in images:
                label = label_dir / f"{image.stem}.txt"
                rows.append({"path": str(label), "check": f"label_for:{image.name}", "status": "ok" if label.exists() else "missing", "message": "" if label.exists() else "Missing label file"})
    else:
        raise ValueError("task must be 'detect' or 'classify'.")
    return pd.DataFrame(rows)


def write_dataset_manifest(df: pd.DataFrame, output_path: str | Path) -> Path:
    """Write a dataset preparation manifest as CSV or JSON."""

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".json":
        df.to_json(out, orient="records", indent=2)
    else:
        df.to_csv(out, index=False)
    return out.resolve()


def _read_manifest(manifest: pd.DataFrame | str | Path) -> pd.DataFrame:
    if isinstance(manifest, pd.DataFrame):
        if manifest.empty:
            raise ValueError("Dataset manifest must be nonempty.")
        return manifest.copy()
    path = Path(manifest)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    if path.suffix.lower() == ".json":
        return _read_manifest(pd.read_json(path))
    return _read_manifest(pd.read_csv(path))


def _require_columns(df: pd.DataFrame, columns: Iterable[str | None]) -> None:
    missing = [col for col in columns if col and col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _validate_copy_mode(copy_mode: str) -> None:
    if copy_mode not in {"copy", "symlink", "move"}:
        raise ValueError("copy_mode must be 'copy', 'symlink', or 'move'.")


def _normalize_split(value: Any) -> SplitName:
    split = str(value).strip().lower()
    if split in {"training", "tr"}:
        split = "train"
    if split in {"validation", "valid"}:
        split = "val"
    if split not in {"train", "val", "test"}:
        raise ValueError(f"Invalid split {value!r}; expected train, val, or test.")
    return split  # type: ignore[return-value]


def _sanitize_token(value: Any) -> str:
    if pd.isna(value):
        raise ValueError("Dataset identifiers and class names must be nonmissing.")
    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    if not text:
        raise ValueError(f"Cannot create a safe dataset token from {value!r}.")
    return text


def _class_names(values: pd.Series) -> list[str]:
    original = list(pd.unique(values))
    sanitized = [_sanitize_token(value) for value in original]
    if len(set(sanitized)) != len(sanitized):
        raise ValueError("Class name collision after filename sanitization.")
    return sanitized


def _path_from_value(value: Any, label: str) -> Path:
    if value is None or pd.isna(value):
        raise ValueError(f"Missing {label}.")
    path = Path(str(value))
    if not path.exists():
        raise FileNotFoundError(f"{label.title()} not found: {path}")
    return path


def _optional_path(value: Any) -> Path | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    path = Path(str(value))
    if not path.exists():
        raise FileNotFoundError(f"Label path not found: {path}")
    return path


def _is_nifti(path: Path) -> bool:
    return path.name.lower().endswith(NIFTI_SUFFIXES)


def _write_or_copy_nifti(
    source: Path,
    target: Path,
    *,
    copy_mode: CopyMode,
    overwrite: bool,
    integer: bool = False,
) -> None:
    if target.exists() and not overwrite:
        raise FileExistsError(f"Output file exists and overwrite=False: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.name.lower().endswith(".nii.gz"):
        _copy_file(source, target, copy_mode=copy_mode, overwrite=overwrite)
        return
    if source.is_dir():
        image = _read_first_dicom_series(source)
        with _atomic_output(target, overwrite=overwrite) as staged:
            write_nifti(image, staged)
        return
    if source.is_file():
        try:
            image = sitk.ReadImage(str(source))
            if integer:
                image = sitk.Cast(image, sitk.sitkUInt16)
            with _atomic_output(target, overwrite=overwrite) as staged:
                write_nifti(image, staged)
            if _is_nifti(source) and copy_mode == "move":
                source.unlink()
            return
        except RuntimeError as exc:
            raise ValueError(f"Unsupported image input for NIfTI conversion: {source}") from exc
    raise ValueError(f"Unsupported image input: {source}")


def _copy_file(source: Path, target: Path, *, copy_mode: CopyMode, overwrite: bool) -> None:
    if source.resolve() == target.resolve() or (target.exists() and source.exists() and source.samefile(target)):
        raise ValueError("Source and target must not be the same file.")
    with _atomic_output(target, overwrite=overwrite) as staged:
        if copy_mode == "symlink":
            if not source.is_file():
                raise FileNotFoundError("Source file is missing.")
            staged.unlink()
            staged.symlink_to(source.resolve())
        else:
            shutil.copy2(source, staged)
    if copy_mode == "move":
        source.unlink()


@contextmanager
def _atomic_output(target: Path, *, overwrite: bool):
    if (target.exists() or target.is_symlink()) and not overwrite:
        raise FileExistsError(f"Output file exists and overwrite=False: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".fyron-", suffix="".join(target.suffixes), dir=target.parent)
    os.close(fd)
    staged = Path(name)
    try:
        yield staged
        if overwrite:
            os.replace(staged, target)
        else:
            os.link(staged, target, follow_symlinks=False)
    finally:
        staged.unlink(missing_ok=True)


def _read_first_dicom_series(source: Path) -> sitk.Image:
    series_ids = get_dicom_series_ids(source)
    if not series_ids:
        raise ValueError(f"No DICOM series found in {source}")
    if len(series_ids) != 1:
        raise ValueError("DICOM input must contain exactly one series; select a series folder explicitly.")
    return read_dicom_series(source, series_id=series_ids[0])  # type: ignore[return-value]


def _require_same_image_size(image_path: Path, label_path: Path, *, case_id: str) -> None:
    image = _read_first_dicom_series(image_path) if image_path.is_dir() else sitk.ReadImage(str(image_path))
    label = _read_first_dicom_series(label_path) if label_path.is_dir() else sitk.ReadImage(str(label_path))
    if image.GetSize() != label.GetSize():
        raise ValueError(f"Image and label sizes differ for {case_id}: {image.GetSize()} vs {label.GetSize()}")
    if image.GetDimension() != 3 or any(
        not np.allclose(getattr(image, name)(), getattr(label, name)(), rtol=0, atol=1e-5)
        for name in ("GetSpacing", "GetOrigin", "GetDirection")
    ):
        raise ValueError("Image and label geometry must be aligned in physical space.")


def _nnunet_dataset_json(
    *,
    dataset_name: str,
    channel_names: dict[int | str, str] | Sequence[str] | None,
    labels: dict[int | str, str] | None,
    manifest_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    channels: dict[str, str]
    if channel_names is None:
        channels = {"0": "CT"}
    elif isinstance(channel_names, dict):
        channels = {str(key): str(value) for key, value in channel_names.items()}
    else:
        channels = {str(index): str(name) for index, name in enumerate(channel_names)}
    label_map: dict[str, Any] = {"background": 0, "foreground": 1}
    if labels is not None:
        if all(str(key).isdigit() for key in labels):
            label_map = {str(value): int(key) for key, value in labels.items()}
        else:
            label_map = {str(key): int(value) if str(value).isdigit() else value for key, value in labels.items()}
    train_count = sum(1 for row in manifest_rows if row["split"] in {"train", "val"} and row["status"] == "written")
    test_count = sum(1 for row in manifest_rows if row["split"] == "test" and row["status"] == "written")
    return {
        "name": dataset_name,
        "channel_names": channels,
        "labels": label_map,
        "numTraining": train_count,
        "numTest": test_count,
        "file_ending": ".nii.gz",
    }


def _normalize_image_format(image_format: str) -> str:
    fmt = image_format.lower().lstrip(".")
    if fmt not in {"png", "jpg", "jpeg"}:
        raise ValueError("image_format must be png, jpg, or jpeg.")
    return "jpg" if fmt == "jpeg" else fmt


def _sample_id(row: pd.Series, sample_id_col: str | None, source: Path, index: int) -> str:
    if sample_id_col:
        return _sanitize_token(row[sample_id_col])
    return _sanitize_token(f"{source.stem}_{index:04d}")


def _write_yolo_images(
    source: Path,
    target_dir: Path,
    *,
    sample_id: str,
    image_format: str,
    copy_mode: CopyMode,
    dicom_window: tuple[float, float] | None,
    nifti_slice: int | Literal["middle", "all"],
    overwrite: bool,
) -> list[dict[str, Any]]:
    if source.is_file() and source.suffix.lower() in IMAGE_EXTENSIONS:
        width, height = _image_size_2d(source)
        target = target_dir / f"{sample_id}{source.suffix.lower()}"
        _copy_file(source, target, copy_mode=copy_mode, overwrite=overwrite)
        return [{"path": target, "slice_index": pd.NA, "width": width, "height": height}]
    if source.is_dir():
        image = _read_first_dicom_series(source)
        array = sitk.GetArrayFromImage(image)
        return _write_array_slices(array, target_dir, sample_id=sample_id, image_format=image_format, dicom_window=dicom_window, nifti_slice=nifti_slice, overwrite=overwrite)
    if source.is_file():
        image = sitk.ReadImage(str(source))
        array = sitk.GetArrayFromImage(image)
        return _write_array_slices(array, target_dir, sample_id=sample_id, image_format=image_format, dicom_window=dicom_window, nifti_slice=nifti_slice, overwrite=overwrite)
    raise ValueError(f"Unsupported YOLO image input: {source}")


def _write_array_slices(
    array: np.ndarray,
    target_dir: Path,
    *,
    sample_id: str,
    image_format: str,
    dicom_window: tuple[float, float] | None,
    nifti_slice: int | Literal["middle", "all"],
    overwrite: bool,
) -> list[dict[str, Any]]:
    arr = np.asarray(array)
    if arr.ndim == 2:
        indices = [None]
        slices = [arr]
    elif arr.ndim == 3:
        if nifti_slice == "middle":
            mid = arr.shape[0] // 2
            indices = [mid]
        elif nifti_slice == "all":
            indices = list(range(arr.shape[0]))
        elif isinstance(nifti_slice, int):
            if nifti_slice < 0 or nifti_slice >= arr.shape[0]:
                raise ValueError(f"nifti_slice {nifti_slice} outside volume with {arr.shape[0]} slices.")
            indices = [nifti_slice]
        else:
            raise ValueError("nifti_slice must be 'middle', 'all', or an integer.")
        slices = [arr[int(idx)] for idx in indices]
    else:
        raise ValueError("YOLO conversion expects a 2D image or 3D volume.")

    target_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for idx, slc in zip(indices, slices):
        suffix = "" if idx is None else f"_z{int(idx):04d}"
        target = target_dir / f"{sample_id}{suffix}.{image_format}"
        if target.exists() and not overwrite:
            raise FileExistsError(f"Output image exists and overwrite=False: {target}")
        norm = _normalize_slice(slc, dicom_window=dicom_window)
        with _atomic_output(target, overwrite=overwrite) as staged:
            _pyplot().imsave(staged, norm, cmap="gray", vmin=0.0, vmax=1.0)
        written.append({"path": target, "slice_index": idx if idx is not None else pd.NA, "width": norm.shape[1], "height": norm.shape[0]})
    return written


def _normalize_slice(array: np.ndarray, *, dicom_window: tuple[float, float] | None) -> np.ndarray:
    arr = np.asarray(array, dtype=float)
    if dicom_window is not None:
        center, width = dicom_window
        lo = center - width / 2
        hi = center + width / 2
    else:
        lo, hi = np.nanpercentile(arr, [1, 99])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo, hi = float(np.nanmin(arr)), float(np.nanmax(arr))
    if hi <= lo:
        return np.zeros(arr.shape, dtype=float)
    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0)


def _image_size_2d(path: Path) -> tuple[int, int]:
    from PIL import Image

    # Restrict decoders as well as extensions. A TIFF renamed as .jpg must not
    # reach a TIFF decoder, particularly on the Python 3.10 Pillow branch.
    with Image.open(path, formats=["PNG", "JPEG"]) as image:
        return image.size


def _row_has_empty_box(row: pd.Series, bbox_cols: Sequence[str]) -> bool:
    missing = [col not in row.index or pd.isna(row[col]) for col in bbox_cols]
    if any(missing) and not all(missing):
        raise ValueError("Bounding box is incomplete: provide all four coordinates or none.")
    return all(missing)


def _yolo_box_line(row: pd.Series, bbox_cols: Sequence[str], *, width: int, height: int, class_id: int) -> str:
    x_min, y_min, x_max, y_max = [float(row[col]) for col in bbox_cols]
    if not all(math.isfinite(v) for v in [x_min, y_min, x_max, y_max]):
        raise ValueError("Bounding box contains non-finite values.")
    if x_min < 0 or y_min < 0 or x_max > width or y_max > height or x_max <= x_min or y_max <= y_min:
        raise ValueError(f"Invalid xyxy box {x_min, y_min, x_max, y_max} for image size {width}x{height}.")
    x_center = ((x_min + x_max) / 2) / width
    y_center = ((y_min + y_max) / 2) / height
    box_width = (x_max - x_min) / width
    box_height = (y_max - y_min) / height
    return f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"


def _write_yolo_data_yaml(root: Path, class_to_id: dict[str, int], *, overwrite: bool) -> None:
    names = {idx: name for name, idx in class_to_id.items()}
    lines = [
        f"path: {root.resolve()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "names:",
    ]
    for idx in sorted(names):
        lines.append(f"  {idx}: {names[idx]}")
    with _atomic_output(root / "data.yaml", overwrite=overwrite) as target:
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
