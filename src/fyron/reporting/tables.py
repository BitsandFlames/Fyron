"""Compact publication-oriented tables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


def summarize_baseline_table(
    df: pd.DataFrame,
    *,
    group_col: str | None = None,
    continuous: Sequence[str] | None = None,
    categorical: Sequence[str] | None = None,
    digits: int = 1,
) -> pd.DataFrame:
    """Create a compact baseline characteristics table.

    Parameters
    ----------
    df
        Patient-level cohort or analysis table.
    group_col
        Optional column used to stratify summaries, such as treatment arm,
        risk group, cohort, or center.
    continuous
        Continuous variables to summarize as mean and standard deviation. If
        omitted, numeric columns are selected automatically.
    categorical
        Categorical variables to summarize as count and percent. If omitted,
        non-continuous columns are selected automatically.
    digits
        Decimal places used in formatted summary strings.

    Returns
    -------
    pandas.DataFrame
        Long baseline table with variable, level, summary type, and one column
        per group or an overall column.
    """

    if group_col is not None and group_col not in df.columns:
        raise ValueError(f"group_col {group_col!r} not in dataframe.")
    continuous_cols = list(continuous or df.select_dtypes(include="number").columns)
    categorical_cols = list(categorical or [c for c in df.columns if c not in continuous_cols])
    if group_col in continuous_cols:
        continuous_cols.remove(group_col)
    if group_col in categorical_cols:
        categorical_cols.remove(group_col)
    _require_columns(df, continuous_cols + categorical_cols)

    groups = [(None, df)] if group_col is None else list(df.groupby(group_col, dropna=False))
    rows: list[dict[str, Any]] = []
    for variable in continuous_cols:
        row = {"variable": variable, "level": "", "summary_type": "mean_sd"}
        for group, group_df in groups:
            row[_group_label(group, group_col)] = _format_mean_sd(group_df[variable], digits)
        rows.append(row)
    for variable in categorical_cols:
        levels = df[variable].value_counts(dropna=False).index
        for level in levels:
            row = {"variable": variable, "level": "<missing>" if pd.isna(level) else level, "summary_type": "n_percent"}
            for group, group_df in groups:
                n = int((group_df[variable].isna() if pd.isna(level) else group_df[variable] == level).sum())
                denom = len(group_df)
                pct = 100 * n / denom if denom else 0.0
                row[_group_label(group, group_col)] = f"{n} ({pct:.{digits}f}%)"
            rows.append(row)
    return pd.DataFrame(rows)


def format_estimate_ci(
    estimate: float,
    lower: float,
    upper: float,
    *,
    digits: int = 2,
    separator: str = " to ",
) -> str:
    """Format an estimate and confidence interval for manuscript tables.

    Parameters
    ----------
    estimate
        Point estimate, such as beta, odds ratio, hazard ratio, or metric value.
    lower
        Lower confidence interval bound.
    upper
        Upper confidence interval bound.
    digits
        Decimal places used for all numeric values.
    separator
        Text placed between lower and upper confidence interval bounds.

    Returns
    -------
    str
        Formatted string such as ``"1.24 (1.02 to 1.51)"``.
    """

    return f"{estimate:.{digits}f} ({lower:.{digits}f}{separator}{upper:.{digits}f})"


def metrics_table(
    metrics: Mapping[str, Mapping[str, Any]] | pd.DataFrame,
    *,
    model_col: str = "model",
    digits: int = 3,
) -> pd.DataFrame:
    """Normalize model metrics into a rounded report table.

    Parameters
    ----------
    metrics
        Either a DataFrame that already contains metric columns, or a nested
        mapping such as ``{"RF": {"auc": 0.82}}``.
    model_col
        Name of the output column containing model names.
    digits
        Decimal places used for numeric metric columns.

    Returns
    -------
    pandas.DataFrame
        One row per model or metric source with rounded numeric metric columns.
    """

    if isinstance(metrics, pd.DataFrame):
        table = metrics.copy()
    else:
        table = pd.DataFrame.from_dict(metrics, orient="index").reset_index(names=model_col)
    for col in table.columns:
        if col != model_col and pd.api.types.is_numeric_dtype(table[col]):
            table[col] = table[col].map(lambda value: round(float(value), digits) if pd.notna(value) else value)
    return table


def compare_models_table(
    results: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    model_col: str = "model",
    metrics_key: str = "metrics",
    digits: int = 3,
) -> pd.DataFrame:
    """Combine multiple model result objects into one paper-ready metrics table.

    Parameters
    ----------
    results
        Either ``{"model name": result}`` or a sequence of result dictionaries.
        Each result may contain a ``metrics`` dictionary or metric keys at top level.
    model_col
        Name of the output model column.
    metrics_key
        Key containing the metric dictionary when present.
    digits
        Decimal places for numeric metric columns.

    Returns
    -------
    pandas.DataFrame
        One row per model/result with rounded metric columns.
    """

    rows: list[dict[str, Any]] = []
    if isinstance(results, Mapping):
        iterable = results.items()
    else:
        iterable = enumerate(results)
    for key, result in iterable:
        item = dict(result)
        model_name = item.get(model_col, key)
        metrics = item.get(metrics_key)
        if isinstance(metrics, Mapping):
            row = {model_col: model_name, **dict(metrics)}
        else:
            row = {model_col: model_name}
            row.update({k: v for k, v in item.items() if _is_metric_value(v) and k != model_col})
        rows.append(row)
    return metrics_table(pd.DataFrame(rows), model_col=model_col, digits=digits)


def cohort_flow_table(steps: Sequence[Mapping[str, Any]] | pd.DataFrame) -> pd.DataFrame:
    """Create a simple cohort flow table from named analysis steps.

    ``steps`` may be a sequence of dictionaries or a DataFrame such as
    ``FlowTracker.to_dataframe()`` output.

    Parameters
    ----------
    steps
        Ordered step records with at least ``step`` or ``label`` and ``n``.
        Optional ``excluded`` and ``reason`` values are preserved or derived.

    Returns
    -------
    pandas.DataFrame
        Ordered flow table with step number, label, count, excluded count, and
        exclusion reason.
    """

    rows = []
    previous_n: int | None = None
    iterable = steps.to_dict(orient="records") if isinstance(steps, pd.DataFrame) else steps
    for index, step in enumerate(iterable, start=1):
        label = step.get("step") or step.get("label")
        if label is None:
            raise ValueError("Each step must include 'step' or 'label'.")
        n = step.get("n")
        if n is None:
            raise ValueError("Each step must include 'n'.")
        n_int = int(n)
        excluded = step.get("excluded")
        if pd.isna(excluded):
            excluded = None
        if excluded is None and previous_n is not None:
            excluded = previous_n - n_int
        rows.append(
            {
                "order": index,
                "step": label,
                "n": n_int,
                "excluded": None if excluded is None else int(excluded),
                "reason": step.get("reason"),
            }
        )
        previous_n = n_int
    return pd.DataFrame(rows)


def dataframe_to_markdown(df: pd.DataFrame, *, index: bool = False) -> str:
    """Render a DataFrame as a plain Markdown table.

    Parameters
    ----------
    df
        DataFrame to render.
    index
        If True, include the DataFrame index as the first column.

    Returns
    -------
    str
        Markdown table string suitable for notes, reports, documentation, or
        pull-request review.
    """

    table = df.reset_index() if index else df.copy()
    headers = [str(col) for col in table.columns]
    rows = [[_stringify(value) for value in row] for row in table.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _format_mean_sd(values: pd.Series, digits: int) -> str:
    values = pd.to_numeric(values, errors="coerce")
    return f"{values.mean():.{digits}f} ({values.std():.{digits}f})"


def _is_metric_value(value: Any) -> bool:
    return isinstance(value, (int, float, bool)) or value is None


def _stringify(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def _group_label(group: Any, group_col: str | None) -> str:
    if group_col is None:
        return "overall"
    return f"{group_col}={group}"


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
