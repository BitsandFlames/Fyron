"""Survival model output tables for reporting and validation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from fyron._survival_data import positive_horizons


def cox_forest_table(cox_result: Any, *, covariate_col: str = "covariate") -> pd.DataFrame:
    """Extract hazard ratios and confidence intervals for forest plots.

    Parameters
    ----------
    cox_result
        Output from ``fit_multivariate_cox`` / ``fit_univariate_cox``, a lifelines
        ``CoxPHFitter``, or a DataFrame with Cox summary columns.
    covariate_col
        Name for the covariate column in the returned table.

    Returns
    -------
    pandas.DataFrame
        Columns include covariate, hazard ratio, confidence interval, p-value,
        and a formatted label.
    """

    table = _coerce_cox_table(cox_result).copy()
    rename = {
        "exp(coef)": "hazard_ratio",
        "exp(coef) lower 95%": "ci_lower",
        "exp(coef) upper 95%": "ci_upper",
        "p": "p_value",
    }
    table = table.rename(columns=rename)
    if covariate_col not in table.columns:
        if "index" in table.columns:
            table = table.rename(columns={"index": covariate_col})
        elif table.index.name or not isinstance(table.index, pd.RangeIndex):
            table = table.reset_index().rename(columns={table.index.name or "index": covariate_col})
    required = [covariate_col, "hazard_ratio", "ci_lower", "ci_upper", "p_value"]
    missing = [col for col in required if col not in table.columns]
    if missing:
        raise ValueError(f"Cox table is missing columns: {missing}")
    out = table[required].copy()
    out["label"] = out.apply(
        lambda row: f"{row['hazard_ratio']:.2f} ({row['ci_lower']:.2f} to {row['ci_upper']:.2f})",
        axis=1,
    )
    return out


def survival_prediction_table(
    model: Any,
    df: pd.DataFrame,
    times: Sequence[float],
    *,
    id_col: str | None = None,
) -> pd.DataFrame:
    """Create fixed-time survival/risk predictions for supported survival models.

    Parameters
    ----------
    model
        Fitted model with ``predict_survival_function`` support.
    df
        Feature rows to score.
    times
        Positive time horizons.
    id_col
        Optional identifier column copied into the output.

    Returns
    -------
    pandas.DataFrame
        Long table with one row per input row and time horizon.
    """

    horizons = positive_horizons(times)
    features = df.drop(columns=[id_col]) if id_col else df
    ids = df[id_col].tolist() if id_col else list(range(len(df)))
    survival = _predict_survival(model, features, horizons)
    if survival.shape != (len(df), len(horizons)) or not np.isfinite(survival).all():
        raise ValueError("Model must return finite survival probabilities for every row and horizon.")
    if np.any((survival < 0) | (survival > 1)):
        raise ValueError("Survival probabilities must be in [0, 1].")
    rows = []
    for row_idx, row_id in enumerate(ids):
        for time_idx, horizon in enumerate(horizons):
            value = float(survival[row_idx, time_idx])
            rows.append(
                {
                    "row_id": row_id,
                    "time": float(horizon),
                    "survival_probability": value,
                    "event_risk": 1.0 - value,
                }
            )
    return pd.DataFrame(rows)


def _coerce_cox_table(cox_result: Any) -> pd.DataFrame:
    if isinstance(cox_result, pd.DataFrame):
        return cox_result
    if isinstance(cox_result, dict) and "results" in cox_result:
        return pd.DataFrame(cox_result["results"])
    summary = getattr(cox_result, "summary", None)
    if summary is not None:
        return pd.DataFrame(summary).reset_index()
    raise TypeError("cox_result must be a Cox result dict, lifelines fitter, or DataFrame.")


def _predict_survival(model: Any, features: pd.DataFrame, times: np.ndarray) -> np.ndarray:
    if hasattr(model, "predict_survival_function"):
        try:
            pred = model.predict_survival_function(features, times=np.unique(times))
        except TypeError:
            pred = model.predict_survival_function(features)
        if isinstance(pred, pd.DataFrame):
            pred = pred.sort_index()
            if np.any(times > pred.index.max()):
                raise ValueError("Requested times exceed the model's survival timeline.")
            frame = pred.reindex(times, method="ffill")
            frame.iloc[np.flatnonzero(times < pred.index.min())] = 1.0
            return frame.to_numpy(dtype=float).T
        values = []
        for fn in pred:
            values.append([float(fn(t)) for t in times])
        return np.asarray(values, dtype=float)
    raise TypeError("model must support predict_survival_function; risk scores are not survival probabilities.")
