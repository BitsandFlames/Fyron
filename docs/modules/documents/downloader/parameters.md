# Document downloader: complete parameter reference

[Back to the workflow guide](../downloader.md)

Use this page when you know the operation and need every argument, its actual Python default and its interactions. Signatures and parameter coverage are generated from the current source; descriptions explain operational choices.

**Version scope:** Fyron 0.3.20b5 (Beta 5). The reporting, deadline, naming and validation options below require Beta 5 or newer; they are not available in previously published Beta 4 packages.

## Reading the tables

- **Required** means the Python signature has no default. A default of `None` can still require environment configuration or a value from the resource.
- **Keyword only** arguments must be passed by name. Boolean options accept Python `True` / `False`; `None` is a separate inherit/unset choice where documented.
- Use the workflow guide for setup, authentication, return schemas and safe restarts. FHIR `params` and SQL schemas are site-specific; this page lists Fyron arguments, not every parameter a remote service might support.
- These clients support `with ... as client:` and `close()`; they close owned resources and keep borrowed HTTP sessions open.

## Function index

- [DocumentDownloader](#constructor)
- [close](#close)
- [download_id](#download-id)
- [download_url](#download-url)
- [download_urls](#download-urls)
- [download_from_dataframe](#download-from-dataframe)
- [download_from_df](#download-from-df)

## Constructor

`DocumentDownloader`

Signature reference (use the workflow guide for runnable calls):

```python
def DocumentDownloader(
    auth=None,
    base_url=None,
    output_dir='documents_out',
    timeout=30,
    skip_existing=True,
    log_downloads=False,
    max_workers=4,
    retries=None,
    save_mode='auto',
    force_extension=None,
    basic_auth=None,
    *,
    require_pdf=False,
    allow_redirects=True,
    write_completion_record=True,
    flat_output=False,
    expected_content_types=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `auth` | `Optional[Union[Auth, requests.Session]]` | `None` | An existing Fyron `Auth` or `requests.Session`. Borrowed sessions stay open and retain their configuration. Use a service-approved authentication method. |
| `base_url` | `Optional[str]` | `None` | Service base URL. `None` falls back to `FHIR_BASE_URL`. Documents use it only to resolve relative URLs; absolute URLs work without it. |
| `output_dir` | `Union[str, pathlib.Path]` | `'documents_out'` | Destination directory. DICOM creates study/series folders beneath it; documents use flat or per-document layout according to `flat_output`. |
| `timeout` | `int` | `30` | Positive finite network connect/read timeout in seconds. Python defaults to 30; document CLI defaults to 90. Not a whole-batch deadline. |
| `skip_existing` | `bool` | `True` | True skips only outputs verified by matching completion records. False explicitly permits replacement. Disabling JSON does not make existing files automatically trusted. |
| `log_downloads` | `bool` | `False` | Enable controlled download timing, outcomes and counts. Configure console colors or JSON logging once in the application. |
| `max_workers` | `int` | `4` | Thread count for list/DataFrame downloads. The scheduler submits at most twice the worker count at a time; results remain in input order. |
| `retries` | `Optional[Retry]` | `None` | An optional `urllib3.util.retry.Retry` GET policy. `None` selects Fyron’s bounded default, including 429/502/503/504 and Retry-After. Existing retry-capable caller adapters retain their own policy. No automatic SQL or write retries. |
| `save_mode` | `str` | `'auto'` | Naming choices: `"auto"` uses response MIME extension when available; `"txt"` or `"pdf"` appends that extension. Other values retain the URL-derived name. This changes naming, not conversion or validation. |
| `force_extension` | `Optional[str]` | `None` | Optional extension, with or without a leading dot, appended to the automatic base name. Takes precedence over save_mode. It does not convert the content. |
| `basic_auth` | `Optional[Tuple[str, str]]` | `None` | Optional `(username, password)` tuple. Do not combine with shared `auth` or conflicting explicit credentials. |
| `require_pdf` (keyword only) | `bool` | `False` | Require HTTP 200, PDF media type and a streamed `%PDF-` prefix. Does not validate full PDF syntax or clinical correctness. |
| `allow_redirects` (keyword only) | `bool` | `True` | True follows guarded same-origin redirects; False rejects redirects. Never authorizes sending tokens to arbitrary attachment hosts. |
| `write_completion_record` (keyword only) | `bool` | `True` | Write new hidden JSON completion records for verified restarts. False omits new records; it neither deletes existing JSON nor disables token caching. |
| `flat_output` (keyword only) | `bool` | `False` | True writes custom-ID/hash-named files directly in output_dir with absolute result paths. False uses a document subfolder. Explicit output_path overrides both. |
| `expected_content_types` (keyword only) | `Optional[Sequence[str]]` | `None` | Optional nonempty sequence of exact MIME types, e.g. `["text/plain", "application/pdf"]`. Comparison ignores response charset/case. No wildcards. A PDF requirement must remain compatible. |

## close

`close`

Signature reference (use the workflow guide for runnable calls):

```python
def close(
):
    ...
```

No arguments. Closes owned resources; call once work has finished.

## download id

`download_id`

Signature reference (use the workflow guide for runnable calls):

```python
def download_id(
    url,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `url` | `str` | **Required** | Approved HTTP(S) document URL, or a relative URL with a configured base URL. Embedded credentials and whitespace are rejected. |

## download url

`download_url`

Signature reference (use the workflow guide for runnable calls):

```python
def download_url(
    url,
    *,
    output_path=None,
    document_id=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `url` | `str` | **Required** | Approved HTTP(S) document URL, or a relative URL with a configured base URL. Embedded credentials and whitespace are rejected. |
| `output_path` (keyword only) | `Optional[Union[str, pathlib.Path]]` | `None` | Optional exact destination file for one document. Overrides automatic directory/name choices. Existing-file protection still applies. |
| `document_id` (keyword only) | `Optional[Union[str, int]]` | `None` | Optional custom string/integer ID for one document. Replaces the default hash in automatic names; explicit `output_path` still takes precedence. |

## download urls

`download_urls`

Signature reference (use the workflow guide for runnable calls):

```python
def download_urls(
    urls,
    results_csv=None,
    *,
    return_report=False,
    show_progress=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `urls` | `Iterable[str]` | **Required** | Iterable of approved document URLs. Use a DataFrame method when you also need per-document custom IDs. |
| `results_csv` | `Optional[Union[str, pathlib.Path]]` | `None` | Optional sensitive CSV of outcome rows and actual paths. Written atomically; keep it separate from downloaded files and client metadata. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |
| `show_progress` (keyword only) | `bool` | `False` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |

## download from dataframe

`download_from_dataframe`

Signature reference (use the workflow guide for runnable calls):

```python
def download_from_dataframe(
    df,
    url_col='document_url',
    results_csv=None,
    *,
    id_col=None,
    return_report=False,
    show_progress=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `url_col` | `str` | `'document_url'` | Input column containing document URLs. |
| `results_csv` | `Optional[Union[str, pathlib.Path]]` | `None` | Optional sensitive CSV of outcome rows and actual paths. Written atomically; keep it separate from downloaded files and client metadata. |
| `id_col` (keyword only) | `Optional[str]` | `None` | Optional column of unique filename-safe document IDs. Strings preserve leading zeros; integers are accepted, but floats, booleans, missing values and case-insensitive duplicates are rejected. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |
| `show_progress` (keyword only) | `bool` | `False` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |

## download from df

`download_from_df`

Signature reference (use the workflow guide for runnable calls):

```python
def download_from_df(
    df,
    url_col='document_url',
    results_csv=None,
    *,
    id_col=None,
    return_report=False,
    show_progress=False,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `url_col` | `str` | `'document_url'` | Input column containing document URLs. |
| `results_csv` | `Optional[Union[str, pathlib.Path]]` | `None` | Optional sensitive CSV of outcome rows and actual paths. Written atomically; keep it separate from downloaded files and client metadata. |
| `id_col` (keyword only) | `Optional[str]` | `None` | Optional column of unique filename-safe document IDs. Strings preserve leading zeros; integers are accepted, but floats, booleans, missing values and case-insensitive duplicates are rejected. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |
| `show_progress` (keyword only) | `bool` | `False` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |

## Return formats and limits

`download_url` returns DocumentResult; batch methods return a DataFrame, or data with `report.rows` / `report.summary` when requested. Batch results retain input order. The internal download_id remains the source URL hash even with custom filenames. PDF/MIME checks do not establish clinical validity.

**Sensitive outputs:** result paths, identifiers, URLs and detailed reports belong in approved research storage. Progress logs use controlled labels and counts.

Return to the [workflow guide](../downloader.md) for worked examples.
