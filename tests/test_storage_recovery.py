"""Synthetic failure injection for download completion and S3 pagination."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from fyron._completion import marker_path, publish_files, verified_files
from fyron.core.s3 import S3Storage
from fyron.dicom.client import DICOMDownloader, _series_exists
from fyron.documents.client import DocumentDownloader


def test_completion_detects_corruption_and_preserves_conflicts(tmp_path):
    stage = tmp_path / "stage"
    target = tmp_path / "target"
    stage.mkdir()
    target.mkdir()
    (stage / "image.dcm").write_bytes(b"complete")
    publish_files(stage, target, "dicom:1", overwrite=False)
    assert verified_files(target, "dicom:1") == [target / "image.dcm"]
    (target / "image.dcm").write_bytes(b"damaged!")
    assert not verified_files(target, "dicom:1")
    (stage / "image.dcm").write_bytes(b"replacement")
    with pytest.raises(FileExistsError):
        publish_files(stage, target, "dicom:1", overwrite=False)
    assert (target / "image.dcm").read_bytes() == b"damaged!"
    publish_files(stage, target, "dicom:1", overwrite=True)
    assert verified_files(target, "dicom:1")


def test_manifest_rejects_traversal(tmp_path):
    marker_path(tmp_path, "test").write_text(json.dumps({"version": 1, "files": [{"name": "../outside"}]}))
    assert verified_files(tmp_path, "test") == []


def test_failed_multifile_commit_has_no_completion_record(tmp_path, monkeypatch):
    import fyron._completion as completion
    stage, target = tmp_path / "stage", tmp_path / "target"
    stage.mkdir()
    target.mkdir()
    for name in ("a", "b"):
        (stage / name).write_bytes(b"data")
    original = completion.os.link
    def failing_link(source, destination):
        if source.name == "b":
            raise OSError("synthetic write failure")
        original(source, destination)
    monkeypatch.setattr(completion.os, "link", failing_link)
    with pytest.raises(OSError):
        publish_files(stage, target, "test", overwrite=False)
    assert (target / "a").exists()
    assert not verified_files(target, "test")


def document_client(tmp_path, chunks, headers=None, skip=True):
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.headers = headers or {"Content-Type": "application/pdf"}
    response.status_code = 200
    response.iter_content.return_value = chunks
    session = requests.Session()
    session.get = Mock(return_value=response)
    return DocumentDownloader(auth=session, output_dir=tmp_path, skip_existing=skip), session


def test_document_interruption_does_not_publish(tmp_path):
    def chunks():
        yield b"partial"
        raise requests.ConnectionError("synthetic interruption")
    client, _ = document_client(tmp_path, chunks())
    result = client.download_url("https://example.org/report.pdf")
    assert result.error
    assert not list(tmp_path.rglob("*.pdf"))
    assert not list(tmp_path.rglob(".fyron-stage-*"))
    assert not list(tmp_path.rglob(".fyron-complete-*"))


def test_document_verified_restart_and_conflict(tmp_path):
    url = "https://example.org/report.pdf"
    client, session = document_client(tmp_path, [b"complete"])
    first = client.download_url(url)
    assert first.error is None
    assert client.download_url(url).skipped
    assert session.get.call_count == 1
    Path(first.path).write_bytes(b"partial")
    conflict = client.download_url(url)
    assert "unverified" in conflict.error
    assert Path(first.path).read_bytes() == b"partial"


def test_document_length_mismatch_preserves_existing(tmp_path):
    url = "https://example.org/report.pdf"
    client, _ = document_client(tmp_path, [b"old"])
    first = client.download_url(url)
    client, _ = document_client(tmp_path, [b"short"], {"Content-Length": "20", "Content-Type": "application/pdf"}, skip=False)
    assert client.download_url(url).error
    assert Path(first.path).read_bytes() == b"old"


def test_dicom_skip_requires_verified_series(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    target.mkdir()
    instance = source / "1.dcm"
    instance.write_bytes(b"synthetic instance")
    with DICOMDownloader(dicom_web_url="https://example.org", output_format="dicom") as client:
        result = client._store_series_files("1", "2", [instance], target, overwrite=False)
        assert result.error is None
        assert _series_exists(target, "dicom", "2")
        assert not _series_exists(target, "dicom", "3")
        (target / "1.dcm").unlink()
        assert not _series_exists(target, "dicom", "2")


def test_nifti_skip_honors_requested_reference(tmp_path):
    stage, target = tmp_path / "stage", tmp_path / "target"
    stage.mkdir()
    target.mkdir()
    (stage / "2.nii.gz").write_bytes(b"synthetic volume")
    publish_files(stage, target, "nifti:2", overwrite=False)
    assert _series_exists(target, "nifti", "2")
    assert not _series_exists(target, "nifti", "2", "meta.dcm")


def storage():
    value = S3Storage.__new__(S3Storage)
    value.bucket, value.prefix = "synthetic", ""
    value.client = Mock()
    return value


@pytest.mark.parametrize("status", [404, 403, 500])
def test_s3_exists_only_hides_not_found(status):
    ClientError = pytest.importorskip("botocore.exceptions").ClientError
    value = storage()
    value.client.head_object.side_effect = ClientError({"Error": {"Code": str(status)}, "ResponseMetadata": {"HTTPStatusCode": status}}, "HeadObject")
    if status == 404:
        assert value.exists("object") is False
    else:
        with pytest.raises(ClientError):
            value.exists("object")


def test_s3_pagination_suffix_and_global_limit():
    value = storage()
    value.client.list_objects_v2.side_effect = [
        {"Contents": [{"Key": "a.txt"}], "IsTruncated": True, "NextContinuationToken": "next"},
        {"Contents": [{"Key": "b.csv"}, {"Key": "c.csv"}], "IsTruncated": True, "NextContinuationToken": "last"},
    ]
    assert [r["Key"] for r in value.list(suffix=".csv", max_keys=2)] == ["b.csv", "c.csv"]
    assert value.client.list_objects_v2.call_args.kwargs["ContinuationToken"] == "next"
    value.client.list_objects_v2.reset_mock()
    assert value.list(max_keys=0) == []
    value.client.list_objects_v2.assert_not_called()


def test_s3_repeated_continuation_raises():
    value = storage()
    value.client.list_objects_v2.return_value = {"IsTruncated": True, "NextContinuationToken": "same"}
    with pytest.raises(RuntimeError):
        value.list()
    assert value.client.list_objects_v2.call_count == 2
