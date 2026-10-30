---
name: fyron
description: Use Fyron for local-first clinical data science workflows: FHIR REST/SQL extraction, DICOM and imaging inputs, cohort construction, BOA features, statistics, survival, ML validation, publication plots, Curate image review, reporting, and provenance.
---

# Fyron

Use this skill when a user asks an assistant to build, review, or explain a clinical data science workflow with Fyron. Fyron is a Python toolkit for inspectable healthcare research code: FHIR, DICOM, imaging, cohorts, statistics, survival analysis, ML validation, plotting, Curate review, and provenance.

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
| CT/MRI/X-ray previews for review | `fyron dataset-curate-previews`, `references/curate.md` |
| Local image cohort review | `fyron curate`, `references/curate.md` |
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
uv add "fyron[curate]"
```

With pip:

```bash
pip install "fyron[all]"
```

See `references/install-extras.md` for the full extra map.

## Public Docs

Use the public docs as the source of truth:

- Modules: https://fyron.bitsandflames.ai/modules/
- Examples: https://fyron.bitsandflames.ai/example-gallery/
- Function lookup: https://fyron.bitsandflames.ai/function-reference/
- Complete reference: https://fyron.bitsandflames.ai/reference/
- Curate: https://fyron.bitsandflames.ai/applications/curate/
- AI assistant guide: https://fyron.bitsandflames.ai/agents/

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

Curate previews:

```bash
fyron dataset-curate-previews --input-dir imaging_exports/ --output-dir curate_previews/
fyron curate
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
- `references/curate.md`
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

Current project source and Curate frontend/backend use CC BY-NC 4.0. Describe it as source available for noncommercial use with attribution, not OSI open source or research-only. Preserve third-party licenses and earlier MIT permissions. Never rewrite historical release licensing or replace published artifacts; a future distribution of the license change needs a new version. Keep package metadata, Docker labels, Curate's public license files and documentation consistent.
