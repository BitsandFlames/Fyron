# Example: Clinical Data Science

This example combines cohort construction, tabular ML, survival analysis, and plots.

Use this pattern when you already have a patient-level table or when feature engineering has produced one row per patient. The same cohort can support survival analysis and classification, but the endpoints should be defined separately: `time`/`event` for time-to-event analysis, and a separate `binary_endpoint` for classification.

## What This Example Demonstrates

- Validate the cohort before modeling.
- Build survival columns from explicit dates.
- Compare groups with Kaplan-Meier curves.
- Fit an adjusted Cox model for interpretable hazard ratios.
- Train a classifier and inspect clinical metrics.
- Generate correlation and metric plots for reporting.

```python
from fyron.cohort import build_survival_columns, validate_cohort_table
from fyron.survival import plot_kaplan_meier, fit_multivariate_cox
from fyron import ml

cohort = build_survival_columns(
    cohort,
    start_col="index_date",
    end_col="last_followup_or_event_date",
    event_col="event",
)

validate_cohort_table(
    cohort,
    required_columns=["patient_id", "time", "event", "age", "risk_score"],
)

km = plot_kaplan_meier(
    cohort,
    duration_col="time",
    event_col="event",
    group_col="treatment",
    at_risk_counts=True,
)

cox = fit_multivariate_cox(
    cohort,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score"],
)

X = cohort[["age", "risk_score", "lab_value"]]
y = cohort["binary_endpoint"]

model = ml.run_classification_pipeline(
    X,
    y,
    model="random_forest",
    use_grid_search=True,
    random_state=42,
    plot=True,
)

ml.plot_correlation_heatmap(X, method="spearman")
ml.plot_metric_bars({"Random Forest": model["metrics"]})
```

Review the survival and ML outputs together, but do not treat them as interchangeable. A Cox model explains time-to-event associations; a classifier estimates a binary endpoint under a specific prediction setup.
