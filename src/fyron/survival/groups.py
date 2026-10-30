"""Survival cohort grouping utilities."""

from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence

import numpy as np
import pandas as pd

from fyron.survival._validate import require_columns, validate_non_empty_groups

SplitMethod = Literal["categorical", "median", "tertile", "quartile", "custom"]


def create_survival_groups(
    df: pd.DataFrame,
    column: str,
    method: SplitMethod,
    group_col: str,
    *,
    bins: int | Sequence[float] | None = None,
    labels: Sequence[str] | bool | None = None,
    duplicates: Literal["raise", "drop"] = "drop",
) -> pd.DataFrame:
    """Add a survival/stratification group column to a copy of ``df``.

    Parameters
    ----------
    df
        Input table.
    column
        Column used to derive groups (categorical levels or numeric for splits).
    method
        ``\"categorical\"`` copies stringified levels from ``column``.
        ``\"median\"``, ``\"tertile\"``, and ``\"quartile\"`` use ``pandas.qcut``.
        ``\"custom\"`` uses ``pandas.cut`` with ``bins`` (required).
    group_col
        Name of the new column to create.
    bins
        For ``method=\"custom\"``: edges passed to ``pandas.cut`` (sequence of bin edges
        or an integer number of equal-width bins). Ignored for quantile methods unless
        you rely on ``pandas`` defaults for integer ``bins`` with ``cut`` (not used here).
    labels
        Optional labels for ``qcut``/``cut`` groups. Must match the number of resulting bins.
    duplicates
        Quantile method duplicate policy. ``\"drop\"`` matches ``pandas.qcut``; ``\"raise\"``
        surfaces ``ValueError`` when quantiles are not distinct.

    Returns
    -------
    pandas.DataFrame
        A **copy** of ``df`` including ``group_col``.

    Raises
    ------
    ValueError
        If any resulting group is empty, quantiles cannot be formed, or arguments are invalid.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.survival.groups import create_survival_groups
    >>> df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 6, 7, 8]})
    >>> out = create_survival_groups(df, "x", "quartile", "g")
    >>> sorted(out["g"].astype(str).unique())
    ['Q1', 'Q2', 'Q3', 'Q4']
    """
    require_columns(df, [column], context="create_survival_groups")
    out = df.copy()

    if group_col in df.columns:
        raise ValueError(f"group_col {group_col!r} already exists; choose a new column name.")

    if method == "categorical":
        grp = out[column].astype("string")
        if grp.isna().any():
            raise ValueError(f"Column {column!r} contains NaN; drop rows or fill before grouping.")
        out[group_col] = grp
    elif method == "median":
        out[group_col] = _qcut_labels(
            out[column],
            q=2,
            default_labels=("below_median", "above_median"),
            labels=labels,
            duplicates=duplicates,
        )
    elif method == "tertile":
        out[group_col] = _qcut_labels(
            out[column],
            q=3,
            default_labels=("T1", "T2", "T3"),
            labels=labels,
            duplicates=duplicates,
        )
    elif method == "quartile":
        out[group_col] = _qcut_labels(
            out[column],
            q=4,
            default_labels=("Q1", "Q2", "Q3", "Q4"),
            labels=labels,
            duplicates=duplicates,
        )
    elif method == "custom":
        if bins is None:
            raise ValueError('method="custom" requires the ``bins`` argument.')
        out[group_col] = pd.cut(out[column], bins=bins, labels=labels, include_lowest=True)
        if out[group_col].isna().any():
            bad = int(out[group_col].isna().sum())
            raise ValueError(
                f"After binning, {bad} row(s) fell outside bins; adjust ``bins`` or filter data."
            )
    else:
        raise ValueError(f"Unknown method: {method!r}")

    counts = out.groupby(group_col, dropna=False, observed=True).size().to_dict()
    validate_non_empty_groups(counts.keys(), counts)
    return out


def _qcut_labels(
    series: pd.Series,
    *,
    q: int,
    default_labels: Sequence[str],
    labels: Sequence[str] | bool | None,
    duplicates: Literal["raise", "drop"],
) -> pd.Series:
    if series.isna().any():
        raise ValueError("Cannot split on a column that contains NaN.")
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError("median/tertile/quartile splits require a numeric column.")
    dup = "drop" if duplicates == "drop" else "raise"
    use_labels: Any
    if labels is None:
        use_labels = list(default_labels)
    else:
        use_labels = labels
    try:
        cats = pd.qcut(series, q=q, labels=use_labels, duplicates=dup)
    except ValueError as exc:
        raise ValueError(
            f"Could not form {q} quantile groups on column (duplicate quantiles or too few rows). "
            f"Original error: {exc}"
        ) from exc
    if dup == "drop" and isinstance(cats.dtype, pd.CategoricalDtype):
        n_cat = cats.cat.categories.size
        if n_cat < q:
            raise ValueError(
                f"Quantile split produced only {n_cat} distinct group(s) but {q} were required; "
                "try fewer splits, remove duplicate values, or use method='custom'."
            )
    return cats.astype("string")


def default_tau_from_observed_times(
    df: pd.DataFrame,
    duration_col: str,
    group_col: str | None = None,
) -> float:
    """Default RMST truncation: minimum of per-group maximum observed times."""
    require_columns(df, [duration_col])
    if group_col is None:
        return float(df[duration_col].max())
    require_columns(df, [group_col])
    mins: list[float] = []
    for _, part in df.groupby(group_col, observed=True):
        if part.empty:
            continue
        mins.append(float(part[duration_col].max()))
    if not mins:
        raise ValueError("No rows available to compute default tau.")
    return float(np.min(mins))
