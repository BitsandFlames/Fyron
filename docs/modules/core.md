# Core I/O

Development update: see [Safe Network Diagnostics](../diagnostics.md) for logging,
safe error text, batch outcome counts, and sensitive-result handling.

## S3 Reliability (Development)

`S3Storage.exists(key)` returns `False` only for an explicit not-found response.
Access denial, network failures, and other service errors raise safe exceptions;
they no longer masquerade as absent objects. Callers must handle these failures
instead of treating them as permission to create or replace an object.

`S3Storage.list()` follows continuation tokens until the listing is complete.
`max_keys=None` returns all matching objects, `max_keys=0` returns an empty list
without a request, and a positive integer caps the total returned items **after
suffix filtering**, across all pages. Negative values and non-integers are rejected.
Malformed or repeated continuation tokens raise instead of returning a partial
listing as complete. Large unbounded listings are materialized in memory.

`fyron.core` is the data-boundary layer: environment variables, local tables, JSON sidecars, file summaries, Teable review tables, finished research cohort write-back, and optional S3 object storage. Use it whenever data enters or leaves a reproducible clinical workflow.

## When To Use Core Helpers

- load credentials from `.env` before creating FHIR, DICOM, Teable, or S3 clients,
- write analysis-ready tables with explicit file boundaries,
- store JSON sidecars such as mappings, manifests, and validation reports,
- read manually curated Teable tables into Python,
- write locked research cohorts back to Teable for review and audit,
- read/write cohort tables from S3 or S3-compatible storage.

## Imports

```python
from fyron import (
    load_env,
    read_table,
    write_table,
    read_json,
    write_json,
    summarize_table,
    describe_file,
)
from fyron.core import DataIO, TeableClient
from fyron.core.s3 import S3Storage
```

## Environment Loading

```python
from fyron import load_env

load_env(".env", override=False)
```

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `load_env(path=None, ...)` | none | `override=False`, `warn_if_missing=True` | loaded path or `None` |

Typical variables include `FHIR_BASE_URL`, `DICOM_WEB_URL`, `TEABLE_TOKEN`, `S3_BUCKET`, and AWS credentials.

## Local Table I/O

Use `read_table` and `write_table` when a pipeline may receive CSV, TSV, Excel, JSON, or JSONL files.

```python
from fyron import read_table, write_table

cohort = read_table("data/reviewed_cohort.csv")
write_table(cohort, "outputs/analysis_ready/cohort.jsonl")
```

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `read_table(path, ...)` | path | `file_format`, pandas kwargs | DataFrame |
| `write_table(df, path, ...)` | DataFrame, path | `file_format`, `create_parent=True`, `index=False`, pandas kwargs | output `Path` |
| `read_csv(path, **kwargs)` | path | pandas kwargs | DataFrame |
| `write_csv(df, path, **kwargs)` | DataFrame, path | pandas kwargs | `None` |
| `read_excel(path, **kwargs)` | path | pandas kwargs | DataFrame |
| `write_excel(df, path, **kwargs)` | DataFrame, path | pandas kwargs | `None` |

Supported table formats: `.csv`, `.tsv`, `.xlsx`, `.xls`, `.json`, `.jsonl`.

## JSON Sidecars

```python
from fyron import read_json, write_json

mapping = {"code_col": "loinc", "value_col": "value"}
write_json(mapping, "outputs/fhir/observation_mapping.json")
loaded = read_json("outputs/fhir/observation_mapping.json")
```

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `read_json(path, **kwargs)` | path | JSON load kwargs | Python object |
| `write_json(payload, path, ...)` | payload, path | `indent=2`, `create_parent=True` | output `Path` |

## File And Table Summaries

```python
from fyron import describe_file, summarize_table

summary = summarize_table(cohort, name="analysis_cohort")
file_info = describe_file("outputs/analysis_ready/cohort.csv")
```

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `ensure_parent_dir(path)` | path | none | `Path` |
| `summarize_table(df, ...)` | DataFrame | `name` | dict |
| `describe_file(path)` | path | none | dict |

`summarize_table` reports row count, column count, column names, missing cells, duplicate rows, and memory use.

## DataIO Object

`DataIO` exposes the same helpers as static methods for projects that prefer passing an I/O object.

```python
from fyron.core import DataIO

io = DataIO()
df = io.read_table("features.csv")
io.write_json({"rows": len(df)}, "outputs/features.summary.json")
```

## Teable Review Tables And Research Cohorts

Use Teable when curated review tables or locked cohorts need to move between Python and a collaborative workspace.

```python
from fyron.core import TeableClient

teable = TeableClient(base_url="https://app.teable.ai", token="YOUR_TOKEN")
reviewed = teable.read_cohort(
    "tbl_reviewed",
    id_col="patient_id",
    required_columns=["patient_id", "outcome", "follow_up_days"],
)
```

Write a finished research cohort:

```python
result = teable.write_research_cohort(
    "tbl_final_cohort",
    cohort,
    mode="append",
    cohort_name="BOA survival cohort",
    version="v1.0",
    id_col="patient_id",
    metadata={"analysis": "body composition survival model"},
)
```

| Method | Required | Optional | Returns |
| --- | --- | --- | --- |
| `read_table(table_id, ...)` | table ID | view, projection, max records | DataFrame |
| `read_cohort(table_id, ...)` | table ID | ID column, required columns, view, max records | validated DataFrame |
| `write_dataframe(table_id, df, ...)` | table ID, DataFrame | typecast, chunks | record IDs |
| `overwrite_table(table_id, df, ...)` | table ID, DataFrame | batch sizes, typecast | record IDs |
| `write_research_cohort(table_id, df, ...)` | table ID, DataFrame | mode, name, version, metadata, ID column | audit dict |
| `create_research_cohort_table(base_id, name, ...)` | base ID, name | DataFrame, fields, metadata | table dict |
| `summarize_teable_table(table_id, ...)` | table ID | view, projection, max records | summary dict |

## S3 And S3-Compatible Storage

Install the optional extra:

```bash
uv add "fyron[s3]"
```

```python
from fyron.core.s3 import S3Storage

s3 = S3Storage(
    bucket="clinical-research",
    prefix="projects/boa-survival",
    endpoint_url=None,  # set for MinIO or other S3-compatible systems
)

s3.write_table("cohorts/final.csv", cohort)
cohort_from_s3 = s3.read_table("cohorts/final.csv")
s3.write_json("manifests/run.json", {"rows": len(cohort)})
```

| Method | Required | Optional | Returns |
| --- | --- | --- | --- |
| `S3Storage(...)` | bucket or `S3_BUCKET` | prefix, endpoint, region, credentials | storage client |
| `exists(key)` | key | none | bool |
| `list(prefix=None, ...)` | none | suffix, max keys | object list |
| `read_bytes(key)` / `write_bytes(key, data)` | key | content type | bytes / S3 URI |
| `read_json(key)` / `write_json(key, payload)` | key | indent | object / S3 URI |
| `read_table(key, ...)` / `write_table(key, df, ...)` | key | format, pandas kwargs | DataFrame / S3 URI |
| `download_file(key, local_path)` | key, local path | parent creation | local `Path` |
| `upload_file(local_path, key=None)` | local path | key, content type | S3 URI |

Convenience functions:

```python
from fyron.core.s3 import read_s3_table, write_s3_table

df = read_s3_table("s3://clinical-research/projects/cohort.csv")
write_s3_table(df, "s3://clinical-research/projects/cohort_clean.csv")
```

## Practical Tips

- Keep `.env` files out of git and call `load_env()` at notebook or CLI startup.
- Use `write_table(..., index=False)` unless the index is clinically meaningful.
- Store JSON mappings and validation reports beside generated FHIR bundles.
- Use `read_cohort` for Teable review tables so missing columns and duplicate IDs fail early.
- Use S3 prefixes as project boundaries, e.g. `projects/boa-survival/v1`.
- Parquet is intentionally not part of Core I/O v1.
