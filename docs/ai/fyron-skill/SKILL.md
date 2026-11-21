---
name: fyron
description: Use Fyron for local-first clinical data science workflows: FHIR REST/SQL extraction, DICOM and imaging inputs, cohort construction, BOA features, statistics, survival, ML validation, publication plots, reporting, and provenance.
---

# Fyron

Use this skill when a user asks an assistant to build, review, or explain a clinical data science workflow with Fyron. Fyron is a Python toolkit for inspectable healthcare research code: FHIR, DICOM, imaging, cohorts, statistics, survival analysis, ML validation, plotting, and provenance.

The operating style is simple: choose the smallest public Fyron API that fits the task, keep clinical assumptions visible, write auditable artifacts, and avoid hidden automation around patient data.

## First Move

Before writing code, identify the workflow:

| User intent | Start with |
| --- | --- |
| FHIR API extraction | `fyron.FHIRRestClient`, `fyron fhir-rest`, `references/fhir-rest.md` |
| SQL-backed FHIR tables | `fyron.FHIRSQLClient`, `fyron.fhir.sql`, `references/module-map.md` |
| FHIR JSON or write-back bundles | `fyron.fhir.builder`, `fyron.fhir.mapping` |
| DICOMweb or local DICOM/NIfTI | `fyron.DICOMDownloader`, `fyron.imaging`, `references/dicom-imaging.md` |
| OIDC document/PDF downloads | `fyron.DocumentDownloader`, `fyron document-download` |
| BOA/body-composition features | `fyron.boa_extraction`, `fyron.boa_radiomics` |
| Cohorts and endpoints | `fyron.cohort`, `fyron.phenotyping`, `fyron.clinical_codes`, `fyron.dataframe` |
| Table 1, tests, effect sizes | `fyron.descriptive`, `fyron.statistics`, `fyron.reporting` |
| Survival analysis | `fyron.survival`, `fyron.validation.survival` |
| ML and validation | `fyron.ml`, `fyron.preprocessing`, `fyron.validation`, `fyron.explainability` |
| Publication figures | `fyron.plotting`, `references/plotting.md` |
| Reproducibility | `fyron.audit`, `fyron audit-manifest` |

If the task spans multiple areas, make a short plan first and name the artifact outputs: CSV, JSON, PNG/SVG, notebook, report, or provenance manifest.

## Install

Prefer `uv` when the project already uses it:

```bash
uv add fyron
uv add "fyron[all]"
```

Use targeted extras for lean installs:

```bash
uv add "fyron[ml,statistics,descriptive,validation,explainability]"
uv add "fyron[survival,survival-ml]"
uv add "fyron[dicom-seg,visualization,radiomics]"
```

With pip:

```bash
pip install "fyron[all]"
```

See `references/install-extras.md` for the full extra map.

## Public Docs

Use the public docs as the source of truth:

- Modules: https://docs.fyron.bitsandflames.ai/modules/
- Examples: https://docs.fyron.bitsandflames.ai/example-gallery/
- Function lookup: https://docs.fyron.bitsandflames.ai/function-reference/
- Complete reference: https://docs.fyron.bitsandflames.ai/reference/
- AI assistant guide: https://docs.fyron.bitsandflames.ai/agents/

## Coding Rules

Documents reuse `Auth(auth_type="device_code", auth_url=..., client_id=...)` or
`Auth.client_credentials(...)`. For strict PDF retrieval, use `require_pdf=True`
and `allow_redirects=False`; exact file destinations use `output_path`. The CLI
defaults to 90-second requests, no redirects, and verified skips. Use
`--client-secret-env` for secrets and `--overwrite` only for intentional replacement.
PDF signature/type validation does not prove full PDF validity or clinical correctness.

- Prefer documented public APIs over private helpers.
- Keep examples synthetic or clearly de-identified.
- Validate required columns, array lengths, image dimensions, masks, and date columns before analysis.
- Keep event coding explicit; for survival, use `event=1` for event and `event=0` for censored unless the user states otherwise.
- Do not invent clinical defaults, study inclusion criteria, FHIR profiles, or statistical assumptions.
- Return inspectable tables, figures, JSON manifests, and saved scripts rather than only prose.
- Use Matplotlib-based Fyron plotting helpers for figures.
- Add provenance for serious analysis.
- Keep optional dependencies behind extras and report the exact install command when something is missing.
- Warn before sending patient data, private documents, or endpoint responses to a non-local LLM.

## Canonical Patterns

FHIR REST:

```python
from fyron import FHIRRestClient

client = FHIRRestClient(base_url="https://fhir.example.org/fhir", bearer_token=token)
patients = client.search_df("Patient", params={"_count": "100"}, max_pages=2)
```

Cohort table:

```python
from fyron import cohort

analysis = cohort.build_time_to_event_table(
    patients,
    index_date_col="diagnosis_date",
    event_date_col="death_date",
    last_followup_col="last_followup_date",
    patient_id_col="patient_id",
)
```

Table 1:

```python
from fyron import descriptive as fd

table_one = fd.create_table_one(
    analysis,
    group_col="outcome_group",
    include_smd=True,
)
```

Image previews:

```bash
fyron dataset-curate-previews --input-dir imaging_exports/ --output-dir curate_previews/
```

Plotting:

```python
from fyron import plotting as fp

fig, ax = fp.plot_directional_ratio_rows(
    data=ratios,
    feature_col="feature",
    ratio_col="hazard_ratio",
    ci_low_col="ci_low",
    ci_high_col="ci_high",
    p_value_col="p_value",
    ratio_label="Hazard ratio",
)
```

Provenance:

```python
from fyron import audit

manifest = audit.create_provenance_manifest(
    title="Analysis",
    inputs=["data/features.csv"],
    outputs=["results/table_one.csv", "figures/km.png"],
    parameters={"endpoint": "overall_survival"},
)
audit.write_manifest(manifest, "results/provenance.json")
```

## Assistant Workflow

1. Restate the task as a small Fyron workflow.
2. Ask only for missing clinical definitions that would change results.
3. Choose the module using `references/module-map.md`.
4. Write code that validates inputs before analysis.
5. Save artifacts into predictable folders such as `data/`, `results/`, `figures/`, and `manifests/`.
6. Include runnable commands.
7. Add a short review checklist for the user.

## Stop Conditions

Pause and ask for review when:

- cohort inclusion/exclusion criteria are ambiguous,
- endpoint coding or censoring is unclear,
- features could leak future information,
- real patient identifiers might enter prompts or logs,
- a workflow would write back to a live FHIR server,
- model output could affect patient care,
- regulatory-grade DICOM/FHIR validation is expected.

## Reference Files

Use the compact references when this skill is installed as a folder:

- `references/module-map.md`
- `references/install-extras.md`
- `references/cli-recipes.md`
- `references/fhir-rest.md`
- `references/dicom-imaging.md`
- `references/plotting.md`
- `references/safety.md`

## Install This Skill

The folder includes a local installer:

```bash
python install.py --target codex
python install.py --target claude --project-dir /path/to/project
python install.py --target cursor --project-dir /path/to/project
python install.py --target all --project-dir /path/to/project
```

Inside a `uv`-managed project, prefer:

```bash
uv run python fyron-skill/install.py --target codex
uv run python fyron-skill/install.py --target claude --project-dir .
uv run python fyron-skill/install.py --target cursor --project-dir .
```

Codex receives the native skill folder. Claude receives `CLAUDE.md` guidance, a
`.claude/fyron-skill/` copy, and a single `fyron-claude-project-knowledge.md`
bundle for Claude Project knowledge. Cursor receives `.cursor/rules/fyron.mdc`
plus reference files.

## Authentication documentation

Use the [authentication guides](../../authentication/index.md) for provider-neutral FHIR REST, DICOMweb, document and PostgreSQL examples. Let the site administrator determine the permitted method, client, scopes and endpoints. Distinguish native environment defaults from explicitly loaded example variables and Python support from CLI support. SQL uses PostgreSQL credentials, not the HTTP Auth object. Never include institutional endpoints, tokens or credentials in shared examples.

Explain token renewal as demand-driven, not background keep-alive. Static Bearer tokens do not renew. Device flow can refresh cached credentials; `allow_reauthentication=False` permits refresh but fails when browser approval is required. Client credentials obtain new access tokens using the registered credentials. Keep shared Auth alive across the operation and never imply SQL credentials renew through HTTP Auth.

## Licensing

Current project source uses CC BY-NC 4.0. Describe it as source available for noncommercial use with attribution, not OSI open source or research-only. Preserve third-party licenses and earlier MIT permissions. Never rewrite historical release licensing or replace published artifacts; a future distribution of the license change needs a new version. Keep package metadata and documentation consistent.

For SQL diagnostics, configure the shared Fyron console logger and use
`FHIRSQLClient(log_queries=True)` for timed INFO activity and row/chunk counts.
`SQLQueryError` provides controlled PostgreSQL-code-based troubleshooting hints.
Never log SQL, bound values or remote database error text. Early stream closure
is incomplete; failed batches must not be presented as successful partial results.
No automatic retries or transaction rollback are implied.

DICOM full-study folders retain hashes by default. `append_study_hash=False`
uses exact explicit labels from `study_folder_name` / `study_folder_name_col`;
reject unsafe labels and cross-study/case collisions before requests. The option
works in single-study, DataFrame, alias and worker routes for DICOM/NIfTI.
`write_completion_record=False` on DICOMDownloader disables per-series JSON;
`save_study_manifest=False` separately disables the study summary. CLI equivalents
are `--no-study-hash`, `--no-completion-record`, and `--no-study-manifest`.
No-record reruns retain existing-file protection; explicit overwrite is required.
Documents already support exact `document_id` / `id_col`, flat output and optional
completion JSON. Do not add a second naming or token-cache implementation.

Client reliability: keep DataFrame returns by default. DICOM and document batch
methods optionally return `data` and `report.rows` / `report.summary` using
`return_report=True`; task counts must remain distinct from series/file counts.
DICOM exposes opt-in `request_timeout` and `parallel_job_timeout`; SQL exposes
opt-in `statement_timeout` and `lock_timeout` in seconds on owned connections.
SQL partition exports require matching query/config fingerprints and file digests
for skips; preserve unverified files unless overwrite is explicit. Completion
JSON remains optional. Documents accept optional `expected_content_types` and
use bounded scheduling. Cancelled batches must raise, clean staging, preserve
published files and report unfinished work honestly. Do not mutate or close
borrowed HTTP sessions. Guard redirects per request and suppress upstream raw
transport diagnostics only inside Fyron operations. GET retry policies can honor
429/Retry-After; do not automatically retry writes, permission failures or SQL.

The four client guides link to dedicated parameter subpages under FHIR REST,
FHIR SQL, DICOMDownloader and DocumentDownloader. They enumerate every public
client argument, default, keyword-only binding and operational choice. Signatures
are generated from source by `scripts/generate_client_parameters.py`; update its
behavior descriptions when changing client options. Run it with `--check` to
verify synchronization. The documentation build regenerates these pages.

Use `fyron.llm.load_prompt_templates` and `LLMAgent.run_prompts_on_dataframe` for
named text prompts or grouped documents. Only explicitly selected context columns
accompany text. Keep identifiers in local metadata. Use `summarize_dataframe`
for reviewed answers, retain unsuccessful rows and inspect statuses and source
mappings. Both methods default to sequential requests; `max_workers` enables
bounded parallel HTTP requests with independent worker sessions.
