# LLM

`fyron.llm` provides a lightweight interface for prompts over text, files, images, DataFrames, and directories. It is designed for narrative assistance, extraction prototypes, and methods-documentation support. Keep statistical analysis and clinical decisions in explicit code.

Treat LLM outputs as generated annotations that need review. The module is most useful for summarizing documents, drafting methods text, extracting candidate labels for later validation, or applying the same prompt across a DataFrame. Keep prompts versioned and store outputs next to the input identifiers.

DataFrame batch prompts preserve original column names, including spaces. Directory batches return filename keys and reject duplicate basenames in recursive searches before sending requests. In `mode="auto"`, ordinary text files use the text route.

Requests-based FHIR, DICOMweb, document, and LLM clients follow redirects only within the same scheme, host, and port. Cross-origin redirects, HTTPS downgrades, and URLs containing user credentials are blocked before forwarding request bodies or custom authentication headers. Configure the approved final endpoint directly when a service redirects elsewhere. This guard is also installed on supplied sessions, while preserving existing response hooks.

## LLMs and Agents

| Task | Start here |
| --- | --- |
| Run prompts from Python | [Configure LLMAgent](#llmagent), then use [DataFrame](#promptdataframe) or [document prompts](#promptdocuments) |
| Give an assistant reusable Fyron knowledge | [Install the Fyron skill](../agent-skill.md) |
| Read the packaged instructions | [SKILL.md](../ai/fyron-skill/SKILL.md) |
| Ask an assistant to build a workflow | [AI Assistant Guide](../agents.md#quick-start-prompt) and [prompt recipes](../agents.md#hands-on-prompt-recipes) |
| Preserve the source of generated evidence | [FHIR LLM Evidence example](../examples/fhir-llm-extracted-evidence.md) |
| Record inputs, settings, and outputs | [Audit & Provenance](audit.md#minimal-example) |

See [Safe Network Diagnostics](../diagnostics.md) for logging, error handling, batch outcome counts, and sensitive-result handling.

## Responsible Use Pattern

- Keep prompts explicit and reusable.
- Store the source text/file identifier with every generated answer.
- Review outputs before using them as labels or report text.
- Use deterministic code for final statistics and clinical endpoints.
- Avoid sending sensitive data to external providers unless the deployment has been approved.

## Import

```python
from fyron import LLMAgent
```

## `LLMAgent`

```python
agent = LLMAgent(
    provider="openai",
    api_key="...",
    model="gpt-4.1-mini",
)
```

### Constructor Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `provider` | no | `str | None` | env `LLM_PROVIDER` or `"openai"` | `"openai"`, `"anyllm"`, or `"custom"`. |
| `base_url` | no | `str | None` | env `LLM_BASE_URL` or OpenAI URL | API base URL or custom endpoint. |
| `api_key` | conditionally | `str | None` | env `LLM_API_KEY` | Required for `openai` and `anyllm` unless `auth_required=False`. |
| `model` | no | `str | None` | env `LLM_MODEL` or `"gpt-4.1-mini"` | Model name. |
| `timeout` | no | `int | None` | env `LLM_TIMEOUT` or `30` | Request timeout. |
| `extra_headers` | no | `dict | None` | `None` | Additional HTTP headers. |
| `auth_required` | no | `bool | None` | provider-dependent | Whether missing API key should raise. |
| `verify_ssl` | no | `bool` | `True` | Verify TLS certificates. |

## `prompt` / `chat`

Sends one prompt. `chat` is an alias for `prompt`.

```python
response = agent.prompt("Summarize the cohort in three bullet points.")
```

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `user_prompt` | yes | none | Prompt text. |
| `image_path` | no | `None` | Optional image path for multimodal mode. |
| `file_path` | no | `None` | Optional file path for multimodal/file mode. |
| `mode` | no | `"text"` | `"text"` or a provider-supported multimodal mode. |

Returns the model response as a string.

## `prompt_dataframe`

Runs a prompt over a DataFrame text column and appends an output column.

```python
out = agent.prompt_dataframe(
    df=notes_df,
    text_col="note_text",
    prompt="Extract clinically relevant adverse events.",
    output_col="adverse_events",
    output_csv="notes_with_adverse_events.csv",
)
```

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `df` | yes | none | Input DataFrame. |
| `text_col` | yes | none | Column containing text. |
| `prompt` | yes | none | Prompt or instruction prepended/appended to each row. |
| `output_col` | no | `"llm_output"` | Name of generated output column. |
| `output_csv` | no | `None` | Optional CSV path to write results. |
| `format_func` | no | `None` | Callable to format prompt per row. |
| `image_col` | no | `None` | Column containing image paths. |
| `file_col` | no | `None` | Column containing file paths. |
| `mode` | no | `"text"` | Text or multimodal mode. |

Aliases: `prompt_df`, `run_prompt_on_dataframe`. Lower-level method: `run_on_dataframe`.

## `prompt_documents`

Runs a prompt over a list of text strings or file paths.

```python
results = agent.prompt_documents(
    documents=["note text", "/path/to/report.txt"],
    prompt="Summarize clinically relevant findings.",
    output_csv="doc_summaries.csv",
)
```

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `documents` | yes | none | List of text strings or file paths. |
| `prompt` | yes | none | Prompt applied to each document. |
| `output_csv` | no | `None` | Optional CSV output. |
| `mode` | no | `"text"` | Text or multimodal mode. |

Alias/lower-level method: `run_on_documents`.

## `describe_python_file`

Generates a methods-style markdown description of a Python file.

```python
md = agent.describe_python_file(
    file_path="src/project/pipeline.py",
    output_md="docs/methods_pipeline.md",
)
```

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `file_path` | yes | none | Python file to describe. |
| `output_md` | yes | none | Markdown file to write. |
| `prompt` | no | `None` | Custom prompt. |

Returns generated markdown text.

## `prompt_directory`

Runs a prompt over files in a directory.

```python
results = agent.prompt_directory(
    input_dir="notes",
    prompt="Extract diagnoses.",
    glob="*.txt",
)
```

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `input_dir` | yes | none | Directory to scan. |
| `prompt` | yes | none | Prompt applied to each file. |
| `glob` | no | `"*.txt"` | File pattern. |
| `mode` | no | `"text"` | Text or multimodal mode. |

Alias: `run_on_directory`.

## Practical Tips

- Do not send protected health information to external APIs unless your deployment and agreements allow it.
- Use `output_csv` for batch prompts so runs are auditable.
- Keep prompts version-controlled when using LLM outputs in research workflows.
- Treat LLM outputs as extracted/narrative assistance, not ground truth.
