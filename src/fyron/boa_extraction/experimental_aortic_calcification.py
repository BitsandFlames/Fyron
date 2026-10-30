"""Experimental aortic calcification features from BOA masks."""

from __future__ import annotations
from .._extraction_report import decision, case_result, validate_cases, collect_results, feature_status

from collections.abc import Iterable, Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fyron.boa_extraction.features import _process_cases

DEFAULT_CT_FILENAMES = ("ct.nii.gz", "CT.nii.gz", "image.nii.gz", "ct.nii", "image.nii")
DEFAULT_AORTA_MASK_FILENAMES = ("aorta.nii.gz",)
DEFAULT_TOTAL_MASK_FILENAMES = ("total.nii.gz",)
DEFAULT_TOTAL_AORTA_LABELS = (52,)
DEFAULT_BODY_REGION_MASK_FILENAME = "body-regions.nii.gz"
DEFAULT_BODY_REGION_LABELS = {
    "thoracic_aorta": 3,
    "abdominal_aorta": 4,
}


def extract_experimental_aortic_calcification_features(
    case_folder_or_masks_dir: str | Path,
    *,
    ct_path: str | Path | None = None,
    masks_dir: str | Path | None = None,
    download_id: str | None = None,
    hu_threshold: float = 130.0,
    prefix: str = "aortic_calcification",
    aorta_mask_filenames: str | Sequence[str] = DEFAULT_AORTA_MASK_FILENAMES,
    total_mask_filenames: str | Sequence[str] = DEFAULT_TOTAL_MASK_FILENAMES,
    total_aorta_labels: Sequence[int] = DEFAULT_TOTAL_AORTA_LABELS,
    thoracic_mask_filename: str = "thoracic_cavity.nii.gz",
    abdominal_mask_filename: str = "abdominal_cavity.nii.gz",
    body_region_mask_filename: str = DEFAULT_BODY_REGION_MASK_FILENAME,
    body_region_labels: Mapping[str, int] | None = DEFAULT_BODY_REGION_LABELS,
    iliac_glob: str = "*iliac*.nii.gz",
    include_iliac: bool = True,
    missing_value: float | None = np.nan,
) -> dict[str, Any] | None:
    """Extract experimental aortic calcification burden from BOA-style masks.

    This API is marked experimental because aortic and iliac mask names differ
    between BOA/TotalSegmentator exports. Keep the defaults inspectable and pass
    explicit filenames or labels for a specific project.

    Parameters
    ----------
    case_folder_or_masks_dir:
        Patient folder or mask folder.
    ct_path:
        CT NIfTI in Hounsfield units. If omitted, common filenames are searched
        in the case folder.
    masks_dir:
        Folder containing BOA masks. Defaults to ``case_folder_or_masks_dir``.
    download_id:
        Optional explicit case identifier. Defaults to the folder name.
    hu_threshold:
        Voxels inside the vascular mask with HU >= this value are counted as
        calcification.
    prefix:
        Prefix for all generated feature columns.
    aorta_mask_filenames:
        Binary aorta mask filenames to try first.
    total_mask_filenames:
        Fallback multiclass total segmentation filenames.
    total_aorta_labels:
        Label values counted as aorta in ``total.nii.gz``. Defaults to ``52``
        and should be verified against the local label map.
    thoracic_mask_filename, abdominal_mask_filename:
        Optional binary body-region masks used to split the aorta.
    body_region_mask_filename:
        Optional multiclass body-region mask fallback.
    body_region_labels:
        Mapping of output region names to labels in ``body_region_mask_filename``.
    iliac_glob:
        Glob used to discover iliac masks for aortoiliac burden.
    include_iliac:
        Whether to include iliac-extension and total-aortoiliac features.
    missing_value:
        Value used for unavailable optional regions.

    Returns
    -------
    dict or None
        One flat feature row, or ``None`` when CT/aorta inputs are unavailable.
    """

    case_path = Path(case_folder_or_masks_dir)
    mask_path = Path(masks_dir) if masks_dir is not None else case_path
    resolved_ct_path = Path(ct_path) if ct_path is not None else _first_existing(mask_path, DEFAULT_CT_FILENAMES)
    if resolved_ct_path is None or not resolved_ct_path.exists():
        resolved_ct_path = _first_existing(case_path, DEFAULT_CT_FILENAMES)
    if resolved_ct_path is None or not resolved_ct_path.exists():
        decision("missing_inputs")
        return None

    try:
        ct, spacing = _load_nifti(resolved_ct_path)
    except (OSError, RuntimeError, ImportError):
        decision("extraction_failure")
        return None

    aorta_mask = _load_aorta_mask(
        mask_path,
        shape=ct.shape,
        aorta_mask_filenames=aorta_mask_filenames,
        total_mask_filenames=total_mask_filenames,
        total_aorta_labels=total_aorta_labels,
    )
    if aorta_mask is None or not np.any(aorta_mask):
        decision("missing_inputs" if aorta_mask is None else "empty_label")
        return None

    voxel_volume_ml = float(np.prod(spacing) / 1000.0)
    row: dict[str, Any] = {"download_id": download_id or case_path.name}
    row.update(
        _calcification_region_features(
            ct,
            aorta_mask,
            voxel_volume_ml=voxel_volume_ml,
            hu_threshold=hu_threshold,
            name=f"{prefix}_total_aorta",
        )
    )

    region_masks = _load_body_region_masks(
        mask_path,
        shape=ct.shape,
        thoracic_mask_filename=thoracic_mask_filename,
        abdominal_mask_filename=abdominal_mask_filename,
        body_region_mask_filename=body_region_mask_filename,
        body_region_labels=body_region_labels,
    )
    for region_name in ("thoracic_aorta", "abdominal_aorta"):
        region_mask = region_masks.get(region_name)
        feature_name = f"{prefix}_{region_name}"
        if region_mask is None:
            row.update(_missing_calcification_features(feature_name, missing_value))
            continue
        row.update(
            _calcification_region_features(
                ct,
                aorta_mask & region_mask,
                voxel_volume_ml=voxel_volume_ml,
                hu_threshold=hu_threshold,
                name=feature_name,
            )
        )

    if include_iliac:
        iliac_mask = _load_iliac_mask(mask_path, shape=ct.shape, iliac_glob=iliac_glob)
        if iliac_mask is None:
            row.update(_missing_calcification_features(f"{prefix}_iliac_extension", missing_value))
            row.update(_missing_calcification_features(f"{prefix}_total_aortoiliac", missing_value))
        else:
            row.update(
                _calcification_region_features(
                    ct,
                    iliac_mask,
                    voxel_volume_ml=voxel_volume_ml,
                    hu_threshold=hu_threshold,
                    name=f"{prefix}_iliac_extension",
                )
            )
            row.update(
                _calcification_region_features(
                    ct,
                    aorta_mask | iliac_mask,
                    voxel_volume_ml=voxel_volume_ml,
                    hu_threshold=hu_threshold,
                    name=f"{prefix}_total_aortoiliac",
                )
            )

    decision(feature_status(row))
    return row


def extract_experimental_cohort_aortic_calcification_features(
    cohort_folder_or_cases: str | Path | Iterable[str | Path],
    *,
    num_workers: int = 1,
    show_progress: bool = True,
    return_report: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | dict[str, Any]:
    """Extract experimental aortic calcification features for many BOA cases.

    Parameters
    ----------
    cohort_folder_or_cases:
        Case path, cohort directory, or iterable of case paths; names must be unique.
    num_workers:
        Number of extraction processes; use one for sequential execution.
    show_progress:
        Display completed case progress.
    return_report:
        If True, return data plus rows and summary report tables; otherwise return the DataFrame.
    kwargs:
        Additional keyword arguments passed to the corresponding single-case extractor.

    Returns
    -------
    DataFrame or dict
        Feature data, optionally wrapped with case/label decision reports.
    """

    cases = _resolve_case_inputs(cohort_folder_or_cases)
    validate_cases(cases)
    worker = partial(case_result, extractor=extract_experimental_aortic_calcification_features,
                     family="aortic_experimental", kwargs=kwargs)
    rows = _process_cases(cases, worker, num_workers=num_workers, show_progress=show_progress)
    return collect_results(rows, return_report)


def _load_nifti(path: Path) -> tuple[np.ndarray, tuple[float, float, float]]:
    try:
        import SimpleITK as sitk
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Experimental aortic calcification extraction requires SimpleITK."
        ) from exc

    image = sitk.ReadImage(str(path))
    array = sitk.GetArrayFromImage(image)
    spacing = tuple(float(value) for value in image.GetSpacing())
    return array, spacing


def _load_aorta_mask(
    masks_dir: Path,
    *,
    shape: tuple[int, ...],
    aorta_mask_filenames: str | Sequence[str],
    total_mask_filenames: str | Sequence[str],
    total_aorta_labels: Sequence[int],
) -> np.ndarray | None:
    aorta_path = _first_existing(masks_dir, aorta_mask_filenames)
    if aorta_path is not None:
        mask = _load_mask(aorta_path, shape=shape)
        return None if mask is None else mask > 0

    total_path = _first_existing(masks_dir, total_mask_filenames)
    if total_path is None:
        return None
    total = _load_mask(total_path, shape=shape)
    if total is None:
        return None
    return np.isin(total, list(total_aorta_labels))


def _load_body_region_masks(
    masks_dir: Path,
    *,
    shape: tuple[int, ...],
    thoracic_mask_filename: str,
    abdominal_mask_filename: str,
    body_region_mask_filename: str,
    body_region_labels: Mapping[str, int] | None,
) -> dict[str, np.ndarray]:
    region_masks: dict[str, np.ndarray] = {}
    direct_masks = {
        "thoracic_aorta": thoracic_mask_filename,
        "abdominal_aorta": abdominal_mask_filename,
    }
    for region_name, filename in direct_masks.items():
        mask = _load_mask(masks_dir / filename, shape=shape)
        if mask is not None:
            region_masks[region_name] = mask > 0

    missing_regions = [name for name in direct_masks if name not in region_masks]
    if missing_regions and body_region_labels:
        body_regions = _load_mask(masks_dir / body_region_mask_filename, shape=shape)
        if body_regions is not None:
            for region_name in missing_regions:
                label = body_region_labels.get(region_name)
                if label is not None:
                    region_masks[region_name] = body_regions == label

    return region_masks


def _load_iliac_mask(
    masks_dir: Path,
    *,
    shape: tuple[int, ...],
    iliac_glob: str,
) -> np.ndarray | None:
    iliac_paths = sorted(path for path in masks_dir.glob(iliac_glob) if path.is_file())
    masks = []
    for path in iliac_paths:
        mask = _load_mask(path, shape=shape)
        if mask is not None:
            masks.append(mask > 0)
    if not masks:
        return None
    return np.logical_or.reduce(masks)


def _load_mask(path: Path, *, shape: tuple[int, ...]) -> np.ndarray | None:
    if not path.exists():
        return None
    try:
        mask, _ = _load_nifti(path)
    except (OSError, RuntimeError, ImportError):
        return None
    if mask.shape != shape:
        raise ValueError(f"Mask shape {mask.shape} does not match CT shape {shape}: {path}")
    return mask


def _calcification_region_features(
    ct: np.ndarray,
    mask: np.ndarray,
    *,
    voxel_volume_ml: float,
    hu_threshold: float,
    name: str,
) -> dict[str, Any]:
    mask = np.asarray(mask, dtype=bool)
    mask_voxel_count = int(np.sum(mask))
    calcification_mask = mask & (ct >= hu_threshold)
    calcified_voxel_count = int(np.sum(calcification_mask))
    calcified_values = ct[calcification_mask]

    return {
        f"{name}_mask_voxel_count": mask_voxel_count,
        f"{name}_mask_volume_ml": mask_voxel_count * voxel_volume_ml,
        f"{name}_calcium_voxel_count": calcified_voxel_count,
        f"{name}_calcified_volume_ml": calcified_voxel_count * voxel_volume_ml,
        f"{name}_calcium_max_hu": float(np.max(calcified_values)) if calcified_voxel_count else np.nan,
        f"{name}_calcium_mean_hu": float(np.mean(calcified_values)) if calcified_voxel_count else np.nan,
        f"{name}_normalized_calcified_volume": (
            calcified_voxel_count / mask_voxel_count if mask_voxel_count else np.nan
        ),
    }


def _missing_calcification_features(name: str, missing_value: float | None) -> dict[str, Any]:
    return {
        f"{name}_mask_voxel_count": missing_value,
        f"{name}_mask_volume_ml": missing_value,
        f"{name}_calcium_voxel_count": missing_value,
        f"{name}_calcified_volume_ml": missing_value,
        f"{name}_calcium_max_hu": missing_value,
        f"{name}_calcium_mean_hu": missing_value,
        f"{name}_normalized_calcified_volume": missing_value,
    }


def _first_existing(folder: Path, filenames: str | Sequence[str]) -> Path | None:
    if isinstance(filenames, str):
        path = folder / filenames
        return path if path.exists() else None
    for filename in filenames:
        path = folder / filename
        if path.exists():
            return path
    return None


def _resolve_case_inputs(cohort_folder_or_cases: str | Path | Iterable[str | Path]) -> list[Path]:
    if isinstance(cohort_folder_or_cases, (str, Path)):
        path = Path(cohort_folder_or_cases)
        if path.is_dir() and any((path / name).exists() for name in DEFAULT_CT_FILENAMES):
            return [path]
        if path.is_dir():
            return sorted(child for child in path.iterdir() if child.is_dir())
        return [path]
    return [Path(case) for case in cohort_folder_or_cases]
