"""Quality-control summaries for local DICOM, NIfTI, and mask data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence, Union

import numpy as np
import pandas as pd
import pydicom
import SimpleITK as sitk

from fyron.imaging.dicom_io import get_dicom_series_ids
from ._spacing import voxel_volume_ml

StrPath = Union[str, Path]


def summarize_dicom_series_geometry(dicom_dir: StrPath, *, recursive: bool = False) -> pd.DataFrame:
    """Summarize DICOM series geometry under a directory."""
    meta = get_dicom_series_ids(dicom_dir, include_metadata=True, recursive=recursive)
    rows: list[dict[str, Any]] = []
    for _, item in meta.iterrows():
        first_file = item.get("first_file")
        row = item.to_dict()
        if first_file:
            try:
                ds = pydicom.dcmread(str(first_file), stop_before_pixels=True)
                row.update(_dicom_geometry_row(ds))
            except Exception:
                row.update(_empty_dicom_geometry())
        else:
            row.update(_empty_dicom_geometry())
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_nifti_geometry(paths: StrPath | Sequence[StrPath]) -> pd.DataFrame:
    """Summarize shape and geometry for one or more NIfTI files."""
    if isinstance(paths, (str, Path)):
        paths = [paths]
    rows = []
    for path in paths:
        p = Path(path)
        image = sitk.ReadImage(str(p))
        arr = sitk.GetArrayFromImage(image)
        spacing = tuple(float(v) for v in image.GetSpacing())
        rows.append(
            {
                "path": str(p),
                "shape_zyx": tuple(int(v) for v in arr.shape),
                "size_xyz": tuple(int(v) for v in image.GetSize()),
                "spacing_xyz": spacing,
                "origin_xyz": tuple(float(v) for v in image.GetOrigin()),
                "direction": tuple(float(v) for v in image.GetDirection()),
                "voxel_volume_ml": voxel_volume_ml(spacing, arr.ndim),
                "dtype": str(arr.dtype),
            }
        )
    return pd.DataFrame(rows)


def check_image_mask_alignment(image: sitk.Image | StrPath, mask: sitk.Image | StrPath) -> dict[str, Any]:
    """Check whether image and mask share shape, spacing, origin, and direction."""
    image_obj = _read_image(image)
    mask_obj = _read_image(mask)
    checks = {
        "size_match": image_obj.GetSize() == mask_obj.GetSize(),
        "spacing_match": np.allclose(image_obj.GetSpacing(), mask_obj.GetSpacing()),
        "origin_match": np.allclose(image_obj.GetOrigin(), mask_obj.GetOrigin()),
        "direction_match": np.allclose(image_obj.GetDirection(), mask_obj.GetDirection()),
    }
    checks["aligned"] = bool(all(checks.values()))
    checks["image_size_xyz"] = tuple(int(v) for v in image_obj.GetSize())
    checks["mask_size_xyz"] = tuple(int(v) for v in mask_obj.GetSize())
    checks["image_spacing_xyz"] = tuple(float(v) for v in image_obj.GetSpacing())
    checks["mask_spacing_xyz"] = tuple(float(v) for v in mask_obj.GetSpacing())
    return checks


def summarize_mask_volume(
    mask: sitk.Image | np.ndarray | StrPath,
    *,
    labels: Sequence[int] | None = None,
    spacing: Sequence[float] | None = None,
) -> pd.DataFrame:
    """Return label-wise mask voxel counts and volumes in ml."""
    image = _read_image(mask) if not isinstance(mask, np.ndarray) else None
    arr = sitk.GetArrayFromImage(image) if image is not None else np.asarray(mask)
    selected_spacing = spacing if spacing is not None else (image.GetSpacing() if image is not None else None)
    per_voxel_ml = voxel_volume_ml(selected_spacing, arr.ndim)
    spacing_values = tuple(float(v) for v in selected_spacing)
    label_values = labels if labels is not None else sorted(int(v) for v in np.unique(arr) if int(v) != 0)
    rows = []
    for label in label_values:
        count = int(np.sum(arr == int(label)))
        rows.append(
            {
                "label": int(label),
                "voxel_count": count,
                "volume_ml": float(count * per_voxel_ml),
                "spacing_xyz": spacing_values,
            }
        )
    return pd.DataFrame(rows)


def summarize_intensity_range(
    image: sitk.Image | np.ndarray | StrPath,
    *,
    mask: sitk.Image | np.ndarray | StrPath | None = None,
    percentiles: Sequence[float] = (0.5, 99.5),
) -> dict[str, Any]:
    """Summarize intensity distribution, optionally inside a mask."""
    image_arr = _image_array(image).astype(float)
    values = image_arr[np.isfinite(image_arr)]
    if mask is not None:
        mask_arr = _image_array(mask)
        if mask_arr.shape != image_arr.shape:
            raise ValueError(f"mask shape {mask_arr.shape} does not match image shape {image_arr.shape}")
        values = image_arr[(mask_arr > 0) & np.isfinite(image_arr)]
    if values.size == 0:
        raise ValueError("No finite intensity values available for summary.")
    summary: dict[str, Any] = {
        "n_voxels": int(values.size),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
    }
    for percentile in percentiles:
        summary[f"p{str(percentile).replace('.', '_')}"] = float(np.percentile(values, float(percentile)))
    return summary


def _read_image(image: sitk.Image | np.ndarray | StrPath) -> sitk.Image:
    if isinstance(image, sitk.Image):
        return image
    if isinstance(image, np.ndarray):
        return sitk.GetImageFromArray(image)
    return sitk.ReadImage(str(image))


def _image_array(image: sitk.Image | np.ndarray | StrPath) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return np.asarray(image)
    return sitk.GetArrayFromImage(_read_image(image))


def _dicom_geometry_row(ds: pydicom.Dataset) -> dict[str, Any]:
    return {
        "rows": int(getattr(ds, "Rows", 0) or 0),
        "columns": int(getattr(ds, "Columns", 0) or 0),
        "pixel_spacing": tuple(float(v) for v in getattr(ds, "PixelSpacing", [])),
        "slice_thickness": float(getattr(ds, "SliceThickness", np.nan)),
        "spacing_between_slices": float(getattr(ds, "SpacingBetweenSlices", np.nan)),
        "image_orientation_patient": tuple(float(v) for v in getattr(ds, "ImageOrientationPatient", [])),
        "image_position_patient": tuple(float(v) for v in getattr(ds, "ImagePositionPatient", [])),
        "frame_of_reference_uid": str(getattr(ds, "FrameOfReferenceUID", "")),
    }


def _empty_dicom_geometry() -> dict[str, Any]:
    return {
        "rows": np.nan,
        "columns": np.nan,
        "pixel_spacing": (),
        "slice_thickness": np.nan,
        "spacing_between_slices": np.nan,
        "image_orientation_patient": (),
        "image_position_patient": (),
        "frame_of_reference_uid": "",
    }
