"""Tests for DICOM SEG helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pydicom
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, SegmentationStorage, generate_uid

from fyron.dicom import (
    label_map_to_segments,
    load_source_dicom_series,
    read_segment_descriptions,
    validate_dicom_seg,
    validate_segment_descriptions,
    write_dicom_seg,
)


def test_label_map_to_segments() -> None:
    label_map = np.array(
        [
            [[0, 1], [2, 1]],
            [[2, 0], [1, 0]],
        ],
        dtype=np.uint8,
    )

    segments = label_map_to_segments(label_map, labels=[1, 2])

    assert segments.shape == (2, 2, 2, 2)
    assert segments.dtype == bool
    assert int(segments[0].sum()) == 3
    assert int(segments[1].sum()) == 2


def test_write_dicom_seg_requires_highdicom_when_missing() -> None:
    pytest.importorskip("highdicom")


def _source_slice(path: Path, *, study_uid: str, series_uid: str, frame_uid: str, z: float, instance: int) -> Path:
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
    ds.FrameOfReferenceUID = frame_uid
    ds.Modality = "CT"
    ds.PatientName = "Test^Patient"
    ds.PatientID = "P001"
    ds.PatientBirthDate = ""
    ds.PatientSex = "O"
    ds.AccessionNumber = ""
    ds.StudyID = "1"
    ds.StudyDate = "20200101"
    ds.StudyTime = "120000"
    ds.SeriesNumber = 1
    ds.InstanceNumber = instance
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
    ds.ImagePositionPatient = [0.0, 0.0, z]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.PixelSpacing = [1.0, 1.0]
    ds.SliceThickness = 1.0
    ds.SpacingBetweenSlices = 1.0
    ds.save_as(str(path), write_like_original=False)
    return path


def test_load_source_dicom_series_sorts_by_geometry(tmp_path: Path) -> None:
    study_uid = generate_uid()
    series_uid = generate_uid()
    frame_uid = generate_uid()
    _source_slice(tmp_path / "b.dcm", study_uid=study_uid, series_uid=series_uid, frame_uid=frame_uid, z=2.0, instance=1)
    _source_slice(tmp_path / "a.dcm", study_uid=study_uid, series_uid=series_uid, frame_uid=frame_uid, z=0.0, instance=3)
    _source_slice(tmp_path / "c.dcm", study_uid=study_uid, series_uid=series_uid, frame_uid=frame_uid, z=1.0, instance=2)

    sources = load_source_dicom_series(tmp_path)

    assert [float(ds.ImagePositionPatient[2]) for ds in sources] == [0.0, 1.0, 2.0]


def test_load_source_dicom_series_falls_back_to_instance_number(tmp_path: Path) -> None:
    study_uid = generate_uid()
    series_uid = generate_uid()
    frame_uid = generate_uid()
    paths = [
        _source_slice(tmp_path / "z.dcm", study_uid=study_uid, series_uid=series_uid, frame_uid=frame_uid, z=0.0, instance=2),
        _source_slice(tmp_path / "a.dcm", study_uid=study_uid, series_uid=series_uid, frame_uid=frame_uid, z=1.0, instance=1),
    ]
    for path in paths:
        ds = pydicom.dcmread(path)
        del ds.ImagePositionPatient
        ds.save_as(path, write_like_original=False)

    sources = load_source_dicom_series(tmp_path)

    assert [int(ds.InstanceNumber) for ds in sources] == [1, 2]


def test_validate_segment_descriptions_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="at least one segment"):
        validate_segment_descriptions([])
    with pytest.raises(ValueError, match="label"):
        validate_segment_descriptions([{"label_value": 1}])
    with pytest.raises(ValueError, match="Duplicate label_value"):
        validate_segment_descriptions([{"label": "a", "label_value": 1}, {"label": "b", "label_value": 1}])
    with pytest.raises(ValueError, match="coded concept"):
        validate_segment_descriptions([{"label": "a", "category": ("T-D0050", "SRT")}])


def test_read_segment_descriptions(tmp_path: Path) -> None:
    path = tmp_path / "segments.json"
    path.write_text('[{"label": "liver", "label_value": 5}]', encoding="utf-8")

    descriptions = read_segment_descriptions(path)

    assert descriptions == [{"label": "liver", "label_value": 5}]


def test_write_dicom_seg_validates_mask_against_source_count(tmp_path: Path) -> None:
    source = _source_slice(
        tmp_path / "src0.dcm",
        study_uid=generate_uid(),
        series_uid=generate_uid(),
        frame_uid=generate_uid(),
        z=0.0,
        instance=1,
    )
    label_map = np.zeros((2, 4, 5), dtype=np.uint8)

    with pytest.raises(ValueError, match="slice count"):
        write_dicom_seg(
            label_map,
            source_images=[source],
            output_path=tmp_path / "mask.seg.dcm",
            segment_descriptions=[{"label": "lesion", "label_value": 1}],
        )


def test_write_dicom_seg_validates_4d_segment_count(tmp_path: Path) -> None:
    source = _source_slice(
        tmp_path / "src0.dcm",
        study_uid=generate_uid(),
        series_uid=generate_uid(),
        frame_uid=generate_uid(),
        z=0.0,
        instance=1,
    )
    stack = np.zeros((2, 1, 4, 5), dtype=bool)

    with pytest.raises(ValueError, match="Number of mask segments"):
        write_dicom_seg(
            stack,
            source_images=[source],
            output_path=tmp_path / "mask.seg.dcm",
            segment_descriptions=[{"label": "lesion"}],
        )


def test_write_dicom_seg_with_highdicom_when_available(tmp_path: Path) -> None:
    pytest.importorskip("highdicom")
    study_uid = generate_uid()
    series_uid = generate_uid()
    frame_uid = generate_uid()
    sources = [
        _source_slice(tmp_path / "src0.dcm", study_uid=study_uid, series_uid=series_uid, frame_uid=frame_uid, z=0.0, instance=1),
        _source_slice(tmp_path / "src1.dcm", study_uid=study_uid, series_uid=series_uid, frame_uid=frame_uid, z=1.0, instance=2),
    ]
    label_map = np.zeros((2, 4, 5), dtype=np.uint8)
    label_map[:, 1:3, 2:4] = 1

    out = write_dicom_seg(
        label_map,
        source_images=sources,
        output_path=tmp_path / "mask.seg.dcm",
        segment_descriptions=[{"label": "lesion", "label_value": 1}],
    )

    info = validate_dicom_seg(out, source_images=sources)
    assert info["modality"] == "SEG"
    assert info["number_of_segments"] == 1


def test_write_dicom_seg_import_error_is_clear(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "highdicom":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    source = _source_slice(
        tmp_path / "source.dcm",
        study_uid=generate_uid(),
        series_uid=generate_uid(),
        frame_uid=generate_uid(),
        z=0.0,
        instance=1,
    )
    with pytest.raises(ImportError, match="fyron\\[dicom-seg\\]"):
        write_dicom_seg(
            np.ones((1, 1, 4, 5), dtype=bool),
            source_images=[source],
            output_path="seg.dcm",
            segment_descriptions=[{"label": "lesion"}],
        )


def test_validate_dicom_seg_metadata(tmp_path: Path) -> None:
    path = tmp_path / "seg.dcm"
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = SegmentationStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()
    ds = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.is_implicit_VR = False
    ds.is_little_endian = True
    ds.SOPClassUID = SegmentationStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SeriesInstanceUID = generate_uid()
    ds.Modality = "SEG"
    item = pydicom.Dataset()
    item.SegmentNumber = 1
    item.SegmentLabel = "lesion"
    ds.SegmentSequence = [item]
    ds.save_as(str(path), write_like_original=False)

    info = validate_dicom_seg(path)

    assert info["modality"] == "SEG"
    assert info["number_of_segments"] == 1
    assert info["segment_labels"] == ["lesion"]
