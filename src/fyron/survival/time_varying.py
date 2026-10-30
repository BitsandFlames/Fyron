"""Time-varying and time-interaction Cox helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import numpy as np
import pandas as pd
from lifelines import CoxTimeVaryingFitter

from fyron.survival._validate import formula_complete_rows, require_columns, validate_duration_column, validate_event_column
from fyron.survival.cox import fit_multivariate_cox
from fyron.survival.ph_diagnostics import check_ph_assumptions
from fyron.survival.rmst import calculate_rmst
from fyron.survival.weibull_aft import fit_weibull_aft

TimeTransform = Literal["log", "identity", "sqrt"]


def _time_varying_summary_table(fitter: CoxTimeVaryingFitter) -> pd.DataFrame:
    table = fitter.summary.reset_index().rename(
        columns={
            "exp(coef)": "hazard_ratio",
            "exp(coef) lower 95%": "ci_lower",
            "exp(coef) upper 95%": "ci_upper",
            "p": "p_value",
        }
    )
    if "covariate" not in table.columns:
        table = table.rename(columns={table.columns[0]: "covariate"})
    keep = ["covariate", "hazard_ratio", "ci_lower", "ci_upper", "p_value"]
    return table[[col for col in keep if col in table.columns]]


def _fit_formula(covariates: Sequence[str] | None, formula: str | None) -> str:
    if formula is not None and covariates is not None:
        raise ValueError("Pass only one of ``formula`` or ``covariates``.")
    if formula is None and covariates is None:
        raise ValueError("One of ``formula`` or ``covariates`` is required.")
    if formula is not None:
        return formula
    names = list(covariates or [])
    if not names:
        raise ValueError("covariates must contain at least one column.")
    return " + ".join(names)


def _validate_start_stop(
    df: pd.DataFrame,
    *,
    start_col: str,
    stop_col: str,
    event_col: str,
) -> pd.DataFrame:
    require_columns(df, [start_col, stop_col, event_col])
    work = df.copy()
    for col in [start_col, stop_col]:
        if not pd.api.types.is_numeric_dtype(work[col]):
            raise TypeError(f"{col} must be numeric, got {work[col].dtype}.")
        if work[col].isna().any():
            raise ValueError(f"{col} contains NaN; drop or impute before fitting.")
        if work[col].isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"{col} must be finite.")
    if (work[start_col] < 0).any():
        raise ValueError(f"{start_col} must be non-negative.")
    if (work[stop_col] <= work[start_col]).any():
        raise ValueError(f"Every interval must satisfy {start_col} < {stop_col}.")
    work[event_col] = validate_event_column(work[event_col], name=event_col)
    return work


def fit_time_varying_cox(
    df: pd.DataFrame,
    event_col: str,
    *,
    start_col: str = "start",
    stop_col: str = "stop",
    id_col: str | None = None,
    covariates: Sequence[str] | None = None,
    formula: str | None = None,
    strata: str | Sequence[str] | None = None,
    robust: bool = False,
) -> dict[str, Any]:
    """Fit a Cox model for long-format start-stop survival data.

    Parameters
    ----------
    df
        Long-format survival data with one row per time interval.
    event_col
        Event indicator column, where 1 means the event occurred at interval end.
    start_col, stop_col
        Interval start and stop time columns. Every row must satisfy start < stop.
    id_col
        Optional subject identifier column used by lifelines.
    covariates
        Covariate column names joined into a formula.
    formula
        Lifelines formula string. Pass either this or ``covariates``.
    strata
        Optional strata passed to ``CoxTimeVaryingFitter.fit``.
    robust
        Whether to request robust variance estimates from lifelines.

    Returns
    -------
    dict
        ``results`` table, fitted ``fitter``, ``n_used``, ``formula_used``, and
        ``concordance_index`` when lifelines exposes it.
    """
    fit_formula = _fit_formula(covariates, formula)
    required = [event_col, start_col, stop_col]
    if id_col is not None:
        required.append(id_col)
    if covariates is not None:
        required.extend(covariates)
    if strata is not None:
        required.extend([strata] if isinstance(strata, str) else list(strata))
    require_columns(df, list(dict.fromkeys(required)))

    work = _validate_start_stop(df, start_col=start_col, stop_col=stop_col, event_col=event_col)
    subset_cols = list(dict.fromkeys(required))
    if formula is not None:
        work = formula_complete_rows(work.dropna(subset=subset_cols), fit_formula)
    else:
        work = work.loc[:, subset_cols].dropna().copy()
    if len(work) < 3:
        raise ValueError("Too few complete intervals remain after dropping missing data.")

    fitter = CoxTimeVaryingFitter()
    fitter.fit(
        work,
        event_col=event_col,
        start_col=start_col,
        stop_col=stop_col,
        id_col=id_col,
        formula=fit_formula,
        strata=strata,
        robust=robust,
        show_progress=False,
    )
    c_index = getattr(fitter, "concordance_index_", float("nan"))
    return {
        "results": _time_varying_summary_table(fitter),
        "fitter": fitter,
        "n_used": int(len(work)),
        "formula_used": fit_formula,
        "concordance_index": float(c_index) if c_index == c_index else float("nan"),
    }


def _time_transform(values: np.ndarray, transform: TimeTransform) -> np.ndarray:
    if transform == "log":
        return np.log(np.maximum(values, 1e-12))
    if transform == "identity":
        return values
    if transform == "sqrt":
        return np.sqrt(np.maximum(values, 0.0))
    raise ValueError("time_transform must be 'log', 'identity', or 'sqrt'.")


def _interval_stops(duration: float, breakpoints: Sequence[float]) -> list[float]:
    internal = [float(point) for point in breakpoints if 0.0 < float(point) < duration]
    return internal + [float(duration)]


def _make_breakpoints(
    durations: pd.Series,
    *,
    n_intervals: int,
    breakpoints: Sequence[float] | None,
) -> list[float]:
    if breakpoints is not None:
        points = sorted({float(point) for point in breakpoints})
        if any(not np.isfinite(point) or point <= 0 for point in points):
            raise ValueError("breakpoints must be positive follow-up times.")
        return points
    if n_intervals < 1:
        raise ValueError("n_intervals must be at least 1.")
    max_time = float(durations.max())
    if n_intervals == 1:
        return []
    return [float(x) for x in np.linspace(0.0, max_time, n_intervals + 1)[1:-1]]


def expand_time_interaction_dataframe(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    *,
    covariates: Sequence[str],
    time_interaction_covariates: Sequence[str],
    time_transform: TimeTransform = "log",
    n_intervals: int = 8,
    breakpoints: Sequence[float] | None = None,
    id_col: str | None = None,
    start_col: str = "start",
    stop_col: str = "stop",
) -> dict[str, Any]:
    """Expand data with piecewise-constant interactions at common interval ends."""
    covariate_names = list(covariates)
    interaction_names = list(time_interaction_covariates)
    if not covariate_names:
        raise ValueError("covariates must contain at least one column.")
    missing_interactions = [name for name in interaction_names if name not in covariate_names]
    if missing_interactions:
        raise ValueError("time_interaction_covariates must be included in covariates.")
    required = [duration_col, event_col, *covariate_names]
    if id_col is not None:
        required.append(id_col)
    require_columns(df, list(dict.fromkeys(required)))

    base = df.loc[:, list(dict.fromkeys(required))].dropna().copy()
    validate_duration_column(base[duration_col], name=duration_col)
    base[event_col] = validate_event_column(base[event_col], name=event_col)
    if (base[duration_col] <= 0).any():
        raise ValueError(f"{duration_col} must be positive for time-interaction expansion.")
    points = _make_breakpoints(base[duration_col], n_intervals=n_intervals, breakpoints=breakpoints)
    common_ends = np.array(sorted(set([*points, float(base[duration_col].max())])))

    id_name = id_col or "__fyron_id"
    rows: list[dict[str, Any]] = []
    for fallback_id, row in base.reset_index(drop=True).iterrows():
        start = 0.0
        duration = float(row[duration_col])
        for stop in _interval_stops(duration, points):
            out: dict[str, Any] = {
                id_name: row[id_col] if id_col is not None else int(fallback_id),
                start_col: start,
                stop_col: stop,
                event_col: int(row[event_col]) if stop == duration else 0,
            }
            for covariate in covariate_names:
                out[covariate] = row[covariate]
            common_end = common_ends[np.searchsorted(common_ends, stop, side="left")]
            transformed = float(_time_transform(np.array([common_end]), time_transform)[0])
            for covariate in interaction_names:
                out[f"{covariate}__x_{time_transform}_time"] = float(row[covariate]) * transformed
            rows.append(out)
            start = stop

    long_df = pd.DataFrame(rows)
    interaction_columns = [f"{name}__x_{time_transform}_time" for name in interaction_names]
    return {
        "data": long_df,
        "id_col": id_name,
        "start_col": start_col,
        "stop_col": stop_col,
        "event_col": event_col,
        "interaction_columns": interaction_columns,
        "breakpoints": points,
        "time_transform": time_transform,
        "n_input_rows": int(len(base)),
        "n_intervals": int(len(long_df)),
    }


def fit_cox_time_interactions(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    *,
    covariates: Sequence[str],
    time_interaction_covariates: Sequence[str] | None = None,
    time_transform: TimeTransform = "log",
    n_intervals: int = 8,
    breakpoints: Sequence[float] | None = None,
    id_col: str | None = None,
    strata: str | Sequence[str] | None = None,
    robust: bool = False,
) -> dict[str, Any]:
    """Fit a Cox model with generated covariate-by-time interaction terms."""
    interaction_covariates = list(time_interaction_covariates or covariates)
    expanded = expand_time_interaction_dataframe(
        df,
        duration_col,
        event_col,
        covariates=covariates,
        time_interaction_covariates=interaction_covariates,
        time_transform=time_transform,
        n_intervals=n_intervals,
        breakpoints=breakpoints,
        id_col=id_col,
    )
    if strata is not None:
        strata_cols = [strata] if isinstance(strata, str) else list(strata)
        require_columns(df, strata_cols)
        source_cols = list(dict.fromkeys([duration_col, event_col, *covariates, *([id_col] if id_col else [])]))
        source = df.dropna(subset=source_cols)
        for col in strata_cols:
            if id_col is None:
                lookup = source.reset_index(drop=True)[col]
            else:
                if source[id_col].duplicated().any():
                    raise ValueError("Baseline subject identifiers must be unique.")
                lookup = source.set_index(id_col)[col]
            expanded["data"][col] = expanded["data"][expanded["id_col"]].map(lookup)
    model_covariates = list(covariates) + list(expanded["interaction_columns"])
    out = fit_time_varying_cox(
        expanded["data"],
        event_col,
        start_col=expanded["start_col"],
        stop_col=expanded["stop_col"],
        id_col=expanded["id_col"],
        covariates=model_covariates,
        strata=strata,
        robust=robust,
    )
    out.update(
        {
            "expanded_data": expanded["data"],
            "interaction_columns": expanded["interaction_columns"],
            "time_transform": time_transform,
            "breakpoints": expanded["breakpoints"],
            "n_input_rows": expanded["n_input_rows"],
            "n_intervals": expanded["n_intervals"],
        }
    )
    return out


def _recommendations(violations: Sequence[str], *, ran_interactions: bool, ran_aft: bool, ran_rmst: bool) -> list[str]:
    if not violations:
        return ["No Schoenfeld-test PH violations were detected at the configured threshold."]
    recs = [
        "Do not present Cox PH hazard ratios as time-constant effects without addressing PH diagnostics.",
        "Inspect Kaplan-Meier curves and Schoenfeld residual plots for clinical plausibility.",
        "Consider stratified Cox for categorical variables with non-proportional baseline hazards.",
    ]
    if ran_interactions:
        recs.append("Review generated Cox time-interaction terms for evidence that effects vary over follow-up.")
    else:
        recs.append("Time-interaction Cox was skipped; provide direct covariate columns to fit it automatically.")
    if ran_rmst:
        recs.append("Use RMST as an absolute time-based sensitivity estimand at the prespecified tau.")
    if ran_aft:
        recs.append("Use Weibull AFT as a parametric time-ratio sensitivity model when clinically interpretable.")
    return recs


def run_survival_sensitivity_analysis(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    *,
    covariates: Sequence[str] | None = None,
    formula: str | None = None,
    group_col: str | None = None,
    rmst_tau: float | None = None,
    ph_p_value_threshold: float = 0.05,
    time_interaction_covariates: Sequence[str] | None = None,
    time_transform: TimeTransform = "log",
    n_intervals: int = 8,
    breakpoints: Sequence[float] | None = None,
    fit_time_interactions: bool = True,
    fit_aft: bool = True,
    fit_rmst: bool = True,
) -> dict[str, Any]:
    """Run Cox PH diagnostics and sensitivity models for PH concerns."""
    cox = fit_multivariate_cox(
        df,
        duration_col,
        event_col,
        covariates=covariates,
        formula=formula,
    )
    training_df = cox["training_df"]
    ph = check_ph_assumptions(training_df, cox["fitter"], p_value_threshold=ph_p_value_threshold, show_plots=False)
    violations = list(ph["violations"])

    selected_interactions = list(time_interaction_covariates or [])
    if not selected_interactions and covariates is not None:
        selected_interactions = [name for name in violations if name in set(covariates)]

    time_interaction = None
    if fit_time_interactions and covariates is not None and selected_interactions:
        time_interaction = fit_cox_time_interactions(
            df,
            duration_col,
            event_col,
            covariates=covariates,
            time_interaction_covariates=selected_interactions,
            time_transform=time_transform,
            n_intervals=n_intervals,
            breakpoints=breakpoints,
        )

    aft = None
    if fit_aft:
        aft = fit_weibull_aft(
            df,
            duration_col,
            event_col,
            covariates=covariates,
            formula=formula,
        )

    rmst = None
    if fit_rmst:
        rmst = calculate_rmst(df, duration_col, event_col, group_col=group_col, tau=rmst_tau)

    return {
        "cox": cox,
        "ph_diagnostics": ph,
        "violating_covariates": violations,
        "time_interaction_cox": time_interaction,
        "weibull_aft": aft,
        "rmst": rmst,
        "recommendations": _recommendations(
            violations,
            ran_interactions=time_interaction is not None,
            ran_aft=aft is not None,
            ran_rmst=rmst is not None,
        ),
    }
