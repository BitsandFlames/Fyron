# Manuscript Statistics Workflow

This tutorial shows the data-science layer often needed for a scientific paper: Table 1 support, FDR correction, classical regression tables, model-comparison tests, Cox proportional hazards diagnostics, and exportable manuscript artifacts.

## Synthetic Cohort

```python
import numpy as np
import pandas as pd

from fyron import statistics as fst
from fyron.survival import (
    fit_multivariate_cox,
    plot_schoenfeld_residuals,
    schoenfeld_residuals_table,
    schoenfeld_test_table,
)

rng = np.random.default_rng(42)
n = 160

cohort = pd.DataFrame(
    {
        "age": rng.normal(64, 9, n),
        "stage": rng.choice(["I", "II", "III"], n),
        "l3_sma_cm2": rng.normal(120, 18, n),
        "vat_ml": rng.normal(240, 55, n),
        "risk_score": rng.normal(0, 1, n),
        "time": rng.exponential(16, n) + 1,
        "event": rng.binomial(1, 0.55, n),
    }
)
cohort["response"] = rng.binomial(1, 1 / (1 + np.exp(-(0.04 * cohort["age"] + cohort["risk_score"] - 3))))
```

## Statistical QC

```python
normality = fst.normality_table(
    cohort,
    ["age", "l3_sma_cm2", "vat_ml", "risk_score"],
)

correlations = fst.correlation_pvalue_table(
    cohort,
    ["age", "l3_sma_cm2", "vat_ml", "risk_score"],
    method="spearman",
    p_adjust="fdr_bh",
)

missingness = fst.missingness_by_group_table(
    cohort,
    group_col="stage",
    columns=["age", "l3_sma_cm2", "vat_ml", "risk_score"],
)

outliers = fst.outlier_table(
    cohort,
    ["age", "l3_sma_cm2", "vat_ml", "risk_score"],
)
```

## Regression Tables

```python
logistic = fst.fit_logistic_regression_table(
    cohort,
    outcome_col="response",
    covariates=["age", "stage", "l3_sma_cm2", "vat_ml"],
    p_adjust="fdr_bh",
)

linear = fst.fit_linear_regression_table(
    cohort,
    outcome_col="risk_score",
    covariates=["age", "stage", "l3_sma_cm2", "vat_ml"],
)

vif = fst.vif_table(
    cohort,
    ["age", "stage", "l3_sma_cm2", "vat_ml"],
)
```

## Model Comparison

```python
y_true = cohort["response"]
pred_a = (cohort["risk_score"] > 0).astype(int)
pred_b = (cohort["age"] > cohort["age"].median()).astype(int)
prob_a = 1 / (1 + np.exp(-cohort["risk_score"]))
prob_b = 1 / (1 + np.exp(-(cohort["age"] - cohort["age"].mean()) / cohort["age"].std()))

mcnemar = fst.mcnemar_test(y_true, pred_a, pred_b)
auc_diff = fst.bootstrap_auc_difference(
    y_true,
    prob_a,
    prob_b,
    n_rounds=2000,
    random_state=42,
)
```

## Cox PH And Schoenfeld Diagnostics

```python
cox = fit_multivariate_cox(
    cohort,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score", "l3_sma_cm2"],
)

residuals = schoenfeld_residuals_table(cox["fitter"], cohort.dropna())
ph_tests = schoenfeld_test_table(
    cox["fitter"],
    cohort.dropna(),
    method="rank",
    p_adjust="fdr_bh",
)

fig, ax = plot_schoenfeld_residuals(
    residuals,
    covariates=["age", "risk_score"],
)
```

## Save Paper Artifacts

```python
normality.to_csv("normality.csv", index=False)
correlations.to_csv("correlations_fdr.csv", index=False)
logistic.to_csv("logistic_regression_or_table.csv", index=False)
cox["results"].to_csv("cox_results.csv", index=False)
ph_tests.to_csv("schoenfeld_ph_tests.csv", index=False)
fig.savefig("schoenfeld_residuals.png", bbox_inches="tight", dpi=300)
```

Use these outputs in the Results section and supplement, but keep the analysis plan explicit: correction method, endpoint coding, covariate selection, and Cox PH interpretation should be decided before final reporting.
