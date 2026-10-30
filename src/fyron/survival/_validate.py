"""Shared validation helpers for survival analysis."""

from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd
from fyron._survival_data import duration_column, event_column, positive_horizon


def require_columns(df: pd.DataFrame, columns: Sequence[str], *, context: str = "") -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        label = f" ({context})" if context else ""
        raise KeyError(f"Missing required column(s){label}: {missing}")


def validate_duration_column(
    series: pd.Series,
    *,
    name: str = "duration",
    allow_infinite: bool = False,
) -> None:
    duration_column(series, name=name, allow_infinite=allow_infinite)


def validate_event_column(series: pd.Series, *, name: str = "event") -> pd.Series:
    return event_column(series, name=name)


def validate_positive_tau(tau: float, *, name: str = "tau") -> None:
    positive_horizon(tau, name=name)


def validate_non_empty_groups(labels: Iterable[object], counts: dict[object, int]) -> None:
    empty = [g for g in labels if counts.get(g, 0) == 0]
    if empty:
        raise ValueError(f"Every group must have at least one row; empty groups: {empty}")


def assert_unique_index(df: pd.DataFrame) -> None:
    if not df.index.is_unique:
        raise IndexError("DataFrame index must be unique; use reset_index(drop=True).")


def formula_complete_rows(df: pd.DataFrame, formula: str) -> pd.DataFrame:
    """Keep complete formula rows without dropping unrelated missing columns."""
    from formulaic import model_matrix

    matrix = model_matrix(formula, df, na_action="drop")
    return df.loc[matrix.index].copy()
