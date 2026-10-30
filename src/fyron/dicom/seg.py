"""DICOM SEG export helpers."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Sequence, Union

import numpy as np
import pydicom
from pydicom.uid import SegmentationStorage, generate_uid

StrPath = Union[str, Path]


def load_source_dicom_series(source_dicom_dir: StrPath, sort_by: str = "geometry") -> list[pydicom.Dataset]:
    """Load source DICOM slices from a directory in deterministic SEG order.

    Parameters
    ----------
    source_dicom_dir:
        Directory containing source ``.dcm`` files.
    sort_by:
        ``"geometry"`` sorts by ``ImagePositionPatient`` when available,
        falling back to ``InstanceNumber`` and then path. ``"instance"`` and
        ``"path"`` are also supported for explicit workflows.
    """
    root = Path(source_dicom_dir)
    if not root.exists():
        raise FileNotFoundError(f"source_dicom_dir does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"source_dicom_dir must be a directory, got: {root}")
    if sort_by not in {"geometry", "instance", "path"}:
        raise ValueError("sort_by must be one of: 'geometry', 'instance', 'path'")

    paths = sorted(root.rglob("*.dcm"))
    if not paths:
        raise ValueError(f"No .dcm files found under {root}")

    items = [(path, pydicom.dcmread(str(path), stop_before_pixels=False)) for path in paths]
    if sort_by == "path":
        return [dataset for _, dataset in items]
    if sort_by == "instance":
        items.sort(key=lambda item: (_instance_number(item[1]), str(item[0])))
    else:
        items.sort(key=lambda item: (_geometry_position(item[1]), _instance_number(item[1]), str(item[0])))
    return [dataset for _, dataset in items]


def read_segment_descriptions(path: StrPath) -> list[dict[str, Any]]:
    """Read and validate a JSON list of DICOM SEG segment descriptions."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_segment_descriptions(payload)


def validate_segment_descriptions(segment_descriptions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and normalize DICOM SEG segment description dictionaries."""
    if not isinstance(segment_descriptions, Sequence) or isinstance(segment_descriptions, (str, bytes)):
        raise ValueError("segment_descriptions must be a non-empty sequence of dictionaries")
    if not segment_descriptions:
        raise ValueError("segment_descriptions must contain at least one segment")

    normalized: list[dict[str, Any]] = []
    segment_numbers: set[int] = set()
    label_values: set[int] = set()
    for index, spec in enumerate(segment_descriptions, start=1):
        if not isinstance(spec, dict):
            raise ValueError(f"segment_descriptions[{index - 1}] must be a dictionary")
        label = str(spec.get("label", "")).strip()
        if not label:
            raise ValueError(f"segment_descriptions[{index - 1}] must define a non-empty 'label'")

        if "segment_number" in spec:
            number = int(spec["segment_number"])
            if number in segment_numbers:
                raise ValueError(f"Duplicate segment_number: {number}")
            segment_numbers.add(number)

        if "label_value" in spec:
            label_value = int(spec["label_value"])
            if label_value in label_values:
                raise ValueError(f"Duplicate label_value: {label_value}")
            label_values.add(label_value)

        for key in ("category", "type"):
            if key in spec:
                _validate_coded_concept_shape(spec[key], f"segment_descriptions[{index - 1}].{key}")
        normalized.append(dict(spec))
    return normalized


def label_map_to_segments(label_map: np.ndarray, labels: Sequence[int]) -> np.ndarray:
    """Convert an integer label map to a binary segment stack.

    Parameters
    ----------
    label_map:
        Array in ``(z, y, x)`` order.
    labels:
        Integer label values to convert.

    Returns
    -------
    numpy.ndarray
        Boolean array in ``(segment, z, y, x)`` order.
    """
    arr = np.asarray(label_map)
    if arr.ndim != 3:
        raise ValueError(f"label_map must be 3D in (z, y, x) order, got shape {arr.shape}")
    if not labels:
        raise ValueError("labels must contain at least one label value")
    return np.stack([(arr == int(label)) for label in labels], axis=0).astype(bool)


def write_dicom_seg(
    mask: np.ndarray,
    source_images: Sequence[pydicom.Dataset | StrPath],
    output_path: StrPath,
    segment_descriptions: Sequence[dict[str, Any]],
    *,
    series_description: str = "Fyron DICOM SEG",
    manufacturer: str = "Bits & Flames",
    algorithm_type: str = "AUTOMATIC",
    algorithm_name: str = "Fyron",
) -> Path:
    """Write a standards-oriented DICOM SEG object using highdicom.

    ``source_images`` are required because DICOM SEG objects reference the
    original image series and frame of reference.
    """
    segment_descriptions = validate_segment_descriptions(segment_descriptions)
    src = _load_source_images(source_images)
    if not src:
        raise ValueError("source_images must contain at least one DICOM dataset or file path")

    segments = _normalise_mask(mask, segment_descriptions)
    _validate_mask_source_alignment(segments, src)
    highdicom = _require_highdicom()
    pixel_array = np.moveaxis(segments, 0, -1).astype(np.uint8)
    if pixel_array.shape[-1] == 1:
        pixel_array = pixel_array[..., 0]

    descriptions = [
        _make_highdicom_segment_description(
            highdicom,
            spec,
            index=index,
            algorithm_type=algorithm_type,
            algorithm_name=algorithm_name,
        )
        for index, spec in enumerate(segment_descriptions, start=1)
    ]

    seg = highdicom.seg.Segmentation(
        source_images=src,
        pixel_array=pixel_array,
        segmentation_type=highdicom.seg.SegmentationTypeValues.BINARY,
        segment_descriptions=descriptions,
        series_instance_uid=generate_uid(),
        series_number=9001,
        sop_instance_uid=generate_uid(),
        instance_number=1,
        manufacturer=manufacturer,
        manufacturer_model_name="Fyron",
        software_versions=_fyron_version(),
        device_serial_number="fyron",
        series_description=series_description,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    seg.save_as(str(out))
    return out.resolve()


def validate_dicom_seg(path: StrPath, source_images: Sequence[pydicom.Dataset | StrPath] | None = None) -> dict[str, Any]:
    """Read a DICOM SEG and return lightweight validation metadata."""
    ds = pydicom.dcmread(str(path), stop_before_pixels=True)
    if getattr(ds, "Modality", None) != "SEG":
        raise ValueError(f"Expected Modality SEG, got {getattr(ds, 'Modality', None)!r}")
    if str(getattr(ds, "SOPClassUID", "")) != str(SegmentationStorage):
        raise ValueError("DICOM object is not Segmentation Storage")

    source_count = None
    if source_images is not None:
        source_count = len(_load_source_images(source_images))

    return {
        "path": str(Path(path).resolve()),
        "modality": ds.Modality,
        "sop_class_uid": str(ds.SOPClassUID),
        "sop_instance_uid": str(ds.SOPInstanceUID),
        "series_instance_uid": str(ds.SeriesInstanceUID),
        "series_description": str(getattr(ds, "SeriesDescription", "")),
        "manufacturer": str(getattr(ds, "Manufacturer", "")),
        "software_versions": str(getattr(ds, "SoftwareVersions", "")),
        "number_of_segments": len(getattr(ds, "SegmentSequence", [])),
        "referenced_source_images": source_count,
        "segment_labels": [
            str(getattr(item, "SegmentLabel", ""))
            for item in getattr(ds, "SegmentSequence", [])
        ],
        "segment_numbers": [
            int(getattr(item, "SegmentNumber", 0))
            for item in getattr(ds, "SegmentSequence", [])
        ],
    }


def summarize_dicom_seg(path: StrPath, source_images: Sequence[pydicom.Dataset | StrPath] | None = None) -> dict[str, Any]:
    """Return a lightweight metadata summary for a DICOM SEG object."""
    return validate_dicom_seg(path, source_images=source_images)


def _require_highdicom():
    try:
        import highdicom
    except ImportError as exc:
        raise ImportError(
            'DICOM SEG export requires highdicom. Install it with: uv add "fyron[dicom-seg]"'
        ) from exc
    return highdicom


def _load_source_images(source_images: Sequence[pydicom.Dataset | StrPath]) -> list[pydicom.Dataset]:
    return [
        item if isinstance(item, pydicom.Dataset) else pydicom.dcmread(str(item), stop_before_pixels=False)
        for item in source_images
    ]


def _normalise_mask(mask: np.ndarray, segment_descriptions: Sequence[dict[str, Any]]) -> np.ndarray:
    arr = np.asarray(mask)
    if arr.ndim == 3:
        labels = [spec.get("label_value", index) for index, spec in enumerate(segment_descriptions, start=1)]
        arr = label_map_to_segments(arr, labels)
    elif arr.ndim == 4:
        pass
    else:
        raise ValueError("mask must be a 3D label map or 4D binary stack in (segment, z, y, x) order")

    if arr.shape[0] != len(segment_descriptions):
        raise ValueError("Number of mask segments must match segment_descriptions")
    return arr.astype(bool)


def _validate_mask_source_alignment(segments: np.ndarray, source_images: Sequence[pydicom.Dataset]) -> None:
    if segments.ndim != 4:
        raise ValueError("Normalized SEG mask must be 4D in (segment, z, y, x) order")
    if segments.shape[1] != len(source_images):
        raise ValueError(
            f"Mask slice count ({segments.shape[1]}) must match source image count ({len(source_images)})"
        )
    rows = int(getattr(source_images[0], "Rows", segments.shape[2]))
    cols = int(getattr(source_images[0], "Columns", segments.shape[3]))
    if segments.shape[2:] != (rows, cols):
        raise ValueError(
            f"Mask in-plane shape {segments.shape[2:]} must match source image rows/columns {(rows, cols)}"
        )


def _make_highdicom_segment_description(
    highdicom,
    spec: dict[str, Any],
    *,
    index: int,
    algorithm_type: str,
    algorithm_name: str,
):
    code = highdicom.sr.CodedConcept
    category = _coded_concept(code, spec.get("category", ("T-D0050", "SRT", "Tissue")))
    property_type = _coded_concept(code, spec.get("type", ("T-D0050", "SRT", spec.get("label", f"Segment {index}"))))
    algorithm = highdicom.AlgorithmIdentificationSequence(
        name=str(spec.get("algorithm_name", algorithm_name)),
        version=str(spec.get("algorithm_version", "unknown")),
        family=code("99FYRON", "99FYRON", "Fyron"),
    )
    return highdicom.seg.SegmentDescription(
        segment_number=int(spec.get("segment_number", index)),
        segment_label=str(spec.get("label", f"Segment {index}")),
        segmented_property_category=category,
        segmented_property_type=property_type,
        algorithm_type=highdicom.seg.SegmentAlgorithmTypeValues(str(spec.get("algorithm_type", algorithm_type))),
        algorithm_identification=algorithm,
    )


def _coded_concept(constructor, value: Any):
    if isinstance(value, dict):
        return constructor(
            value=str(value["value"]),
            scheme_designator=str(value["scheme_designator"]),
            meaning=str(value["meaning"]),
        )
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return constructor(str(value[0]), str(value[1]), str(value[2]))
    return value


def _validate_coded_concept_shape(value: Any, name: str) -> None:
    if isinstance(value, dict):
        missing = {"value", "scheme_designator", "meaning"} - set(value)
        if missing:
            raise ValueError(f"{name} coded concept is missing keys: {sorted(missing)}")
        return
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return
    if all(hasattr(value, attr) for attr in ("CodeValue", "CodingSchemeDesignator", "CodeMeaning")):
        return
    raise ValueError(f"{name} must be a dict or 3-item tuple/list coded concept")


def _geometry_position(dataset: pydicom.Dataset) -> tuple[int, float]:
    position = getattr(dataset, "ImagePositionPatient", None)
    if position is None or len(position) < 3:
        return (1, 0.0)
    try:
        return (0, float(position[2]))
    except (TypeError, ValueError):
        return (1, 0.0)


def _instance_number(dataset: pydicom.Dataset) -> tuple[int, int]:
    try:
        return (0, int(getattr(dataset, "InstanceNumber")))
    except (TypeError, ValueError):
        return (1, 0)


def _fyron_version() -> str:
    try:
        return version("fyron")
    except PackageNotFoundError:
        return "0.3.2"
