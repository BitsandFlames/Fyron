# Prompt templates and context

Use one row per document. This example asks for findings in radiology reports and follow-up recommendations in every document. Download the [example JSON prompt pack](../../assets/research_prompts.json) as `research_prompts.json` in your working directory. Configure your approved endpoint as described in [LLMAgent](../llm.md#llmagent).

```python
import pandas as pd
from fyron.llm import LLMAgent, load_prompt_templates

agent = LLMAgent()  # Reads your configured LLM environment variables.
pack = load_prompt_templates("research_prompts.json")
documents = pd.DataFrame([
    ("0007", "A", "2025-01-01", "radiology", "Repeat imaging in six weeks."),
    ("0007", "B", "2025-01-08", "discharge", "Outpatient imaging was scheduled."),
    ("0008", "C", "2025-01-03", "radiology", "No interval change described."),
], columns=["patient_id", "doc_id", "date", "category", "text"])

answers = agent.run_prompts_on_dataframe(
    documents, prompts=pack, prompt_names=["findings", "follow_up"],
    text_col="text", document_id_col="doc_id", category_col="category",
    context_cols=["date"], keep_cols=["patient_id", "date", "category"],
    max_workers=4,
)
print(answers[["patient_id", "prompt_name", "status", "sources"]])
```

Expect five result rows. Documents A and C each receive two questions. Document B receives only the follow-up question. Each result has an `answer`, a `status` and a local mapping from source labels to document IDs.

## What context reaches the model?

For the first row, the model receives the selected instruction followed by this evidence:

```json
[{"source": "S1", "text": "Repeat imaging in six weeks.", "context": {"date": "2025-01-01"}}]
```

| Option | What it does |
| --- | --- |
| `context_cols=["date"]` | Sends the date beside each text so the model can interpret relative dates. Omit this option to send evidence without metadata. |
| `keep_cols=["patient_id", "date", "category"]` | Copies these columns into the answer table for review, joins or later summaries. A field can be both kept and sent. |
| `category_col="category"` | Selects rows for category-specific prompts. Add the category to `context_cols` if the model also needs its value. |
| `max_workers=4` | Allows up to four concurrent model requests with independent HTTP sessions. The default is one. Output order stays deterministic. |

Put instructions shared by every row directly in the template. For example, this Python pack works wherever the example uses `prompts=pack`. The same structure can be saved as JSON.

```python
follow_up_pack = {"prompts": [{
    "name": "follow_up",
    "prompt": "Quote the follow-up recommendation. Use the supplied date to interpret relative timing. If timing is unclear, say so."
}]}
```

Keep patient identifiers local unless the endpoint needs them and is approved to receive them. Review the document text itself for identifying details. Continue with [grouped summaries](summaries.md) to combine records for the same patient.
