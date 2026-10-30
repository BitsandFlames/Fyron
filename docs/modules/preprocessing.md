# Preprocessing And Cohort QC

See the [survival workflow](../survival-workflow.md) for explicit predictor preparation. Survival fits do not impute outcomes or predictors; inspect their returned fitting-cohort counts before interpreting results.

`fyron.preprocessing` provides small quality-control tables for clinical feature matrices before modeling or survival analysis. Use it to inspect missingness, duplicate patient identifiers, categorical levels, train/test balance, and column names that may leak outcomes.

If the feature matrix still needs ICD-10 groups, OPS categories, exact code indicators, age-at-baseline, or time-window flags, create those first with [DataFrame Operations](dataframe.md). Then use preprocessing for imputation, stable categorical encoding, and leakage checks.

## Install

```bash
uv add fyron
```

## Imports

```python
from fyron import preprocessing as fp
```

## API Contract

Imputation refuses to overwrite existing `<column>_was_missing` fields. Nullable integer columns can receive fractional fitted fills, and categorical columns retain their values when the fitted fill level must be added.

One-hot encoding rejects output-name collisions, both between sanitized category
names (for example `A/B` and `A B`) and with retained input columns. Rename the
conflicting levels or columns before fitting/applying; values are never silently
overwritten. Numeric imputation indicators flag missing values **after** numeric
conversion, so malformed numeric strings that are imputed are also flagged.
Rebuild previously affected encoded tables and missingness indicators.

| Topic | Contract |
| --- | --- |
| Input shape | Cohort or feature-matrix DataFrames; encoders/imputers are plain dictionaries returned by fit helpers. |
| Required columns | ID, group, numeric, categorical, or feature columns named in the call must exist. |
| Return shape | QC tables, transformed DataFrames, or `(DataFrame, transformer_dict)` tuples. |
| Saved artifacts | Save QC reports, imputation plans, encoding plans, and learned transformer dictionaries when reproducibility matters. |
| Failure modes | Missing columns, unsupported strategies, nonnumeric columns passed as numeric, unseen categorical levels, or leakage flags requiring review. |

## Function Reference

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `summarize_missingness(df, ...)` | `df` | `columns`, `group_col` | missingness DataFrame |
| `find_duplicate_ids(df, ...)` | `df` | `id_col="patient_id"` | duplicate rows with counts |
| `summarize_categorical_levels(df, ...)` | `df` | `columns`, `max_levels`, `include_missing` | level count table |
| `compare_train_test_balance(train, test, ...)` | `train`, `test` | `columns` | train/test balance DataFrame |
| `detect_potential_leakage(columns, ...)` | DataFrame or column list | outcome/time keywords | suspicious column table |
| `feature_matrix_report(X, ...)` | feature matrix | labels, rare threshold, leakage keywords | one-row-per-feature QC table |
| `summarize_imputation_plan(df, ...)` | `df` | numeric/categorical columns and strategies | imputation plan table |
| `fit_imputer(df, ...)` | training DataFrame | strategies, fill values, missing indicators | imputer dict |
| `apply_imputer(df, imputer)` | DataFrame and imputer | none | imputed DataFrame |
| `impute_dataframe(df, ...)` | DataFrame | same as `fit_imputer` | `(DataFrame, imputer)` |
| `summarize_encoding_plan(df, ...)` | `df` | columns, max levels | encoding plan table |
| `fit_categorical_encoder(df, ...)` | training DataFrame | columns, rare category settings, drop first | encoder dict |
| `apply_categorical_encoder(df, encoder)` | DataFrame and encoder | none | encoded DataFrame |
| `encode_categorical(df, ...)` | DataFrame | same as `fit_categorical_encoder` | `(DataFrame, encoder)` |

## Example

```python
from fyron import preprocessing as fp

missing = fp.summarize_missingness(
    cohort,
    columns=["age", "sex", "l3_sma_cm2", "event"],
    group_col="risk_group",
)

duplicates = fp.find_duplicate_ids(cohort, id_col="patient_id")
levels = fp.summarize_categorical_levels(cohort, columns=["sex", "stage"])
leakage = fp.detect_potential_leakage(cohort)
feature_qc = fp.feature_matrix_report(cohort[feature_cols], cohort["event"])
```

Use these tables before dropping rows or fitting models. They are meant to make data-cleaning decisions visible in notebooks and analysis supplements.

## Research Decision: Feature Matrix Readiness

Before a model is trained, save a feature matrix report. It flags constant columns, missingness, rare binary variables, and column names that look like outcomes or post-index information.

```python
feature_qc = fp.feature_matrix_report(
    X_train,
    y_train,
    rare_threshold=0.01,
)
```

Treat leakage flags as review prompts, not automatic exclusions. A column named `last_followup_days` is usually suspicious in a baseline prediction model, but a column named `baseline_event_count` may be legitimate if it was measured before the index date.

## Imputation

Fit imputation on training data and apply the learned fill values to validation or external cohorts.

```python
imputer = fp.fit_imputer(
    train,
    numeric=["age", "l3_sma_cm2"],
    categorical=["sex", "stage"],
    strategy_numeric="median",
    strategy_categorical="most_frequent",
    add_missing_indicators=True,
)

train_imp = fp.apply_imputer(train, imputer)
external_imp = fp.apply_imputer(external, imputer)
```

The imputer is a plain dictionary with `numeric`, `categorical`, `strategies`,
`fill_values`, `add_missing_indicators`, and `metadata`. Outcomes should never be
included in predictor imputation. All-missing numeric training columns fall back
to `fill_value_numeric`; review these explicitly rather than treating the fill
as a learned clinical value.

## Encoding

Use Fyron’s encoder when you need stable one-hot columns across train/test splits without adding a pipeline object.

```python
encoder = fp.fit_categorical_encoder(
    train_imp,
    columns=["sex", "stage"],
    rare_min_count=5,
)

X_train = fp.apply_categorical_encoder(train_imp, encoder)
X_external = fp.apply_categorical_encoder(external_imp, encoder)
```

Unseen levels map to `__rare__` only when that level exists in the fitted encoder.
Setting `rare_min_count` does not itself create a rare level if every training
category meets the threshold. Otherwise unseen values produce all-zero indicator
columns. Missing values are represented as `__missing__` before category matching;
if that level was absent in training, the same unknown-level rules apply.

With `drop_first=True`, the omitted reference level also produces all-zero
indicators. These outputs therefore cannot distinguish an unseen category from
the reference category. Inspect evaluation categories before transforming them.
Encoding does not infer that unknown values are clinically equivalent.

## Executable Train/Evaluation Example

```bash
uv run python examples/research_contracts.py --output-dir /tmp/fyron-contracts
```

This synthetic repository example fits median imputation and category levels on
training data only, applies the same specifications to evaluation data, selects
the same ordered feature columns, and checks unseen/missing categories and
non-default indices. It writes `training_features.csv` and
`evaluation_features.csv` alongside phenotype, volume, and provenance examples.
It requires no external service or patient data.

In cross-validation, repeat fitting inside each training fold. Never fit an
imputer or encoder on the complete dataset before evaluating held-out folds.
Keep patient identifiers and outcomes outside the selected predictor matrix.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| All-zero category indicators | Unknown levels, missing levels absent during fitting, or `drop_first=True`. |
| Different feature columns | Use the same fitted encoder and select training columns in the same order. |
| Encoded-column collision | Rename source columns or levels; sanitization can produce identical names. |
| Unexpected imputation | Numeric strings are coerced before filling; inspect conversion failures and all-missing training columns. |
| Leakage warning | This is a heuristic review prompt, not proof that the matrix is leakage-free or invalid. |
