"""Independent synthetic regressions for the pre-release audit findings."""

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pydicom
import pytest
import requests
import SimpleITK as sitk

from fyron.boa_extraction import extract_body_region_features, extract_cohort_body_region_features
from fyron.boa_radiomics import extract_case_radiomics_features
from fyron.dicom import DICOMDownloader
from fyron.dicom.client import DicomDownloadError
from fyron.fhir.sql import FHIRSQLClient, SQLQueryError
from fyron.validation import calibration_summary, decision_curve_table, find_best_threshold


def test_dataset_dimension_inspection_rejects_tiff_disguised_as_jpeg(tmp_path):
    from PIL import Image, UnidentifiedImageError
    from fyron.datasets.preparation import _image_size_2d
    path = tmp_path / "disguised.jpg"
    Image.new("RGB", (2, 3)).save(path, format="TIFF")
    with pytest.raises(UnidentifiedImageError):
        _image_size_2d(path)
    Image.new("RGB", (2, 3)).save(path, format="JPEG")
    assert _image_size_2d(path) == (2, 3)


def _save(path, array):
    image = sitk.GetImageFromArray(array)
    image.SetSpacing((2., 2., 5.))
    sitk.WriteImage(image, str(path))


def test_boa_tissue_areas_use_upstream_definitions(tmp_path):
    (tmp_path / "bca-measurements.json").write_text(json.dumps({
        "aggregated": {"l3": {"min_slice_idx": 0, "max_slice_idx": 2}},
    }))
    mask = np.zeros((3, 10, 10), dtype=np.uint8)
    start = 0
    for label, count in {1: 10, 2: 2, 3: 8, 4: 6, 5: 4, 6: 1, 7: 3}.items():
        mask[1].flat[start:start + count] = label
        start += count
    _save(tmp_path / "tissues.nii.gz", mask)
    row = extract_body_region_features(tmp_path, vertebrae=["l3"])
    for column, expected in {"sma_cm2": .4, "sat_area_cm2": .32, "vat_area_cm2": .24, "imat_area_cm2": .16}.items():
        assert row["l3_" + column] == pytest.approx(expected)


def test_body_region_mask_is_not_a_tissue_fallback(tmp_path):
    (tmp_path / "bca-measurements.json").write_text(json.dumps({
        "aggregated": {"l3": {"min_slice_idx": 0, "max_slice_idx": 2}},
    }))
    _save(tmp_path / "body-regions.nii.gz", np.full((3, 4, 4), 2, dtype=np.uint8))
    row = extract_body_region_features(tmp_path, vertebrae=["l3"])
    assert pd.isna(row["l3_sma_cm2"])
    assert pd.isna(row["l3_vat_area_cm2"])
    custom = extract_body_region_features(tmp_path, vertebrae=["l3"],
        sma_segmentation_filename="body-regions.nii.gz", sma_label=2)
    assert custom["l3_sma_cm2"] == pytest.approx(.64)
    assert pd.isna(custom["l3_vat_area_cm2"])


@pytest.mark.parametrize("bounds", [(90, 100), (-1, 1), (2, 1), (0, 4), (1, 1), (0.5, 1), (True, 1), ("0", "2")])
def test_invalid_vertebral_indices_remain_missing_and_are_reported(tmp_path, bounds):
    (tmp_path / "bca-measurements.json").write_text(json.dumps({
        "aggregated": {"l3": {"min_slice_idx": bounds[0], "max_slice_idx": bounds[1]}},
    }))
    _save(tmp_path / "tissues.nii.gz", np.ones((3, 4, 4), dtype=np.uint8))
    result = extract_cohort_body_region_features([tmp_path], vertebrae=["l3"], return_report=True, show_progress=False)
    assert pd.isna(result["data"].iloc[0]["l3_sma_cm2"])
    rows = result["report"]["rows"]
    assert ((rows.label == "l3") & (rows.status == "invalid_measurements")).any()


def test_vertebral_maximum_is_exclusive_as_in_upstream_boa(tmp_path):
    (tmp_path / "bca-measurements.json").write_text(json.dumps({
        "aggregated": {"l3": {"min_slice_idx": 2, "max_slice_idx": 3}},
    }))
    _save(tmp_path / "tissues.nii.gz", np.ones((3, 4, 4), dtype=np.uint8))
    assert extract_body_region_features(tmp_path, vertebrae=["l3"])["l3_sma_cm2"] == pytest.approx(.64)


def test_body_region_radiomics_measures_named_anatomy(tmp_path):
    regions = np.zeros((3, 10, 10), dtype=np.uint8)
    regions[:, :3] = 3
    regions[:, 3:6] = 4
    regions[:, 6:9] = 5
    _save(tmp_path / "body-regions.nii.gz", regions)
    _save(tmp_path / "ct.nii.gz", regions.astype(np.float32) * 100)
    class MeanExtractor:
        def execute(self, image, mask, label):
            return {"Mean": float(sitk.GetArrayFromImage(image)[sitk.GetArrayFromImage(mask) == label].mean())}
    row = extract_case_radiomics_features(tmp_path, segmentation_kind="body_regions", extractor=MeanExtractor(), on_error="raise")
    assert row["radiomics_body_regions_abdominal_cavity_Mean"] == 300
    assert row["radiomics_body_regions_thoracic_cavity_Mean"] == 400
    assert row["radiomics_body_regions_bone_Mean"] == 500
    assert not any("pelvis" in name or "thorax" in name for name in row)


@pytest.mark.parametrize("method", [calibration_summary, decision_curve_table, find_best_threshold])
@pytest.mark.parametrize("labels,probs", [([0, 1, np.nan], [.1, .8, .9]), ([0, None], [.1, .9]),
    ([0, pd.NA], [.1, .9]), ([0, 1, 2], [.1, .5, .9]), ([], []), ([[0], [1]], [.1, .9]),
    ([0, 1], [[.1], [.9]]), ([0, 1], [np.nan, .9]), ([0, 1], [0, np.inf]),
    ([0, 1], [-.1, .9]), ([0, 1], [.1, 1.1]), ([0, 1], [.1])])
def test_probability_validation_rejects_ambiguous_inputs(method, labels, probs):
    with pytest.raises(ValueError):
        method(labels, probs)


def test_calibration_keeps_constant_predictions_in_bin_table():
    summary, bins = calibration_summary([0, 1], [.5, .5])
    assert summary["brier_score"] == .25
    assert bins.n.sum() == summary["n"] == 2
    summary, bins = calibration_summary([0, 0, 1, 1], [.1, .2, .8, .9])
    assert summary["brier_score"] == pytest.approx(.025)


@pytest.mark.parametrize("errors", ["raise", "record"])
def test_failed_sql_partition_discards_early_chunks(errors):
    def stream(_sql, params=None, **_kwargs):
        if params["start_ts"] == "2020-01-01":
            yield pd.DataFrame({"value": ["incomplete"]})
            raise SQLQueryError("synthetic interrupted stream")
        yield pd.DataFrame({"value": ["complete"]})
    client = object.__new__(FHIRSQLClient)
    client.query_df_stream = stream
    result = client.query_df_partitioned("select synthetic", start="2020-01-01", end="2020-01-03",
        window_days=1, continue_on_error=True, errors=errors)
    assert result.value.dropna().tolist() == ["complete"]
    if errors == "record":
        assert (result._fyron_partition_status == "error").sum() == 1


def _instance(uid):
    ds = pydicom.dataset.Dataset()
    ds.is_little_endian = True
    ds.is_implicit_VR = True
    ds.SOPInstanceUID = uid
    ds.SeriesInstanceUID = "1.2.3.1"
    return ds


@pytest.mark.parametrize("mode", ["series", "study"])
@pytest.mark.parametrize("uid", ["../escape", r"..\escape", "/absolute", "1..2", "1.02", "1." * 33])
def test_dicom_rejects_path_like_identifiers_before_writing(tmp_path, mode, uid):
    ds = _instance(uid)
    with requests.Session() as session:
        client = DICOMDownloader(auth=session, dicom_web_url="https://example.invalid", output_format="dicom")
        client.client = SimpleNamespace(iter_series=lambda **_: iter([ds]), iter_study=lambda **_: iter([ds]))
        if mode == "series":
            assert client.download_series("1.2.3", "1.2.3.1", tmp_path, skip_existing=True).error
        else:
            with pytest.raises(DicomDownloadError):
                client._download_study_via_iter_study("1.2.3", tmp_path)
        assert not list(tmp_path.rglob("*.dcm"))


def test_dicom_absolute_identifier_preserves_existing_file(tmp_path):
    victim = tmp_path / "existing.dcm"
    victim.write_bytes(b"synthetic sentinel")
    ds = _instance(str(victim.with_suffix("")))
    with requests.Session() as session:
        client = DICOMDownloader(auth=session, dicom_web_url="https://example.invalid", output_format="dicom")
        client.client = SimpleNamespace(iter_series=lambda **_: iter([ds]))
        assert client.download_series("1.2.3", "1.2.3.1", tmp_path / "out", skip_existing=True).error
    assert victim.read_bytes() == b"synthetic sentinel"


def test_dicom_duplicate_instance_uids_fail_without_publishing(tmp_path):
    ds = _instance("1.2.3.4")
    with requests.Session() as session:
        client = DICOMDownloader(auth=session, dicom_web_url="https://example.invalid", output_format="dicom")
        client.client = SimpleNamespace(iter_series=lambda **_: iter([ds, ds]))
        assert client.download_series("1.2.3", "1.2.3.1", tmp_path).error
    assert not list(tmp_path.rglob("*.dcm"))
