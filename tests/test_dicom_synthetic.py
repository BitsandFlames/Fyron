"""Tests for synthetic DICOM/NIfTI export."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pydicom
import SimpleITK as sitk
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

from fyron.dicom import write_synthetic_dicom_series, write_synthetic_nifti


def _reference_slice(path: Path, *, series_uid: str, study_uid: str, z: float, patient_id: str = "REAL001") -> Path:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = CTImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.is_implicit_VR = False
    ds.is_little_endian = True
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.FrameOfReferenceUID = generate_uid()
    ds.Modality = "CT"
    ds.PatientName = "Real^Patient"
    ds.PatientID = patient_id
    ds.StudyDate = "20200101"
    ds.StudyTime = "120000"
    ds.SeriesDescription = "Reference"
    ds.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 4
    ds.Columns = 5
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.RescaleIntercept = -1024.0
    ds.RescaleSlope = 1.0
    ds.PixelData = np.zeros((4, 5), dtype=np.int16).tobytes()
    ds.ImagePositionPatient = [1.0, 2.0, z]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.PixelSpacing = [0.8, 0.9]
    ds.SliceThickness = 2.0
    ds.SpacingBetweenSlices = 2.0
    ds.InstanceNumber = int(z + 10)
    ds.save_as(str(path), write_like_original=False)
    return path


def test_write_synthetic_nifti_with_reference_geometry(tmp_path: Path) -> None:
    ref = sitk.GetImageFromArray(np.zeros((2, 3, 4), dtype=np.float32))
    ref.SetSpacing((0.7, 0.8, 1.2))
    ref.SetOrigin((4.0, 5.0, 6.0))
    out = tmp_path / "synthetic.nii.gz"

    result = write_synthetic_nifti(
        np.ones((2, 3, 4), dtype=np.float32),
        out,
        reference_image=ref,
        metadata={"synthetic_source": "test"},
    )

    back = sitk.ReadImage(str(result))
    assert np.allclose(back.GetSpacing(), ref.GetSpacing())
    assert np.allclose(back.GetOrigin(), ref.GetOrigin())
    assert sitk.GetArrayFromImage(back).shape == (2, 3, 4)


def test_write_synthetic_dicom_series_generates_new_uids_and_synthetic_patient(tmp_path: Path) -> None:
    ref_dir = tmp_path / "ref"
    ref_dir.mkdir()
    ref_series_uid = generate_uid()
    ref_study_uid = generate_uid()
    for i, z in enumerate([0.0, 2.0, 4.0]):
        _reference_slice(ref_dir / f"ref_{i}.dcm", series_uid=ref_series_uid, study_uid=ref_study_uid, z=z)

    volume = np.full((3, 4, 5), 42.0, dtype=np.float32)
    manifest = write_synthetic_dicom_series(
        volume,
        tmp_path / "synthetic",
        reference_dicom_dir=ref_dir,
        patient_id="SYN001",
        series_description="GAN sample",
    )

    assert len(manifest) == 3
    first = pydicom.dcmread(manifest.loc[0, "path"])
    assert first.Modality == "CT"
    assert first.SeriesDescription == "GAN sample"
    assert first.PatientID == "SYN001"
    assert str(first.PatientName) == "Synthetic^Fyron"
    assert first.StudyInstanceUID != ref_study_uid
    assert first.SeriesInstanceUID != ref_series_uid
    assert first.ImageType == ["DERIVED", "SECONDARY", "SYNTHETIC"]
    assert list(first.PixelSpacing) == [0.8, 0.9]
    assert first.pixel_array.shape == (4, 5)


def test_write_synthetic_dicom_series_can_copy_patient_tags_when_explicit(tmp_path: Path) -> None:
    ref = _reference_slice(tmp_path / "ref.dcm", series_uid=generate_uid(), study_uid=generate_uid(), z=0.0)

    manifest = write_synthetic_dicom_series(
        np.ones((1, 4, 5), dtype=np.float32),
        tmp_path / "out",
        reference_datasets=[ref],
        copy_patient_tags=True,
    )

    ds = pydicom.dcmread(manifest.loc[0, "path"])
    assert ds.PatientID == "REAL001"
    assert str(ds.PatientName) == "Real^Patient"
