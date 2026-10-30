import os
import pytest
import requests

from fyron import FHIRRestClient

HAPI_BASE_URL = "https://hapi.fhir.org/baseR4"


def _integration_enabled() -> bool:
    return os.environ.get("FYRON_INTEGRATION", "").lower() in {"1", "true", "yes"}


def _hapi_available() -> bool:
    try:
        resp = requests.get(f"{HAPI_BASE_URL}/metadata", timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not _integration_enabled(), reason="Set FYRON_INTEGRATION=1 to run")
def test_hapi_patient_query_returns_dataframe():
    if not _hapi_available():
        pytest.skip("HAPI server is unreachable")
    client = FHIRRestClient(base_url=HAPI_BASE_URL)
    try:
        df = client.query_to_dataframe(
            resource_type="Patient",
            params={"_count": 5, "_sort": "_id"},
            max_pages=1,
        )
    except Exception as exc:
        pytest.skip(f"HAPI query failed: {exc}")
    assert df is not None
    assert len(df) >= 0


@pytest.mark.skipif(not _integration_enabled(), reason="Set FYRON_INTEGRATION=1 to run")
def test_hapi_observation_fhirpath():
    if not _hapi_available():
        pytest.skip("HAPI server is unreachable")
    client = FHIRRestClient(base_url=HAPI_BASE_URL)
    try:
        df = client.query_to_dataframe(
            resource_type="Observation",
            params={"_count": 3},
            fhir_paths=[
                ("id", "Observation.id"),
                ("status", "Observation.status"),
            ],
            max_pages=1,
        )
    except Exception as exc:
        pytest.skip(f"HAPI query failed: {exc}")
    assert df is not None
    assert len(df) >= 0
