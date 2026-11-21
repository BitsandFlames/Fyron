# Reconcile a document cohort and retry a failed download

Read or download the [complete example script](../assets/cohort_reconciliation.py). To run the repository copy, install Fyron Beta 6 and execute:

```bash
python examples/cohort_reconciliation.py
```

The example starts with patient strings 001 through 005. A synthetic FHIR DocumentReference search and a simulated PostgreSQL cohort query return the same document index. Both routes run the document extraction and patient summary workflows. Model answers are fixed and all requests stay offline.

| Patient | Records found | Documents expected | Documents read | Summary before retry | Reason |
| --- | ---: | ---: | ---: | --- | --- |
| 001 | 1 | 1 | 1 | ok | |
| 002 | 0 | 0 | 0 | no_matching_records | |
| 003 | 1 | 1 | 0 | incomplete | download_failed |
| 004 | 1 | 1 | 0 | incomplete | empty_text |
| 005 | 2 | 2 | 1 | incomplete | empty_text |

Start the final table from the original cohort and left-join counts and summaries. Patient 002 had no match in this query. Patient 003 had a matching document that could not be retrieved. Treating either as a negative clinical finding would lose that distinction.

## Retry selected results

In the example, inspect `answers[answers.reason.eq("download_failed")]` and retry only after the synthetic service recovers. Replace answers on the pair `(doc_id, prompt_name)` and preserve every other row. Rebuild summaries only for patients whose answers changed. Patient 003 now has one readable document and an `ok` summary. Patients 004 and 005 still need source review or OCR. Inspect the per-source reasons in `sources` when a group reports `multiple_reasons`.

The example uses one extraction prompt per document and one attachment per matching record. When using multiple prompts or attachments, count distinct documents independently of answer rows.
