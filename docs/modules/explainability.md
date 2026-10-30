# Explainability

`fyron.explainability` provides inspectable model-interpretation tables for fitted sklearn-compatible estimators. The module is intentionally table-first so explanations can be reviewed, plotted, and exported. SHAP support is optional and stays explicit because SHAP values are powerful but method-sensitive.

For inclusion/exclusion explanations, use [Flow Explainability](flow.md). A strong study usually keeps both artifacts: a cohort flow explaining who entered the analysis, and model explanation tables explaining which features influenced predictions.

## Install

```bash
uv add "fyron[explainability]"
```

## Imports

```python
from fyron import explainability as fe
```

## API Contract

SHAP tables require one explanation row per evaluated input. Custom feature names rename columns positionally without discarding their values. Legacy lists of per-output arrays and current arrays with the output axis last are supported; for multiple outputs, the last output is selected. Supply a custom explainer returning a two-dimensional array to select a different output explicitly.

| Topic | Contract |
| --- | --- |
| Input shape | Fitted sklearn-compatible estimator plus feature DataFrame/array; optional SHAP/background data for SHAP workflows. |
| Required columns | Feature names should match model inputs; contribution tables need row/patient, feature, value, and contribution columns. |
| Return shape | DataFrames for permutation importance, partial dependence, SHAP values, SHAP summaries, and reviewer-facing summaries. |
| Saved artifacts | Feature importance tables, SHAP/contribution tables, model explanation summaries, and patient-level driver tables. |
| Failure modes | Missing optional SHAP/sklearn support, unsupported estimator interface, mismatched feature names, expensive SHAP runs, or explanations mistaken for causal effects. |

## Function Reference

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `permutation_importance_table(estimator, X, y, ...)` | fitted model, features, labels | feature names, repeats, scoring, random state | sorted importance DataFrame |
| `partial_dependence_table(estimator, X, ...)` | fitted model and feature table | features, names, grid resolution | long partial-dependence DataFrame |
| `shap_values_table(estimator, X, ...)` | fitted model and feature table | feature names, custom explainer, background data, max rows | long row-feature SHAP DataFrame |
| `shap_summary_table(estimator, X, ...)` | fitted model and feature table | feature names, custom explainer, background data, max rows | ranked mean absolute SHAP summary |
| `explain_model_summary(...)` | importance, SHAP, metrics, or QC tables | notes, feature column name | merged reviewer-facing feature summary |
| `explain_patient_prediction(...)` | long contribution table | row/patient selector, top N, column names | top positive and negative drivers |

## Example

```python
importance = fe.permutation_importance_table(
    estimator=rf["model"],
    X=X_test,
    y=y_test,
    feature_names=X_test.columns,
    n_repeats=20,
    scoring="roc_auc",
)

pdp = fe.partial_dependence_table(
    estimator=rf["model"],
    X=X_test,
    features=["l3_sma_cm2", "age"],
)

shap_summary = fe.shap_summary_table(
    estimator=rf["model"],
    X=X_test,
    background_data=X_train.sample(100, random_state=42),
    max_rows=500,
)
```

## Reviewer-Facing Summary

Use `explain_model_summary` to combine model explanation outputs with feature QC and validation metrics:

```python
summary = fe.explain_model_summary(
    importance=importance,
    shap_summary=shap_summary,
    feature_qc=feature_qc,
    metrics={"auc": 0.82, "balanced_accuracy": 0.74},
    notes={"stage": "Clinically plausible direction."},
)
```

For a single patient or row, use a long contribution table such as `shap_values_table` output:

```python
drivers = fe.explain_patient_prediction(
    shap_long,
    row_index=0,
    top_n=5,
)
```

## SHAP Workflow

Use SHAP when you need feature-attribution tables for individual rows or a ranked global importance summary. Fyron returns plain DataFrames rather than SHAP plot objects:

- `shap_values_table` returns one row per patient-row and feature with `feature_value`, `shap_value`, and `abs_shap_value`.
- `shap_summary_table` aggregates those values into `mean_abs_shap`, `mean_shap`, `median_abs_shap`, `n`, and `rank`.
- `background_data` should represent the training distribution; for large cohorts use a reviewed sample.
- `max_rows` keeps expensive SHAP jobs bounded for notebooks and CI.

Use model explanations as inspection tools, not causal evidence. When a feature looks unexpectedly important, check leakage, missingness, coding artifacts, subgroup imbalance, target leakage through follow-up time, and clinical plausibility.
