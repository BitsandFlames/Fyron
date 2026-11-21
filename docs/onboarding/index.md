# Query data. Combine it. Build your cohort.

Fyron helps you bring data into a pandas DataFrame and keep working with it. Start with a patient list, retrieve related records through **FHIR REST or SQL**, then combine the result with a CSV, study groups or other tables.

**Patient list → REST or SQL query → DataFrame → combine → save.**

This first walkthrough uses three invented patient IDs. Choose **one** query route below, then continue with the same pandas steps. You do not need both a FHIR server and a database.

## Before you start

Install Fyron in your project:

```bash
uv add "fyron==0.3.20b6"
```

Use Python 3.11+ and your administrator's approved access settings. All IDs and values below are synthetic. The HTTP route needs your own permitted service and matching IDs. The SQL route runs invented rows on your PostgreSQL connection without creating tables.

Choose the authentication your site supports in [Authentication](authentication.md). Keep `.env`, token caches and downloaded data out of Git. These examples load `.env` explicitly.

## 1. Start with a small table

Run these blocks in a notebook, or place them together in a Python script. Start with:

```python
import pandas as pd

cohort = pd.DataFrame({
    "patient_id": ["001", "002", "003"],
    "study_group": ["A", "A", "B"],
})

# Or start with your own reviewed CSV:
# cohort = pd.read_csv("cohort.csv", dtype={"patient_id": "string"})

if cohort["patient_id"].isna().any() or cohort["patient_id"].duplicated().any():
    raise ValueError("Use one nonmissing patient ID per cohort row")
```

This is your starting population. Keep IDs as strings so `001` does not become `1`. For REST, these must be FHIR logical patient IDs. For SQL, they must match the selected database key. If your CSV uses a different identifier, map it explicitly first.

## 2A. Query through FHIR REST

Use this route when your site provides a FHIR REST endpoint. This example uses browser-approved device login. Other permitted methods can be substituted using the [authentication recipes](authentication.md).

Load approved values through a private `.env` file:

```dotenv
DEMO_FHIR_URL=https://fhir.example.org/r4
DEMO_OIDC_ISSUER=https://login.example.org
DEMO_CLIENT_ID=replace-with-approved-client
DEMO_SCOPE=replace-with-approved-scope
```

Continue after the cohort block:

```python
import os
from dotenv import load_dotenv
from fyron import Auth, FHIRRestClient

load_dotenv(".env", override=False)

with Auth(
    auth_type="device_code",
    auth_url=os.environ["DEMO_OIDC_ISSUER"],
    client_id=os.environ["DEMO_CLIENT_ID"],
    scope=os.environ["DEMO_SCOPE"],
) as auth:
    with FHIRRestClient(os.environ["DEMO_FHIR_URL"], auth=auth) as client:
        # First: inspect a small page to see how the service returns data.
        preview = client.search_df(
            "Patient", params={"_count": 5}, max_pages=1,
            fhir_paths=[("patient_id", "id")],
            use_multiprocessing=False,
        )
        # Inspect `preview` privately. It is not a complete patient population.

        # Next: retrieve observations only for the patients in our table.
        result = client.query_df_from(
            cohort, resource_type="Observation",
            column_map={"subject": "patient_id"},
            param_prefix={"subject": "Patient/"},
            params={"_count": 100}, max_pages=-1,
            fhir_paths=[
                ("record_id", "id"),
                ("patient_reference", "subject.reference"),
            ],
            use_multiprocessing=False, parallel_fetch=False,
            return_report=True,
        )

summary = result["report"]["summary"].iloc[0]
if not summary["execution_complete"] or (
    summary["queries"] and not summary["retrieval_exhaustive"]
):
    raise RuntimeError("Review the extraction report before continuing")

records = result["data"].copy()
if records.empty:
    records = pd.DataFrame(columns=["record_id", "patient_id"])
else:
    # This example accepts relative Patient/<id> references only.
    records["patient_id"] = records["patient_reference"].astype("string").str.extract(
        r"^Patient/([A-Za-z0-9.-]{1,64})$", expand=False,
    )
    if records["patient_id"].isna().any():
        raise ValueError("Map missing or unsupported patient references first")
```

**How you build the query:** `"Observation"` chooses the resource. `column_map` takes each `patient_id` from your DataFrame and sends it as a `subject` search. `param_prefix` turns `001` into `Patient/001`. `fhir_paths` chooses the output columns.

Add a supported filter in `params`, for example `"date": "ge2025-01-01"`. Ask your administrator which search parameters and codes the server supports. Inspect `result["report"]["rows"]` and `result["report"]["summary"]`; exhausted pagination does not prove that a server has no hidden cap.

**Want to build the starting cohort from a larger query?** The [FHIR REST walkthrough](fhir-rest.md) shows date-partitioned Condition queries, extracting patient IDs, and passing those IDs into the next query.

## 2B. Query through PostgreSQL

Use this route instead of the REST block when your data is available through PostgreSQL. Configure the connection using the [SQL connection example](sql.md#connect-with-approved-database-credentials), including explicit `.env` loading and approved TLS settings. SQL credentials are separate from HTTP authentication; libpq must be installed.

Continue after the same cohort block:

```python
from dotenv import load_dotenv
from fyron import FHIRSQLClient

load_dotenv(".env", override=False)

# Invented database rows make this example independent of your site's schema.
# Later, replace the WITH block with your approved table or view.
sql = """
WITH observations(patient_id, record_id, code) AS (
    VALUES ('001', 'obs-1', 'demo'),
           ('001', 'obs-2', 'demo'),
           ('002', 'obs-3', 'demo'),
           ('004', 'obs-4', 'demo')
)
SELECT patient_id, record_id
FROM observations
WHERE patient_id IN ({cohort_keys}) AND code = %(code)s
"""

with FHIRSQLClient(connect_timeout=10) as client:
    # First: a normal SQL query returns a DataFrame.
    preview = client.query_df(
        "SELECT %(patient_id)s::text AS patient_id",
        params={"patient_id": "001"},
    )

    # Next: use the patient IDs from our existing DataFrame as a filter.
    result = client.query_df_for_keys(
        cohort, sql, key_columns=["patient_id"],
        params={"code": "demo"}, result_key_columns=["patient_id"],
        parallel=False, return_report=True,
    )

records = result["data"]
# Inspect the report privately, including result["report"]["unmatched_keys"].
```

**How you build the query:** write ordinary SQL and put `{cohort_keys}` where the patient list belongs. `key_columns` tells Fyron which DataFrame column to use. Other values use bound parameters such as `%(code)s`. Fyron binds the values for you; do not insert IDs with f-strings.

**Expected here:** two rows for `001`, one for `002`, none for `003`. Patient `004` is excluded because it is not in our cohort. A failed batch raises rather than returning a successful partial extraction.

The [PostgreSQL walkthrough](sql.md) also shows a database query that creates the starting cohort, paired patient/encounter keys and coverage reports.

## 3. Combine the result with your other data

Both routes now give you `records` with a `patient_id` column. Use normal pandas operations to combine it with the study groups from your original table:

```python
# Keep every returned record and add its patient's study group.
if not records["patient_id"].isin(cohort["patient_id"]).all():
    raise ValueError("Returned IDs do not match the reviewed cohort")

labelled_records = records.merge(
    cohort, on="patient_id", how="left", validate="many_to_one",
)

# Or make a patient-level table with a count of returned records.
counts = records.groupby("patient_id").size().rename("returned_record_count")
patient_table = cohort.merge(
    counts, on="patient_id", how="left", validate="one_to_one",
)
patient_table["returned_record_count"] = (
    patient_table["returned_record_count"].fillna(0).astype("int64")
)
```

For the synthetic SQL example, `patient_table` is:

| patient_id | study_group | returned_record_count |
| --- | --- | --- |
| 001 | A | 2 |
| 002 | A | 1 |
| 003 | B | 0 |

Zero means **this query returned no records**, not that the patient has no disease or measurements. Counts are a simple starting example. Choose relevant codes, units and dates before calculating clinical summaries.

## 4. Save it or keep going

```python
from pathlib import Path

Path("results").mkdir(exist_ok=True)
patient_table.to_csv("results/patient-table.csv", index=False)
labelled_records.to_csv("results/labelled-records.csv", index=False)
for name, table in result["report"].items():
    table.to_csv(f"results/query-{name}.csv", index=False)
```

From here you can combine another CSV, apply an explicit cohort filter, prepare descriptive tables, or retrieve files:

- [FHIR REST](fhir-rest.md): start broad with partitions, then query related records.
- [PostgreSQL](sql.md): start with a SQL cohort, then query single or paired keys.
- [DICOMweb](dicomweb.md): download studies from a reviewed UID table.
- [Documents](documents.md): download PDFs or text from a CSV of URLs.
- [Cohorts](../modules/cohort.md): inspect joins and construct study endpoints.
- [Descriptive analysis](../modules/descriptive.md): summarize the prepared table.

Start with one query and inspect the resulting DataFrame. Add the next step when the identifiers and rows make sense.

See [Reconcile a document cohort and retry a failed download](reconciliation.md) for the five-patient offline walkthrough.
