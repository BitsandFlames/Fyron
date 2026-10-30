"""Descriptive analysis tables for clinical cohorts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from fyron import statistics as fst


def describe_numeric(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    group_col: str | None = None,
    digits: int = 2,
) -> pd.DataFrame:
    """Describe numeric variables with n, missing, mean, SD, median, IQR, and range.

    Parameters
    ----------
    df
        Cohort or analysis table.
    columns
        Numeric columns to summarize. If omitted, numeric columns are selected
        automatically.
    group_col
        Optional grouping column for stratified summaries.
    digits
        Decimal places used for rounded numeric summaries.

    Returns
    -------
    pandas.DataFrame
        Long table with one row per variable and group containing count,
        missingness, mean, standard deviation, median, quartiles, and range.
    """

    selected = list(columns or df.select_dtypes(include="number").columns)
    if group_col in selected:
        selected.remove(group_col)
    _require_columns(df, selected + ([group_col] if group_col else []))
    groups = [(None, df)] if group_col is None else list(df.groupby(group_col, dropna=False))
    rows = []
    for group, group_df in groups:
        for col in selected:
            values = pd.to_numeric(group_df[col], errors="coerce")
            finite = values[np.isfinite(values)]
            q1 = finite.quantile(0.25) if len(finite) else np.nan
            q3 = finite.quantile(0.75) if len(finite) else np.nan
            rows.append(
                {
                    "group": group if group_col else "overall",
                    "variable": col,
                    "n": int(finite.count()),
                    "missing": int(values.isna().sum()),
                    "mean": round(float(finite.mean()), digits) if len(finite) else np.nan,
                    "sd": round(float(finite.std()), digits) if len(finite) > 1 else np.nan,
                    "median": round(float(finite.median()), digits) if len(finite) else np.nan,
                    "q1": round(float(q1), digits) if pd.notna(q1) else np.nan,
                    "q3": round(float(q3), digits) if pd.notna(q3) else np.nan,
                    "min": round(float(finite.min()), digits) if len(finite) else np.nan,
                    "max": round(float(finite.max()), digits) if len(finite) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def describe_categorical(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    group_col: str | None = None,
    include_missing: bool = True,
    digits: int = 1,
) -> pd.DataFrame:
    """Describe categorical variables with counts and percentages.

    Parameters
    ----------
    df
        Cohort or analysis table.
    columns
        Categorical columns to summarize. If omitted, non-numeric columns are
        selected automatically.
    group_col
        Optional grouping column for stratified summaries.
    include_missing
        Include missing values as an explicit ``"<missing>"`` level.
    digits
        Decimal places used for percentages.

    Returns
    -------
    pandas.DataFrame
        Long table with group, variable, level, count, and percent columns.
    """

    selected = list(columns or [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])])
    if group_col in selected:
        selected.remove(group_col)
    _require_columns(df, selected + ([group_col] if group_col else []))
    groups = [(None, df)] if group_col is None else list(df.groupby(group_col, dropna=False))
    rows = []
    for group, group_df in groups:
        for col in selected:
            counts = group_df[col].value_counts(dropna=not include_missing)
            for level, n in counts.items():
                rows.append(
                    {
                        "group": group if group_col else "overall",
                        "variable": col,
                        "level": "<missing>" if pd.isna(level) else level,
                        "n": int(n),
                        "percent": round(float(100 * n / len(group_df)), digits) if len(group_df) else 0.0,
                    }
                )
    return pd.DataFrame(rows)


def compare_descriptive_groups(
    df: pd.DataFrame,
    *,
    group_col: str,
    numeric: Sequence[str] | None = None,
    categorical: Sequence[str] | None = None,
    include_smd: bool = True,
) -> pd.DataFrame:
    """Compare descriptive variables across groups with explicit statistical tests.

    Parameters
    ----------
    df
        Cohort or analysis table.
    group_col
        Column defining comparison groups.
    numeric
        Numeric variables to compare. If omitted, numeric columns are selected
        automatically.
    categorical
        Categorical variables to compare. If omitted, remaining non-numeric
        columns are selected automatically.
    include_smd
        If True, include standardized mean difference summaries.

    Returns
    -------
    pandas.DataFrame
        One row per variable with variable type, test result fields, p-value,
        optional SMD, and error text when a comparison cannot be computed.
    """

    _require_columns(df, [group_col])
    numeric_cols = list(numeric or df.select_dtypes(include="number").columns)
    categorical_cols = list(categorical or [col for col in df.columns if col not in numeric_cols and col != group_col])
    if group_col in numeric_cols:
        numeric_cols.remove(group_col)
    rows = []
    groups = list(df.groupby(group_col, dropna=False))
    if len(groups) < 2:
        raise ValueError("group_col must contain at least two groups.")
    for col in numeric_cols:
        _require_columns(df, [col])
        values = [group_df[col].dropna() for _, group_df in groups]
        try:
            res = (
                fst.compare_two_groups(values[0], values[1], method="mannwhitney")
                if len(values) == 2
                else fst.compare_multiple_groups(values, method="kruskal")
            )
            smd = _numeric_smd(values) if include_smd else np.nan
            rows.append({"variable": col, "type": "numeric", "smd": smd, **res.to_dict()})
        except Exception as exc:
            rows.append({"variable": col, "type": "numeric", "test": "failed", "p_value": np.nan, "smd": np.nan, "error": str(exc)})
    for col in categorical_cols:
        _require_columns(df, [col])
        try:
            table = pd.crosstab(df[col], df[group_col])
            res = fst.categorical_test(table)
            smd = _categorical_smd(df, col, group_col) if include_smd else np.nan
            rows.append({"variable": col, "type": "categorical", "smd": smd, **res.to_dict()})
        except Exception as exc:
            rows.append({"variable": col, "type": "categorical", "test": "failed", "p_value": np.nan, "smd": np.nan, "error": str(exc)})
    return pd.DataFrame(rows)


def create_table_one(
    df: pd.DataFrame,
    *,
    group_col: str | None = None,
    numeric: Sequence[str] | None = None,
    categorical: Sequence[str] | None = None,
    include_smd: bool = True,
) -> pd.DataFrame:
    """Create a table-one style long table with optional p-values.

    Parameters
    ----------
    df
        Cohort table to describe.
    group_col
        Optional group column such as treatment arm, cohort, split, or outcome.
    numeric
        Numeric variables to include. If omitted, numeric columns are selected
        automatically.
    categorical
        Categorical variables to include. If omitted, non-numeric columns are
        selected automatically.
    include_smd
        If True and ``group_col`` is provided, include standardized mean
        difference values.

    Returns
    -------
    pandas.DataFrame
        Long Table 1 style output with variable, level, group, formatted summary,
        and optional p-value, SMD, and test columns.
    """

    num = describe_numeric(df, columns=numeric, group_col=group_col)
    cat = describe_categorical(df, columns=categorical, group_col=group_col)
    columns = ["variable", "level", "group", "summary"]
    num_table = pd.DataFrame(columns=columns)
    cat_table = pd.DataFrame(columns=columns)
    if not num.empty:
        num["summary"] = num.apply(lambda r: f"{r['mean']} ({r['sd']}) / {r['median']} [{r['q1']}, {r['q3']}]", axis=1)
        num_table = num[["variable", "group", "summary"]].copy()
        num_table["level"] = ""
    if not cat.empty:
        cat["summary"] = cat.apply(lambda r: f"{r['n']} ({r['percent']}%)", axis=1)
        cat_table = cat[columns].copy()
    table = pd.concat([num_table[["variable", "level", "group", "summary"]], cat_table], ignore_index=True)
    if group_col is not None:
        comparisons = compare_descriptive_groups(
            df,
            group_col=group_col,
            numeric=numeric,
            categorical=categorical,
            include_smd=include_smd,
        )
        indexed = comparisons.set_index("variable") if not comparisons.empty else pd.DataFrame()
        p_lookup = indexed["p_value"].to_dict() if "p_value" in indexed else {}
        smd_lookup = indexed["smd"].to_dict() if "smd" in indexed else {}
        test_lookup = indexed["test"].to_dict() if "test" in indexed else {}
        table["p_value"] = table["variable"].map(p_lookup)
        table["smd"] = table["variable"].map(smd_lookup)
        table["test"] = table["variable"].map(test_lookup)
    return table


def summarize_endpoint(
    df: pd.DataFrame,
    *,
    event_col: str,
    time_col: str | None = None,
    group_col: str | None = None,
    digits: int = 2,
) -> pd.DataFrame:
    """Summarize endpoint counts, event rates, and optional follow-up time.

    Parameters
    ----------
    df
        Cohort table containing endpoint and optional follow-up columns.
    event_col
        Binary or numeric event-indicator column where nonzero values count as
        events.
    time_col
        Optional duration/follow-up column to summarize.
    group_col
        Optional grouping column for stratified endpoint summaries.
    digits
        Decimal places used for percentages and follow-up summaries.

    Returns
    -------
    pandas.DataFrame
        One row per group with sample size, event count, event rate, and optional
        median/min/max follow-up.
    """

    _require_columns(df, [event_col] + ([time_col] if time_col else []) + ([group_col] if group_col else []))
    groups = [(None, df)] if group_col is None else list(df.groupby(group_col, dropna=False))
    rows = []
    for group, group_df in groups:
        events = pd.to_numeric(group_df[event_col], errors="coerce").fillna(0)
        row = {
            "group": group if group_col else "overall",
            "n": int(len(group_df)),
            "events": int(events.sum()),
            "event_rate_percent": round(float(100 * events.mean()), digits) if len(group_df) else 0.0,
        }
        if time_col:
            times = pd.to_numeric(group_df[time_col], errors="coerce")
            row["median_followup"] = round(float(times.median()), digits)
            row["min_followup"] = round(float(times.min()), digits)
            row["max_followup"] = round(float(times.max()), digits)
        rows.append(row)
    return pd.DataFrame(rows)


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _numeric_smd(values: Sequence[pd.Series]) -> float:
    if len(values) == 2:
        return fst.standardized_mean_difference(values[0], values[1])
    smds = [
        abs(fst.standardized_mean_difference(values[i], values[j]))
        for i in range(len(values))
        for j in range(i + 1, len(values))
    ]
    return float(np.max(smds)) if smds else np.nan


def _categorical_smd(df: pd.DataFrame, col: str, group_col: str) -> float:
    groups = list(df.groupby(group_col, dropna=False))
    levels = pd.Series(df[col].dropna().unique())
    if len(groups) < 2 or levels.empty:
        return np.nan
    smds = []
    for level in levels:
        indicators = [(group_df[col] == level).astype(int) for _, group_df in groups]
        for i in range(len(indicators)):
            for j in range(i + 1, len(indicators)):
                smds.append(abs(fst.standardized_mean_difference(indicators[i], indicators[j], categorical=True)))
    return float(np.max(smds)) if smds else np.nan
