"""Tests for fyron.boa_radiomics."""

from __future__ import annotations

import numpy as np
import pytest

sitk = pytest.importorskip("SimpleITK")

from fyron.boa_radiomics import (
    discover_boa_radiomics_cases,
    extract_boa_radiomics_features,
    extract_case_radiomics_features,
)
import fyron.boa_radiomics.features as radiomics_features


class DummyExtractor:
    def execute(self, image, mask, label=1):
        mask_array = sitk.GetArrayFromImage(mask)
        image_array = sitk.GetArrayFromImage(image)
        values = image_array[mask_array == label]
        return {
            "diagnostics_Image-original_Size": image.GetSize(),
            "original_firstorder_Mean": float(values.mean()),
            "original_shape_VoxelVolume": float(values.size),
            "non_numeric": "ignored",
        }


def _write_image(path, array, *, spacing=(1.0, 1.0, 1.0)):
    image = sitk.GetImageFromArray(array)
    image.SetSpacing(spacing)
    sitk.WriteImage(image, str(path))


def test_extract_case_radiomics_features_total(tmp_path) -> None:
    case = tmp_path / "patient0001"
    case.mkdir()
    image = np.arange(27, dtype=np.float32).reshape(3, 3, 3)
    seg = np.zeros((3, 3, 3), dtype=np.uint8)
    seg[0, :, :] = 5
    seg[1, :, :] = 1
    _write_image(case / "ct.nii.gz", image)
    _write_image(case / "total.nii.gz", seg)

    row = extract_case_radiomics_features(
        case,
        segmentation_kind="total",
        labels={"liver": 5, "spleen": 1},
        extractor=DummyExtractor(),
        include_paths=False,
    )

    assert row is not None
    assert row["download_id"] == "patient0001"
    assert row["radiomics_total_liver_voxel_count"] == 9
    assert row["radiomics_total_liver_original_firstorder_Mean"] == pytest.approx(
        image[seg == 5].mean()
    )
    assert "radiomics_total_liver_diagnostics_Image-original_Size" not in row
    assert "radiomics_total_liver_non_numeric" not in row


def test_extract_boa_radiomics_features_body_regions(tmp_path, monkeypatch) -> None:
    case_a = tmp_path / "patient0001"
    case_b = tmp_path / "patient0002"
    case_a.mkdir()
    case_b.mkdir()
    for index, case in enumerate([case_a, case_b], start=1):
        image = np.full((2, 3, 3), index, dtype=np.float32)
        seg = np.zeros((2, 3, 3), dtype=np.uint8)
        seg[:, :2, :] = 3
        _write_image(case / "image.nii.gz", image)
        _write_image(case / "body-regions.nii.gz", seg)

    cases = discover_boa_radiomics_cases(tmp_path, segmentation_filename="body-regions.nii.gz")
    assert cases == [case_a, case_b]

    monkeypatch.setattr(radiomics_features, "_make_extractor", lambda settings=None: DummyExtractor())
    df = extract_boa_radiomics_features(
        tmp_path,
        image_filename=("ct.nii.gz", "image.nii.gz"),
        segmentation_kind="body_regions",
        labels={"abdominal_cavity": 3},
        extractor_settings=None,
        include_paths=False,
        num_workers=1,
        show_progress=False,
    )
    rows = [
        extract_case_radiomics_features(
            case,
            image_filename=("ct.nii.gz", "image.nii.gz"),
            segmentation_kind="body_regions",
            labels={"abdominal_cavity": 3},
            extractor=DummyExtractor(),
            include_paths=False,
        )
        for case in cases
    ]
    assert list(df["download_id"]) == ["patient0001", "patient0002"]
    assert [row["download_id"] for row in rows if row is not None] == ["patient0001", "patient0002"]
    assert rows[0]["radiomics_body_regions_abdominal_cavity_voxel_count"] == 12


def test_radiomics_reports_partial_labels_and_safe_errors(tmp_path, monkeypatch, caplog):
    case = tmp_path / "private-case"
    case.mkdir()
    _write_image(case / "ct.nii.gz", np.ones((3, 3, 3), dtype=np.float32))
    seg = np.zeros((3, 3, 3), dtype=np.uint8)
    seg[0, :, :] = 5
    seg[1, 0, 0] = 1
    _write_image(case / "total.nii.gz", seg)
    monkeypatch.setattr(radiomics_features, "_make_extractor", lambda settings: DummyExtractor())
    result = extract_boa_radiomics_features(
        [case, tmp_path / "absent"], labels={"liver": 5, "tiny": 1, "empty": 9},
        minimum_voxels=2, return_report=True, show_progress=False,
    )
    rows = result["report"]["rows"]
    assert rows.status.tolist() == ["success", "undersized_label", "empty_label", "partial", "missing_inputs"]
    assert result["data"].shape[0] == 1
    assert result["data"].loc[0, "radiomics_total_tiny_voxel_count"] == 1
    assert set(result["report"]["summary"].scope) == {"case", "label"}

    class FailingExtractor:
        def execute(self, *args, **kwargs):
            raise ValueError("private-case payload-secret")

    monkeypatch.setattr(radiomics_features, "_make_extractor", lambda settings: FailingExtractor())
    failed = extract_boa_radiomics_features([case], labels={"liver": 5},
        return_report=True, show_progress=False)
    assert "extraction_failure" in failed["report"]["rows"].status.tolist()
    assert "private-case" not in caplog.text and "payload-secret" not in caplog.text
    assert "payload-secret" not in str(failed["report"])
    with pytest.raises(ValueError, match="payload-secret"):
        extract_boa_radiomics_features([case], labels={"liver": 5}, on_error="raise",
                                      return_report=True, show_progress=False)
