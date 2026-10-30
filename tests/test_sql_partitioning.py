"""Tests for SQL partition helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from fyron.fhir.sql import FHIRSQLClient, SQLQueryError, build_sql_partitions


def _client_with_stream(fake_stream):
    client = object.__new__(FHIRSQLClient)
    client.query_df_stream = fake_stream  # type: ignore[method-assign]
    return client


def test_build_sql_partitions_yearly_monthly_and_grid() -> None:
    yearly = build_sql_partitions(start="2020-01-01", end="2022-01-01", frequency="YS")
    assert len(yearly) == 2
    assert yearly[0].params["start_ts"] == "2020-01-01"
    assert yearly[0].params["end_ts"] == "2021-01-01"

    monthly = build_sql_partitions(start="2020-01-01", end="2020-03-01", frequency="MS")
    assert len(monthly) == 2
    assert monthly[1].metadata["_fyron_partition_start"] == "2020-02-01"

    grid = build_sql_partitions(
        start="2020-01-01",
        end="2020-01-03",
        window_days=1,
        param_grid={"med": ["heparin", "xarelto"]},
        derived_params={"med_pattern": lambda p: f"%{p['med']}%"},
    )
    assert len(grid) == 4
    assert grid[0].params["med_pattern"] == "%heparin%"
    assert grid[1].metadata["_fyron_partition_med"] == "xarelto"


def test_query_df_partitioned_merges_and_adds_metadata() -> None:
    seen_params = []

    def fake_stream(sql, params=None, rename=None, chunksize=10000):
        seen_params.append(params)
        yield pd.DataFrame({"value": [params["med"]], "start": [params["start_ts"]]})

    client = _client_with_stream(fake_stream)
    result = client.query_df_partitioned(
        "select 1",
        start="2020-01-01",
        end="2020-01-03",
        window_days=1,
        param_grid={"med": ["a", "b"]},
    )

    assert len(result) == 4
    assert set(result["value"]) == {"a", "b"}
    assert "_fyron_partition_start" in result.columns
    assert seen_params[0]["start_ts"] == "2020-01-01"


def test_query_df_partitioned_records_errors() -> None:
    def fake_stream(sql, params=None, rename=None, chunksize=10000):
        if params["med"] == "bad":
            raise SQLQueryError("boom")
        yield pd.DataFrame({"value": [params["med"]]})

    client = _client_with_stream(fake_stream)
    result = client.query_df_partitioned(
        "select 1",
        start="2020-01-01",
        end="2020-01-02",
        window_days=1,
        param_grid={"med": ["ok", "bad"]},
        errors="record",
        continue_on_error=True,
    )

    assert "ok" in set(result["value"].dropna())
    assert "error" in set(result["_fyron_partition_status"].dropna())


def test_export_query_partitioned_writes_parts_skips_and_combines(tmp_path: Path) -> None:
    calls = []

    def fake_stream(sql, params=None, rename=None, chunksize=10000):
        calls.append(dict(params))
        yield pd.DataFrame(
            {
                "patient_id": [f"p-{params['med']}"],
                "matched_medication": [params["med"]],
            }
        )

    client = _client_with_stream(fake_stream)
    manifest = client.export_query_partitioned(
        "select 1",
        tmp_path,
        start="2020-01-01",
        end="2020-01-03",
        window_days=1,
        param_grid={"med": ["a", "b"]},
        output_columns=["patient_id", "matched_medication"],
        part_filename="{year}/{date}_{med}.csv",
        combine_by="year",
        combined_filename="medication_requests_{year}.csv",
    )

    assert len(manifest) == 4
    assert set(manifest["status"]) == {"ok"}
    assert (tmp_path / "_parts" / "2020" / "2020-01-01_a.csv").is_file()
    combined = pd.read_csv(tmp_path / "medication_requests_2020.csv")
    assert len(combined) == 4

    second = client.export_query_partitioned(
        "select 1",
        tmp_path,
        start="2020-01-01",
        end="2020-01-03",
        window_days=1,
        param_grid={"med": ["a", "b"]},
        output_columns=["patient_id", "matched_medication"],
        part_filename="{year}/{date}_{med}.csv",
    )
    assert set(second["status"]) == {"skipped"}
    assert len(calls) == 4


def test_export_query_partitioned_records_errors(tmp_path: Path) -> None:
    def fake_stream(sql, params=None, rename=None, chunksize=10000):
        if params["med"] == "bad":
            raise SQLQueryError("boom")
        yield pd.DataFrame({"patient_id": ["p1"], "matched_medication": [params["med"]]})

    client = _client_with_stream(fake_stream)
    manifest = client.export_query_partitioned(
        "select 1",
        tmp_path,
        start="2020-01-01",
        end="2020-01-02",
        window_days=1,
        param_grid={"med": ["ok", "bad"]},
        output_columns=["patient_id", "matched_medication"],
        part_filename="{date}_{med}.csv",
        continue_on_error=True,
    )

    assert set(manifest["status"]) == {"ok", "error"}
    assert manifest.loc[manifest["status"] == "error", "message"].iloc[0]


def test_fhir_sql_client_partitioned_methods_are_available() -> None:
    assert hasattr(FHIRSQLClient, "query_df_partitioned")
    assert hasattr(FHIRSQLClient, "export_query_partitioned")
