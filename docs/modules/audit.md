# Audit And Provenance

`fyron.audit` creates lightweight JSON provenance manifests for reproducible analyses. Use it to record input files, output artifacts, parameters, package version, runtime metadata, and notes that explain how an analysis was produced.

The manifest is deliberately simple JSON for internal reports, model artifacts,
and archived cohort folders. It is not automatically safe for a paper supplement.
Paths, query parameters, cohort identifiers, free-text notes, and file hashes can
be sensitive. Hashing detects file changes; it does not anonymize clinical data.

## Audit and Provenance Guides

| Task | Guide |
| --- | --- |
| Record an analysis run | [Create a manifest](#minimal-example) or use the [CLI](#cli-workflow) |
| Decide which details to preserve | [What to record](#what-to-record) |
| Prepare a reviewed publication summary | [Internal records and publication summaries](#internal-records-and-publication-summaries) |
| Interpret logs and batch outcomes | [Safe Network Diagnostics](../diagnostics.md) |
| Assess verification and compatibility | [Research Reliability](../reliability.md) |
| Preserve research artifacts and cite Fyron | [Using Fyron in Research](../repository-trust.md) |

## Install

```bash
uv add fyron
```

## Imports

```python
from fyron import audit as fa
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| input | Source file used by an analysis, such as a cohort CSV, DICOM result table, or BOA feature table. |
| output | File produced by an analysis, such as a table, figure, model artifact, or report. |
| parameter | Explicit setting that affects the result, such as `duration_col`, `event_col`, covariates, thresholds, or random seed. |
| hash | File digest used to detect changes in inputs or outputs. |
| manifest | JSON-serializable record that connects inputs, parameters, environment, and outputs. |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | File paths, output paths, parameter dictionaries, notes, random seeds, and study/run metadata. |
| Required columns/files | Existing files are hashed when paths are supplied; missing paths can still be recorded as planned artifacts. |
| Return shape | JSON-serializable dictionaries or resolved output paths. |
| Saved artifacts | Provenance JSON manifests, file hash records, and analysis-run metadata. |
| Failure modes | Unreadable files, unwritable output paths, non-serializable parameter values, or missing study metadata needed for reviewer interpretation. |

## Function Guide

| Function | Use it when | Returns |
| --- | --- | --- |
| `hash_file` | You need a digest for one file. | hex digest string |
| `create_provenance_manifest` | You need a JSON-ready record of an analysis. | dict |
| `analysis_run_manifest` | You need a study-run manifest with analysis type, cohort ID, and seed. | dict |
| `write_manifest` | You need to write the manifest to disk. | output path |

## Minimal Example

```python
from fyron import audit as fa

manifest = fa.create_provenance_manifest(
    title="BOA survival model analysis",
    inputs=["data/boa_features.csv", "data/outcomes.csv"],
    outputs=["results/cox_model_summary.csv", "figures/km_risk_group.png"],
    parameters={
        "duration_col": "time",
        "event_col": "event",
        "covariates": ["age", "stage", "l3_sma_cm2"],
        "random_state": 42,
    },
)

fa.write_manifest(manifest, "results/provenance.json")
```

For clinical AI studies, prefer the run-specific wrapper:

```python
manifest = fa.analysis_run_manifest(
    title="Locked external validation",
    analysis_type="classification",
    cohort_id="validation-cohort-v1",
    inputs=["data/validation.csv"],
    outputs=["results/model_metrics.csv"],
    parameters={"threshold": 0.4, "model": "Random Forest"},
    random_seed=42,
)
```

## Parameter Notes

| Parameter | Practical guidance |
| --- | --- |
| `title` | Use a human-readable analysis name. |
| `inputs` | Include raw or derived files that determine the result. Existing files receive hashes. |
| `outputs` | Include generated artifacts. Output records contain path, existence, and size; they are not automatically hashed. |
| `parameters` | Record clinical and technical assumptions, not just model hyperparameters. |
| `notes` | Add free-text context such as cohort version, reviewer, or known limitations. |

## CLI Workflow

```bash
fyron audit-manifest \
  --title "BOA survival model analysis" \
  --input data/boa_features.csv \
  --input data/outcomes.csv \
  --output results/cox_model_summary.csv \
  --output figures/km_risk_group.png \
  --param duration_col=time \
  --param event_col=event \
  --write results/provenance.json
```

Use the CLI after a table, model, or figure-producing script has run. It is also useful in pipeline jobs where provenance should be written even when the analysis code is outside Python.

## What To Record

| Workflow | Useful parameters |
| --- | --- |
| FHIR extraction | `resource_type`, `params`, `max_pages`, partition dates, `deduplicate_by` |
| DICOM download | endpoint label, output format, study/series UID columns, manifest path |
| BOA extraction | feature families, label maps, `download_id` mapping, number of workers |
| Survival analysis | `duration_col`, `event_col`, `group_col`, covariates, `tau` |
| ML | model type, split settings, class imbalance settings, random seed, selected features |
| Validation | threshold rule, calibration bins, subgroup columns, time horizon |

## Research Decision: Minimum Provenance

For papers and internal model reviews, record at least the cohort file, feature file, model/table/figure outputs, random seed, endpoint definition, threshold rule, and Fyron version. The manifest is not a substitute for a methods section, but it prevents silent drift between notebooks, exported tables, and final figures.

## Common Pitfalls

- Do not record only final outputs; include the cohort and feature inputs.
- Record random seeds and threshold rules when models are involved.
- Keep manifests next to exported artifacts so they are not separated from results.
- Use stable file paths or archive manifests with the exact files they describe.

## Internal Records And Publication Summaries

Keep full manifests in the controlled research workspace. Review disclosure
separately from reproducibility: never store credentials, access tokens, or
passwords in parameters or notes. Do not assume removing patient names alone
makes an artifact safe to publish.

The executable `examples/research_contracts.py` creates two distinct artifacts:

- `internal_manifest.json`: source paths, an input hash, output file metadata,
  runtime metadata, parameters, and notes.
- `publication_summary.json`: a newly constructed dictionary containing only
  explicitly reviewed software-version and synthetic-method fields.

```bash
uv run python examples/research_contracts.py --output-dir /tmp/fyron-contracts
```

This is an allowlisted example, not an anonymization utility. Construct and
review your own publication summary according to your study's disclosure policy.
Do not copy arbitrary metadata or rely on a generic redactor. Planned output
paths may exist in a manifest before files are created, so a manifest alone is
not proof that a run completed successfully.

## Related Modules

- [Reporting](reporting.md) for tables that should be recorded as outputs.
- [Clinical Plotting](plotting.md) for figures that should be recorded as outputs.
- [Unified CLI](cli.md) for repeatable terminal workflows.
