"""Class imbalance helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike
from sklearn.utils.class_weight import compute_class_weight as sk_compute_class_weight
from sklearn.utils.class_weight import compute_sample_weight as sk_compute_sample_weight

from fyron.ml._arrays import ArrayLikeInput, is_binary, resolve_pos_label, to_numpy_1d


def compute_class_weights(
    y: ArrayLikeInput,
    *,
    class_weight: str = "balanced",
) -> dict[Any, float]:
    """Compute class weights as a label-to-weight mapping.

    Supports binary and multiclass targets.

    Parameters
    ----------
    y
        Target vector.
    class_weight
        Strategy passed to :func:`sklearn.utils.class_weight.compute_class_weight`.

    Returns
    -------
    dict
        Mapping from class label to weight. Pass directly to
        :class:`sklearn.ensemble.RandomForestClassifier(class_weight=...)`.

    Examples
    --------
    >>> from fyron.ml import compute_class_weights
    >>> weights = compute_class_weights([0, 0, 0, 1])
    >>> weights[1] > weights[0]
    True
    """
    y_arr = to_numpy_1d(y)
    classes = np.unique(y_arr)
    weights = sk_compute_class_weight(class_weight, classes=classes, y=y_arr)
    return {cls: float(w) for cls, w in zip(classes, weights)}


def compute_scale_pos_weight(
    y: ArrayLikeInput,
    *,
    pos_label: Any | None = None,
) -> float:
    """Compute XGBoost ``scale_pos_weight`` for binary classification.

    Defined as ``count(negative) / count(positive)``.

    Parameters
    ----------
    y
        Binary target vector.
    pos_label
        Positive class label. Defaults to the larger of the two unique labels.

    Returns
    -------
    float
        Value suitable for :class:`xgboost.XGBClassifier(scale_pos_weight=...)`.

    Examples
    --------
    >>> from fyron.ml import compute_scale_pos_weight
    >>> compute_scale_pos_weight([0, 0, 0, 1])
    3.0
    """
    y_arr = to_numpy_1d(y)
    if not is_binary(y_arr):
        raise ValueError("compute_scale_pos_weight requires a binary target.")
    pos = resolve_pos_label(y_arr, pos_label)
    n_pos = int(np.sum(y_arr == pos))
    n_neg = int(np.sum(y_arr != pos))
    if n_pos == 0:
        raise ValueError("No positive samples in y.")
    return float(n_neg / n_pos)


def sample_weights_for_sklearn(
    y: ArrayLikeInput,
    *,
    class_weight: str | dict[Any, float] = "balanced",
) -> np.ndarray:
    """Per-sample weights for sklearn estimators that accept ``sample_weight``.

    Useful for multiclass XGBoost or any estimator without a ``class_weight`` parameter.

    Examples
    --------
    >>> from fyron.ml import sample_weights_for_sklearn
    >>> w = sample_weights_for_sklearn([0, 0, 1])
    >>> len(w)
    3
    """
    y_arr = to_numpy_1d(y)
    if isinstance(class_weight, dict):
        return np.array([class_weight[label] for label in y_arr], dtype=float)
    return sk_compute_sample_weight(class_weight, y_arr)
