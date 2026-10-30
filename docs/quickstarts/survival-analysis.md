# Quickstart: Survival Analysis

Use this when your cohort already has duration and event columns.

For endpoint construction through evaluation, use the [recommended survival workflow](../survival-workflow.md) and its runnable synthetic example.

## Install

```bash
uv add "fyron[survival]"
```

## Plot Kaplan-Meier Curves

```python
import pandas as pd

from fyron.survival import check_ph_assumptions, fit_multivariate_cox, plot_kaplan_meier

cohort = pd.DataFrame(
    {
        "time": [4, 8, 10, 13, 15, 19, 23, 30],
        "event": [1, 0, 1, 1, 0, 1, 0, 1],
        "risk_group": ["low", "low", "high", "high", "low", "high", "low", "high"],
        "age": [58, 61, 73, 69, 54, 77, 63, 71],
    }
)

fig, ax = plot_kaplan_meier(
    cohort,
    duration_col="time",
    event_col="event",
    group_col="risk_group",
    at_risk_counts=["At risk"],
)
```

## Fit A Cox Model

```python
cox = fit_multivariate_cox(
    cohort,
    duration_col="time",
    event_col="event",
    covariates=["age"],
)

ph = check_ph_assumptions(cox.model, cohort[["time", "event", "age"]])
print(ph.summary)
```

## Next Steps

- Read [Survival Analysis](../modules/survival.md) for RMST, Weibull AFT, Cox forest tables, and proportional hazards diagnostics.
- Use [Survival PH Diagnostics Guide](../examples/survival-ph-diagnostics-guide.md) for Schoenfeld residual interpretation.
