"""Model training helpers for Random Forest and XGBoost."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from fyron.ml._arrays import ArrayLikeInput, is_binary, resolve_pos_label, to_numpy_1d, to_numpy_2d
from fyron.ml.metrics import calculate_classification_metrics
from fyron.ml.plots import (
    plot_calibration_curve,
    plot_confusion_matrix,
    plot_precision_recall_curve,
    plot_roc_curve,
)

TrainingResult = dict[str, Any]


def _predict_proba_positive(
    model: Any, X: ArrayLikeInput, pos_label: Any | None = None,
) -> np.ndarray | None:
    X_arr = to_numpy_2d(X)
    if not hasattr(model, "predict_proba"):
        return None
    proba = model.predict_proba(X_arr)
    if proba.ndim == 2 and proba.shape[1] == 2:
        classes = np.asarray(model.classes_)
        pos = resolve_pos_label(classes, pos_label)
        indices = np.flatnonzero(classes == pos)
        if len(indices) != 1:
            raise ValueError("pos_label is not a fitted model class.")
        return proba[:, indices[0]]
    return None


def _evaluate_classifier(
    model: Any,
    X: Any,
    y: Any,
    *,
    pos_label: Any | None = None,
    plot: bool = False,
    title: str = "Classifier",
) -> TrainingResult:
    y_pred = model.predict(to_numpy_2d(X))
    y_prob = _predict_proba_positive(model, X, pos_label)
    result = {
        "model": model,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "metrics": calculate_classification_metrics(y, y_pred, y_prob, pos_label=pos_label),
        "figures": {},
    }
    if plot and y_prob is not None and is_binary(to_numpy_1d(y)):
        pos = resolve_pos_label(np.asarray(model.classes_), pos_label)
        binary_y = (to_numpy_1d(y) == pos).astype(int)
        result["figures"] = {
            "roc": plot_roc_curve(binary_y, y_prob, title=f"{title} ROC")[0],
            "precision_recall": plot_precision_recall_curve(binary_y, y_prob, title=f"{title} precision-recall")[0],
            "calibration": plot_calibration_curve(binary_y, y_prob, title=f"{title} calibration")[0],
            "confusion_matrix": plot_confusion_matrix(y, y_pred, title=f"{title} confusion matrix")[0],
        }
    return result


def train_random_forest(
    X_train: ArrayLikeInput,
    y_train: ArrayLikeInput,
    X_test: ArrayLikeInput | None = None,
    y_test: ArrayLikeInput | None = None,
    *,
    class_weight: str | dict[Any, float] | None = None,
    random_state: int = 42,
    plot: bool = False,
    pos_label: Any | None = None,
    **model_params: Any,
) -> TrainingResult:
    """Train a :class:`~sklearn.ensemble.RandomForestClassifier`.

    When ``X_test`` and ``y_test`` are provided, metrics and predictions refer to
    the held-out set; otherwise in-sample evaluation is used.

    Examples
    --------
    >>> from fyron.ml import train_random_forest
    >>> result = train_random_forest(
    ...     [[0], [1], [2], [3]],
    ...     [0, 0, 1, 1],
    ...     [[1], [2]],
    ...     [0, 1],
    ...     n_estimators=10,
    ...     random_state=0,
    ... )
    >>> "model" in result and "metrics" in result
    True
    """
    params = dict(model_params)
    params.setdefault("random_state", random_state)
    if class_weight is not None:
        params["class_weight"] = class_weight
    model = RandomForestClassifier(**params)
    model.fit(to_numpy_2d(X_train), to_numpy_1d(y_train))

    eval_X = X_test if X_test is not None else X_train
    eval_y = y_test if y_test is not None else y_train
    return _evaluate_classifier(model, eval_X, eval_y, pos_label=pos_label, plot=plot, title="Random Forest")


def train_xgboost(
    X_train: ArrayLikeInput,
    y_train: ArrayLikeInput,
    X_test: ArrayLikeInput | None = None,
    y_test: ArrayLikeInput | None = None,
    *,
    scale_pos_weight: float | None = None,
    random_state: int = 42,
    plot: bool = False,
    pos_label: Any | None = None,
    **model_params: Any,
) -> TrainingResult:
    """Train an :class:`xgboost.XGBClassifier`.

    For binary targets, ``eval_metric`` defaults to ``logloss``; for multiclass,
    ``mlogloss`` is used unless overridden.

    Examples
    --------
    >>> from fyron.ml import train_xgboost
    >>> result = train_xgboost(
    ...     [[0], [1], [2], [3]],
    ...     [0, 0, 1, 1],
    ...     n_estimators=10,
    ...     random_state=0,
    ... )
    >>> result["model"] is not None
    True
    """
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'train_xgboost requires xgboost. Install with: uv add "fyron[ml]"'
        ) from exc

    y_train_arr = to_numpy_1d(y_train)
    params = dict(model_params)
    params.setdefault("random_state", random_state)
    if is_binary(y_train_arr):
        params.setdefault("eval_metric", "logloss")
    else:
        params.setdefault("eval_metric", "mlogloss")
        params.setdefault("objective", "multi:softprob")
    if scale_pos_weight is not None:
        if not is_binary(y_train_arr):
            raise ValueError("scale_pos_weight is only valid for binary classification.")
        params["scale_pos_weight"] = scale_pos_weight

    model = XGBClassifier(**params)
    model.fit(to_numpy_2d(X_train), y_train_arr)

    eval_X = X_test if X_test is not None else X_train
    eval_y = y_test if y_test is not None else y_train
    return _evaluate_classifier(model, eval_X, eval_y, pos_label=pos_label, plot=plot, title="XGBoost")
