# FHIR SQL: complete parameter reference

[Back to the workflow guide](../sql.md)

Use this page when you know the operation and need every argument, its actual Python default and its interactions. Signatures and parameter coverage are generated from the current source; descriptions explain operational choices.

**Version scope:** Fyron 0.3.20b6 (Beta 6). The reporting, deadline, naming and validation options below require Beta 5 or newer; they are not available in previously published Beta 4 packages.

## Reading the tables

- **Required** means the Python signature has no default. A default of `None` can still require environment configuration or a value from the resource.
- **Keyword only** arguments must be passed by name. Boolean options accept Python `True` / `False`; `None` is a separate inherit/unset choice where documented.
- Use the workflow guide for setup, authentication, return schemas and safe restarts. FHIR `params` and SQL schemas are site-specific; this page lists Fyron arguments, not every parameter a remote service might support.
- These clients support `with ... as client:` and `close()`; they close owned resources and keep borrowed HTTP sessions open.

## Function index

- [FHIRSQLClient](#constructor)
- [close](#close)
- [query](#query)
- [query_to_dataframe](#query-to-dataframe)
- [query_df](#query-df)
- [query_df_partitioned](#query-df-partitioned)
- [query_df_stream](#query-df-stream)
- [export_query_partitioned](#export-query-partitioned)
- [query_df_parallel](#query-df-parallel)
- [query_df_for_keys](#query-df-for-keys)
- [query_from_dataframe](#query-from-dataframe)
- [query_df_from](#query-df-from)

## Constructor

`FHIRSQLClient`

Signature reference (use the workflow guide for runnable calls):

```python
def FHIRSQLClient(
    dsn=None,
    host=None,
    port=None,
    dbname=None,
    user=None,
    password=None,
    sslmode=None,
    connect_timeout=10,
    log_queries=False,
    *,
    statement_timeout=None,
    lock_timeout=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `dsn` | `Optional[str]` | `None` | Optional PostgreSQL DSN; None can read `FHIR_DB_DSN`. A supplied/effective DSN takes precedence over separate host/user/password settings; they are not merged. |
| `host` | `Optional[str]` | `None` | Database host; None reads `FHIR_DB_HOST` when no DSN is used. |
| `port` | `Optional[int]` | `None` | Database port; None can read `FHIR_DB_PORT`, otherwise connection defaults to 5432 without a DSN. |
| `dbname` | `Optional[str]` | `None` | Database name; None reads `FHIR_DB_NAME` when no DSN is used. |
| `user` | `Optional[str]` | `None` | Database role; None reads `FHIR_DB_USER` when no DSN is used. |
| `password` | `Optional[str]` | `None` | Database password/token; None reads `FHIR_DB_PASSWORD` when no DSN is used. HTTP Auth does not renew database credentials. |
| `sslmode` | `Optional[str]` | `None` | PostgreSQL/libpq modes: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`. None reads `FHIR_DB_SSLMODE` or retains connection defaults. Use the site-approved TLS policy, normally `verify-full` plus its CA; do not downgrade verification to bypass errors. |
| `connect_timeout` | `int` | `10` | Database connection timeout in seconds. Separate from statement_timeout and lock_timeout; forwarded to psycopg/libpq. |
| `log_queries` | `bool` | `False` | Enable timed SQL connection/query events and row/chunk counts at INFO; SQL text and parameters are never logged. |
| `statement_timeout` (keyword only) | `Optional[float]` | `None` | Optional positive seconds per SQL statement on parent and worker connections. None retains server settings. No automatic retry or rollback follows cancellation. |
| `lock_timeout` (keyword only) | `Optional[float]` | `None` | Optional positive seconds waiting for SQL locks. None retains server settings. |

## close

`close`

Signature reference (use the workflow guide for runnable calls):

```python
def close(
):
    ...
```

No arguments. Closes owned resources; call once work has finished.

## query

`query`

Signature reference (use the workflow guide for runnable calls):

```python
def query(
    sql,
    params=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `params` | `Optional[Dict[str, Any] \| Sequence[Any]]` | `None` | Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved. |

## query to dataframe

`query_to_dataframe`

Signature reference (use the workflow guide for runnable calls):

```python
def query_to_dataframe(
    sql,
    params=None,
    rename=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `params` | `Optional[Dict[str, Any] \| Sequence[Any]]` | `None` | Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved. |
| `rename` | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |

## query df

`query_df`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df(
    sql,
    params=None,
    rename=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `params` | `Optional[Dict[str, Any] \| Sequence[Any]]` | `None` | Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved. |
| `rename` | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |

## query df partitioned

`query_df_partitioned`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df_partitioned(
    sql,
    *,
    start,
    end,
    params=None,
    frequency='YS',
    window_days=None,
    param_grid=None,
    derived_params=None,
    chunksize=10000,
    rename=None,
    include_partition_columns=True,
    deduplicate_by=None,
    continue_on_error=False,
    errors='raise',
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `start` (keyword only) | `Union[str, pd.Timestamp]` | **Required** | Inclusive first boundary, supplied as a date/date-time string or pandas Timestamp. Use consistent timezone semantics. |
| `end` (keyword only) | `Union[str, pd.Timestamp]` | **Required** | Exclusive final boundary. Must be later than start; do not describe this as an inclusive end date. |
| `params` (keyword only) | `Optional[Dict[str, Any]]` | `None` | Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved. |
| `frequency` (keyword only) | `str` | `'YS'` | Pandas date frequency such as `"MS"` (monthly) or `"YS"` (yearly). Ignored when `window_days` is supplied. |
| `window_days` (keyword only) | `Optional[int]` | `None` | Optional positive fixed window width in days; overrides the calendar frequency. |
| `param_grid` (keyword only) | `Optional[Mapping[str, Sequence[Any]]]` | `None` | Optional mapping of parameter names to nonempty value sequences. Expands a Cartesian grid across time windows; start_ts/end_ts are reserved. |
| `derived_params` (keyword only) | `Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]]` | `None` | Optional mapping of parameter names to callables receiving the partition parameter dictionary. Used to derive approved query values; start_ts/end_ts remain reserved. |
| `chunksize` (keyword only) | `int` | `10000` | Positive number of rows per DataFrame/CSV chunk. It does not guarantee server-side cursor streaming or limit the query’s total result size. |
| `rename` (keyword only) | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |
| `include_partition_columns` (keyword only) | `bool` | `True` | Attach explicit window/grid metadata to returned rows. Metadata names must not collide with result columns. |
| `deduplicate_by` (keyword only) | `Optional[Union[str, Sequence[str]]]` | `None` | A result-column name or ordered list of names used for explicit duplicate removal. None retains repeated rows. Choose resource IDs deliberately; do not deduplicate clinical observations by patient alone. |
| `continue_on_error` (keyword only) | `bool` | `False` | False raises on failed partitions. True allows successful partitions to remain available while failures are recorded. Inspect the manifest/error rows before calling the extract complete. |
| `errors` (keyword only) | `str` | `'raise'` | `"raise"` or `"record"`. Record mode appends explicit error rows and partition metadata; earlier chunks from a failed partition are discarded. |

## query df stream

`query_df_stream`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df_stream(
    sql,
    params=None,
    rename=None,
    chunksize=10000,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `params` | `Optional[Dict[str, Any] \| Sequence[Any]]` | `None` | Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved. |
| `rename` | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |
| `chunksize` | `int` | `10000` | Positive number of rows per DataFrame/CSV chunk. It does not guarantee server-side cursor streaming or limit the query’s total result size. |

## export query partitioned

`export_query_partitioned`

Signature reference (use the workflow guide for runnable calls):

```python
def export_query_partitioned(
    sql,
    output_dir,
    *,
    start,
    end,
    params=None,
    frequency='YS',
    window_days=None,
    param_grid=None,
    derived_params=None,
    output_columns=None,
    part_filename='{date}.csv',
    combine_by=None,
    combined_filename='combined_{value}.csv',
    chunksize=10000,
    skip_existing=True,
    continue_on_error=False,
    rename=None,
    overwrite=False,
    write_completion_record=True,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `output_dir` | `Union[str, Path]` | **Required** | Destination directory. DICOM creates study/series folders beneath it; documents use flat or per-document layout according to `flat_output`. |
| `start` (keyword only) | `Union[str, pd.Timestamp]` | **Required** | Inclusive first boundary, supplied as a date/date-time string or pandas Timestamp. Use consistent timezone semantics. |
| `end` (keyword only) | `Union[str, pd.Timestamp]` | **Required** | Exclusive final boundary. Must be later than start; do not describe this as an inclusive end date. |
| `params` (keyword only) | `Optional[Dict[str, Any]]` | `None` | Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved. |
| `frequency` (keyword only) | `str` | `'YS'` | Pandas date frequency such as `"MS"` (monthly) or `"YS"` (yearly). Ignored when `window_days` is supplied. |
| `window_days` (keyword only) | `Optional[int]` | `None` | Optional positive fixed window width in days; overrides the calendar frequency. |
| `param_grid` (keyword only) | `Optional[Mapping[str, Sequence[Any]]]` | `None` | Optional mapping of parameter names to nonempty value sequences. Expands a Cartesian grid across time windows; start_ts/end_ts are reserved. |
| `derived_params` (keyword only) | `Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]]` | `None` | Optional mapping of parameter names to callables receiving the partition parameter dictionary. Used to derive approved query values; start_ts/end_ts remain reserved. |
| `output_columns` (keyword only) | `Optional[Sequence[str]]` | `None` | Optional ordered columns to retain in exported CSVs. Missing result columns raise. |
| `part_filename` (keyword only) | `str` | `'{date}.csv'` | Relative CSV filename template inside `_parts`, e.g. `"{year}/{date}.csv"`. Templates must not escape the output directory or resolve to colliding partitions. |
| `combine_by` (keyword only) | `Optional[str]` | `None` | Optional partition metadata group such as `"year"` or a grid parameter. None leaves parts separate. Combined output can be partial when errors were allowed. |
| `combined_filename` (keyword only) | `str` | `'combined_{value}.csv'` | Relative combined-output filename template, e.g. `"combined_{value}.csv"`. Verified files are protected and identifier text is preserved when combining CSVs. |
| `chunksize` (keyword only) | `int` | `10000` | Positive number of rows per DataFrame/CSV chunk. It does not guarantee server-side cursor streaming or limit the query’s total result size. |
| `skip_existing` (keyword only) | `bool` | `True` | True skips only outputs verified by matching completion records. False explicitly permits replacement. Disabling JSON does not make existing files automatically trusted. |
| `continue_on_error` (keyword only) | `bool` | `False` | False raises on failed partitions. True allows successful partitions to remain available while failures are recorded. Inspect the manifest/error rows before calling the extract complete. |
| `rename` (keyword only) | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |
| `overwrite` (keyword only) | `bool` | `False` | Explicitly replace existing output after review. For SQL exports, `skip_existing=False` also permits replacement for compatibility. |
| `write_completion_record` (keyword only) | `bool` | `True` | Write new hidden JSON completion records for verified restarts. False omits new records; it neither deletes existing JSON nor disables token caching. |

## query df parallel

`query_df_parallel`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df_parallel(
    jobs,
    rename=None,
    max_workers=None,
    merge='concat',
    unique_on=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `jobs` | `Sequence[Tuple[str, Optional[Dict[str, Any] \| Sequence[Any]]]]` | **Required** | Sequence of `(sql, params)` pairs for parallel SQL execution. Each worker owns its connection; a failed job raises. |
| `rename` | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |
| `max_workers` | `Optional[int]` | `None` | Optional positive SQL process count. None uses the pool default except `query_df_for_keys`, which defaults to four parallel workers. |
| `merge` | `str` | `'concat'` | `"concat"` retains every returned observation; `"drop_duplicates"` explicitly removes duplicates using unique_on or all columns. |
| `unique_on` | `Optional[Sequence[str]]` | `None` | Optional result-column list used only with merge="drop_duplicates". Avoid patient-only deduplication when repeated observations matter. |

## query df for keys

`query_df_for_keys`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df_for_keys(
    df,
    sql,
    *,
    key_columns,
    params=None,
    result_key_columns=None,
    chunk_size=1000,
    parallel=False,
    max_workers=None,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `key_columns` (keyword only) | `Sequence[str]` | **Required** | Nonempty ordered input key-column list. One column filters IDs; multiple columns bind complete tuples. Complete keys are globally deduplicated before batching. |
| `params` (keyword only) | `Optional[Mapping[str, Any]]` | `None` | Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved. |
| `result_key_columns` (keyword only) | `Optional[Sequence[str]]` | `None` | Optional ordered output key columns corresponding to key_columns. Enables matched/unmatched distinct-key coverage; missing or unexpected result keys raise. |
| `chunk_size` (keyword only) | `int` | `1000` | Positive maximum distinct keys per batch. The method reduces it to fit its conservative 45,000-bound-value budget, counting scalar filters and all composite-key values. |
| `parallel` (keyword only) | `bool` | `False` | Execute SQL batches in separate owned connections. False is easier to inspect. Worker connections do not share a transaction snapshot. |
| `max_workers` (keyword only) | `Optional[int]` | `None` | Optional positive SQL process count. None uses the pool default except `query_df_for_keys`, which defaults to four parallel workers. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## query from dataframe

`query_from_dataframe`

Signature reference (use the workflow guide for runnable calls):

```python
def query_from_dataframe(
    df,
    sql,
    column_map,
    rename=None,
    param_limit=50000,
    chunk_size=None,
    parallel=False,
    max_workers=None,
    merge='concat',
    unique_on=None,
    param_style='positional',
    param_safety_factor=0.9,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `column_map` | `Dict[str, str]` | **Required** | Legacy SQL template block → input column, e.g. `{"ids": "patient_id"}` for `{ids}`. Separate lists are independent and do not preserve patient/encounter pairs; use query_df_for_keys for tuples. |
| `rename` | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |
| `param_limit` | `int` | `50000` | Positive SQL bind-parameter budget; constrained by PostgreSQL’s 65,535 maximum and the safety factor. Repeated positional placeholders count more than once. |
| `chunk_size` | `Optional[int]` | `None` | Maximum input rows/keys per bound SQL batch. Positive integer when supplied; the actual size may be reduced by the parameter budget. |
| `parallel` | `bool` | `False` | Execute SQL batches in separate owned connections. False is easier to inspect. Worker connections do not share a transaction snapshot. |
| `max_workers` | `Optional[int]` | `None` | Optional positive SQL process count. None uses the pool default except `query_df_for_keys`, which defaults to four parallel workers. |
| `merge` | `str` | `'concat'` | `"concat"` retains every returned observation; `"drop_duplicates"` explicitly removes duplicates using unique_on or all columns. |
| `unique_on` | `Optional[Sequence[str]]` | `None` | Optional result-column list used only with merge="drop_duplicates". Avoid patient-only deduplication when repeated observations matter. |
| `param_style` | `str` | `'positional'` | `"positional"` expands legacy blocks to `%s`; `"named"` uses named bound placeholders. Both bind values rather than interpolate them. |
| `param_safety_factor` | `float` | `0.9` | Finite fraction in `(0, 1]` of param_limit used for sizing SQL batches. |

## query df from

`query_df_from`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df_from(
    df,
    sql,
    column_map,
    rename=None,
    param_limit=50000,
    chunk_size=None,
    parallel=False,
    max_workers=None,
    merge='concat',
    unique_on=None,
    param_style='positional',
    param_safety_factor=0.9,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `sql` | `str` | **Required** | Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings. |
| `column_map` | `Dict[str, str]` | **Required** | Legacy SQL template block → input column, e.g. `{"ids": "patient_id"}` for `{ids}`. Separate lists are independent and do not preserve patient/encounter pairs; use query_df_for_keys for tuples. |
| `rename` | `Optional[Dict[str, str]]` | `None` | Optional mapping of existing result column names to desired names; does not change the query or its predicates. |
| `param_limit` | `int` | `50000` | Positive SQL bind-parameter budget; constrained by PostgreSQL’s 65,535 maximum and the safety factor. Repeated positional placeholders count more than once. |
| `chunk_size` | `Optional[int]` | `None` | Maximum input rows/keys per bound SQL batch. Positive integer when supplied; the actual size may be reduced by the parameter budget. |
| `parallel` | `bool` | `False` | Execute SQL batches in separate owned connections. False is easier to inspect. Worker connections do not share a transaction snapshot. |
| `max_workers` | `Optional[int]` | `None` | Optional positive SQL process count. None uses the pool default except `query_df_for_keys`, which defaults to four parallel workers. |
| `merge` | `str` | `'concat'` | `"concat"` retains every returned observation; `"drop_duplicates"` explicitly removes duplicates using unique_on or all columns. |
| `unique_on` | `Optional[Sequence[str]]` | `None` | Optional result-column list used only with merge="drop_duplicates". Avoid patient-only deduplication when repeated observations matter. |
| `param_style` | `str` | `'positional'` | `"positional"` expands legacy blocks to `%s`; `"named"` uses named bound placeholders. Both bind values rather than interpolate them. |
| `param_safety_factor` | `float` | `0.9` | Finite fraction in `(0, 1]` of param_limit used for sizing SQL batches. |

## Return formats and limits

`query` returns a list of row dictionaries; `query_df`/`query_to_dataframe` and batch queries return DataFrames; `query_df_stream` yields chunks; exports return a partition manifest. Only `query_df_for_keys` supports `return_report=True`, including `rows`, `summary` and `unmatched_keys`. Coverage requires explicit result_key_columns; unmatched means this query returned no row.

**Sensitive outputs:** result paths, identifiers, URLs and detailed reports belong in approved research storage. Progress logs use controlled labels and counts.

Return to the [workflow guide](../sql.md) for worked examples.
