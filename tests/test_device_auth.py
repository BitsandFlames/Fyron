import io
import json
import multiprocessing as mp
import pickle
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs

import pandas as pd
import pytest
import requests
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage

from fyron import Auth, DICOMDownloader, FHIRRestClient
from fyron.fhir._device_auth import (
    DeviceAuthError,
    _DeviceAuth,
    _url,
)
from fyron.fhir._workers import managed_pool, worker_auth


@pytest.fixture
def provider():
    state = {
        "logins": 0,
        "refreshes": 0,
        "generation": 0,
        "revoked": False,
        "redirect": False,
        "polls": [],
        "bodies": [],
        "refresh_error": None,
        "requests": [],
        "reject_password_refresh": False,
        "active_downloads": 0,
        "peak_downloads": 0,
        "download_delay": 0,
    }
    activity_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, payload, status=200, headers=None):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            state["requests"].append((self.path, self.headers.get("Authorization")))
            if self.path == "/password-login":
                if self.headers.get("Authorization") != "Basic dXNlcjpwYXNz":
                    return self.reply({}, 401)
                state["logins"] += 1
                state["generation"] += 1
                state["revoked"] = False
                return self.reply({"access_token": f"access-{state['generation']}"})
            if self.path == "/password-refresh":
                state["refreshes"] += 1
                if (
                    state["reject_password_refresh"]
                    or self.headers.get("Authorization")
                    != f"Bearer access-{state['generation']}"
                ):
                    return self.reply({}, 401)
                state["generation"] += 1
                state["revoked"] = False
                return self.reply({"access_token": f"access-{state['generation']}"})
            if self.path.endswith("/.well-known/openid-configuration"):
                return self.reply(
                    {
                        "issuer": state["url"],
                        "device_authorization_endpoint": state["url"] + "/device",
                        "token_endpoint": state["url"] + "/token",
                        "authorization_endpoint": state["url"] + "/login",
                    }
                )
            if (
                self.headers.get("Authorization")
                != f"Bearer access-{state['generation']}"
                or state["revoked"]
            ):
                if state["redirect"]:
                    return self.reply(
                        {}, 302, {"Location": state["url"] + "/login?client_id=cli"}
                    )
                return self.reply({}, 401)
            if self.path.startswith("/documents/"):
                with activity_lock:
                    state["active_downloads"] += 1
                    state["peak_downloads"] = max(state["peak_downloads"], state["active_downloads"])
                time.sleep(state["download_delay"])
                body = b"%PDF-1.4\n% Synthetic fixture\n%%EOF\n"
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                with activity_lock:
                    state["active_downloads"] -= 1
                return
            if self.path.startswith("/studies/"):
                with activity_lock:
                    state["active_downloads"] += 1
                    state["peak_downloads"] = max(
                        state["peak_downloads"], state["active_downloads"]
                    )
                time.sleep(state["download_delay"])
                with activity_lock:
                    state["active_downloads"] -= 1
                uid = self.path.split("/")[2]
                meta = FileMetaDataset()
                meta.TransferSyntaxUID = ExplicitVRLittleEndian
                meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
                meta.MediaStorageSOPInstanceUID = uid + ".1.1"
                dataset = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
                dataset.StudyInstanceUID = uid
                dataset.SeriesInstanceUID = uid + ".1"
                dataset.SOPInstanceUID = uid + ".1.1"
                dataset.SOPClassUID = SecondaryCaptureImageStorage
                stream = io.BytesIO()
                dataset.is_little_endian = True
                dataset.is_implicit_VR = False
                dataset.save_as(stream, write_like_original=False)
                body = (
                    b"--testboundary\r\nContent-Type: application/dicom\r\n\r\n"
                    + stream.getvalue()
                    + b"\r\n--testboundary--\r\n"
                )
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    'multipart/related; type="application/dicom"; boundary=testboundary',
                )
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.reply({"resourceType": "Bundle", "type": "searchset", "entry": []})

        def do_POST(self):
            data = parse_qs(
                self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            )
            state["bodies"].append(data)
            if self.path == "/device":
                state["logins"] += 1
                return self.reply(
                    {
                        "device_code": "private-device",
                        "user_code": "ABCD",
                        "verification_uri": state["url"] + "/verify",
                        "expires_in": 60,
                        "interval": 0.001,
                    }
                )
            if data.get("grant_type") == ["refresh_token"]:
                state["refreshes"] += 1
                if state["refresh_error"]:
                    return self.reply({"error": state["refresh_error"]}, 400)
                if data.get("refresh_token") != [f"refresh-{state['generation']}"]:
                    return self.reply({"error": "invalid_grant"}, 400)
            elif state["polls"]:
                return self.reply({"error": state["polls"].pop(0)}, 400)
            state["generation"] += 1
            state["revoked"] = False
            self.reply(
                {
                    "access_token": f"access-{state['generation']}",
                    "refresh_token": f"refresh-{state['generation']}",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield state
    server.shutdown()
    server.server_close()
    thread.join()


def make_auth(provider, **kwargs):
    return Auth(
        auth_type="device_code",
        auth_url=provider["url"],
        client_id="cli",
        device_code_callback=kwargs.pop("device_code_callback", None),
        **kwargs,
    )


@pytest.mark.parametrize("redirect", [False, True])
def test_socket_flow_refresh_and_cache(provider, tmp_path, redirect):
    instructions = []
    path = tmp_path / "tokens.json"
    with make_auth(
        provider, token_cache=str(path), device_code_callback=instructions.append
    ) as auth:
        assert instructions[0]["user_code"] == "ABCD"
        assert "device_code" not in instructions[0]
        assert auth.session.get(provider["url"] + "/Patient").status_code == 200
        provider.update(revoked=True, redirect=redirect)
        result = auth.session.get(provider["url"] + "/Patient")
        assert result.status_code == 200
        assert len(result.history) == 1
    with make_auth(
        provider, token_cache=str(path), allow_reauthentication=False
    ) as cached:
        assert cached.session.get(provider["url"] + "/Patient").status_code == 200
    assert provider["logins"] == provider["refreshes"] == 1
    assert path.stat().st_mode & 0o777 == 0o600


def test_unattended_and_invalid_grant(provider):
    with pytest.raises(DeviceAuthError, match="disabled"):
        make_auth(provider, allow_reauthentication=False)
    with make_auth(provider) as auth:
        handler = auth.session.auth
        handler.allow_reauthentication = False
        provider["refresh_error"] = "invalid_grant"
        with pytest.raises(DeviceAuthError, match="disabled"):
            handler.get_token(rejected=handler.state["access_token"])
        assert provider["logins"] == 1


def test_explicit_endpoints_and_env_precedence(provider, monkeypatch):
    with make_auth(
        provider,
        device_authorization_endpoint=provider["url"] + "/device",
        token_endpoint=provider["url"] + "/token",
    ) as auth:
        monkeypatch.setenv("DICOM_USER", "wrong")
        monkeypatch.setenv("DICOM_PASSWORD", "wrong")
        downloader = DICOMDownloader(auth=auth, dicom_web_url=provider["url"])
        assert downloader.session is auth.session
        assert downloader.dicom_user is None
        with pytest.raises(ValueError, match="not both"):
            DICOMDownloader(
                auth=auth, basic_auth=("u", "p"), dicom_web_url=provider["url"]
            )
    with pytest.raises(ValueError, match="both"):
        make_auth(provider, token_endpoint=provider["url"] + "/token")


def test_pickling_and_copied_session_auth(provider):
    with make_auth(provider) as auth:
        clone = pickle.loads(pickle.dumps(auth.session.auth))
        with requests.Session() as session:
            session.auth = clone
            provider["revoked"] = True
            assert session.get(provider["url"] + "/resource").status_code == 200
        clone.close()
    assert provider["refreshes"] == 1


def worker_get(url):
    auth = worker_auth()
    with requests.Session() as session:
        session.auth = auth
        return session.get(url, timeout=10).status_code


def test_spawned_workers_share_rotating_refresh(provider):
    with make_auth(provider) as auth:
        provider["revoked"] = True
        with (
            managed_pool(auth.session.auth, 3, 10) as (pool, events),
        ):
            assert (
                pool.map(worker_get, [provider["url"] + "/resource"] * 6)
                == [200] * 6
            )
    assert provider["logins"] == provider["refreshes"] == 1
    assert not any(t.name.startswith("fyron-token-") for t in threading.enumerate())


def test_fhir_parallel_device_integration(provider, monkeypatch):
    import fyron.fhir.rest as module

    monkeypatch.setattr(module.mp, "Pool", mp.get_context("spawn").Pool)
    with make_auth(provider) as auth:
        provider["revoked"] = True
        client = FHIRRestClient(provider["url"], auth=auth, num_processes=2)
        bundles = list(
            client.fetch_bundles_parallel(
                "Patient", [{"x": 1}, {"x": 2}], show_progress=False
            )
        )
        assert len(bundles) == 2
    assert provider["refreshes"] == 1


def test_dicom_parallel_download(provider, monkeypatch, tmp_path):
    import fyron.dicom.client as module

    monkeypatch.setattr(module.mp, "Pool", mp.get_context("spawn").Pool)
    monkeypatch.setenv("DICOM_USER", "must-not-override")
    with make_auth(provider) as auth:
        provider.update(revoked=True, redirect=True)
        downloader = DICOMDownloader(
            dicom_web_url=provider["url"],
            auth=auth,
            num_processes=2,
            output_format="dicom",
        )
        results = downloader.download_from_dataframe(
            pd.DataFrame({"study": ["1.2.3", "1.2.4"]}),
            output_dir=tmp_path,
            study_uid_col="study",
            download_full_study=True,
        )
        assert len(results) == 2
        assert results["error"].isna().all()
        assert len(list(tmp_path.rglob("*.dcm"))) == 2
    assert provider["refreshes"] == provider["logins"] == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "http://localhost",
        "https://u:p@example.com",
        "file:///tmp/test",
    ],
)
def test_reject_unsafe_endpoint(url):
    with pytest.raises(ValueError):
        _url(url)


def test_cache_identity_permissions_and_atomicity(provider, tmp_path):
    path = tmp_path / "token.json"
    with make_auth(provider, token_cache=str(path)):
        pass
    record = json.loads(path.read_text())
    record["identity"][1] = "another-client"
    path.write_text(json.dumps(record))
    with pytest.raises(DeviceAuthError, match="disabled"):
        make_auth(provider, token_cache=str(path), allow_reauthentication=False)
    path.chmod(0o644)
    with pytest.raises(DeviceAuthError, match="Unsafe"):
        make_auth(provider, token_cache=str(path))
    assert not list(tmp_path.glob(".fyron-token-*"))


def test_concurrent_cached_refresh(provider, tmp_path):
    path = str(tmp_path / "token.json")
    first = make_auth(provider, token_cache=path)
    second = make_auth(provider, token_cache=path)
    old = first.session.auth.state["access_token"]
    with ThreadPoolExecutor(2) as pool:
        tokens = list(
            pool.map(lambda a: a.session.auth.get_token(rejected=old), [first, second])
        )
    assert tokens[0] == tokens[1]
    assert provider["refreshes"] == 1
    first.close()
    second.close()


def test_proactive_refresh_and_no_refresh_storm(provider):
    with make_auth(provider) as auth:
        handler = auth.session.auth
        old = handler.state["access_token"]
        handler.state["issued_at"] -= 3000
        assert handler.get_token() != old
        handler.get_token(rejected=old)
        assert provider["refreshes"] == 1


@pytest.mark.parametrize("error", ["access_denied", "expired_token", "unexpected"])
def test_terminal_poll_errors(provider, error):
    provider["polls"] = [error]
    with pytest.raises(DeviceAuthError):
        make_auth(provider)


def test_pending_poll(provider):
    provider["polls"] = ["authorization_pending"] * 2
    with make_auth(provider):
        pass
    assert provider["logins"] == 1


def response_for(handler, body=None, status=401, location=None):
    request = requests.Request(
        "POST", "https://resource.example/api", data=body
    ).prepare()
    handler(request)
    response = requests.Response()
    response.status_code = status
    response.request = request
    response.url = request.url
    response.close = Mock()
    response.connection = Mock()
    retry_response = requests.Response()
    retry_response.status_code = 401
    response.connection.send.return_value = retry_response
    if location:
        response.headers["Location"] = location
    return response


def test_challenge_body_rewind_and_single_retry(provider):
    with make_auth(provider) as auth:
        handler = auth.session.auth
        body = io.BytesIO(b"payload")
        response = response_for(handler, body)
        body.read()
        result = handler._challenge(response)
        assert body.tell() == 0
        assert result.status_code == 401
        assert response.connection.send.call_count == 1
        assert handler._challenge not in result.request.hooks["response"]


@pytest.mark.parametrize("case", ["stripped", "generator", "ordinary_redirect"])
def test_no_unsafe_replay(provider, case):
    with make_auth(provider) as auth:
        handler = auth.session.auth
        response = response_for(
            handler, iter([b"data"]) if case == "generator" else None
        )
        if case == "stripped":
            del response.request.headers["Authorization"]
        if case == "ordinary_redirect":
            response.status_code = 302
            response.headers["Location"] = "https://elsewhere.example/login"
        assert handler._challenge(response) is response
        response.connection.send.assert_not_called()
        assert provider["refreshes"] == 0


def test_network_error_redacted_no_relogin(provider, monkeypatch):
    with make_auth(provider) as auth:
        handler = auth.session.auth
        monkeypatch.setattr(
            handler._session,
            "request",
            Mock(side_effect=requests.ConnectionError("secret-token")),
        )
        with pytest.raises(DeviceAuthError) as error:
            handler.get_token(rejected=handler.state["access_token"])
        assert "secret-token" not in str(error.value)
        assert provider["logins"] == 1


def test_poll_backoff_and_default_interval(provider, monkeypatch):
    import fyron.fhir._device_auth as module

    with make_auth(provider) as auth:
        handler = auth.session.auth
        clock = [0]
        waits = []

        def wait(seconds):
            waits.append(seconds)
            clock[0] += seconds
            return False

        handler._cancel = SimpleNamespace(wait=wait)
        monkeypatch.setattr(
            module, "time", SimpleNamespace(monotonic=lambda: clock[0], time=time.time)
        )
        monkeypatch.setattr(
            handler,
            "_request",
            Mock(
                side_effect=[
                    {
                        "device_code": "d",
                        "user_code": "u",
                        "verification_uri": "https://id.example/verify",
                        "expires_in": 200,
                    },
                    {"error": "authorization_pending"},
                    {"error": "slow_down"},
                    {"error": "_timeout"},
                    {"access_token": "opaque", "token_type": "bearer"},
                ]
            ),
        )
        handler._login()
        assert waits == [5, 5, 10, 20]
        assert handler.state["lifetime"] is None


def test_deadline_and_cancellation(provider, monkeypatch):
    with make_auth(provider) as auth:
        handler = auth.session.auth
        payload = {
            "device_code": "d",
            "user_code": "u",
            "verification_uri": "https://id.example/verify",
            "expires_in": 1,
        }
        monkeypatch.setattr(handler, "_request", Mock(return_value=payload))
        with pytest.raises(DeviceAuthError, match="expired"):
            handler._login()
        assert handler._request.call_count == 1
        payload["expires_in"] = 60
        handler._cancel.set()
        with pytest.raises(DeviceAuthError, match="cancelled"):
            handler._login()


@pytest.mark.parametrize("method", ["client_secret_basic", "client_secret_post"])
def test_confidential_client_wire_format(monkeypatch, method):
    from fyron.fhir import _device_auth as module

    session = Mock()
    responses = [
        {
            "issuer": "https://id.example",
            "device_authorization_endpoint": "https://id.example/device",
            "token_endpoint": "https://id.example/token",
            "token_endpoint_auth_methods_supported": [method],
        },
        {
            "device_code": "d",
            "user_code": "u",
            "verification_uri": "https://id.example/verify",
            "expires_in": 60,
            "interval": 0.001,
        },
        {"access_token": "a", "token_type": "Bearer"},
    ]

    def request(*args, **kwargs):
        response = Mock(status_code=200, is_redirect=False)
        response.json.return_value = responses.pop(0)
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        return context

    session.request.side_effect = request
    monkeypatch.setattr(module.requests, "Session", Mock(return_value=session))
    auth = _DeviceAuth("https://id.example", "cli", client_secret="secret")
    for call in session.request.call_args_list[1:]:
        assert call.kwargs["allow_redirects"] is False
        assert "json" not in call.kwargs
        if method == "client_secret_basic":
            assert call.kwargs["auth"] == ("cli", "secret")
            assert "client_secret" not in call.kwargs["data"]
        else:
            assert call.kwargs["data"]["client_secret"] == "secret"
    auth.close()


def test_discovery_mismatch_and_unsupported_method(monkeypatch):
    metadata = {"issuer": "https://other.example"}
    monkeypatch.setattr(_DeviceAuth, "_request", Mock(return_value=metadata))
    with pytest.raises(DeviceAuthError, match="issuer"):
        _DeviceAuth("https://id.example", "cli")
    metadata.update(
        issuer="https://id.example",
        token_endpoint="https://id.example/token",
        device_authorization_endpoint="https://id.example/device",
        token_endpoint_auth_methods_supported=["private_key_jwt"],
    )
    with pytest.raises(DeviceAuthError, match="Unsupported"):
        _DeviceAuth("https://id.example", "cli", client_secret="secret")


def test_cache_symlink_rejected(provider, tmp_path):
    target = tmp_path / "target"
    target.write_text("do not overwrite")
    path = tmp_path / "token.json"
    path.symlink_to(target)
    with pytest.raises(OSError):
        make_auth(provider, token_cache=str(path))
    assert target.read_text() == "do not overwrite"


def test_coordinator_cleanup_on_exception(provider):
    with (
        make_auth(provider) as auth,
        pytest.raises(RuntimeError),
        managed_pool(auth.session.auth, 1, 10),
    ):
        raise RuntimeError("stop")
    assert not any(t.name.startswith("fyron-token-") for t in threading.enumerate())


def test_cache_atomic_failure_keeps_previous_record(provider, tmp_path, monkeypatch):
    import fyron.fhir._device_auth as module

    path = tmp_path / "token.json"
    with make_auth(provider, token_cache=str(path)) as auth:
        previous = path.read_bytes()
        monkeypatch.setattr(
            module.os, "replace", Mock(side_effect=OSError("disk failure"))
        )
        with pytest.raises(OSError):
            auth.session.auth.get_token(
                rejected=auth.session.auth.state["access_token"]
            )
        assert path.read_bytes() == previous
        assert not list(tmp_path.glob(".fyron-token-*"))


def test_worker_reauthentication_callback_stays_in_parent(provider):
    import os

    calls = []
    with make_auth(
        provider, device_code_callback=lambda _: calls.append(os.getpid())
    ) as auth:
        provider["refresh_error"] = "invalid_grant"
        provider["revoked"] = True
        with managed_pool(auth.session.auth, 1, 10) as (pool, events):
            assert pool.map(worker_get, [provider["url"] + "/resource"]) == [200]
    assert calls == [os.getpid(), os.getpid()]


@pytest.mark.parametrize("status", [302, 503])
def test_endpoint_errors_do_not_reauthenticate(provider, monkeypatch, status):
    with make_auth(provider) as auth:
        handler = auth.session.auth
        response = requests.Response()
        response.status_code = status
        response.headers["Location"] = "https://foreign.example/token"
        response._content = b'{"error_description":"secret"}'
        response._content_consumed = True
        monkeypatch.setattr(handler._session, "request", Mock(return_value=response))
        with pytest.raises(DeviceAuthError) as error:
            handler.get_token(rejected=handler.state["access_token"])
        assert "secret" not in str(error.value)
        assert provider["logins"] == 1


def test_refresh_without_rotation_preserves_refresh_token(provider, monkeypatch):
    with make_auth(provider) as auth:
        handler = auth.session.auth
        previous = handler.state["refresh_token"]
        monkeypatch.setattr(
            handler,
            "_request",
            Mock(
                return_value={
                    "access_token": "new-opaque",
                    "token_type": "Bearer",
                    "expires_in": 100,
                }
            ),
        )
        assert handler.get_token(rejected=handler.state["access_token"]) == "new-opaque"
        assert handler.state["refresh_token"] == previous


@pytest.mark.parametrize("reject_refresh", [False, True])
def test_dicom_password_token_uses_bearer_over_http(
    provider, monkeypatch, tmp_path, reject_refresh
):
    monkeypatch.setenv("FHIR_USER", "user")
    monkeypatch.setenv("FHIR_PASSWORD", "pass")
    monkeypatch.setenv("DICOM_USER", "must-not-override")
    monkeypatch.setenv("DICOM_PASSWORD", "must-not-override")
    with Auth.token_env(
        auth_url=provider["url"] + "/password-login",
        refresh_url=provider["url"] + "/password-refresh",
        token_auth_method="basic",
    ) as auth:
        downloader = DICOMDownloader(
            auth=auth,
            dicom_web_url=provider["url"],
            output_format="dicom",
            num_processes=1,
        )
        provider.update(revoked=True, reject_password_refresh=reject_refresh)
        results = downloader.download_study("1.2.3", tmp_path)
        assert len(results) == 1
        assert results[0].error is None
        assert len(list(tmp_path.rglob("*.dcm"))) == 1
    study_headers = [
        header for path, header in provider["requests"] if path.startswith("/studies/")
    ]
    assert study_headers == ["Bearer access-1", "Bearer access-2"]
    refresh_headers = [
        header for path, header in provider["requests"] if path == "/password-refresh"
    ]
    assert refresh_headers == ["Bearer access-1"]
    assert provider["logins"] == (2 if reject_refresh else 1)


def test_dicom_static_bearer_session_overrides_environment(
    provider, monkeypatch, tmp_path
):
    monkeypatch.setenv("DICOM_USER", "must-not-override")
    monkeypatch.setenv("DICOM_PASSWORD", "must-not-override")
    with requests.Session() as session:
        session.headers["Authorization"] = "Bearer access-0"
        downloader = DICOMDownloader(
            auth=session, dicom_web_url=provider["url"], output_format="dicom"
        )
        assert downloader.download_study("1.2.3", tmp_path)[0].error is None
    assert provider["requests"] == [("/studies/1.2.3", "Bearer access-0")]
