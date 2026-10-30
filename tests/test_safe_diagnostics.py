"""Network diagnostics must not serialize provider or clinical content."""

import io
import json
import logging
import traceback
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from fyron._diagnostics import batch_report, completed_task, event, safe_error, safe_network_errors
from fyron.console import configure_logging
from fyron.dicom.client import DICOMDownloader
from fyron.documents.client import DocumentDownloader
from fyron.fhir.rest import FHIRRequestError, _request_json

SECRET = "synthetic-sensitive-content"


@pytest.mark.parametrize("status,category", [(401, "authentication"), (403, "permission"), (500, "unexpected_response")])
def test_safe_http_errors(status, category):
    response = requests.Response()
    response.status_code = status
    response.url = "https://example.org/" + SECRET
    response._content = SECRET.encode()
    error = requests.HTTPError(SECRET, response=response)
    message = safe_error(error)
    assert category in message and str(status) in message
    assert SECRET not in message
    assert SECRET not in DICOMDownloader._format_exception(None, error)


@pytest.mark.parametrize("json_logs", [False, True])
def test_structured_events_are_safe(json_logs):
    stream = io.StringIO()
    logger = configure_logging(json=json_logs, color=False, stream=stream)
    try:
        event(logger, "dicom", "failed", http_status=403, error_category="permission", url=SECRET, body=SECRET)
        output = stream.getvalue()
        assert SECRET not in output
        if json_logs:
            record = json.loads(output)
            assert record["http_status"] == 403
            assert record["time"].endswith("+00:00")
    finally:
        logger.handlers.clear()
        logger.propagate = True


def test_application_handler_and_nested_exception():
    stream = io.StringIO()
    logger = logging.getLogger("fyron.test.safe")
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        try:
            raise ValueError(SECRET)
        except ValueError:
            event(logger, "fhir", "failed")
        assert SECRET not in stream.getvalue()
    finally:
        logger.removeHandler(handler)


def test_fhir_error_traceback_omits_remote_payload():
    response = requests.Response()
    response.status_code = 403
    response.url = "https://example.org/" + SECRET
    response._content = SECRET.encode()
    session = Mock()
    session.get.side_effect = requests.HTTPError(SECRET, response=response)
    with pytest.raises(FHIRRequestError) as caught:
        _request_json(session, response.url, {"patient": SECRET}, 1, None)
    rendered = "".join(traceback.format_exception(type(caught.value), caught.value, caught.tb))
    assert SECRET not in rendered
    assert "permission" in str(caught.value)


def test_network_boundary_preserves_type():
    @safe_network_errors
    def fail():
        raise requests.Timeout(SECRET)
    with pytest.raises(requests.Timeout) as caught:
        fail()
    assert SECRET not in str(caught.value)
    assert caught.value.__suppress_context__


def test_dicom_batch_separates_tasks_and_results(caplog):
    @batch_report("dicom")
    def run():
        completed_task([
            SimpleNamespace(error=None, skipped=False),
            SimpleNamespace(error=None, skipped=True),
            SimpleNamespace(error="safe error", skipped=False),
        ])
        return pd.DataFrame()
    with caplog.at_level(logging.INFO):
        run()
    event_data = caplog.records[-1].fyron_event
    assert event_data["completed"] == 1
    assert [event_data[k] for k in ("succeeded", "skipped", "failed")] == [1, 1, 1]


def test_interrupt_retains_counts(caplog):
    @batch_report("dicom")
    def run():
        completed_task([SimpleNamespace(error=None, skipped=False)])
        raise KeyboardInterrupt()
    with caplog.at_level(logging.INFO), pytest.raises(KeyboardInterrupt):
        run()
    assert caplog.records[-1].fyron_event["stage"] == "incomplete"
    assert caplog.records[-1].fyron_event["completed"] == 1


def test_document_failure_keeps_url_only_in_result_column(tmp_path):
    session = requests.Session()
    session.get = Mock(side_effect=requests.Timeout(SECRET))
    downloader = DocumentDownloader(auth=session, output_dir=tmp_path)
    result = downloader.download_url("https://example.org/" + SECRET)
    assert SECRET in result.url
    assert SECRET not in result.error


def test_s3_provider_exception_is_safe():
    from botocore.exceptions import ClientError
    from fyron.core.s3 import S3Storage

    storage = S3Storage.__new__(S3Storage)
    storage.bucket, storage.prefix = SECRET, ""
    storage.client = Mock()
    storage.client.get_object.side_effect = ClientError(
        {"Error": {"Code": SECRET, "Message": SECRET}, "ResponseMetadata": {"HTTPStatusCode": 403}}, SECRET
    )
    with pytest.raises(ClientError) as caught:
        storage.read_bytes(SECRET)
    assert SECRET not in str(caught.value)
    assert caught.value.__suppress_context__


def test_sql_failure_omits_query_and_exception(caplog):
    from fyron.fhir.sql import FHIRSQLClient, SQLQueryError

    client = FHIRSQLClient.__new__(FHIRSQLClient)
    client.log_queries = True
    client._conn = Mock()
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(pd, "read_sql_query", Mock(side_effect=RuntimeError(SECRET)))
        with caplog.at_level(logging.DEBUG), pytest.raises(SQLQueryError) as caught:
            client.query_to_dataframe("SELECT '" + SECRET + "'")
    assert SECRET not in caplog.text
    assert SECRET not in str(caught.value)
    assert caught.value.__suppress_context__


def test_local_http_errors_are_safe(tmp_path):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(403)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SECRET.encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{SECRET}"
        with DocumentDownloader(output_dir=tmp_path) as downloader:
            result = downloader.download_url(url)
            assert "permission" in result.error
            assert SECRET not in result.error
        with requests.Session() as session, pytest.raises(FHIRRequestError) as caught:
            _request_json(session, url, {}, 2, None)
        assert SECRET not in str(caught.value)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("workers", [1, 2])
def test_dicom_html_response_sequential_and_spawned(tmp_path, workers):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(SECRET)))
            self.end_headers()
            self.wfile.write(SECRET.encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        with DICOMDownloader(
            dicom_web_url=f"http://127.0.0.1:{server.server_port}",
            basic_auth=("synthetic", SECRET), output_format="dicom", num_processes=workers,
        ) as client:
            result = client.download_from_dataframe(
                pd.DataFrame({"study_instance_uid": ["1.2.3", "1.2.4"], "series_instance_uid": ["1.3.1", "1.3.2"]}),
                tmp_path,
            )
        assert len(result) == 2
        assert result.error.str.contains("unexpected_response").all()
        assert not result.error.str.contains(SECRET).any()
        assert not result.skipped.any()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_llm_batch_returns_safe_error_marker(caplog):
    from fyron.llm.agent import LLMAgent
    client = LLMAgent.__new__(LLMAgent)
    client._request = Mock(side_effect=RuntimeError(SECRET))
    with caplog.at_level(logging.INFO):
        result = client.run_on_dataframe(pd.DataFrame({"text": [SECRET]}), text_col="text", prompt=SECRET)
    assert SECRET in result.text.iloc[0]
    assert SECRET not in caplog.text
    assert any(str(value).startswith("ERROR:") and SECRET not in str(value) for value in result.iloc[0])
    assert caplog.records[-1].fyron_event["failed"] == 1
