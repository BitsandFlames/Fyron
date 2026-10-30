"""Dependency-light contracts shared by survival preparation and evaluation."""

import numpy as np
import pandas as pd


def duration_column(series, *, name="duration", allow_zero=True, allow_infinite=False):
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{name} must be numeric, got {series.dtype}.")
    if series.isna().any():
        raise ValueError(f"{name} contains NaN; resolve missing outcomes before fitting.")
    if (series < 0).any() or (not allow_zero and (series == 0).any()):
        rule = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {rule}.")
    if not allow_infinite and not np.isfinite(series.to_numpy(dtype=float)).all():
        raise ValueError(f"{name} must be finite.")


def event_column(series, *, name="event"):
    if series.isna().any() or not series.isin([0, 1]).all():
        raise ValueError(f"{name} must be binary 0/1 without missing values.")
    return series.astype(int)


def positive_horizon(value, *, name="tau"):
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number.")


def positive_horizons(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not values.size or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("times must contain at least one finite positive horizon.")
    return values


def finite_scores(values, *, length=None):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or (length is not None and len(values) != length):
        raise ValueError("Scores must be one-dimensional and aligned with outcomes.")
    if not np.isfinite(values).all():
        raise ValueError("Scores must be finite without missing values.")
    return values


def outcome_arrays(duration, event, *, allow_zero=False):
    duration, event = np.asarray(duration), np.asarray(event)
    if duration.ndim != 1 or event.ndim != 1 or len(duration) != len(event):
        raise ValueError("duration and event must be aligned one-dimensional arrays of the same length.")
    duration = duration.astype(float)
    duration_column(pd.Series(duration), allow_zero=allow_zero)
    events = event_column(pd.Series(event)).to_numpy(dtype=bool)
    return duration, events


def concordance(duration, event, risk):
    duration, event = outcome_arrays(duration, event)
    risk = finite_scores(risk, length=len(duration))
    try:
        from sksurv.exceptions import NoComparablePairException
        from sksurv.metrics import concordance_index_censored
    except ImportError as exc:
        raise ImportError('Survival concordance requires scikit-survival. Install "fyron[survival-ml]".') from exc
    if len(duration) < 2 or not event.any():
        return float("nan")
    try:
        with np.errstate(invalid="ignore", divide="ignore"):
            return float(concordance_index_censored(event, duration, risk)[0])
    except NoComparablePairException:
        return float("nan")


def prepare_fitting_cohort(
    df, duration_col, event_col, covariates=None, *, formula=None,
    strata=None, allow_zero=True,
):
    """Select complete predictors while rejecting invalid outcomes before exclusion."""
    if not df.index.is_unique:
        raise IndexError("DataFrame index must be unique; use reset_index(drop=True).")
    strata_cols = [strata] if isinstance(strata, str) else list(strata or [])
    selected = list(covariates) if formula is None and covariates is not None else []
    required = list(dict.fromkeys([duration_col, event_col, *strata_cols, *selected]))
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")
    duration_column(df[duration_col], name=duration_col, allow_zero=allow_zero)
    events = event_column(df[event_col], name=event_col)
    work = df.copy()
    work[event_col] = events
    if formula is not None:
        from formulaic import model_matrix
        work = work.dropna(subset=strata_cols)
        matrix = model_matrix(formula, work, na_action="drop")
        if not np.isfinite(matrix.to_numpy(dtype=float)).all():
            raise ValueError("Formula predictors must be finite after transformation.")
        variables = set(matrix.model_spec.required_variables)
        columns = list(dict.fromkeys(required + [c for c in df.columns if c in variables]))
        work = work.loc[matrix.index, columns].copy()
    else:
        work = work.loc[:, required].dropna().copy()
    return work, len(df), len(work)
