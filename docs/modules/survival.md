# Survival Analysis

Start with the [recommended survival workflow](../survival-workflow.md) for endpoint construction, fitting-cohort accounting, validation, and plotting.

`fyron.survival` supports standard time-to-event workflows for clinical cohorts: Kaplan-Meier curves, log-rank tests, restricted mean survival time, Cox proportional hazards models, proportional hazards diagnostics, Weibull accelerated failure time models, and optional gradient survival boosting.

## Install

```bash
uv add "fyron[survival]"
```

For gradient survival boosting:

```bash
uv add "fyron[survival-ml]"
```

## Expected Cohort Format

Survival functions expect a patient-level DataFrame with:

| Column | Meaning |
| --- | --- |
| `time` | non-negative follow-up for KM/RMST/Cox; strictly positive for AFT, boosting, and prediction validation |
| `event` | event indicator, where `1` means event and `0` means censored |
| covariates | clinical, imaging, biomarker, or model-score features |
| group column | optional categorical group for KM/log-rank/RMST |

You can build `time` and `event` with `fyron.cohort.build_survival_columns`.

```python
from fyron.cohort import build_survival_columns

df = build_survival_columns(
    df,
    start_col="diagnosis_date",
    end_col="last_followup_or_event_date",
    event_col="death_event",
    time_col="time",
)
```

## Choosing A Survival Method

Use Kaplan-Meier curves to describe survival experience and compare groups visually. Use RMST when proportional hazards are questionable or when an absolute time-based summary is easier to communicate. Use Cox models when you need adjusted hazard ratios and can assess proportional hazards. If Schoenfeld diagnostics suggest time-varying effects, add sensitivity analyses with stratified Cox, Cox time interactions, RMST, or Weibull AFT. Use gradient survival boosting when you need non-linear risk modeling, but keep it separate from classical inference.

Always inspect censoring, follow-up time, and event definitions before modeling. A technically valid model can still be clinically misleading if `time` starts at the wrong index date or if censoring differs systematically between groups.

## Research Decision: Endpoint And Method

| Decision | Practical guidance |
| --- | --- |
| Index date | Use the date where follow-up truly starts, such as diagnosis, baseline CT, treatment, or enrollment. |
| Event coding | `event=1` means the event occurred; `event=0` means censored. |
| Time unit | Keep one unit across KM, Cox, RMST, calibration, and fixed-horizon prediction. |
| KM vs Cox | Use KM for descriptive curves; use Cox for adjusted hazard ratios when PH assumptions are plausible. |
| RMST | Prefer RMST when absolute survival time is easier to communicate or PH is questionable. |
| PH diagnostics | Run `check_ph_assumptions` before presenting adjusted Cox results as stable hazard ratios. |
| PH violations | Use `run_survival_sensitivity_analysis` to collect Cox diagnostics, RMST, Weibull AFT, and time-interaction Cox outputs. |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | Patient-level DataFrame with one row per analysis unit. |
| Required columns | Positive duration column, binary event column where `1` means event, and named group/covariate columns. |
| Return shape | Kaplan-Meier result objects, DataFrames with estimates/tests, fitted lifelines objects, or Matplotlib figures. |
| Saved artifacts | KM figures, at-risk tables, Cox/HR tables, RMST tables, Schoenfeld diagnostics, and survival prediction tables. |
| Failure modes | Missing/invalid duration or event columns, nonpositive follow-up, no events, convergence warnings, violated PH assumptions, or missing optional survival extras. |

## API Summary

| Function | Purpose | Main output |
| --- | --- | --- |
| `plot_kaplan_meier` | KM curves, log-rank tests, optional risk counts/RMST annotation | `KaplanMeierPlotResult` |
| `create_survival_groups` | categorical, median, tertile, quartile, custom splits | DataFrame copy |
| `calculate_rmst` | restricted mean survival time by group | DataFrame |
| `compare_rmst` | pairwise RMST contrasts | DataFrame |
| `fit_univariate_cox` | one Cox model per covariate | result table and fitters |
| `fit_multivariate_cox` | multivariable Cox PH model | result table and fitter |
| `fit_time_varying_cox` | start-stop long-format Cox model | result table and fitter |
| `fit_cox_time_interactions` | generated covariate-by-time Cox interactions | result table, fitter, expanded data |
| `run_survival_sensitivity_analysis` | guided Cox PH violation sensitivity workflow | Cox/AFT/RMST/time-interaction outputs |
| `cox_forest_table` | reporting table for Cox forest plots | DataFrame |
| `survival_prediction_table` | fixed-time survival/risk predictions from supported models | DataFrame |
| `check_ph_assumptions` | Schoenfeld-style PH diagnostics | summary/violations |
| `schoenfeld_residuals_table` | scaled Schoenfeld residuals for Cox PH diagnostics | DataFrame |
| `schoenfeld_test_table` | PH test table with optional adjusted p-values | DataFrame |
| `plot_schoenfeld_residuals` | residual scatter plot by covariate | `(fig, ax)` |
| `fit_weibull_aft` | parametric accelerated failure time model | result table and fitter |
| `plot_aft_survival_curves` | predicted survival curves for covariate profiles | figure/axes |
| `train_gradient_survival_boosting` | non-linear survival risk modeling | model, risk scores, concordance |

## Function Parameter Reference

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `plot_kaplan_meier` | `df`, `duration_col`, `event_col` | `group_col`, split options, CI/risk count/style/save/RMST options | `KaplanMeierPlotResult` |
| `create_survival_groups` | `df`, `column`, `method`, `group_col` | `bins`, `labels`, `duplicates` | DataFrame copy |
| `default_tau_from_observed_times` | `df`, `duration_col` | `group_col` | float tau |
| `calculate_rmst` | `df`, `duration_col`, `event_col` | `group_col`, `tau` | RMST DataFrame |
| `compare_rmst` | `df`, `duration_col`, `event_col`, `group_col`, `reference` | `tau` | comparison DataFrame |
| `fit_univariate_cox` | `df`, `duration_col`, `event_col`, `covariates` | `strata`, `robust` | result table and fitters |
| `fit_multivariate_cox` | `df`, `duration_col`, `event_col`, one of `covariates`/`formula` | `strata`, `robust` | result table and fitter |
| `fit_time_varying_cox` | long-format `df`, `event_col`, start/stop columns | `id_col`, `covariates`/`formula`, `strata`, `robust` | result table and fitter |
| `fit_cox_time_interactions` | baseline `df`, `duration_col`, `event_col`, `covariates` | interaction covariates, time transform, intervals | generated long data and fitted model |
| `run_survival_sensitivity_analysis` | `df`, `duration_col`, `event_col`, covariates or formula | RMST/AFT/time-interaction options | guided sensitivity dict |
| `cox_forest_table` | Cox result dict, fitter, or DataFrame | `covariate_col` | reporting DataFrame |
| `survival_prediction_table` | fitted model, feature DataFrame, times | `id_col` | long prediction DataFrame |
| `check_ph_assumptions` | `training_df`, fitted Cox `fitter` | `p_value_threshold`, `show_plots`, `columns`, `advice` | summary/violations dict |
| `schoenfeld_residuals_table` | fitted Cox `fitter`, training DataFrame | scaled/raw residuals | residual DataFrame |
| `schoenfeld_test_table` | fitted Cox `fitter`, training DataFrame | time transform, FDR correction | test DataFrame |
| `plot_schoenfeld_residuals` | residual table | covariates, save options | `(fig, ax)` |
| `fit_weibull_aft` | `df`, `duration_col`, `event_col`, one of `covariates`/`formula` | `robust` | result table and fitter |
| `plot_aft_survival_curves` | `fitter`, `covariates`, `profiles` | `plot_baseline`, `figsize`, `ax`, `plot_kwargs` | figure/axes/fitter dict |
| `train_gradient_survival_boosting` | `X_train`, `duration_train`, `event_train` | test data, `random_state`, model params | model, risk scores, concordance dict |

## Kaplan-Meier Curves

```python
from fyron.survival import plot_kaplan_meier

km = plot_kaplan_meier(
    df,
    duration_col="time",
    event_col="event",
    group_col="stage",
    at_risk_counts=True,
    at_risk_rows=["at_risk"],
    title="Overall survival by stage",
    figsize=(7, 4),
)

km.logrank
km.n_per_group
```

Use Kaplan-Meier plots for descriptive group comparisons. They are especially helpful before fitting adjusted models because they expose censoring patterns and group sizes.
Set `at_risk_rows=["at_risk"]` with `at_risk_counts=True` when you want the compact table that only shows the number at risk. The default, `at_risk_rows="all"`, keeps the lifelines table with at-risk, censored, and event rows. Use a list such as `["at_risk", "events"]` to select row variants and preserve their order.

Add `reference_bands` when a Kaplan-Meier curve should be interpreted against precomputed survival corridors, such as historical trial ranges, bootstrap percentile bands, or clinically defined favorable/intermediate/poor zones. Fyron only visualizes the supplied intervals; it does not estimate those reference bands.

```python
reference_bands = pd.DataFrame(
    {
        "time": [0, 6, 12, 18] * 3,
        "lower": [0.80, 0.72, 0.64, 0.55, 0.50, 0.40, 0.30, 0.22, 0.00, 0.00, 0.00, 0.00],
        "upper": [1.00, 0.94, 0.86, 0.78, 0.80, 0.72, 0.64, 0.55, 0.50, 0.40, 0.30, 0.22],
        "band": ["Favorable"] * 4 + ["Intermediate"] * 4 + ["Poor"] * 4,
    }
)

km = plot_kaplan_meier(
    df,
    duration_col="time",
    event_col="event",
    group_col="treatment",
    reference_bands=reference_bands,
    reference_band_preset="survival",
    reference_band_alpha=0.28,
    title="Overall survival with reference bands",
)
```

Available presets are `"survival"` for `Favorable`/`Intermediate`/`Poor`, `"risk"` for `Low`/`Intermediate`/`High`, and `"percentile"` for percentile-style survival corridors. You can still override `reference_band_order` or `reference_band_colors` for study-specific labels.

### Automatic Risk Groups

You can derive groups from a continuous score:

```python
km = plot_kaplan_meier(
    df,
    duration_col="time",
    event_col="event",
    split_column="risk_score",
    split_method="quartile",
    at_risk_counts=True,
)
```

## Survival Group Construction

```python
from fyron.survival import create_survival_groups

df_q = create_survival_groups(
    df,
    column="risk_score",
    method="quartile",
    out_col="risk_quartile",
)
```

Supported methods include:

| Method | Use |
| --- | --- |
| `categorical` | preserve an existing categorical column |
| `median` | high/low split |
| `tertile` | three risk bands |
| `quartile` | four risk bands |
| `custom` | user-defined bins and labels |

## Survival Inference Corrections

Boosting scores always increase with event risk. For `squared` and `ipcwls`
losses, Fyron negates predicted survival times before returning risk scores or
calculating concordance. The estimator's native predictions remain unchanged.
Recompute prior scores and concordance from those two losses.

`survival_prediction_table` requires `predict_survival_function`; arbitrary
`predict()` scores are no longer converted to probabilities. DataFrame survival
curves use step values rather than nearest future values when reindexing.

Cox fits retain strata and formula predictors. `fit_multivariate_cox` returns
`training_df` with the exact fitting rows and original index; sensitivity
diagnostics reuse it. PH violation flags follow the requested p-value adjustment.
Unrelated missing columns do not remove patients from the fitting cohort.

Time interactions are piecewise constant over common intervals from `n_intervals`
or `breakpoints`. Their transform uses the common right endpoint, even if a
patient's follow-up ends earlier within that interval. This is an explicit grid
approximation, not an exact continuous-time coefficient model; consider grid
sensitivity. Refit earlier generated time-interaction models whose covariates
depended on individual future follow-up times.

## Restricted Mean Survival Time

RMST is often easier to interpret clinically than a hazard ratio because it estimates average event-free time up to a fixed horizon `tau`.

```python
from fyron.survival import calculate_rmst, compare_rmst

rmst = calculate_rmst(
    df,
    duration_col="time",
    event_col="event",
    group_col="treatment",
    tau=365,
)

contrast = compare_rmst(
    df,
    duration_col="time",
    event_col="event",
    group_col="treatment",
    reference="standard",
    tau=365,
)
```

Choose `tau` before looking at results when possible. It should be within the range where the survival curve is still supported by enough patients.

`rmst_se` is the standard error of the estimated RMST, computed by integrating
Kaplan-Meier covariance with Greenwood weights, following
[survRM2's one-group calculation](https://github.com/cran/survRM2/blob/044089fcdd77b46e754cd18ac6d7f21498ce5e73/R/rmst1.R#L23-L27).
Each event-time contribution is its squared remaining KM area up to `tau`,
multiplied by `d / (Y * (Y - d))`, where `Y` is the risk count and `d` the
event count. A terminal event exhausting the risk set contributes zero.
This is the variance of the estimated mean, not the variance of individual
restricted survival times returned by `lifelines` with `return_variance=True`.

Intervals are two-sided 95% normal intervals without clipping to `[0, tau]`.
Group comparisons assume independent groups and add their estimator variances.
When the comparison standard error is zero, the interval collapses to a point
and `p_value` is `NaN`. These asymptotic intervals can be unreliable with sparse
events; no observed events produces a zero plug-in standard error, not proof of
zero uncertainty in the population.

`tau` must be finite and positive. Its default is the smallest group-specific
maximum follow-up (the overall maximum without grouping). An explicit `tau`
beyond follow-up continues the final KM survival level unchanged for compatibility;
this relies on an unsupported tail when that level is positive.

**RMST inference correction:** Earlier calculations used the individual-time
variance as estimator variance, producing incorrect standard errors, intervals,
and comparison p-values. Recompute these quantities for existing analyses.
RMST point estimates remain unchanged.

## Cox Regression

```python
from fyron.survival import fit_univariate_cox, fit_multivariate_cox

uni = fit_univariate_cox(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score", "tumor_volume"],
)

multi = fit_multivariate_cox(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score", "tumor_volume"],
)

multi["results"]
```

The results table includes hazard ratios, confidence intervals, p-values, row counts, and concordance information when available.

For reporting and forest plots:

```python
from fyron.survival import cox_forest_table

forest = cox_forest_table(multi)
```

For fixed-time survival or event-risk tables:

```python
from fyron.survival import survival_prediction_table

predictions = survival_prediction_table(
    multi["fitter"],
    df[["age", "risk_score", "tumor_volume"]],
    times=[365, 730],
)
```

### Formula Interface

Use formulas for categorical terms or interactions supported by lifelines:

```python
multi = fit_multivariate_cox(
    df,
    duration_col="time",
    event_col="event",
    formula="age + risk_score + C(stage)",
)
```

## Proportional Hazards Diagnostics

```python
from fyron.survival import check_ph_assumptions

diagnostics = check_ph_assumptions(
    df.dropna(),
    multi["fitter"],
    show_plots=False,
)

diagnostics["summary"]
diagnostics["violations"]
```

Use these checks before interpreting Cox coefficients as time-constant hazard ratios.

For manuscript supplements and reviewer-facing diagnostics, export the residual and test tables explicitly:

```python
from fyron.survival import (
    plot_schoenfeld_residuals,
    schoenfeld_residuals_table,
    schoenfeld_test_table,
)

residuals = schoenfeld_residuals_table(multi["fitter"], df.dropna())
ph_tests = schoenfeld_test_table(
    multi["fitter"],
    df.dropna(),
    method="rank",
    p_adjust="fdr_bh",
)

fig, ax = plot_schoenfeld_residuals(
    residuals,
    covariates=["age", "risk_score"],
)
```

Low p-values suggest possible time-varying effects. They do not automatically invalidate a study; they indicate that the model interpretation needs review, such as stratification, time interactions, RMST, or AFT modeling.

## PH Violation Sensitivity Workflow

Use the guided helper when you want one object that collects the primary Cox model, Schoenfeld diagnostics, and common sensitivity analyses.

```python
from fyron.survival import run_survival_sensitivity_analysis

sensitivity = run_survival_sensitivity_analysis(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score", "tumor_volume"],
    group_col="risk_group",
    rmst_tau=24,
    time_interaction_covariates=["risk_score"],
)

sensitivity["ph_diagnostics"]["summary"]
sensitivity["violating_covariates"]
sensitivity["time_interaction_cox"]["results"]
sensitivity["weibull_aft"]["results"]
sensitivity["rmst"]
sensitivity["recommendations"]
```

The helper does not decide which model is clinically correct. It keeps the alternatives together so reviewers can see the assumptions: Cox PH for adjusted hazard ratios, time-interaction Cox for effects that change over follow-up, RMST for absolute time differences, and Weibull AFT for time-ratio interpretation.

## Time-Interaction Cox Models

For baseline covariates that may change effect over follow-up, generate covariate-by-time terms and fit a start-stop Cox model:

```python
from fyron.survival import fit_cox_time_interactions

time_cox = fit_cox_time_interactions(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score"],
    time_interaction_covariates=["risk_score"],
    time_transform="log",
    n_intervals=8,
)

time_cox["interaction_columns"]
time_cox["results"]
```

For already-long start-stop data, fit the time-varying Cox model directly:

```python
from fyron.survival import fit_time_varying_cox

tv = fit_time_varying_cox(
    long_df,
    event_col="event",
    start_col="start",
    stop_col="stop",
    id_col="patient_id",
    covariates=["treatment", "risk_score"],
)
```

Every interval must satisfy `start < stop`, and only the final interval for a patient should usually carry the event indicator.

## Weibull AFT

AFT models describe covariate effects on survival time rather than instantaneous hazard.

```python
from fyron.survival import fit_weibull_aft, plot_aft_survival_curves

aft = fit_weibull_aft(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score"],
)

plot_aft_survival_curves(
    aft["fitter"],
    covariates="risk_score",
    profiles=[{"risk_score": -1.0}, {"risk_score": 1.0}],
    figsize=(6, 4),
)
```

## Gradient Survival Boosting

Gradient survival boosting is useful when you expect non-linear or interaction effects and want a risk ranking for censored outcomes.

```python
from fyron.survival import train_gradient_survival_boosting

boosted = train_gradient_survival_boosting(
    X_train,
    duration_train=train_df["time"],
    event_train=train_df["event"],
    X_test=X_test,
    duration_test=test_df["time"],
    event_test=test_df["event"],
    n_estimators=300,
    learning_rate=0.05,
    max_depth=2,
    random_state=42,
)

boosted["concordance_index"]
boosted["risk_score"]
```

Returned keys include:

| Key | Meaning |
| --- | --- |
| `model` | fitted `GradientBoostingSurvivalAnalysis` |
| `risk_score` | evaluation-set risk scores |
| `concordance_index` | evaluation concordance |
| `train_risk_score` | training-set risk scores |
| `train_concordance_index` | training concordance |
| `y_train` / `y_eval` | structured survival arrays used by scikit-survival |

Higher risk scores indicate higher event risk.

## Practical Checklist

- Confirm `time` values are positive.
- Confirm `event` uses `1` for event and `0` for censored.
- Plot Kaplan-Meier curves before modeling.
- Report group sizes and censoring patterns.
- Use RMST when an absolute time difference is more interpretable than a hazard ratio.
- Check PH assumptions before relying on Cox PH interpretations.
- Treat survival boosting as a prediction/ranking model, not a replacement for causal survival analysis.

## Return Values

| Function family | Return shape | Notes |
| --- | --- | --- |
| Kaplan-Meier plotting | `KaplanMeierPlotResult` | Includes figure/axes plus group counts and log-rank details when available. |
| RMST helpers | DataFrame | One row per group or contrast. |
| Cox/AFT helpers | dict with result table and fitted model | Keep both the table and fitter for diagnostics or plotting. |
| PH diagnostics | dict | Includes summary tables and violation flags. |
| survival boosting | dict | Includes model, risk scores, concordance, and structured survival arrays. |

## Common Pitfalls

- Do not use a post-diagnosis or post-treatment variable as if it were baseline.
- Do not interpret Cox hazard ratios without checking proportional hazards.
- Do not choose `tau` for RMST only after inspecting the most favorable result.
- Do not compare KM curves without checking group sizes and censoring.
- Ensure all duration columns use the same time unit.

## Related Modules

- [Cohort Tables](cohort.md) for building `time` and `event`.
- [Descriptive Analysis](descriptive.md) for endpoint summaries before modeling.
- [Clinical Plotting](plotting.md) for KM and survival validation figures.
- [Model Validation](validation.md) for survival risk score validation.
