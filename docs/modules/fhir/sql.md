# FHIR SQL

**Version scope:** Fyron 0.3.20b6 (Beta 6). Reporting, timeout, validation and naming additions described here require Beta 5 or newer.

## Find the right operation

Start with ordinary bound SQL returning a DataFrame. Use that table's keys for dependent queries, then merge or summarize explicitly in pandas. SQL schemas are site-specific; this page's runnable query examples use invented rows.

**[All parameters, defaults and accepted options](sql/parameters.md)** · [Connection setup](../../authentication/sql.md) · [Cohort walkthrough](../../onboarding/sql.md)

| What you want | Use | Important controls |
| --- | --- | --- |
| One SQL result as a table | `query_df` / `query_to_dataframe` | `params`, `rename` |
| Matching rows for a cohort | `query_df_for_keys` | ordered `key_columns`, `result_key_columns`, `chunk_size` |
| Preserve patient/encounter pairs | `query_df_for_keys` with tuple `IN` | one `{cohort_keys}` block; paired output mapping |
| Consume result chunks | `query_df_stream` | `chunksize`, statement/lock time limits |
| Split a time/grid extraction | `query_df_partitioned` | `frequency`, `window_days`, `param_grid`, error policy |
| Write resumable CSV parts | `export_query_partitioned` | verification records, filename templates, explicit overwrite |
| Maintain an existing list-based query | `query_df_from` | `column_map`, binding style and parameter budget |

### Example: first query, then dependent rows

Load your approved database `.env` explicitly. HTTP `Auth` is not used for PostgreSQL. This example needs a connection but does not create tables or read institutional data.

```python
from dotenv import load_dotenv
from fyron import FHIRSQLClient
from fyron.console import configure_logging

configure_logging("INFO", color=True)
load_dotenv(".env", override=False)
with FHIRSQLClient(
    statement_timeout=120, lock_timeout=10, log_queries=True,
) as client:
    cohort = client.query_df(
        "SELECT patient_id FROM (VALUES ('001'), ('002'), ('003')) AS p(patient_id)"
    )
    result = client.query_df_for_keys(
        df=cohort,
        sql="""
        WITH measurements(patient_id, code, value) AS (
            VALUES ('001', 'demo', 10), ('001', 'demo', 12), ('002', 'demo', 20)
        )
        SELECT patient_id, value FROM measurements
        WHERE patient_id IN ({cohort_keys}) AND code = %(code)s
        """,
        key_columns=["patient_id"], params={"code": "demo"},
        result_key_columns=["patient_id"], chunk_size=1000,
        parallel=False, return_report=True,
    )

measurements = result["data"]                  # Three rows, retaining repeated measurements
unmatched = result["report"]["unmatched_keys"]  # Synthetic patient 003
summary = result["report"]["summary"]
```

**What changes when you change an option?** `key_columns` binds complete input keys; `result_key_columns` enables coverage checks. `chunk_size` changes batch size, not clinical selection. `parallel=True` uses independent worker connections. `return_report=True` is supported by `query_df_for_keys`; it is not a general option on every SQL method.

For paired keys, use `(patient_id, encounter_id) IN ({cohort_keys})` with both columns in the same order. Legacy `column_map` lists are independent and do not preserve pairs. Time limits, file verification and explicit merges protect the workflow but do not choose clinical eligibility or provide a common transaction snapshot across workers.


For site-specific access setup, see [SQL authentication and connections](../../authentication/sql.md). Choose the method and permissions approved by your administrator.

Development update: see [Safe Network Diagnostics](../../diagnostics.md) for logging,
safe error text, batch outcome counts, and sensitive-result handling.

`query_df_partitioned` publishes a partition only after its stream finishes.
If a later chunk fails, all rows from that partition are discarded, including
with `continue_on_error=True`. Use `errors="record"` to retain an explicit error
row; successful partitions remain available. Partition metadata must not
collide with query result columns.

`fyron.fhir.sql` queries relational FHIR stores with explicit SQL and returns analysis-ready DataFrames. Use it when your institution exposes FHIR resources through Postgres or a warehouse layer and SQL joins are more appropriate than paginated REST calls.

## When To Use It

- cohort-scale extraction from FHIR warehouse tables,
- joins across patients, encounters, observations, conditions, and imaging metadata,
- reproducible SQL queries versioned with the analysis,
- chunked or parallel SQL jobs for large extracts.

Use [FHIR REST](rest.md) for live API access, server write-back, or smaller endpoint-driven workflows.

## Required Inputs

| Input | Needed for | Notes |
| --- | --- | --- |
| connection settings | all queries | `FHIR_DB_DSN` or host/db/user/password variables. |
| `sql` | all query methods | SQL statement with optional placeholders. |

## Optional Inputs

| Input | Use |
| --- | --- |
| `params` | safe parameterized queries |
| `rename` | normalize output column names |
| `chunksize` | stream large result sets |
| `column_map` | independent parameter lists from cohort columns |
| `parallel` | split repeated row-wise jobs |

## Minimal Example

```python
from fyron import FHIRSQLClient

client = FHIRSQLClient(dsn="postgresql://user:password@localhost/fhir")
patients = client.query_df(
    "select id as patient_id, birth_date from patient limit 100"
)
```

## Clinical Example

```python
labs = client.query_df(
    """
    select
      o.subject_id as patient_id,
      o.effective_datetime,
      o.value_quantity_value as hemoglobin,
      o.value_quantity_unit as unit
    from observation o
    where o.code_code = %(loinc)s
      and o.effective_datetime >= %(start)s
    """,
    params={"loinc": "718-7", "start": "2020-01-01"},
)
```

## Function Table

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `FHIRSQLClient(...)` | DSN or DB env vars | timeout, logging | client |
| `query(sql, ...)` | SQL | params | list of dict rows |
| `query_df(sql, ...)` | SQL | params, rename | DataFrame |
| `query_df_stream(sql, ...)` | SQL | params, rename, chunksize | iterator of DataFrames |
| `query_df_parallel(jobs, ...)` | jobs | workers, merge, unique keys | DataFrame |
| `query_df_from(df, ...)` | input table, SQL, column map | chunking, parallelism | DataFrame |
| `query_df_for_keys(df, sql, ...)` | table, SQL, ordered key columns | scalar filters, paired keys, batching, coverage report | DataFrame or data/report dictionary |
| `query_df_partitioned(sql, ...)` | SQL, start/end | time windows, parameter grid, de-duplication | DataFrame |
| `export_query_partitioned(sql, ...)` | SQL, output dir, start/end | resumable CSV parts, combine groups | manifest DataFrame |

## Query from cohort IDs

Use `query_df_for_keys` to filter PostgreSQL rows using a DataFrame of IDs.
It deduplicates complete keys before batching, preserves strings such as `"001"`,
and binds values as query parameters. SQL stays explicit and schema-specific.
The following examples use SQL `VALUES` tables containing only synthetic data;
set `FHIR_DB_DSN` to your own disposable local PostgreSQL database first.

```python
import pandas as pd
from fyron import FHIRSQLClient

cohort = pd.DataFrame({"patient_id": ["001", "002", "001", "003"]})
sql = """
WITH observations(patient_id, code, value) AS (
    VALUES ('001', 'demo', 10), ('001', 'demo', 12), ('002', 'demo', 20)
)
SELECT * FROM observations
WHERE patient_id IN ({cohort_keys}) AND code = %(code)s
"""
with FHIRSQLClient() as client:
    result = client.query_df_for_keys(
        cohort, sql,
        key_columns=["patient_id"],
        params={"code": "demo"},
        result_key_columns=["patient_id"],
        chunk_size=1000,
        return_report=True,
    )

observations = result["data"]
print(result["report"]["summary"])
print(result["report"]["rows"])
print(result["report"]["unmatched_keys"])
```

The default return is a DataFrame. `return_report=True` returns `data` and a
`report` dictionary containing `rows`, `summary`, and `unmatched_keys` DataFrames.
Batch rows record their ordinal, requested keys, returned rows, elapsed seconds,
and completion status. The summary counts input rows, distinct keys, removed
input duplicates, completed batches, and returned rows.

Coverage requires `result_key_columns` in the same order as `key_columns`.
Those columns must be present in every batch result, retain compatible key values,
and identify only requested keys. Without this mapping, coverage is unavailable;
an empty unmatched table must not be interpreted as full coverage.
Unmatched means **no rows returned by this query**, not that a patient is absent
from the database. Report key tables are sensitive research outputs.

## Preserve paired keys

Separate `patient_id IN (...)` and `encounter_id IN (...)` filters allow unintended
combinations. Use a tuple predicate to keep the DataFrame's pairs together:

```python
pairs = pd.DataFrame({"patient_id": ["001", "002"], "encounter_id": [1, 2]})
paired_sql = """
WITH visits(patient_id, encounter_id, value) AS (
    VALUES ('001', 1, 10), ('001', 2, 20), ('002', 1, 30), ('002', 2, 40)
)
SELECT * FROM visits
WHERE (patient_id, encounter_id) IN ({cohort_keys})
"""
with FHIRSQLClient() as client:
    visits = client.query_df_for_keys(
        pairs, paired_sql,
        key_columns=["patient_id", "encounter_id"],
        result_key_columns=["patient_id", "encounter_id"],
        chunk_size=1000,
    )
# Only ('001', 1) and ('002', 2) match, returning values 10 and 40.
```

Input column labels and selected key columns must be unique. Missing key values
are rejected before execution. Exactly one executable `{cohort_keys}` block is
required. Quoted strings, identifiers, comments, and dollar-quoted SQL bodies are
not template locations. Additional scalar filters use named `%(name)s` parameters;
parameter names beginning `_fyron_key_` are reserved. Use PostgreSQL's default
`standard_conforming_strings=on` with ordinary string literals; use `E'...'` for
backslash escapes.

## Batching, failures, and explicit joins

`chunk_size` is a maximum distinct-key count, reduced when necessary to fit a
45,000-parameter budget including scalar filters. Empty cohorts execute no query.
Rows returned by the database are retained, including repeated observations.
Batches are concatenated in submission order; use an explicit final sort if you
need a globally ordered result.

For independent batches, pass `parallel=True, max_workers=4`. Put parallel calls
inside `main()` and invoke it under `if __name__ == "__main__":` so spawned workers
can import the script safely. Workers use separate connections; parallel batches
do not share a transaction snapshot. Use a stable source snapshot for reproducible
extraction from a changing database. Every failed batch raises `SQLQueryError`;
partial data is never returned as a successful extraction.

Keep joins to your cohort explicit. For the single-ID example, aggregate repeated
observations deliberately before attaching one row per patient:

```python
summary = observations.groupby("patient_id", as_index=False).agg(
    mean_value=("value", "mean"), observation_count=("value", "size")
)
annotated = cohort.merge(summary, on="patient_id", how="left", validate="many_to_one")
```

`query_df_from` and `query_from_dataframe` remain available for existing
`column_map` workflows. Their template blocks expand to **independent value lists**,
not paired keys. They preserve legacy input duplication semantics. Their positional
bindings follow SQL occurrence order, including repeated blocks, and batch limits
account for repeated bindings. Prefer `query_df_for_keys` for cohort-key filtering.

## Partitioned SQL Queries

Use `query_df_partitioned` when one broad SQL statement is too expensive or likely to hit a warehouse timeout. The SQL must use named parameters. Fyron adds `start_ts` and `end_ts` for every time window, plus any values from `param_grid`.

```python
from fyron import FHIRSQLClient

SQL = """
select
  m0._id as request_id,
  lower(m0."authoredOn") as authored_on,
  %(med)s as matched_medication
from medicationrequest m0
where m0."authoredOn" && tstzrange(
    %(start_ts)s::timestamptz,
    %(end_ts)s::timestamptz,
    '[)'
)
and lower(m0._json::text) like %(med_pattern)s
"""

with FHIRSQLClient() as client:
    df = client.query_df_partitioned(
        SQL,
        start="2015-01-01",
        end="2025-01-01",
        frequency="MS",
        param_grid={"med": ["heparin", "xarelto"]},
        derived_params={"med_pattern": lambda p: f"%{p['med'].lower()}%"},
        chunksize=2000,
        deduplicate_by=["request_id", "matched_medication"],
    )
```

For very large extracts, prefer `export_query_partitioned`. It writes one CSV part per partition through a temporary file, skips completed parts on restart, and can combine parts into final grouped files.

```python
manifest = client.export_query_partitioned(
    SQL,
    output_dir="data/medication_requests_yearly",
    start="2015-01-01",
    end="2025-01-01",
    frequency="D",
    param_grid={"med": MEDS},
    derived_params={"med_pattern": lambda p: f"%{p['med'].lower()}%"},
    output_columns=[
        "patient_id",
        "encounter_id",
        "medication_text",
        "medication_code",
        "medication_display",
        "medication_system",
        "authored_on",
        "matched_medication",
    ],
    part_filename="{year}/{date}_{med}.csv",
    combine_by="year",
    combined_filename="medication_requests_{year}.csv",
    chunksize=2000,
    skip_existing=True,
)
```

Filter clinically relevant rows in SQL whenever possible. Partitioning makes extraction resumable and smaller, but post-query filtering still forces the database and network to move unnecessary rows.

## Common Pitfalls

- SQL table names and JSON paths vary by FHIR warehouse implementation.
- Prefer parameterized SQL over string formatting.
- Keep patient identifiers explicit and avoid accidental cross-patient joins.
- Store the SQL text with analysis outputs for auditability.
- If streaming fails before the first chunk, reduce the SQL partition size or add stronger SQL filters; `chunksize` only affects rows fetched after the database starts returning results.

## Related Modules

- [FHIR](../../fhir/index.html) for the overview.
- [FHIR REST](rest.md) for endpoint-driven queries and write-back.
- [Cohort Tables](../../cohort/index.html) for joining extracted features to outcomes.

## Query progress and helpful errors

Enable Fyron's shared console logger once, then opt into SQL activity messages:

```python
from fyron import FHIRSQLClient
from fyron.console import configure_logging
from fyron.fhir.sql import SQLQueryError

configure_logging("INFO", color=True)
# Load your approved connection settings before creating the client.
try:
    with FHIRSQLClient(log_queries=True) as client:
        frame = client.query_df("SELECT %(value)s::int AS value", params={"value": 1})
except SQLQueryError as error:
    # Fyron supplies controlled guidance, without remote database diagnostics.
    print(str(error))
```

`log_queries=True` logs connection/query starts and finishes at INFO, elapsed
seconds and returned row counts. Streaming adds chunk counts. It never prints
SQL, parameter values, credentials, database names or returned records. Failed
operations are logged at ERROR even when activity logging is disabled.

Colors use the same console settings as FHIR REST: supported terminals receive
colored levels; `NO_COLOR` disables ANSI output. Use
`configure_logging("INFO", json=True)` for structured scheduler logs. No logger
configuration or banner is applied automatically by the SQL client.

Errors distinguish authentication, permissions, syntax, missing schema objects,
cancelled/timed-out statements, connection failures, aborted transactions,
transaction conflicts and rejected values when PostgreSQL supplies a recognized
error code. Pandas-wrapped database errors retain this classification. Unknown
failures receive general troubleshooting guidance; remote error text stays private.
Connection failures without a server error code cannot reliably distinguish TLS,
network and authentication causes. Check those settings with your administrator.

Streaming results yielded before a failure are incomplete. A stream closed early
is logged as incomplete rather than successful. Batch failures raise without a
successful partial extraction. Fyron does not automatically retry queries or roll
back transactions: an aborted transaction requires an explicit rollback on the
owned connection or a new client before retrying. Do not retry writes blindly.

## Verified exports and database time limits

`export_query_partitioned` skips an existing partition only when its completion
record matches the SQL, bound parameters, partition metadata, selected columns
and rename mapping, and its file digest still matches. A nonempty CSV alone is
not proof of completion. The record stores fingerprints and file checksums,
not SQL or bound values. These records describe a previous extraction; they do
not prove that a live database has remained unchanged since that extraction.

An unverified or changed partition is preserved and raises an error. Use
`overwrite=True` for intentional replacement. The existing explicit
`skip_existing=False` behavior also permits replacement. Set
`write_completion_record=False` to omit new completion JSON, accepting that new
outputs cannot be verified for later skips. Interrupted partitions are staged
beside their destination and never replace an earlier file. Partition filename
collisions are rejected before querying.

```python
from fyron import FHIRSQLClient
from fyron.console import configure_logging

configure_logging("INFO", color=True)
with FHIRSQLClient(
    statement_timeout=120,  # Seconds per statement; None retains server settings
    lock_timeout=10,       # Seconds waiting for locks
    log_queries=True,
) as client:
    table = client.query_df("SELECT %(value)s::int AS value", params={"value": 1})
```

Both limits apply to newly owned parent and worker connections. A cancelled
statement can leave its transaction aborted; open a new client or explicitly
roll back your connection before retrying. Fyron does not retry SQL or reconnect
and replay it automatically. DataFrame chunking is not a guarantee of bounded
server/client memory or a shared snapshot across worker connections.

Combined exports also use verified records and preserve CSV identifier text,
including leading zeros and literal `NA` values. If `continue_on_error=True`, a
combined file can contain only the completed partitions; inspect the returned
manifest for errors before using it as a complete extract.
