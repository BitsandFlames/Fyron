# Grouped summaries

Choose the evidence you want the model to read. A direct timeline uses the original documents. A summary of reviewed answers uses the extraction table and any corrections you have made to its answer text. The examples use the synthetic `documents`, `answers`, `agent` and `pack` from [Prompt templates and context](prompts.md).

## Summarize the original documents

```python
timelines = agent.run_prompts_on_dataframe(
    documents, text_col="text", document_id_col="doc_id", prompts=pack,
    prompt_names=["timeline"], group_cols=["patient_id"], order_by="date",
    context_cols=["date", "category"],
)
print(timelines[["patient_id", "status", "sources"]])
```

Patient 0007 gets one timeline from documents A and B, in date order. Patient 0008 gets a separate timeline from C. The date is sent because it appears in `context_cols`. Sorting alone only changes evidence order. Use datetime values or sortable ISO dates.

| Desired summary | Group columns |
| --- | --- |
| One per patient across all categories | `["patient_id"]` |
| Separate radiology and discharge summaries for each patient | `["patient_id", "category"]` |
| One per encounter | `["patient_id", "encounter_id"]`, when the input includes encounter IDs |

A template’s optional `categories` filter limits which records contribute. Groups with no matching evidence produce no row.

## Summarize reviewed answers

```python
follow_up = agent.summarize_dataframe(
    answers, prompts=pack, group_cols=["patient_id"],
    source_prompt_names=["follow_up"], prompt_names=["timeline"],
    order_by="date", context_cols=["date"], max_workers=4,
)
print(follow_up[["patient_id", "answer", "status", "sources"]])
```

Here `source_prompt_names` chooses the earlier **answers to read**. `prompt_names` chooses the new **questions to ask**. Retain unsuccessful rows during review so Fyron can detect gaps. Labels such as S1 are local to each request. Follow the nested `sources` mapping to trace a summary through each selected answer to its original document.

## Decide which outputs are usable

| Status | Interpretation |
| --- | --- |
| `ok` | The model returned nonempty text. Review its content against the sources. |
| `failed` | The model request failed or returned empty text. |
| `incomplete` | Required evidence was missing or unusable. The affected summary was withheld. |
| `partial` | With `allow_partial=True` on `summarize_dataframe`, the model used available answers despite incomplete evidence. At least one usable answer is required. |
| `oversized` | The rendered request exceeded `max_input_chars` (default 100,000 characters). Choose smaller groups or summarize reviewed extractions. |

Use `max_input_chars` with your endpoint’s token budget in mind. Characters and tokens measure different things.

See [Reconcile a document cohort and retry a failed download](../../onboarding/reconciliation.md) for the five-patient offline walkthrough.

For a nonempty answer table, each requested `source_prompt_names` entry must occur in its prompt-name column. Unknown names raise before model calls. Empty answer tables with the expected columns yield empty summaries. Incomplete and partial summaries retain reasons in the source mapping, including through nested summaries.
