"""Small, inspectable preprocessing QC tables for clinical cohorts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd


def summarize_missingness(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    group_col: str | None = None,
) -> pd.DataFrame:
    """Summarize missing values by column, optionally within groups."""

    _require_columns(df, [group_col] if group_col else [])
    selected = _select_columns(df, columns)
    if group_col is None:
        return _missingness_for_frame(df[selected], group=None)
    frames = []
    for group_value, group_df in df.groupby(group_col, dropna=False):
        frames.append(_missingness_for_frame(group_df[selected], group=group_value))
    return pd.concat(frames, ignore_index=True)


def find_duplicate_ids(df: pd.DataFrame, *, id_col: str = "patient_id") -> pd.DataFrame:
    """Return rows whose patient identifier appears more than once."""

    _require_columns(df, [id_col])
    duplicated = df[df[id_col].duplicated(keep=False)].copy()
    if duplicated.empty:
        return pd.DataFrame(columns=list(df.columns) + ["duplicate_count"])
    counts = df[id_col].value_counts(dropna=False)
    duplicated["duplicate_count"] = duplicated[id_col].map(counts)
    return duplicated.sort_values([id_col])


def summarize_categorical_levels(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    max_levels: int = 20,
    include_missing: bool = True,
) -> pd.DataFrame:
    """Summarize counts and percentages for categorical columns."""

    if max_levels <= 0:
        raise ValueError("max_levels must be positive.")
    if columns is None:
        selected = [
            col
            for col in df.columns
            if not pd.api.types.is_numeric_dtype(df[col]) or df[col].nunique(dropna=True) <= max_levels
        ]
    else:
        selected = _select_columns(df, columns)
    rows: list[dict[str, Any]] = []
    for col in selected:
        counts = df[col].value_counts(dropna=not include_missing).head(max_levels)
        denominator = len(df)
        for value, count in counts.items():
            rows.append(
                {
                    "column": col,
                    "level": "<missing>" if pd.isna(value) else value,
                    "n": int(count),
                    "percent": float(100 * count / denominator) if denominator else 0.0,
                }
            )
    return pd.DataFrame(rows)


def compare_train_test_balance(
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Compare simple train/test distributions for leakage and split sanity checks."""

    selected = _select_columns(train, columns)
    _require_columns(test, selected)
    rows: list[dict[str, Any]] = []
    for col in selected:
        if pd.api.types.is_numeric_dtype(train[col]) and pd.api.types.is_numeric_dtype(test[col]):
            train_mean = float(train[col].mean())
            test_mean = float(test[col].mean())
            rows.append(
                {
                    "column": col,
                    "type": "numeric",
                    "train_summary": train_mean,
                    "test_summary": test_mean,
                    "absolute_difference": abs(train_mean - test_mean),
                    "train_missing_percent": float(train[col].isna().mean() * 100),
                    "test_missing_percent": float(test[col].isna().mean() * 100),
                }
            )
        else:
            train_top = train[col].mode(dropna=True)
            test_top = test[col].mode(dropna=True)
            rows.append(
                {
                    "column": col,
                    "type": "categorical",
                    "train_summary": train_top.iloc[0] if not train_top.empty else None,
                    "test_summary": test_top.iloc[0] if not test_top.empty else None,
                    "absolute_difference": None,
                    "train_missing_percent": float(train[col].isna().mean() * 100),
                    "test_missing_percent": float(test[col].isna().mean() * 100),
                }
            )
    return pd.DataFrame(rows)


def detect_potential_leakage(
    columns: Sequence[str] | pd.DataFrame,
    *,
    outcome_keywords: Sequence[str] = ("event", "death", "survival", "outcome", "label", "target"),
    time_keywords: Sequence[str] = ("followup", "follow_up", "last", "end_date", "post", "after"),
) -> pd.DataFrame:
    """Flag column names that may encode outcomes, labels, or post-index information."""

    names = list(columns.columns) if isinstance(columns, pd.DataFrame) else list(columns)
    rows = []
    for name in names:
        lowered = str(name).lower()
        matched = [kw for kw in outcome_keywords if kw in lowered]
        matched.extend(kw for kw in time_keywords if kw in lowered)
        if matched:
            rows.append({"column": name, "matched_keywords": ", ".join(sorted(set(matched)))})
    return pd.DataFrame(rows)


def feature_matrix_report(
    X: pd.DataFrame,
    y: Sequence[Any] | pd.Series | None = None,
    *,
    rare_threshold: float = 0.01,
    leakage_keywords: Sequence[str] = ("event", "death", "survival", "outcome", "label", "target"),
) -> pd.DataFrame:
    """Summarize feature-matrix quality before modeling.

    Parameters
    ----------
    X
        Feature matrix with one column per candidate predictor.
    y
        Optional labels used only for target count metadata.
    rare_threshold
        Binary features with a minority-class frequency below this value are flagged.
    leakage_keywords
        Column-name fragments that suggest outcome or post-index leakage.

    Returns
    -------
    pandas.DataFrame
        One row per feature with dtype, missingness, uniqueness, constant, rare-binary,
        and leakage-name flags.
    """

    if rare_threshold < 0 or rare_threshold > 0.5:
        raise ValueError("rare_threshold must be between 0 and 0.5.")
    if not isinstance(X, pd.DataFrame):
        X = pd.DataFrame(X)
    target_n = len(y) if y is not None else None
    if y is not None and len(X) != len(y):
        raise ValueError("X and y must have the same length.")

    rows: list[dict[str, Any]] = []
    for col in X.columns:
        series = X[col]
        non_missing = series.dropna()
        unique_non_missing = int(non_missing.nunique(dropna=True))
        value_counts = non_missing.value_counts(normalize=True)
        is_binary_feature = unique_non_missing == 2
        minority_frequency = float(value_counts.min()) if is_binary_feature and not value_counts.empty else None
        lowered = str(col).lower()
        matched = [kw for kw in leakage_keywords if kw in lowered]
        rows.append(
            {
                "feature": col,
                "n_rows": int(len(X)),
                "target_n": target_n,
                "dtype": str(series.dtype),
                "missing": int(series.isna().sum()),
                "missing_percent": float(series.isna().mean() * 100) if len(series) else 0.0,
                "unique_non_missing": unique_non_missing,
                "is_numeric": bool(pd.api.types.is_numeric_dtype(series)),
                "is_constant": bool(unique_non_missing <= 1),
                "is_binary": bool(is_binary_feature),
                "minority_frequency": minority_frequency,
                "rare_binary": bool(is_binary_feature and minority_frequency is not None and minority_frequency < rare_threshold),
                "leakage_flag": bool(matched),
                "leakage_keywords": ", ".join(matched),
            }
        )
    return pd.DataFrame(rows)


def _missingness_for_frame(df: pd.DataFrame, *, group: Any) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in df.columns:
        missing = int(df[col].isna().sum())
        row = {
            "column": col,
            "n": int(n),
            "missing": missing,
            "missing_percent": float(100 * missing / n) if n else 0.0,
            "dtype": str(df[col].dtype),
        }
        if group is not None:
            row["group"] = group
        rows.append(row)
    return pd.DataFrame(rows)


def _select_columns(df: pd.DataFrame, columns: Sequence[str] | None) -> list[str]:
    selected = list(columns) if columns is not None else list(df.columns)
    _require_columns(df, selected)
    return selected


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
