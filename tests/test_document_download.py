"""Document retrieval contracts using synthetic responses and loopback OAuth."""

import io
import json
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from fyron import Auth, DocumentDownloader
from fyron.cli import main
from fyron.documents import _cli
from test_device_auth import provider


PDF = b"%PDF-1.4\n% Synthetic document\n%%EOF\n"
URL = "https://documents.example.test/reports/demo/pdf"


class DocumentAdapter(requests.adapters.BaseAdapter):
    def __init__(self, status=200, content_type="application/pdf", body=PDF, headers=None, chunks=None):
        self.status, self.body, self.content_type = status, body, content_type
        self.headers, self.chunks = headers or {}, chunks
        self.calls = []
        self.closed = False

    def send(self, request, **kwargs):
        self.calls.append((request, kwargs))
        response = requests.Response()
        response.status_code = self.status
        response.headers.update({"Content-Type": self.content_type, **self.headers})
        response.raw = io.BytesIO(self.body)
        response.url, response.request, response.connection = request.url, request, self
        if self.chunks is not None:
            response.iter_content = lambda **kwargs: iter(self.chunks())
        return response

    def close(self):
        self.closed = True


def client(tmp_path, adapter=None, **kwargs):
    adapter = adapter or DocumentAdapter()
    downloader = DocumentDownloader(auth=requests.Session(), output_dir=tmp_path, **kwargs)
    downloader.session.mount("https://", adapter)
    return downloader, adapter


def test_pdf_split_prefix_exact_output_and_restart(tmp_path):
    adapter = DocumentAdapter(chunks=lambda: [b"%", b"", b"PD", b"F", b"-1.4\n"])
    downloader, _ = client(tmp_path, adapter, require_pdf=True, allow_redirects=False)
    output = tmp_path / "named" / "chosen.pdf"
    result = downloader.download_url(URL, output_path=output)
    assert result.error is None and result.status_code == 200
    assert Path(result.path) == output and output.read_bytes() == b"%PDF-1.4\n"
    assert result.sha256 and adapter.calls[0][0].headers["Accept"] == "application/pdf"
    assert downloader.download_url(URL, output_path=output).skipped
    assert len(adapter.calls) == 1
    assert not list(tmp_path.rglob(".fyron-stage-*"))


@pytest.mark.parametrize("status,content_type,body", [
    (200, "text/html", b"<html>login</html>"), (200, "application/pdf", b"not PDF"),
    (200, "application/pdf", b"%PDF"), (200, "application/pdf", b""),
    (206, "application/pdf", PDF), (204, "application/pdf", b""),
    (302, "application/pdf", PDF), (403, "text/html", b"private remote message"),
])
def test_invalid_pdf_never_published(tmp_path, status, content_type, body):
    downloader, _ = client(tmp_path, DocumentAdapter(status, content_type, body),
                           require_pdf=True, allow_redirects=False)
    result = downloader.download_url(URL, output_path=tmp_path / "report.pdf")
    assert result.error and result.status_code == status
    assert "private" not in result.error
    assert not list(tmp_path.iterdir())


def test_pdf_content_type_parameters_and_general_documents(tmp_path):
    downloader, _ = client(tmp_path, DocumentAdapter(content_type="Application/PDF; charset=binary"), require_pdf=True)
    assert downloader.download_url(URL).error is None
    downloader, _ = client(tmp_path / "text", DocumentAdapter(content_type="text/plain", body=b"plain text"))
    result = downloader.download_url(URL)
    assert result.error is None and Path(result.path).read_text() == "plain text"


def test_no_completion_record_preserves_unverified_files(tmp_path):
    downloader, adapter = client(tmp_path, require_pdf=True, write_completion_record=False)
    output = tmp_path / "report.pdf"
    result = downloader.download_url(URL, output_path=output)
    assert result.error is None and result.sha256
    assert list(tmp_path.iterdir()) == [output]
    adapter.body = b"%PDF-replacement"
    repeated = downloader.download_url(URL, output_path=output)
    assert repeated.error and not repeated.skipped
    assert output.read_bytes() == PDF
    downloader.skip_existing = False
    assert downloader.download_url(URL, output_path=output).error is None
    assert output.read_bytes() == adapter.body
    assert list(tmp_path.iterdir()) == [output]


def test_no_completion_record_overwrite_removes_old_marker(tmp_path):
    output = tmp_path / "report.pdf"
    original, _ = client(tmp_path, require_pdf=True)
    assert original.download_url(URL, output_path=output).error is None
    assert list(tmp_path.glob(".fyron-complete-*.json"))
    replacement, _ = client(tmp_path, require_pdf=True, skip_existing=False,
                            write_completion_record=False)
    assert replacement.download_url(URL, output_path=output).error is None
    assert list(tmp_path.iterdir()) == [output]


@pytest.mark.parametrize("write_record", [True, False])
@pytest.mark.parametrize("require_pdf", [True, False])
def test_flat_batch_paths_collisions_and_restart(tmp_path, monkeypatch, write_record, require_pdf):
    monkeypatch.chdir(tmp_path)
    downloader, _ = client(Path("downloads"), flat_output=True, require_pdf=require_pdf,
                           write_completion_record=write_record)
    urls = [URL + "?case=one", URL + "?case=two"]
    report = tmp_path / "results.csv"
    results = downloader.download_urls(urls, results_csv=report)
    assert results.error.isna().all()
    assert results.path.nunique() == 2
    assert set(pd.read_csv(report).path) == set(results.path)
    for row in results.itertuples():
        path = Path(row.path)
        assert path.is_absolute() and path.parent == tmp_path / "downloads"
        assert path.name == downloader.download_id(row.url) + ".pdf"
        assert path.read_bytes() == PDF
    assert not any(path.is_dir() for path in (tmp_path / "downloads").iterdir())
    repeated = downloader.download_urls(urls)
    if write_record:
        assert repeated.skipped.all() and repeated.error.isna().all()
    else:
        assert repeated.error.notna().all() and not repeated.skipped.any()
        assert not list((tmp_path / "downloads").glob("*.json"))


def test_flat_exact_output_and_report_collision(tmp_path):
    downloader, _ = client(tmp_path, flat_output=True, require_pdf=True)
    chosen = tmp_path / "custom.pdf"
    assert downloader.download_url(URL, output_path=chosen).path == str(chosen)
    report = tmp_path / (downloader.download_id(URL) + ".pdf")
    with pytest.raises(ValueError, match="overwrite a document"):
        downloader.download_urls([URL], results_csv=report)
    assert report.read_bytes() == PDF


@pytest.mark.parametrize("failure", ["interrupt", "length", "bad_pdf", "cancel"])
def test_failed_replacement_preserves_original(tmp_path, failure):
    output = tmp_path / "original.pdf"
    output.write_bytes(b"original")
    def interrupted():
        yield b"%PDF-"
        if failure == "cancel":
            raise KeyboardInterrupt
        raise requests.ConnectionError("private URL token and contents")
    adapter = (DocumentAdapter(chunks=interrupted) if failure in {"interrupt", "cancel"} else
               DocumentAdapter(headers={"Content-Length": "1000"}) if failure == "length" else
               DocumentAdapter(body=b"no PDF"))
    downloader, _ = client(tmp_path, adapter, require_pdf=True, skip_existing=False)
    if failure == "cancel":
        with pytest.raises(KeyboardInterrupt):
            downloader.download_url(URL, output_path=output)
    else:
        assert downloader.download_url(URL, output_path=output).error
    assert output.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [output]


def test_completion_records_bind_source_destination_and_validation(tmp_path):
    downloader, adapter = client(tmp_path)
    output = tmp_path / "one.pdf"
    assert downloader.download_url(URL, output_path=output).error is None
    assert downloader.download_url(URL, output_path=output).skipped
    assert not downloader.download_url(URL, output_path=tmp_path / "two.pdf").skipped
    other = downloader.download_url(URL + "-other", output_path=output)
    assert other.error and not other.skipped
    strict, _ = client(tmp_path, require_pdf=True)
    assert strict.download_url(URL, output_path=output).error  # General marker cannot prove PDF policy.
    strict.skip_existing = False
    assert strict.download_url(URL, output_path=output).error is None
    strict.skip_existing = True
    assert strict.download_url(URL, output_path=output).skipped
    output.write_bytes(b"corrupt")
    assert strict.download_url(URL, output_path=output).error
    assert output.read_bytes() == b"corrupt"


@pytest.mark.parametrize("target", ["https://other.example.test/private", "http://documents.example.test/plain"])
def test_redirect_never_sends_token_to_other_origin(tmp_path, target):
    downloader, adapter = client(tmp_path, DocumentAdapter(status=307, headers={"Location": target}))
    downloader.session.headers["Authorization"] = "Bearer synthetic-secret"
    result = downloader.download_url(URL)
    assert result.error and result.status_code == 307
    assert len(adapter.calls) == 1


def test_same_origin_redirect_policy(tmp_path):
    class RedirectOnce(DocumentAdapter):
        def send(self, request, **kwargs):
            self.status = 302 if not self.calls else 200
            self.headers = {"Location": "/final.pdf"} if not self.calls else {}
            return super().send(request, **kwargs)
    downloader, adapter = client(tmp_path / "blocked", RedirectOnce(), allow_redirects=False)
    result = downloader.download_url(URL)
    assert result.status_code == 302 and result.error and len(adapter.calls) == 1
    downloader, adapter = client(tmp_path / "allowed", RedirectOnce(), require_pdf=True)
    assert downloader.download_url(URL).error is None and len(adapter.calls) == 2


@pytest.mark.parametrize("url", [None, float("nan"), "", "relative", "file:///tmp/document", "https://u:p@example.test/a"])
def test_invalid_urls_rejected_before_request(tmp_path, url):
    downloader, adapter = client(tmp_path)
    with pytest.raises(ValueError):
        downloader.download_from_df(pd.DataFrame({"document_url": [URL, url]}))
    assert not adapter.calls


def test_empty_batch_and_duplicate_urls(tmp_path):
    downloader, adapter = client(tmp_path, require_pdf=True)
    empty = downloader.download_urls([])
    assert "error" in empty.columns and empty.empty
    result = downloader.download_urls([URL] * 6)
    assert result.error.isna().all() and result.skipped.sum() == 5


def test_caller_owned_session_remains_open(tmp_path):
    downloader, adapter = client(tmp_path)
    with downloader:
        assert downloader.download_url(URL).error is None
    assert not adapter.closed
    downloader.session.close()
    assert adapter.closed


def fake_cli(monkeypatch, adapter):
    def build(**kwargs):
        downloader = DocumentDownloader(**kwargs)
        downloader.session.mount("https://", adapter)
        return downloader
    monkeypatch.setattr(_cli, "DocumentDownloader", build)


def test_cli_single_file_restart_and_overwrite(tmp_path, monkeypatch, capsys):
    adapter = DocumentAdapter()
    fake_cli(monkeypatch, adapter)
    # Explicit anonymous mode cannot trigger unrelated environment auth.
    monkeypatch.setenv("FHIR_AUTH_URL", "https://unused.example.test")
    output, report = tmp_path / "report.pdf", tmp_path / "results.csv"
    args = ["--no-color", "document-download", "--url", URL, "--output", str(output), "--pdf", "--results-csv", str(report)]
    assert main(args) == 0
    assert output.read_bytes() == PDF and adapter.closed
    assert adapter.calls[0][1]["timeout"] == 90
    assert main(args) == 0 and len(adapter.calls) == 1
    assert pd.read_csv(report).skipped.tolist() == [True]
    adapter.body = b"%PDF-new"
    assert main(args + ["--overwrite"]) == 0 and output.read_bytes() == b"%PDF-new"
    output_text = capsys.readouterr().out
    assert "1 skipped" in output_text and URL not in output_text


def test_cli_csv_without_completion_records(tmp_path, monkeypatch):
    fake_cli(monkeypatch, DocumentAdapter())
    source = tmp_path / "documents.csv"
    pd.DataFrame({"document_url": [URL, URL + "-second"]}).to_csv(source, index=False)
    output = tmp_path / "downloads"
    report = tmp_path / "results.csv"
    args = ["document-download", "--csv", str(source), "--output-dir", str(output),
            "--pdf", "--flat-output", "--no-completion-record", "--results-csv", str(report)]
    assert main(args) == 0
    assert len(list(output.rglob("*.pdf"))) == 2
    assert not list(output.rglob("*.json"))
    assert len(pd.read_csv(report)) == 2
    assert all(Path(path).parent == output for path in pd.read_csv(report).path)
    assert not any(path.is_dir() for path in output.iterdir())
    assert main(args) == 1  # Existing unverified files remain protected.
    assert main(args + ["--overwrite"]) == 0
    assert not list(output.rglob("*.json"))


def test_cli_csv_partial_failure_json_and_quiet(tmp_path, monkeypatch, capsys):
    class Mixed(DocumentAdapter):
        def send(self, request, **kwargs):
            self.status = 403 if request.url.endswith("bad") else 200
            return super().send(request, **kwargs)
    fake_cli(monkeypatch, Mixed())
    source, report = tmp_path / "input.csv", tmp_path / "results.csv"
    pd.DataFrame({"link": [URL, URL + "/bad"]}).to_csv(source, index=False)
    args = ["document-download", "--csv", str(source), "--url-col", "link", "--pdf",
            "--output-dir", str(tmp_path / "output"), "--results-csv", str(report)]
    assert main(["--json-log", *args]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and URL not in captured.err
    events = [json.loads(line) for line in captured.err.splitlines()]
    assert events[-1]["failed"] == 1 and events[-1]["succeeded"] == 1
    assert len(pd.read_csv(report)) == 2
    assert main(["--quiet", *args]) == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("options", [
    ["--timeout", "nan"], ["--workers", "0"], ["--client-id", "demo"],
    ["--auth-type", "device_code", "--client-id", "demo"],
    ["--auth-type", "device_code", "--client-id", "demo", "--auth-url", "https://identity.example.test", "--token-endpoint", "https://identity.example.test/token"],
    ["--auth-type", "client_credentials", "--client-id", "demo", "--token-endpoint", "https://identity.example.test/token"],
])
def test_cli_invalid_arguments_do_not_authenticate(tmp_path, monkeypatch, options):
    auth = Mock(side_effect=AssertionError("Must not authenticate"))
    monkeypatch.setattr(_cli, "Auth", auth)
    assert main(["document-download", "--url", URL, "--output", str(tmp_path / "out"), *options]) == 2
    auth.assert_not_called()


def test_cli_invalid_csv_precedes_authentication(tmp_path, monkeypatch):
    source = tmp_path / "input.csv"
    source.write_text("document_url\n\"\"\n")
    auth = Mock(side_effect=AssertionError("Must not authenticate"))
    monkeypatch.setattr(_cli, "Auth", auth)
    assert main(["document-download", "--csv", str(source), "--auth-type", "device_code",
                 "--client-id", "demo", "--auth-url", "https://identity.example.test"]) == 2
    auth.assert_not_called()


def test_document_device_refresh_and_parallel_downloads(provider, tmp_path):
    provider["download_delay"] = 0.03
    with Auth(auth_type="device_code", auth_url=provider["url"], client_id="demo") as auth:
        with DocumentDownloader(auth=auth, output_dir=tmp_path, require_pdf=True, allow_redirects=False) as downloader:
            assert downloader.download_url(provider["url"] + "/documents/first").error is None
            provider["revoked"] = True
            results = downloader.download_urls([provider["url"] + f"/documents/{i}" for i in range(8)])
            assert results.error.isna().all()
            assert all(Path(path).read_bytes().startswith(b"%PDF-") for path in results.path)
    assert provider["logins"] == 1 and provider["refreshes"] == 1
    assert provider["peak_downloads"] > 1


def test_cli_device_approval_with_explicit_endpoints(provider, tmp_path, capsys):
    output = tmp_path / "document.pdf"
    assert main(["--quiet", "--no-color", "document-download", "--url", provider["url"] + "/documents/one",
                 "--output", str(output), "--pdf", "--auth-type", "device_code", "--auth-url", provider["url"],
                 "--client-id", "demo", "--scope", "openid user/DocumentReference.rs",
                 "--device-authorization-endpoint", provider["url"] + "/device", "--token-endpoint", provider["url"] + "/token"]) == 0
    assert output.read_bytes().startswith(b"%PDF-")
    captured = capsys.readouterr()
    assert "Sign in" in captured.out and "Documents:" not in captured.out
    assert "ABCD" not in captured.err and "private-device" not in captured.err


def test_cli_service_account_configuration_and_close(tmp_path, monkeypatch):
    fake_cli(monkeypatch, DocumentAdapter())
    session = requests.Session()
    auth = Mock()
    auth.__enter__ = Mock(return_value=session)
    auth.__exit__ = Mock(side_effect=lambda *args: session.close())
    factory = Mock(return_value=auth)
    monkeypatch.setattr(_cli.Auth, "client_credentials", factory)
    monkeypatch.setenv("DOCUMENT_TEST_SECRET", "synthetic-secret")
    assert main(["document-download", "--url", URL, "--output", str(tmp_path / "doc.pdf"),
                 "--auth-type", "client_credentials", "--client-id", "service-demo",
                 "--token-endpoint", "https://identity.example.test/token", "--client-secret-env", "DOCUMENT_TEST_SECRET"]) == 0
    assert factory.call_args.kwargs["client_secret"] == "synthetic-secret"
    auth.__exit__.assert_called_once()


def test_cli_cancellation_and_sensitive_error_are_controlled(tmp_path, monkeypatch, capsys):
    def fail(**kwargs):
        raise RuntimeError("private-url secret-token remote-body")
    monkeypatch.setattr(_cli, "DocumentDownloader", fail)
    args = ["--json-log", "document-download", "--url", URL, "--output", str(tmp_path / "doc.pdf")]
    assert main(args) == 1
    assert "secret-token" not in capsys.readouterr().err
    def cancel(**kwargs):
        raise KeyboardInterrupt
    monkeypatch.setattr(_cli, "DocumentDownloader", cancel)
    assert main(args) == 130
