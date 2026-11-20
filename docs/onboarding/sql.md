# PostgreSQL: a cohort-first workflow

**You will produce:** three synthetic patient IDs, three measurement rows, two correctly paired visits, and an unmatched-key table containing `003`.

**Prerequisite:** [Setup](index.md), libpq and an approved PostgreSQL connection. This exercise does not use the HTTP authentication helper or require a FHIR server.

### Connect with approved database credentials

PostgreSQL does not use `make_auth`. Obtain your database host, role, TLS settings and schema separately. Use a read-only role when appropriate. In a separate `.env`:

```dotenv
FHIR_DB_HOST=database.example.org
FHIR_DB_PORT=5432
FHIR_DB_NAME=demo_database
FHIR_DB_USER=replace-with-approved-role
FHIR_DB_PASSWORD=replace-with-approved-password
FHIR_DB_SSLMODE=verify-full
PGSSLROOTCERT=/path/to/approved-ca.pem
```

Fyron reads `FHIR_DB_*` after your script loads the file. `PGSSLROOTCERT` is a libpq setting. Use the administrator's CA file and matching hostname; do not disable verification. Psycopg needs a working libpq installation; see [SQL authentication](../authentication/sql.md) for platform setup.

### First table, then dependent queries

**Exercise 4.** Save the entire next block as `sql_cohort.py`. Load the database `.env` shown above. This script uses only invented rows and performs no table creation or inserts. It still needs an approved PostgreSQL connection to execute the queries:

```python
import pandas as pd
from dotenv import load_dotenv
from fyron import FHIRSQLClient

load_dotenv(".env", override=False)

# Optional MCP demo: describe the query to your approved assistant/tool.
# Prompt: "Using synthetic patients(patient_id text, included boolean),
# return distinct included patient IDs. Bind the flag as %(included)s.
# Use the synthetic VALUES rows below. Return SQL only; do not execute it."
# Illustrative tool call only (not a Fyron API or a configured connection):
# draft = await mcp_session.call_tool("draft_sql", {"question": prompt})
# Tool names/arguments depend on your server. Review the returned SQL first.
# The SQL below stands in for that reviewed response; no MCP call is made.
PATIENT_SQL = """
WITH patients(patient_id, included) AS (
    VALUES ('001', true), ('002', true), ('003', true), ('004', false)
)
SELECT DISTINCT patient_id FROM patients WHERE included = %(included)s
"""
# Optional follow-up prompt to the same approved drafting tool:
# "For synthetic measurements(patient_id text, code text, value integer),
# return patient_id and value for my local cohort and selected code.
# Use patient_id IN ({cohort_keys}) and code = %(code)s.
# Keep repeated measurements. Return a SQL template only; do not execute."
# Send the approved schema description, not your real patient IDs/DataFrame.
# Copy the reviewed template here. Fyron binds cohort IDs locally later.
MEASUREMENT_SQL = """
WITH measurements(patient_id, code, value) AS (
    VALUES ('001', 'demo', 10), ('001', 'demo', 12), ('002', 'demo', 20)
)
SELECT patient_id, value FROM measurements
WHERE patient_id IN ({cohort_keys}) AND code = %(code)s
"""
# Optional paired-key prompt:
# "Keep patient/encounter pairs together using
# (patient_id, encounter_id) IN ({cohort_keys}), not separate IN lists."
PAIRED_SQL = """
WITH visits(patient_id, encounter_id, value) AS (
    VALUES ('001', 'a', 10), ('001', 'b', 99), ('002', 'a', 99), ('002', 'b', 20)
)
SELECT * FROM visits
WHERE (patient_id, encounter_id) IN ({cohort_keys})
"""


def sql_workflow(client):
    cohort = client.query_df(PATIENT_SQL, params={"included": True})
    result = client.query_df_for_keys(
        cohort, MEASUREMENT_SQL, key_columns=["patient_id"],
        params={"code": "demo"}, result_key_columns=["patient_id"],
        chunk_size=1000, parallel=False, return_report=True,
    )
    measurements = result["data"]
    print(result["report"]["summary"].to_string(index=False))
    # These are synthetic expectations, not rules for a real research cohort.
    assert len(measurements) == 3
    assert set(result["report"]["unmatched_keys"]["patient_id"]) == {"003"}

    pairs = pd.DataFrame({"patient_id": ["001", "002"], "encounter_id": ["a", "b"]})
    visits = client.query_df_for_keys(
        pairs, PAIRED_SQL, key_columns=["patient_id", "encounter_id"],
        result_key_columns=["patient_id", "encounter_id"],
    )
    assert sorted(visits["value"].tolist()) == [10, 20]
    # Only values 10 and 20 match; the cross-pair values 99 are excluded.

    counts = measurements.groupby("patient_id").size().rename("measurement_count")
    annotated = cohort.merge(
        counts, on="patient_id", how="left", validate="one_to_one",
    )
    # Leave missing counts explicit; no returned measurement is not a clinical negative.
    from pathlib import Path
    Path("results").mkdir(exist_ok=True)
    measurements.to_csv("results/sql-measurements.csv", index=False)
    annotated.to_csv("results/sql-cohort.csv", index=False)
    visits.to_csv("results/sql-visits.csv", index=False)
    for name, table in result["report"].items():
        table.to_csv(f"results/sql-{name}.csv", index=False)
    return annotated, visits, result["report"]


if __name__ == "__main__":
    with FHIRSQLClient(connect_timeout=10) as client:
        annotated, visits, report = sql_workflow(client)
        print("Synthetic cohort with measurement counts:")
        print(annotated.to_string(index=False))
        print("Synthetic paired visits:")
        print(visits.to_string(index=False))
        print("Synthetic keys without measurements:")
        print(report["unmatched_keys"].to_string(index=False))
```

Run it:

```bash
uv run python sql_cohort.py
```

**Expected result for these synthetic rows** (display spacing and row order may vary):

| patient_id | measurement_count |
| --- | --- |
| 001 | 2 |
| 002 | 1 |
| 003 | missing (`NaN`) |

The paired visit values are `10` and `20`; neither cross-pair value `99` is returned. The unmatched-key table contains `003`. If you see a libpq error before connecting, follow the [SQL installation guidance](../authentication/sql.md#installation-and-running-from-a-shell).

**Try a change:** change `params={"code": "demo"}` to `params={"code": "other"}` in the dependent query. All three patients should become unmatched; update the two synthetic measurement assertions to expect zero rows and `{"001", "002", "003"}`. Restore it, then try `chunk_size=1`: the measurement rows should remain the same while the batch report shows more completed batches.

Values are bound parameters, never inserted into SQL text. `query_df_for_keys` deduplicates complete input keys before batching and rejects missing keys. Empty input executes no dependent query. Returned observations are retained; they are not automatically joined or deduplicated.

Coverage requires ordered `result_key_columns`. An unmatched key means **no rows returned by this query**, not that a patient is absent from the database. A failed batch raises `SQLQueryError`; no partial result is returned as a successful extraction. Batches do not establish a global sort order.

### DSN alternative

Instead of separate `FHIR_DB_*` settings, configure:

```dotenv
FHIR_DB_DSN="host=database.example.org port=5432 dbname=demo_database user=replace-with-approved-role sslmode=verify-full"
PGPASSWORD=replace-with-approved-password
PGSSLROOTCERT=/path/to/approved-ca.pem
```

Keep the workflow above, replacing the entrypoint with:

```python
import os

if __name__ == "__main__":
    with FHIRSQLClient(dsn=os.environ["FHIR_DB_DSN"], connect_timeout=10) as client:
        annotated, visits, report = sql_workflow(client)
```

A DSN takes precedence over separate host/user/password settings; they are not merged into it. Remove stale `FHIR_DB_DSN` values before switching back. `PGPASSWORD` is a libpq fallback in this example. Never print a credential-bearing DSN. A short-lived database password/token does not gain HTTP OIDC renewal through this client.

### Existing `query_df_from` workflows

For an existing single-list SQL workflow, the following function is equivalent in intent, without the key-coverage report:

```python
def legacy_lookup(client, cohort):
    return client.query_df_from(
        cohort,
        """WITH demo(patient_id, value) AS (VALUES ('001', 10), ('002', 20))
        SELECT * FROM demo WHERE patient_id IN ({patient_ids})""",
        column_map={"patient_ids": "patient_id"}, parallel=False,
    )
```

SQL `column_map` maps **template name → DataFrame column**. Multiple template lists are independent: `patient_id IN (...) AND encounter_id IN (...)` does not preserve patient/encounter pairs. Prefer `query_df_for_keys` for new cohort workflows and tuple predicates for paired keys. REST's similarly named method instead performs row-wise FHIR searches; the two APIs are not interchangeable.

### About the commented MCP demonstration

The comments in `sql_cohort.py` show what you could ask an approved MCP-connected assistant and where its reviewed SQL would go. They are demonstration comments only: no MCP server, model, credentials or extra dependencies are needed. The script executes the supplied synthetic SQL through your configured PostgreSQL connection.

Fyron does not currently ship an MCP client, server or natural-language SQL method. The commented `draft_sql` call is illustrative, not an existing Fyron tool. A chosen external server must provide a drafting tool, or an assistant must draft from approved schema information. Review its SQL before using it; parameter binding does not validate clinical meaning or make arbitrary generated SQL safe. Keep real identifiers, credentials and internal schema details out of unapproved services.

## REST and SQL side by side

| Step | FHIR REST | PostgreSQL |
| --- | --- | --- |
| First DataFrame | `search_df` with explicit projections | `query_df` with bound parameters |
| Larger extraction | Date partitions and observed pagination | Reviewed filters, batching or documented SQL partitioning |
| Dependent queries | `search_df_from` / `query_df_from`, one search per input row | `query_df_for_keys`, distinct keys in bound batches |
| Completeness | Inspect execution and pagination reports; confirm server caps | Inspect batch completion and mapped-key coverage |
| Join back | Explicit mapping of resource references and validated joins | Explicit key mapping and validated joins |
| Files | Reviewed DICOM UIDs and approved document URLs | Same downloader inputs after explicit schema mapping |

Keep sequential execution while learning. For later parallel work, use supported shared authentication, guarded `main()` entrypoints, and the documented worker limits. Custom sessions have restrictions. Separate SQL worker connections do not share a transaction snapshot; use a stable source when reproducibility requires it.

Continue with [FHIR REST](../modules/fhir/rest.md), [PostgreSQL](../modules/fhir/sql.md), [DICOMweb downloads](../modules/dicom/downloader.md), [document downloads](../modules/documents/downloader.md), and [safe diagnostics](../diagnostics.md). Keep identifiers, URLs and detailed result tables in approved research storage, not shared logs.

**Next:** use reviewed download inputs with [DICOMweb](dicomweb.md) or [Documents](documents.md).

## Reliability in current source

For longer jobs, consider `FHIRSQLClient(statement_timeout=120, lock_timeout=10)`. Verified partition exports preserve unverified files; use explicit overwrite only after review. These options are included in Beta 5.
