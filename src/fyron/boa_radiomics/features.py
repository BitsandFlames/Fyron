"""Radiomics feature extraction from BOA segmentations."""

from __future__ import annotations

import logging
import multiprocessing
from collections.abc import Iterable, Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from tqdm import tqdm

from fyron.boa_extraction import TOTAL_LABELS
from .._boa_labels import BODY_REGION_LABELS
from .._diagnostics import error_event
from .._extraction_report import decision, case_result, validate_cases, collect_results


LOGGER = logging.getLogger(__name__)

DEFAULT_BODY_REGION_LABELS = dict(BODY_REGION_LABELS)
DEFAULT_IMAGE_FILENAMES = (
    "ct.nii.gz",
    "CT.nii.gz",
    "image.nii.gz",
    "CT/image.nii.gz",
    "ct.nii",
    "image.nii",
)
DEFAULT_SEGMENTATION_FILENAMES = {
    "total": "total.nii.gz",
    "body_regions": "body-regions.nii.gz",
}
RADIOMICS_DIAGNOSTIC_PREFIX = "diagnostics_"

SegmentationKind = Literal["total", "body_regions"]
OnError = Literal["skip", "raise"]


def _require_simpleitk():
    try:
        import SimpleITK as sitk
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "BOA radiomics extraction requires SimpleITK. Install Fyron with imaging support "
            "or install SimpleITK."
        ) from exc
    return sitk


def _make_extractor(settings: Mapping[str, Any] | None = None):
    try:
        from radiomics import featureextractor  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "BOA radiomics extraction requires PyRadiomics. "
            'Install it with: uv add "fyron[radiomics]"'
        ) from exc

    extractor = featureextractor.RadiomicsFeatureExtractor(**dict(settings or {}))
    return extractor


def _first_existing_path(case_folder: Path, candidates: str | Path | Sequence[str | Path]) -> Path | None:
    if isinstance(candidates, (str, Path)):
        candidates = (candidates,)
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = case_folder / path
        if path.exists():
            return path
    return None


def discover_boa_radiomics_cases(
    cohort_folder: str | Path,
    *,
    segmentation_filename: str | Path = "total.nii.gz",
) -> list[Path]:
    """Discover BOA patient folders with a target segmentation file."""

    root = Path(cohort_folder)
    return sorted({path.parent for path in root.rglob(str(segmentation_filename))})


def _resolve_labels(
    segmentation_kind: SegmentationKind,
    labels: Mapping[str, int] | Sequence[int] | None,
) -> dict[str, int]:
    if labels is None:
        if segmentation_kind == "total":
            return dict(TOTAL_LABELS)
        if segmentation_kind == "body_regions":
            return dict(DEFAULT_BODY_REGION_LABELS)
        raise ValueError("segmentation_kind must be 'total' or 'body_regions'.")
    if isinstance(labels, Mapping):
        return {str(name): int(value) for name, value in labels.items()}
    return {f"label_{int(value)}": int(value) for value in labels}


def _same_grid(image: Any, mask: Any) -> bool:
    return (
        image.GetSize() == mask.GetSize()
        and np.allclose(list(image.GetSpacing()), list(mask.GetSpacing()))
        and np.allclose(list(image.GetOrigin()), list(mask.GetOrigin()))
        and np.allclose(list(image.GetDirection()), list(mask.GetDirection()))
    )


def _resample_to_reference(moving_img: Any, reference_img: Any, *, is_label: bool) -> Any:
    sitk = _require_simpleitk()
    interpolator = sitk.sitkNearestNeighbor if is_label else sitk.sitkBSpline
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(reference_img)
    resampler.SetInterpolator(interpolator)
    resampler.SetOutputPixelType(moving_img.GetPixelID())
    return resampler.Execute(moving_img)


def _ensure_same_grid(image: Any, mask: Any) -> Any:
    if _same_grid(image, mask):
        return mask
    return _resample_to_reference(mask, image, is_label=True)


def _binary_mask_for_label(segmentation: Any, reference: Any, label_value: int) -> tuple[Any, int]:
    sitk = _require_simpleitk()
    array = sitk.GetArrayFromImage(segmentation)
    binary = (array == label_value).astype(np.uint8)
    voxel_count = int(np.sum(binary))
    mask = sitk.GetImageFromArray(binary)
    mask.CopyInformation(reference)
    return mask, voxel_count


def _clean_feature_name(name: str) -> str:
    return name.replace(" ", "_").replace("-", "_")


def _coerce_feature_value(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(numeric):
        return None
    return numeric


def _extract_label_features(
    extractor: Any,
    image: Any,
    mask: Any,
    *,
    label_name: str,
    label_value: int,
    segmentation_kind: str,
    feature_prefix: str,
    exclude_diagnostics: bool,
) -> tuple[dict[str, Any], bool]:
    result = extractor.execute(image, mask, label=1)
    features: dict[str, Any] = {}
    complete = True
    measurements = 0
    for key, value in result.items():
        key = str(key)
        if exclude_diagnostics and key.startswith(RADIOMICS_DIAGNOSTIC_PREFIX):
            continue
        numeric = _coerce_feature_value(value)
        if numeric is None:
            if not key.startswith(RADIOMICS_DIAGNOSTIC_PREFIX):
                try:
                    float(value)
                except (TypeError, ValueError):
                    pass
                else:
                    complete = False
            continue
        feature_name = _clean_feature_name(key)
        column = f"{feature_prefix}_{segmentation_kind}_{label_name}_{feature_name}"
        features[column] = numeric
        if not key.startswith(RADIOMICS_DIAGNOSTIC_PREFIX):
            measurements += 1
    features[f"{feature_prefix}_{segmentation_kind}_{label_name}_label"] = int(label_value)
    return features, complete and measurements > 0


def extract_case_radiomics_features(
    case_folder: str | Path,
    *,
    image_filename: str | Path | Sequence[str | Path] = DEFAULT_IMAGE_FILENAMES,
    segmentation_kind: SegmentationKind = "total",
    segmentation_filename: str | Path | None = None,
    labels: Mapping[str, int] | Sequence[int] | None = None,
    extractor: Any | None = None,
    extractor_settings: Mapping[str, Any] | None = None,
    feature_prefix: str = "radiomics",
    download_id: str | None = None,
    include_paths: bool = True,
    exclude_diagnostics: bool = True,
    minimum_voxels: int = 1,
    resample_mask: bool = True,
    on_error: OnError = "skip",
) -> dict[str, Any] | None:
    """Extract PyRadiomics features for one BOA case folder.

    The output is a wide feature dictionary with one row per patient. Feature
    columns follow ``radiomics_<segmentation_kind>_<label>_<feature>``.
    """

    case_path = Path(case_folder)
    if on_error not in {"skip", "raise"}:
        raise ValueError("on_error must be 'skip' or 'raise'.")
    image_path = _first_existing_path(case_path, image_filename)
    if segmentation_filename is None:
        segmentation_filename = DEFAULT_SEGMENTATION_FILENAMES[segmentation_kind]
    segmentation_path = _first_existing_path(case_path, segmentation_filename)
    if image_path is None or segmentation_path is None:
        decision("missing_inputs")
        if on_error == "raise":
            raise FileNotFoundError(
                f"Missing CT image or segmentation for case {case_path}. "
                f"image={image_path}, segmentation={segmentation_path}"
            )
        return None

    sitk = _require_simpleitk()
    label_map = _resolve_labels(segmentation_kind, labels)
    try:
        image = sitk.ReadImage(str(image_path))
        segmentation = sitk.ReadImage(str(segmentation_path))
        if resample_mask:
            segmentation = _ensure_same_grid(image, segmentation)
        elif not _same_grid(image, segmentation):
            raise ValueError(f"Image and segmentation grids differ for case {case_path}.")
    except Exception as exc:
        decision("extraction_failure")
        if on_error == "raise":
            raise
        error_event(LOGGER, "radiomics", exc)
        return None

    extractor_obj = extractor if extractor is not None else _make_extractor(extractor_settings)
    row: dict[str, Any] = {"download_id": download_id or case_path.name}
    if include_paths:
        row["image_path"] = str(image_path)
        row["segmentation_path"] = str(segmentation_path)
        row["segmentation_kind"] = segmentation_kind

    extracted_any = False
    failed_labels = False
    for label_name, label_value in label_map.items():
        try:
            mask, voxel_count = _binary_mask_for_label(segmentation, image, label_value)
            row[f"{feature_prefix}_{segmentation_kind}_{label_name}_voxel_count"] = voxel_count
            if voxel_count < minimum_voxels:
                decision("empty_label" if voxel_count == 0 else "undersized_label", label_name)
                failed_labels = True
                continue
            label_features, complete = _extract_label_features(
                extractor_obj,
                image,
                mask,
                label_name=label_name,
                label_value=label_value,
                segmentation_kind=segmentation_kind,
                feature_prefix=feature_prefix,
                exclude_diagnostics=exclude_diagnostics,
            )
            row.update(label_features)
            extracted_any = extracted_any or bool(label_features)
            failed_labels = failed_labels or not complete
            decision("success" if complete else "partial", label_name)
        except Exception as exc:
            failed_labels = True
            decision("extraction_failure", label_name)
            if on_error == "raise":
                raise
            error_event(LOGGER, "radiomics", exc)
            continue

    decision("partial" if failed_labels else ("success" if extracted_any else "empty_label"))
    if not extracted_any and minimum_voxels > 0:
        return row if any(key.endswith("_voxel_count") for key in row) else None
    return row


def _resolve_cases(
    cohort_folder_or_cases: str | Path | Iterable[str | Path],
    *,
    segmentation_filename: str | Path,
) -> list[Path]:
    if isinstance(cohort_folder_or_cases, (str, Path)):
        path = Path(cohort_folder_or_cases)
        if path.is_dir() and (path / segmentation_filename).exists():
            return [path]
        if path.is_dir():
            return discover_boa_radiomics_cases(path, segmentation_filename=segmentation_filename)
        return [path]
    return [Path(case) for case in cohort_folder_or_cases]


def _process_cases(
    cases: Sequence[Path],
    worker: Any,
    *,
    num_workers: int,
    show_progress: bool,
) -> list[dict[str, Any] | None]:
    if num_workers <= 1:
        iterator: Iterable[dict[str, Any] | None] = (worker(case) for case in cases)
        if show_progress:
            iterator = tqdm(iterator, total=len(cases))
        return list(iterator)

    with multiprocessing.Pool(num_workers) as pool:
        iterator = pool.imap_unordered(worker, cases)
        if show_progress:
            iterator = tqdm(iterator, total=len(cases))
        return list(iterator)


def extract_boa_radiomics_features(
    cohort_folder_or_cases: str | Path | Iterable[str | Path],
    *,
    image_filename: str | Path | Sequence[str | Path] = DEFAULT_IMAGE_FILENAMES,
    segmentation_kind: SegmentationKind = "total",
    segmentation_filename: str | Path | None = None,
    labels: Mapping[str, int] | Sequence[int] | None = None,
    extractor_settings: Mapping[str, Any] | None = None,
    feature_prefix: str = "radiomics",
    include_paths: bool = True,
    exclude_diagnostics: bool = True,
    minimum_voxels: int = 1,
    resample_mask: bool = True,
    on_error: OnError = "skip",
    num_workers: int = 1,
    show_progress: bool = True,
    return_report: bool = False,
) -> pd.DataFrame | dict[str, Any]:
    """Extract BOA radiomics features for a cohort of patient folders.

    Parameters
    ----------
    cohort_folder_or_cases:
        Case path, cohort directory, or iterable of case paths; names must be unique.
    image_filename:
        Image filename or ordered candidate filenames.
    segmentation_kind:
        Label convention: total or body_regions.
    segmentation_filename:
        Explicit mask filename; defaults to the selected convention.
    labels:
        Mapping of label names to integer values, or a sequence of integers.
    extractor_settings:
        Settings passed to the PyRadiomics extractor.
    feature_prefix:
        Prefix for extracted feature columns.
    include_paths:
        Include sensitive source paths in the feature table.
    exclude_diagnostics:
        Omit PyRadiomics diagnostic feature columns.
    minimum_voxels:
        Skip feature extraction for masks smaller than this voxel count.
    resample_mask:
        Resample masks to the image grid when needed; this is not registration.
    on_error:
        Use skip to retain partial results, or raise to propagate extraction failures.
    num_workers:
        Number of extraction processes; use one for sequential execution.
    show_progress:
        Display completed case progress.
    return_report:
        If True, return data plus rows and summary report tables; otherwise return the DataFrame.

    Returns
    -------
    DataFrame or dict
        Feature data, optionally wrapped with case/label decision reports.
    """

    if segmentation_filename is None:
        segmentation_filename = DEFAULT_SEGMENTATION_FILENAMES[segmentation_kind]
    cases = _resolve_cases(cohort_folder_or_cases, segmentation_filename=segmentation_filename)
    validate_cases(cases)
    worker = partial(
        extract_case_radiomics_features,
        image_filename=image_filename,
        segmentation_kind=segmentation_kind,
        segmentation_filename=segmentation_filename,
        labels=labels,
        extractor_settings=extractor_settings,
        feature_prefix=feature_prefix,
        include_paths=include_paths,
        exclude_diagnostics=exclude_diagnostics,
        minimum_voxels=minimum_voxels,
        resample_mask=resample_mask,
        on_error=on_error,
    )
    worker = partial(case_result, extractor=worker, family="radiomics", kwargs={})
    rows = _process_cases(cases, worker, num_workers=num_workers, show_progress=show_progress)
    return collect_results(rows, return_report)
