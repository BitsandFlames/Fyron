"""Tests for fyron.cohort."""

from __future__ import annotations

import pandas as pd

from fyron.cohort import (
    build_survival_columns,
    build_time_to_event_endpoint,
    cohort_profile,
    join_cohort_tables,
    validate_cohort_table,
)


def test_join_cohort_tables() -> None:
    features = pd.DataFrame({"patient_id": ["p1", "p2"], "age": [50, 60]})
    outcomes = pd.DataFrame({"patient_id": ["p1", "p2"], "event": [1, 0]})
    merged = join_cohort_tables(features, outcomes)
    assert merged.shape == (2, 3)


def test_validate_cohort_table() -> None:
    df = pd.DataFrame({"patient_id": ["a"], "time": [1.0], "event": [1]})
    assert validate_cohort_table(df, required_columns=["time", "event"]).equals(df)


def test_build_survival_columns() -> None:
    df = pd.DataFrame(
        {
            "start": pd.to_datetime(["2020-01-01", "2020-01-01"]),
            "end": pd.to_datetime(["2020-07-01", "2020-04-01"]),
            "died": [1, 0],
        }
    )
    out = build_survival_columns(df, start_col="start", end_col="end", event_col="died")
    assert out["time"].iloc[0] > out["time"].iloc[1]
    assert out["event"].tolist() == [1, 0]


def test_build_time_to_event_endpoint_event_and_censor() -> None:
    df = pd.DataFrame(
        {
            "patient_id": ["p1", "p2", "p3"],
            "index": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-01-01"]),
            "event_date": pd.to_datetime(["2020-02-01", None, "2020-05-01"]),
            "last_followup": pd.to_datetime(["2020-03-01", "2020-04-01", "2020-04-01"]),
        }
    )
    out = build_time_to_event_endpoint(
        df,
        index_date_col="index",
        event_date_col="event_date",
        censor_date_col="last_followup",
    )
    assert out["event"].tolist() == [1, 0, 0]
    assert out["endpoint_source"].tolist() == ["event", "censor", "censor"]
    assert out.loc[1, "time"] == 91.0


def test_build_time_to_event_endpoint_negative_time_raises() -> None:
    df = pd.DataFrame(
        {
            "index": pd.to_datetime(["2020-02-01"]),
            "event_date": pd.to_datetime(["2020-01-01"]),
            "last_followup": pd.to_datetime([None]),
        }
    )
    try:
        build_time_to_event_endpoint(
            df,
            index_date_col="index",
            event_date_col="event_date",
            censor_date_col="last_followup",
        )
    except ValueError as exc:
        assert "Negative endpoint times" in str(exc)
    else:
        raise AssertionError("Expected negative endpoint time to fail")


def test_cohort_profile() -> None:
    df = pd.DataFrame(
        {
            "patient_id": ["p1", "p1", "p2", None],
            "event": [1, 0, 1, None],
            "arm": ["A", "A", "B", "B"],
        }
    )
    profile = cohort_profile(df, endpoint_cols=["event"], group_col="arm")
    values = dict(zip(profile["metric"], profile["value"]))
    assert values["rows"] == 4
    assert values["duplicate_id_rows"] == 2
    assert values["event.sum"] == 2
    assert values["arm.A.n"] == 2
