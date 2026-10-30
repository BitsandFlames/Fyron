"""Synthetic adapters exercise Requests redirects without any network access."""

import json
import io
import requests
import pytest

from fyron.fhir import rest


class RedirectAdapter(requests.adapters.BaseAdapter):
    def __init__(self, destination):
        self.destination = destination
        self.calls = []

    def send(self, request, **kwargs):
        self.calls.append(request)
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = 307 if len(self.calls) == 1 else 200
        if len(self.calls) == 1:
            response.headers["Location"] = self.destination
        response._content = json.dumps({"resourceType": "Bundle", "entry": []}).encode()
        response.raw = io.BytesIO(response._content)
        return response

    def close(self):
        pass


@pytest.mark.parametrize("operation", ["read", "write"])
@pytest.mark.parametrize("destination", ["https://foreign.invalid/collect", "http://service.invalid/fhir",
                                          "https://service.invalid:8443/fhir", "https://user:secret@service.invalid/fhir"])
def test_fhir_blocks_unsafe_redirects_before_transmission(operation, destination):
    session = requests.Session()
    session.trust_env = False
    adapter = RedirectAdapter(destination)
    session.mount("https://", adapter); session.mount("http://", adapter)
    session.headers["X-API-Key"] = "SYNTHETIC"
    with pytest.raises(rest.FHIRRequestError):
        if operation == "write":
            rest._write_json_request(session, "POST", "https://service.invalid/fhir",
                                     {"resourceType": "Patient", "id": "SYNTHETIC"}, 5, None)
        else:
            rest._request_json(session, "https://service.invalid/fhir", {}, 5, None)
    assert len(adapter.calls) == 1


def test_same_origin_redirects_and_existing_hooks_still_work():
    session = requests.Session(); session.trust_env = False
    adapter = RedirectAdapter("/fhir/page2")
    session.mount("https://", adapter)
    seen = []
    session.hooks["response"].append(lambda response, **kwargs: seen.append(response.status_code))
    payload, url, status, _ = rest._request_json(session, "https://service.invalid/fhir", {}, 5, None)
    assert payload["resourceType"] == "Bundle" and status == 200
    assert url == "https://service.invalid/fhir/page2"
    assert seen == [307, 200]


@pytest.mark.parametrize("client_kind", ["documents", "dicom", "llm"])
def test_other_network_clients_guard_shared_transport(tmp_path, client_kind):
    from fyron.documents import DocumentDownloader
    from fyron.dicom import DICOMDownloader
    from fyron.llm import LLMAgent
    session = requests.Session(); session.trust_env = False
    if client_kind == "documents":
        client = DocumentDownloader(output_dir=tmp_path, auth=session)
    elif client_kind == "dicom":
        client = DICOMDownloader(dicom_web_url="https://service.invalid", auth=session)
    else:
        client = LLMAgent(provider="custom", base_url="https://service.invalid", auth_required=False)
        session = client.session
    adapter = RedirectAdapter("https://foreign.invalid/collect")
    session.mount("https://", adapter)
    with pytest.raises(requests.RequestException, match="redirect"):
        session.post("https://service.invalid/input", json={"text": "SYNTHETIC"})
    assert len(adapter.calls) == 1
