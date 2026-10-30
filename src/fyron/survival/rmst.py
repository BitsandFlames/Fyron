"""Restricted mean survival time (RMST) helpers."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.utils import restricted_mean_survival_time
from scipy.stats import norm

from fyron.survival._validate import (
    require_columns,
    validate_duration_column,
    validate_event_column,
    validate_positive_tau,
)
from fyron.survival.groups import default_tau_from_observed_times

_Z_95 = float(norm.ppf(0.975))


def _rmst_variance(kmf: KaplanMeierFitter, tau: float) -> float:
    """Integrate KM covariance using Greenwood weights, as in survRM2::rmst1."""
    table = kmf.event_table.loc[kmf.event_table.index <= tau]
    times = table.index.to_numpy(dtype=float)
    survival = kmf.survival_function_.reindex(table.index).iloc[:, 0].to_numpy()
    # Each event contributes its squared remaining area, after the KM jump.
    areas = np.diff(np.append(times, tau)) * survival
    remaining_area = np.cumsum(areas[::-1])[::-1]
    risk = table["at_risk"].to_numpy(dtype=float)
    events = table["observed"].to_numpy(dtype=float)
    weights = np.zeros_like(risk)
    np.divide(events, risk * (risk - events), out=weights, where=risk > events)
    return float(np.sum(remaining_area**2 * weights))


def calculate_rmst(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    *,
    group_col: str | None = None,
    tau: float | None = None,
) -> pd.DataFrame:
    """Compute RMST at truncation ``tau`` using Kaplan–Meier integration.

    When ``tau`` is omitted, it defaults to the minimum of the largest observed
    follow-up times across groups (or overall maximum when ``group_col`` is None).

    Parameters
    ----------
    df
        Survival data.
    duration_col, event_col
        Time and event columns (1 = event, 0 = censored).
    group_col
        Optional categorical column; one RMST row per level plus ``n`` counts.
    tau
        Upper integration limit. Must be finite and positive. Beyond observed
        follow-up, the final KM survival level is continued unchanged.

    Returns
    -------
    pandas.DataFrame
        Columns: ``group``, ``n``, ``rmst``, ``rmst_se``, ``rmst_lower``, ``rmst_upper``, ``tau``.
        Standard errors use the Greenwood-based variance of the RMST estimator.
        Normal-based 95% intervals use the 0.975 standard normal quantile.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.survival.rmst import calculate_rmst
    >>> df = pd.DataFrame({"t": [1, 2, 4, 5], "e": [1, 1, 0, 1]})
    >>> out = calculate_rmst(df, "t", "e", tau=3.0)
    >>> "rmst" in out.columns
    True
    """
    require_columns(df, [duration_col, event_col])
    work = df[[duration_col, event_col]].copy()
    validate_duration_column(work[duration_col], name=duration_col)
    work[event_col] = validate_event_column(work[event_col], name=event_col)

    if group_col is not None:
        require_columns(df, [group_col])
        mask = df[group_col].notna()
        work = work.loc[mask].copy()
        work[group_col] = df.loc[mask, group_col].astype(str)

    if tau is None:
        tau_val = default_tau_from_observed_times(df, duration_col, group_col)
    else:
        tau_val = float(tau)
    validate_positive_tau(tau_val, name="tau")
    if not np.isfinite(tau_val):
        raise ValueError(f"tau must be a finite positive number; got {tau_val!r}.")

    rows: list[dict[str, Any]] = []
    if group_col is None:
        kmf = KaplanMeierFitter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            kmf.fit(work[duration_col], work[event_col])
        rmst = restricted_mean_survival_time(kmf, t=tau_val)
        se = float(np.sqrt(_rmst_variance(kmf, tau_val)))
        rows.append(
            _row("__all__", int(len(work)), float(rmst), se, tau_val),
        )
    else:
        for g, part in work.groupby(group_col, sort=True):
            kmf = KaplanMeierFitter()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                kmf.fit(part[duration_col], part[event_col])
            rmst = restricted_mean_survival_time(kmf, t=tau_val)
            se = float(np.sqrt(_rmst_variance(kmf, tau_val)))
            rows.append(_row(str(g), int(len(part)), float(rmst), se, tau_val))
    return pd.DataFrame(rows)


def _row(group: str, n: int, rmst: float, se: float, tau: float) -> dict[str, Any]:
    z = _Z_95
    lower = rmst - z * se if se == se else float("nan")
    upper = rmst + z * se if se == se else float("nan")
    return {
        "group": group,
        "n": n,
        "rmst": rmst,
        "rmst_se": se,
        "rmst_lower": lower,
        "rmst_upper": upper,
        "tau": tau,
    }


def compare_rmst(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    group_col: str,
    reference: str,
    *,
    tau: float | None = None,
) -> pd.DataFrame:
    """Pairwise RMST differences versus a reference group.

    Uses independent Greenwood-based RMST variance estimates and a normal
    approximation for the difference (adequate for moderate sample sizes).
    When the difference has zero standard error, its interval is a point and
    its p-value is NaN because the normal test statistic is undefined.

    Parameters
    ----------
    df, duration_col, event_col, group_col
        Same conventions as :func:`calculate_rmst`.
    reference
        Reference level of ``group_col`` (string-coerced).
    tau
        Truncation time; defaults like :func:`calculate_rmst`.

    Returns
    -------
    pandas.DataFrame
        Columns include ``group``, ``reference``, ``rmst_group``, ``rmst_reference``,
        ``difference``, ``diff_lower``, ``diff_upper``, ``p_value``, ``tau``.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.survival.rmst import compare_rmst
    >>> df = pd.DataFrame({
    ...     "t": [1, 2, 3, 4, 5, 6],
    ...     "e": [1, 1, 0, 1, 1, 0],
    ...     "g": ["A", "A", "A", "B", "B", "B"],
    ... })
    >>> tab = compare_rmst(df, "t", "e", "g", reference="A", tau=4.0)
    >>> set(["difference", "p_value"]).issubset(tab.columns)
    True
    """
    require_columns(df, [duration_col, event_col, group_col])
    base = calculate_rmst(df, duration_col, event_col, group_col=group_col, tau=tau)
    ref = str(reference)
    ref_rows = base.loc[base["group"].astype(str) == ref]
    if ref_rows.empty:
        raise ValueError(f"Reference group {ref!r} not found in data.")
    ref_rmst = float(ref_rows.iloc[0]["rmst"])
    ref_se = float(ref_rows.iloc[0]["rmst_se"])
    tau_val = float(ref_rows.iloc[0]["tau"])

    out_rows: list[dict[str, Any]] = []
    for _, row in base.iterrows():
        g = str(row["group"])
        if g == ref:
            continue
        rg = float(row["rmst"])
        se_g = float(row["rmst_se"])
        diff = rg - ref_rmst
        if not (se_g == se_g and ref_se == ref_se):
            p_val = float("nan")
            lo = hi = float("nan")
        else:
            se_diff = float(np.sqrt(se_g**2 + ref_se**2))
            if se_diff == 0.0:
                p_val = float("nan")
            else:
                zstat = diff / se_diff
                p_val = float(2 * norm.sf(abs(zstat)))
            lo = diff - _Z_95 * se_diff if se_diff == se_diff else float("nan")
            hi = diff + _Z_95 * se_diff if se_diff == se_diff else float("nan")
        out_rows.append(
            {
                "group": g,
                "reference": ref,
                "rmst_group": rg,
                "rmst_reference": ref_rmst,
                "difference": diff,
                "diff_lower": lo,
                "diff_upper": hi,
                "p_value": p_val,
                "tau": tau_val,
            }
        )
    if not out_rows:
        raise ValueError("No non-reference groups available for comparison.")
    return pd.DataFrame(out_rows)
