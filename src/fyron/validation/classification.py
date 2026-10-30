"""Validation tables for binary clinical prediction models."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import numpy as np
import pandas as pd

from fyron.ml.metrics import calculate_classification_metrics

ThresholdMetric = Literal["youden", "f1", "balanced_accuracy"]


def _validate_binary_probabilities(y_true, y_prob, pos_label):
    labels = np.asarray(y_true)
    probabilities = np.asarray(y_prob, dtype=float)
    if labels.ndim != 1 or probabilities.ndim != 1:
        raise ValueError("y_true and y_prob must be one-dimensional.")
    if not len(labels) or pd.isna(labels).any() or pd.isna(pos_label):
        raise ValueError("y_true and pos_label must be nonmissing; y_true must be nonempty.")
    unique = pd.unique(labels)
    if len(unique) > 2 or (len(unique) == 2 and pos_label not in unique):
        raise ValueError("y_true must be binary and include pos_label.")
    if len(labels) != len(probabilities):
        raise ValueError("y_true and y_prob must have the same length.")
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("y_prob must contain finite probabilities in [0, 1].")
    return labels, probabilities


def find_best_threshold(
    y_true: Sequence[Any],
    y_prob: Sequence[float],
    *,
    metric: ThresholdMetric = "youden",
    pos_label: Any = 1,
    thresholds: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Find a binary decision threshold by an explicit metric."""

    yt, yp = _validate_binary_probabilities(y_true, y_prob, pos_label)
    if len(pd.unique(yt)) != 2:
        raise ValueError("Threshold selection requires both target classes.")
    threshold_values = np.asarray(thresholds if thresholds is not None else np.linspace(0, 1, 101), dtype=float)
    if (threshold_values.ndim != 1 or not threshold_values.size
            or not np.isfinite(threshold_values).all()
            or ((threshold_values < 0) | (threshold_values > 1)).any()):
        raise ValueError("thresholds must be a nonempty one-dimensional sequence in [0, 1].")
    rows = []
    for threshold in threshold_values:
        pred = np.where(yp >= threshold, pos_label, _negative_label(yt, pos_label))
        metrics = calculate_classification_metrics(yt, pred, yp, pos_label=pos_label)
        if metric == "youden":
            score = metrics["sensitivity"] + metrics["specificity"] - 1
        elif metric == "f1":
            score = metrics["f1"]
        elif metric == "balanced_accuracy":
            score = metrics["balanced_accuracy"]
        else:
            raise ValueError("metric must be 'youden', 'f1', or 'balanced_accuracy'.")
        rows.append({"threshold": float(threshold), "score": float(score), **metrics})
    table = pd.DataFrame(rows).sort_values(["score", "threshold"], ascending=[False, True])
    best = table.iloc[0].to_dict()
    best["threshold_table"] = table.reset_index(drop=True)
    return best


def calibration_summary(
    y_true: Sequence[Any],
    y_prob: Sequence[float],
    *,
    n_bins: int = 10,
    pos_label: Any = 1,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Return calibration-in-the-large, calibration slope proxy, and bin table."""

    if isinstance(n_bins, bool) or not isinstance(n_bins, (int, np.integer)) or n_bins <= 0:
        raise ValueError("n_bins must be a positive integer.")
    labels, yp = _validate_binary_probabilities(y_true, y_prob, pos_label)
    yt = (labels == pos_label).astype(float)
    bins = (pd.cut(yp, bins=1) if len(np.unique(yp)) == 1
            else pd.qcut(yp, q=min(n_bins, len(np.unique(yp))), duplicates="drop"))
    table = (
        pd.DataFrame({"y": yt, "prob": yp, "bin": bins})
        .groupby("bin", observed=False)
        .agg(n=("y", "size"), observed=("y", "mean"), predicted=("prob", "mean"))
        .reset_index()
    )
    eps = 1e-12
    clipped = np.clip(yp, eps, 1 - eps)
    logit = np.log(clipped / (1 - clipped))
    slope = float(np.polyfit(logit, yt, deg=1)[0]) if len(np.unique(logit)) > 1 else float("nan")
    summary = {
        "n": float(len(yt)),
        "observed_rate": float(np.mean(yt)),
        "mean_predicted_probability": float(np.mean(yp)),
        "calibration_in_the_large": float(np.mean(yp) - np.mean(yt)),
        "calibration_slope_proxy": slope,
        "brier_score": float(np.mean((yt - yp) ** 2)),
    }
    return summary, table


def subgroup_metric_table(
    df: pd.DataFrame,
    *,
    group_col: str,
    y_true_col: str,
    y_pred_col: str,
    y_prob_col: str | None = None,
    pos_label: Any = 1,
) -> pd.DataFrame:
    """Calculate classification metrics separately for each subgroup."""

    _require_columns(df, [group_col, y_true_col, y_pred_col] + ([y_prob_col] if y_prob_col else []))
    rows = []
    for group, group_df in df.groupby(group_col, dropna=False):
        metrics = calculate_classification_metrics(
            group_df[y_true_col],
            group_df[y_pred_col],
            group_df[y_prob_col] if y_prob_col else None,
            pos_label=pos_label,
        )
        rows.append({group_col: group, "n": len(group_df), **metrics})
    return pd.DataFrame(rows)


def decision_curve_table(
    y_true: Sequence[Any],
    y_prob: Sequence[float],
    *,
    thresholds: Sequence[float] | None = None,
    pos_label: Any = 1,
) -> pd.DataFrame:
    """Compute binary decision-curve net benefit over thresholds."""

    labels, yp = _validate_binary_probabilities(y_true, y_prob, pos_label)
    yt = labels == pos_label
    threshold_values = np.asarray(thresholds if thresholds is not None else np.linspace(0.01, 0.99, 99), dtype=float)
    if (
        threshold_values.ndim != 1
        or not threshold_values.size
        or not np.isfinite(threshold_values).all()
        or ((threshold_values <= 0) | (threshold_values >= 1)).any()
    ):
        raise ValueError("thresholds must be a nonempty one-dimensional sequence in (0, 1).")
    prevalence = float(np.mean(yt))
    rows = []
    n = len(yt)
    for threshold in threshold_values:
        predicted = yp >= threshold
        tp = int(np.sum(predicted & yt))
        fp = int(np.sum(predicted & ~yt))
        net_benefit = (tp / n) - (fp / n) * (threshold / (1 - threshold))
        treat_all = prevalence - (1 - prevalence) * (threshold / (1 - threshold))
        rows.append(
            {
                "threshold": float(threshold),
                "net_benefit_model": float(net_benefit),
                "net_benefit_treat_all": float(treat_all),
                "net_benefit_treat_none": 0.0,
                "tp": tp,
                "fp": fp,
            }
        )
    return pd.DataFrame(rows)


def bootstrap_classification_metrics(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    y_prob: Sequence[float] | None = None,
    *,
    n_rounds: int = 1000,
    random_state: int = 42,
    pos_label: Any = 1,
    ci: float = 0.95,
) -> pd.DataFrame:
    """Bootstrap binary classification metrics with percentile intervals.

    Parameters
    ----------
    y_true, y_pred
        Ground-truth and predicted labels.
    y_prob
        Optional positive-class probabilities for AUC intervals.
    n_rounds
        Number of bootstrap resamples.
    random_state
        Random seed for deterministic intervals.
    pos_label
        Positive class label.
    ci
        Confidence interval width, for example ``0.95``.

    Returns
    -------
    pandas.DataFrame
        One row per numeric metric with estimate, bootstrap mean, lower and upper CI.
    """

    if n_rounds <= 0:
        raise ValueError("n_rounds must be positive.")
    if not 0 < ci < 1:
        raise ValueError("ci must be between 0 and 1.")
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    prob = None if y_prob is None else np.asarray(y_prob, dtype=float)
    if len(yt) != len(yp) or (prob is not None and len(prob) != len(yt)):
        raise ValueError("y_true, y_pred, and y_prob must have the same length.")
    if len(pd.unique(yt)) != 2:
        raise ValueError("Binary metric bootstrap requires both target classes.")

    point = calculate_classification_metrics(yt, yp, prob, pos_label=pos_label)
    numeric_metrics = [name for name, value in point.items() if isinstance(value, (int, float)) and value is not None]
    rng = np.random.default_rng(random_state)
    values: dict[str, list[float]] = {name: [] for name in numeric_metrics}
    for _ in range(n_rounds):
        idx = rng.integers(0, len(yt), len(yt))
        if len(pd.unique(yt[idx])) != 2:
            continue
        try:
            metrics = calculate_classification_metrics(
                yt[idx],
                yp[idx],
                prob[idx] if prob is not None else None,
                pos_label=pos_label,
            )
        except ValueError:
            continue
        for name in numeric_metrics:
            value = metrics.get(name)
            if value is not None:
                values[name].append(float(value))

    alpha = (1.0 - ci) / 2.0
    rows = []
    for name in numeric_metrics:
        arr = np.asarray(values[name], dtype=float)
        rows.append(
            {
                "metric": name,
                "estimate": float(point[name]),
                "bootstrap_mean": float(np.nanmean(arr)) if arr.size else float("nan"),
                "ci_lower": float(np.nanpercentile(arr, 100 * alpha)) if arr.size else float("nan"),
                "ci_upper": float(np.nanpercentile(arr, 100 * (1 - alpha))) if arr.size else float("nan"),
                "n_rounds": int(n_rounds),
                "n_successful_rounds": int(arr.size),
            }
        )
    return pd.DataFrame(rows)


def _negative_label(y_true: np.ndarray, pos_label: Any) -> Any:
    labels = [label for label in pd.unique(y_true) if label != pos_label]
    return labels[0] if labels else 0


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
