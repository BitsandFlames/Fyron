"""Real-process regressions for password-to-token DICOM downloads."""

import multiprocessing as mp
import threading
from unittest.mock import Mock

import pandas as pd
import pytest
import requests
from test_device_auth import provider as _http_provider

from fyron import Auth, DICOMDownloader
from fyron.fhir._device_auth import DeviceAuthError
from fyron.fhir._workers import managed_pool, worker_auth

provider = _http_provider


def reject_token(_):
    handler = worker_auth()
    token = handler.get_token()
    return handler.get_token(rejected=token)


@pytest.mark.parametrize("renewal", ["refresh", "relogin", "no_refresh_url"])
def test_password_token_downloads_are_parallel(
    provider, monkeypatch, tmp_path, renewal
):
    import fyron.dicom.client as module

    monkeypatch.setattr(module.mp, "Pool", mp.get_context("spawn").Pool)
    monkeypatch.setenv("FHIR_USER", "user")
    monkeypatch.setenv("FHIR_PASSWORD", "pass")
    monkeypatch.setenv("DICOM_USER", "must-not-override")
    monkeypatch.setenv("DICOM_PASSWORD", "must-not-override")
    refresh_url = (
        None if renewal == "no_refresh_url" else provider["url"] + "/password-refresh"
    )
    with Auth.token_env(
        auth_url=provider["url"] + "/password-login", refresh_url=refresh_url
    ) as auth:
        provider.update(
            revoked=True,
            reject_password_refresh=renewal == "relogin",
            download_delay=0.5,
        )
        downloader = DICOMDownloader(
            auth=auth,
            dicom_web_url=provider["url"],
            output_format="dicom",
            num_processes=3,
        )
        results = downloader.download_from_dataframe(
            pd.DataFrame(
                {
                    "study": [f"1.2.{i}" for i in range(6)],
                    "series": [f"1.2.{i}.1" for i in range(6)],
                }
            ),
            output_dir=tmp_path,
            study_uid_col="study",
            series_uid_col="series",
            download_full_study=False,
        )
        assert downloader.num_processes == 3
        assert len(results) == 6
        assert results["error"].isna().all()
        assert len(list(tmp_path.rglob("*.dcm"))) == 6
        assert provider["peak_downloads"] >= 2
        assert auth.session.auth._get_token(rejected="access-1") == "access-2"
    assert provider["refreshes"] == (0 if renewal == "no_refresh_url" else 1)
    assert provider["logins"] == (1 if renewal == "refresh" else 2)
    assert all(
        header.startswith("Bearer ")
        for path, header in provider["requests"]
        if path.startswith("/studies/")
    )
    assert not any(t.name.startswith("fyron-token-") for t in threading.enumerate())


def test_token_coordinator_failure_redacts_credentials(provider, monkeypatch):
    monkeypatch.setenv("FHIR_USER", "user")
    monkeypatch.setenv("FHIR_PASSWORD", "pass")
    with Auth.token_env(auth_url=provider["url"] + "/password-login") as auth:
        monkeypatch.setattr(
            auth.session.auth,
            "_refresh",
            Mock(side_effect=requests.HTTPError("secret")),
        )
        with managed_pool(auth.session.auth, 1, 10) as (pool, events):
            with pytest.raises(DeviceAuthError, match="Parent token renewal") as error:
                pool.map(reject_token, [None])
            assert "secret" not in str(error.value)
    assert not any(t.name.startswith("fyron-token-") for t in threading.enumerate())
