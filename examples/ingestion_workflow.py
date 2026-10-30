"""Synthetic FHIR bundle to audited cohort; no server or credentials required."""

import argparse
from pathlib import Path

import pandas as pd
import requests
from fyron import FHIRRestClient
from fyron.cohort import (
    audit_cohort_join, join_cohort_tables, audit_time_to_event_endpoint,
    build_time_to_event_endpoint,
)


class OfflineSession(requests.Session):
    """Prevent accidental HTTP calls, including inherited environment auth."""

    def send(self, request, **kwargs):
        raise AssertionError("This synthetic example must not make HTTP requests.")


def run(output_dir):
    bundle = {"resourceType": "Bundle", "type": "searchset", "entry": [
        {"resource": {"resourceType": "Patient", "id": f"synthetic-{i}", "gender": "unknown"}}
        for i in range(4)
    ]}
    session = OfflineSession()
    session.trust_env = False
    client = FHIRRestClient(base_url="https://example.invalid/fhir", auth=session, num_processes=1)
    try:
        patients = client.bundles_to_dataframe(
            [bundle], fhir_paths=[("patient_id", "id"), ("gender", "gender")],
            use_multiprocessing=False,
        )
    finally:
        client.session.close()
    if isinstance(patients, dict):
        patients = patients["Patient"]
    outcomes = pd.DataFrame({
        "patient_id": [f"synthetic-{i}" for i in range(4)],
        "baseline": ["2020-01-01"] * 4,
        "event_date": ["2020-02-01", None, "2021-01-01", None],
        "followup": ["2020-06-01", "2020-06-01", "2020-06-01", None],
    })
    joins = audit_cohort_join(patients, outcomes)
    frame = join_cohort_tables(patients, outcomes)
    options = dict(index_date_col="baseline", event_date_col="event_date",
                   censor_date_col="followup", administrative_censor_date="2020-05-01")
    quality = audit_time_to_event_endpoint(frame, **options)
    endpoints = build_time_to_event_endpoint(frame, **options, require_endpoint=False)
    cohort = endpoints.loc[quality["rows"].positive_duration_eligible].copy()
    assert len(patients) == 4 and len(cohort) == 3
    assert cohort.event.tolist() == [1, 0, 0]
    assert quality["rows"].missing_endpoint.sum() == 1
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name, table in [("cohort", cohort), ("endpoint-quality", quality["summary"]), ("join-quality", joins)]:
        table.to_csv(output / f"{name}.csv", index=False)
        assert (output / f"{name}.csv").stat().st_size > 0
    return cohort


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    run(parser.parse_args().output_dir)
