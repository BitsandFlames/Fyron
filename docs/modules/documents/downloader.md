# DocumentDownloader

For site-specific access setup, see [Document authentication](../../authentication/documents.md). Choose the method and permissions approved by your administrator.

Download PDF and plain-text documents from individual URLs or cohort tables.
Return to the [Documents overview](../documents.md), or see
[Safe Network Diagnostics](../../diagnostics.md) for controlled logging and sensitive results.

The document downloader follows redirects only within the same scheme, host, and port when redirects are enabled. Cross-origin redirects, HTTPS downgrades, and URLs containing user credentials are blocked before forwarding request bodies or custom authentication headers. Configure the approved final endpoint directly when a service redirects elsewhere. This guard is also installed on supplied sessions, while preserving existing response hooks.

## Supported Formats

| Download | Python | CLI | Behavior |
| --- | --- | --- | --- |
| Plain text (`text/plain`) | Default `require_pdf=False` | Omit `--pdf` | Save the response bytes; automatic naming uses `.txt` when appropriate. |
| PDF (`application/pdf`) | `require_pdf=True` for strict checks | Add `--pdf` for strict checks | Require HTTP 200, the PDF media type, and a `%PDF-` signature. |
| Mixed text and PDF batch | Default `require_pdf=False` | Omit `--pdf` | Save each response using its content type for automatic filename extensions. |

PDFs also download in the default general mode. Strict PDF mode rejects plain text
and other response types. General mode is not a MIME-type allowlist: inspect the
returned `content_type` and `error` fields, especially if an endpoint might return
a sign-in page. Files are saved as bytes without text decoding or format conversion.
An explicit `output_path`/`--output` keeps the exact filename you choose.

### Plain Text

```python
from fyron import Auth, DocumentDownloader

with Auth(
    auth_type="device_code",
    auth_url="https://identity.example.org/realms/research",
    client_id="research-documents-cli",
    scope="openid user/DocumentReference.rs",
) as auth:
    with DocumentDownloader(auth=auth, timeout=90, allow_redirects=False) as loader:
        result = loader.download_url(
            "https://documents.example.org/reports/synthetic-001/text",
            output_path="documents_out/report.txt",
        )
        if result.error:
            raise RuntimeError(result.error)
```

```bash
fyron document-download \
  --url 'https://documents.example.org/reports/synthetic-001/text' \
  --output documents_out/report.txt \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs'
```

### Mixed Text and PDF Batches

Create a CSV with a `document_url` column containing the approved document URLs:

```bash
fyron document-download \
  --csv documents.csv --output-dir documents_out \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs' \
  --results-csv document-results.csv
```

Omit `--pdf` for mixed batches. In Python, use `loader.download_urls(urls)` or
`loader.download_from_df(documents_df)` with the default `require_pdf=False`.
All examples use fictional endpoints; configure your provider's registered client
and approved scopes before running them.

## Safe Restarts

Downloads are written into temporary staging folders. Fyron checks an available
unencoded `Content-Length`, then publishes the file and writes a completion
record with its size and SHA-256 hash. Interrupted transfers do not replace final
files, and staging folders are cleaned up during normal exception handling.

`skip_existing=True` now requires a valid completion record. It also recognizes
the resolved filename when the response changes the file extension. An existing
file without a valid record is preserved and reported as a conflict, not silently
skipped or overwritten. Review/back up legacy or partial outputs before using
`skip_existing=False` for an intentional replacement. Abrupt process termination
may leave hidden staging folders; these are never treated as completed outputs.

Keep hidden completion records with the downloads. Hash verification reads the
local file and may add noticeable I/O for large documents. It verifies local
integrity, not the clinical correctness or remote completeness of a document.

### Save Documents Without JSON Completion Records

Set `write_completion_record=False` to save documents without creating a hidden
`.fyron-complete-*.json` file for each download:

```python
with DocumentDownloader(
    auth=auth,
    output_dir="documents_out",
    timeout=90,
    require_pdf=True,
    allow_redirects=False,
    write_completion_record=False,
) as downloader:
    results = downloader.download_from_df(
        documents,
        url_col="document_url",
        results_csv="document-results.csv",
    )
```

Here `auth` is your configured `Auth` object and `documents` is the DataFrame
loaded from your CSV. For the CLI, add `--no-completion-record` to either the
single-document or CSV batch command. The optional results CSV is still written.

PDF validation and staged publication remain enabled. Without a completion
record, a subsequent run cannot verify and skip the saved file: it reports an
existing-file conflict. Intentional replacement requires `skip_existing=False`
in Python or `--overwrite` on the CLI. Existing valid records may still permit
verified skips; opting out does not remove records for files that are skipped.
When a file is replaced, its matching old completion record is removed.

`fyron.documents` downloads clinical documents, PDFs, reports, text files, or other URL-addressable artifacts. It supports individual URLs, URL lists, and DataFrame-driven batch downloads.

Document downloads are often the bridge between structured cohorts and narrative evidence. Store the returned metadata with your cohort so each local file can be traced back to the source URL, row identifier, and download status. Avoid mixing document retrieval with LLM extraction in the same step; first collect the files, then analyze them.

## Document Workflow

1. Resolve or construct document URLs from your source system.
2. Download documents with deterministic output paths.
3. Store hashes, status, and local paths.
4. Review failed downloads separately from content extraction.
5. Pass local paths to downstream parsing or LLM workflows only after retrieval is complete.

## Import

```python
from fyron import DocumentDownloader
```

## Browser-approved OIDC downloads

Use the same `Auth` object as FHIR and DICOMweb. Fyron discovers the device and
token endpoints from the OIDC issuer, displays browser approval instructions,
and renews access tokens during downloads. Thread workers share authentication
and token refresh. No institutional endpoints or client identifiers are built in.

```python
from fyron import Auth, DocumentDownloader

with Auth(
    auth_type="device_code",
    auth_url="https://identity.example.org/realms/research",
    client_id="research-documents-cli",
    scope="openid user/DocumentReference.rs",  # Use your provider's approved scopes.
) as auth:
    with DocumentDownloader(
        auth=auth,
        output_dir="documents_out",
        timeout=90,
        require_pdf=True,
        allow_redirects=False,
    ) as loader:
        result = loader.download_url(
            "https://documents.example.org/reports/synthetic-001/pdf",
            output_path="documents_out/report.pdf",
        )
        if result.error:
            raise RuntimeError(result.error)
```

These endpoints are fictional. The server must support device authorization and
authorize the registered client and requested scopes. To bypass discovery, pass
both `device_authorization_endpoint` and `token_endpoint` to `Auth`. For service
accounts, pass an `Auth.client_credentials(...)` instance instead.

`require_pdf=True` sends `Accept: application/pdf` and requires HTTP 200, the PDF
media type, and the first five bytes (`%PDF-`). It rejects HTML sign-in pages and
partial-content responses. These checks do not parse the full PDF or establish
clinical correctness. General documents remain supported with the default
`require_pdf=False`; `save_mode="pdf"` and `force_extension` only affect filenames.

The Python timeout still defaults to 30 seconds; 90 seconds is useful for servers
that generate PDFs on demand. Requests timeouts limit connection/read waits, not
the total elapsed streaming duration. Set `allow_redirects=False` to reject
redirects. When enabled, redirects remain restricted to the same origin.

An exact `output_path` is used without appending an extension. Completion records
bind the source URL, destination filename, and validation policy. A general-download
record cannot prove strict PDF validation. Keep records beside their files.
Changing policy or finding an unverified existing file requires reviewing the
output before allowing replacement with `skip_existing=False`.

## Command line

```bash
fyron document-download \
  --url 'https://documents.example.org/reports/synthetic-001/pdf' \
  --output documents_out/report.pdf --pdf \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs' \
  --results-csv document-results.csv
```

### CSV Batch Downloads

Save the document URLs in a local file named `documents.csv`, with one URL per
row under the `document_url` header:

```csv
document_url
https://documents.example.org/reports/synthetic-001/pdf
https://documents.example.org/reports/synthetic-002/pdf
```

Download every document listed in that column using browser-approved OIDC login:

```bash
fyron document-download \
  --csv documents.csv \
  --url-col document_url \
  --output-dir documents_out \
  --pdf \
  --timeout 90 \
  --workers 4 \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs' \
  --results-csv document-results.csv
```

This reads the local CSV and downloads its listed documents; it does not download
the CSV itself. `document_url` is the default column name, so `--url-col` is
optional here. Use `--output-dir` for batches; `--output` is for a single URL.
Documents are saved in deterministic URL-hash folders beneath `documents_out`,
and `document-results.csv` records their local paths and outcomes. Repeat the
same command to skip verified completed downloads and retry failed transfers.
For plain-text or mixed-format endpoints, omit `--pdf`.

Every row must contain a nonempty HTTP(S) URL, or a relative path when
`--base-url` is supplied. Batch results may arrive in completion order; match
them by URL/download ID. The endpoints and client identifier above are fictional.

### Save All Documents in One Folder

Available in Fyron 0.3.17 and newer, together with the JSON-record opt-out.

Use `flat_output=True` in Python or `--flat-output` on the CLI to save every
document directly inside `output_dir`, without per-document subfolders. Filenames
use the full SHA-256 URL hash plus the content-type extension, for example
`<url-hash>.pdf`. Different URLs with the same basename stay separate. The
returned DataFrame and results CSV contain the absolute file path in `path`.
An explicit single-file `output_path` / `--output` still takes precedence.

```python
import pandas as pd
from fyron import Auth, DocumentDownloader

documents = pd.read_csv("documents.csv", dtype={"document_url": "string"})

with Auth(
    auth_type="device_code",
    auth_url="https://identity.example.org/realms/research",
    client_id="research-documents-cli",
    scope="openid user/DocumentReference.rs",
) as auth:
    with DocumentDownloader(
        auth=auth,
        output_dir="documents_out",
        flat_output=True,
        write_completion_record=False,
        require_pdf=True,
        allow_redirects=False,
        timeout=90,
        max_workers=4,
    ) as downloader:
        results = downloader.download_from_df(
            documents,
            url_col="document_url",
            results_csv="document-results.csv",
        )

# Inspect outcomes before using the downloaded files.
successful_files = results.loc[results["error"].isna(), ["url", "path"]]
failed_downloads = results.loc[results["error"].notna()]
```

The equivalent command reads the same `documents.csv`:

```bash
fyron document-download \
  --csv documents.csv \
  --url-col document_url \
  --output-dir documents_out \
  --flat-output \
  --no-completion-record \
  --pdf \
  --timeout 90 \
  --workers 4 \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs' \
  --results-csv document-results.csv
```

Both examples use fictional endpoints and leave only the document files in the
output folder. The separate results CSV maps each source URL to its absolute
local `path`, with `error` and `skipped` outcome fields. Results can arrive in
completion order, so use `url` or `download_id` rather than row position to join
them back to your input table. For mixed PDF/plain-text batches, set
`require_pdf=False` or omit `--pdf`.

Omit `write_completion_record=False` / `--no-completion-record` to retain
verified restart support. Without completion records, existing files remain
protected and require explicit overwrite on a rerun. The results CSV should have
a different path from every downloaded document.

### Custom Document IDs and Cached Login

Choose exact document names using a CSV/DataFrame ID column. For example,
`documents.csv` can contain:

```csv
document_url,document_id
https://documents.example.org/reports/synthetic-001/pdf,00123
https://documents.example.org/reports/synthetic-002/pdf,00456
```

This complete example saves `documents_out/00123.pdf` and
`documents_out/00456.pdf`, without per-document JSON files. Authentication tokens
are cached separately, outside the document directory:

```python
import pandas as pd
from fyron import Auth, DocumentDownloader

documents = pd.read_csv("documents.csv", dtype=str, keep_default_na=False)

with Auth(
    auth_type="device_code",
    auth_url="https://identity.example.org/realms/research",
    client_id="research-documents-cli",
    scope="openid user/DocumentReference.rs",
    token_cache="~/.cache/fyron/document-tokens.json",
) as auth:
    with DocumentDownloader(
        auth=auth,
        output_dir="documents_out",
        flat_output=True,
        write_completion_record=False,
        require_pdf=True,
        allow_redirects=False,
        timeout=90,
    ) as downloader:
        results = downloader.download_from_df(
            documents,
            id_col="document_id",
            url_col="document_url",
            results_csv="document-results.csv",
        )

successful_files = results.loc[results["error"].isna(), ["document_id", "path"]]
failed_downloads = results.loc[results["error"].notna()]
```

The equivalent CLI command is:

```bash
fyron document-download \
  --csv documents.csv \
  --url-col document_url \
  --id-col document_id \
  --output-dir documents_out \
  --flat-output \
  --no-completion-record \
  --pdf \
  --timeout 90 \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs' \
  --token-cache "$HOME/.cache/fyron/document-tokens.json" \
  --results-csv document-results.csv
```

All endpoints and client identifiers above are fictional. The first run requires
browser approval; subsequent runs reuse usable cached credentials and renew
access tokens through the shared `Auth` implementation. For unattended use after
establishing the cache, add `allow_reauthentication=False` to `Auth` or
`--no-reauthentication` to the CLI. An unusable cache or failed renewal then fails
without prompting for a new login.

The cache contains sensitive, unencrypted tokens and requires POSIX owner-only
permissions and locking. Protected caching is not supported on Windows. It is
opt-in and independent of `write_completion_record=False`: disabling document
JSON records does not disable the authentication cache. Cached login also does
not verify existing documents; without completion records, reruns still require
intentional `skip_existing=False` / `--overwrite` to replace existing files.

For single downloads, use `download_url(url, document_id="00123")` or
`--url ... --document-id 00123`. An explicit `output_path` / `--output` overrides
the generated filename. Without flat output, custom IDs produce
`<output_dir>/<id>/<id>.<extension>`. Existing extension rules still apply.

IDs accept strings and integers. Preserve leading zeros by loading IDs as strings.
They must be 1–128 ASCII characters, start with a letter or digit, and contain only
letters, digits, dots, underscores, and hyphens. Trailing dots, Windows reserved
names, missing values, booleans, and floats are rejected. IDs are not silently
trimmed or sanitized. Selected IDs must be unique within a batch, including
case-insensitive comparisons; invalid batches fail before downloading (and before
CLI authentication).
If distinct IDs resolve to the same final filename after applying response
extensions, the conflicting download fails rather than overwriting another
document in the batch, even when overwrite is enabled.

Custom naming is opt-in: omitting `id_col` / `--id-col` keeps existing URL-hash
behavior even if the table has a column named `document_id`. Results retain the
original URL-hash `download_id` and add `document_id` with the chosen ID (or the
hash by default). The `path` column records the actual destination. Use these
columns rather than completion order to match results to the input table.
Completion records bind the source URL, chosen ID, destination, and validation
policy, so reusing an ID for a different URL cannot silently skip that download.

### CLI Defaults and Authentication Options

The CLI defaults to a 90-second request timeout, four workers, verified skips,
and no redirects. `--overwrite` permits replacement; `--allow-redirects` enables
only same-origin redirects. Console summaries contain counts; results CSV files
contain sensitive URLs and paths. Browser approval instructions remain visible
with `--quiet`, separately from diagnostic logs.

For unattended service accounts, use `--auth-type client_credentials`,
`--client-id`, `--auth-url` (or `--token-endpoint`), and
`--client-secret-env DOCUMENT_CLIENT_SECRET`. Provision that environment variable
through your secret-management process; never put the secret itself on the command
line. Scopes are optional and provider-specific.

`--token-cache` opts into sensitive, unencrypted device-token storage.
`--no-reauthentication` prohibits browser approval and requires usable cached
credentials. `--auth-type none` is the CLI default and does not inherit FHIR
authentication environment variables. See the [CLI reference](../cli.md#document-downloads)
for options and exit codes.

## `DocumentDownloader`

```python
loader = DocumentDownloader(
    base_url="https://example.org",
    output_dir="docs_out",
    skip_existing=True,
)
```

### Constructor Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `auth` | no | `Auth | requests.Session | None` | `None` | Reuse Fyron auth/session. |
| `base_url` | no | `str | None` | env `FHIR_BASE_URL` | Prefix for relative URLs. |
| `output_dir` | no | `str | Path` | `"documents_out"` | Parent folder for downloads. |
| `timeout` | no | `float` | `30` | Positive finite request timeout in seconds. |
| `skip_existing` | no | `bool` | `True` | Skip only verified downloads; False permits replacement. |
| `log_downloads` | no | `bool` | `False` | Log each download. |
| `max_workers` | no | `int` | `4` | Thread workers for URL lists/DataFrames. |
| `retries` | no | `urllib3 Retry | None` | default retry policy | Custom retry behavior. |
| `save_mode` | no | `str` | `"auto"` | Save behavior: auto/text/PDF style handling. |
| `force_extension` | no | `str | None` | `None` | Force a file extension. |
| `basic_auth` | no | `(str, str) | None` | `None` | Standalone basic auth tuple. |
| `require_pdf` | no | `bool` | `False` | Keyword-only: require HTTP 200, PDF media type, and PDF signature. |
| `allow_redirects` | no | `bool` | `True` | Keyword-only: follow only guarded same-origin redirects; False rejects redirects. |
| `write_completion_record` | no | `bool` | `True` | Keyword-only: write a hidden JSON record for verified skips; False saves the document without a new record. |
| `flat_output` | no | `bool` | `False` | Keyword-only: save directly in the output directory with URL-hash filenames and absolute result paths. Explicit `output_path` takes precedence. |

## `download_url`

Downloads one URL into a deterministic folder based on URL hash.

```python
result = loader.download_url("https://example.org/report_001.pdf")
```

| Parameter | Required | Description |
| --- | --- | --- |
| `url` | yes | Absolute URL or relative URL when `base_url` is set. |
| `output_path` | no | Keyword-only exact file destination; omit for automatic naming. |
| `document_id` | no | Keyword-only custom string/integer ID; omit to retain URL-hash naming. |

Returns a `DocumentResult` with URL, local path, status, content type, hash, and error metadata.

## `download_urls`

Downloads many URLs, optionally writing a results CSV.

```python
results = loader.download_urls(
    [
        "https://example.org/report_001.pdf",
        "https://example.org/report_002.pdf",
    ],
    results_csv="document_downloads.csv",
)
```

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `urls` | yes | none | Iterable of URLs. |
| `results_csv` | no | `None` | Optional CSV path for results. |

Returns a DataFrame of download results.

## `download_from_df`

Downloads URLs from a DataFrame column.

```python
results = loader.download_from_df(
    documents_df,
    url_col="document_url",
    results_csv="document_downloads.csv",
)
```

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `df` | yes | none | Input DataFrame. |
| `url_col` | no | `"document_url"` | Column containing URLs. |
| `id_col` | no | `None` | Keyword-only column containing custom document IDs; supported by both DataFrame methods. |
| `results_csv` | no | `None` | Optional output CSV. |

`download_from_dataframe` is the same method under the longer name.

## Static Helper: `download_id`

```python
download_id = DocumentDownloader.download_id("https://example.org/report.pdf")
```

Returns a deterministic SHA-256 ID for a URL. This ID is used for stable folder naming.

## Context Manager

```python
with DocumentDownloader(output_dir="docs") as loader:
    results = loader.download_urls(urls)
```

The context manager closes owned sessions and internally created authentication.
Caller-supplied `Auth` objects and sessions remain caller-owned; close them
separately, as in the nested context managers above.

## Practical Tips

- Use `results_csv` for long-running batches so failures can be inspected.
- Use `skip_existing=True` to make download jobs restartable.
- Use `basic_auth` or `auth`, not both.
- Use `force_extension=".pdf"` only when the server does not provide useful filenames/content types.
