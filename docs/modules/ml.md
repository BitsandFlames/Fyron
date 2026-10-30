# Machine Learning

`fyron.ml` provides tabular classification workflows for clinical data science. It is designed for patient-level feature matrices where the target is a binary or multiclass endpoint, such as treatment response, readmission, toxicity, or progression status.

The module covers the full lightweight workflow:

1. split data reproducibly,
2. handle class imbalance,
3. train Random Forest or XGBoost classifiers,
4. compute clinically meaningful metrics,
5. cross-validate and tune,
6. inspect feature importance,
7. generate publication-ready evaluation plots,
8. save fitted estimators.

## What This Module Is For

Use `fyron.ml` when you have a patient-level feature matrix and a classification endpoint. The module is intentionally focused on tabular clinical prediction workflows. It does not decide which variables are clinically valid, whether leakage is present, or whether a model is appropriate for deployment; those remain study-design decisions.

For transparent feature derivation from ICD-10, OPS, delimited code strings, or date columns, use [DataFrame Operations](dataframe.md) before ML preprocessing and model fitting.

## Core Concepts

### Correctness Notes

- Boruta in `run_classification_pipeline` is fitted after the holdout split and,
  when tuning, independently inside each CV training fold. The returned model
  includes the selection step and accepts the original feature columns, as do
  the returned `X_train` and `X_test`. An empty selection raises an error.
- Grid search preserves estimator parameters and imbalance weights. Returned
  predictions, metrics, and figures all use the selected estimator. With Boruta,
  unprefixed classifier grid keys are mapped to `model__...`.
- Binary `y_prob` always means probability of `pos_label`, including label
  `0` and string labels supported by the estimator. If omitted, the larger
  label is positive. F1, precision, recall, AUC, CV, external validation, and
  training plots use that same convention. XGBoost still requires its usual
  numeric class encoding; `scale_pos_weight` weights internal class 1.

Re-run previous Boruta pipeline evaluations because selection previously saw
held-out data. Regenerate prior grid-search predictions/plots and evaluations
using nondefault positive labels because those outputs could be inconsistent.

| Concept | Meaning |
| --- | --- |
| `X` | Feature matrix. A DataFrame is preferred because feature names are preserved. |
| `y` | Endpoint labels. Binary endpoints are most fully supported. |
| `X_train`, `X_test` | Split feature matrices used for model fitting and evaluation. |
| `y_pred` | Hard class predictions. |
| `y_prob` | Positive-class probabilities for binary classifiers. |
| class imbalance | Event rates are often skewed; use `class_weight` or `scale_pos_weight` deliberately. |
| result dict | Named output bundle containing model, predictions, probabilities, metrics, and figures. |

## Install

```bash
uv add "fyron[ml]"
```

Optional Boruta feature selection:

```bash
uv add "fyron[ml,boruta]"
```

## Import Pattern

```python
from fyron import ml
```

Using the `ml` namespace keeps notebooks readable and makes it clear which helpers come from Fyron.

## Expected Data

| Input | Accepted types | Notes |
| --- | --- | --- |
| `X` | DataFrame, NumPy array, list-like | DataFrames preserve feature names for importance plots |
| `y` | Series, NumPy array, list-like | Binary labels are most fully supported |
| probabilities | 1-D array-like | Positive-class probabilities for binary metrics and plots |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | Feature matrix `X`, label vector `y`, train/test splits, or result dictionaries from Fyron training helpers. |
| Required columns | DataFrames should preserve feature names; metric/plot helpers require explicit label, prediction, probability, or feature columns. |
| Return shape | Result dictionaries with model/predictions/metrics/figures, metric DataFrames, fitted estimators, or Matplotlib figures. |
| Saved artifacts | Fitted estimator files, metric tables, feature importance tables, ROC/PR/calibration/confusion plots, and model-card summaries. |
| Failure modes | Missing optional ML dependencies, mismatched array lengths, nonnumeric feature matrices, invalid labels, missing probabilities, or leakage/imbalance requiring review. |

Clinical ML usually benefits from explicit preprocessing before modeling:

- encode categorical variables,
- impute missing values,
- avoid leakage from post-outcome variables,
- split by patient, not row, when repeated measurements exist,
- keep a held-out validation set when possible.

Fyron does not hide those choices because they are study-design decisions.

## Research Decision: Model Development Versus Validation

| Decision | Practical guidance |
| --- | --- |
| Feature window | Include only features available before the prediction/index time. |
| Split | Keep a locked validation set or external cohort separate from model development. |
| Imbalance | State whether class weights, `scale_pos_weight`, or sampling were used. |
| Threshold | Threshold scans are development information unless pre-specified before validation. |
| Calibration | Report calibration when probabilities influence decisions. |
| Interpretation | Treat feature importance as model inspection, not causal evidence. |

## How To Interpret Outputs

Fyron ML functions return dictionaries instead of a single score so you can inspect the model, predictions, probabilities, metrics, and figures independently. In clinical settings, accuracy is rarely enough. Review sensitivity, specificity, AUC, confusion counts, and calibration together, then decide whether threshold tuning or subgroup analysis is needed before reporting performance.

Use feature importance as a model-inspection tool, not as causal evidence. If a feature is clinically surprising, check leakage, coding artifacts, missingness patterns, and whether the train/test split respects patient-level independence.

## Parameter Notes

| Parameter | Practical guidance |
| --- | --- |
| `test_size` | Choose before model evaluation; common values are 0.2 or 0.3. |
| `stratify` | Keep `True` for imbalanced binary endpoints unless study design says otherwise. |
| `random_state` | Set for reproducibility and record it in a provenance manifest. |
| `class_weight` | Use with sklearn models such as Random Forest. |
| `scale_pos_weight` | Use with XGBoost binary classification. |
| `pos_label` | Set explicitly when the positive/event label is not `1`. |
| `plot` | Use `True` to create ROC, PR, calibration, and confusion-matrix figures during training. |
| `search` / parameter grids | Use for development; keep final reported settings explicit. |

## API Summary

| Function | Purpose |
| --- | --- |
| `train_test_split_data` | Stratified train/test split |
| `compute_class_weights` | sklearn class weights for imbalanced targets |
| `compute_scale_pos_weight` | XGBoost binary imbalance ratio |
| `train_random_forest` | Fit RF, predict, score, optionally plot |
| `train_xgboost` | Fit XGBClassifier, predict, score, optionally plot |
| `calculate_classification_metrics` | Accuracy, balanced accuracy, F1, precision, recall, sensitivity, specificity, AUC, counts |
| `cross_validate_model` | Stratified k-fold with fold metrics and optional OOF predictions |
| `grid_search_model` | GridSearchCV wrapper with optional validation metrics |
| `get_default_param_grid` | Default grids for RF, XGB, survival boosting |
| `get_feature_importance` | Extract tree-model feature importance table |
| `plot_feature_importance` | Plot top feature importances |
| `run_boruta_feature_selection` | Optional all-relevant feature selection |
| `run_classification_pipeline` | Split, optional Boruta, optional search, train, evaluate |
| `save_estimator` / `load_estimator` | joblib persistence |

Before training, use `fyron.preprocessing.feature_matrix_report` to flag missingness, constants, rare binary variables, and leakage-like column names.

## Function Parameter Reference

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `train_test_split_data` | `X`, `y` | `test_size`, `stratify`, `random_state` | train/test split tuple |
| `compute_class_weights` | `y` | `class_weight` | class-weight dict |
| `compute_scale_pos_weight` | `y` | `pos_label` | float ratio |
| `sample_weights_for_sklearn` | `y` | `class_weight` | sample-weight array |
| `train_random_forest` | `X_train`, `y_train` | test data, `class_weight`, `random_state`, `plot`, `pos_label`, RF params | training result dict |
| `train_xgboost` | `X_train`, `y_train` | test data, `scale_pos_weight`, `random_state`, `plot`, `pos_label`, XGB params | training result dict |
| `calculate_classification_metrics` | `y_true`, `y_pred` | `y_prob`, `pos_label` | metrics dict |
| `cross_validate_model` | `estimator`, `X`, `y` | `cv`, `random_state`, `return_models`, `return_oof_predictions`, `pos_label` | CV result dict |
| `grid_search_model` | `estimator`, `param_grid`, `X_train`, `y_train` | validation data, `scoring`, `cv`, `n_jobs`, `refit`, `random_state` | search result dict |
| `get_default_param_grid` | `model_name` | none | param grid dict |
| `get_feature_importance` | `model` | `feature_names` | DataFrame |
| `plot_feature_importance` | `model`, optional feature names | `top_n`, `title`, `save_path`, `fmt` | `(fig, ax)` |
| `run_boruta_feature_selection` | `X`, `y` | `estimator`, `class_weight`, `max_iter`, `random_state` | Boruta result dict |
| `run_classification_pipeline` | `X`, `y` | model/split/imbalance/Boruta/search/plot params | full result dict |
| `save_estimator` | `model`, `path` | none | writes file |
| `load_estimator` | `path` | none | loaded estimator |

## Train/Test Split

```python
X_train, X_test, y_train, y_test = ml.train_test_split_data(
    X,
    y,
    test_size=0.2,
    stratify=True,
    random_state=42,
)
```

Use `stratify=True` for binary clinical endpoints unless there is a specific study-design reason not to.

## Class Imbalance

For Random Forest:

```python
class_weight = ml.compute_class_weights(y_train)
```

For XGBoost:

```python
scale_pos_weight = ml.compute_scale_pos_weight(y_train)
```

These helpers are intentionally separate because sklearn and XGBoost use different imbalance APIs.

## Random Forest

```python
rf = ml.train_random_forest(
    X_train,
    y_train,
    X_test,
    y_test,
    class_weight=class_weight,
    n_estimators=500,
    max_depth=None,
    random_state=42,
    plot=True,
)

rf["metrics"]
rf["figures"].keys()
```

Returned keys include:

| Key | Meaning |
| --- | --- |
| `model` | fitted `RandomForestClassifier` |
| `y_pred` | predicted class labels on evaluation data |
| `y_prob` | positive-class probabilities for binary targets |
| `metrics` | dictionary of classification metrics |
| `figures` | ROC, PR, calibration, confusion matrix when `plot=True` |

For clinical reporting, preserve `metrics`, `y_pred`, `y_prob`, and the exact train/test split so validation can be audited later.

## XGBoost

```python
xgb = ml.train_xgboost(
    X_train,
    y_train,
    X_test,
    y_test,
    scale_pos_weight=scale_pos_weight,
    n_estimators=500,
    max_depth=3,
    learning_rate=0.05,
    random_state=42,
    plot=True,
)
```

For binary targets, Fyron defaults `eval_metric` to `logloss`. For multiclass targets, it defaults to `mlogloss` and `multi:softprob`.

## Metrics

```python
metrics = ml.calculate_classification_metrics(
    y_test,
    rf["y_pred"],
    rf["y_prob"],
)
```

Binary outputs include:

- `accuracy`
- `balanced_accuracy`
- `f1`
- `precision`
- `recall`
- `sensitivity`
- `specificity`
- `auc`
- `tn`, `fp`, `fn`, `tp`

For clinical models, inspect sensitivity and specificity directly. Accuracy can be misleading when events are rare.

## Cross-Validation

```python
from sklearn.ensemble import RandomForestClassifier

cv = ml.cross_validate_model(
    RandomForestClassifier(n_estimators=300, random_state=42),
    X,
    y,
    cv=5,
    return_oof_predictions=True,
)

cv["fold_metrics"]
cv["mean_metrics"]
cv["std_metrics"]
```

Set `return_oof_predictions=True` when you want out-of-fold predictions for calibration or error analysis.

## Grid Search

```python
from sklearn.ensemble import RandomForestClassifier

grid = ml.get_default_param_grid("random_forest")

search = ml.grid_search_model(
    RandomForestClassifier(random_state=42),
    grid,
    X_train,
    y_train,
    X_val=X_test,
    y_val=y_test,
    scoring="roc_auc",
    cv=5,
    n_jobs=1,
)

search["best_params"]
search["val_metrics"]
```

`n_jobs=1` is useful in restricted notebook, CI, or sandbox environments. Use higher parallelism on local machines when appropriate.

## End-To-End Pipeline

```python
result = ml.run_classification_pipeline(
    X,
    y,
    model="xgboost",
    test_size=0.2,
    handle_imbalance=True,
    use_grid_search=False,
    random_state=42,
    n_estimators=300,
    learning_rate=0.05,
    plot=True,
)
```

Use the pipeline helper for fast baselines. For final analyses, consider calling the lower-level functions explicitly so every preprocessing and modeling step is visible in your methods.

## Feature Importance

```python
importance = ml.get_feature_importance(
    rf["model"],
    feature_names=list(X.columns),
)

fig, ax = ml.plot_feature_importance(
    rf["model"],
    feature_names=list(X.columns),
    top_n=20,
)
```

For XGBoost, Fyron extracts booster importance scores and normalizes them when possible.

## Boruta Feature Selection

```python
boruta = ml.run_boruta_feature_selection(
    X_train,
    y_train,
    max_iter=100,
    random_state=42,
)

selected = boruta["selected_features"]
ranking = boruta["ranking_df"]
```

Boruta is an all-relevant feature-selection method. It can be useful in biomarker discovery, but it should still be validated with external or held-out data.

## External Validation And Calibration

Use these helpers when a model is already trained and the next question is reliability on locked or external data.

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `nested_cross_validate_model` | estimator, parameter grid, X, y | inner/outer CV, scoring | nested CV result dict |
| `evaluate_external_validation` | fitted estimator, external X/y | locked threshold, positive label | metrics dict |
| `evaluate_locked_threshold` | labels, probabilities, threshold | positive/negative labels | threshold metrics dict |
| `fit_probability_calibrator` | fitted estimator, calibration X/y | method | sklearn calibrator |
| `apply_probability_calibrator` | calibrator, X | positive class index | calibrated probabilities |
| `model_card_summary` | estimator | data, metrics, intended use, limitations | model-card dict |

```python
nested = ml.nested_cross_validate_model(
    estimator,
    {"C": [0.1, 1.0, 10.0]},
    X,
    y,
    outer_cv=5,
    inner_cv=3,
)

external = ml.evaluate_external_validation(
    fitted_model,
    X_external,
    y_external,
    threshold=0.35,
)

calibrator = ml.fit_probability_calibrator(
    fitted_model,
    X_calibration,
    y_calibration,
)

card = ml.model_card_summary(
    fitted_model,
    X=X_train,
    y=y_train,
    metrics=external["metrics"],
    intended_use="Research endpoint prediction",
)
```

## Clinical Plotting

Model evaluation plots:

```python
fig_roc, _ = ml.plot_roc_curve(y_test, rf["y_prob"])
fig_pr, _ = ml.plot_precision_recall_curve(y_test, rf["y_prob"])
fig_cal, _ = ml.plot_calibration_curve(y_test, rf["y_prob"])
fig_cm, _ = ml.plot_confusion_matrix(y_test, rf["y_pred"])
```

Exploratory feature plots:

```python
fig_corr, _, corr = ml.plot_correlation_heatmap(
    X,
    method="spearman",
    mask_upper=True,
)
```

Model comparison:

```python
fig_metrics, _ = ml.plot_metric_bars(
    {
        "Random Forest": rf["metrics"],
        "XGBoost": xgb["metrics"],
    },
    metrics_to_plot=["auc", "sensitivity", "specificity", "f1"],
)
```

Grouped clinical summaries:

```python
fig_bar, _ = ml.plot_patterned_bar(
    summary_df,
    x="endpoint",
    y="rate",
    group="cohort",
    error="ci_half_width",
    title="Endpoint rates by cohort",
    annotate=True,
)
```

See [Clinical Plotting](plotting.md) for detailed plotting guidance.

## Persistence

```python
ml.save_estimator(rf["model"], "models/rf.joblib")
loaded = ml.load_estimator("models/rf.joblib")
```

Persist only the fitted estimator. Keep feature-generation code and schema validation separately versioned so the model can be reproduced.

## Practical Checklist

- Confirm rows represent independent patients or split by patient ID.
- Define the endpoint before feature engineering.
- Remove leakage variables.
- Preserve feature names with DataFrames.
- Use stratified splits for imbalanced endpoints.
- Report sensitivity, specificity, AUC, and calibration when probabilities are used clinically.
- Save both figures and metric tables for reproducibility.
