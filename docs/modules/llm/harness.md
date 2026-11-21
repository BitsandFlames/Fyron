# Build your own research agent

A harness is the Python loop that gives a model a question, runs the tools it requests, and returns their results for the next turn. In this walkthrough the model can read a report, but Python decides which patient's records are accessible and calculates the interval between dates.

## Run the starter

[Download the runnable starter and synthetic records](../../assets/research-agent-starter.zip). Extract the ZIP in an empty folder and open a terminal there. The commands also work from the root of the Fyron checkout. Use a Python 3.11 or 3.12 environment with Fyron installed. Install the Beta 6 wheel from the GitHub release or pin Beta 6 when available on your package index:

```bash
python -m pip install "fyron==0.3.20b6"
```

Run this first. The bundled documents and scripted model work offline:

```bash
python examples/agent_harness/run.py --data-mode sandbox --model scripted --patient 0007
```

**Question:** What follow-up was recommended, and how many days passed between imaging and discharge?

**Answer:** Repeat imaging in six weeks. The discharge letter was dated seven days after the study.

| Tool call | Evidence available to the next turn |
| --- | --- |
| `list_imaging_studies()` | I1, dated January 1 |
| `list_documents()` | D1 is the radiology report. D2 is the discharge letter. |
| `read_document("D1")` | “Repeat imaging in six weeks.” |
| `read_document("D2")` | “Outpatient imaging was scheduled.” |
| `days_between("I1", "D2")` | Seven elapsed days, calculated in Python |

The sixth turn returns the answer with source labels D1, I1 and D2. The terminal trace records tool names, input labels and outcomes. The trace omits excerpts. Review the answer against its cited records before using it.

Choose the next step according to what you want to change:

| Goal | Keep | Change |
| --- | --- | --- |
| Let a model choose the next tool | Synthetic files and built-in tools | [Connect a model](#connect-a-model) |
| Ask questions about your own files | Local readers and the configured model | [Supply your own data folder](#bring-your-own-local-data) |
| Give the model a new capability | Patient scope and dispatch loop | [Register and test a Python function](#register-your-own-function) |
| Query a live service | Model and tool names | [Enable a read-only reader](#switch-one-reader-to-a-connected-service) |

## Bring your own local data

The caller selects the patient before the model sees any tools. The starter reads this structure beneath `--root`:

```text
demo_data/
  fhir/studies.bundle.json
  tables/encounters.csv
  documents/manifest.csv
  documents/report-a.txt
  documents/discharge-b.txt
  documents/report-c.txt
```

Use a FHIR Bundle with ImagingStudy entries, relative references such as `Patient/0007` and a `started` date. The encounter CSV requires `patient_id,date`. The document manifest uses the following columns:

```csv
patient_id,label,category,date,path
0007,D1,radiology,2025-01-01,report-a.txt
```

Keep IDs as strings. Document labels are unique within a patient's manifest and follow D1, D2, etc. Paths resolve under the local data root. Text files use UTF-8. Text-bearing PDFs require Poppler's `pdftotext` on PATH. The reader rejects files over 5 MB and extracted texts over 8,000 characters. Listings over 30 records return an incomplete outcome.

After configuring your model, point the same command at your own folder. The patient argument is matched as a string, so `0007` and `7` select different records.

```bash
python examples/agent_harness/run.py --root ./my_data --patient 0007 \
  --model configured --question "What follow-up did the discharge letter describe?"
```

## Connect a model

The offline adapter plays a fixed walkthrough for patient 0007. To let a model decide which tool to call next, configure an approved endpoint and run the same local readers:

```bash
export LLM_PROVIDER=anyllm
export LLM_BASE_URL=https://model.example.org
export LLM_MODEL=example-model
# Set LLM_API_KEY through your approved credential mechanism.
python examples/agent_harness/run.py --patient 0007 --model configured
```

The adapter calls `LLMAgent.prompt()` with the question, tool descriptions and the results of earlier calls. A remote model receives listed dates and categories, local labels, document text returned by a read, and computed intervals. Sandbox selects the data source. Use the scripted adapter or a local model endpoint when evidence must stay local.

The dispatcher accepts two JSON shapes:

```json
{"tool":"read_document","args":{"label":"D1"}}
```

```json
{"answer":"The report recommends repeat imaging in six weeks.","sources":["D1"]}
```

Each call must name a registered tool and match its argument names. A final citation to a document requires a successful read. An invalid response, unknown tool, failed read or exhausted six-step budget yields a status alongside the trace. Source checks establish which records were available to the model. Reviewing whether the answer accurately represents those records remains a human task.

## Register your own function

In `examples/agent_harness/run.py`, the registry associates a name and description with a Python callable. Here are the custom document reader and the Fyron-backed calculation:

```python
tools["read_document"] = ("Read a document by its listed label.", read_document)
tools["days_between"] = ("Signed elapsed days between two previously listed sources.", days_between)
```

The first callable reads from the configured patient index. The second calls `fyron.dataframe.date_difference(dates[first], dates[second], unit="days")` and returns the interval and both labels. Model arguments are short strings. The dispatcher checks arguments named `label`, `first` or `second` against previously listed source labels.

**Try adding a tool.** Insert the following inside the `if documents is not None` block in `registry()`. Then run the configured adapter with `--question "What follow-up did the radiology report recommend?"`.

```python
def list_documents_by_category(category):
    return [row for row in list_documents() if row["category"] == category]

tools["list_documents_by_category"] = (
    "List documents with the supplied category, such as radiology.",
    list_documents_by_category,
)
```

### Check your tool before connecting the model

From the starter root, verify the function, the registry name and the synthetic result in Python. Run this after adding the function above. It uses the same registry as the configured model.

```python
import sys
from pathlib import Path

starter = Path("examples/agent_harness").resolve()
sys.path.insert(0, str(starter))
from readers import sandbox
from run import registry

tools, _ = registry(sandbox(starter / "demo_data", "0007"))
description, lookup = tools["list_documents_by_category"]
assert lookup("radiology") == [
    {"label": "D1", "category": "radiology", "date": "2025-01-01"}
]
```

When the model calls this tool it sees only a label, category and date. To answer a question about the recommendation it must then call `read_document("D1")`. This is the advantage of exposing separate listing and reading tools.

## Switch one reader to a connected service

Start with just FHIR. The reader exposes a predefined patient-scoped search. Configure an approved HTTPS base and a read-scoped credential before running:

```bash
export FHIR_BASE_URL=https://fhir.example.org/r4
# Set HARNESS_FHIR_TOKEN locally.
python examples/agent_harness/run.py --data-mode connected --readers fhir \
  --model configured --patient 0007 --question "Which imaging study dates are available?"
```

| Enabled reader | Configuration and behavior |
| --- | --- |
| `fhir` | Calls `FHIRRestClient.search_df("ImagingStudy", ...)` with a bound patient reference, a field projection and a two-page limit. Checks returned patient references and pagination status. |
| `sql` | Set `FHIR_DB_DSN` for a role granted SELECT on approved views. Use verified TLS for remote connections. Adapt the fixed view and columns in `sql_encounters()` to your schema. The example sets read-only transactions on its own connection, binds the patient parameter and applies a statement timeout. |
| `documents` | Set `HARNESS_DOCUMENT_INDEX` to a local CSV with `patient_id,label,category,date,url`, `HARNESS_DOCUMENT_ORIGIN` to the approved HTTPS origin, and `HARNESS_DOCUMENT_TOKEN` to its read-scoped token. The reader uses `DocumentDownloader`, disables redirects, accepts plain text or PDF, and removes its temporary files. |

Pass multiple names after `--readers` to enable more tools. The document index always uses your local patient ID. When institutional FHIR or SQL IDs differ, set `HARNESS_PATIENT_MAP` to a CSV with `patient_id,fhir_id,sql_id` and one row per selected patient. Without a mapping, both readers use the caller's patient ID. Confirm the mapping and permissions with your site. More authentication examples are in the [authentication guides](../../authentication/index.md).

For example, a connected documents index uses a URL in place of the local path:

```csv
patient_id,label,category,date,url
0007,D1,radiology,2025-01-01,https://documents.example.org/reports/a.pdf
```

After configuring the SQL and document readers above, request just those services:

```bash
python examples/agent_harness/run.py --data-mode connected --readers sql documents \
  --model configured --patient 0007 --question "How many days elapsed from the encounter to the report?"
```

## When a run stops

Inspect the top-level `status` and the last entry in `trace`. An early stop returns an empty answer and a nonzero process exit code.

| Status | What to check |
| --- | --- |
| `incomplete` | Read the trace outcome. For `pagination_limit` or `record_limit`, narrow the reader's query. For `missing_date`, inspect the source dates before retrying the calculation. |
| `tool_failed` | Check the named reader's local setup, permissions, file paths and PDF extractor. |
| `invalid_response`, `unknown_tool`, `invalid_arguments` | Compare the model's proposed action with the two JSON shapes above, the registered tool names and the labels returned by listing tools. |
| `invalid_citation` | Check whether the model actually read the cited document. Listing a document alone does not establish its content. |
| `model_failed`, `step_limit` | For a failed request check the configured endpoint and credentials. If the six-turn budget ran out, try a narrower question. |

Use [DataFrame prompts](prompts.md) for a fixed set of questions across a cohort. Use this starter when an earlier result determines which function to call or which document to read.
