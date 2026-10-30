---
name: fyron
description: Use Fyron for interoperable clinical data science workflows: FHIR REST/SQL extraction, FHIR JSON bundles, DICOM/DICOM SEG, imaging QC, BOA extraction/radiomics/visualization, cohort construction, filter-flow tracking, descriptive statistics, survival analysis, ML, validation, explainability, plotting, reporting, and provenance.
---

# Fyron Skill

Use Python 3.11 or newer. The configured PyRadiomics workflow uses Python 3.11.

BOA tissue areas default to `tissues.nii.gz` (muscle=1, SAT=3, VAT=4, IMAT=5).
Anatomical body-region masks are not tissue fallbacks; custom masks require
explicit labels. Vertebral ranges use `[min_slice_idx, max_slice_idx)`.
Curate binds published ports to loopback and keeps PostgreSQL internal.
Original files and reviewed DICOM series are immutable; retry interrupted
uploads with the same batch before export. Use a single local API process.

For everyday cohort tracking, use `FlowTracker(id_col=..., progress=True)` and
`flow.add(label, dataframe)`. Optional `with flow.step(label, kind="query")`
contexts accept `step.result(result)` and do not change the cohort baseline.
Use `cohort_table()` for completed selections and `to_dataframe()` for all
activities. Keep console labels nonidentifying; never log patient values.

BOA cohort helpers and FHIR DataFrame queries support `return_report=True`, returning
`data` plus `report.rows` and `report.summary`. BOA reports contain sensitive case
identifiers and label outcomes; case identifiers must be unique. FHIR reports
distinguish execution completion from exhausted pagination. Parallel input metadata
uses original values; collisions with resource columns raise rather than overwrite.
Failed FHIR DataFrame queries never return a successful partial result.

Physical imaging volumes require 3D data and known positive finite millimetre
spacing. Array-based distances require array-axis spacing (ZYX for SimpleITK arrays);
QC `spacing_xyz` retains XYZ semantics. Phenotype combination requires unique
patient keys and one binary flag; summaries reject conflicting patient flags or
groups. Absence of evidence is not confirmed clinical absence. Fit preprocessing
on training data only; unseen categories use rare only if that level was fitted.
Keep provenance manifests internal; publication summaries need explicit reviewed
field selection. See `examples/research_contracts.py` for a synthetic workflow.

Public modules remain evolving. Follow `docs/reliability.md`: distinguish configured
CI from verified support, preserve the docstring ratchet, and exercise built wheels
outside the checkout. Never install all extras to conceal an isolated-extra failure.
Keep executable examples synthetic and seeded, with explicit cohort exclusions.

Before survival fitting, use `fyron.cohort.audit_time_to_event_endpoint` to review
endpoint quality and `audit_cohort_join` to inspect key coverage/multiplication.
Unresolved endpoints are not observed censoring. Administrative cutoffs cap existing
follow-up, never create it. Reuse private `fyron._dates` contracts: strict endpoint
parsing, opt-in strict generic date parsing, exact index alignment, UTC elapsed
time for aware dates, and rejection of naive/aware mixtures. Month/year units are
fixed elapsed durations. Row-level audits remain sensitive research outputs.

Use `docs/survival-workflow.md` for the recommended endpoint-to-plot workflow.
Keep endpoint construction in cohort, explicit feature preparation in preprocessing,
fitting in survival, prediction evaluation in validation, and plotting through
`fyron.plotting`. Existing plotting imports remain compatible. Reuse private
`fyron._survival_data` checks and fitting-cohort preparation. KM/RMST/Cox support
zero durations; AFT, boosting, and validation require positive durations. Outcomes
must be finite and events binary before conversion. Cox/AFT return the exact
`training_df` with original indices and fitting counts; unrelated missing columns
must not alter that cohort. Do not silently impute outcomes or predictors.

Network diagnostics use `fyron._diagnostics` controlled events. Never log remote
exception text, clinical identifiers, URLs, SQL, prompts, or response bodies,
even at DEBUG. Identifying result columns remain sensitive. Batch completion
does not establish that all downloads succeeded; inspect errors and skips.
Download skips require verified completion records. Preserve unverified files
unless overwrite is explicit. S3 existence checks raise on permission/network
errors; listings follow pagination and apply limits to matching results globally.

Use this skill when an LLM or agent needs to choose and apply the right Fyron tools for clinical data science, imaging AI, FHIR/DICOM interoperability, BOA workflows, manuscript-ready analysis, or reproducible research pipelines.

Fyron is intentionally explicit: prefer DataFrame-first APIs, inspectable JSON/dicts, Matplotlib figures, and CLI commands that write auditable files. Do not hide clinical or statistical assumptions behind opaque automation.

## First Decision

Fyron 0.3.12 adds `worker_auth_timeout=120` to FHIR/DICOM clients and
`parallel_job_timeout=300` to FHIR. Use guarded script entrypoints for spawned
workers. Authentication leases stay in workers; renewal and credentials stay in
the parent. Failed parallel extraction is not a complete dataset, even when a
streaming consumer received earlier bundles. Diagnostic logs must omit clinical
values and credentials.

For service accounts, use `Auth.client_credentials(client_id=..., client_secret=...,
auth_url=<OIDC issuer>, scope=<approved scopes>)`, or an explicit `token_endpoint`.
FHIR and DICOM workers coordinate Bearer renewal. This supports OAuth client
credentials with shared secrets, not ID-token validation or `private_key_jwt`.
Keep provider examples generic and credentials outside source control.

For browser-approved FHIR/DICOMweb sign-in, use `Auth(auth_type="device_code",
auth_url=<OIDC issuer>, client_id=<registered client>)` and pass it as `auth`.
Device auth coordinates refresh across Fyron workers. DICOM `Auth.token_env()`
also supports parallel downloads with parent-coordinated Bearer renewal. Explicit DICOM `auth`
overrides environment Basic credentials; do not combine explicit auth methods.
Token caching is opt-in and contains sensitive, unencrypted credentials. Use
`allow_reauthentication=False` with an established cache for unattended jobs.

Document downloads reuse shared `Auth` through `DocumentDownloader(auth=...)`.
Use `Auth(token_cache=...)` / `--token-cache` for opt-in device-token caching,
separate from document completion records. Unattended use requires an established
cache and `allow_reauthentication=False` / `--no-reauthentication`.
Use `document_id=...` / `--document-id` for single documents, or keyword-only
`id_col=...` / `--id-col` for table batches. Preserve string IDs and leading zeros;
reject unsafe or case-insensitively duplicate IDs before requests. Results retain
the URL-hash `download_id` and add the effective `document_id`.
Use `flat_output=True` / `--flat-output` for one output folder with deterministic
URL-hash filenames; the results `path` column contains absolute file paths.
Use `write_completion_record=False` / `--no-completion-record` to omit document
JSON completion records. Keep existing-file protection: without a valid record,
reruns require explicit overwrite rather than silently skipping unverified files.
Use `require_pdf=True`, `allow_redirects=False`, and an explicit timeout for PDF
endpoints. `download_url(..., output_path=...)` supports an exact file destination.
The `document-download` CLI defaults to 90-second requests, no redirects, and
verified skips; `--overwrite` permits intentional replacement. Supply client secrets
through `--client-secret-env`, never command-line values. PDF checks validate media
type and signature, not full syntax or clinical correctness.

Choose the workflow by user intent:

| Intent | Use |
| --- | --- |
| Query live FHIR APIs | `fyron.FHIRRestClient`, `fyron fhir-rest` |
| Query SQL-backed FHIR tables | `fyron.FHIRSQLClient`, `fyron.fhir.sql` |
| Build FHIR JSON resources or transaction bundles | `fyron.fhir.builder` |
| Convert reviewed CSV/DataFrame rows to FHIR | `fyron.fhir.mapping`, `fyron fhir-build-bundle` |
| Download DICOMweb data | `fyron.DICOMDownloader`, `fyron dicom-download` |
| Download documents with OIDC device/service-account auth | `fyron.DocumentDownloader`, `fyron document-download` |
| Export synthetic DICOM/NIfTI volumes | `fyron.dicom.synthetic`, `fyron synthetic-dicom` |
| Write DICOM SEG from source DICOM and masks | `fyron.dicom.seg`, `fyron dicom-seg` |
| Read images or normalize CT/MR | `fyron.imaging` |
| Check image geometry, mask alignment, volumes, intensity ranges | `fyron.imaging.qc`, `fyron imaging-qc` |
| Compare segmentations | `fyron.imaging.segmentation` |
| Prepare nnU-Net v2 or YOLO training datasets | `fyron.datasets`, `fyron dataset-nnunetv2`, `fyron dataset-yolo-classify`, `fyron dataset-yolo-detect` |
| Prepare CT/MRI folders for Curate review | `fyron.visualization.prepare_curate_image_previews`, `fyron dataset-curate-previews` |
| Extract BOA body composition features | `fyron.boa_extraction`, `fyron boa-extract` |
| Extract BOA radiomics | `fyron.boa_radiomics`, `fyron boa-radiomics` |
| Render BOA collages or aligned CT/MR difference heatmaps | `fyron.visualization` |
| Read/write CSV, Excel, JSON, Teable, S3 | `fyron.core`, `fyron.core.s3` |
| Derive ICD-10/OPS groups, MDC partitions, Charlson scores, or encounter status | `fyron.clinical_codes` |
| Derive local code indicators, date differences, age, or time-window flags | `fyron.dataframe` |
| Join patient tables and outcome definitions | `fyron.cohort` |
| Define transparent phenotypes | `fyron.phenotyping` |
| Missingness, imputation, encoding, leakage checks | `fyron.preprocessing` |
| Descriptive analysis and Table 1 | `fyron.descriptive`, `fyron.reporting` |
| Track inclusion/exclusion flow | `fyron.flow.FlowTracker`, `fyron.flow.track_filter` |
| Statistical tests, FDR correction, regression tables, model-comparison tests, effect sizes, bootstrap metrics | `fyron.statistics` |
| Survival analysis | `fyron.survival` |
| Survival model validation | `fyron.validation.survival` |
| Classification ML | `fyron.ml` |
| Feature selection | `fyron.feature_selection` |
| Model validation | `fyron.validation` |
| Censoring-aware survival validation | `fyron.validation` with `fyron[survival-ml]` |
| Model explainability, PDP, SHAP tables | `fyron.explainability` |
| Clinical plots and paper figures | `fyron.plotting` |
| Provenance manifests and file hashes | `fyron.audit`, `fyron audit-manifest` |
| Curate local image cohorts | `fyron curate` with `fyron[curate]` |
| LLM-assisted prompting over docs/tables | `fyron.llm` |

## Install Extras

Default install:

```bash
uv add fyron
```

Common extras:

```bash
uv add "fyron[all]"
uv add "fyron[excel,s3]"
uv add "fyron[ml,statistics,descriptive,validation,explainability]"
uv add "fyron[survival,survival-ml]"
uv add "fyron[dicom-seg,visualization,radiomics]"
uv add "fyron[feature-selection]"
uv add "fyron[curate]"
```

Use `fyron[all]` for full local research workstations, tutorials, and feature exploration. For servers, CI jobs, and missing-dependency errors, prefer the targeted extra and tell the user the exact `uv add "fyron[extra]"` command.

## Canonical API Patterns

### FHIR REST

Use friendly REST names:

```python
from fyron import FHIRRestClient

client = FHIRRestClient(base_url="https://fhir.example.org/fhir", bearer_token=token)
patients = client.search_df("Patient", params={"_count": "100"}, max_pages=2)
observations = client.search_df_from(
    cohort,
    resource="Observation",
    column_map={"subject": "patient_id"},
    params={"code": "http://loinc.org|718-7"},
    max_pages=1,
)
```

Use `query_df` names for SQL workflows, not REST-first docs.

### FHIR Builder And Mapping

Builders return plain dictionaries:

```python
from fyron.fhir import builder as fb

obs = fb.build_observation(
    subject="Patient/P001",
    code=fb.loinc("718-7", "Hemoglobin"),
    value=fb.ucum_quantity(13.2, "g/dL"),
)

bundle = fb.build_bundle([obs], bundle_type="collection")
report = fb.fhir_validation_report(bundle)
```

Mapping functions return:

```python
{
    "bundle": bundle,
    "resources": resources,
    "summary": summary,
    "validation": validation,
}
```

Use mapping for reviewed extraction tables, BOA measurements, imaging features, and LLM outputs that need FHIR write-back.

### DICOM SEG

Do not claim valid DICOM SEG export from NIfTI alone. Require source DICOM images:

```python
from fyron.dicom.seg import (
    load_source_dicom_series,
    read_segment_descriptions,
    write_dicom_seg,
    summarize_dicom_seg,
)

source_images = load_source_dicom_series("dicom/")
segments = read_segment_descriptions("segments.json")
write_dicom_seg(mask, source_images, "mask.seg.dcm", segments)
summary = summarize_dicom_seg("mask.seg.dcm", source_images=source_images)
```

### BOA Extraction

Use `boa_extraction` for measurement tables and `boa_radiomics` for texture/shape features:

```python
from fyron.boa_extraction import extract_boa_cohort_features

features = extract_boa_cohort_features(
    cohort_folder="boa/",
    include_body_regions=True,
    include_total=True,
    include_aortic_experimental=False,
)
```

For body composition indices, keep formulas explicit:

- `sarcopenia_index_si = muscle / bone`
- `myosteatosis_fat_index_mfi = (imat / tat) * 100`
- `visceral_fat_index_vfi = vat / sat`
- `eat_pat_ratio = eat / pat` only for thoracic or ventral/abdominal cavity contexts when available

SMA, IMATI, and VATI are area-style L3 markers; do not require height unless the API explicitly asks for height-normalized indices.

### Descriptive And Statistical Analysis

Use descriptive tables before modeling:

```python
from fyron import descriptive as fd

table_one = fd.create_table_one(
    cohort,
    group_col="outcome_group",
    include_smd=True,
)
```

Use `fyron.statistics` for explicit tests, Benjamini-Hochberg FDR correction, regression tables, model-comparison tests, effect sizes, and bootstrap intervals. Record assumptions and use non-parametric tests when normality is not justified.

### Plotting

Prefer `fyron.plotting` for clinical figures:

```python
from fyron import plotting as fp

fig, ax, table = fp.plot_grouped_bar_with_significance(
    data=cohort,
    x="risk_group",
    y="l3_sma_cm2",
    hue="sex",
    estimator="mean",
    error="sem",
)
```

Plot functions return Matplotlib objects, usually `(fig, ax)` or `(fig, ax, table)` when computations should be auditable.

### Explainability

Use table-first explainability:

```python
from fyron import explainability as fe

importance = fe.permutation_importance_table(model, X_test, y_test, scoring="roc_auc")
pdp = fe.partial_dependence_table(model, X_test, features=["age", "l3_sma_cm2"])
shap_summary = fe.shap_summary_table(model, X_test, background_data=X_train.sample(100))
```

Treat explanations as model inspection, not causal evidence. Always check leakage, missingness, coding artifacts, cohort imbalance, and clinical plausibility.

### Audit

Write provenance for every serious analysis:

```python
from fyron import audit

manifest = audit.create_provenance_manifest(
    title="External validation",
    inputs=["data/features.csv"],
    outputs=["results/metrics.csv"],
    parameters={"model": "locked-rf-v1"},
)
audit.write_manifest(manifest, "results/provenance.json")
```

## CLI Defaults

Use CLI commands for repeatable jobs:

```bash
fyron fhir-rest --base-url "$FHIR_BASE_URL" --resource Patient --output patients.csv
fyron fhir-build-bundle --input observations.csv --mapping mapping.json --resource Observation --subject-col patient_id --output bundle.json
fyron dicom-download --dicom-web-url "$DICOM_WEB_URL" --study-uid "$STUDY_UID" --output-dir dicom_out
fyron synthetic-dicom --volume volume.nii.gz --reference-dicom dicom/ --output-dir synthetic/
fyron dicom-seg --mask mask.nii.gz --source-dicom dicom/ --segments segments.json --output mask.seg.dcm --validate
fyron dataset-curate-previews --input-dir ct_exports/ --output-dir curate_previews/
fyron curate
fyron boa-extract --cohort-folder boa/ --output body_regions.csv --include-body-regions --include-total
fyron boa-radiomics --cohort-folder boa/ --segmentation total --output radiomics.csv
fyron imaging-qc --nifti image.nii.gz --mask mask.nii.gz --output qc.csv
fyron audit-manifest --title "Analysis" --input data/features.csv --output results/metrics.csv --write results/provenance.json
```

Global flags:

```bash
fyron --quiet ...
fyron --verbose ...
fyron --no-color ...
fyron --json-log ...
fyron --no-progress ...
```

Use `fyron spark` only as an opt-in console easter egg.

## Clinical Safety Defaults

- Keep patient identifiers, dates, and source references explicit.
- Do not treat LLM outputs as validated labels unless a human review step is documented.
- For survival, `event=1` means event and `event=0` means censored.
- Check duration values are positive.
- In binary classification, report sensitivity, specificity, balanced accuracy, AUC when probabilities exist, and confusion counts.
- For imbalanced endpoints, expose class weighting or XGBoost `scale_pos_weight`.
- Use Spearman correlation by default for exploratory clinical heatmaps.
- Use hatches or grayscale-safe encodings for manuscript bars.
- For DICOM SEG, preserve source image references and validate segment descriptions before writing.
- For FHIR write-back, distinguish `collection` bundles for local evidence packages from `transaction` bundles for server submission.

## When To Avoid Fyron Automation

Pause and ask for clinical/statistical review when:

- the cohort definition is ambiguous,
- feature leakage is possible,
- FHIR profiles or implementation guides are required,
- regulatory-grade DICOM/FHIR validation is expected,
- a model output would affect patient care,
- LLM-generated labels are being used as ground truth,
- a statistical test depends on assumptions not visible in the data.

## MCP Direction

A future Fyron MCP server should expose stable, file-oriented tools rather than opaque analysis automation. Good tool candidates are:

- `fyron.describe_modules`
- `fyron.recommend_workflow`
- `fyron.build_fhir_bundle_from_csv`
- `fyron.run_fhir_rest_query`
- `fyron.run_dicom_download`
- `fyron.extract_boa_features`
- `fyron.run_imaging_qc`
- `fyron.create_table_one`
- `fyron.create_statistical_plot`
- `fyron.create_audit_manifest`

Keep MCP tools explicit, auditable, and backed by the public Python APIs.


For PostgreSQL cohort extraction, use `FHIRSQLClient.query_df_for_keys` with
ordered `key_columns` and one `{cohort_keys}` block. Composite keys require
`(a, b) IN ({cohort_keys})`; independent `column_map` lists do not preserve pairs.
The method deduplicates complete keys, binds values, and rejects missing keys.
Use `return_report=True` for `data` and a `report` dictionary containing `rows`,
`summary`, and `unmatched_keys` DataFrames. Coverage requires explicit ordered
`result_key_columns`. Unmatched means no rows returned by the query, not an absent
patient. Failures raise without returning partial data. Keep cohort joins explicit,
reports protected, and parallel calls under a guarded script entrypoint.

## Authentication documentation

Use the [authentication guides](../../authentication/index.md) for provider-neutral FHIR REST, DICOMweb, document and PostgreSQL examples. Let the site administrator determine the permitted method, client, scopes and endpoints. Distinguish native environment defaults from explicitly loaded example variables and Python support from CLI support. SQL uses PostgreSQL credentials, not the HTTP Auth object. Never include institutional endpoints, tokens or credentials in shared examples.

Explain token renewal as demand-driven, not background keep-alive. Static Bearer tokens do not renew. Device flow can refresh cached credentials; `allow_reauthentication=False` permits refresh but fails when browser approval is required. Client credentials obtain new access tokens using the registered credentials. Keep shared Auth alive across the operation and never imply SQL credentials renew through HTTP Auth.

## Licensing

Current project source and Curate frontend/backend use CC BY-NC 4.0. Describe it as source available for noncommercial use with attribution, not OSI open source or research-only. Preserve third-party licenses and earlier MIT permissions. Never rewrite historical release licensing or replace published artifacts; a future distribution of the license change needs a new version. Keep package metadata, Docker labels, Curate's public license files and documentation consistent.
