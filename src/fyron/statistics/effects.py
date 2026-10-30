"""Effect-size helpers for clinical descriptive analysis."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ._deps import require_numpy, require_scipy_stats


def cohens_d(group_a: Sequence[Any], group_b: Sequence[Any]) -> float:
    """Return Cohen's d; zero pooled variance produces NaN, not zero effect."""

    np = require_numpy()
    a = _numeric(group_a)
    b = _numeric(group_b)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = (((len(a) - 1) * np.var(a, ddof=1)) + ((len(b) - 1) * np.var(b, ddof=1))) / (len(a) + len(b) - 2)
    if pooled <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pooled))


def cliffs_delta(group_a: Sequence[Any], group_b: Sequence[Any]) -> float:
    """Return Cliff's delta for ordinal/non-parametric two-group comparisons."""

    np = require_numpy()
    a = _numeric(group_a)
    b = _numeric(group_b)
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    comparisons = np.subtract.outer(a, b)
    return float((np.sum(comparisons > 0) - np.sum(comparisons < 0)) / (len(a) * len(b)))


def cramers_v(table: Sequence[Sequence[Any]]) -> float:
    """Return Cramer's V for a contingency table."""

    np = require_numpy()
    stats = require_scipy_stats()
    observed = np.asarray(table, dtype=float)
    if observed.ndim != 2 or min(observed.shape) < 2:
        raise ValueError("table must be at least 2x2.")
    chi2 = stats.chi2_contingency(observed, correction=False).statistic
    n = observed.sum()
    if n <= 0:
        return float("nan")
    return float(np.sqrt((chi2 / n) / (min(observed.shape) - 1)))


def odds_ratio_ci(
    table: Sequence[Sequence[Any]],
    *,
    alpha: float = 0.05,
    correction: float = 0.5,
) -> dict[str, float]:
    """Return odds ratio and Wald confidence interval for a 2x2 table."""

    np = require_numpy()
    stats = require_scipy_stats()
    arr = _table_2x2(table).astype(float)
    if (arr == 0).any() and correction:
        arr = arr + correction
    a, b, c, d = arr.ravel()
    odds = (a * d) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    z = stats.norm.ppf(1 - alpha / 2)
    log_or = np.log(odds)
    return {
        "odds_ratio": float(odds),
        "ci_lower": float(np.exp(log_or - z * se)),
        "ci_upper": float(np.exp(log_or + z * se)),
        "alpha": float(alpha),
    }


def risk_ratio_ci(
    table: Sequence[Sequence[Any]],
    *,
    alpha: float = 0.05,
    correction: float = 0.5,
) -> dict[str, float]:
    """Return risk ratio and Wald confidence interval for a 2x2 table."""

    np = require_numpy()
    stats = require_scipy_stats()
    arr = _table_2x2(table).astype(float)
    if (arr == 0).any() and correction:
        arr = arr + correction
    a, b, c, d = arr.ravel()
    risk_a = a / (a + b)
    risk_c = c / (c + d)
    rr = risk_a / risk_c
    se = np.sqrt((1 / a) - (1 / (a + b)) + (1 / c) - (1 / (c + d)))
    z = stats.norm.ppf(1 - alpha / 2)
    log_rr = np.log(rr)
    return {
        "risk_ratio": float(rr),
        "ci_lower": float(np.exp(log_rr - z * se)),
        "ci_upper": float(np.exp(log_rr + z * se)),
        "alpha": float(alpha),
    }


def standardized_mean_difference(group_a: Sequence[Any], group_b: Sequence[Any], *, categorical: bool = False) -> float:
    """Return numeric/binary SMD, or NaN when its denominator is zero."""

    np = require_numpy()
    if categorical:
        a = np.asarray(group_a)
        b = np.asarray(group_b)
        if len(a) == 0 or len(b) == 0:
            return float("nan")
        pa = np.mean(a.astype(bool))
        pb = np.mean(b.astype(bool))
        pooled = np.sqrt((pa * (1 - pa) + pb * (1 - pb)) / 2)
        return float((pa - pb) / pooled) if pooled > 0 else float("nan")
    return cohens_d(group_a, group_b)


def _numeric(values: Sequence[Any]):
    np = require_numpy()
    arr = np.asarray(values, dtype=float)
    return arr[np.isfinite(arr)]


def _table_2x2(table: Sequence[Sequence[Any]]):
    np = require_numpy()
    arr = np.asarray(table, dtype=float)
    if arr.shape != (2, 2):
        raise ValueError("table must be 2x2.")
    if (arr < 0).any():
        raise ValueError("table counts must be non-negative.")
    return arr
