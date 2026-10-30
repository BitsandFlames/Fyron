"""Bootstrap utilities for scores and model metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Mapping, Sequence

import pandas as pd

from ._deps import require_numpy, require_scipy_stats


SummaryStatistic = Literal["mean", "median"]
MetricFunc = Callable[..., float]


@dataclass(frozen=True)
class BootstrapResult:
    """Result for one bootstrapped statistic."""

    statistic: str
    estimate: float
    ci_low: float
    ci_high: float
    n_rounds: int
    alpha: float
    distribution: Sequence[float] = field(repr=False)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_distribution: bool = False) -> dict[str, Any]:
        data = {
            "statistic": self.statistic,
            "estimate": self.estimate,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "n_rounds": self.n_rounds,
            "alpha": self.alpha,
            **self.details,
        }
        if include_distribution:
            data["distribution"] = list(self.distribution)
        return data


def _finite_numeric(values: Sequence[Any], *, name: str):
    np = require_numpy()
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError(f"{name} must contain at least one finite numeric value.")
    return arr


def _ci(values, alpha: float):
    np = require_numpy()
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in the interval (0, 1).")
    low = 100 * (alpha / 2)
    high = 100 * (1 - alpha / 2)
    return np.percentile(values, [low, high])


def bootstrap_summary(
    values: Sequence[Any],
    *,
    statistic: SummaryStatistic | Callable[[Any], float] = "mean",
    n_rounds: int = 1000,
    alpha: float = 0.05,
    random_state: int | None = None,
) -> BootstrapResult:
    """Bootstrap a one-sample summary statistic such as mean or median."""
    np = require_numpy()
    arr = _finite_numeric(values, name="values")
    if n_rounds <= 0:
        raise ValueError("n_rounds must be positive.")
    if statistic == "mean":
        func = np.mean
        name = "mean"
    elif statistic == "median":
        func = np.median
        name = "median"
    elif callable(statistic):
        func = statistic
        name = getattr(statistic, "__name__", "custom_statistic")
    else:
        raise ValueError("statistic must be 'mean', 'median', or a callable.")

    rng = np.random.default_rng(random_state)
    distribution = np.empty(n_rounds, dtype=float)
    n = len(arr)
    for index in range(n_rounds):
        sample = arr[rng.integers(0, n, size=n)]
        distribution[index] = float(func(sample))
    ci_low, ci_high = _ci(distribution, alpha)
    return BootstrapResult(
        statistic=name,
        estimate=float(func(arr)),
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        n_rounds=int(n_rounds),
        alpha=float(alpha),
        distribution=distribution,
        details={"n": int(n)},
    )


def bootstrap_metric(
    *arrays: Sequence[Any],
    metric_func: MetricFunc,
    metric_name: str | None = None,
    n_rounds: int = 1000,
    alpha: float = 0.05,
    random_state: int | None = None,
    drop_invalid: bool = True,
    **metric_kwargs: Any,
) -> BootstrapResult:
    """Bootstrap an arbitrary metric over one or more aligned arrays.

    ``metric_func`` receives the resampled arrays in the same order as provided.
    This works for scores such as ``roc_auc_score(y_true, y_prob)`` or custom
    cohort metrics such as ``mean_difference(group, value)``.
    """
    np = require_numpy()
    if not arrays:
        raise ValueError("at least one array is required.")
    if n_rounds <= 0:
        raise ValueError("n_rounds must be positive.")
    converted = [np.asarray(values) for values in arrays]
    lengths = {len(values) for values in converted}
    if len(lengths) != 1:
        raise ValueError("all arrays must have the same length.")
    n = lengths.pop()
    if n == 0:
        raise ValueError("arrays must not be empty.")

    rng = np.random.default_rng(random_state)
    values: list[float] = []
    for _ in range(n_rounds):
        indices = rng.integers(0, n, size=n)
        sampled = [values_[indices] for values_ in converted]
        try:
            metric_value = float(metric_func(*sampled, **metric_kwargs))
        except Exception:
            if drop_invalid:
                continue
            raise
        if np.isfinite(metric_value):
            values.append(metric_value)
    if not values:
        raise ValueError("no valid bootstrap rounds were produced.")
    distribution = np.asarray(values, dtype=float)
    ci_low, ci_high = _ci(distribution, alpha)
    estimate = float(metric_func(*converted, **metric_kwargs))
    return BootstrapResult(
        statistic=metric_name or getattr(metric_func, "__name__", "metric"),
        estimate=estimate,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        n_rounds=int(len(distribution)),
        alpha=float(alpha),
        distribution=distribution,
        details={
            "n": int(n),
            "requested_rounds": int(n_rounds),
            "dropped_rounds": int(n_rounds - len(distribution)),
        },
    )


def _binary_confusion(y_true, y_pred, *, pos_label: Any = 1) -> dict[str, int]:
    np = require_numpy()
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    positive_true = yt == pos_label
    positive_pred = yp == pos_label
    tp = int(np.sum(positive_true & positive_pred))
    tn = int(np.sum(~positive_true & ~positive_pred))
    fp = int(np.sum(~positive_true & positive_pred))
    fn = int(np.sum(positive_true & ~positive_pred))
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return float("nan")
    return float(numerator / denominator)


def _auc_from_ranks(y_true, y_score, *, pos_label: Any = 1) -> float:
    np = require_numpy()
    stats = require_scipy_stats()
    yt = np.asarray(y_true)
    score = np.asarray(y_score, dtype=float)
    positive = yt == pos_label
    n_pos = int(np.sum(positive))
    n_neg = int(np.sum(~positive))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = stats.rankdata(score)
    rank_sum_pos = float(np.sum(ranks[positive]))
    auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return float(auc)


def _binary_metrics(
    y_true,
    y_pred,
    y_prob=None,
    *,
    pos_label: Any = 1,
) -> dict[str, float]:
    cm = _binary_confusion(y_true, y_pred, pos_label=pos_label)
    tp = cm["tp"]
    tn = cm["tn"]
    fp = cm["fp"]
    fn = cm["fn"]
    sensitivity = _safe_divide(tp, tp + fn)
    specificity = _safe_divide(tn, tn + fp)
    precision = _safe_divide(tp, tp + fp)
    npv = _safe_divide(tn, tn + fn)
    accuracy = _safe_divide(tp + tn, tp + tn + fp + fn)
    f1 = _safe_divide(2 * precision * sensitivity, precision + sensitivity)
    metrics = {
        "accuracy": accuracy,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balanced_accuracy": (sensitivity + specificity) / 2,
        "precision": precision,
        "npv": npv,
        "f1": f1,
        "tp": float(tp),
        "tn": float(tn),
        "fp": float(fp),
        "fn": float(fn),
    }
    if y_prob is not None:
        metrics["auc"] = _auc_from_ranks(y_true, y_prob, pos_label=pos_label)
    return metrics


def bootstrap_binary_classification_metrics(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    y_prob: Sequence[Any] | None = None,
    *,
    metrics: Sequence[str] | None = None,
    pos_label: Any = 1,
    n_rounds: int = 1000,
    alpha: float = 0.05,
    random_state: int | None = None,
    drop_invalid: bool = True,
) -> pd.DataFrame:
    """Bootstrap common binary classification metrics.

    Returns one row per metric with the original estimate, percentile
    confidence interval, completed rounds, and dropped rounds.
    """
    np = require_numpy()
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    if len(yt) != len(yp):
        raise ValueError("y_true and y_pred must have the same length.")
    if y_prob is not None:
        y_score = np.asarray(y_prob, dtype=float)
        if len(y_score) != len(yt):
            raise ValueError("y_prob must have the same length as y_true.")
    else:
        y_score = None
    if len(yt) == 0:
        raise ValueError("y_true must not be empty.")
    if n_rounds <= 0:
        raise ValueError("n_rounds must be positive.")

    estimate = _binary_metrics(yt, yp, y_score, pos_label=pos_label)
    selected_metrics = list(metrics or estimate.keys())
    missing = [metric for metric in selected_metrics if metric not in estimate]
    if missing:
        raise ValueError(f"unknown or unavailable metrics: {missing}")

    rng = np.random.default_rng(random_state)
    distributions: dict[str, list[float]] = {metric: [] for metric in selected_metrics}
    dropped = 0
    n = len(yt)
    for _ in range(n_rounds):
        indices = rng.integers(0, n, size=n)
        boot = _binary_metrics(
            yt[indices],
            yp[indices],
            y_score[indices] if y_score is not None else None,
            pos_label=pos_label,
        )
        valid_round = True
        for metric in selected_metrics:
            value = boot[metric]
            if not np.isfinite(value):
                valid_round = False
                break
        if not valid_round:
            if drop_invalid:
                dropped += 1
                continue
            raise ValueError("bootstrap round produced a non-finite metric.")
        for metric in selected_metrics:
            distributions[metric].append(float(boot[metric]))

    rows = []
    for metric in selected_metrics:
        values = np.asarray(distributions[metric], dtype=float)
        if values.size == 0:
            raise ValueError(f"metric {metric!r} had no valid bootstrap rounds.")
        ci_low, ci_high = _ci(values, alpha)
        rows.append(
            {
                "metric": metric,
                "estimate": float(estimate[metric]),
                "ci_low": float(ci_low),
                "ci_high": float(ci_high),
                "n_rounds": int(values.size),
                "requested_rounds": int(n_rounds),
                "dropped_rounds": int(dropped),
                "alpha": float(alpha),
            }
        )
    return pd.DataFrame(rows)
