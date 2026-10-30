# Documents

For site-specific access setup, see [Document authentication](../authentication/documents.md). Choose the method and permissions approved by your administrator.

`fyron.documents` retrieves URL-addressable documents for research workflows,
including plain-text reports (`text/plain`) and PDFs (`application/pdf`). Download
files first, review their outcomes, then pass the local files to parsing or analysis.

## Documents Submodules

| Chapter | Use it for |
| --- | --- |
| [DocumentDownloader](documents/downloader.md) | Single-document and batch downloads, OIDC authentication, PDF validation, and verified restarts. |

## Choose The Right Path

| Need | Prefer |
| --- | --- |
| Download a plain-text report | [Plain text](documents/downloader.md#plain-text), without strict PDF mode. |
| Download and validate a PDF response | [OIDC PDF workflow](documents/downloader.md#browser-approved-oidc-downloads), with `require_pdf=True` or `--pdf`. |
| Download a mixed cohort of text files and PDFs | [Mixed batches](documents/downloader.md#mixed-text-and-pdf-batches), without `--pdf`. |
| Download URLs listed in a CSV | [CSV batch downloads](documents/downloader.md#csv-batch-downloads), using the `document_url` column. |
| Save all files in one folder and record their paths | [Flat-folder Python and CLI examples](documents/downloader.md#save-all-documents-in-one-folder), with `flat_output=True` / `--flat-output`. |
| Omit per-document JSON files | [Completion-record opt-out](documents/downloader.md#save-documents-without-json-completion-records), with explicit overwrite required on unverified reruns. |
| Sign in through browser approval or a service account | [Authentication](documents/downloader.md#browser-approved-oidc-downloads) using the shared Fyron `Auth`. |
| Choose document filenames and reuse cached login | [Custom IDs and cached login](documents/downloader.md#custom-document-ids-and-cached-login). |
| Restart an interrupted download | [Safe restarts](documents/downloader.md#safe-restarts), with verified completion records. |
| Run downloads from a terminal | [Document CLI](cli.md#document-downloads). |

## Typical Workflow

1. Obtain approved document URLs from the source system or a cohort table.
2. Configure authentication and choose general or strict PDF download mode.
3. Download files and inspect the returned errors, content types, and paths.
4. Keep completion records and sensitive results tables with the downloaded files.
5. Process local documents only after checking the download outcomes.

## Import

```python
from fyron import Auth, DocumentDownloader
```

## Formats and Output

General mode supports both text and PDF files and saves response bytes without
converting formats. Automatic naming uses the response content type; an explicit
output path keeps the chosen filename. Strict PDF mode is optional and rejects
non-PDF responses. It checks the media type and signature, not the entire PDF syntax.

The same downloader supports one URL, URL lists, and DataFrame/CSV batches. Results
include a deterministic download ID, local path, HTTP status, content type, hash,
and error/skip information. URL and path fields can be sensitive; logs contain
controlled diagnostics and outcome counts.

## Related Modules

- [FHIR](fhir.md) for querying document metadata and resource references.
- [Core I/O](core.md) for local tables and file operations.
- [LLM](llm.md) for reviewed narrative assistance after retrieval.
- [Audit & Provenance](audit.md) for reproducibility manifests.
