"""Classification metrics for healthcare tabular models."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike
from sklearn import metrics as sk_metrics

from fyron.ml._arrays import ArrayLikeInput, is_binary, resolve_pos_label, to_numpy_1d


def calculate_classification_metrics(
    y_true: ArrayLikeInput,
    y_pred: ArrayLikeInput,
    y_prob: ArrayLike | None = None,
    *,
    pos_label: Any | None = None,
) -> dict[str, Any]:
    """Compute binary classification metrics and confusion-matrix counts.

    Sensitivity, specificity, and AUC require a binary target. When
    ``y_prob`` is omitted, ``auc`` is set to ``None``.

    Parameters
    ----------
    y_true
        Ground-truth labels.
    y_pred
        Predicted labels.
    y_prob
        Predicted probability of the positive class (binary only).
    pos_label
        Positive class label for binary metrics.

    Returns
    -------
    dict
        Keys include ``accuracy``, ``f1``, ``precision``, ``recall``,
        ``sensitivity``, ``specificity``, ``balanced_accuracy``, ``auc``,
        and ``tn``, ``fp``, ``fn``, ``tp``.

    Examples
    --------
    >>> from fyron.ml import calculate_classification_metrics
    >>> m = calculate_classification_metrics([0, 1, 1, 0], [0, 1, 0, 0], [0.2, 0.9, 0.4, 0.1])
    >>> m["tp"] == 1 and m["tn"] == 2
    True
    """
    y_true_arr = to_numpy_1d(y_true)
    y_pred_arr = to_numpy_1d(y_pred)
    out: dict[str, Any] = {
        "accuracy": float(sk_metrics.accuracy_score(y_true_arr, y_pred_arr)),
        "balanced_accuracy": float(sk_metrics.balanced_accuracy_score(y_true_arr, y_pred_arr)),
    }
    average = "binary" if is_binary(y_true_arr) else "macro"
    options = {}
    if average == "binary":
        pos = resolve_pos_label(y_true_arr, pos_label)
        if pos not in y_true_arr:
            raise ValueError("pos_label is not a target class.")
        options["pos_label"] = pos
    out["f1"] = float(sk_metrics.f1_score(y_true_arr, y_pred_arr, average=average, zero_division=0, **options))
    out["precision"] = float(
        sk_metrics.precision_score(y_true_arr, y_pred_arr, average=average, zero_division=0, **options)
    )
    out["recall"] = float(sk_metrics.recall_score(y_true_arr, y_pred_arr, average=average, zero_division=0, **options))

    if is_binary(y_true_arr):
        pos = resolve_pos_label(y_true_arr, pos_label)
        labels = [x for x in np.unique(np.concatenate([y_true_arr, y_pred_arr])) if x != pos] + [pos]
        if len(labels) == 2:
            neg = labels[0] if labels[1] == pos else labels[1]
            tn, fp, fn, tp = sk_metrics.confusion_matrix(
                y_true_arr, y_pred_arr, labels=[neg, pos]
            ).ravel()
            out.update(tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp))
            out["sensitivity"] = float(tp / (tp + fn)) if (tp + fn) else 0.0
            out["specificity"] = float(tn / (tn + fp)) if (tn + fp) else 0.0
        else:
            out.update(tn=None, fp=None, fn=None, tp=None, sensitivity=None, specificity=None)
        if y_prob is not None:
            out["auc"] = float(sk_metrics.roc_auc_score(y_true_arr == pos, to_numpy_1d(y_prob)))
        else:
            out["auc"] = None
    else:
        out.update(
            tn=None,
            fp=None,
            fn=None,
            tp=None,
            sensitivity=None,
            specificity=None,
            auc=None,
        )
    return out
