# Documents: from a URL table to local files

**You will produce:** named files in `documents_out/`, verified completion records and `results/documents.csv` with actual file paths.

**Prerequisite:** [Setup](index.md), the [authentication helper](authentication.md), and reviewed URLs on a service permitted to receive the selected token.

**Exercise 3.** Save this complete script as `download_documents.py` beside the auth helper. Replace the three fictional document URLs with approved PDF URLs before connecting to a real service:

```python
from pathlib import Path
import pandas as pd
from fyron import DocumentDownloader
from onboarding_auth import make_auth


def download_documents(auth):
    Path("results").mkdir(exist_ok=True)
    documents = pd.DataFrame({
        "document_id": ["001", "002"],
        "document_url": [
            "https://documents.example.org/reports/001.pdf",
            "https://documents.example.org/reports/002.pdf",
        ],
    })
    # Alternative: preserve IDs such as "001" when loading your reviewed CSV.
    # documents = pd.read_csv("documents.csv", dtype="string")
    with DocumentDownloader(
        auth=auth, output_dir="documents_out", flat_output=True,
        timeout=90, max_workers=1, require_pdf=True, allow_redirects=False,
        write_completion_record=True,
    ) as downloader:
        single = downloader.download_url(
            "https://documents.example.org/reports/003.pdf", document_id="003",
        )
        if single.error is not None:
            raise RuntimeError("Single document failed; inspect its result privately")
        results = downloader.download_from_df(
            documents, url_col="document_url", id_col="document_id",
            results_csv="results/documents.csv",
        )
    if results.empty or results["error"].notna().any():
        raise RuntimeError("Some documents failed; inspect results/documents.csv")
    return results


if __name__ == "__main__":
    with make_auth("device_code", cache_name="documents-demo.json") as auth:
        results = download_documents(auth)
```

Run it:

```bash
uv run python download_documents.py
```

**Check your result:** successful output contains `documents_out/001.pdf`, `002.pdf` and `003.pdf`, plus completion records. `results/documents.csv` contains the two batch outcomes, including absolute paths, errors and skip indicators. The single `003` request is checked separately. Rerun unchanged and confirm verified skips instead of replacement.

**Try CSV input:** save this as `documents.csv`, replace the URLs with approved ones, and replace the inline `documents = pd.DataFrame(...)` assignment with `documents = pd.read_csv("documents.csv", dtype="string")`:

```csv
document_id,document_url
001,https://documents.example.org/reports/001.pdf
002,https://documents.example.org/reports/002.pdf
```

For client credentials, replace only the entrypoint block:

```python
if __name__ == "__main__":
    with make_auth("client_credentials") as auth:
        results = download_documents(auth)
```

The PDF example produces `001.pdf`, `002.pdf` and `003.pdf` directly in `documents_out`. The results `path` column holds actual absolute paths for this layout. IDs must be filename-safe and unique, including case-insensitive comparisons. Omitting custom IDs retains URL-hash naming.

Set `require_pdf=False` for general documents, including `text/plain`. Extensions then follow the downloader's existing URL/content-type rules. Strict PDF checking validates HTTP status, media type and signature, not the full PDF or its clinical content. See [document downloads](../modules/documents/downloader.md) for exact rules.

Set `write_completion_record=False` only if you deliberately do not want per-document JSON records. This does not disable the separate authentication cache. Without a valid completion record, existing files are protected rather than silently skipped. For an intentional replacement, use `skip_existing=False` in Python; the CLI equivalent is `--overwrite`. On interruption, inspect result errors and completion records before retrying. Keep result CSVs separate from downloaded files.

## General documents, including plain text

For a manifest containing text reports, keep the same function and CSV input, but use `require_pdf=False` and approved text URLs. If using the single-document example too, change its URL to a text document. This disables PDF-only checks; it is not a promise that an HTTP 200 response contains the report you intended.

```csv
document_id,document_url
001,https://documents.example.org/reports/001.txt
002,https://documents.example.org/reports/002.txt
```

Inspect content type, result errors and the saved file before treating it as usable input. Authentication/login HTML can be a successful HTTP response when strict PDF checking is off. Use the actual `path` returned by Fyron rather than reconstructing a filename.

## A practical retry checkpoint

| Outcome | Next action |
| --- | --- |
| `error` is missing, file present | Inspect the content and keep the result row |
| `skipped` is true | Confirm this is an expected verified restart |
| `error` is present | Resolve it and retry; do not count the row as a successful download |
| Completion JSON disabled, destination exists | Explicitly choose whether replacement is intended; no automatic verified skip |

**Next:** compare [REST and SQL](sql.md#rest-and-sql-side-by-side), or explore the detailed [downloader guide](../modules/documents/downloader.md).

For exact custom names without new JSON records, use `id_col` together with
`flat_output=True` and `write_completion_record=False`. See the
[custom naming recipe](../modules/documents/downloader.md#custom-names-without-hash-folders-or-completion-json).

## Reliability in current source

For text endpoints, `expected_content_types=["text/plain"]` rejects unexpected HTML. Batch `return_report=True` adds task counts without changing the default DataFrame return. These options are included in Beta 5.

See [Reconcile a document cohort and retry a failed download](reconciliation.md) for the five-patient offline walkthrough.
