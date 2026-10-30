"""Cross-validation utilities."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold

from fyron.ml._arrays import ArrayLikeInput, is_binary, to_numpy_1d, to_numpy_2d
from fyron.ml.metrics import calculate_classification_metrics
from fyron.ml.training import _predict_proba_positive

CVResult = dict[str, Any]


def cross_validate_model(
    estimator: Any,
    X: ArrayLikeInput,
    y: ArrayLikeInput,
    *,
    cv: int = 5,
    random_state: int = 42,
    return_models: bool = False,
    return_oof_predictions: bool = False,
    pos_label: Any | None = None,
) -> CVResult:
    """Stratified k-fold cross-validation with healthcare-oriented metrics.

    Parameters
    ----------
    estimator
        Any sklearn-compatible classifier (must support ``fit`` / ``predict``).
    X, y
        Full dataset.
    cv
        Number of folds.
    return_models
        If True, include a list of fitted models (one per fold).
    return_oof_predictions
        If True, include out-of-fold predictions and positive-class probabilities.

    Returns
    -------
    dict
        Keys: ``fold_metrics`` (DataFrame), ``mean_metrics``, ``std_metrics``,
        and optionally ``models``, ``oof_pred``, ``oof_prob``.

    Examples
    --------
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from fyron.ml import cross_validate_model
    >>> X = [[i] for i in range(20)]
    >>> y = [0] * 10 + [1] * 10
    >>> out = cross_validate_model(
    ...     RandomForestClassifier(n_estimators=10, random_state=0), X, y, cv=3
    ... )
    >>> len(out["fold_metrics"]) == 3
    True
    """
    X_arr = to_numpy_2d(X)
    y_arr = to_numpy_1d(y)
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)

    fold_rows: list[dict[str, Any]] = []
    models: list[Any] = []
    oof_pred = np.empty_like(y_arr)
    oof_prob: np.ndarray | None = np.full(shape=y_arr.shape, fill_value=np.nan, dtype=float)

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X_arr, y_arr)):
        model = clone(estimator)
        model.fit(X_arr[train_idx], y_arr[train_idx])
        y_pred = model.predict(X_arr[test_idx])
        y_prob = _predict_proba_positive(model, X_arr[test_idx], pos_label)
        fold_metrics = calculate_classification_metrics(
            y_arr[test_idx], y_pred, y_prob, pos_label=pos_label
        )
        fold_metrics["fold"] = fold_idx
        fold_rows.append(fold_metrics)
        if return_models:
            models.append(model)
        if return_oof_predictions:
            oof_pred[test_idx] = y_pred
            if y_prob is not None and is_binary(y_arr):
                oof_prob[test_idx] = y_prob

    fold_df = pd.DataFrame(fold_rows)
    metric_cols = [c for c in fold_df.columns if c != "fold"]
    mean_metrics = fold_df[metric_cols].mean(numeric_only=True)
    std_metrics = fold_df[metric_cols].std(numeric_only=True)

    result: CVResult = {
        "fold_metrics": fold_df,
        "mean_metrics": mean_metrics,
        "std_metrics": std_metrics,
    }
    if return_models:
        result["models"] = models
    if return_oof_predictions:
        result["oof_pred"] = oof_pred
        result["oof_prob"] = oof_prob
    return result
