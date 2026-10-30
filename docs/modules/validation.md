# Model Validation

The [survival workflow](../survival-workflow.md) distinguishes training, evaluation, and censoring-reference cohorts, risk scores, and event probabilities.

`fyron.validation` adds model reliability helpers that complement `fyron.ml`. Use it after training a classifier or survival model to inspect thresholds, calibration, subgroup performance, decision-curve net benefit, and external validation behavior.

Validation outputs are tables and dictionaries designed for review. They help you decide whether a model is clinically usable, not just whether it has a high headline score.

Calibration, threshold selection, and decision curves validate outcomes before
encoding the positive class. Missing or multiclass outcomes, empty/misaligned
arrays, and nonfinite or out-of-range probabilities raise `ValueError`.
Resolve missing outcomes explicitly before analysis. Constant probabilities
remain represented in the calibration bin table.

Threshold selection and binary metric bootstrapping require both target classes. Bootstrap draws containing only one class are excluded so macro and binary metrics are never mixed; inspect `n_successful_rounds` for each interval.

## Install

Decision curves require nonempty, aligned one-dimensional label/probability
vectors, nonmissing binary labels, finite probabilities in `[0, 1]`, and finite
thresholds strictly inside `(0, 1)`. Column-vector arrays such as shape
`(n, 1)` now raise an error instead of broadcasting to an incorrect count
matrix. Explicitly select a Series or flatten the intended single column;
recalculate curves previously generated from two-dimensional inputs.

```bash
uv add "fyron[validation]"
```

Survival validation additionally requires `uv add "fyron[survival-ml]"`.
These dependencies are loaded only when a survival metric is called.

## Survival Inference Corrections

Fixed-horizon calibration uses Kaplan-Meier event probability, and Brier scores
use inverse-probability-of-censoring weighting (IPCW). Early censoring is not a
known non-event. Predictions must be event probabilities in `[0, 1]`; ranking
scores belong in concordance/AUC calculations, not probability calibration.

`survival_calibration_at_time`, `brier_score_at_time`, and
`external_survival_validation` accept keyword-only `censoring_df=None`. Supply a
reference DataFrame with the same duration/event column names to estimate its
censoring distribution; otherwise the evaluation cohort is used. IPCW assumes
independent censoring and a censoring distribution applicable to the evaluated
cohort. Required censoring probabilities must be positive. Unsupported horizons
raise `ValueError`, including calibration bins ending in censoring before the
horizon. Reduce the horizon or choose fewer bins for sparse calibration data.

Survival outcomes must be complete, finite, positive-time observations with
binary events. Scores must be finite. Invalid outcomes are not silently coerced
or dropped. Dynamic AUC preserves requested horizon order, including repeats.
Concordance follows scikit-survival's event/censoring and risk-tie conventions.
Bootstrap output adds `valid_rounds` and `dropped_rounds`; undefined replicates
are excluded, and no valid replicates raises `ValueError`.

Recompute prior naive survival Brier/calibration results, concordance with tied
follow-up times, and AUC tables requested with unsorted horizons.

## Imports

```python
from fyron import validation as fv
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| `y_true` | Observed labels, usually `0`/`1` for binary classification. |
| `y_prob` | Predicted probability for the positive class. Required for AUC, calibration, thresholds, and decision curves. |
| `y_pred` | Hard predicted labels after applying a threshold. |
| `pos_label` | Label treated as the event/positive class. |
| subgroup column | Clinical group used to inspect performance heterogeneity. |
| fixed-horizon survival prediction | Predicted event risk by a chosen time point, such as 12 months. |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | Arrays for labels/predictions/probabilities, or DataFrames for subgroup and survival validation tables. |
| Required columns | Named true label, prediction, probability, subgroup, time, event, or risk columns must exist. |
| Return shape | Dictionaries with summary values plus DataFrames for bins/thresholds, or standalone validation DataFrames. |
| Saved artifacts | Threshold tables, calibration bins, subgroup metrics, decision-curve tables, bootstrap CIs, and external validation summaries. |
| Failure modes | Mismatched lengths, missing probabilities, one-class validation sets, invalid thresholds, empty subgroups, or unavailable optional survival-ML dependencies. |

## Function Guide

| Function | Use it when | Returns |
| --- | --- | --- |
| `find_best_threshold` | You need a threshold table and exploratory best threshold. | best-threshold dict with table |
| `calibration_summary` | You need observed versus predicted risk by probability bin. | summary dict and bin table |
| `subgroup_metric_table` | You need metrics by sex, stage, center, scanner, or other subgroup. | subgroup metric DataFrame |
| `decision_curve_table` | You need net-benefit values over clinical risk thresholds. | decision-curve DataFrame |
| `bootstrap_classification_metrics` | You need uncertainty intervals for classification metrics. | metric CI DataFrame |
| `bootstrap_concordance_index` | You need uncertainty for survival risk ranking. | C-index summary dict |
| `survival_calibration_at_time` | You need fixed-horizon survival calibration. | summary dict and bin table |
| `brier_score_at_time` | You need fixed-horizon prediction error. | Brier score dict |
| `external_survival_validation` | You need a compact external validation summary. | validation dict |
| `time_dependent_auc_table` | You need dynamic AUC and have `fyron[survival-ml]`. | AUC DataFrame |

## Classification Example

```python
from fyron import validation as fv

threshold = fv.find_best_threshold(
    y_true=y_test,
    y_prob=rf["y_prob"],
    metric="youden",
)

calibration, calibration_bins = fv.calibration_summary(
    y_true=y_test,
    y_prob=rf["y_prob"],
    n_bins=10,
)

subgroups = fv.subgroup_metric_table(
    validation_df,
    group_col="sex",
    y_true_col="event",
    y_pred_col="prediction",
    y_prob_col="probability",
)

dca = fv.decision_curve_table(y_test, rf["y_prob"])

metric_ci = fv.bootstrap_classification_metrics(
    y_test,
    y_pred,
    rf["y_prob"],
    n_rounds=1000,
    random_state=42,
)
```

## Research Decision: What To Report

| Output | Why it matters |
| --- | --- |
| AUC | Ranking discrimination, not clinical usefulness by itself. |
| Sensitivity/specificity | Depends on a threshold; state whether the threshold was locked. |
| Calibration | Shows whether predicted probabilities match observed risk. |
| Subgroups | Reveals performance heterogeneity across clinically relevant strata. |
| Decision curve | Connects predictions to threshold-dependent net benefit. |
| Confidence intervals | Makes sampling uncertainty visible for metrics and C-index. |

## Parameter Notes

| Parameter | Practical guidance |
| --- | --- |
| `metric` | Threshold scans often use `youden`, sensitivity, specificity, or balanced accuracy. Pre-specify this for confirmatory analyses. |
| `n_bins` | Calibration bins should be large enough to contain meaningful patient counts. |
| `group_col` | Choose clinically relevant subgroups, not arbitrary slices. |
| `thresholds` | Use clinically meaningful ranges for decision curves. |
| `time_horizon` | Must use the same time unit as `duration_col`. |
| `prediction_col` | For fixed-horizon helpers, this should be event risk by `time_horizon`. |

## Survival Validation

Use survival validation helpers after generating a risk score or fixed-horizon event-risk prediction.

```python
c_index = fv.bootstrap_concordance_index(
    validation_df,
    duration_col="time",
    event_col="event",
    risk_col="risk_score",
    n_rounds=1000,
)

calibration, calibration_bins = fv.survival_calibration_at_time(
    validation_df,
    duration_col="time",
    event_col="event",
    prediction_col="risk_12_month",
    time_horizon=12,
)

brier = fv.brier_score_at_time(
    validation_df,
    "time",
    "event",
    "risk_12_month",
    12,
)
```

The fixed-horizon helpers treat `prediction_col` as event risk by the selected time horizon.

With `fyron[survival-ml]`, dynamic AUC is available:

```python
auc = fv.time_dependent_auc_table(
    train_df,
    validation_df,
    duration_col="time",
    event_col="event",
    risk_col="risk_score",
    times=[365, 730],
)
```

## Common Pitfalls

- Do not report a threshold chosen on the test set as if it were pre-specified.
- Calibration can be poor even when AUC is high.
- Subgroup tables can become unstable when groups are small.
- Decision curves require clinically meaningful threshold probabilities.
- Ensure `time_horizon` uses the same unit as `duration_col`.

## Related Modules

- [Machine Learning](ml.md) for model training and classification metrics.
- [Survival Analysis](survival.md) for risk scores and time-to-event models.
- [Clinical Plotting](plotting.md) for calibration, decision-curve, and validation figures.
