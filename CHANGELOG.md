# Changelog

## 0.3.20b6

Released November 21, 2026 under CC BY-NC 4.0. Python 3.11+ is required.

- Run named JSON prompt templates on DataFrame text or document URLs. Select context columns, combine records by patient or encounter, and summarize reviewed answers with source mappings.
- Process model requests concurrently with bounded workers. Per-document download and extraction limits protect URL workflows. Inspect controlled failure reasons and selectively retry failed documents.
- Build a research agent using the downloadable starter, synthetic local records and optional read-only FHIR REST, SQL and document readers.
- Follow the five-patient reconciliation example to distinguish missing records, unreadable documents and completed summaries.

## Upgrade notes

Single-prompt workflows remain available. Direct document downloads have an optional byte cap, unlimited by default. URL prompt workflows default to 5,000,000 decoded bytes and 100,000 extracted characters per document. Text-bearing PDFs require Poppler’s pdftotext executable. Source prompt names must match the supplied nonempty answer table.
