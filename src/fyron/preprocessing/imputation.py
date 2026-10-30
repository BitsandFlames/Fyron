"""Simple train/apply imputation helpers for clinical tables."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import pandas as pd

NumericStrategy = Literal["median", "mean", "constant"]
CategoricalStrategy = Literal["most_frequent", "constant"]


def summarize_imputation_plan(
    df: pd.DataFrame,
    *,
    numeric: Sequence[str] | None = None,
    categorical: Sequence[str] | None = None,
    strategy_numeric: NumericStrategy = "median",
    strategy_categorical: CategoricalStrategy = "most_frequent",
) -> pd.DataFrame:
    """Summarize columns and strategies before fitting an imputer."""

    numeric_cols, categorical_cols = _resolve_columns(df, numeric, categorical)
    _validate_strategies(strategy_numeric, strategy_categorical)
    rows = []
    for col in numeric_cols:
        rows.append(_plan_row(df, col, "numeric", strategy_numeric))
    for col in categorical_cols:
        rows.append(_plan_row(df, col, "categorical", strategy_categorical))
    return pd.DataFrame(rows)


def fit_imputer(
    df: pd.DataFrame,
    *,
    numeric: Sequence[str] | None = None,
    categorical: Sequence[str] | None = None,
    strategy_numeric: NumericStrategy = "median",
    strategy_categorical: CategoricalStrategy = "most_frequent",
    fill_value_numeric: float = 0.0,
    fill_value_categorical: str = "__missing__",
    add_missing_indicators: bool = False,
) -> dict[str, Any]:
    """Fit a lightweight imputation specification on a training DataFrame."""

    numeric_cols, categorical_cols = _resolve_columns(df, numeric, categorical)
    _validate_strategies(strategy_numeric, strategy_categorical)
    if add_missing_indicators:
        _validate_indicator_names(df, numeric_cols + categorical_cols)
    fill_values: dict[str, Any] = {}
    for col in numeric_cols:
        values = pd.to_numeric(df[col], errors="coerce")
        if strategy_numeric == "median":
            value = values.median()
        elif strategy_numeric == "mean":
            value = values.mean()
        else:
            value = fill_value_numeric
        fill_values[col] = float(value) if pd.notna(value) else float(fill_value_numeric)
    for col in categorical_cols:
        series = df[col]
        if strategy_categorical == "most_frequent":
            mode = series.mode(dropna=True)
            value = mode.iloc[0] if not mode.empty else fill_value_categorical
        else:
            value = fill_value_categorical
        fill_values[col] = value
    return {
        "type": "fyron_imputer",
        "numeric": list(numeric_cols),
        "categorical": list(categorical_cols),
        "strategies": {"numeric": strategy_numeric, "categorical": strategy_categorical},
        "fill_values": fill_values,
        "add_missing_indicators": bool(add_missing_indicators),
        "metadata": {"n_rows_fit": int(len(df))},
    }


def apply_imputer(df: pd.DataFrame, imputer: dict[str, Any]) -> pd.DataFrame:
    """Apply a fitted Fyron imputer to a DataFrame."""

    columns = list(imputer.get("numeric", [])) + list(imputer.get("categorical", []))
    _require_columns(df, columns)
    if imputer.get("add_missing_indicators", False):
        _validate_indicator_names(df, columns)
    out = df.copy()
    fill_values = imputer.get("fill_values", {})
    for col in imputer.get("numeric", []):
        values = pd.to_numeric(out[col], errors="coerce")
        if imputer.get("add_missing_indicators", False):
            out[f"{col}_was_missing"] = values.isna().astype(int)
        fill = fill_values[col]
        if (values.isna().any() and pd.api.types.is_integer_dtype(values.dtype)
                and float(fill) != int(fill)):
            values = values.astype("Float64")
        out[col] = values.fillna(fill)
    for col in imputer.get("categorical", []):
        if imputer.get("add_missing_indicators", False):
            out[f"{col}_was_missing"] = out[col].isna().astype(int)
        values = out[col]
        fill = fill_values[col]
        if (isinstance(values.dtype, pd.CategoricalDtype) and pd.notna(fill)
                and fill not in values.cat.categories):
            values = values.cat.add_categories([fill])
        out[col] = values.fillna(fill)
    return out


def impute_dataframe(df: pd.DataFrame, **kwargs: Any) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit and apply an imputer to one DataFrame."""

    imputer = fit_imputer(df, **kwargs)
    return apply_imputer(df, imputer), imputer


def _resolve_columns(
    df: pd.DataFrame,
    numeric: Sequence[str] | None,
    categorical: Sequence[str] | None,
) -> tuple[list[str], list[str]]:
    numeric_cols = list(numeric) if numeric is not None else list(df.select_dtypes(include="number").columns)
    categorical_cols = (
        list(categorical)
        if categorical is not None
        else [col for col in df.columns if col not in numeric_cols]
    )
    _require_columns(df, numeric_cols + categorical_cols)
    overlap = set(numeric_cols).intersection(categorical_cols)
    if overlap:
        raise ValueError(f"Columns cannot be both numeric and categorical: {sorted(overlap)}")
    return numeric_cols, categorical_cols


def _plan_row(df: pd.DataFrame, col: str, kind: str, strategy: str) -> dict[str, Any]:
    return {
        "column": col,
        "type": kind,
        "strategy": strategy,
        "n": int(len(df)),
        "missing": int(df[col].isna().sum()),
        "missing_percent": float(df[col].isna().mean() * 100) if len(df) else 0.0,
    }


def _validate_strategies(strategy_numeric: str, strategy_categorical: str) -> None:
    if strategy_numeric not in {"median", "mean", "constant"}:
        raise ValueError("strategy_numeric must be 'median', 'mean', or 'constant'.")
    if strategy_categorical not in {"most_frequent", "constant"}:
        raise ValueError("strategy_categorical must be 'most_frequent' or 'constant'.")


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _validate_indicator_names(df: pd.DataFrame, columns: Sequence[str]) -> None:
    names = [f"{col}_was_missing" for col in columns]
    if len(set(names)) != len(names) or set(names).intersection(df.columns):
        raise ValueError("Missing indicator columns must not overwrite existing columns.")
