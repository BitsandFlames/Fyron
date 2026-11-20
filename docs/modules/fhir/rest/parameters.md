# FHIR REST: complete parameter reference

[Back to the workflow guide](../rest.md)

Use this page when you know the operation and need every argument, its actual Python default and its interactions. Signatures and parameter coverage are generated from the current source; descriptions explain operational choices.

**Version scope:** Fyron 0.3.20b5 (Beta 5). The reporting, deadline, naming and validation options below require Beta 5 or newer; they are not available in previously published Beta 4 packages.

## Reading the tables

- **Required** means the Python signature has no default. A default of `None` can still require environment configuration or a value from the resource.
- **Keyword only** arguments must be passed by name. Boolean options accept Python `True` / `False`; `None` is a separate inherit/unset choice where documented.
- Use the workflow guide for setup, authentication, return schemas and safe restarts. FHIR `params` and SQL schemas are site-specific; this page lists Fyron arguments, not every parameter a remote service might support.
- These clients support `with ... as client:` and `close()`; they close owned resources and keep borrowed HTTP sessions open.

## Function index

- [FHIRRestClient](#constructor)
- [close](#close)
- [fetch_bundles](#fetch-bundles)
- [fetch_bundles_parallel](#fetch-bundles-parallel)
- [fetch_bundles_partitioned](#fetch-bundles-partitioned)
- [bundles_to_dataframe](#bundles-to-dataframe)
- [query_to_dataframe_partitioned](#query-to-dataframe-partitioned)
- [query_to_dataframe](#query-to-dataframe)
- [query_from_dataframe](#query-from-dataframe)
- [query_df](#query-df)
- [search_df](#search-df)
- [query_df_partitioned](#query-df-partitioned)
- [search_df_partitioned](#search-df-partitioned)
- [query_df_from](#query-df-from)
- [search_df_from](#search-df-from)
- [bundles_to_df](#bundles-to-df)
- [create_resource](#create-resource)
- [update_resource](#update-resource)
- [submit_bundle](#submit-bundle)

## Constructor

`FHIRRestClient`

Signature reference (use the workflow guide for runnable calls):

```python
def FHIRRestClient(
    base_url=None,
    auth_url=None,
    auth=None,
    num_processes=4,
    request_timeout=30,
    request_params=None,
    bearer_token=None,
    log_requests=False,
    log_request_urls=False,
    extra_headers=None,
    retries=None,
    return_fhir_obj=False,
    token_auth_method=None,
    cache_ttl_seconds=300,
    cache_max_entries=1000,
    *,
    worker_auth_timeout=120,
    parallel_job_timeout=300,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `base_url` | `Optional[str]` | `None` | Service base URL. `None` falls back to `FHIR_BASE_URL`. Documents use it only to resolve relative URLs; absolute URLs work without it. |
| `auth_url` | `Optional[str]` | `None` | Login/token endpoint for Fyron’s existing environment username/password mechanism. Use shared Auth for OIDC issuer discovery, device flow or service accounts; this argument is not a universal OAuth selector. |
| `auth` | `Optional[Union[Auth, requests.Session]]` | `None` | An existing Fyron `Auth` or `requests.Session`. Borrowed sessions stay open and retain their configuration. Use a service-approved authentication method. |
| `num_processes` | `int` | `4` | Worker process count. Use `1` while learning. FHIR uses it for parallel fetch/conversion; DICOM uses it for DataFrame downloads with supported worker authentication. Guard spawned script entrypoints. |
| `request_timeout` | `int` | `30` | Positive seconds for each network connect/read wait. This is not a whole-extraction deadline. DICOM also accepts `None` to retain unbounded request waits. |
| `request_params` | `Optional[Dict[str, Any]]` | `None` | Default FHIR query-parameter dictionary merged into every request; per-query values override matching defaults. |
| `bearer_token` | `Optional[str]` | `None` | Optional static access token; otherwise FHIR_TOKEN may apply. A static token does not renew. Shared Auth/session authentication takes precedence when already configured. |
| `log_requests` | `bool` | `False` | Enable controlled request timing/status events with the shared Fyron logger. Never prints query values, tokens, URLs or response bodies. |
| `log_request_urls` | `bool` | `False` | Compatibility option for controlled activity events. Actual URLs are never printed. |
| `extra_headers` | `Optional[Dict[str, str]]` | `None` | Additional HTTP headers applied per request, leaving a borrowed session unchanged. Do not log or publish credential-bearing values. |
| `retries` | `Optional[Retry]` | `None` | An optional `urllib3.util.retry.Retry` GET policy. `None` selects Fyron’s bounded default, including 429/502/503/504 and Retry-After. Existing retry-capable caller adapters retain their own policy. No automatic SQL or write retries. |
| `return_fhir_obj` | `bool` | `False` | Wrap fetched resources/bundles as FHIRObj rather than plain dictionaries. Normal DataFrame processing still uses the conversion helpers. |
| `token_auth_method` | `Optional[str]` | `None` | For Fyron’s existing username/password token mechanism: `"basic"` or `"post"`. This is not a universal OAuth password grant. |
| `cache_ttl_seconds` | `int` | `300` | In-memory GET response lifetime in seconds. Zero disables caching; a cached response is not proof the source has remained unchanged. |
| `cache_max_entries` | `int` | `1000` | Maximum entries in the in-memory response cache; zero disables it. No response cache is written to disk. |
| `worker_auth_timeout` (keyword only) | `float` | `120` | Positive finite seconds a worker may wait for parent-coordinated authentication. |
| `parallel_job_timeout` (keyword only) | `Optional[float]` | `300` | Positive finite worker execution deadline in seconds, excluding queue wait; `None` disables it. FHIR and DICOM have different constructor defaults, shown in the table. |

## close

`close`

Signature reference (use the workflow guide for runnable calls):

```python
def close(
):
    ...
```

No arguments. Closes owned resources; call once work has finished.

## fetch bundles

`fetch_bundles`

Signature reference (use the workflow guide for runnable calls):

```python
def fetch_bundles(
    resource_type,
    params=None,
    max_pages=-1,
    show_progress=True,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |

## fetch bundles parallel

`fetch_bundles_parallel`

Signature reference (use the workflow guide for runnable calls):

```python
def fetch_bundles_parallel(
    resource_type,
    param_list,
    max_pages=-1,
    show_progress=True,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `param_list` | `Sequence[Dict[str, Any]]` | **Required** | Sequence of separate FHIR query dictionaries; each becomes an independent fetch job. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |

## fetch bundles partitioned

`fetch_bundles_partitioned`

Signature reference (use the workflow guide for runnable calls):

```python
def fetch_bundles_partitioned(
    resource_type,
    partition_param,
    start,
    end,
    params=None,
    frequency='YS',
    window_days=None,
    max_pages_per_partition=-1,
    show_progress=True,
    parallel_fetch=False,
    auto_sort=True,
    sort='_id',
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `partition_param` | `str` | **Required** | Actual server-supported FHIR date search parameter, e.g. `"recorded-date"`, `"date"` or `"_lastUpdated"`. It describes the chosen resource date, not necessarily clinical onset. |
| `start` | `Union[str, pd.Timestamp]` | **Required** | Inclusive first boundary, supplied as a date/date-time string or pandas Timestamp. Use consistent timezone semantics. |
| `end` | `Union[str, pd.Timestamp]` | **Required** | Exclusive final boundary. Must be later than start; do not describe this as an inclusive end date. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `frequency` | `str` | `'YS'` | Pandas date frequency such as `"MS"` (monthly) or `"YS"` (yearly). Ignored when `window_days` is supplied. |
| `window_days` | `Optional[int]` | `None` | Optional positive fixed window width in days; overrides the calendar frequency. |
| `max_pages_per_partition` | `int` | `-1` | Page limit within each window: positive integer, `-1` for all available pages, `0` for no request. Not a limit across all windows. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |
| `parallel_fetch` | `bool` | `False` | Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion. |
| `auto_sort` | `bool` | `True` | Add the selected sort unless an explicit `_sort` is already supplied in params. Requires server support; sorting does not prove completeness. |
| `sort` | `str` | `'_id'` | FHIR `_sort` expression used by auto_sort, normally `"_id"`; select a server-supported stable sort. |

## bundles to dataframe

`bundles_to_dataframe`

Signature reference (use the workflow guide for runnable calls):

```python
def bundles_to_dataframe(
    bundles,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    per_bundle_metadata=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `bundles` | `Iterable[Dict[str, Any] \| FHIRObj]` | **Required** | Iterable of already retrieved Bundle dictionaries/FHIRObj objects to convert. Conversion materializes the iterable; it does not fetch more pages. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `per_bundle_metadata` | `Optional[List[Dict[str, Any]]]` | `None` | Advanced: list of dictionaries aligned one-to-one with bundles. Values are attached to every output row; conflicting output names raise. |

## query to dataframe partitioned

`query_to_dataframe_partitioned`

Signature reference (use the workflow guide for runnable calls):

```python
def query_to_dataframe_partitioned(
    resource_type,
    partition_param,
    start,
    end,
    params=None,
    frequency='YS',
    window_days=None,
    max_pages_per_partition=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_fetch=False,
    include_partition_columns=True,
    deduplicate_by=None,
    auto_sort=True,
    sort='_id',
    show_progress=True,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `partition_param` | `str` | **Required** | Actual server-supported FHIR date search parameter, e.g. `"recorded-date"`, `"date"` or `"_lastUpdated"`. It describes the chosen resource date, not necessarily clinical onset. |
| `start` | `Union[str, pd.Timestamp]` | **Required** | Inclusive first boundary, supplied as a date/date-time string or pandas Timestamp. Use consistent timezone semantics. |
| `end` | `Union[str, pd.Timestamp]` | **Required** | Exclusive final boundary. Must be later than start; do not describe this as an inclusive end date. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `frequency` | `str` | `'YS'` | Pandas date frequency such as `"MS"` (monthly) or `"YS"` (yearly). Ignored when `window_days` is supplied. |
| `window_days` | `Optional[int]` | `None` | Optional positive fixed window width in days; overrides the calendar frequency. |
| `max_pages_per_partition` | `int` | `-1` | Page limit within each window: positive integer, `-1` for all available pages, `0` for no request. Not a limit across all windows. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_fetch` | `bool` | `False` | Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion. |
| `include_partition_columns` | `bool` | `True` | Attach explicit window/grid metadata to returned rows. Metadata names must not collide with result columns. |
| `deduplicate_by` | `Optional[Union[str, Sequence[str]]]` | `None` | A result-column name or ordered list of names used for explicit duplicate removal. None retains repeated rows. Choose resource IDs deliberately; do not deduplicate clinical observations by patient alone. |
| `auto_sort` | `bool` | `True` | Add the selected sort unless an explicit `_sort` is already supplied in params. Requires server support; sorting does not prove completeness. |
| `sort` | `str` | `'_id'` | FHIR `_sort` expression used by auto_sort, normally `"_id"`; select a server-supported stable sort. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## query to dataframe

`query_to_dataframe`

Signature reference (use the workflow guide for runnable calls):

```python
def query_to_dataframe(
    resource_type,
    params=None,
    max_pages=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_params=None,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_params` | `Optional[Sequence[Dict[str, Any]]]` | `None` | Optional sequence of query dictionaries for independent parallel FHIR searches. None performs one search with params. Inspect job-level completeness. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## query from dataframe

`query_from_dataframe`

Signature reference (use the workflow guide for runnable calls):

```python
def query_from_dataframe(
    df,
    resource_type,
    column_map,
    params=None,
    max_pages=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_fetch=False,
    param_prefix=None,
    include_column_map_columns=False,
    show_progress=True,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `column_map` | `Dict[str, str]` | **Required** | FHIR search parameter → input DataFrame column, e.g. `{"subject": "patient_id"}`. Each input row creates a query; null, blank or empty-list keys are rejected. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_fetch` | `bool` | `False` | Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion. |
| `param_prefix` | `Optional[Dict[str, str]]` | `None` | Optional mapping from FHIR search parameter to a prefix, e.g. `{"subject": "Patient/"}`. Original input values are retained when metadata is requested. |
| `include_column_map_columns` | `bool` | `False` | Copy original mapped input columns into each returned row. Works with parallel fetch/custom processing; collisions with output columns raise. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## query df

`query_df`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df(
    resource_type,
    params=None,
    max_pages=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_params=None,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_params` | `Optional[Sequence[Dict[str, Any]]]` | `None` | Optional sequence of query dictionaries for independent parallel FHIR searches. None performs one search with params. Inspect job-level completeness. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## search df

`search_df`

Signature reference (use the workflow guide for runnable calls):

```python
def search_df(
    resource_type,
    params=None,
    max_pages=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_params=None,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_params` | `Optional[Sequence[Dict[str, Any]]]` | `None` | Optional sequence of query dictionaries for independent parallel FHIR searches. None performs one search with params. Inspect job-level completeness. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## query df partitioned

`query_df_partitioned`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df_partitioned(
    resource_type,
    partition_param,
    start,
    end,
    params=None,
    frequency='YS',
    window_days=None,
    max_pages_per_partition=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_fetch=False,
    include_partition_columns=True,
    deduplicate_by=None,
    auto_sort=True,
    sort='_id',
    show_progress=True,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `partition_param` | `str` | **Required** | Actual server-supported FHIR date search parameter, e.g. `"recorded-date"`, `"date"` or `"_lastUpdated"`. It describes the chosen resource date, not necessarily clinical onset. |
| `start` | `Union[str, pd.Timestamp]` | **Required** | Inclusive first boundary, supplied as a date/date-time string or pandas Timestamp. Use consistent timezone semantics. |
| `end` | `Union[str, pd.Timestamp]` | **Required** | Exclusive final boundary. Must be later than start; do not describe this as an inclusive end date. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `frequency` | `str` | `'YS'` | Pandas date frequency such as `"MS"` (monthly) or `"YS"` (yearly). Ignored when `window_days` is supplied. |
| `window_days` | `Optional[int]` | `None` | Optional positive fixed window width in days; overrides the calendar frequency. |
| `max_pages_per_partition` | `int` | `-1` | Page limit within each window: positive integer, `-1` for all available pages, `0` for no request. Not a limit across all windows. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_fetch` | `bool` | `False` | Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion. |
| `include_partition_columns` | `bool` | `True` | Attach explicit window/grid metadata to returned rows. Metadata names must not collide with result columns. |
| `deduplicate_by` | `Optional[Union[str, Sequence[str]]]` | `None` | A result-column name or ordered list of names used for explicit duplicate removal. None retains repeated rows. Choose resource IDs deliberately; do not deduplicate clinical observations by patient alone. |
| `auto_sort` | `bool` | `True` | Add the selected sort unless an explicit `_sort` is already supplied in params. Requires server support; sorting does not prove completeness. |
| `sort` | `str` | `'_id'` | FHIR `_sort` expression used by auto_sort, normally `"_id"`; select a server-supported stable sort. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## search df partitioned

`search_df_partitioned`

Signature reference (use the workflow guide for runnable calls):

```python
def search_df_partitioned(
    resource_type,
    partition_param,
    start,
    end,
    params=None,
    frequency='YS',
    window_days=None,
    max_pages_per_partition=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_fetch=False,
    include_partition_columns=True,
    deduplicate_by=None,
    auto_sort=True,
    sort='_id',
    show_progress=True,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `partition_param` | `str` | **Required** | Actual server-supported FHIR date search parameter, e.g. `"recorded-date"`, `"date"` or `"_lastUpdated"`. It describes the chosen resource date, not necessarily clinical onset. |
| `start` | `Union[str, pd.Timestamp]` | **Required** | Inclusive first boundary, supplied as a date/date-time string or pandas Timestamp. Use consistent timezone semantics. |
| `end` | `Union[str, pd.Timestamp]` | **Required** | Exclusive final boundary. Must be later than start; do not describe this as an inclusive end date. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `frequency` | `str` | `'YS'` | Pandas date frequency such as `"MS"` (monthly) or `"YS"` (yearly). Ignored when `window_days` is supplied. |
| `window_days` | `Optional[int]` | `None` | Optional positive fixed window width in days; overrides the calendar frequency. |
| `max_pages_per_partition` | `int` | `-1` | Page limit within each window: positive integer, `-1` for all available pages, `0` for no request. Not a limit across all windows. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_fetch` | `bool` | `False` | Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion. |
| `include_partition_columns` | `bool` | `True` | Attach explicit window/grid metadata to returned rows. Metadata names must not collide with result columns. |
| `deduplicate_by` | `Optional[Union[str, Sequence[str]]]` | `None` | A result-column name or ordered list of names used for explicit duplicate removal. None retains repeated rows. Choose resource IDs deliberately; do not deduplicate clinical observations by patient alone. |
| `auto_sort` | `bool` | `True` | Add the selected sort unless an explicit `_sort` is already supplied in params. Requires server support; sorting does not prove completeness. |
| `sort` | `str` | `'_id'` | FHIR `_sort` expression used by auto_sort, normally `"_id"`; select a server-supported stable sort. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## query df from

`query_df_from`

Signature reference (use the workflow guide for runnable calls):

```python
def query_df_from(
    df,
    resource_type,
    column_map,
    params=None,
    max_pages=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_fetch=False,
    param_prefix=None,
    include_column_map_columns=False,
    show_progress=True,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `column_map` | `Dict[str, str]` | **Required** | FHIR search parameter → input DataFrame column, e.g. `{"subject": "patient_id"}`. Each input row creates a query; null, blank or empty-list keys are rejected. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_fetch` | `bool` | `False` | Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion. |
| `param_prefix` | `Optional[Dict[str, str]]` | `None` | Optional mapping from FHIR search parameter to a prefix, e.g. `{"subject": "Patient/"}`. Original input values are retained when metadata is requested. |
| `include_column_map_columns` | `bool` | `False` | Copy original mapped input columns into each returned row. Works with parallel fetch/custom processing; collisions with output columns raise. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## search df from

`search_df_from`

Signature reference (use the workflow guide for runnable calls):

```python
def search_df_from(
    df,
    resource_type,
    column_map,
    params=None,
    max_pages=-1,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
    parallel_fetch=False,
    param_prefix=None,
    include_column_map_columns=False,
    show_progress=True,
    *,
    return_report=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `resource_type` | `str` | **Required** | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |
| `column_map` | `Dict[str, str]` | **Required** | FHIR search parameter → input DataFrame column, e.g. `{"subject": "patient_id"}`. Each input row creates a query; null, blank or empty-list keys are rejected. |
| `params` | `Optional[Dict[str, Any]]` | `None` | FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters. |
| `max_pages` | `int` | `-1` | Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |
| `parallel_fetch` | `bool` | `False` | Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion. |
| `param_prefix` | `Optional[Dict[str, str]]` | `None` | Optional mapping from FHIR search parameter to a prefix, e.g. `{"subject": "Patient/"}`. Original input values are retained when metadata is requested. |
| `include_column_map_columns` | `bool` | `False` | Copy original mapped input columns into each returned row. Works with parallel fetch/custom processing; collisions with output columns raise. |
| `show_progress` | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |

## bundles to df

`bundles_to_df`

Signature reference (use the workflow guide for runnable calls):

```python
def bundles_to_df(
    bundles,
    process_function=None,
    fhir_paths=None,
    mode='flatten',
    use_multiprocessing=True,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `bundles` | `Iterable[Dict[str, Any] \| FHIRObj]` | **Required** | Iterable of already retrieved Bundle dictionaries/FHIRObj objects to convert. Conversion materializes the iterable; it does not fetch more pages. |
| `process_function` | `Optional[ProcessFunc]` | `None` | Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries. |
| `fhir_paths` | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function. |
| `mode` | `str` | `'flatten'` | `"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise. |
| `use_multiprocessing` | `bool` | `True` | Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint. |

## create resource

`create_resource`

Signature reference (use the workflow guide for runnable calls):

```python
def create_resource(
    resource,
    resource_type=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource` | `Dict[str, Any]` | **Required** | A validated FHIR R4 resource dictionary. It must agree with an explicitly supplied resource type. |
| `resource_type` | `Optional[str]` | `None` | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |

## update resource

`update_resource`

Signature reference (use the workflow guide for runnable calls):

```python
def update_resource(
    resource,
    resource_id=None,
    resource_type=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `resource` | `Dict[str, Any]` | **Required** | A validated FHIR R4 resource dictionary. It must agree with an explicitly supplied resource type. |
| `resource_id` | `Optional[str]` | `None` | Logical FHIR resource ID for update. None uses the ID in the resource; an update requires an ID. |
| `resource_type` | `Optional[str]` | `None` | FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server. |

## submit bundle

`submit_bundle`

Signature reference (use the workflow guide for runnable calls):

```python
def submit_bundle(
    bundle,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `bundle` | `Dict[str, Any]` | **Required** | Validated FHIR transaction Bundle to submit to the server base URL. Collection bundles are not accepted for submission. |

## Return formats and limits

Fetch methods yield bundles. DataFrame methods return a DataFrame or a dictionary of tables according to conversion output; `return_report=True` wraps data with `report.rows` and `report.summary`. A failure raises. Write methods return FHIRWriteResult metadata. An exhausted page sequence is not proof against hidden server caps.

**Sensitive outputs:** result paths, identifiers, URLs and detailed reports belong in approved research storage. Progress logs use controlled labels and counts.

Return to the [workflow guide](../rest.md) for worked examples.
