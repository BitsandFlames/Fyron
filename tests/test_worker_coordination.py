"""Synthetic worker lifecycle and lease regressions; no external services."""

import json
import multiprocessing as mp
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import pytest

from fyron import Auth, DICOMDownloader, FHIRRestClient
from fyron.fhir._client_credentials import _ClientCredentialsAuth
from fyron.fhir._device_auth import DeviceAuthError
from fyron.fhir._workers import (
    PipeAuth,
    TokenBroker,
    managed_pool,
    monitored_results,
    stage,
    worker_auth,
)
from fyron.fhir.rest import FHIRRequestError


def _cached_job(count):
    auth = worker_auth()
    first = auth.get_token()
    for _ in range(count):
        assert auth.get_token() == first
    return auth.generation


def _sleep_job(seconds):
    stage("http")
    time.sleep(seconds)
    return seconds


def _die(_):
    os._exit(17)


def _fail(_):
    raise ValueError("synthetic-patient-secret")


def _auth():
    return Auth.client_credentials(
        client_id="synthetic",
        client_secret="private-synthetic",
        token_endpoint="https://identity.example.org/token",
    )


@pytest.mark.parametrize("processes", [1, 2, 10])
def test_spawned_cached_leases(processes):
    payload = {"access_token": "synthetic", "token_type": "Bearer", "expires_in": 3600}
    with (
        patch.object(
            _ClientCredentialsAuth, "_request", return_value=payload
        ) as endpoint,
        _auth() as auth,
    ):
        with patch.object(TokenBroker, "lease", autospec=True, wraps=None) as lease:
            # Count IPC requests while retaining real lease behavior.
            lease.side_effect = lambda broker, rejected, deadline=None: (
                "synthetic",
                1,
                time.monotonic() + 100,
            )
            with managed_pool(auth.session.auth, processes, 3) as (pool, events):
                result = list(
                    monitored_results(pool, events, _cached_job, [100] * 20, 10)
                )
            assert result == [1] * 20
            assert lease.call_count <= processes
        assert endpoint.call_count == 1
    assert not any(t.name.startswith("fyron-token-") for t in threading.enumerate())


def test_generation_when_provider_reissues_same_token():
    payload = {"access_token": "same", "token_type": "Bearer", "expires_in": 3600}
    with (
        patch.object(
            _ClientCredentialsAuth, "_request", return_value=payload
        ) as endpoint,
        _auth() as auth,
    ):
        broker = TokenBroker(auth.session.auth)
        _, generation, _ = broker.lease(None)
        _, renewed, _ = broker.lease(generation)
        assert renewed > generation
        assert broker.lease(generation)[1] == renewed
        assert endpoint.call_count == 2
        auth.session.auth._renew_at = 0
        assert broker.lease(None)[1] > renewed
        assert endpoint.call_count == 3


def test_opaque_lease_does_not_reissue():
    with (
        patch.object(
            _ClientCredentialsAuth,
            "_request",
            return_value={"access_token": "opaque", "token_type": "Bearer"},
        ) as endpoint,
        _auth() as auth,
    ):
        broker = TokenBroker(auth.session.auth)
        assert 0 < broker.lease(None)[2] - time.monotonic() <= 30
        broker.lease(None)
        assert endpoint.call_count == 1


def test_pipe_timeout_and_disconnect():
    a, b = mp.Pipe()
    try:
        handler = PipeAuth(a, 0.03, None)
        with pytest.raises(DeviceAuthError, match="deadline"):
            handler.get_token()
    finally:
        a.close()
        b.close()
    a, b = mp.Pipe()
    b.close()
    try:
        with pytest.raises(DeviceAuthError, match="disconnected"):
            PipeAuth(a, 0.03, None).get_token()
    finally:
        a.close()


def test_job_deadline_and_cleanup():
    before = {p.pid for p in mp.active_children()}
    with (
        pytest.raises(FHIRRequestError, match="deadline in http"),
        managed_pool(None, 1, 1) as (pool, events),
    ):
        list(monitored_results(pool, events, _sleep_job, [3], 0.1))
    assert {p.pid for p in mp.active_children()} == before


def test_queue_time_is_not_execution_time():
    with managed_pool(None, 1, 1) as (pool, events):
        assert (
            list(monitored_results(pool, events, _sleep_job, [0.1] * 4, 0.3))
            == [0.1] * 4
        )


@pytest.mark.parametrize(
    "function, message", [(_die, "worker exited"), (_fail, "query failed")]
)
def test_failure_is_redacted(function, message):
    with (
        pytest.raises(FHIRRequestError, match=message) as error,
        managed_pool(None, 1, 1) as (pool, events),
    ):
        list(monitored_results(pool, events, function, [None], 5))
    assert "synthetic-patient-secret" not in str(error.value)


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan"), True])
def test_invalid_timeouts(value):
    with pytest.raises(ValueError):
        FHIRRestClient(base_url="https://example.org", worker_auth_timeout=value)
    with pytest.raises(ValueError):
        DICOMDownloader(dicom_web_url="https://example.org", worker_auth_timeout=value)
    with pytest.raises(ValueError):
        FHIRRestClient(base_url="https://example.org", parallel_job_timeout=value)


@pytest.fixture
def slow_service():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if "/slow/" in self.path or "cursor=2" in self.path:
                time.sleep(0.5)
            payload = {"resourceType": "Bundle", "entry": []}
            if "/pages/" in self.path and "cursor" not in self.path:
                payload["link"] = [{"relation": "next", "url": self.path + "?cursor=2"}]
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("path", ["slow", "pages"])
def test_dataframe_stalled_http_or_pagination_fails(slow_service, path):
    import pandas as pd

    payload = {"access_token": "synthetic", "token_type": "Bearer", "expires_in": 3600}
    with (
        patch.object(_ClientCredentialsAuth, "_request", return_value=payload),
        _auth() as auth,
    ):
        client = FHIRRestClient(
            base_url=slow_service + "/" + path,
            auth=auth,
            num_processes=2,
            parallel_job_timeout=0.1,
        )
        with pytest.raises(FHIRRequestError, match="deadline"):
            client.query_df_from(
                pd.DataFrame({"patient": ["private-a", "private-b"]}),
                "Patient",
                {"_id": "patient"},
                parallel_fetch=True,
                show_progress=False,
            )


def test_slow_renewal_expires_worker_wait():
    payload = {"access_token": "synthetic", "token_type": "Bearer", "expires_in": 3600}
    with (
        patch.object(_ClientCredentialsAuth, "_request", return_value=payload),
        _auth() as auth,
    ):
        auth.session.auth._renew_at = 0

        def delayed(*args, **kwargs):
            time.sleep(0.3)
            return payload

        with (
            patch.object(auth.session.auth, "_request", side_effect=delayed),
            managed_pool(auth.session.auth, 1, 0.05) as (pool, events),
            pytest.raises(FHIRRequestError, match="query failed"),
        ):
            list(monitored_results(pool, events, _cached_job, [1], 5))
    assert not any(t.name.startswith("fyron-token-") for t in threading.enumerate())


def test_interrupt_cleans_workers():
    before = {p.pid for p in mp.active_children()}
    with pytest.raises(KeyboardInterrupt), managed_pool(None, 2, 1):
        raise KeyboardInterrupt()
    assert {p.pid for p in mp.active_children()} == before
