"""Explicit date, endpoint, and join-audit contracts using synthetic data."""

import numpy as np
import pandas as pd
import pytest

from fyron.dataframe import date_difference, add_date_difference, age_at_date, add_time_window_flag
from fyron.cohort import (
    audit_cohort_join, audit_time_to_event_endpoint, build_time_to_event_endpoint,
    build_survival_columns, join_cohort_tables,
)


OPTIONS = dict(index_date_col="start", event_date_col="event_date", censor_date_col="followup")


def test_date_parity_and_units():
    start = pd.Series(pd.to_datetime(["2020-02-28", "2020-01-01"]), index=[8, 2])
    end = pd.Series(pd.to_datetime(["2020-03-01", "2020-01-01 12:00"], format="mixed"), index=[8, 2])
    for unit, divisor in [("days", 1), ("weeks", 7), ("months", 30.4375), ("years", 365.25)]:
        result = date_difference(start, end, unit=unit)
        assert result.index.equals(start.index)
        np.testing.assert_allclose(result, np.array([2, .5]) / divisor)
    assert date_difference("2020-01-01", end).index.equals(end.index)
    assert date_difference(start, "2020-03-01").tolist() == [2, 60]
    assert date_difference("2020-01-01", "2020-01-02").tolist() == [1]
    with pytest.raises(ValueError, match="indices"):
        date_difference(start, end.reset_index(drop=True))
    with pytest.raises(ValueError, match="lengths"):
        date_difference(["2020-01-01"], ["2020-01-02", "2020-01-03"])


def test_missing_malformed_and_strict_wrappers():
    assert date_difference([None, "bad"], "2020-01-01").isna().all()
    assert date_difference("9999-01-01", "2020-01-01").isna().all()
    assert date_difference(None, "2020-01-01", errors="raise").isna().all()
    frame = pd.DataFrame({"a": ["bad"], "b": ["2020-01-01"]})
    for call in [lambda: date_difference(frame.a, frame.b, errors="raise"),
                 lambda: add_date_difference(frame, "a", "b", "d", errors="raise"),
                 lambda: age_at_date(frame, "a", "b", errors="raise"),
                 lambda: add_time_window_flag(frame, "a", "b", "w", after=1, errors="raise")]:
        with pytest.raises(ValueError, match="invalid dates"):
            call()
    assert add_time_window_flag(frame, "a", "b", "w", after=1).w.tolist() == [0]
    for bound in [-1, np.inf, np.nan]:
        with pytest.raises(ValueError, match="finite and nonnegative"):
            add_time_window_flag(frame, "a", "b", "w", before=bound)


def test_timezone_offsets_and_dst():
    assert date_difference("2024-03-31T01:30:00+01:00", "2024-03-31T03:30:00+02:00").iloc[0] == pytest.approx(1/24)
    assert date_difference(["2024-01-01T00:00:00Z", "2024-01-01T02:00:00+02:00"],
                           "2024-01-02T00:00:00Z").tolist() == [1, 1]
    with pytest.raises(ValueError, match="naive"):
        date_difference("2024-01-01", "2024-01-02T00:00:00Z")


def test_endpoint_cutoff_and_audit_agree():
    frame = pd.DataFrame({
        "start": ["2020-01-01"] * 7,
        "event_date": ["2020-01-03", "2020-01-05", "2020-01-07", None, None, "2020-01-01", "2020-01-04"],
        "followup": ["2020-01-08", "2020-01-05", "2020-01-06", "2020-01-10", None, None, None],
    }, index=[7, 7, 5, 4, 3, 2, 1])
    original = frame.copy(deep=True)
    options = dict(**OPTIONS, administrative_censor_date="2020-01-05")
    audit = audit_time_to_event_endpoint(frame, **options)
    result = build_time_to_event_endpoint(frame, **options, require_endpoint=False)
    for col in ["time", "event", "endpoint_date", "endpoint_source"]:
        pd.testing.assert_series_equal(result[col], audit["rows"][col])
    assert result.event.tolist() == [1, 1, 0, 0, 0, 1, 1]
    np.testing.assert_allclose(result.time, [2, 4, 4, 4, np.nan, 0, 3], equal_nan=True)
    assert audit["rows"].valid_endpoint.tolist() == [True, True, True, True, False, True, True]
    assert audit["rows"].positive_duration_eligible.tolist() == [True, True, True, True, False, False, True]
    assert audit["rows"].cutoff_truncated.sum() == 2
    assert audit["rows"].event_censor_tie.sum() == 1
    assert audit["rows"].event_after_followup.sum() == 1
    counts = audit["summary"].set_index("metric")["count"]
    assert counts.valid_events == 4 and counts.valid_censored == 2
    pd.testing.assert_frame_equal(frame, original)
    with pytest.raises(ValueError, match="neither"):
        build_time_to_event_endpoint(frame, **options)


def test_malformed_endpoint_audit_and_negative_chronology():
    frame = pd.DataFrame({"start": ["2020-01-02", None, "invalid", "2020-01-02"],
                          "event_date": ["invalid", None, None, "2020-01-01"],
                          "followup": ["2020-01-03", None, None, None]})
    rows = audit_time_to_event_endpoint(frame, **OPTIONS)["rows"]
    assert not rows.valid_endpoint.any()
    assert rows.invalid_event_date.tolist() == [True, False, False, False]
    assert rows.missing_index_date.sum() == 1 and rows.invalid_index_date.sum() == 1
    assert rows.event_before_index.sum() == rows.negative_followup.sum() == 1
    with pytest.raises(ValueError, match="invalid dates"):
        build_time_to_event_endpoint(frame, **OPTIONS)
    with pytest.raises(ValueError, match="Negative endpoint"):
        build_time_to_event_endpoint(frame.iloc[[3]], **OPTIONS)


def test_empty_cutoffs_and_output_conflicts():
    frame = pd.DataFrame({"start": ["2020-01-01"], "event_date": ["2020-01-03"], "followup": [None]})
    empty = frame.iloc[:0]
    assert audit_time_to_event_endpoint(empty, **OPTIONS)["rows"].empty
    assert build_time_to_event_endpoint(empty, **OPTIONS).empty
    for cutoff in ["bad", pd.NaT, ["2020-01-04"]]:
        with pytest.raises(ValueError):
            audit_time_to_event_endpoint(empty, **OPTIONS, administrative_censor_date=cutoff)
    for kwargs in [dict(time_col="start"), dict(event_col="time"), dict(endpoint_source_col="followup")]:
        with pytest.raises(ValueError, match="output"):
            build_time_to_event_endpoint(frame, **OPTIONS, **kwargs)
    with pytest.raises(ValueError, match="Negative endpoint"):
        build_time_to_event_endpoint(frame, **OPTIONS, administrative_censor_date="2019-01-01")
    numeric = pd.DataFrame({"start": [1], "end": [3], "died": [1]})
    result = build_survival_columns(numeric, start_col="start", end_col="end", event_col="died")
    assert result.time.tolist() == [2]
    with pytest.raises(ValueError, match="output"):
        build_survival_columns(numeric, start_col="start", end_col="end", event_col="died", time_col="start")


@pytest.mark.parametrize("left,right", [(["a", "a", "b"], ["a", "a", "c"]),
                                         (["a", None, None], ["a", None]), ([], []),
                                         (["a"], []), ([], ["a"])])
def test_join_audit_matches_pandas_without_mutation(left, right):
    features = pd.DataFrame({"patient_id": pd.Series(left, dtype=object)})
    outcomes = pd.DataFrame({"patient_id": pd.Series(right, dtype=object)})
    original = features.copy(deep=True)
    report = audit_cohort_join(features, outcomes).set_index("metric")["count"]
    for how in ["inner", "left", "right", "outer"]:
        assert report[f"expected.{how}_rows"] == len(features.merge(outcomes, on="patient_id", how=how))
    assert report["features.missing_key_rows"] == features.patient_id.isna().sum()
    assert report["features.duplicate_key_rows"] == features.patient_id.dropna().duplicated(keep=False).sum()
    pd.testing.assert_frame_equal(features, original)
    if features.patient_id.isna().any() or outcomes.patient_id.isna().any():
        with pytest.raises(ValueError, match="missing"):
            join_cohort_tables(features, outcomes)


def test_join_validation_unchanged():
    left = pd.DataFrame({"patient_id": ["a", "a"]})
    right = pd.DataFrame({"patient_id": ["a", "a"]})
    assert audit_cohort_join(left, right).set_index("metric").loc["expected.inner_rows", "count"] == 4
    with pytest.raises(pd.errors.MergeError):
        join_cohort_tables(left, right)
