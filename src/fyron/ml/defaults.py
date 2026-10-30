"""Default hyperparameter grids."""

from __future__ import annotations

from typing import Any


def get_default_param_grid(model_name: str) -> dict[str, Any]:
    """Return a sensible default parameter grid for grid search.

    Parameters
    ----------
    model_name
        ``"random_forest"``, ``"xgboost"``, or ``"survival_gradient_boosting"``.

    Examples
    --------
    >>> from fyron.ml import get_default_param_grid
    >>> grid = get_default_param_grid("random_forest")
    >>> "n_estimators" in grid
    True
    """
    key = model_name.strip().lower().replace("-", "_")
    if key in {"random_forest", "rf", "randomforest"}:
        return {
            "n_estimators": [100, 300, 500],
            "max_depth": [None, 5, 10, 20],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
            "max_features": ["sqrt", "log2"],
        }
    if key in {"xgboost", "xgb"}:
        return {
            "n_estimators": [100, 300, 500],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.01, 0.05, 0.1],
            "subsample": [0.7, 0.85, 1.0],
            "colsample_bytree": [0.7, 0.85, 1.0],
        }
    if key in {"survival_gradient_boosting", "gradient_survival_boosting", "gbsa"}:
        return {
            "n_estimators": [100, 300, 500],
            "learning_rate": [0.01, 0.05, 0.1],
            "max_depth": [1, 2, 3],
            "subsample": [0.7, 0.85, 1.0],
        }
    raise ValueError(
        f"Unknown model_name {model_name!r}. Use 'random_forest', 'xgboost', "
        "or 'survival_gradient_boosting'."
    )
