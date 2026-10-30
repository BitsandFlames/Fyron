# One Survival Workflow, Explicit Decisions

Use small functions, not a mandatory pipeline. This development update preserves
public imports, signatures, result types, and columns while sharing internal
validation and fitting-cohort preparation.

## Choose the Right Function

| Task | Recommended entry point | Meaning |
| --- | --- | --- |
| Join predictors and outcomes | `fyron.cohort.join_cohort_tables` | Validated join; not endpoint selection |
| Duration from an already-selected endpoint | `fyron.cohort.build_survival_columns` | Subtract start from end; use the supplied event indicator |
| Choose between event and censoring dates | `fyron.cohort.build_time_to_event_endpoint` | Select the earlier date; ties count as events |
| Prepare predictors | `fyron.preprocessing` | Explicit preprocessing, fit using training data only |
| Fit Cox or Weibull AFT | `fyron.survival` | Estimation and fitting-cohort accounting |
| Check proportional hazards | `fyron.survival.check_ph_assumptions` | Use the exact Cox `training_df` |
| Evaluate locked predictions | `fyron.validation` | Censoring-aware metrics on evaluation data |
| Plot results | `fyron.plotting` | Recommended plotting facade |

The two endpoint builders are not duplicates. The date-selection builder has
explicit event/censoring rules and time units. The simpler builder accepts an
endpoint decision already made by the researcher. Neither determines which
clinical endpoint is appropriate for a study.

`fyron.plotting.plot_kaplan_meier`, `fyron.ml.plot_kaplan_meier`, and the survival
entry point use the same implementation. Existing imports remain supported;
no deprecation or migration is required.

## Prepare and Inspect

Event indicators are binary: `1` is an event and `0` is censored. Fitting and
validation reject missing or nonfinite outcomes before selecting complete
predictor rows. No outcome is imputed and zero durations are never shifted.
Endpoint construction can retain missing endpoints when explicitly permitted;
these rows must be resolved or explicitly excluded before fitting.

KM, RMST, and the existing Cox paths support nonnegative durations. Weibull AFT,
boosting, and survival validation require strictly positive durations. Fixed
prediction horizons and RMST `tau` must be finite and positive. Do not assume a
cohort accepted by one method automatically satisfies another method's contract.

Document the time unit. Date-based subtraction in `build_survival_columns` uses
days; numeric columns retain their original unit. The date-selection builder
accepts days, weeks, months, or years using its documented conversion factors.

## Fit and Account for Exclusions

Cox and AFT now share preparation of explicitly selected predictors or formula
terms. Missing predictors are excluded using complete cases, including formula
transformations and categorical terms. Unrelated missing columns do not exclude
rows. Nonfinite transformed predictors raise instead of being silently accepted.
Original indices and required stratum columns are retained.

Both multivariate Cox and AFT results provide `results`, `fitter`, `n_used`,
`n_excluded`, `formula_used`, and `training_df`. AFT's `training_df` is additive.
Model-specific keys remain unchanged. Univariate Cox remains a collection of
separate fits, so sample sizes can differ by predictor. Do not assume every
model was fitted to the same rows simply because it received the same input.

AFT formula exclusions are now counted before fitting. If earlier analyses used
missing formula predictors, review their cohort counts and rerun them. The
estimator itself has not been replaced. Model assumptions still require scientific
review, and complete-case selection may introduce bias.

## Validate Predictions

Risk scores and event probabilities are different quantities. Concordance expects
higher scores to mean greater risk; it does not require probabilities. Undefined
concordance returns `NaN`, not zero. Bootstrap summaries retain valid/dropped
replicate counts. Boosting retains its loss-specific risk-direction conversion.

Brier scoring and calibration require genuine event probabilities at an explicit
horizon. No sigmoid conversion of an arbitrary score is used. An explicit
`censoring_df` must use the same outcome column names; otherwise censoring is
estimated from the evaluation cohort. Unsupported horizons and undefined
censoring weights raise. Clinical transportability and censoring assumptions
remain the researcher's responsibility.

## Run the Synthetic Example

Install `fyron[survival-ml]` for the complete example, or `fyron[survival]` for
classical estimation without scikit-survival validation. Shared data helpers do
not import lifelines, formulaic, or scikit-survival until their functionality is
needed. No extra dependency was added.

From a checkout of Fyron:

```bash
uv run python examples/survival_workflow.py --output-dir /tmp/fyron-survival-example
```

The script constructs censored synthetic endpoints in days, splits training and
evaluation data, demonstrates three training predictor exclusions, fits Cox and
AFT, checks PH using the fitting cohort, evaluates one-year predictions with an
explicit censoring-reference cohort, and writes tables and a KM figure. It does
not choose a model automatically or establish that PH or Weibull assumptions hold
in a real study.

Endpoint and join audits now precede fitting. The example adds one deliberately
unresolved follow-up row, reviews it, and explicitly excludes it using
`positive_duration_eligible`; it is never counted as observed censoring. An
administrative cutoff caps the remaining follow-up without creating missing
endpoints. `endpoint-quality.csv` and `join-quality.csv` record aggregate decisions.
See [cohort auditing](modules/cohort.md) for flag definitions and blocking issues.
