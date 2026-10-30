# Fyron Agent Guide

This file helps LLMs and coding agents choose the right Fyron module and preserve the project style.

## Project Intent

Fyron is a Python toolkit for interoperable healthcare data and AI workflows. Prefer small, explicit functions that keep clinical data transformations inspectable. Do not hide statistical or healthcare assumptions behind opaque abstractions.

## Use the Right Module

| Task | Use |
| --- | --- |
| FHIR REST queries, pagination, auth, bundle processing | `fyron.fhir`, top-level `FHIRRestClient`, `Auth` |
| SQL-backed FHIR tables | `fyron.fhir.sql`, top-level `FHIRSQLClient` |
| Build/write FHIR R4 JSON resources, bundles, LLM evidence, imaging measurements | `fyron.fhir.builder` |
| Map reviewed CSV/DataFrame outputs to FHIR bundles | `fyron.fhir.mapping` |
| DICOMweb downloads | `fyron.dicom`, top-level `DICOMDownloader` |
| Synthetic DICOM/NIfTI export for GAN studies | `fyron.dicom.synthetic` |
| Valid DICOM SEG export from source-referenced masks | `fyron.dicom.seg` with `fyron[dicom-seg]` |
| Local DICOM/NIfTI I/O, CT/MR normalization | `fyron.imaging` |
| Imaging geometry, mask alignment, mask volume, intensity QC | `fyron.imaging.qc` |
| Segmentation overlap, surface, and volume metrics | `fyron.imaging.segmentation` |
| Tiny synthetic cohorts, DICOM/NIfTI, BOA-like demo folders | `fyron.datasets` |
| nnU-Net v2 and YOLO dataset folder preparation | `fyron.datasets` |
| Download reports, PDFs, or URL/file tables | `fyron.documents`, top-level `DocumentDownloader` |
| LLM prompts over DataFrames/documents | `fyron.llm`, top-level `LLMAgent` |
| CSV/Excel/JSON/table I/O, `.env`, Teable cohorts, S3 storage | `fyron.core`, top-level I/O helpers, `fyron.core.s3` |
| Console messages, structured logging, run headers/footers | `fyron.console`, `fyron.banner` |
| ICD-10/OPS groups, MDC partitions, Charlson Comorbidity Index, encounter status | `fyron.clinical_codes` |
| Local code indicators, date differences, age/time-window columns | `fyron.dataframe` |
| Join patient tables and build `time`/`event` | `fyron.cohort` |
| Track inclusion/exclusion filters and text cohort flows | `fyron.flow` |
| Rule-based clinical phenotype definitions | `fyron.phenotyping` |
| Missingness, imputation, categorical encoding, leakage checks, split balance | `fyron.preprocessing` |
| Descriptive numeric/categorical summaries, Table 1, SMD, endpoint summaries | `fyron.descriptive` |
| Baseline tables, metric tables, cohort flow tables | `fyron.reporting` |
| KM, RMST, Cox, Weibull AFT, PH checks | `fyron.survival` |
| Gradient survival boosting | `fyron.survival.train_gradient_survival_boosting` with `fyron[survival-ml]` |
| Classification ML, metrics, model plots | `fyron.ml` |
| Clinical plotting facade for KM, ML, exploratory, and paper figures | `fyron.plotting` |
| Scientific feature selection and consensus selection tables | `fyron.feature_selection` with `fyron[feature-selection]` |
| Thresholds, calibration, subgroup metrics, decision curves | `fyron.validation` with `fyron[validation]` |
| Survival validation (IPCW Brier, KM calibration, concordance, dynamic AUC) | `fyron.validation` with `fyron[survival-ml]` |
| Permutation importance, partial dependence, SHAP tables, and model explanation summaries | `fyron.explainability` with `fyron[explainability]` |
| Provenance manifests and file hashes | `fyron.audit` |
| BOA cohort feature extraction | `fyron.boa_extraction` |
| BOA radiomics from `body-regions.nii.gz` or `total.nii.gz` | `fyron.boa_radiomics` with `fyron[radiomics]` |
| BOA segmentation collages and aligned CT/MR difference heatmaps | `fyron.visualization` |
| Prepare CT/MRI folders as PNG previews for Curate | `fyron.visualization.prepare_curate_image_previews`, `fyron dataset-curate-previews` |
| Local image cohort curation dashboard | `fyron curate` with `fyron[curate]` |
| Repeatable terminal workflows | unified `fyron` CLI |

## Dependency Extras

- Base install: FHIR, DICOM, documents, imaging, core, LLM, DataFrame operations, cohort, flow.
- `fyron[all]`: full local research environment with every optional dependency.
- `fyron[excel]`: Excel read/write.
- `fyron[s3]`: boto3-backed S3 and S3-compatible object storage.
- `fyron[survival]`: lifelines survival analysis and survival plots.
- `fyron[survival-ml]`: scikit-survival gradient survival boosting and censoring-aware survival validation.
- `fyron[descriptive]`: descriptive analysis and Table 1 helpers.
- `fyron[dicom-seg]`: highdicom-backed DICOM SEG export.
- `fyron[ml]`: tabular classification ML, XGBoost, clinical plots.
- `fyron[feature-selection]`: univariate, correlation, model, permutation, Boruta, and stability selection.
- `fyron[validation]`: model validation helpers for thresholds, calibration, subgroups, and decision curves.
- `fyron[explainability]`: sklearn model interpretation and SHAP tables.
- `fyron[reporting]`: reporting helper alias; no extra dependency.
- `fyron[audit]`: provenance helper alias; no extra dependency.
- `fyron[ml,boruta]`: Boruta feature selection.
- `fyron[visualization]`: BOA/OpenCV collages and Matplotlib CT/MR difference heatmaps.
- `fyron[radiomics]`: PyRadiomics feature extraction from BOA segmentations; currently use Python 3.11 because PyRadiomics 3.0.1 does not build on Python 3.12.
- `fyron[curate]`: local Docker Compose image cohort review app launched with `fyron curate`.

Use `fyron[all]` for local workstations, tutorials, and full-feature exploration. Prefer targeted extras for lean deployments and for missing-dependency messages. If adding an import from an optional dependency, place it behind the relevant module/extra and raise a clear `ImportError` with the targeted install command.

## CLI Defaults

Fyron 0.3.12 adds `worker_auth_timeout=120` to FHIR/DICOM clients and
`parallel_job_timeout=300` to FHIR. The latter starts at worker execution, not
queueing; `None` opts out. Authentication uses process-local leases and parent
pipe coordination. Use guarded script entrypoints for spawn. Never interpret
bundles yielded before a worker error as a complete extract. New slow-job logs
must contain only job ordinals, stages, timings, and counts, never clinical values.

For service accounts, use `Auth.client_credentials(client_id=..., client_secret=...,
auth_url=<OIDC issuer>, scope=<approved scopes>)`, or supply `token_endpoint` instead
of the issuer. FHIR and DICOM workers share automatic Bearer renewal. This is
OAuth client credentials, not user login or ID-token validation. Keep examples
provider-neutral and never embed institutional credentials.

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

Prefer the unified `fyron` command for repeatable jobs:

- `fyron fhir-rest` for FHIR REST extraction.
- `fyron fhir-build-bundle` for CSV/DataFrame-to-FHIR bundle write-back.
- `fyron dicom-download` for DICOMweb downloads.
- `fyron document-download` for documents/PDFs with OIDC device or service-account authentication.
- `fyron synthetic-dicom` for generated volume export.
- `fyron dicom-seg` for DICOM SEG creation.
- `fyron dataset-nnunetv2`, `fyron dataset-yolo-classify`, and `fyron dataset-yolo-detect` for training dataset folder preparation.
- `fyron dataset-curate-previews` for CT/MRI/X-ray PNG previews that can be dropped into Curate.
- `fyron boa-extract` and `fyron boa-radiomics` for BOA tables.
- `fyron curate` for the local image cohort curation app.
- `fyron imaging-qc` for geometry, alignment, mask volume, and intensity checks.
- `fyron audit-manifest` for provenance.
- `fyron spark` for the opt-in Bits & Flames/Fyron banner easter egg.

Keep `fyron-banner` and `fyron-dicom` working as compatibility commands, but document new workflows with `fyron ...`.

Use global console flags consistently:

- `--quiet` suppresses nonessential CLI messages but must not change generated files.
- `--verbose` enables debug logging through the `fyron` logger.
- `--no-color` disables ANSI output.
- `--json-log` emits parseable log records for schedulers and CI.
- `--no-progress` disables progress bars for supported batch commands.

## Coding Style

Network diagnostics must use controlled events from `fyron._diagnostics`. Never
log remote exception text, clinical identifiers, URLs, SQL, prompts, or response
bodies, even at DEBUG. Keep identifying data only in explicit result columns.
Document and DICOM completion counts do not imply successful downloads.
New download skips require verified completion records. Preserve unverified
existing files; explicit overwrite requires user intent. S3 existence failures
other than not-found must propagate, and S3 lists must follow pagination.

- Keep APIs DataFrame/array friendly and return dictionaries or dataclasses with named outputs.
- Validate required columns and array lengths before fitting models.
- Prefer explicit parameter names like `duration_col`, `event_col`, `group_col`, `save_path`.
- Preserve existing patterns: helpers in focused modules, public exports in `__init__.py`, tests in `tests/test_*.py`.
- Avoid broad refactors when adding one workflow.
- Library functions should use `logging.getLogger("fyron...")` or `fyron.console.get_logger`; avoid direct `print(...)` except explicit banner helpers.
- CLI commands own user-facing terminal summaries and should use `fyron.console` helpers for status messages.
- Do not print the package banner automatically on import or before normal CLI commands; keep it opt-in through `fyron banner`, `fyron spark`, or `fyron.banner.print_banner`.
- Use Matplotlib for package plots; do not require Seaborn for core plotting.
- For publication plots, return `(fig, ax)` or `(fig, ax, table)` if a computed table is useful.

## Clinical Data Science Defaults

- Prefer `FlowTracker(id_col=..., progress=True)` and `flow.add(label, dataframe)`
  for explicit cohort tracking. Use `with flow.step(label, kind="query")` and
  `step.result(result)` for query activity; it must not imply cohort exclusion.
  `cohort_table()` contains selections; `to_dataframe()` includes activities.
  Keep live step labels nonidentifying.

- BOA cohort helpers and FHIR DataFrame query helpers accept `return_report=True`,
  returning `data` plus `report.rows` and `report.summary` tables. Default returns
  remain unchanged. BOA case identifiers must be unique; its reports are sensitive.
  FHIR reports distinguish executed queries from exhausted pagination, and failed
  DataFrame queries still raise. Parallel input metadata uses original values;
  name collisions with resource columns must raise, never overwrite.
- BOA tissue areas default to `tissues.nii.gz` (muscle=1, SAT=3, VAT=4,
  IMAT=5). Anatomical body-region masks are not tissue fallbacks. Vertebral
  ranges use `[min_slice_idx, max_slice_idx)`; invalid ranges remain missing.
- Curate binds published ports to loopback and keeps PostgreSQL internal.
  Original files and reviewed DICOM series are immutable; retry interrupted
  uploads with the same batch before export. Keep deployment single-process.
- Physical imaging volumes require 3D data and known positive finite millimetre
  spacing. Array distance metrics use array-axis spacing (ZYX for SimpleITK arrays);
  QC `spacing_xyz` retains XYZ metadata semantics. Do not label counts as ml.
- Phenotype combination requires unique patient keys and unambiguous binary
  flags; summaries reject conflicting patient flags/groups. Absence of recorded
  evidence is not a confirmed clinical negative. Fit preprocessing on training
  data only; unknown categories map to rare only if that level was fitted.
- Provenance manifests are internal research artifacts by default. Publication
  summaries must explicitly select reviewed fields, not claim automatic anonymization.

- Audit date endpoints with `fyron.cohort.audit_time_to_event_endpoint` before fitting; unresolved endpoints are not observed censoring. `administrative_censor_date` caps available follow-up but never creates missing follow-up. Use `audit_cohort_join` for key coverage and expected row multiplication without weakening merge validation.
- Reuse `fyron._dates` parsing/elapsed-time/unit helpers. Date features default to `errors="coerce"`; strict parsing is opt-in. Endpoint construction is strict. Reject mixed naive/aware dates, preserve indices, and treat month/year units as fixed elapsed durations.

- Follow `docs/survival-workflow.md` for endpoint construction, explicit predictor preparation, fitting, diagnostics, validation, and plotting.
- Reuse the dependency-light private `fyron._survival_data` contracts instead of duplicating outcome validation or fitting-cohort selection. KM/RMST/Cox accept zero durations; AFT, boosting, and survival validation require positive durations.
- Cox/AFT `training_df` retains the actual fitting rows and original index. Use it for diagnostics and inspect `n_used`/`n_excluded`; unrelated missing columns must not exclude rows. Never silently impute outcomes.

- Survival workflows expect finite durations under the method-specific rules above and event indicators where `1` means event and `0` means censored.
- Classification metrics should include sensitivity, specificity, balanced accuracy, AUC when probabilities are available, and confusion counts for binary targets.
- Imbalanced binary classification should expose both sklearn `class_weight` and XGBoost `scale_pos_weight` paths.
- Use Spearman correlation as the default for clinical exploratory heatmaps unless there is a reason to assume linear Pearson relationships.
- Patterned bars should remain grayscale-safe with hatches and readable labels.

## Documentation

- Detailed public docs live in `docs/` and are built with the custom BF-native generator in `scripts/build_docs.py`.
- Reusable LLM/user-facing Fyron skill instructions live in `docs/ai/fyron/SKILL.md`.
- When adding or changing public APIs, update the relevant page under `docs/modules/`.
- When changing module intent, CLI workflows, or dependency extras, keep `docs/ai/fyron/SKILL.md` aligned with `AGENTS.md`.
- Keep README short; it is a landing page, not the full manual.
- Build docs locally with `python3 scripts/build_docs.py`.

## Testing

- Run `uv run python scripts/check_docstrings.py`; prune repaired gaps with `--prune`, never expand the baseline for new APIs.
- Use `scripts/check_wheel.py --wheel <built-wheel> --extra <extra>` with the target Python interpreter for isolated installed-package operations. Do not add development dependencies to these environments to mask missing runtime declarations.
- Keep examples synthetic, deterministic, executable outside the checkout, and explicit about exclusions. Public modules remain evolving; configured CI targets are not evidence of passing platform support.

- Install/update the development environment with `uv sync --all-extras --dev`.
- Core tests: `uv run pytest`.
- Focused ML/survival tests: `uv run pytest tests/test_ml.py tests/test_survival.py`.
- Documentation build: `uv run python scripts/build_docs.py`.
- Package build: `uv build`.
- Optional tests may skip when extras such as Boruta are not installed.


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

Use the [authentication guides](docs/authentication/index.md) for provider-neutral FHIR REST, DICOMweb, document and PostgreSQL examples. Let the site administrator determine the permitted method, client, scopes and endpoints. Distinguish native environment defaults from explicitly loaded example variables and Python support from CLI support. SQL uses PostgreSQL credentials, not the HTTP Auth object. Never include institutional endpoints, tokens or credentials in shared examples.

Explain token renewal as demand-driven, not background keep-alive. Static Bearer tokens do not renew. Device flow can refresh cached credentials; `allow_reauthentication=False` permits refresh but fails when browser approval is required. Client credentials obtain new access tokens using the registered credentials. Keep shared Auth alive across the operation and never imply SQL credentials renew through HTTP Auth.

## Licensing

Current project source and Curate frontend/backend use CC BY-NC 4.0. Describe it as source available for noncommercial use with attribution, not OSI open source or research-only. Preserve third-party licenses and earlier MIT permissions. Never rewrite historical release licensing or replace published artifacts; a future distribution of the license change needs a new version. Keep package metadata, Docker labels, Curate's public license files and documentation consistent.
