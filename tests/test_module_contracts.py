"""Scientific contracts and opt-in extraction report regressions."""

import json
from unittest.mock import Mock
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import requests

from fyron.boa_extraction import extract_boa_features, extract_cohort_body_region_features
from fyron.imaging.segmentation import (
    dice_score, hausdorff_distance, surface_dice, volume_difference, segmentation_metric_table,
)
from fyron.imaging.qc import summarize_mask_volume
from fyron.phenotyping import combine_phenotypes, phenotype_summary, define_code_phenotype
from fyron.preprocessing import fit_categorical_encoder, apply_categorical_encoder
from fyron.fhir import rest


@pytest.mark.parametrize("spacing", [None, (1, 2), (1, 0, 2), (1, -1, 2), (1, np.nan, 2), (1, np.inf, 2)])
def test_physical_volume_requires_valid_spacing(spacing):
    mask = np.zeros((2, 2, 2))
    with pytest.raises(ValueError):
        volume_difference(mask, mask, spacing=spacing)
    with pytest.raises(ValueError):
        segmentation_metric_table(mask, mask, spacing=spacing)
    with pytest.raises(ValueError):
        summarize_mask_volume(mask, spacing=spacing)


def test_anisotropic_units_and_empty_masks():
    a, b = np.zeros((3, 3, 3)), np.zeros((3, 3, 3))
    a[0, 0, 0], b[1, 0, 0] = 1, 1
    assert hausdorff_distance(a, b, spacing=(4, 2, 1)) == 4
    assert volume_difference(a, b, spacing=(4, 2, 1))["true_volume_ml"] == .008
    empty = np.zeros_like(a)
    assert dice_score(empty, empty) == 1
    assert surface_dice(empty, empty) == 1
    assert surface_dice(a, empty) == 0
    assert np.isnan(hausdorff_distance(empty, empty))
    assert np.isnan(volume_difference(empty, a, spacing=(1, 1, 1))["relative_difference_percent"])
    with pytest.raises(ValueError):
        volume_difference(a[0], b[0], spacing=(1, 1))


@pytest.mark.parametrize("value", [-1, np.inf, np.nan])
def test_invalid_surface_tolerances(value):
    a = np.zeros((2, 2, 2))
    with pytest.raises(ValueError):
        surface_dice(a, a, tolerance=value)
    with pytest.raises(ValueError):
        segmentation_metric_table(a, a, spacing=(1, 1, 1), surface_tolerance=value)


@pytest.mark.parametrize("value", [-1, 101, np.inf, np.nan])
def test_invalid_percentiles(value):
    with pytest.raises(ValueError):
        hausdorff_distance(np.zeros((2, 2)), np.zeros((2, 2)), percentile=value)


def test_encoder_unknowns_only_use_fitted_rare_level():
    train = pd.DataFrame({"category": ["a", "a", "b", "b"]})
    unknown = pd.DataFrame({"category": ["c", None]}, index=[12, 8])
    encoder = fit_categorical_encoder(train, rare_min_count=2)
    assert apply_categorical_encoder(unknown, encoder).to_numpy().sum() == 0
    encoder = fit_categorical_encoder(train.iloc[:3], rare_min_count=2)
    actual = apply_categorical_encoder(unknown, encoder)
    assert actual.index.tolist() == [12, 8]
    assert actual.to_numpy().sum() == 2
    assert unknown.iloc[0, 0] == "c"
    dropped = fit_categorical_encoder(train, drop_first=True)
    result = apply_categorical_encoder(pd.DataFrame({"category": ["a", "unknown"]}), dropped)
    assert result.iloc[0].equals(result.iloc[1])


@pytest.mark.parametrize("flags", [[True, None], [0, 2], ["False", "True"], [0, np.inf]])
def test_bad_phenotype_flags(flags):
    table = pd.DataFrame({"patient_id": ["a", "b"], "flag": flags})
    with pytest.raises(ValueError):
        combine_phenotypes([table])
    with pytest.raises(ValueError):
        phenotype_summary(table, "flag")


def test_patient_level_ambiguity_and_evidence():
    table = pd.DataFrame({"patient_id": ["a", "a"], "flag": [True, False]})
    with pytest.raises(ValueError):
        phenotype_summary(table, "flag")
    with pytest.raises(ValueError):
        combine_phenotypes([table])
    with pytest.raises(ValueError):
        combine_phenotypes([pd.DataFrame({"patient_id": [None], "flag": [True]})])
    with pytest.raises(ValueError):
        combine_phenotypes([pd.DataFrame({"patient_id": ["a"], "flag": [True], "other": [False]})])
    with pytest.raises(ValueError):
        combine_phenotypes([pd.DataFrame({"patient_id": ["a"], "flag": [True], "other": [1]})])
    consistent = table.assign(flag=True)
    assert phenotype_summary(consistent, "flag").loc[0, "n_patients"] == 1
    evidence = pd.DataFrame({"patient_id": ["a", "a", "b"], "code": ["X", "X", "X.1"]})
    result = define_code_phenotype(evidence, "code", ["X"])
    assert result["patient_id"].tolist() == ["a"]
    assert result.loc[0, "evidence_count"] == 2


def _case(tmp_path, name, content):
    case = tmp_path / name
    case.mkdir()
    (case / "bca-measurements.json").write_text(json.dumps(content))
    return case


@pytest.mark.parametrize("num_workers", [1, 2])
def test_boa_reports_agree_with_data_and_preserve_generators(tmp_path, num_workers):
    good = _case(tmp_path, "good", {"aggregated": {"abdominal_cavity": {
        "measurements_no_extremities": {"muscle": {"sum": 10}}}}})
    bad = _case(tmp_path, "bad", [])
    missing = tmp_path / "missing"
    kwargs = dict(body_regions=["abdominal_cavity"], tissues=["muscle"], include_sma=False,
                  include_derived_markers=False)
    result = extract_boa_features((p for p in [good, bad, missing]),
        body_region_kwargs=kwargs, return_report=True, show_progress=False, num_workers=num_workers)
    assert result["data"]["download_id"].tolist() == ["good"]
    rows = result["report"]["rows"]
    assert len(rows) == 6
    assert rows.loc[rows.family == "body_regions"].set_index("download_id")["status"].to_dict() == {
        "good": "success", "bad": "invalid_measurements", "missing": "missing_inputs"}
    assert (rows.loc[rows.family == "total", "status"] == "missing_inputs").all()
    plain = extract_cohort_body_region_features([good], show_progress=False, **kwargs)
    pd.testing.assert_frame_equal(plain, result["data"])
    empty = extract_boa_features([], return_report=True, show_progress=False)
    assert empty["data"].empty and empty["report"]["rows"].empty
    with pytest.raises(ValueError, match="unique"):
        extract_boa_features([good, good], show_progress=False)
    partial = extract_cohort_body_region_features([good], return_report=True, show_progress=False)
    assert partial["report"]["rows"].loc[0, "status"] == "partial"


def _bundle(value, next_link=False):
    result = {"resourceType": "Bundle", "entry": [{"resource": {"resourceType": "Patient", "id": value}}]}
    if next_link:
        result["link"] = [{"relation": "next", "url": "?page=2"}]
    return result


def test_fhir_parallel_association_metadata_and_completeness(monkeypatch):
    client = rest.FHIRRestClient(base_url="https://example.test/fhir", auth=requests.Session(), num_processes=2)
    client._fetch_parallel_jobs = Mock(return_value=[
        (2, [_bundle("c", True)]), (0, [_bundle("a")]), (1, [])])
    source = pd.DataFrame({"input_id": ["same", "same", "third"]}, index=[9, 4, 9])
    result = client.query_df_from(source, "Patient", {"_id": "input_id"}, parallel_fetch=True,
        include_column_map_columns=True, param_prefix={"_id": "Patient/"},
        use_multiprocessing=False, return_report=True, show_progress=False)
    assert result["data"]["id"].tolist() == ["a", "c"]
    assert result["data"]["input_id"].tolist() == ["same", "third"]
    assert result["report"]["rows"]["status"].tolist() == ["success", "no_match", "page_limit"]
    assert not result["report"]["summary"].loc[0, "retrieval_exhaustive"]
    assert source.index.tolist() == [9, 4, 9]
    assert client._fetch_parallel_jobs.call_args.kwargs["param_list"][0]["_id"] == "Patient/same"
    client._fetch_parallel_jobs = Mock(return_value=[(0, [_bundle("a")])])
    with pytest.raises(rest.FHIRRequestError, match="incomplete"):
        client.query_df_from(source, "Patient", {"_id": "input_id"}, parallel_fetch=True,
                             use_multiprocessing=False, show_progress=False)


@pytest.mark.parametrize("method", ["query_to_dataframe", "query_df", "search_df"])
def test_fhir_zero_pages_report(method):
    client = rest.FHIRRestClient(base_url="https://example.test", auth=requests.Session())
    client.session.get = Mock(side_effect=AssertionError("Unexpected HTTP"))
    result = getattr(client, method)("Patient", max_pages=0, use_multiprocessing=False, return_report=True)
    assert result["report"]["rows"].loc[0, "status"] == "not_requested"
    assert not result["report"]["summary"].loc[0, "retrieval_exhaustive"]


def test_fhir_metadata_collisions():
    client = rest.FHIRRestClient(base_url="https://example.test", auth=requests.Session())
    with pytest.raises(ValueError, match="conflicts"):
        client.bundles_to_dataframe([_bundle("a")], use_multiprocessing=False,
                                   per_bundle_metadata=[{"id": "original"}])
    inputs = pd.DataFrame({"input_id": [2**60 + 1], "other": [1.5]})
    client.fetch_bundles = Mock(return_value=iter([_bundle("a")]))
    result = client.query_df_from(inputs, "Patient", {"_id": "input_id"},
        include_column_map_columns=True, use_multiprocessing=False, show_progress=False)
    assert result["input_id"].iloc[0] == 2**60 + 1


@pytest.mark.parametrize("method", ["query_to_dataframe_partitioned", "query_df_partitioned", "search_df_partitioned"])
def test_partition_reports_and_metadata(method):
    client = rest.FHIRRestClient(base_url="https://example.test", auth=requests.Session(), num_processes=2)
    client._fetch_parallel_jobs = Mock(return_value=[(1, [_bundle("b")]), (0, [_bundle("a")])])
    result = getattr(client, method)(
        "Patient", "_lastUpdated", "2020-01-01", "2022-01-01",
        parallel_fetch=True, return_report=True, use_multiprocessing=False, show_progress=False,
    )
    assert result["data"]["id"].tolist() == ["a", "b"]
    assert result["report"]["rows"]["job"].tolist() == [0, 1]
    assert result["report"]["summary"].loc[0, "retrieval_exhaustive"]
    assert any("partition" in col for col in result["data"].columns)


def test_fhir_worker_session_reused_and_closed(monkeypatch):
    rest._close_worker_session()
    session = requests.Session()
    close = Mock(wraps=session.close)
    session.close = close
    factory = Mock(return_value=session)
    monkeypatch.setattr(rest.requests, "Session", factory)
    monkeypatch.setattr(rest.mp, "current_process", lambda: SimpleNamespace(name="SpawnPoolWorker"))
    monkeypatch.setattr(rest, "_request_json", Mock(return_value=(_bundle("a"), "https://example.test/Patient", 200, 0)))
    args = ("https://example.test", rest.QueryJob("Patient", {}, 1), {}, 30, {}, False, False,
            "none", None, None, None, 0, 0)
    try:
        rest._worker_fetch_bundles(args)
        rest._worker_fetch_bundles(args)
        assert factory.call_count == 1
        close.assert_not_called()
    finally:
        rest._close_worker_session()
    close.assert_called_once()
