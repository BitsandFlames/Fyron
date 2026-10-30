"""Stable categorical encoding helpers without sklearn dependency."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd


def summarize_encoding_plan(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    max_levels: int = 20,
) -> pd.DataFrame:
    """Summarize categorical levels before one-hot encoding."""

    if max_levels <= 0:
        raise ValueError("max_levels must be positive.")
    selected = _resolve_columns(df, columns)
    rows = []
    for col in selected:
        counts = df[col].value_counts(dropna=False)
        rows.append(
            {
                "column": col,
                "n_levels": int(df[col].nunique(dropna=True)),
                "missing": int(df[col].isna().sum()),
                "top_levels": "|".join(map(str, counts.head(max_levels).index.tolist())),
                "max_levels": int(max_levels),
            }
        )
    return pd.DataFrame(rows)


def fit_categorical_encoder(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    drop_first: bool = False,
    rare_min_count: int | None = None,
    rare_label: str = "__rare__",
) -> dict[str, Any]:
    """Fit a deterministic one-hot encoder specification."""

    selected = _resolve_columns(df, columns)
    if rare_min_count is not None and rare_min_count < 1:
        raise ValueError("rare_min_count must be positive when provided.")
    levels: dict[str, list[str]] = {}
    for col in selected:
        series = df[col].astype(object).fillna("__missing__").astype(str)
        if rare_min_count is not None:
            counts = series.value_counts()
            kept = [level for level, count in counts.items() if count >= rare_min_count]
            if len(kept) < len(counts):
                kept.append(rare_label)
        else:
            kept = sorted(series.unique().tolist())
        levels[col] = sorted(set(kept))
    encoder = {
        "type": "fyron_categorical_encoder",
        "columns": selected,
        "levels": levels,
        "drop_first": bool(drop_first),
        "rare_min_count": rare_min_count,
        "rare_label": rare_label,
        "metadata": {"n_rows_fit": int(len(df))},
    }
    _validate_output_names(df, encoder)
    return encoder


def apply_categorical_encoder(df: pd.DataFrame, encoder: dict[str, Any]) -> pd.DataFrame:
    """Apply a fitted Fyron categorical encoder."""

    columns = list(encoder.get("columns", []))
    _require_columns(df, columns)
    _validate_output_names(df, encoder)
    out = df.drop(columns=columns).copy()
    rare_min_count = encoder.get("rare_min_count")
    rare_label = encoder.get("rare_label", "__rare__")
    for col in columns:
        levels = list(encoder["levels"][col])
        encoded_levels = levels[1:] if encoder.get("drop_first", False) else levels
        values = df[col].astype(object).fillna("__missing__").astype(str)
        known = set(levels)
        if rare_min_count is not None and rare_label in known:
            values = values.where(values.isin(known), rare_label)
        for level in encoded_levels:
            out[f"{col}__{_safe_level(level)}"] = (values == level).astype(int)
    return out


def encode_categorical(df: pd.DataFrame, **kwargs: Any) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit and apply a categorical encoder to one DataFrame."""

    encoder = fit_categorical_encoder(df, **kwargs)
    return apply_categorical_encoder(df, encoder), encoder


def _resolve_columns(df: pd.DataFrame, columns: Sequence[str] | None) -> list[str]:
    selected = list(columns) if columns is not None else [
        col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])
    ]
    _require_columns(df, selected)
    return selected


def _safe_level(level: Any) -> str:
    return str(level).strip().replace(" ", "_").replace("/", "_").replace("\\", "_")


def _validate_output_names(df: pd.DataFrame, encoder: dict[str, Any]) -> None:
    names = list(df.drop(columns=encoder["columns"]).columns)
    for col in encoder["columns"]:
        levels = encoder["levels"][col]
        levels = levels[1:] if encoder.get("drop_first", False) else levels
        names.extend(f"{col}__{_safe_level(level)}" for level in levels)
    if len(names) != len(set(names)):
        raise ValueError("Encoded column name collision; rename columns or category levels before encoding.")


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
