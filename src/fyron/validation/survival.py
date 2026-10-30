"""Survival model validation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from fyron._survival_data import (
    concordance,
    finite_scores,
    outcome_arrays,
    positive_horizon,
    positive_horizons,
)


def bootstrap_concordance_index(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    risk_col: str,
    *,
    n_rounds: int = 1000,
    random_state: int = 42,
) -> dict[str, Any]:
    """Bootstrap Harrell-style concordance index for risk scores."""

    _require_columns(df, [duration_col, event_col, risk_col])
    if n_rounds <= 0:
        raise ValueError("n_rounds must be positive.")
    work = _survival_frame(df, duration_col, event_col, risk_col)
    rng = np.random.default_rng(random_state)
    values = []
    for _ in range(n_rounds):
        idx = rng.integers(0, len(work), len(work))
        sampled = work.iloc[idx]
        values.append(_concordance_index(sampled[duration_col], sampled[event_col], sampled[risk_col]))
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if not len(arr):
        raise ValueError("No bootstrap samples contain comparable survival pairs.")
    return {
        "n": int(len(work)),
        "metric": "concordance_index",
        "estimate": float(_concordance_index(work[duration_col], work[event_col], work[risk_col])),
        "bootstrap_mean": float(np.nanmean(arr)),
        "ci_lower": float(np.nanpercentile(arr, 2.5)),
        "ci_upper": float(np.nanpercentile(arr, 97.5)),
        "n_rounds": int(n_rounds),
        "valid_rounds": int(len(arr)),
        "dropped_rounds": int(n_rounds - len(arr)),
    }


def survival_calibration_at_time(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    prediction_col: str,
    time_horizon: float,
    *,
    n_bins: int = 5,
    censoring_df: pd.DataFrame | None = None,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Compare event risks with KM estimates and an IPCW Brier score.

    ``censoring_df`` optionally supplies the censoring-reference cohort, using
    the same outcome column names. By default the evaluation cohort is used.
    Requires ``fyron[survival-ml]`` and independent censoring. Horizons must be
    supported by the evaluation/reference cohorts and every calibration bin.
    """

    _require_columns(df, [duration_col, event_col, prediction_col])
    positive_horizon(time_horizon, name="time_horizon")
    if n_bins <= 0:
        raise ValueError("n_bins must be positive.")
    work = _survival_frame(df, duration_col, event_col, prediction_col)
    if not work[prediction_col].between(0, 1).all():
        raise ValueError("Predicted event risks must be in [0, 1].")
    brier = _ipcw_brier(work, duration_col, event_col, prediction_col, time_horizon, censoring_df)
    observed = _km_event_risk(work, duration_col, event_col, time_horizon)
    work["_bin"] = pd.qcut(work[prediction_col], q=min(n_bins, work[prediction_col].nunique()), duplicates="drop")
    table = (
        work.groupby("_bin", observed=False)
        .agg(
            n=(event_col, "size"),
            predicted=(prediction_col, "mean"),
            prediction_min=(prediction_col, "min"),
            prediction_max=(prediction_col, "max"),
        )
        .reset_index()
        .rename(columns={"_bin": "bin"})
    )
    table["observed"] = [
        _km_event_risk(part, duration_col, event_col, time_horizon)
        for _, part in work.groupby("_bin", observed=False)
    ]
    table = table[["bin", "n", "observed", "predicted", "prediction_min", "prediction_max"]]
    summary = {
        "n": float(len(work)),
        "time_horizon": float(time_horizon),
        "observed_event_rate": observed,
        "mean_predicted_risk": float(work[prediction_col].mean()),
        "calibration_in_the_large": float(work[prediction_col].mean() - observed),
        "brier_score": brier,
    }
    return summary, table


def brier_score_at_time(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    prediction_col: str,
    time_horizon: float,
    *,
    censoring_df: pd.DataFrame | None = None,
) -> dict[str, float]:
    """Return IPCW Brier score; censoring defaults to the evaluation cohort."""

    summary, _ = survival_calibration_at_time(
        df,
        duration_col,
        event_col,
        prediction_col,
        time_horizon,
        n_bins=1,
        censoring_df=censoring_df,
    )
    return {
        "n": summary["n"],
        "time_horizon": summary["time_horizon"],
        "brier_score": summary["brier_score"],
    }


def external_survival_validation(
    train_summary_or_model: Any,
    external_df: pd.DataFrame,
    *,
    duration_col: str,
    event_col: str,
    risk_col: str,
    prediction_col: str | None = None,
    time_horizon: float | None = None,
    censoring_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Evaluate a locked survival score or prediction column in an external cohort."""

    _require_columns(external_df, [duration_col, event_col, risk_col] + ([prediction_col] if prediction_col else []))
    work = _survival_frame(external_df, duration_col, event_col, risk_col)
    result: dict[str, Any] = {
        "n": int(len(work)),
        "concordance_index": float(_concordance_index(work[duration_col], work[event_col], work[risk_col])),
        "source": type(train_summary_or_model).__name__,
    }
    if prediction_col and time_horizon is not None:
        calibration, table = survival_calibration_at_time(
            external_df,
            duration_col,
            event_col,
            prediction_col,
            time_horizon,
            censoring_df=censoring_df,
        )
        result["calibration"] = calibration
        result["calibration_table"] = table
    return result


def time_dependent_auc_table(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    *,
    duration_col: str,
    event_col: str,
    risk_col: str,
    times: Sequence[float],
) -> pd.DataFrame:
    """Compute cumulative/dynamic AUC at fixed time horizons.

    Parameters
    ----------
    train_df
        Training cohort used to estimate the censoring distribution.
    test_df
        Validation cohort with risk scores.
    duration_col, event_col
        Survival time and event indicator columns.
    risk_col
        Higher values should indicate higher event risk.
    times
        Positive time horizons for dynamic AUC.

    Returns
    -------
    pandas.DataFrame
        AUC by time plus the mean AUC returned by scikit-survival.
    """

    try:
        from sksurv.metrics import cumulative_dynamic_auc
        from sksurv.util import Surv
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "time_dependent_auc_table requires scikit-survival. "
            'Install with: uv add "fyron[survival-ml]"'
        ) from exc

    _require_columns(train_df, [duration_col, event_col])
    _require_columns(test_df, [duration_col, event_col, risk_col])
    horizons = positive_horizons(times)
    train = _outcome_frame(train_df, duration_col, event_col)
    test = _survival_frame(test_df, duration_col, event_col, risk_col)
    if train.empty or test.empty:
        raise ValueError("train_df and test_df must contain complete survival rows.")
    y_train = Surv.from_arrays(event=train[event_col].astype(bool), time=train[duration_col].astype(float))
    y_test = Surv.from_arrays(event=test[event_col].astype(bool), time=test[duration_col].astype(float))
    unique_times, inverse = np.unique(horizons, return_inverse=True)
    auc, mean_auc = cumulative_dynamic_auc(y_train, y_test, test[risk_col].astype(float).to_numpy(), unique_times)
    return pd.DataFrame(
        {
            "time": horizons,
            "auc": np.asarray(auc, dtype=float)[inverse],
            "mean_auc": float(mean_auc),
            "n_train": int(len(train)),
            "n_test": int(len(test)),
        }
    )


def _survival_frame(df: pd.DataFrame, duration_col: str, event_col: str, score_col: str) -> pd.DataFrame:
    work = _outcome_frame(df, duration_col, event_col)
    work[score_col] = pd.to_numeric(df[score_col], errors="raise")
    finite_scores(work[score_col].to_numpy(dtype=float, na_value=np.nan), length=len(work))
    return work


def _outcome_frame(df: pd.DataFrame, duration_col: str, event_col: str) -> pd.DataFrame:
    _require_columns(df, [duration_col, event_col])
    work = df[[duration_col, event_col]].copy()
    for col in work:
        work[col] = pd.to_numeric(work[col], errors="raise")
    if work.empty:
        raise ValueError("No complete survival validation rows available.")
    outcome_arrays(work[duration_col], work[event_col])
    return work


def _concordance_index(duration: Sequence[Any], event: Sequence[Any], risk: Sequence[Any]) -> float:
    return concordance(duration, event, risk)


def _require_sksurv() -> None:
    try:
        import sksurv  # noqa: F401
    except ImportError as exc:
        raise ImportError('Survival validation requires scikit-survival. Install "fyron[survival-ml]".') from exc


def _km_event_risk(work: pd.DataFrame, duration_col: str, event_col: str, horizon: float) -> float:
    _require_sksurv()
    from sksurv.nonparametric import kaplan_meier_estimator

    if work.empty:
        return float("nan")
    times, survival = kaplan_meier_estimator(work[event_col].to_numpy(dtype=bool), work[duration_col].to_numpy())
    if horizon > times[-1] and survival[-1] > 0:
        raise ValueError("Calibration horizon exceeds observed follow-up in a calibration group.")
    index = np.searchsorted(times, horizon, side="right") - 1
    return float(1 - survival[index]) if index >= 0 else 0.0


def _ipcw_brier(
    work: pd.DataFrame,
    duration_col: str,
    event_col: str,
    prediction_col: str,
    horizon: float,
    censoring_df: pd.DataFrame | None,
) -> float:
    _require_sksurv()
    from sksurv.metrics import brier_score
    from sksurv.nonparametric import CensoringDistributionEstimator
    from sksurv.util import Surv

    reference = work if censoring_df is None else _outcome_frame(censoring_df, duration_col, event_col)
    y_ref = Surv.from_arrays(reference[event_col].astype(bool), reference[duration_col])
    y_eval = Surv.from_arrays(work[event_col].astype(bool), work[duration_col])
    if horizon > reference[duration_col].max():
        raise ValueError("Horizon exceeds censoring-reference follow-up.")
    censor = CensoringDistributionEstimator().fit(y_ref)
    event_times = work.loc[(work[event_col] == 1) & (work[duration_col] <= horizon), duration_col]
    needed = np.append(event_times.to_numpy(), horizon)
    weights = censor.predict_proba(needed)
    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError("Censoring probabilities must be positive at required times.")
    _, scores = brier_score(y_ref, y_eval, (1 - work[prediction_col].to_numpy())[:, None], [horizon])
    return float(scores[0])


def _require_columns(df: pd.DataFrame, columns: Sequence[str | None]) -> None:
    missing = [col for col in columns if col and col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
