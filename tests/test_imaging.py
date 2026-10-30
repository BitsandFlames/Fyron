"""Tests for fyron.imaging."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import SimpleITK as sitk
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, CTImageStorage, generate_uid

from fyron import imaging as fim


def _write_minimal_ct_slice(
    path: Path,
    *,
    series_uid: str,
    study_uid: str,
    sop_instance_uid: str,
    ipp_z: float,
    pixel_hu: np.ndarray,
) -> None:
    rows, cols = int(pixel_hu.shape[0]), int(pixel_hu.shape[1])
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = CTImageStorage
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.file_meta = file_meta
    ds.is_implicit_VR = False
    ds.is_little_endian = True

    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = sop_instance_uid
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.Modality = "CT"
    ds.SeriesDescription = "SynSeries"
    ds.StudyDescription = "SynStudy"
    ds.PatientName = "Test^Patient"
    ds.PatientID = "001"
    ds.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.RescaleIntercept = 0.0
    ds.RescaleSlope = 1.0
    arr = np.asarray(pixel_hu, dtype=np.int16)
    ds.PixelData = arr.tobytes()
    ds.ImagePositionPatient = [0.0, 0.0, float(ipp_z)]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.PixelSpacing = [1.0, 1.0]
    ds.SliceThickness = 1.0
    ds.SpacingBetweenSlices = 1.0
    ds.FrameOfReferenceUID = generate_uid()
    ds.InstanceNumber = int(ipp_z + 10)
    ds.save_as(str(path), write_like_original=False)


def test_read_dicom_header(tmp_path: Path) -> None:
    series_uid = generate_uid()
    study_uid = generate_uid()
    p = tmp_path / "slice1.dcm"
    _write_minimal_ct_slice(
        p,
        series_uid=series_uid,
        study_uid=study_uid,
        sop_instance_uid=generate_uid(),
        ipp_z=0.0,
        pixel_hu=np.zeros((8, 8), dtype=np.int16),
    )
    ds = fim.read_dicom_header(p, stop_before_pixels=True)
    assert ds.SeriesInstanceUID == series_uid
    dct = fim.read_dicom_header(p, stop_before_pixels=True, as_dict=True)
    assert isinstance(dct, dict)
    assert dct.get("Modality") == "CT"


def test_read_dicom_header_selected_tags(tmp_path: Path) -> None:
    series_uid = generate_uid()
    study_uid = generate_uid()
    p = tmp_path / "slice.dcm"
    _write_minimal_ct_slice(
        p,
        series_uid=series_uid,
        study_uid=study_uid,
        sop_instance_uid=generate_uid(),
        ipp_z=0.0,
        pixel_hu=np.ones((4, 4), dtype=np.int16),
    )
    sub = fim.read_dicom_header(p, selected_tags=["Modality", "0010,0020"])
    assert getattr(sub, "Modality", None) == "CT"
    d2 = fim.read_dicom_header(p, as_dict=True, selected_tags=["SeriesInstanceUID"])
    assert d2["SeriesInstanceUID"] == series_uid


def test_read_dicom_header_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        fim.read_dicom_header(tmp_path / "nope.dcm")


def test_get_dicom_series_ids(tmp_path: Path) -> None:
    series_uid = generate_uid()
    study_uid = generate_uid()
    for i, z in enumerate([0.0, 1.0]):
        _write_minimal_ct_slice(
            tmp_path / f"sl{i}.dcm",
            series_uid=series_uid,
            study_uid=study_uid,
            sop_instance_uid=generate_uid(),
            ipp_z=z,
            pixel_hu=np.zeros((4, 4), dtype=np.int16),
        )
    ids = fim.get_dicom_series_ids(tmp_path)
    assert series_uid in ids
    meta = fim.get_dicom_series_ids(tmp_path, include_metadata=True)
    assert len(meta) >= 1
    row = meta.loc[meta["series_id"] == series_uid].iloc[0]
    assert row["number_of_files"] == 2
    assert row["modality"] == "CT"


def test_get_dicom_series_ids_empty(tmp_path: Path) -> None:
    assert fim.get_dicom_series_ids(tmp_path) == []
    df = fim.get_dicom_series_ids(tmp_path, include_metadata=True)
    assert list(df.columns) == [
        "series_id",
        "number_of_files",
        "first_file",
        "modality",
        "series_description",
        "study_instance_uid",
        "series_instance_uid",
    ]
    assert len(df) == 0


def test_get_dicom_series_ids_recursive(tmp_path: Path) -> None:
    series_uid = generate_uid()
    study_uid = generate_uid()
    sub = tmp_path / "nested"
    sub.mkdir()
    _write_minimal_ct_slice(
        sub / "a.dcm",
        series_uid=series_uid,
        study_uid=study_uid,
        sop_instance_uid=generate_uid(),
        ipp_z=0.0,
        pixel_hu=np.zeros((4, 4), dtype=np.int16),
    )
    ids = fim.get_dicom_series_ids(tmp_path, recursive=True)
    assert series_uid in ids


def test_read_dicom_series(tmp_path: Path) -> None:
    series_uid = generate_uid()
    study_uid = generate_uid()
    for i, z in enumerate([0.0, 2.0]):
        _write_minimal_ct_slice(
            tmp_path / f"a{i}.dcm",
            series_uid=series_uid,
            study_uid=study_uid,
            sop_instance_uid=generate_uid(),
            ipp_z=z,
            pixel_hu=np.full((4, 4), 100 * (i + 1), dtype=np.int16),
        )
    img = fim.read_dicom_series(tmp_path, series_uid)
    assert isinstance(img, sitk.Image)
    img2, arr = fim.read_dicom_series(tmp_path, series_uid, return_array=True)
    assert arr.shape[0] == 2
    assert np.max(arr) > 0


def test_read_dicom_series_unknown_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Series ID not found"):
        fim.read_dicom_series(tmp_path, "1.2.3.4.5.nonexistent")


def test_read_nifti_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "vol.nii.gz"
    arr_in = np.random.rand(3, 4, 5).astype(np.float32)
    ref = sitk.GetImageFromArray(arr_in)
    ref.SetSpacing((0.7, 0.8, 1.2))
    sitk.WriteImage(ref, str(p))
    img = fim.read_nifti(p)
    assert isinstance(img, sitk.Image)
    img2, arr = fim.read_nifti(p, return_array=True)
    assert arr.shape == arr_in.shape


def test_read_nifti_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        fim.read_nifti(tmp_path / "missing.nii.gz")


def test_write_nifti_from_sitk(tmp_path: Path) -> None:
    arr = np.ones((2, 3, 4), dtype=np.float32)
    img = sitk.GetImageFromArray(arr)
    out = tmp_path / "out.nii.gz"
    ret = fim.write_nifti(img, out)
    assert ret == out.resolve()
    assert out.exists()


def test_write_nifti_from_array_with_reference(tmp_path: Path) -> None:
    ref = sitk.GetImageFromArray(np.zeros((2, 3, 4), dtype=np.float32))
    ref.SetSpacing((2.0, 3.0, 4.0))
    ref.SetOrigin((1.0, 2.0, 3.0))
    arr = np.ones((2, 3, 4), dtype=np.float32)
    out = tmp_path / "from_arr.nii.gz"
    fim.write_nifti(arr, out, reference_image=ref)
    back = sitk.ReadImage(str(out))
    assert back.GetSpacing() == ref.GetSpacing()
    assert back.GetOrigin() == ref.GetOrigin()


def test_normalize_ct_default_range() -> None:
    x = np.array([[-1500.0, 0.0, 4000.0]], dtype=np.float32)
    y = fim.normalize_ct(x)
    assert y.dtype == np.float32
    assert float(y.min()) == 0.0
    assert float(y.max()) == 1.0


def test_normalize_ct_custom_range() -> None:
    y = fim.normalize_ct(np.array([[0.0, 500.0]], dtype=np.float32), hu_min=0.0, hu_max=1000.0)
    assert np.allclose(y, np.array([[0.0, 0.5]], dtype=np.float32))


def test_normalize_ct_invalid_range() -> None:
    with pytest.raises(ValueError):
        fim.normalize_ct(np.zeros((2, 2), dtype=np.float32), hu_min=1.0, hu_max=1.0)


def test_normalize_mr_percentile() -> None:
    x = np.array([[0.0, 10.0, 100.0]], dtype=np.float32)
    y95 = fim.normalize_mr(x, mode="percentile", percentile=95.0, ignore_zeros=True)
    y99 = fim.normalize_mr(x, mode="percentile", percentile=99.0, ignore_zeros=True)
    assert y95.dtype == np.float32
    assert float(y99.max()) <= 1.0


def test_normalize_mr_max() -> None:
    x = np.array([[1.0, 2.0, 4.0]], dtype=np.float32)
    y = fim.normalize_mr(x, mode="max", ignore_zeros=False)
    assert np.isclose(float(y.max()), 1.0)


def test_normalize_mr_value_mode() -> None:
    x = np.array([[2.0, 4.0]], dtype=np.float32)
    y = fim.normalize_mr(x, mode="value", value=4.0, clip=False)
    assert np.allclose(y, np.array([[0.5, 1.0]], dtype=np.float32))


def test_normalize_mr_ignore_zeros_percentile() -> None:
    x = np.array([[0.0, 0.0, 50.0, 100.0]], dtype=np.float32)
    y = fim.normalize_mr(x, mode="percentile", percentile=50.0, ignore_zeros=True)
    assert float(y.max()) <= 1.0


def test_normalize_mr_invalid_mode() -> None:
    with pytest.raises(ValueError, match="mode must be"):
        fim.normalize_mr(np.ones((2, 2), dtype=np.float32), mode="other")


def test_normalize_mr_value_missing() -> None:
    with pytest.raises(ValueError, match="positive `value`"):
        fim.normalize_mr(np.ones((2, 2), dtype=np.float32), mode="value")


def test_normalize_mr_zero_denom() -> None:
    with pytest.raises(ValueError, match="Invalid normalization denominator"):
        fim.normalize_mr(np.zeros((2, 2), dtype=np.float32), mode="max", ignore_zeros=True)


def test_read_nifti_bad_suffix(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("a")
    with pytest.raises(ValueError, match="NIfTI path"):
        fim.read_nifti(p)


def test_normalize_ct_sitk_preserves_meta(tmp_path: Path) -> None:
    arr = np.zeros((2, 4, 4), dtype=np.int16)
    img = sitk.GetImageFromArray(arr)
    img.SetSpacing((1.5, 1.0, 1.0))
    out = fim.normalize_ct(img)
    assert out.GetSpacing() == img.GetSpacing()
