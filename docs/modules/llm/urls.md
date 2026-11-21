# Documents from URLs

A table of distinct document URLs is enough to ask several questions per file. Fyron downloads each applicable URL once per call, extracts its text locally and reuses it across prompts. The addresses below are fictional. Supply URLs from your approved document service when running the example.

```python
import pandas as pd
from fyron.llm import LLMAgent

agent = LLMAgent()  # Uses your configured model endpoint.
links = pd.DataFrame({"document_url": [
    "https://documents.example.org/reports/report-a.pdf",
    "https://documents.example.org/reports/note-b.txt",
]})
answers = agent.run_prompts_on_dataframe(
    links, url_col="document_url", prompts="research_prompts.json",
    prompt_names=["follow_up", "timeline"], max_workers=4,
)
print(answers[["prompt_name", "status"]])
```

Download the [example prompt pack](../../assets/research_prompts.json) into your working directory first. This example gives each document its own timeline. For a combined timeline, include a patient column and pass `group_cols=["patient_id"]`. Include a date column and use `context_cols=["date"]` when dates should accompany the extracted text. [Grouped summaries](summaries.md)

## Protected document services

Configure the site's approved authentication method using the [document authentication guide](../../authentication/documents.md). Pass the resulting `auth` and the exact HTTPS origin together:

```python
protected_answers = agent.run_prompts_on_dataframe(
    links, url_col="document_url", prompts="research_prompts.json",
    prompt_names=["follow_up"], document_auth=auth,
    document_origin="https://documents.example.org",
)
```

Document authentication is separate from the model credentials. The default fetch is anonymous and redirects are disabled. URLs are retained locally as source IDs by default. Supply a unique `document_id_col` to keep signed links out of result mappings or to distinguish rows that share a URL.

## Formats and concurrency

| HTTP content type | Preparation |
| --- | --- |
| `text/plain` | Uses the declared charset, defaulting to UTF-8. |
| `application/pdf` | Requires Poppler’s `pdftotext` on PATH and an extractable text layer. Run OCR first for image-only scans. |

Downloads run sequentially in temporary storage. `max_workers` controls the subsequent model requests. Failed downloads, unsupported content types or empty extracted text yield `incomplete` for affected requests. Inspect the [summary statuses](summaries.md#decide-which-outputs-are-usable) before using the results.

## Limits and failure reasons

URL workflows default to `max_download_bytes=5_000_000` per response and `max_extracted_chars=100_000` per decoded document. Plain-text and PDF extraction enforce the character limit while reading. `max_input_chars` separately limits the whole rendered model request. Direct `DocumentDownloader` calls default to unlimited bytes unless you set a cap.

Inspect `reason` alongside `status`. Successful answers have an empty reason. A failed source can report `download_failed`, `download_too_large`, `unsupported_media_type`, `decoding_failed`, `pdf_converter_unavailable`, `pdf_conversion_timeout`, `extracted_text_too_large` or `empty_text`. A rendered prompt can report `prompt_too_large` and an unsuccessful model call can report `model_failed`. Mixed failures yield `multiple_reasons` with details in the local source mapping.
