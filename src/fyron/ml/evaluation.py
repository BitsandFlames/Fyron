"""External validation, calibration, and model-card helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from fyron.ml._arrays import ArrayLikeInput, feature_names, resolve_pos_label, to_numpy_1d, to_numpy_2d
from fyron.ml.metrics import calculate_classification_metrics
from fyron.ml.training import _predict_proba_positive


def nested_cross_validate_model(
    estimator: Any,
    param_grid: Mapping[str, Sequence[Any]],
    X: ArrayLikeInput,
    y: ArrayLikeInput,
    *,
    outer_cv: int = 5,
    inner_cv: int = 3,
    scoring: str = "roc_auc",
    random_state: int = 42,
    n_jobs: int = -1,
    pos_label: Any | None = None,
) -> dict[str, Any]:
    """Run nested stratified CV with an inner grid search."""

    X_arr = to_numpy_2d(X)
    y_arr = to_numpy_1d(y)
    outer = StratifiedKFold(n_splits=outer_cv, shuffle=True, random_state=random_state)
    inner = StratifiedKFold(n_splits=inner_cv, shuffle=True, random_state=random_state)
    rows = []
    best_params = []
    for fold, (train_idx, test_idx) in enumerate(outer.split(X_arr, y_arr)):
        search = GridSearchCV(clone(estimator), dict(param_grid), scoring=scoring, cv=inner, n_jobs=n_jobs, refit=True)
        search.fit(X_arr[train_idx], y_arr[train_idx])
        model = search.best_estimator_
        y_pred = model.predict(X_arr[test_idx])
        y_prob = _predict_proba_positive(model, X_arr[test_idx], pos_label)
        metrics = calculate_classification_metrics(y_arr[test_idx], y_pred, y_prob, pos_label=pos_label)
        rows.append({"fold": fold, "best_score": float(search.best_score_), **metrics})
        best_params.append(search.best_params_)
    fold_metrics = pd.DataFrame(rows)
    metric_cols = [col for col in fold_metrics.columns if col != "fold"]
    return {
        "fold_metrics": fold_metrics,
        "mean_metrics": fold_metrics[metric_cols].mean(numeric_only=True),
        "std_metrics": fold_metrics[metric_cols].std(numeric_only=True),
        "best_params": best_params,
    }


def evaluate_locked_threshold(
    y_true: ArrayLikeInput,
    y_prob: ArrayLikeInput,
    *,
    threshold: float,
    pos_label: Any = 1,
    neg_label: Any = 0,
) -> dict[str, Any]:
    """Evaluate probabilities with a pre-specified decision threshold."""

    yp = to_numpy_1d(y_prob).astype(float)
    yt = to_numpy_1d(y_true)
    if len(yt) != len(yp):
        raise ValueError("y_true and y_prob must have the same length.")
    pred = np.where(yp >= threshold, pos_label, neg_label)
    return {"threshold": float(threshold), **calculate_classification_metrics(yt, pred, yp, pos_label=pos_label)}


def evaluate_external_validation(
    estimator: Any,
    X_external: ArrayLikeInput,
    y_external: ArrayLikeInput,
    *,
    threshold: float | None = None,
    pos_label: Any | None = None,
) -> dict[str, Any]:
    """Evaluate a fitted sklearn-style estimator on an external cohort."""

    X_arr = to_numpy_2d(X_external)
    y_arr = to_numpy_1d(y_external)
    y_pred = estimator.predict(X_arr)
    y_prob = _predict_proba_positive(estimator, X_arr, pos_label)
    metrics = calculate_classification_metrics(y_arr, y_pred, y_prob, pos_label=pos_label)
    out = {"n": int(len(y_arr)), "metrics": metrics}
    if threshold is not None and y_prob is not None:
        pos = resolve_pos_label(np.asarray(estimator.classes_), pos_label)
        neg = next(label for label in estimator.classes_ if label != pos)
        out["locked_threshold_metrics"] = evaluate_locked_threshold(
            y_arr,
            y_prob,
            threshold=threshold,
            pos_label=pos,
            neg_label=neg,
        )
    return out


def fit_probability_calibrator(
    estimator: Any,
    X_calibration: ArrayLikeInput,
    y_calibration: ArrayLikeInput,
    *,
    method: str = "sigmoid",
) -> CalibratedClassifierCV:
    """Fit a probability calibrator for an already fitted classifier."""

    calibrator = CalibratedClassifierCV(estimator, method=method, cv="prefit")
    calibrator.fit(to_numpy_2d(X_calibration), to_numpy_1d(y_calibration))
    return calibrator


def apply_probability_calibrator(
    calibrator: Any,
    X: ArrayLikeInput,
    *,
    positive_class_index: int = 1,
) -> np.ndarray:
    """Return calibrated positive-class probabilities."""

    probs = calibrator.predict_proba(to_numpy_2d(X))
    return np.asarray(probs[:, positive_class_index], dtype=float)


def model_card_summary(
    estimator: Any,
    *,
    X: ArrayLikeInput | None = None,
    y: ArrayLikeInput | None = None,
    metrics: Mapping[str, Any] | None = None,
    intended_use: str | None = None,
    limitations: str | None = None,
    random_state: int | None = None,
) -> dict[str, Any]:
    """Create a small inspectable model-card summary dictionary."""

    names = feature_names(X) if X is not None else None
    card: dict[str, Any] = {
        "model_type": type(estimator).__name__,
        "n_features": len(names) if names is not None else None,
        "feature_names": names,
        "metrics": dict(metrics or {}),
        "intended_use": intended_use,
        "limitations": limitations,
        "random_state": random_state,
    }
    if y is not None:
        y_arr = to_numpy_1d(y)
        labels, counts = np.unique(y_arr, return_counts=True)
        card["target_distribution"] = {str(label): int(count) for label, count in zip(labels, counts)}
    params = getattr(estimator, "get_params", lambda: {})()
    card["estimator_parameters"] = dict(params)
    return card
