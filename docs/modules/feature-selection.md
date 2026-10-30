# Feature Selection

`fyron.feature_selection` provides transparent feature-selection strategies for clinical data science. It is designed for model development notebooks where every selection decision should be inspectable and reportable.

## Install

```bash
uv add "fyron[feature-selection]"
```

## Imports

```python
from fyron import feature_selection as fs
```

## Function Reference

Regression screening pairs `X` and `y` by row position, not pandas index labels.
Only finite numeric pairs contribute to Spearman correlation; `n` reports that
retained pair count. Re-run prior screening with non-default indices, which
could previously lose valid pairs through index alignment.

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `univariate_feature_screening(X, y, ...)` | feature table, target | task, alpha, FDR correction | selected features and screening table |
| `variance_filter(X, ...)` | feature table | variance threshold | selected features and variance table |
| `correlation_filter(X, ...)` | feature table | threshold, method | selected/dropped features and correlation pairs |
| `model_importance_selection(estimator, X, y, ...)` | estimator, features, target | threshold or top N | importance table and fitted model |
| `permutation_importance_selection(estimator, X, y, ...)` | estimator, features, target | repeats, scoring, threshold/top N | permutation importance table |
| `boruta_feature_selection(X, y, ...)` | features, target | Boruta/sklearn options | Boruta ranking table |
| `stability_selection(estimator, X, y, ...)` | estimator, features, target | rounds, sample fraction, threshold | selection-frequency table |
| `combine_feature_selection_results(results, ...)` | result dictionaries | strategy, minimum methods | consensus table |

## Example

```python
from sklearn.ensemble import RandomForestClassifier
from fyron import feature_selection as fs

univariate = fs.univariate_feature_screening(
    X,
    y,
    task="classification",
    alpha=0.05,
)

correlation = fs.correlation_filter(
    X,
    threshold=0.85,
    method="spearman",
)

stable = fs.stability_selection(
    RandomForestClassifier(n_estimators=300, random_state=42),
    X[correlation["selected_features"]],
    y,
    n_rounds=100,
    selection_threshold=0.6,
)

final = fs.combine_feature_selection_results(
    {
        "univariate": univariate,
        "correlation": correlation,
        "stability": stable,
    },
    strategy="consensus",
    min_methods=2,
)

final["selected_features"]
final["summary_table"]
```

## Interpretation

Feature selection is a model-development tool, not causal evidence. Use the returned tables to document why a feature was kept or dropped, and validate the final feature set on held-out or external data when possible.
