"""Paper-ready statistical QC tables."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from ._deps import require_numpy
from .correction import p_value_correction_table
from .tests import correlation_test, normality_test


def normality_table(
    df: pd.DataFrame,
    columns: Sequence[str],
    *,
    method: str = "shapiro",
) -> pd.DataFrame:
    """Run normality tests for multiple columns and return one table.

    Parameters
    ----------
    df
        Analysis table containing numeric columns to test.
    columns
        Column names to test.
    method
        Normality test passed to ``normality_test``. The default is
        ``"shapiro"``.

    Returns
    -------
    pandas.DataFrame
        One row per variable with test name, statistic, p-value, non-missing
        sample size, and an error column when a test could not be computed.
    """
    rows = []
    for col in columns:
        _require_columns(df, [col])
        try:
            result = normality_test(df[col], method=method)  # type: ignore[arg-type]
            rows.append({"variable": col, **result.to_dict()})
        except Exception as exc:
            rows.append({"variable": col, "test": method, "statistic": pd.NA, "p_value": pd.NA, "n": int(df[col].notna().sum()), "error": str(exc)})
    return pd.DataFrame(rows)


def correlation_pvalue_table(
    df: pd.DataFrame,
    columns: Sequence[str],
    *,
    method: str = "spearman",
    p_adjust: str | None = "fdr_bh",
) -> pd.DataFrame:
    """Return pairwise correlations, p-values, and optional adjusted p-values.

    Parameters
    ----------
    df
        Analysis table containing numeric variables.
    columns
        Variables for pairwise correlation testing.
    method
        Correlation method, typically ``"spearman"`` or ``"pearson"``.
    p_adjust
        Optional multiple-testing correction method. Pass ``None`` to keep only
        raw p-values.

    Returns
    -------
    pandas.DataFrame
        Pairwise table with variable names, method, correlation coefficient,
        p-value, sample size, and optional adjusted p-value columns.
    """
    rows = []
    cols = list(columns)
    _require_columns(df, cols)
    for i, left in enumerate(cols):
        for right in cols[i + 1 :]:
            result = correlation_test(df[left], df[right], method=method)  # type: ignore[arg-type]
            rows.append({"variable_a": left, "variable_b": right, "method": method, "correlation": result.statistic, "p_value": result.p_value, "n": result.n})
    table = pd.DataFrame(rows)
    if p_adjust is not None and not table.empty:
        table = p_value_correction_table(table, p_col="p_value", method=p_adjust)
    return table


def missingness_by_group_table(
    df: pd.DataFrame,
    *,
    group_col: str,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Summarize missingness overall and by group for manuscript supplements.

    Parameters
    ----------
    df
        Cohort or feature table to audit.
    group_col
        Column defining groups such as cohort, center, split, or endpoint status.
    columns
        Columns to summarize. If omitted, all columns except ``group_col`` are
        included.

    Returns
    -------
    pandas.DataFrame
        Long table with variable, group, row count, missing count, and missing
        percent.
    """
    _require_columns(df, [group_col])
    cols = list(columns or [col for col in df.columns if col != group_col])
    _require_columns(df, cols)
    rows = []
    groups = [("overall", df)] + [(str(group), sub) for group, sub in df.groupby(group_col, dropna=False)]
    for variable in cols:
        for group, sub in groups:
            missing = int(sub[variable].isna().sum())
            n = int(len(sub))
            rows.append(
                {
                    "variable": variable,
                    "group": group,
                    "n": n,
                    "missing": missing,
                    "missing_percent": 100 * missing / n if n else 0.0,
                }
            )
    return pd.DataFrame(rows)


def outlier_table(
    df: pd.DataFrame,
    columns: Sequence[str],
    *,
    method: str = "iqr",
    iqr_multiplier: float = 1.5,
) -> pd.DataFrame:
    """Flag numeric outliers by IQR fences and return one summary row per column.

    Parameters
    ----------
    df
        Analysis table containing numeric variables.
    columns
        Numeric columns to inspect.
    method
        Outlier method. Currently only ``"iqr"`` is supported.
    iqr_multiplier
        Multiplier for the IQR fence, commonly ``1.5``.

    Returns
    -------
    pandas.DataFrame
        One row per variable with non-missing count, outlier count, outlier
        percent, lower fence, and upper fence.
    """
    np = require_numpy()
    if method != "iqr":
        raise ValueError("method currently supports only 'iqr'.")
    _require_columns(df, columns)
    rows = []
    for col in columns:
        values = pd.to_numeric(df[col], errors="coerce")
        arr = values.dropna().to_numpy(dtype=float)
        if arr.size == 0:
            rows.append({"variable": col, "n": 0, "outliers": 0, "outlier_percent": 0.0, "lower_fence": pd.NA, "upper_fence": pd.NA})
            continue
        q1, q3 = np.percentile(arr, [25, 75])
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        count = int(((arr < lower) | (arr > upper)).sum())
        rows.append({"variable": col, "n": int(arr.size), "outliers": count, "outlier_percent": 100 * count / arr.size, "lower_fence": float(lower), "upper_fence": float(upper)})
    return pd.DataFrame(rows)


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
