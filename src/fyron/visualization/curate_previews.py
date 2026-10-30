"""Prepare Curate-ready PNG previews from CT/MRI volumes or 2-D images."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence, Union

import cv2
import numpy as np
import SimpleITK as sitk

from fyron.visualization._cv_render import window_ct_uint8
from fyron.visualization._slices import Orientation, center_slice_index, extract_slice, slice_pixel_aspect

StrPath = Union[str, Path]
SourceKind = Literal["dicom_series", "image_file"]

_DICOM_SUFFIXES = {".dcm", ".dicom", ".ima"}
_RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
_VOLUME_SUFFIXES = {".nii", ".nii.gz", ".mha", ".mhd", ".nrrd", ".nhdr"}
_ORIENTATIONS: tuple[Orientation, ...] = ("axial", "coronal", "sagittal")


@dataclass(frozen=True)
class PreviewSource:
    """Input source resolved from a directory scan."""

    kind: SourceKind
    path: Path
    label: str
    series_id: str | None = None


def prepare_curate_image_previews(
    input_dir: StrPath,
    output_dir: StrPath,
    *,
    recursive: bool = True,
    include_dicom: bool = True,
    include_image_files: bool = True,
    panel_width: int = 384,
    window_center: float | None = None,
    window_width: float | None = None,
    percentile_clip: tuple[float, float] = (1.0, 99.0),
    overwrite: bool = False,
    manifest_csv: StrPath | None = None,
) -> dict[str, Any]:
    """Write Curate-ready PNG previews from medical image folders.

    3-D volumes produce three images: middle axial, coronal, and sagittal
    slices. 2-D images produce one image. The function walks nested folders by
    default and preserves relative folder structure in the output directory.

    Parameters
    ----------
    input_dir
        Directory containing CT/MRI volumes, DICOM files, or 2-D images.
    output_dir
        Destination folder for PNG previews.
    recursive
        If True, scan nested folders.
    include_dicom
        If True, read DICOM series from directories containing DICOM files.
    include_image_files
        If True, read NIfTI/MHA/NRRD and common 2-D raster image files.
    panel_width
        Output width per PNG. Height follows physical spacing for 3-D slices.
    window_center, window_width
        Optional fixed grayscale window, useful for CT. If omitted, robust
        percentile normalization is used, which also works for MRI.
    percentile_clip
        Low/high percentiles for automatic normalization when no fixed window
        is supplied.
    overwrite
        If False, existing PNG files are left untouched.
    manifest_csv
        Optional manifest path. Defaults to ``output_dir / "manifest.csv"``.

    Returns
    -------
    dict
        ``input_dir``, ``output_dir``, ``manifest_csv``, ``sources_found``,
        ``images_written``, ``images_skipped``, and ``rows``.

    Examples
    --------
    >>> from fyron.visualization import prepare_curate_image_previews
    >>> # prepare_curate_image_previews("/data/ct_folder", "curate_previews")
    """
    root = Path(input_dir).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Input directory not found: {root}")
    out_root = Path(output_dir).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(manifest_csv).expanduser().resolve() if manifest_csv else out_root / "manifest.csv"

    sources = discover_preview_sources(
        root,
        recursive=recursive,
        include_dicom=include_dicom,
        include_image_files=include_image_files,
    )
    rows: list[dict[str, Any]] = []
    written = 0
    skipped = 0

    for source in sources:
        try:
            image = _read_source_image(source)
            arr = sitk.GetArrayFromImage(image)
            spacing = _spacing_for_array(image, arr)
            source_rows, source_written, source_skipped = _write_source_previews(
                source,
                arr,
                spacing,
                input_root=root,
                output_root=out_root,
                panel_width=panel_width,
                window_center=window_center,
                window_width=window_width,
                percentile_clip=percentile_clip,
                overwrite=overwrite,
            )
            rows.extend(source_rows)
            written += source_written
            skipped += source_skipped
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "source_path": str(source.path),
                    "source_kind": source.kind,
                    "source_label": source.label,
                    "series_id": source.series_id or "",
                    "output_path": "",
                    "orientation": "",
                    "slice_index": "",
                    "shape": "",
                    "status": "error",
                    "error": str(exc),
                }
            )

    _write_manifest(manifest_path, rows)
    return {
        "input_dir": str(root),
        "output_dir": str(out_root),
        "manifest_csv": str(manifest_path),
        "sources_found": len(sources),
        "images_written": written,
        "images_skipped": skipped,
        "rows": rows,
    }


def discover_preview_sources(
    input_dir: StrPath,
    *,
    recursive: bool = True,
    include_dicom: bool = True,
    include_image_files: bool = True,
) -> list[PreviewSource]:
    """Discover DICOM series and image files below a directory."""
    root = Path(input_dir).expanduser().resolve()
    sources: list[PreviewSource] = []
    dicom_dirs: set[Path] = set()

    if include_dicom:
        candidates = root.rglob("*") if recursive else root.iterdir()
        for path in candidates:
            if path.is_file() and path.suffix.lower() in _DICOM_SUFFIXES:
                dicom_dirs.add(path.parent)
        if not dicom_dirs and any(root.glob("*")):
            dicom_dirs.add(root)
        for folder in sorted(dicom_dirs):
            try:
                series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(folder)) or []
            except RuntimeError:
                series_ids = []
            for series_id in sorted(series_ids):
                label = f"{_relative_label(folder, root)}__series-{_safe_name(series_id)[-16:]}"
                sources.append(PreviewSource("dicom_series", folder, label, series_id))

    if include_image_files:
        candidates = root.rglob("*") if recursive else root.iterdir()
        for path in sorted(p for p in candidates if p.is_file()):
            suffix = _compound_suffix(path)
            if suffix in _DICOM_SUFFIXES:
                continue
            if suffix in _VOLUME_SUFFIXES or suffix in _RASTER_SUFFIXES:
                sources.append(PreviewSource("image_file", path, _relative_label(path, root)))

    return sources


def _read_source_image(source: PreviewSource) -> sitk.Image:
    if source.kind == "dicom_series":
        if not source.series_id:
            raise ValueError(f"Missing DICOM series id for {source.path}")
        files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(source.path), source.series_id)
        if not files:
            raise ValueError(f"No DICOM files found for series {source.series_id}")
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(files)
        return reader.Execute()
    return sitk.ReadImage(str(source.path))


def _write_source_previews(
    source: PreviewSource,
    arr: np.ndarray,
    spacing: tuple[float, float, float],
    *,
    input_root: Path,
    output_root: Path,
    panel_width: int,
    window_center: float | None,
    window_width: float | None,
    percentile_clip: tuple[float, float],
    overwrite: bool,
) -> tuple[list[dict[str, Any]], int, int]:
    arr = np.squeeze(np.asarray(arr))
    rows: list[dict[str, Any]] = []
    written = 0
    skipped = 0
    shape_text = "x".join(str(v) for v in arr.shape)

    if arr.ndim == 2:
        output_path = _output_path_for(source, input_root, output_root, "slice")
        status = _write_png(
            _render_2d(arr, panel_width=panel_width, window_center=window_center, window_width=window_width, percentile_clip=percentile_clip),
            output_path,
            overwrite=overwrite,
        )
        written += int(status == "written")
        skipped += int(status == "skipped")
        rows.append(_manifest_row(source, output_path, "slice", 0, shape_text, status))
        return rows, written, skipped

    if arr.ndim != 3:
        raise ValueError(f"Expected a 2-D or 3-D image, got shape {arr.shape}")

    for orientation in _ORIENTATIONS:
        idx = center_slice_index(arr.shape, orientation)
        sl = extract_slice(arr, orientation, idx)
        panel = _render_slice(
            sl,
            spacing=spacing,
            orientation=orientation,
            panel_width=panel_width,
            window_center=window_center,
            window_width=window_width,
            percentile_clip=percentile_clip,
        )
        output_path = _output_path_for(source, input_root, output_root, orientation)
        status = _write_png(panel, output_path, overwrite=overwrite)
        written += int(status == "written")
        skipped += int(status == "skipped")
        rows.append(_manifest_row(source, output_path, orientation, idx, shape_text, status))
    return rows, written, skipped


def _render_slice(
    image_slice: np.ndarray,
    *,
    spacing: tuple[float, float, float],
    orientation: Orientation,
    panel_width: int,
    window_center: float | None,
    window_width: float | None,
    percentile_clip: tuple[float, float],
) -> np.ndarray:
    gray = _normalize_uint8(image_slice, window_center=window_center, window_width=window_width, percentile_clip=percentile_clip)
    height = max(1, int(round(panel_width * slice_pixel_aspect(orientation, spacing, gray.shape))))
    return cv2.resize(gray, (panel_width, height), interpolation=cv2.INTER_AREA)


def _render_2d(
    image: np.ndarray,
    *,
    panel_width: int,
    window_center: float | None,
    window_width: float | None,
    percentile_clip: tuple[float, float],
) -> np.ndarray:
    gray = _normalize_uint8(image, window_center=window_center, window_width=window_width, percentile_clip=percentile_clip)
    height = max(1, int(round(panel_width * gray.shape[0] / max(gray.shape[1], 1))))
    return cv2.resize(gray, (panel_width, height), interpolation=cv2.INTER_AREA)


def _normalize_uint8(
    arr: np.ndarray,
    *,
    window_center: float | None,
    window_width: float | None,
    percentile_clip: tuple[float, float],
) -> np.ndarray:
    image = np.asarray(arr)
    if window_center is not None and window_width is not None:
        return window_ct_uint8(image, window_center=window_center, window_width=window_width)

    values = image[np.isfinite(image)]
    if values.size == 0:
        return np.zeros(image.shape, dtype=np.uint8)
    low_q, high_q = percentile_clip
    low, high = np.percentile(values.astype(np.float32), [low_q, high_q])
    if high <= low:
        low = float(values.min())
        high = float(values.max())
    if high <= low:
        return np.zeros(image.shape, dtype=np.uint8)
    clipped = np.clip(image.astype(np.float32), low, high)
    return (((clipped - low) / (high - low)) * 255.0).astype(np.uint8)


def _spacing_for_array(image: sitk.Image, arr: np.ndarray) -> tuple[float, float, float]:
    spacing = tuple(float(v) for v in image.GetSpacing())
    if arr.ndim >= 3 and len(spacing) >= 3:
        return (spacing[0], spacing[1], spacing[2])
    if len(spacing) >= 2:
        return (spacing[0], spacing[1], 1.0)
    return (1.0, 1.0, 1.0)


def _write_png(image: np.ndarray, path: Path, *, overwrite: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return "skipped"
    ok = cv2.imwrite(str(path), image)
    if not ok:
        raise ValueError(f"Failed to write PNG: {path}")
    return "written"


def _output_path_for(source: PreviewSource, input_root: Path, output_root: Path, suffix: str) -> Path:
    try:
        rel_parent = source.path.parent.relative_to(input_root) if source.path.is_file() else source.path.relative_to(input_root)
    except ValueError:
        rel_parent = Path()
    rel_parent = Path() if str(rel_parent) == "." else rel_parent
    base = _safe_name(Path(source.label).name)
    if source.kind == "dicom_series" and source.series_id:
        base = f"{_safe_name(source.path.name)}__series-{_safe_name(source.series_id)[-16:]}"
    return output_root / rel_parent / f"{base}_{suffix}.png"


def _manifest_row(
    source: PreviewSource,
    output_path: Path,
    orientation: str,
    slice_index: int,
    shape: str,
    status: str,
) -> dict[str, Any]:
    return {
        "source_path": str(source.path),
        "source_kind": source.kind,
        "source_label": source.label,
        "series_id": source.series_id or "",
        "output_path": str(output_path),
        "orientation": orientation,
        "slice_index": slice_index,
        "shape": shape,
        "status": status,
        "error": "",
    }


def _write_manifest(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_path",
        "source_kind",
        "source_label",
        "series_id",
        "output_path",
        "orientation",
        "slice_index",
        "shape",
        "status",
        "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _compound_suffix(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".nii.gz"):
        return ".nii.gz"
    return path.suffix.lower()


def _relative_label(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path.name
    return str(rel)


def _safe_name(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._-")
    return text or "image"
