# AI Assistant Guide

You can use Fyron with ChatGPT, Claude, Cursor, Codex, or another coding assistant even when the assistant only sees the public documentation. The most useful pattern is simple: give the assistant your study goal, the shape of your data, and the Fyron docs pages it should use before it writes code.

This page gives you copy-paste prompts and module shortcuts so an assistant can help build scripts, notebooks, figures, Curate preview folders, and provenance manifests without guessing.

If your assistant supports reusable skills or project knowledge, install the [Fyron Skill](agent-skill.md). It packages the same guidance into a Codex/Claude-friendly folder with compact references for modules, install extras, CLI recipes, FHIR REST, DICOM/imaging, Curate, plotting, and safety.

Read the packaged [SKILL.md](ai/fyron-skill/SKILL.md) to inspect the instructions. For prompts executed from Python over text, files, or tables, use the [LLM module](modules/llm.md).

## Quick Start Prompt

Copy this into your assistant before asking for code:

```text
Use Fyron for this task. Please rely on the public docs:
- Modules: https://fyron.bitsandflames.ai/modules/
- Examples: https://fyron.bitsandflames.ai/example-gallery/
- Function lookup: https://fyron.bitsandflames.ai/function-reference/
- Complete reference: https://fyron.bitsandflames.ai/reference/

Use public Fyron APIs only. Keep clinical assumptions explicit. Use synthetic or de-identified examples. Validate required columns before analysis. Return inspectable tables, figures, and provenance files.
```

Then add your concrete request, for example:

```text
I have a cohort CSV with patient_id, diagnosis_date, last_followup_date,
death_event, age, sex, stage, and a CT feature table. Create a Fyron notebook
that builds survival columns, creates a Table 1, plots Kaplan-Meier curves,
fits a Cox model, and writes a provenance manifest.
```

## What To Give The Assistant

The assistant works much better when you provide:

| Input | Example |
| --- | --- |
| Goal | "Create a survival analysis workflow for an NSCLC imaging cohort." |
| Data shape | column names, file types, one-row-per-patient or long table |
| Outcome | event coding, follow-up dates, censoring rule, endpoint name |
| Artifacts | CSV tables, PNG/SVG figures, notebook, manifest, Curate export |
| Constraints | local-only, no PHI, no hidden clinical defaults, no external upload |

You do not need to paste private data. A small synthetic table with the same column names is usually enough.

## Choose The Right Fyron Page

| Task | Tell the assistant to use |
| --- | --- |
| FHIR extraction | [FHIR](modules/fhir.md), [FHIR REST](modules/fhir/rest.md), [FHIR examples](example-gallery.md) |
| DICOMweb downloads | [DICOM](modules/dicom.md), [DICOMDownloader](modules/dicom/downloader.md) |
| DICOM/NIfTI image QC | [Imaging](modules/imaging.md), [BOA Visualization](modules/visualization.md) |
| Curate image review | [Fyron Curate](applications/curate.md), [Unified CLI](modules/cli.md) |
| CT/MRI preview PNG folders | [BOA Visualization](modules/visualization.md#curate-preview-preparation), [Fyron Curate](applications/curate.md) |
| BOA features or radiomics | [BOA](modules/boa.md), [BOA Extraction](modules/boa-extraction.md), [BOA Radiomics](modules/boa-radiomics.md) |
| Cohort and endpoints | [Cohort Tables](modules/cohort.md), [Phenotyping](modules/phenotyping.md) |
| Table 1 and summaries | [Descriptive Analysis](modules/descriptive.md), [Reporting](modules/reporting.md) |
| Statistics | [Statistics](modules/statistics.md), [Manuscript Statistics Workflow](examples/manuscript-statistics-workflow.md) |
| Survival analysis | [Survival Analysis](modules/survival.md), [Clinical Plotting](modules/plotting.md) |
| ML and validation | [Machine Learning](modules/ml.md), [Model Validation](modules/validation.md), [Explainability](modules/explainability.md) |
| Figures | [Clinical Plotting](modules/plotting.md), [Visual Figure Gallery](examples/visual-figure-gallery.md), [Colors And Styles](colors.md) |
| Provenance | [Audit & Provenance](modules/audit.md), [Unified CLI](modules/cli.md) |

## Hands-On Prompt Recipes

### Build A Cohort Script

```text
Using Fyron, write a Python script that reads cohort.csv and features.csv,
validates patient_id uniqueness, joins the tables, builds time/event columns,
prints a cohort profile, and saves analysis_cohort.csv. Use the docs at
https://fyron.bitsandflames.ai/modules/cohort/ and keep all column names explicit.
```

### Prepare Images For Curate

```text
Using Fyron, create a terminal workflow for preparing a nested folder of CT/MRI
or X-ray exports for Fyron Curate. Use fyron dataset-curate-previews, write PNGs
to curate_previews/, explain which formats are supported, and include the command
to start Curate locally.
```

### Create Manuscript Figures

```text
Using Fyron plotting, create a figure script for Kaplan-Meier curves, a Table 1
summary figure, and a directional ratio rows plot. Use the visual figure gallery
to choose suitable functions. Save SVG and PNG outputs in figures/.
```

### Add Provenance

```text
Add a Fyron provenance manifest to this workflow. It should record input files,
output files, endpoint settings, model parameters, random seed, and Fyron version.
Keep the manifest JSON-readable and suitable for a manuscript supplement.
```

## Review Checklist

Before you use AI-generated Fyron code on real data, check:

- column names match your files,
- event coding is explicit, usually `1 = event` and `0 = censored`,
- time windows and censoring dates match your protocol,
- train/test splits do not leak future information,
- image geometry and orientation are checked before visual comparison,
- examples contain no PHI, accessions, MRNs, or private endpoint URLs,
- outputs are saved as tables, figures, and manifests that can be reviewed.

## Related Pages

- [Getting Started](getting-started.md)
- [Fyron Skill](agent-skill.md)
- [Modules Overview](modules/index.md)
- [Function Reference](function-reference.md)
- [Complete Function Reference](reference/index.md)
- [Using Fyron In Research](repository-trust.md)

## Authentication documentation

Use the [authentication guides](authentication/index.md) for provider-neutral FHIR REST, DICOMweb, document and PostgreSQL examples. Let the site administrator determine the permitted method, client, scopes and endpoints. Distinguish native environment defaults from explicitly loaded example variables and Python support from CLI support. SQL uses PostgreSQL credentials, not the HTTP Auth object. Never include institutional endpoints, tokens or credentials in shared examples.

Explain token renewal as demand-driven, not background keep-alive. Static Bearer tokens do not renew. Device flow can refresh cached credentials; `allow_reauthentication=False` permits refresh but fails when browser approval is required. Client credentials obtain new access tokens using the registered credentials. Keep shared Auth alive across the operation and never imply SQL credentials renew through HTTP Auth.

## Licensing

Current project source and Curate frontend/backend use CC BY-NC 4.0. Describe it as source available for noncommercial use with attribution, not OSI open source or research-only. Preserve third-party licenses and earlier MIT permissions. Never rewrite historical release licensing or replace published artifacts; a future distribution of the license change needs a new version. Keep package metadata, Docker labels, Curate's public license files and documentation consistent.
