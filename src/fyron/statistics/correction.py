"""Multiple-testing correction helpers for manuscript tables."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import pandas as pd

from ._deps import require_numpy

PValueCorrectionMethod = Literal["fdr_bh", "benjamini_hochberg", "bonferroni", "holm", "none"]


def adjust_p_values(
    p_values: Sequence[Any],
    *,
    method: PValueCorrectionMethod = "fdr_bh",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Adjust p-values for multiple testing and return a review table.

    Parameters
    ----------
    p_values
        Sequence of raw p-values. Missing values are preserved.
    method
        Correction method: ``"fdr_bh"``/Benjamini-Hochberg, ``"bonferroni"``,
        ``"holm"``, or ``"none"``.
    alpha
        Significance level used to compute the rejected flag.

    Returns
    -------
    pandas.DataFrame
        One row per p-value with raw p-value, adjusted p-value, rank, rejected
        flag, correction method, and alpha.
    """
    np = require_numpy()
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in the interval (0, 1).")
    p = np.asarray(p_values, dtype=float)
    out = np.full(p.shape, np.nan, dtype=float)
    rank = np.full(p.shape, np.nan, dtype=float)
    valid_mask = np.isfinite(p)
    valid = p[valid_mask]
    if ((valid < 0) | (valid > 1)).any():
        raise ValueError("p-values must be between 0 and 1.")

    normalized = _normalize_method(method)
    if valid.size:
        order = np.argsort(valid)
        sorted_p = valid[order]
        ranks_sorted = np.arange(1, valid.size + 1, dtype=float)
        if normalized == "none":
            adjusted_sorted = sorted_p
        elif normalized == "bonferroni":
            adjusted_sorted = np.minimum(sorted_p * valid.size, 1.0)
        elif normalized == "holm":
            adjusted_sorted = np.maximum.accumulate((valid.size - ranks_sorted + 1) * sorted_p)
            adjusted_sorted = np.minimum(adjusted_sorted, 1.0)
        else:
            adjusted_sorted = sorted_p * valid.size / ranks_sorted
            adjusted_sorted = np.minimum.accumulate(adjusted_sorted[::-1])[::-1]
            adjusted_sorted = np.minimum(adjusted_sorted, 1.0)

        valid_adjusted = np.empty_like(valid, dtype=float)
        valid_ranks = np.empty_like(valid, dtype=float)
        valid_adjusted[order] = adjusted_sorted
        valid_ranks[order] = ranks_sorted
        out[valid_mask] = valid_adjusted
        rank[valid_mask] = valid_ranks

    return pd.DataFrame(
        {
            "p_value": p,
            "p_adjusted": out,
            "rank": rank,
            "rejected": out <= alpha,
            "method": normalized,
            "alpha": float(alpha),
        }
    )


def p_value_correction_table(
    df: pd.DataFrame,
    *,
    p_col: str = "p_value",
    method: PValueCorrectionMethod = "fdr_bh",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Append adjusted p-values and rejection flags to a result DataFrame.

    Parameters
    ----------
    df
        Result table containing one raw p-value column, for example a regression,
        correlation, or feature-screening table.
    p_col
        Name of the column containing raw p-values.
    method
        Multiple-testing correction method. Use ``"fdr_bh"`` for
        Benjamini-Hochberg FDR, ``"bonferroni"``, ``"holm"``, or ``"none"``.
    alpha
        Significance threshold used to compute the ``rejected`` flag.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with ``p_adjusted``, ``p_rank``, ``rejected``,
        ``p_adjust_method``, and ``alpha`` columns appended.
    """
    if p_col not in df.columns:
        raise ValueError(f"p_col {p_col!r} is not present in dataframe.")
    out = df.copy()
    corrected = adjust_p_values(out[p_col], method=method, alpha=alpha)
    out["p_adjusted"] = corrected["p_adjusted"].to_numpy()
    out["p_rank"] = corrected["rank"].to_numpy()
    out["rejected"] = corrected["rejected"].to_numpy()
    out["p_adjust_method"] = corrected["method"].to_numpy()
    out["alpha"] = corrected["alpha"].to_numpy()
    return out


def _normalize_method(method: str) -> str:
    key = method.lower().replace("-", "_")
    aliases = {"bh": "fdr_bh", "benjamini_hochberg": "fdr_bh"}
    key = aliases.get(key, key)
    if key not in {"fdr_bh", "bonferroni", "holm", "none"}:
        raise ValueError("method must be 'fdr_bh', 'bonferroni', 'holm', or 'none'.")
    return key
