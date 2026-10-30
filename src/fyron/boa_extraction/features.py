"""Extract tabular features from Body-and-Organ-Analysis output folders."""

from __future__ import annotations

import json
from .._extraction_report import (
    decision, case_result, validate_cases, feature_status, collect_results, report_result,
)
import multiprocessing
from collections.abc import Iterable, Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm
from .._boa_labels import TISSUE_LABELS


BODY_REGIONS = ("abdominal_cavity", "thoracic_cavity", "ventral_cavity", "l1", "l2", "l3", "l4", "l5")
TISSUES = ("bone", "muscle", "tat", "imat", "eat", "pat", "vat", "sat")
VERTEBRAE = tuple(f"l{i}" for i in range(1, 7)) + tuple(f"t{i}" for i in range(1, 13))
DEFAULT_BODY_REGION_DERIVED_MARKERS = (
    {
        "name": "sarcopenia_index_si",
        "numerator": "muscle",
        "denominator": "bone",
        "regions": None,
    },
    {
        "name": "myosteatosis_fat_index_mfi",
        "numerator": "imat",
        "denominator": "tat",
        "regions": None,
        "multiplier": 100.0,
    },
    {
        "name": "visceral_fat_index_vfi",
        "numerator": "vat",
        "denominator": "sat",
        "regions": ("abdominal_cavity",),
    },
    {
        "name": "eat_pat_ratio",
        "numerator": "eat",
        "denominator": "pat",
        "regions": ("thoracic_cavity", "ventral_cavity"),
    },
)
DEFAULT_VERTEBRAL_SLICE_LABELS = {
    "sma": TISSUE_LABELS["muscle"],
    "imat": TISSUE_LABELS["imat"],
    "vat": TISSUE_LABELS["vat"],
    "sat": TISSUE_LABELS["sat"],
}
TOTAL_LABELS = {
    "spleen": 1,
    "kidney_right": 2,
    "kidney_left": 3,
    "liver": 5,
    "stomach": 6,
    "pancreas": 10,
    "lung_upper_lobe_left": 13,
    "lung_lower_lobe_left": 14,
    "lung_upper_lobe_right": 15,
    "lung_middle_lobe_right": 16,
    "lung_lower_lobe_right": 17,
    "vertebrae_L1": 22,
    "vertebrae_L3": 20,
    "vertebrae_L5": 18,
    "vertebrae_T1": 34,
    "vertebrae_T4": 31,
}
TOTAL_RATIOS = (("spleen", "liver"),)


def read_json_file(file_path: str | Path) -> dict[str, Any] | list[Any]:
    """Read a JSON file and return parsed content.

    Parameters
    ----------
    file_path:
        JSON file path.

    Returns
    -------
    dict or list
        Parsed JSON content.

    Raises
    ------
    ValueError
        If the file cannot be decoded as JSON.
    OSError
        If the file cannot be opened.
    """

    path = Path(file_path)
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not decode JSON file: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"Could not read JSON file as UTF-8: {path}") from exc


def discover_boa_cases(
    cohort_folder: str | Path,
    *,
    measurement_filename: str = "bca-measurements.json",
) -> list[Path]:
    """Discover BOA patient folders below a cohort directory.

    Parameters
    ----------
    cohort_folder:
        Root folder containing patient subfolders such as ``patient0001``.
    measurement_filename:
        File used to identify completed BOA cases.

    Returns
    -------
    list[pathlib.Path]
        Sorted patient folders that contain the measurement file.
    """

    root = Path(cohort_folder)
    measurement_paths = sorted(root.rglob(measurement_filename))
    return [path.parent for path in measurement_paths]


def _nested_get(data: Mapping[str, Any], keys: Sequence[str]) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _load_nifti_array(path: Path) -> tuple[np.ndarray, tuple[float, float, float]]:
    try:
        import SimpleITK as sitk
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "BOA SMA extraction requires SimpleITK. "
            "Install Fyron with imaging support or install SimpleITK."
        ) from exc

    image = sitk.ReadImage(str(path))
    array = sitk.GetArrayFromImage(image)
    return array, tuple(float(value) for value in image.GetSpacing())


def extract_body_region_features(
    case_folder_or_measurements: str | Path,
    *,
    body_regions: Sequence[str] = BODY_REGIONS,
    tissues: Sequence[str] = TISSUES,
    vertebrae: Sequence[str] = VERTEBRAE,
    measurement_filename: str = "bca-measurements.json",
    sma_segmentation_filename: str | Sequence[str] = ("tissues.nii.gz",),
    sma_label: int | None = None,
    slice_levels: Sequence[str] = ("l3",),
    slice_tissue_labels: Mapping[str, int] | None = None,
    height_m: float | None = None,
    include_derived_markers: bool = True,
    derived_markers: Sequence[Mapping[str, Any]] = DEFAULT_BODY_REGION_DERIVED_MARKERS,
    download_id: str | None = None,
    include_sma: bool = True,
    missing_value: float | None = np.nan,
) -> dict[str, Any] | None:
    """Extract body-region tissue volumes and vertebral SMA features.

    Parameters
    ----------
    case_folder_or_measurements:
        Patient folder or path to ``bca-measurements.json``.
    body_regions:
        Body-region keys expected in the BOA aggregated measurements.
    tissues:
        Tissue keys read from ``measurements_no_extremities``.
    vertebrae:
        Vertebral level keys used to select the middle axial slice.
    measurement_filename:
        Measurement filename when a patient folder is passed.
    sma_segmentation_filename:
        Segmentation file used for skeletal muscle area calculation. Pass a
        sequence to try multiple filenames in order.
    sma_label:
        Explicit muscle label override. By default, use label 1 in BOA tissues.
        Custom masks require explicit labels; anatomical body-region masks are
        not a substitute for HU-filtered tissue masks.
    slice_levels:
        Vertebral levels used for richer axial area markers, e.g. ``("l3",)``.
    slice_tissue_labels:
        Mapping from marker names to segmentation label values. Defaults to
        ``{"sma": 1, "imat": 5, "vat": 4, "sat": 3}`` for ``tissues.nii.gz``.
        For other filenames, only explicitly supplied labels are measured.
    height_m:
        Optional patient height in meters. Area-based ``smi``, ``imati``,
        ``vati``, and ``sati`` do not require height. When height is provided,
        additional ``*_cm2_per_m2`` columns are calculated.
    include_derived_markers:
        Calculate body-region volume ratios such as muscle/bone and IMAT/TAT.
    derived_markers:
        Marker definitions with ``name``, ``numerator``, ``denominator``, and
        optional ``regions`` keys.
    download_id:
        Optional explicit case identifier. Defaults to the patient folder name.
    include_sma:
        Calculate ``<vertebra>_sma`` when the segmentation file is present.
    missing_value:
        Value used when a measurement key is missing.

    Returns
    -------
    dict or None
        One row of features. ``None`` is returned when the JSON file is missing
        or malformed.
    """

    input_path = Path(case_folder_or_measurements)
    measurement_path = input_path if input_path.is_file() else input_path / measurement_filename
    case_folder = measurement_path.parent

    if not measurement_path.exists():
        decision("missing_inputs")
        return None

    try:
        data = read_json_file(measurement_path)
    except (OSError, ValueError):
        decision("invalid_measurements")
        return None
    if not isinstance(data, Mapping):
        decision("invalid_measurements")
        return None

    row: dict[str, Any] = {"download_id": download_id or case_folder.name}
    aggregated = data.get("aggregated")
    if not isinstance(aggregated, Mapping):
        decision("invalid_measurements")
        return None

    for body_region in body_regions:
        for tissue in tissues:
            value = _nested_get(
                aggregated,
                [body_region, "measurements_no_extremities", tissue, "sum"],
            )
            row[f"{body_region}_{tissue}_sum_ml"] = missing_value if value is None else value

    if include_derived_markers:
        row.update(
            _extract_body_region_derived_markers(
                row,
                body_regions=body_regions,
                derived_markers=derived_markers,
                missing_value=missing_value,
            )
        )

    if include_sma:
        marker_labels = dict(slice_tissue_labels or {})
        if sma_label is not None:
            marker_labels.setdefault("sma", sma_label)
        row.update(
            _extract_vertebral_slice_markers(
                case_folder,
                aggregated,
                vertebrae=vertebrae,
                slice_levels=slice_levels,
                segmentation_filename=sma_segmentation_filename,
                tissue_labels=marker_labels,
                height_m=height_m,
                missing_value=missing_value,
            )
        )

    decision(feature_status(row, missing_value))
    return row


def _extract_body_region_derived_markers(
    row: Mapping[str, Any],
    *,
    body_regions: Sequence[str],
    derived_markers: Sequence[Mapping[str, Any]],
    missing_value: float | None,
) -> dict[str, Any]:
    features: dict[str, Any] = {}
    active_regions = set(body_regions)
    for marker in derived_markers:
        name = marker.get("name")
        numerator = marker.get("numerator")
        denominator = marker.get("denominator")
        if not name or not numerator or not denominator:
            continue
        regions = marker.get("regions")
        if regions is None:
            marker_regions = body_regions
        else:
            marker_regions = [region for region in regions if region in active_regions]
        for region in marker_regions:
            numerator_value = row.get(f"{region}_{numerator}_sum_ml")
            denominator_value = row.get(f"{region}_{denominator}_sum_ml")
            value = _safe_ratio(
                numerator_value,
                denominator_value,
                round_digits=None,
                missing_value=missing_value,
            )
            multiplier = marker.get("multiplier", 1.0)
            if not _matches_missing_value(value, missing_value):
                try:
                    value = float(value) * float(multiplier)
                except (TypeError, ValueError):
                    value = missing_value
            features[f"{region}_{name}"] = value
    return features


def _matches_missing_value(value: Any, missing_value: float | None) -> bool:
    if value is missing_value:
        return True
    if value is None or missing_value is None:
        return value is None and missing_value is None
    try:
        value_float = float(value)
        missing_float = float(missing_value)
    except (TypeError, ValueError):
        return value == missing_value
    if np.isnan(value_float) and np.isnan(missing_float):
        return True
    return value == missing_value


def _extract_vertebral_slice_markers(
    case_folder: Path,
    aggregated: Mapping[str, Any],
    *,
    vertebrae: Sequence[str],
    slice_levels: Sequence[str],
    segmentation_filename: str | Sequence[str],
    tissue_labels: Mapping[str, int],
    height_m: float | None,
    missing_value: float | None,
) -> dict[str, Any]:
    features = {f"{vertebra}_sma": missing_value for vertebra in vertebrae}
    normalized_levels = tuple(level.lower() for level in slice_levels)
    for level in normalized_levels:
        features[f"{level}_sma_cm2"] = missing_value
        for marker in dict.fromkeys([*DEFAULT_VERTEBRAL_SLICE_LABELS, *tissue_labels]):
            if marker == "sma":
                continue
            features[f"{level}_{marker}_area_cm2"] = missing_value
        features[f"{level}_smi"] = missing_value
        features[f"{level}_imati"] = missing_value
        features[f"{level}_vati"] = missing_value
        features[f"{level}_sati"] = missing_value
        if height_m is not None:
            features[f"{level}_smi_cm2_per_m2"] = missing_value
            features[f"{level}_imati_cm2_per_m2"] = missing_value
            features[f"{level}_vati_cm2_per_m2"] = missing_value
            features[f"{level}_sati_cm2_per_m2"] = missing_value

    segmentation_path = _first_existing_path(case_folder, segmentation_filename)
    if segmentation_path is None:
        return features

    if not segmentation_path.exists():
        return features

    if segmentation_path.name in {"tissues.nii.gz", "tissues.nii"}:
        tissue_labels = {**DEFAULT_VERTEBRAL_SLICE_LABELS, **tissue_labels}
    elif not tissue_labels:
        raise ValueError("Custom or body-region masks require explicit slice_tissue_labels or sma_label.")
    if any(isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value <= 0
           for value in tissue_labels.values()):
        raise ValueError("Tissue labels must be positive integers.")

    try:
        segmentation, spacing = _load_nifti_array(segmentation_path)
    except (OSError, RuntimeError, ImportError):
        return features

    if (segmentation.ndim != 3 or len(spacing) != 3 or not np.isfinite(spacing).all()
            or np.any(np.asarray(spacing) <= 0)):
        decision("invalid_measurements", label="slice_geometry")
        return features
    spacing_cm2 = (spacing[0] * spacing[1]) / 100.0
    slice_count = segmentation.shape[0]
    height_m2 = _valid_height_squared(height_m)

    for vertebra in vertebrae:
        metadata = aggregated.get(vertebra)
        if not isinstance(metadata, Mapping):
            continue
        try:
            min_slice = metadata["min_slice_idx"]
            max_slice_idx = metadata["max_slice_idx"]
            if (any(isinstance(value, bool) or not isinstance(value, (int, np.integer))
                    for value in (min_slice, max_slice_idx))
                    or not 0 <= min_slice < max_slice_idx <= slice_count):
                raise ValueError("Invalid vertebral slice range.")
        except (KeyError, TypeError, ValueError):
            decision("invalid_measurements", label=vertebra)
            continue
        slice_index = (min_slice + max_slice_idx) // 2
        slice_data = segmentation[slice_index]
        sma_area = (_label_area_cm2(slice_data, tissue_labels["sma"], spacing_cm2)
                    if "sma" in tissue_labels else missing_value)
        features[f"{vertebra}_sma"] = sma_area
        if vertebra.lower() not in normalized_levels:
            continue
        level = vertebra.lower()
        features[f"{level}_sma_cm2"] = sma_area
        features[f"{level}_smi"] = sma_area
        for marker, label in tissue_labels.items():
            if marker == "sma":
                continue
            features[f"{level}_{marker}_area_cm2"] = _label_area_cm2(
                slice_data,
                label,
                spacing_cm2,
            )
        features[f"{level}_imati"] = features.get(f"{level}_imat_area_cm2", missing_value)
        features[f"{level}_vati"] = features.get(f"{level}_vat_area_cm2", missing_value)
        features[f"{level}_sati"] = features.get(f"{level}_sat_area_cm2", missing_value)
        if height_m2 is not None:
            features[f"{level}_smi_cm2_per_m2"] = _safe_ratio(sma_area, height_m2, None, missing_value)
            features[f"{level}_imati_cm2_per_m2"] = _safe_ratio(
                features.get(f"{level}_imat_area_cm2"),
                height_m2,
                None,
                missing_value,
            )
            features[f"{level}_vati_cm2_per_m2"] = _safe_ratio(
                features.get(f"{level}_vat_area_cm2"),
                height_m2,
                None,
                missing_value,
            )
            features[f"{level}_sati_cm2_per_m2"] = _safe_ratio(
                features.get(f"{level}_sat_area_cm2"),
                height_m2,
                None,
                missing_value,
            )

    return features


def _label_area_cm2(slice_data: np.ndarray, label: int, spacing_cm2: float) -> float:
    return float(np.sum(slice_data == label) * spacing_cm2)


def _valid_height_squared(height_m: float | None) -> float | None:
    if height_m is None:
        return None
    try:
        value = float(height_m)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(value) or value <= 0:
        return None
    return value * value


def _first_existing_path(case_folder: Path, filenames: str | Sequence[str]) -> Path | None:
    if isinstance(filenames, str):
        return case_folder / filenames
    for filename in filenames:
        path = case_folder / filename
        if path.exists():
            return path
    return None


def extract_total_segmentation_features(
    case_folder: str | Path,
    *,
    labels: Mapping[str, int] = TOTAL_LABELS,
    ratios: Sequence[tuple[str, str]] = TOTAL_RATIOS,
    measurement_filename: str = "total-measurements.json",
    download_id: str | None = None,
    round_digits: int | None = 2,
    missing_value: float | None = np.nan,
) -> dict[str, Any] | None:
    """Extract organ volume, HU, CNR, and ratio features from total measurements.

    Parameters
    ----------
    case_folder:
        Patient folder containing ``total-measurements.json``.
    labels:
        Organ labels to extract from ``segmentations.total``.
    ratios:
        Organ volume ratios to compute as ``organ_a / organ_b``.
    measurement_filename:
        Total segmentation measurements filename.
    download_id:
        Optional explicit case identifier. Defaults to the patient folder name.
    round_digits:
        Number of digits used for rounded numeric features. Set to ``None`` to
        keep original precision.
    missing_value:
        Value used when a metric or organ is missing.

    Returns
    -------
    dict or None
        One row of total-segmentation features, or ``None`` when no valid JSON
        is available.
    """

    case_path = Path(case_folder)
    measurement_path = case_path / measurement_filename
    if not measurement_path.exists():
        decision("missing_inputs")
        return None

    try:
        data = read_json_file(measurement_path)
    except (OSError, ValueError):
        decision("invalid_measurements")
        return None
    if not isinstance(data, Mapping):
        decision("invalid_measurements")
        return None

    total = _nested_get(data, ["segmentations", "total"])
    if not isinstance(total, Mapping):
        decision("invalid_measurements")
        return None

    row: dict[str, Any] = {"download_id": download_id or case_path.name}

    for label in labels:
        metrics = total.get(label)
        if not isinstance(metrics, Mapping):
            row[f"{label}_cnr"] = missing_value
            row[f"{label}_total"] = missing_value
            row[f"{label}_hu"] = missing_value
            continue
        row[f"{label}_cnr"] = _maybe_round(metrics.get("cnr", missing_value), round_digits)
        row[f"{label}_total"] = _maybe_round(metrics.get("volume_ml", missing_value), round_digits)
        row[f"{label}_hu"] = _maybe_round(metrics.get("mean_hu", missing_value), round_digits)

    for organ_a, organ_b in ratios:
        numerator = _nested_get(total, [organ_a, "volume_ml"])
        denominator = _nested_get(total, [organ_b, "volume_ml"])
        row[f"{organ_a}_{organ_b}_ratio"] = _safe_ratio(numerator, denominator, round_digits, missing_value)

    decision(feature_status(row, missing_value))
    return row


def _maybe_round(value: Any, round_digits: int | None) -> Any:
    if value is None:
        return np.nan
    if round_digits is None:
        return value
    try:
        return round(float(value), round_digits)
    except (TypeError, ValueError):
        return value


def _safe_ratio(
    numerator: Any,
    denominator: Any,
    round_digits: int | None,
    missing_value: float | None,
) -> float | None:
    try:
        numerator_value = float(numerator)
        denominator_value = float(denominator)
    except (TypeError, ValueError):
        return missing_value
    if not np.isfinite(numerator_value) or not np.isfinite(denominator_value):
        return missing_value
    if denominator_value == 0:
        return missing_value
    ratio = numerator_value / denominator_value
    return ratio if round_digits is None else round(ratio, round_digits)


def extract_cohort_body_region_features(
    cohort_folder_or_cases: str | Path | Iterable[str | Path],
    *,
    num_workers: int = 1,
    show_progress: bool = True,
    measurement_filename: str = "bca-measurements.json",
    return_report: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | dict[str, Any]:
    """Extract body-region features for all completed BOA cases in a cohort.

    Parameters
    ----------
    cohort_folder_or_cases:
        Case path, cohort directory, or iterable of case paths; names must be unique.
    num_workers:
        Number of extraction processes; use one for sequential execution.
    show_progress:
        Display completed case progress.
    measurement_filename:
        Measurement JSON filename used for discovery and extraction.
    return_report:
        If True, return data plus rows and summary report tables; otherwise return the DataFrame.
    kwargs:
        Additional keyword arguments passed to the corresponding single-case extractor.

    Returns
    -------
    DataFrame or dict
        Feature data, optionally wrapped with case/label decision reports.
    """

    cases = _resolve_cases(cohort_folder_or_cases, measurement_filename=measurement_filename)
    validate_cases(cases)
    worker = partial(case_result, extractor=extract_body_region_features, family="body_regions",
                     kwargs={"measurement_filename": measurement_filename, **kwargs})
    rows = _process_cases(cases, worker, num_workers=num_workers, show_progress=show_progress)
    return collect_results(rows, return_report)


def extract_cohort_total_features(
    cohort_folder_or_cases: str | Path | Iterable[str | Path],
    *,
    num_workers: int = 1,
    show_progress: bool = True,
    measurement_filename: str = "total-measurements.json",
    return_report: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | dict[str, Any]:
    """Extract total-segmentation features for all BOA cases in a cohort.

    Parameters
    ----------
    cohort_folder_or_cases:
        Case path, cohort directory, or iterable of case paths; names must be unique.
    num_workers:
        Number of extraction processes; use one for sequential execution.
    show_progress:
        Display completed case progress.
    measurement_filename:
        Measurement JSON filename used for discovery and extraction.
    return_report:
        If True, return data plus rows and summary report tables; otherwise return the DataFrame.
    kwargs:
        Additional keyword arguments passed to the corresponding single-case extractor.

    Returns
    -------
    DataFrame or dict
        Feature data, optionally wrapped with case/label decision reports.
    """

    cases = _resolve_cases(cohort_folder_or_cases, measurement_filename=measurement_filename)
    validate_cases(cases)
    worker = partial(case_result, extractor=extract_total_segmentation_features, family="total",
                     kwargs={"measurement_filename": measurement_filename, **kwargs})
    rows = _process_cases(cases, worker, num_workers=num_workers, show_progress=show_progress)
    return collect_results(rows, return_report)


def extract_boa_features(
    cohort_folder_or_cases: str | Path | Iterable[str | Path],
    *,
    include_body_regions: bool = True,
    include_total: bool = True,
    num_workers: int = 1,
    show_progress: bool = True,
    body_region_kwargs: Mapping[str, Any] | None = None,
    total_kwargs: Mapping[str, Any] | None = None,
    return_report: bool = False,
) -> pd.DataFrame | dict[str, Any]:
    """Extract and merge available BOA feature families by ``download_id``.

    Parameters
    ----------
    cohort_folder_or_cases:
        Case path, cohort directory, or iterable of case paths; names must be unique.
    include_body_regions:
        Include body-composition measurements.
    include_total:
        Include total-organ measurements.
    num_workers:
        Number of extraction processes; use one for sequential execution.
    show_progress:
        Display completed case progress.
    body_region_kwargs:
        Options forwarded to body-region extraction.
    total_kwargs:
        Options forwarded to total-organ extraction.
    return_report:
        If True, return data plus rows and summary report tables; otherwise return the DataFrame.

    Returns
    -------
    DataFrame or dict
        Feature data, optionally wrapped with case/label decision reports.
    """

    families = []
    if include_body_regions:
        families.append((extract_cohort_body_region_features, dict(body_region_kwargs or {}), "bca-measurements.json"))
    if include_total:
        families.append((extract_cohort_total_features, dict(total_kwargs or {}), "total-measurements.json"))
    if isinstance(cohort_folder_or_cases, (str, Path)):
        cases = sorted(set(case for _, kwargs, filename in families for case in _resolve_cases(
            cohort_folder_or_cases, measurement_filename=kwargs.get("measurement_filename", filename))))
    else:
        cases = [Path(case) for case in cohort_folder_or_cases]
    validate_cases(cases)
    frames, reports = [], []
    for extractor, kwargs, _ in families:
        kwargs.pop("return_report", None)
        result = extractor(cases, num_workers=num_workers, show_progress=show_progress,
                           return_report=True, **kwargs)
        if not result["data"].empty:
            frames.append(result["data"])
        reports.extend(result["report"]["rows"].to_dict("records"))
    merged = frames[0] if frames else pd.DataFrame()
    for frame in frames[1:]:
        merged = merged.merge(frame, on="download_id", how="outer", validate="one_to_one")
    return report_result(merged, reports, return_report)


def _resolve_cases(
    cohort_folder_or_cases: str | Path | Iterable[str | Path],
    *,
    measurement_filename: str,
) -> list[Path]:
    if isinstance(cohort_folder_or_cases, (str, Path)):
        path = Path(cohort_folder_or_cases)
        if path.is_dir() and (path / measurement_filename).exists():
            return [path]
        if path.is_dir():
            return discover_boa_cases(path, measurement_filename=measurement_filename)
        return [path.parent if path.name == measurement_filename else path]

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
