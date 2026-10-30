"""Tests for Fyron core IO helpers."""

from __future__ import annotations

import importlib
import json
import sys
import types

import pandas as pd
import pytest

from fyron.core import (
    DataIO,
    TeableClient,
    describe_file,
    ensure_parent_dir,
    read_json,
    read_table,
    summarize_table,
    write_json,
    write_table,
)


def test_json_and_table_helpers_roundtrip(tmp_path) -> None:
    payload = {"study": "demo", "n": 2}
    json_path = write_json(payload, tmp_path / "nested" / "manifest.json")
    assert json_path.exists()
    assert read_json(json_path) == payload

    df = pd.DataFrame({"patient_id": ["p1", "p2"], "value": [1.0, None]})
    csv_path = write_table(df, tmp_path / "tables" / "cohort.csv")
    tsv_path = write_table(df, tmp_path / "tables" / "cohort.tsv")
    jsonl_path = write_table(df, tmp_path / "tables" / "cohort.jsonl")

    assert read_table(csv_path).shape == (2, 2)
    assert read_table(tsv_path).shape == (2, 2)
    assert read_table(jsonl_path).shape == (2, 2)
    assert DataIO.read_table(csv_path).equals(read_table(csv_path))


def test_table_summary_file_description_and_unsupported_format(tmp_path) -> None:
    output = ensure_parent_dir(tmp_path / "a" / "b" / "table.csv")
    assert output.parent.exists()

    df = pd.DataFrame({"a": [1, 1], "b": [None, None]})
    summary = summarize_table(df, name="demo")
    assert summary["name"] == "demo"
    assert summary["rows"] == 2
    assert summary["missing_cells"] == 2
    assert summary["duplicate_rows"] == 1

    write_table(df, output)
    description = describe_file(output)
    assert description["exists"] is True
    assert description["suffix"] == ".csv"
    assert description["size_bytes"] > 0

    with pytest.raises(ValueError, match="Unsupported table format"):
        write_table(df, tmp_path / "table.parquet")


def test_teable_cohort_helpers_validate_and_summarize(monkeypatch) -> None:
    client = TeableClient.__new__(TeableClient)
    df = pd.DataFrame({"patient_id": ["p1", "p2"], "age": [50, 60]})
    calls = {}

    monkeypatch.setattr(client, "read_table", lambda table_id, **kwargs: df)
    assert client.read_cohort("tbl", id_col="patient_id", required_columns=["age"]).equals(df)
    with pytest.raises(ValueError, match="Missing required"):
        client.read_cohort("tbl", required_columns=["missing"])

    def fake_write(table_id, frame, **kwargs):
        calls["write"] = (table_id, len(frame), kwargs)
        return ["rec1", "rec2"]

    def fake_overwrite(table_id, frame, **kwargs):
        calls["overwrite"] = (table_id, len(frame), kwargs)
        return ["rec3", "rec4"]

    monkeypatch.setattr(client, "write_dataframe", fake_write)
    monkeypatch.setattr(client, "overwrite_table", fake_overwrite)

    summary = client.write_research_cohort("tbl", df, cohort_name="locked", version="v1", id_col="patient_id")
    assert summary["mode"] == "append"
    assert summary["rows"] == 2
    assert summary["record_ids"] == ["rec1", "rec2"]

    overwrite = client.write_research_cohort("tbl", df, mode="overwrite")
    assert overwrite["record_ids"] == ["rec3", "rec4"]

    monkeypatch.setattr(client, "create_table", lambda **kwargs: {"id": "tbl", **kwargs})
    created = client.create_research_cohort_table(base_id="base", name="Final cohort", df=df)
    assert created["table"]["id"] == "tbl"
    assert {field["name"] for field in created["fields"]} == {"patient_id", "age"}

    table_summary = client.summarize_teable_table("tbl")
    assert table_summary["table_id"] == "tbl"
    assert table_summary["rows"] == 2


def test_teable_cohort_duplicate_ids_raise(monkeypatch) -> None:
    client = TeableClient.__new__(TeableClient)
    monkeypatch.setattr(client, "read_table", lambda table_id, **kwargs: pd.DataFrame({"patient_id": ["p1", "p1"]}))
    with pytest.raises(ValueError, match="duplicate"):
        client.read_cohort("tbl", id_col="patient_id")


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def read(self) -> bytes:
        return self.data


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.uploads: list[tuple[str, str, str]] = []
        self.endpoint_url = None

    def put_object(self, **kwargs):
        self.objects[(kwargs["Bucket"], kwargs["Key"])] = kwargs["Body"]
        return {}

    def get_object(self, Bucket, Key):
        return {"Body": FakeBody(self.objects[(Bucket, Key)])}

    def head_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise KeyError(Key)
        return {}

    def list_objects_v2(self, **kwargs):
        prefix = kwargs.get("Prefix", "")
        return {
            "Contents": [
                {"Key": key, "Size": len(value)}
                for (bucket, key), value in self.objects.items()
                if bucket == kwargs["Bucket"] and key.startswith(prefix)
            ]
        }

    def download_file(self, bucket, key, filename):
        with open(filename, "wb") as handle:
            handle.write(self.objects[(bucket, key)])

    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        with open(filename, "rb") as handle:
            self.objects[(bucket, key)] = handle.read()
        self.uploads.append((filename, bucket, key))


def _install_fake_boto3(monkeypatch):
    fake_client = FakeS3Client()

    class FakeSession:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def client(self, service, **kwargs):
            assert service == "s3"
            fake_client.endpoint_url = kwargs.get("endpoint_url")
            return fake_client

    fake_boto3 = types.SimpleNamespace(Session=FakeSession)
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    return fake_client


def test_s3_storage_with_mocked_boto3(monkeypatch, tmp_path) -> None:
    fake_client = _install_fake_boto3(monkeypatch)
    s3 = importlib.reload(importlib.import_module("fyron.core.s3"))

    storage = s3.S3Storage(bucket="bucket", prefix="project", endpoint_url="https://minio.example.org")
    assert fake_client.endpoint_url == "https://minio.example.org"

    assert storage.write_json("manifest.json", {"ok": True}) == "s3://bucket/project/manifest.json"
    assert storage.exists("manifest.json") is True
    assert storage.read_json("manifest.json") == {"ok": True}

    df = pd.DataFrame({"patient_id": ["p1"], "value": [1.2]})
    storage.write_table("cohort.csv", df)
    assert storage.read_table("cohort.csv").shape == (1, 2)
    assert storage.list(suffix=".csv")[0]["Key"] == "project/cohort.csv"

    local = storage.download_file("cohort.csv", tmp_path / "downloads" / "cohort.csv")
    assert local.exists()
    uploaded = storage.upload_file(local, "copy.csv")
    assert uploaded == "s3://bucket/project/copy.csv"
    assert s3.parse_s3_uri("s3://bucket/path/table.csv") == {"bucket": "bucket", "key": "path/table.csv"}


def test_s3_missing_boto3_raises_clear_import_error(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "boto3", None)
    s3 = importlib.reload(importlib.import_module("fyron.core.s3"))
    with pytest.raises(ImportError, match='fyron\\[s3\\]'):
        s3.S3Storage(bucket="bucket")
