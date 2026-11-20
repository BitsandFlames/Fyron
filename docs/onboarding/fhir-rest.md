# FHIR REST: build a cohort, then follow its IDs

**You will produce:** `cohort.csv`, `observations.csv`, and separate reports for the starting and dependent queries.

**Prerequisite:** complete [Setup](index.md) and save [onboarding_auth.py](authentication.md). Confirm that your FHIR server supports `Condition`, `Observation`, `recorded-date`, `subject` and `_sort=_id`.

### First inspect a small result

**Exercise 1.** Save the entire next Python block as `rest_cohort.py`, beside `onboarding_auth.py`. Configure `.env` for your approved FHIR service. The initial one-page query is a **preview**, not a complete cohort.

```python
import os
import pandas as pd
from fyron import FHIRRestClient
from onboarding_auth import make_auth

CONDITION_FIELDS = [
    ("condition_id", "id"),
    ("patient_reference", "subject.reference"),
    ("recorded_date", "recordedDate"),
]


def require_exhaustive(result):
    summary = result["report"]["summary"].iloc[0]
    if not summary["execution_complete"] or (summary["queries"] and not summary["retrieval_exhaustive"]):
        raise RuntimeError("Extraction is page-limited; review its report")
    return result["data"]


def patient_keys(records):
    references = records.get(
        "patient_reference", pd.Series(index=records.index, dtype="object")
    )
    # Accept only relative Patient/<FHIR logical id> references in this tutorial.
    ids = references.map(
        lambda value: value if isinstance(value, str) else None
    ).str.extract(r"^Patient/([A-Za-z0-9.-]{1,64})$", expand=False)
    unresolved = records.loc[ids.isna()].copy()
    keys = pd.DataFrame({"patient_id": ids.dropna().drop_duplicates()})
    return keys.reset_index(drop=True), unresolved


def rest_workflow(client):
    preview = client.search_df(
        "Condition", params={"_count": 10}, max_pages=1,
        fhir_paths=CONDITION_FIELDS, use_multiprocessing=False,
        return_report=True,
    )
    print("Preview report:")
    print(preview["report"]["summary"].to_string(index=False))

    extraction = client.search_df_partitioned(
        "Condition", partition_param="recorded-date",
        start="2025-01-01", end="2025-04-01", frequency="MS",
        params={"_count": 100}, max_pages_per_partition=-1,
        fhir_paths=CONDITION_FIELDS, deduplicate_by="condition_id",
        use_multiprocessing=False, parallel_fetch=False,
        show_progress=False, return_report=True,
    )
    conditions = require_exhaustive(extraction)
    cohort, unresolved = patient_keys(conditions)
    if not unresolved.empty:
        # Inspect this table privately; never silently discard unresolved patients.
        raise ValueError("Resolve missing or unsupported patient references first")
    if cohort.empty:
        return cohort, pd.DataFrame(), {"conditions": extraction["report"]}

    related = client.query_df_from(
        cohort, resource_type="Observation",
        column_map={"subject": "patient_id"},
        param_prefix={"subject": "Patient/"},
        params={"_count": 100}, max_pages=-1,
        fhir_paths=[
            ("observation_id", "id"),
            ("patient_reference", "subject.reference"),
            ("value", "valueQuantity.value"),
            ("unit", "valueQuantity.unit"),
        ],
        use_multiprocessing=False, parallel_fetch=False,
        show_progress=False, return_report=True,
    )
    observations = require_exhaustive(related)
    return cohort, observations, {"conditions": extraction["report"], "observations": related["report"]}


if __name__ == "__main__":
    with make_auth("device_code", cache_name="fhir-demo.json") as auth:
        with FHIRRestClient(
            os.environ["DEMO_FHIR_URL"], auth=auth, num_processes=1,
        ) as client:
            cohort, observations, reports = rest_workflow(client)
            from pathlib import Path
            Path("results").mkdir(exist_ok=True)
            cohort.to_csv("results/cohort.csv", index=False)
            observations.to_csv("results/observations.csv", index=False)
            for label, report in reports.items():
                report["rows"].to_csv(f"results/{label}-query-report.csv", index=False)
                report["summary"].to_csv(f"results/{label}-summary.csv", index=False)
            print(f"Cohort patients: {len(cohort)}")
            print(f"Observation rows: {len(observations)}")
            for label, report in reports.items():
                print(label, report["summary"].to_string(index=False))
```

Run it:

```bash
uv run python rest_cohort.py
```

**Check your result:** inspect `results/cohort.csv`, `results/observations.csv` and the `conditions-*` and `observations-*` report files in your approved local environment. Counts depend on your service. Expect one row per distinct patient in the cohort, potentially several observation rows per patient, and one dependent-query report row per cohort patient. Stop if the script reports unresolved references or limited pagination. An empty cohort is a valid query outcome, not a reason to remove filters blindly.

**Try a change:** shorten the date range to one month, rerun, and compare the cohort count. Then change the dependent resource from `Observation` only after choosing its supported search parameters and projections.

`search_df_from(...)` is the preferred REST-facing convenience name and accepts the same arguments as `query_df_from(...)`. Either makes one dependent search per input row; deduplicate your patient table first. `column_map` maps **FHIR search parameter → DataFrame column**.

The partition start is inclusive and the end exclusive. Fyron adds trace columns for each date window and defaults to `_sort=_id`; confirm the server supports the chosen date parameter and sort. `max_pages_per_partition=-1` follows available pagination within each window. The report can detect page limits, but cannot prove a server has not silently capped its results. Narrow windows or use the site's approved bulk-extraction route if caps persist. A recorded date is not necessarily a diagnosis onset date or complete patient history.

`execution_complete` means the requested work executed. `retrieval_exhaustive` describes the observed pagination, not clinical completeness. Inspect `report["rows"]` for `page_limited`, `no_match` and per-query counts. A request failure raises; never catch it and label accumulated output complete.

The reference helper deliberately stops on absolute, versioned, contained, missing or list-valued references. Review those privately and implement an explicit site-approved mapping. A FHIR logical patient ID is not automatically a medical-record number, DICOM PatientID or warehouse patient key.

Keep repeated observations. Before a cohort merge, select clinically comparable measurements, units and dates explicitly. Do not average unrelated laboratory values just because they belong to one patient.

## Read the cohort file without losing IDs

```python
cohort = pd.read_csv("results/cohort.csv", dtype={"patient_id": "string"})
if cohort["patient_id"].isna().any() or cohort["patient_id"].duplicated().any():
    raise ValueError("Review missing or duplicate cohort identifiers before querying")
```

This snippet belongs after the imports in a follow-up script. Do not cast patient IDs to numbers. The first extraction selects conditions recorded within the date window; it does not by itself define a disease phenotype or establish clinical eligibility.

## From FHIR resources to download inputs

Use the same dependent-query pattern for `ImagingStudy` or `DocumentReference`, with reviewed projections such as:

```python
imaging_fields = [
    ("imaging_id", "id"),
    ("study_uid", "identifier.where(system = 'urn:dicom:uid').value"),
]
document_fields = [
    ("document_id", "id"),
    ("document_url", "content.attachment.url"),
    ("content_type", "content.attachment.contentType"),
]
```

These projections are starting points, not ready-made download manifests. Review missing and multivalued fields. A DICOM identifier may carry a `urn:oid:` prefix; map a verified DICOM UID explicitly rather than using the FHIR resource ID. A document may have several attachments, inline data, relative URLs, or a `Binary` reference requiring a different endpoint. Select attachments deliberately, resolve only approved URLs, and assign unique document IDs after expansion. Never send a service token to unreviewed attachment hosts.

The runnable downloader examples below use small, explicitly synthetic manifests instead of assuming those mappings are universal.

## Next: download the reviewed files

Continue with [DICOMweb](dicomweb.md) for study UIDs or [Documents](documents.md) for approved attachment URLs. To compare the same cohort-first pattern in a database, use [PostgreSQL](sql.md).

## Reliability in current source

Inspect `executed_queries`, `not_requested` and `pagination_complete_queries` alongside the existing report fields. Keep page limits separate from empty matches. These options are included in Beta 5.
