# Reporting

`fyron.reporting` turns ordinary analysis outputs into clean review tables. Think of it as the last mile between a notebook and something another data scientist, clinician, reviewer, or co-author can actually read.

Use it after cohort construction, descriptive analysis, survival modeling, or ML evaluation when you need structured outputs for manuscripts, supplements, internal reports, or Markdown review. It does not write the manuscript for you; it helps make the numbers easy to inspect, compare, and export.

## Install

```bash
uv add fyron
```

## Imports

```python
from fyron import reporting as fr
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| baseline table | Cohort characteristics table, optionally stratified by a group column. |
| metric table | Normalized model metrics from dictionaries or DataFrames. |
| cohort flow table | Ordered inclusion/exclusion count table. |
| flow tracker table | Output from `fyron.flow.FlowTracker.to_dataframe()`, compatible with flow reporting and plotting. |
| formatted estimate | Human-readable estimate with confidence interval. |
| Markdown table | Lightweight review/export format for docs, reports, and PRs. |

## When This Helps

| You have... | Use reporting to create... |
| --- | --- |
| a cleaned cohort table | a compact baseline table for first review |
| model result dictionaries | one comparable metric table across models |
| inclusion/exclusion steps | a cohort flow table for methods and supplements |
| estimates and confidence intervals | consistent manuscript strings |
| any DataFrame your team must review | a Markdown table for comments, docs, or PRs |

The best reporting workflow is boring in a good way: return a table, save it, review it, and keep the exact artifact with your figures and provenance manifest.

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | Cohort/result DataFrames, metric dictionaries, model result dictionaries, or ordered flow-step records. |
| Required columns | Columns named as continuous, categorical, metric, step, count, estimate, or CI inputs must exist. |
| Return shape | DataFrames for report tables or strings for formatted estimates and Markdown exports. |
| Saved artifacts | Caller writes CSV, Markdown, Excel, or manuscript supplement files from returned tables. |
| Failure modes | Missing columns, nonnumeric metric values, inconsistent model result dictionaries, invalid flow counts, or formatting assumptions that need reviewer adjustment. |

## Function Guide

| Function | Use it when | Returns |
| --- | --- | --- |
| `summarize_baseline_table` | You need a compact baseline characteristics table. | DataFrame |
| `metrics_table` | You need comparable model metrics across one or more models. | DataFrame |
| `compare_models_table` | You have several Fyron model result dicts and need one comparison table. | DataFrame |
| `cohort_flow_table` | You need a count flow from source population to final cohort. | DataFrame |
| `format_estimate_ci` | You need consistent estimate/CI strings. | string |
| `dataframe_to_markdown` | You need a reviewable text table. | Markdown string |

## Typical Workflow

```python
from fyron import reporting as fr

baseline = fr.summarize_baseline_table(
    cohort,
    group_col="risk_group",
    continuous=["age", "l3_sma_cm2", "vat_ml"],
    categorical=["sex", "stage"],
)

model_metrics = fr.compare_models_table(
    {
        "Random Forest": rf_result,
        "XGBoost": xgb_result,
    }
)

flow = fr.cohort_flow_table(flow_tracker.to_dataframe())

baseline_md = fr.dataframe_to_markdown(baseline)
```

Save the DataFrames as CSV/Parquet for reproducibility and use Markdown only for human review.

## Parameter Notes

| Parameter | Practical guidance |
| --- | --- |
| `df` | Usually a patient-level cohort or result table. |
| `group_col` | Stratifies summaries, for example by treatment, risk group, or cohort. |
| `continuous` | Explicit continuous variables; avoid automatic selection for final tables. |
| `categorical` | Explicit categorical variables; include binary endpoints when count summaries are desired. |
| `metrics` | Dict or DataFrame from `fyron.ml`, `fyron.validation`, or custom model code. |
| `steps` | Ordered list of dicts with at least `step` and `n`; optional `reason` explains exclusions. |

## Baseline Table

```python
baseline = fr.summarize_baseline_table(
    cohort,
    group_col="risk_group",
    continuous=["age", "l3_sma_cm2", "vat_ml"],
    categorical=["sex", "stage"],
)
```

Use this for an early baseline table, not as a replacement for a final statistical Table 1. For final manuscripts, pair it with `fyron.descriptive.create_table_one` when you need p-values, SMDs, or stricter formatting.

## Model Metrics

```python
metrics = fr.metrics_table(
    {
        "Random Forest": rf_result["metrics"],
        "XGBoost": xgb_result["metrics"],
    }
)
```

When you have full model result dictionaries, use:

```python
model_table = fr.compare_models_table(
    {
        "Random Forest": rf_result,
        "XGBoost": xgb_result,
    }
)
```

For binary clinical classifiers, include sensitivity, specificity, balanced accuracy, AUC when probabilities are available, and confusion counts.

## Cohort Flow

```python
flow = fr.cohort_flow_table(
    [
        {"step": "FHIR patients queried", "n": 1240},
        {"step": "With baseline CT", "n": 830, "reason": "missing CT"},
        {"step": "With complete outcome", "n": 790, "reason": "missing follow-up"},
    ]
)

markdown = fr.dataframe_to_markdown(flow)
```

When filters are executed in code, use `fyron.flow` to record steps automatically and then pass the resulting table into reporting:

```python
from fyron.flow import FlowTracker
from fyron import reporting as fr

tracker = FlowTracker("NSCLC CT cohort")
tracker.add_step("Source cohort", raw)
tracker.add_step("Has baseline CT", with_ct, reason="missing CT")

markdown = fr.dataframe_to_markdown(tracker.to_dataframe())
```

For methods sections, keep the flow table and the text explanation aligned. If a filter removes patients, the `reason` should be meaningful enough that a reviewer can understand what happened without opening the code.

## What To Save

| Artifact | Why save it |
| --- | --- |
| baseline table CSV | shows the cohort that entered the analysis |
| model metric table CSV | preserves exact rounded and unrounded model results |
| cohort flow table CSV | documents inclusion/exclusion counts |
| Markdown table | supports review in issues, PRs, reports, or docs |
| provenance manifest | links tables back to inputs, parameters, and package version |

## Return Values

Reporting helpers return simple strings or `pandas.DataFrame` objects so the outputs can be saved, reviewed, converted to Markdown, or plotted with `fyron.plotting`.

## Common Pitfalls

- Reporting helpers do not decide what belongs in the manuscript; authors still review wording and clinical interpretation.
- Keep inclusion/exclusion reasons explicit in cohort flow tables.
- Do not mix training and validation metrics without a clear model/source column.
- Preserve unrounded numeric outputs elsewhere if rounded tables are used in manuscripts.
- Do not let a pretty report hide weak study design; reporting is an artifact layer, not a validity layer.

## Related Modules

- [Descriptive Analysis](descriptive.md) for Table 1 and endpoint summaries.
- [Clinical Plotting](plotting.md) for cohort flow and metric figures.
- [Flow Explainability](flow.md) for decorated cohort/filter tracking.
- [Audit & Provenance](audit.md) for recording table and figure inputs.
