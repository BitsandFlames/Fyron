"""Provider-neutral service-account authentication tests."""

import multiprocessing as mp
import pickle
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pandas as pd
import pytest
import requests
from test_device_auth import provider as _http_provider

from fyron import Auth, DICOMDownloader, FHIRRestClient
from fyron.fhir._client_credentials import _ClientCredentialsAuth
from fyron.fhir._workers import TokenBroker

provider = _http_provider


def token(value="first", **kwargs):
    return dict(access_token=value, token_type="Bearer", expires_in=3600, **kwargs)


def make(**kwargs):
    return Auth.client_credentials(
        client_id="research",
        client_secret="secret",
        token_endpoint="https://id.example.org/token",
        **kwargs,
    )


@pytest.mark.parametrize("method", ["client_secret_basic", "client_secret_post"])
def test_form_credentials_and_bearer(method):
    with (
        patch.object(
            _ClientCredentialsAuth, "_request", return_value=token()
        ) as request,
        make(client_auth_method=method, scope="system/Patient.read") as auth,
    ):
        prepared = auth.session.prepare_request(
            requests.Request("GET", "https://fhir.example.org/Patient")
        )
        assert prepared.headers["Authorization"] == "Bearer first"
        data = request.call_args.kwargs["data"]
        assert data["grant_type"] == "client_credentials"
        assert data["scope"] == "system/Patient.read"
        if method == "client_secret_basic":
            assert request.call_args.kwargs["auth"] == ("research", "secret")
            assert "client_secret" not in data
        else:
            assert data["client_secret"] == "secret"


def test_discovery_and_rotation():
    metadata = {
        "issuer": "https://id.example.org",
        "token_endpoint": "https://id.example.org/token",
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
    }
    with (
        patch.object(
            _ClientCredentialsAuth,
            "_request",
            side_effect=[metadata, token(), token("second"), token("third")],
        ),
        Auth.client_credentials(
            auth_url=metadata["issuer"], client_id="a", client_secret="b"
        ) as auth,
    ):
        handler = auth.session.auth
        assert handler.client_method == "client_secret_post"
        assert handler.get_token(rejected="first") == "second"
        assert handler.get_token(rejected="first") == "second"
        handler._renew_at = 0
        assert handler.get_token() == "third"
        copy = pickle.loads(pickle.dumps(handler))
        assert copy.get_token() == "third"
        copy.close()


def test_coordinator_serializes_rejections():
    with (
        patch.object(
            _ClientCredentialsAuth, "_request", side_effect=[token(), token("second")]
        ) as request,
        make() as auth,
    ):
        broker = TokenBroker(auth.session.auth)
        generation = broker.lease(None)[1]
        with ThreadPoolExecutor(max_workers=4) as pool:
            assert [lease[0] for lease in pool.map(broker.lease, [generation] * 8)] == ["second"] * 8
        assert request.call_count == 2


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"access_token": "x", "token_type": "MAC"},
        {"access_token": "x", "token_type": "Bearer", "expires_in": -1},
    ],
)
def test_invalid_tokens(payload):
    with (
        patch.object(_ClientCredentialsAuth, "_request", return_value=payload),
        pytest.raises(RuntimeError),
    ):
        make()


def test_issuer_mismatch():
    with (
        patch.object(
            _ClientCredentialsAuth,
            "_request",
            return_value={"issuer": "https://wrong.example.org"},
        ),
        pytest.raises(RuntimeError, match="issuer"),
    ):
        Auth.client_credentials(
            auth_url="https://id.example.org", client_id="a", client_secret="b"
        )


def test_redacted_network_failure():
    with patch(
        "requests.Session.request", side_effect=requests.ConnectionError("secret token")
    ):
        with pytest.raises(RuntimeError) as error:
            make()
        assert "secret" not in str(error.value)
        assert error.value.__suppress_context__


def test_redirect_rejected():
    response = requests.Response()
    response.status_code = 302
    response._content = b"secret"
    response._content_consumed = True
    with patch("requests.Session.request", return_value=response) as request:
        with pytest.raises(RuntimeError, match="redirected"):
            make()
        assert request.call_args.kwargs["allow_redirects"] is False


def test_direct_style_and_no_password_environment(monkeypatch):
    monkeypatch.delenv("FHIR_USER", raising=False)
    with (
        patch.object(_ClientCredentialsAuth, "_request", return_value=token()),
        Auth(
            auth_type="client_credentials",
            client_id="a",
            client_secret="b",
            token_endpoint="https://id.example.org/token",
        ) as auth,
    ):
        assert auth.session.auth.scope == ""


def test_socket_fhir_and_dicom_spawn(provider, monkeypatch, tmp_path):
    import fyron.dicom.client as dicom
    from fyron.fhir import rest

    monkeypatch.setattr(rest.mp, "Pool", mp.get_context("spawn").Pool)
    monkeypatch.setattr(dicom.mp, "Pool", mp.get_context("spawn").Pool)
    with Auth.client_credentials(
        auth_url=provider["url"], client_id="research", client_secret="secret"
    ) as auth:
        provider["revoked"] = True
        client = FHIRRestClient(provider["url"], auth=auth, num_processes=2)
        assert (
            len(
                list(
                    client.fetch_bundles_parallel(
                        "Patient", [{"x": 1}, {"x": 2}], show_progress=False
                    )
                )
            )
            == 2
        )
        assert provider["generation"] == 2
        provider["revoked"] = True
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
        assert results["error"].isna().all()
        assert len(list(tmp_path.rglob("*.dcm"))) == 2
        assert provider["generation"] == 3
        assert all(
            body["grant_type"] == ["client_credentials"] for body in provider["bodies"]
        )
