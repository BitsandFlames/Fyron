"""Synthetic DICOM and NIfTI export helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Sequence, Union

import numpy as np
import pandas as pd
import pydicom
import SimpleITK as sitk
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import (
    CTImageStorage,
    ExplicitVRLittleEndian,
    MRImageStorage,
    SecondaryCaptureImageStorage,
    generate_uid,
)

StrPath = Union[str, Path]


def write_synthetic_nifti(
    volume: sitk.Image | np.ndarray,
    output_path: StrPath,
    *,
    reference_image: sitk.Image | StrPath | None = None,
    spacing: Sequence[float] | None = None,
    origin: Sequence[float] | None = None,
    direction: Sequence[float] | None = None,
    dtype: str | np.dtype = "float32",
    compress: bool = True,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Write a synthetic volume to NIfTI while preserving inspectable geometry.

    Arrays are interpreted in SimpleITK order ``(z, y, x)``. If
    ``reference_image`` is supplied, its spacing, origin, and direction are used
    unless an explicit geometry argument overrides them.
    """
    out = Path(output_path)
    if not (out.name.lower().endswith(".nii") or out.name.lower().endswith(".nii.gz")):
        raise ValueError(f"output_path must end with .nii or .nii.gz, got: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(volume, sitk.Image):
        image = sitk.Image(volume)
        if dtype is not None:
            image = sitk.Cast(image, _sitk_pixel_type(dtype))
    else:
        arr = np.asarray(volume)
        if arr.ndim != 3:
            raise ValueError(f"volume must be a 3D array in (z, y, x) order, got shape {arr.shape}")
        image = sitk.GetImageFromArray(arr.astype(dtype, copy=False))

    reference = _load_reference_image(reference_image)
    if reference is not None:
        image.CopyInformation(reference)

    if spacing is not None:
        image.SetSpacing(_geometry_tuple(spacing, "spacing"))
    if origin is not None:
        image.SetOrigin(_geometry_tuple(origin, "origin"))
    if direction is not None:
        direction_values = tuple(float(x) for x in direction)
        if len(direction_values) != image.GetDimension() ** 2:
            raise ValueError("direction must contain dimension^2 values")
        image.SetDirection(direction_values)

    if metadata:
        for key, value in metadata.items():
            image.SetMetaData(str(key), str(value))

    writer = sitk.ImageFileWriter()
    writer.SetFileName(str(out))
    writer.SetUseCompression(bool(compress or out.name.lower().endswith(".nii.gz")))
    writer.Execute(image)
    return out.resolve()


def write_synthetic_dicom_series(
    volume: np.ndarray | sitk.Image,
    output_dir: StrPath,
    *,
    reference_dicom_dir: StrPath | None = None,
    reference_datasets: Sequence[pydicom.Dataset | StrPath] | None = None,
    patient_id: str = "SYNTHETIC",
    study_instance_uid: str | None = None,
    series_instance_uid: str | None = None,
    modality: str = "CT",
    series_description: str = "Synthetic Fyron volume",
    intensity_mode: str = "hu",
    rescale_intercept: float = -1024.0,
    rescale_slope: float = 1.0,
    copy_patient_tags: bool = False,
) -> pd.DataFrame:
    """Write a synthetic 3D volume as one DICOM file per slice.

    The writer generates new UIDs by default and marks the series as derived
    synthetic data. Reference DICOM datasets are used for geometry only unless
    ``copy_patient_tags=True``.
    """
    arr = _volume_to_array(volume)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if rescale_slope == 0:
        raise ValueError("rescale_slope must not be zero")

    refs = _load_reference_datasets(reference_datasets, reference_dicom_dir)
    if refs and any(int(ref.Rows) != arr.shape[1] or int(ref.Columns) != arr.shape[2] for ref in refs[: min(len(refs), arr.shape[0])]):
        raise ValueError("Reference DICOM rows/columns must match the synthetic volume shape")

    study_uid = study_instance_uid or generate_uid()
    series_uid = series_instance_uid or generate_uid()
    frame_uid = str(getattr(refs[0], "FrameOfReferenceUID", generate_uid())) if refs else generate_uid()
    sop_class_uid = _sop_class_for_modality(modality)
    now = datetime.now()
    manifest_rows: list[dict[str, Any]] = []

    for index in range(arr.shape[0]):
        ref = refs[index] if index < len(refs) else (refs[0] if refs else None)
        sop_uid = generate_uid()
        stored = _encode_pixels(arr[index], intensity_mode=intensity_mode, slope=rescale_slope, intercept=rescale_intercept)
        ds = _make_file_dataset(out / f"slice_{index + 1:04d}.dcm", sop_class_uid, sop_uid)

        ds.SOPClassUID = sop_class_uid
        ds.SOPInstanceUID = sop_uid
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid
        ds.FrameOfReferenceUID = str(getattr(ref, "FrameOfReferenceUID", frame_uid))
        ds.Modality = modality.upper()
        ds.Manufacturer = "Bits & Flames"
        ds.ManufacturerModelName = "Fyron synthetic writer"
        ds.SeriesDescription = series_description
        ds.ImageType = ["DERIVED", "SECONDARY", "SYNTHETIC"]
        ds.ContentDate = now.strftime("%Y%m%d")
        ds.ContentTime = now.strftime("%H%M%S.%f")
        ds.StudyDate = str(getattr(ref, "StudyDate", ds.ContentDate))
        ds.StudyTime = str(getattr(ref, "StudyTime", ds.ContentTime))
        ds.SeriesDate = ds.ContentDate
        ds.SeriesTime = ds.ContentTime
        ds.InstanceNumber = index + 1

        _set_patient_tags(ds, ref, patient_id=patient_id, copy_patient_tags=copy_patient_tags)
        _set_geometry_tags(ds, ref, index=index, n_slices=arr.shape[0])
        _set_pixel_tags(ds, stored, rescale_intercept=rescale_intercept, rescale_slope=rescale_slope)

        path = out / f"slice_{index + 1:04d}.dcm"
        ds.save_as(str(path), write_like_original=False)
        manifest_rows.append(
            {
                "slice_index": index,
                "path": str(path.resolve()),
                "sop_instance_uid": sop_uid,
                "study_instance_uid": study_uid,
                "series_instance_uid": series_uid,
                "z_position": float(ds.ImagePositionPatient[2]),
                "rows": int(ds.Rows),
                "columns": int(ds.Columns),
                "modality": ds.Modality,
                "series_description": ds.SeriesDescription,
            }
        )

    return pd.DataFrame(manifest_rows)


def _load_reference_image(reference_image: sitk.Image | StrPath | None) -> sitk.Image | None:
    if reference_image is None:
        return None
    if isinstance(reference_image, sitk.Image):
        return reference_image
    return sitk.ReadImage(str(reference_image))


def _sitk_pixel_type(dtype: str | np.dtype) -> int:
    np_dtype = np.dtype(dtype)
    if np_dtype == np.dtype("float32"):
        return sitk.sitkFloat32
    if np_dtype == np.dtype("float64"):
        return sitk.sitkFloat64
    if np_dtype == np.dtype("int16"):
        return sitk.sitkInt16
    if np_dtype == np.dtype("uint16"):
        return sitk.sitkUInt16
    if np_dtype == np.dtype("uint8"):
        return sitk.sitkUInt8
    if np_dtype == np.dtype("int8"):
        return sitk.sitkInt8
    raise ValueError(f"Unsupported NIfTI dtype: {dtype!r}")


def _geometry_tuple(values: Sequence[float], name: str) -> tuple[float, float, float]:
    out = tuple(float(x) for x in values)
    if len(out) != 3:
        raise ValueError(f"{name} must contain 3 values")
    return out


def _volume_to_array(volume: np.ndarray | sitk.Image) -> np.ndarray:
    arr = sitk.GetArrayFromImage(volume) if isinstance(volume, sitk.Image) else np.asarray(volume)
    if arr.ndim != 3:
        raise ValueError(f"volume must be 3D in (z, y, x) order, got shape {arr.shape}")
    return arr.astype(np.float32, copy=False)


def _load_reference_datasets(
    reference_datasets: Sequence[pydicom.Dataset | StrPath] | None,
    reference_dicom_dir: StrPath | None,
) -> list[pydicom.Dataset]:
    if reference_datasets is not None and reference_dicom_dir is not None:
        raise ValueError("Provide either reference_datasets or reference_dicom_dir, not both")
    if reference_datasets is not None:
        datasets = [
            item if isinstance(item, pydicom.Dataset) else pydicom.dcmread(str(item), stop_before_pixels=True)
            for item in reference_datasets
        ]
    elif reference_dicom_dir is not None:
        root = Path(reference_dicom_dir)
        if not root.exists():
            raise FileNotFoundError(f"reference_dicom_dir does not exist: {root}")
        datasets = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            try:
                datasets.append(pydicom.dcmread(str(path), stop_before_pixels=True))
            except Exception:
                continue
    else:
        return []
    return sorted(datasets, key=_slice_sort_key)


def _slice_sort_key(ds: pydicom.Dataset) -> tuple[float, int]:
    ipp = getattr(ds, "ImagePositionPatient", None)
    z = float(ipp[2]) if ipp is not None and len(ipp) >= 3 else float(getattr(ds, "SliceLocation", 0.0))
    instance = int(getattr(ds, "InstanceNumber", 0))
    return z, instance


def _sop_class_for_modality(modality: str) -> str:
    mod = modality.upper()
    if mod == "CT":
        return CTImageStorage
    if mod == "MR":
        return MRImageStorage
    return SecondaryCaptureImageStorage


def _encode_pixels(slice_array: np.ndarray, *, intensity_mode: str, slope: float, intercept: float) -> np.ndarray:
    mode = intensity_mode.lower()
    if mode == "hu":
        stored = np.rint((slice_array - intercept) / slope)
    elif mode == "raw":
        stored = np.rint(slice_array)
    else:
        raise ValueError("intensity_mode must be 'hu' or 'raw'")
    return np.clip(stored, np.iinfo(np.int16).min, np.iinfo(np.int16).max).astype(np.int16)


def _make_file_dataset(path: Path, sop_class_uid: str, sop_instance_uid: str) -> FileDataset:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = sop_class_uid
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()
    ds = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.is_implicit_VR = False
    ds.is_little_endian = True
    return ds


def _set_patient_tags(
    ds: FileDataset,
    ref: pydicom.Dataset | None,
    *,
    patient_id: str,
    copy_patient_tags: bool,
) -> None:
    if copy_patient_tags and ref is not None:
        for keyword in ("PatientName", "PatientID", "PatientBirthDate", "PatientSex"):
            if hasattr(ref, keyword):
                setattr(ds, keyword, getattr(ref, keyword))
        return
    ds.PatientName = "Synthetic^Fyron"
    ds.PatientID = patient_id
    ds.PatientBirthDate = ""
    ds.PatientSex = ""


def _set_geometry_tags(ds: FileDataset, ref: pydicom.Dataset | None, *, index: int, n_slices: int) -> None:
    rows = int(getattr(ref, "Rows", 0)) if ref is not None else 0
    cols = int(getattr(ref, "Columns", 0)) if ref is not None else 0
    ds.Rows = rows or int(getattr(ds, "Rows", 0) or 1)
    ds.Columns = cols or int(getattr(ds, "Columns", 0) or 1)
    ds.PixelSpacing = [float(x) for x in getattr(ref, "PixelSpacing", [1.0, 1.0])]
    ds.ImageOrientationPatient = [float(x) for x in getattr(ref, "ImageOrientationPatient", [1.0, 0.0, 0.0, 0.0, 1.0, 0.0])]
    ds.SliceThickness = float(getattr(ref, "SliceThickness", 1.0))
    ds.SpacingBetweenSlices = float(getattr(ref, "SpacingBetweenSlices", ds.SliceThickness))

    if ref is not None and hasattr(ref, "ImagePositionPatient"):
        ds.ImagePositionPatient = [float(x) for x in ref.ImagePositionPatient]
        return

    row = np.asarray(ds.ImageOrientationPatient[:3], dtype=float)
    col = np.asarray(ds.ImageOrientationPatient[3:], dtype=float)
    normal = np.cross(row, col)
    if not np.any(normal):
        normal = np.asarray([0.0, 0.0, 1.0])
    center_offset = index - (n_slices - 1) / 2.0
    pos = normal * ds.SpacingBetweenSlices * center_offset
    ds.ImagePositionPatient = [float(pos[0]), float(pos[1]), float(pos[2])]


def _set_pixel_tags(ds: FileDataset, pixels: np.ndarray, *, rescale_intercept: float, rescale_slope: float) -> None:
    ds.Rows = int(pixels.shape[0])
    ds.Columns = int(pixels.shape[1])
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.RescaleIntercept = float(rescale_intercept)
    ds.RescaleSlope = float(rescale_slope)
    ds.PixelData = np.ascontiguousarray(pixels).tobytes()
