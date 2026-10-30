# Safe Network Diagnostics

These changes are in the development checkout after 0.3.12. They are not present
in previously built 0.3.12 wheels.

Fyron network diagnostics use controlled operation/stage labels, run-local IDs,
durations, counts, HTTP status codes, and error categories. They do not emit
remote response bodies, query values, clinical identifiers, SQL, prompts, or
raw exception messages. DEBUG does not enable an unsafe diagnostic mode.

```python
from fyron.console import configure_logging

configure_logging(level="INFO", json=True)
```

The CLI equivalent is `fyron --json-log ...`. JSON events contain timezone-aware
timestamps and structured fields; readable logs contain the same event fields.
Applications may supply their own Python logging handlers. Protection is applied
at Fyron's emission sites, not only in its formatter. Existing request-logging
flags now control safe events, not disclosure of request URLs.

External SDK logging, user callbacks, and application-created log messages are
outside this guarantee. Do not enable HTTP wire tracing on clinical systems.
Device-login approval instructions intentionally remain available through the
interactive console or approval callback. Do not persist approval instructions
or token-cache contents in diagnostic logs.

## Errors and Sensitive Outputs

Safe error categories include `authentication`, `permission`, `timeout`,
`network`, `unexpected_response`, `conversion`, `filesystem`, `empty_download`,
and `unknown`. Categories describe available evidence, not a guaranteed root
cause. Unknown failures are deliberately not expanded into raw provider text.

Existing result fields and public Fyron exception classes remain available.
Diagnostic error text is now safe text rather than the original provider
message. LLM batch failures retain their `ERROR:` prefix. Code that parsed raw
error messages must be updated. Error traceback chains no longer display
underlying remote messages.

Results are **not anonymized**: explicit URL, path, identifier, document, and
clinical-data columns retain their purpose. Treat result CSVs and manifests as
sensitive research outputs. Share diagnostic logs instead, after reviewing them.

## Batch Completion

Batch events distinguish `started`, `finished`, and `incomplete`. A finished
batch may contain failed items. Inspect outcome counts and result errors before
using downloaded data. Interrupted runs report the counts collected so far.

DICOM `completed` counts tasks. `succeeded`, `failed`, and `skipped` count result
items: one study task may produce multiple series results. DICOM and document
results include an additive `skipped` Boolean, defaulting to false. The current
development implementation requires a valid local completion record before
skipping. Verification establishes local integrity, not remote completeness.
Unverified existing outputs are preserved and reported as conflicts unless an
explicit overwrite was requested.

FHIR query completion counts input query jobs, not patients found or bundles.
A worker failure still raises rather than returning a successful partial table.
Previously yielded streaming bundles must be treated as incomplete on failure.

Progress reaching 100% means all tasks were processed, not that all succeeded.
No new automatic retries or resubmission of uncertain writes are introduced.

## DICOM HTML Responses

`text/html` instead of a DICOM multipart response means an unexpected response.
Possible causes include a login page, gateway error, or endpoint mismatch. It
occurs before NIfTI conversion. Do not assume changing output format fixes it.

Check one approved series request with redirects disabled, reporting only its
HTTP status, media type, whether a Bearer header was attached, and whether a
redirect occurred. Never print the token, full URL, Location header, or body.
Compare sequential and parallel behavior before attributing the fault to either
the server or Fyron. Cross-host credential stripping and retry limits remain
unchanged.

To inspect failed downloads locally:

```python
failed = results.loc[results["error"].notna()]
skipped = results.loc[results["skipped"]]
```

Review partial files before manually retrying failures. Keep identifying result
columns local, and do not interpret a completed progress bar as a successful
download report.
