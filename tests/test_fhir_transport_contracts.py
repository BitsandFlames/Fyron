"""Synthetic request contracts shared by sequential and worker retrieval."""

from unittest.mock import Mock
from contextlib import contextmanager

import pytest
import requests
from urllib3.util.retry import Retry

from fyron.fhir import rest


@pytest.mark.parametrize("link,expected", [
    ("?page=2", "https://example.test/fhir/Patient?page=2"),
    ("Patient?page=2", "https://example.test/fhir/Patient?page=2"),
    ("/fhir/Patient?page=2", "https://example.test/fhir/Patient?page=2"),
])
def test_relative_links(link, expected):
    assert rest._resolve_next_url("https://example.test/fhir/Patient?page=1", link) == expected


@pytest.mark.parametrize("link", ["https://foreign.test/secret", "//foreign.test/secret",
                                      "http://example.test/fhir", "https://user:secret@example.test/fhir"])
def test_untrusted_links_are_redacted(link):
    with pytest.raises(rest.FHIRRequestError) as exc:
        rest._resolve_next_url("https://example.test/fhir/Patient", link)
    assert "secret" not in str(exc.value)
    assert "example.test" not in str(exc.value)


@pytest.mark.parametrize("payload", [{}, {"resourceType": "OperationOutcome", "text": "secret"}, []])
def test_bad_payloads(payload):
    with pytest.raises(rest.FHIRRequestError):
        rest._ensure_bundle_payload(payload, "https://example.test")


@pytest.mark.parametrize("parallel", [False, True])
def test_page_limits(parallel):
    client = rest.FHIRRestClient(base_url="https://example.test", auth=requests.Session())
    fetch = (lambda limit: client.fetch_bundles_parallel("Patient", [{}], max_pages=limit)) if parallel else (
        lambda limit: client.fetch_bundles("Patient", max_pages=limit, show_progress=False))
    for bad in [-2, True, 1.5, "1"]:
        with pytest.raises(ValueError):
            list(fetch(bad))
    assert list(fetch(0)) == []


@pytest.mark.parametrize("worker", [False, True])
def test_cycles_fail_without_duplicate_results(monkeypatch, worker):
    url = "https://example.test/fhir/Patient"
    request = Mock(return_value=({"resourceType": "Bundle", "link": [
        {"relation": "next", "url": url}]}, url, 200, 1))
    monkeypatch.setattr(rest, "_request_json", request)
    with pytest.raises(rest.FHIRRequestError, match="Repeated pagination"):
        if worker:
            rest._worker_fetch_bundles(("https://example.test/fhir", rest.QueryJob("Patient", {}, -1),
                                       {}, 30, {}, False, False, "none", None, None, None, 0, 0))
        else:
            client = rest.FHIRRestClient(base_url="https://example.test/fhir", auth=requests.Session())
            list(client.fetch_bundles("Patient", show_progress=False))
    assert request.call_count == 1


def test_worker_retry_policy_and_zero_limit(monkeypatch):
    session = requests.Session()
    session.get = Mock(side_effect=AssertionError("No request expected"))
    monkeypatch.setattr(rest.requests, "Session", lambda: session)
    retry = Retry(total=7, allowed_methods=["GET"])
    assert rest._worker_fetch_bundles(("https://example.test", rest.QueryJob("Patient", {}, 0),
                                      {}, 30, {}, False, False, "none", None, None, None, 0, 0,
                                      None, retry)) == []
    assert session.get_adapter("https://example.test").max_retries.total == 7


def test_static_bearer_applies_to_sequential_session():
    session = requests.Session()
    rest.FHIRRestClient(base_url="https://example.test", auth=session, bearer_token="test-only")
    assert session.headers["Authorization"] == "Bearer test-only"


def test_parallel_preserves_explicit_basic_headers_and_retries(monkeypatch):
    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth("explicit-user", "explicit-password")
    session.headers["Accept"] = "application/fhir+json"
    monkeypatch.setenv("FHIR_USER", "wrong-user")
    monkeypatch.setenv("FHIR_PASSWORD", "wrong-password")
    retry = Retry(total=5)
    client = rest.FHIRRestClient(base_url="https://example.test", auth=session, retries=retry)

    @contextmanager
    def pool(*args):
        yield None, None

    def results(pool, events, func, tasks, timeout):
        task = tasks[0]
        assert task[2]["Authorization"] == requests.auth._basic_auth_str("explicit-user", "explicit-password")
        assert task[2]["Accept"] == "application/fhir+json"
        assert task[7] == "explicit_basic"
        assert task[14] is retry
        yield 0, [{"resourceType": "Bundle"}]

    monkeypatch.setattr(rest, "managed_pool", pool)
    monkeypatch.setattr(rest, "monitored_results", results)
    assert len(list(client.fetch_bundles_parallel("Patient", [{}], show_progress=False))) == 1


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_request_timeout(value):
    with pytest.raises(ValueError):
        rest.FHIRRestClient(base_url="https://example.test", request_timeout=value)
