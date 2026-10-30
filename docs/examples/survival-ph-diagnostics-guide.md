# Survival Models and Proportional Hazards Diagnostics in Fyron

This guide shows how to use Fyron for Kaplan-Meier curves, Cox proportional hazards models, Schoenfeld residual diagnostics, RMST, and Weibull accelerated failure time models.

## Install

```bash
pip install "fyron[survival]"
```

## Data Requirements

Use one row per patient or observation unit.

Required columns:

- `time`: positive follow-up duration.
- `event`: event indicator, where `1` means event and `0` means censored.

Optional columns:

- Group columns, for example `stage`, `treatment`, or `risk_group`.
- Covariates, for example `age`, `sex`, `risk_score`, imaging features, or laboratory values.

```python
import pandas as pd

df = pd.read_csv("survival_cohort.csv")
```

## 1. Plot Kaplan-Meier Curves

Kaplan-Meier curves are descriptive survival curves. They are useful before modeling because they show group separation, censoring patterns, and approximate group sizes over time.

```python
from fyron.survival import plot_kaplan_meier

km = plot_kaplan_meier(
    df,
    duration_col="time",
    event_col="event",
    group_col="risk_group",
    at_risk_counts=True,
    at_risk_rows=["at_risk"],
    show_censors=True,
    annotate_logrank=True,
    title="Survival by risk group",
    figsize=(7, 4),
)

km.figure.savefig("kaplan_meier.png", dpi=300, bbox_inches="tight")
km.logrank
km.n_per_group
```

Risk table options:

```python
at_risk_rows="all"                  # At risk, censored, and events
at_risk_rows=["at_risk"]            # Only at-risk row
at_risk_rows=["at_risk", "events"]  # Selected rows in this order
```

Important interpretation note: Kaplan-Meier curves do not require the proportional hazards assumption. The log-rank test is often most natural when hazards are approximately proportional, but the plot itself is descriptive.

## 2. Fit a Cox Proportional Hazards Model

Use Cox PH when you want adjusted hazard ratios and can defend the proportional hazards assumption.

```python
from fyron.survival import fit_multivariate_cox

cox = fit_multivariate_cox(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score"],
)

cox["results"]
cox["concordance_index"]
cox["n_used"]
cox["n_excluded"]
```

For categorical variables or interactions, use the formula interface:

```python
cox = fit_multivariate_cox(
    df,
    duration_col="time",
    event_col="event",
    formula="age + risk_score + C(stage)",
)

cox["results"]
```

The `results` table contains hazard ratios, confidence intervals, and p-values.

## 3. Check Proportional Hazards Assumptions

Before interpreting Cox coefficients as time-constant hazard ratios, run Schoenfeld-based diagnostics.

```python
from fyron.survival import check_ph_assumptions

diagnostics = check_ph_assumptions(
    df.dropna(),
    cox["fitter"],
    p_value_threshold=0.05,
    show_plots=False,
)

diagnostics["summary"]
diagnostics["violations"]
diagnostics["warnings"]
diagnostics["suggestions"]
```

Return values:

- `summary`: long-form Schoenfeld proportional hazards test table.
- `violations`: covariates with p-values below the threshold.
- `warnings`: short text warnings when possible violations are found.
- `suggestions`: modeling options to consider.
- `plot_axes`: axes returned by lifelines when `show_plots=True`.
- `residuals`: residual table when `include_residuals=True`.

Low p-values suggest possible time-varying effects. They do not automatically invalidate the analysis, but they mean the Cox PH interpretation needs review.

## 4. Export Schoenfeld Test and Residual Tables

For manuscripts, supplements, or reviewer responses, export the diagnostic tables directly.

```python
from fyron.survival import (
    schoenfeld_residuals_table,
    schoenfeld_test_table,
)

ph_tests = schoenfeld_test_table(
    cox["fitter"],
    df.dropna(),
    method="rank",
    p_adjust="fdr_bh",
)

residuals = schoenfeld_residuals_table(
    cox["fitter"],
    df.dropna(),
    scaled=True,
)

ph_tests.to_csv("cox_ph_schoenfeld_tests.csv", index=False)
residuals.to_csv("cox_schoenfeld_residuals.csv", index=False)
```

Common `method` values:

```python
method="rank"
method="km"
method=["rank", "km"]
```

## 5. Plot Schoenfeld Residuals

Residual plots help inspect whether covariate effects appear to drift over follow-up time.

```python
from fyron.survival import plot_schoenfeld_residuals

fig, ax = plot_schoenfeld_residuals(
    residuals,
    covariates=["age", "risk_score"],
    title="Scaled Schoenfeld residuals",
)

fig.savefig("cox_schoenfeld_residuals.png", dpi=300, bbox_inches="tight")
```

## 6. What To Do If PH Is Violated

If the proportional hazards diagnostics suggest violations, common next steps are:

- Stratify Cox models for categorical variables with non-proportional baseline hazards.
- Add time-varying effects or interactions with functions of time.
- Report RMST as an absolute time-based summary.
- Use an accelerated failure time model when time-ratio interpretation is more appropriate.

Fyron can keep these sensitivity analyses together:

```python
from fyron.survival import run_survival_sensitivity_analysis

sensitivity = run_survival_sensitivity_analysis(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score"],
    group_col="risk_group",
    rmst_tau=24,
    time_interaction_covariates=["risk_score"],
)

sensitivity["violating_covariates"]
sensitivity["time_interaction_cox"]["results"]
sensitivity["weibull_aft"]["results"]
sensitivity["rmst"]
sensitivity["recommendations"]
```

This helper is not an automatic model-selection rule. It is a structured way to present the primary Cox PH model together with sensitivity analyses when proportional hazards are questionable.

## 7. Use RMST When PH Is Questionable

Restricted mean survival time can be easier to interpret than hazard ratios, especially when survival curves cross or hazards are not proportional.

```python
from fyron.survival import calculate_rmst, compare_rmst

rmst = calculate_rmst(
    df,
    duration_col="time",
    event_col="event",
    group_col="risk_group",
    tau=24,
)

rmst_comparison = compare_rmst(
    df,
    duration_col="time",
    event_col="event",
    group_col="risk_group",
    reference="low",
    tau=24,
)

rmst
rmst_comparison
```

Choose `tau` based on a clinically meaningful follow-up horizon or a prespecified common follow-up time.

## 8. Fit a Weibull AFT Model

Weibull AFT models describe covariate effects on survival time rather than instantaneous hazard. They do not rely on the Cox proportional hazards assumption for their main interpretation.

```python
from fyron.survival import fit_weibull_aft, plot_aft_survival_curves

aft = fit_weibull_aft(
    df,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score"],
)

aft["results"]
aft["AIC"]
aft["concordance_index"]
```

Plot predicted AFT survival curves for example profiles:

```python
profiles = [
    {"age": 55, "risk_score": -1.0},
    {"age": 55, "risk_score": 1.0},
]

out = plot_aft_survival_curves(
    aft["fitter"],
    covariates=["age", "risk_score"],
    profiles=profiles,
    figsize=(7, 4),
)

out["figure"].savefig("weibull_aft_profiles.png", dpi=300, bbox_inches="tight")
```

## 9. Fit Cox Time-Interaction Models

If Schoenfeld tests flag a baseline covariate, a Cox model with a generated interaction against follow-up time can show whether the effect changes over time.

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

For long-format data that already has one row per patient interval, use the start-stop helper directly:

```python
from fyron.survival import fit_time_varying_cox

tv_cox = fit_time_varying_cox(
    long_df,
    event_col="event",
    start_col="start",
    stop_col="stop",
    id_col="patient_id",
    covariates=["risk_score", "current_treatment"],
)

tv_cox["results"]
```

## Suggested Reporting Flow

1. Plot Kaplan-Meier curves with an at-risk table.
2. Fit unadjusted and adjusted Cox PH models when hazard ratios are the target estimand.
3. Run Schoenfeld proportional hazards diagnostics.
4. If diagnostics are acceptable, report Cox hazard ratios with confidence intervals.
5. If diagnostics suggest violations, add sensitivity analyses using RMST, stratified/time-interaction Cox models, start-stop Cox models, or Weibull AFT.
6. Export diagnostic tables and figures for reproducibility.

## Minimal End-to-End Example

```python
from fyron.survival import (
    calculate_rmst,
    check_ph_assumptions,
    fit_multivariate_cox,
    fit_cox_time_interactions,
    fit_weibull_aft,
    plot_kaplan_meier,
    plot_schoenfeld_residuals,
    schoenfeld_residuals_table,
    schoenfeld_test_table,
)

km = plot_kaplan_meier(
    df,
    "time",
    "event",
    group_col="risk_group",
    at_risk_counts=True,
    at_risk_rows=["at_risk"],
    annotate_logrank=True,
)

cox = fit_multivariate_cox(
    df,
    "time",
    "event",
    formula="age + risk_score + C(stage)",
)

ph = check_ph_assumptions(df.dropna(), cox["fitter"], show_plots=False)
ph_tests = schoenfeld_test_table(cox["fitter"], df.dropna(), method=["rank", "km"])
residuals = schoenfeld_residuals_table(cox["fitter"], df.dropna())
fig, ax = plot_schoenfeld_residuals(residuals)

rmst = calculate_rmst(df, "time", "event", group_col="risk_group", tau=24)
time_cox = fit_cox_time_interactions(
    df,
    "time",
    "event",
    covariates=["age", "risk_score"],
    time_interaction_covariates=["risk_score"],
)
aft = fit_weibull_aft(df, "time", "event", formula="age + risk_score + C(stage)")
```

## Function Cheat Sheet

| Question | Fyron function |
| --- | --- |
| Show descriptive survival curves | `plot_kaplan_meier` |
| Fit adjusted Cox hazard ratios | `fit_multivariate_cox` |
| Fit separate univariate Cox models | `fit_univariate_cox` |
| Check proportional hazards assumptions | `check_ph_assumptions` |
| Export Schoenfeld PH test table | `schoenfeld_test_table` |
| Export Schoenfeld residual table | `schoenfeld_residuals_table` |
| Plot Schoenfeld residuals | `plot_schoenfeld_residuals` |
| Run guided PH-violation sensitivity workflow | `run_survival_sensitivity_analysis` |
| Fit Cox time-interaction terms | `fit_cox_time_interactions` |
| Fit start-stop time-varying Cox model | `fit_time_varying_cox` |
| Estimate restricted mean survival time | `calculate_rmst` |
| Compare RMST between groups | `compare_rmst` |
| Fit Weibull accelerated failure time model | `fit_weibull_aft` |
| Plot AFT survival profiles | `plot_aft_survival_curves` |
