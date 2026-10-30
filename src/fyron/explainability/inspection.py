"""Inspectable model explanation tables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd


def permutation_importance_table(
    estimator: Any,
    X: Any,
    y: Any,
    *,
    feature_names: Sequence[str] | None = None,
    n_repeats: int = 10,
    scoring: str | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Return sklearn permutation importance as a sorted DataFrame."""

    try:
        from sklearn.inspection import permutation_importance
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'fyron.explainability requires scikit-learn. Install with: uv add "fyron[ml]"'
        ) from exc

    result = permutation_importance(
        estimator,
        X,
        y,
        n_repeats=n_repeats,
        scoring=scoring,
        random_state=random_state,
    )
    names = _feature_names(X, feature_names)
    table = pd.DataFrame(
        {
            "feature": names,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    )
    return table.sort_values("importance_mean", ascending=False).reset_index(drop=True)


def partial_dependence_table(
    estimator: Any,
    X: Any,
    *,
    features: Sequence[int | str],
    feature_names: Sequence[str] | None = None,
    grid_resolution: int = 50,
) -> pd.DataFrame:
    """Return one-way partial dependence values in long tabular form."""

    try:
        from sklearn.inspection import partial_dependence
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'fyron.explainability requires scikit-learn. Install with: uv add "fyron[ml]"'
        ) from exc

    names = _feature_names(X, feature_names)
    rows = []
    for feature in features:
        feature_index = names.index(feature) if isinstance(feature, str) else int(feature)
        result = partial_dependence(
            estimator,
            X,
            [feature_index],
            grid_resolution=grid_resolution,
        )
        values = result["grid_values"][0] if "grid_values" in result else result["values"][0]
        averages = result["average"][0]
        for value, average in zip(values, averages):
            rows.append(
                {
                    "feature": names[feature_index],
                    "value": value,
                    "partial_dependence": float(average),
                }
            )
    return pd.DataFrame(rows)


def shap_values_table(
    estimator: Any,
    X: Any,
    *,
    feature_names: Sequence[str] | None = None,
    explainer: Any | None = None,
    background_data: Any | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Return SHAP values in long patient-feature form.

    SHAP is optional because it can be a heavy dependency. Install it with
    ``uv add "fyron[explainability]"``.
    """

    names = _feature_names(X, feature_names)
    X_eval = _limit_rows(X, max_rows)
    values = _compute_shap_values(estimator, X_eval, explainer=explainer, background_data=background_data)
    arr = _coerce_shap_array(values, n_features=len(names))
    if arr.ndim != 2:
        raise ValueError(f"SHAP values must resolve to a 2D array, got shape {arr.shape}.")
    if arr.shape[1] != len(names):
        raise ValueError(f"SHAP feature count {arr.shape[1]} does not match feature names {len(names)}.")
    if arr.shape[0] != len(X_eval):
        raise ValueError("SHAP row count must match the evaluated input rows.")

    rows = []
    feature_values = _to_feature_value_frame(X_eval, names)
    for row_index in range(arr.shape[0]):
        for feature_index, feature in enumerate(names):
            rows.append(
                {
                    "row_index": row_index,
                    "feature": feature,
                    "feature_value": feature_values.iat[row_index, feature_index],
                    "shap_value": float(arr[row_index, feature_index]),
                    "abs_shap_value": float(abs(arr[row_index, feature_index])),
                }
            )
    return pd.DataFrame(rows)


def shap_summary_table(
    estimator: Any,
    X: Any,
    *,
    feature_names: Sequence[str] | None = None,
    explainer: Any | None = None,
    background_data: Any | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Return mean absolute SHAP importance by feature."""

    long_table = shap_values_table(
        estimator,
        X,
        feature_names=feature_names,
        explainer=explainer,
        background_data=background_data,
        max_rows=max_rows,
    )
    summary = (
        long_table.groupby("feature", as_index=False)
        .agg(
            mean_abs_shap=("abs_shap_value", "mean"),
            mean_shap=("shap_value", "mean"),
            median_abs_shap=("abs_shap_value", "median"),
            n=("shap_value", "size"),
        )
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
    summary["rank"] = np.arange(1, len(summary) + 1)
    return summary


def explain_model_summary(
    *,
    importance: pd.DataFrame | None = None,
    shap_summary: pd.DataFrame | None = None,
    metrics: Mapping[str, Any] | pd.DataFrame | None = None,
    feature_qc: pd.DataFrame | None = None,
    notes: Mapping[str, str] | pd.DataFrame | None = None,
    feature_col: str = "feature",
) -> pd.DataFrame:
    """Create a reviewer-facing model explanation summary table.

    Parameters
    ----------
    importance
        Feature importance table, for example from ``permutation_importance_table``.
    shap_summary
        Feature-level SHAP summary table, for example from ``shap_summary_table``.
    metrics
        Optional model metrics as a dictionary or one-row DataFrame. Metrics are
        repeated on each feature row for convenient review/export.
    feature_qc
        Optional feature quality-control table, for example from
        ``fyron.preprocessing.feature_matrix_report``.
    notes
        Optional mapping or DataFrame with feature-specific reviewer notes.
    feature_col
        Column name containing feature names in feature-level inputs.

    Returns
    -------
    pandas.DataFrame
        One row per feature with available importance, SHAP, QC, metric, and
        note columns merged by feature name.
    """
    frames: list[pd.DataFrame] = []
    for frame, prefix in ((importance, "importance"), (shap_summary, "shap"), (feature_qc, "qc")):
        if frame is not None:
            frames.append(_prepare_feature_frame(frame, feature_col=feature_col, prefix=prefix))
    if not frames:
        raise ValueError("At least one of importance, shap_summary, or feature_qc must be provided.")

    summary = frames[0]
    for frame in frames[1:]:
        summary = summary.merge(frame, on=feature_col, how="outer")

    if notes is not None:
        summary = summary.merge(_prepare_notes(notes, feature_col=feature_col), on=feature_col, how="left")

    for key, value in _metric_row(metrics).items():
        summary[f"metric.{key}"] = value

    sort_col = _first_existing(
        summary,
        [
            "shap.mean_abs_shap",
            "importance.importance_mean",
            "importance.importance",
            "qc.leakage_flag",
        ],
    )
    if sort_col is not None:
        summary = summary.sort_values(sort_col, ascending=False, na_position="last")
    return summary.reset_index(drop=True)


def explain_patient_prediction(
    contributions: pd.DataFrame,
    *,
    row_index: Any | None = None,
    patient_id: Any | None = None,
    row_col: str = "row_index",
    patient_col: str = "patient_id",
    feature_col: str = "feature",
    contribution_col: str = "shap_value",
    feature_value_col: str = "feature_value",
    top_n: int = 5,
) -> pd.DataFrame:
    """Return the strongest positive and negative drivers for one prediction.

    Parameters
    ----------
    contributions
        Long contribution table with feature names and signed contributions,
        such as output from ``shap_values_table``.
    row_index
        Optional row identifier to select when ``row_col`` exists.
    patient_id
        Optional patient identifier to select when ``patient_col`` exists.
    row_col, patient_col, feature_col, contribution_col, feature_value_col
        Column names used to identify rows, features, contributions, and values.
    top_n
        Number of positive and negative drivers to return.

    Returns
    -------
    pandas.DataFrame
        Feature-level contribution rows sorted by direction and absolute impact.
    """
    if top_n <= 0:
        raise ValueError("top_n must be positive.")
    table = contributions.copy()
    _require_columns(table, [feature_col, contribution_col])
    if patient_id is not None:
        if patient_col not in table.columns:
            raise ValueError(f"patient_col {patient_col!r} is not present in contributions.")
        table = table[table[patient_col] == patient_id]
    elif row_index is not None:
        if row_col not in table.columns:
            raise ValueError(f"row_col {row_col!r} is not present in contributions.")
        table = table[table[row_col] == row_index]
    elif row_col in table.columns and table[row_col].nunique(dropna=False) > 1:
        raise ValueError("Multiple rows are present; provide row_index or patient_id.")
    if table.empty:
        raise ValueError("No contribution rows match the requested prediction.")

    table[contribution_col] = pd.to_numeric(table[contribution_col], errors="coerce")
    table = table.dropna(subset=[contribution_col]).copy()
    table["abs_contribution"] = table[contribution_col].abs()
    table["direction"] = np.where(table[contribution_col] >= 0, "positive", "negative")

    positives = table[table["direction"] == "positive"].nlargest(top_n, "abs_contribution")
    negatives = table[table["direction"] == "negative"].nlargest(top_n, "abs_contribution")
    out_cols = [col for col in [row_col, patient_col, feature_col, feature_value_col] if col in table.columns]
    out_cols.extend([contribution_col, "abs_contribution", "direction"])
    return pd.concat([positives, negatives], ignore_index=True)[out_cols]


def _compute_shap_values(
    estimator: Any,
    X: Any,
    *,
    explainer: Any | None,
    background_data: Any | None,
) -> Any:
    if explainer is None:
        try:
            import shap
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ImportError(
                'SHAP explainability requires shap. Install with: uv add "fyron[explainability]"'
            ) from exc
        explainer = shap.Explainer(estimator, background_data if background_data is not None else X)
    explanation = explainer(X)
    return getattr(explanation, "values", explanation)


def _prepare_feature_frame(frame: pd.DataFrame, *, feature_col: str, prefix: str) -> pd.DataFrame:
    table = frame.copy()
    if feature_col not in table.columns:
        raise ValueError(f"{prefix} table must include feature column {feature_col!r}.")
    renamed = {}
    for col in table.columns:
        if col != feature_col and not col.startswith(f"{prefix}."):
            renamed[col] = f"{prefix}.{col}"
    return table.rename(columns=renamed)


def _prepare_notes(notes: Mapping[str, str] | pd.DataFrame, *, feature_col: str) -> pd.DataFrame:
    if isinstance(notes, pd.DataFrame):
        table = notes.copy()
        if feature_col not in table.columns:
            raise ValueError(f"notes DataFrame must include feature column {feature_col!r}.")
        if "note" not in table.columns:
            non_feature = [col for col in table.columns if col != feature_col]
            if len(non_feature) != 1:
                raise ValueError("notes DataFrame must include a 'note' column or exactly one non-feature column.")
            table = table.rename(columns={non_feature[0]: "note"})
        return table[[feature_col, "note"]]
    return pd.DataFrame({feature_col: list(notes.keys()), "note": list(notes.values())})


def _metric_row(metrics: Mapping[str, Any] | pd.DataFrame | None) -> dict[str, Any]:
    if metrics is None:
        return {}
    if isinstance(metrics, pd.DataFrame):
        if metrics.empty:
            return {}
        row = metrics.iloc[0].to_dict()
    else:
        row = dict(metrics)
    return {str(key): value for key, value in row.items() if _is_scalar(value)}


def _first_existing(df: pd.DataFrame, columns: Sequence[str]) -> str | None:
    for col in columns:
        if col in df.columns:
            return col
    return None


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool, np.integer, np.floating, np.bool_))


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _coerce_shap_array(values: Any, *, n_features: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 3:
        if isinstance(values, (list, tuple)):
            # Legacy SHAP returns a list of (samples, features) arrays, one per output.
            arr = arr[-1, :, :]
        elif arr.shape[1] == n_features:
            arr = arr[:, :, -1]
        elif arr.shape[2] == n_features:
            arr = arr[-1, :, :]
        else:
            raise ValueError(f"Cannot resolve 3D SHAP values with shape {arr.shape}.")
    return arr


def _limit_rows(X: Any, max_rows: int | None) -> Any:
    if max_rows is None:
        return X
    if max_rows <= 0:
        raise ValueError("max_rows must be positive when provided.")
    if hasattr(X, "iloc"):
        return X.iloc[:max_rows]
    return np.asarray(X)[:max_rows]


def _to_feature_value_frame(X: Any, names: Sequence[str]) -> pd.DataFrame:
    if hasattr(X, "loc"):
        return pd.DataFrame(X.to_numpy(), columns=list(names))
    return pd.DataFrame(np.asarray(X), columns=list(names))


def _feature_names(X: Any, feature_names: Sequence[str] | None) -> list[str]:
    if feature_names is not None:
        return list(feature_names)
    if hasattr(X, "columns"):
        return [str(col) for col in X.columns]
    n_features = getattr(X, "shape", [None, 0])[1]
    return [f"feature_{index}" for index in range(n_features)]
