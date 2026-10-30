"""Cox proportional hazards regression helpers."""

from __future__ import annotations

from typing import Any, Sequence

import pandas as pd
from fyron._survival_data import prepare_fitting_cohort
from lifelines import CoxPHFitter


def _prepare_df(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    covariates: Sequence[str] | None,
    strata: str | Sequence[str] | None = None,
) -> tuple[pd.DataFrame, int, int]:
    return prepare_fitting_cohort(df, duration_col, event_col, covariates,
                                  strata=strata, allow_zero=True)


def _fit_cox_table(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    *,
    formula: str | None,
    covariates: Sequence[str] | None,
    strata: str | Sequence[str] | None,
    robust: bool,
) -> dict[str, Any]:
    if formula is not None and covariates is not None:
        raise ValueError("Pass only one of ``formula`` or ``covariates``.")
    if formula is None and covariates is None:
        raise ValueError("One of ``formula`` or ``covariates`` is required.")

    work, n_before, n_after = prepare_fitting_cohort(
        df, duration_col, event_col, covariates, formula=formula,
        strata=strata, allow_zero=True,
    )
    fit_formula = formula if formula is not None else " + ".join(covariates)
    drop_covariates = None if formula is not None else list(covariates)

    if n_after < 3:
        raise ValueError("Too few complete rows remain after dropping missing data.")

    cph = CoxPHFitter()
    cph.fit(
        work,
        duration_col=duration_col,
        event_col=event_col,
        formula=fit_formula,
        strata=strata,
        robust=robust,
        show_progress=False,
    )

    table = cph.summary.reset_index().rename(
        columns={
            "exp(coef)": "hazard_ratio",
            "exp(coef) lower 95%": "ci_lower",
            "exp(coef) upper 95%": "ci_upper",
            "p": "p_value",
        }
    )
    keep = ["covariate", "hazard_ratio", "ci_lower", "ci_upper", "p_value"]
    table = table[[c for c in keep if c in table.columns]]

    return {
        "results": table,
        "fitter": cph,
        "n_excluded": int(n_before - n_after),
        "n_used": int(n_after),
        "concordance_index": float(cph.concordance_index_),
        "formula_used": fit_formula,
        "dropped_covariates": drop_covariates,
        "training_df": work.copy(),
    }


def fit_univariate_cox(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    covariates: str | Sequence[str],
    *,
    strata: str | Sequence[str] | None = None,
    robust: bool = False,
) -> dict[str, Any]:
    """Fit separate univariate Cox models for one or more covariates.

    Parameters
    ----------
    df
        Survival dataset.
    duration_col, event_col
        Follow-up time and event indicator (1 = event).
    covariates
        Column name(s) modeled one at a time (each produces its own fit).
    strata
        Passed through to ``lifelines.CoxPHFitter.fit``.
    robust
        If True, use robust sandwich errors (cluster-robust when combined with ``cluster_col`` in lifelines).

    Returns
    -------
    dict
        ``results`` — stacked summary table with ``model`` identifying the covariate used;
        ``fitters`` — list of fitted ``CoxPHFitter`` objects in the same order;
        ``n_excluded`` / ``n_used`` per fit (included as columns ``n_excluded``, ``n_used`` on each slice).

    Examples
    --------
    >>> from lifelines.datasets import load_rossi
    >>> from fyron.survival.cox import fit_univariate_cox
    >>> rossi = load_rossi()
    >>> out = fit_univariate_cox(rossi, "week", "arrest", ["age", "prio"])
    >>> set(["covariate", "hazard_ratio", "p_value"]).issubset(out["results"].columns)
    True
    """
    names = [covariates] if isinstance(covariates, str) else list(covariates)
    if not names:
        raise ValueError("covariates must be a non-empty string or sequence.")

    tables: list[pd.DataFrame] = []
    fitters: list[CoxPHFitter] = []
    for name in names:
        chunk = _fit_cox_table(
            df,
            duration_col,
            event_col,
            formula=None,
            covariates=[name],
            strata=strata,
            robust=robust,
        )
        res = chunk["results"].copy()
        res.insert(0, "model", name)
        res["n_excluded"] = chunk["n_excluded"]
        res["n_used"] = chunk["n_used"]
        res["concordance_index"] = chunk["concordance_index"]
        tables.append(res)
        fitters.append(chunk["fitter"])

    stacked = pd.concat(tables, ignore_index=True)
    return {
        "results": stacked,
        "fitters": fitters,
    }


def fit_multivariate_cox(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    *,
    covariates: Sequence[str] | None = None,
    formula: str | None = None,
    strata: str | Sequence[str] | None = None,
    robust: bool = False,
) -> dict[str, Any]:
    """Fit a multivariate Cox model.

    Exactly one of ``covariates`` or ``formula`` must be supplied.
    The returned ``training_df`` preserves the fitting cohort and original index
    for row-aligned residual and proportional-hazards diagnostics.

    Examples
    --------
    >>> from lifelines.datasets import load_rossi
    >>> from fyron.survival.cox import fit_multivariate_cox
    >>> rossi = load_rossi()
    >>> out = fit_multivariate_cox(rossi, "week", "arrest", covariates=["age", "prio"])
    >>> len(out["results"]) >= 2
    True
    """
    out = _fit_cox_table(
        df,
        duration_col,
        event_col,
        formula=formula,
        covariates=covariates,
        strata=strata,
        robust=robust,
    )
    return {
        "results": out["results"],
        "fitter": out["fitter"],
        "n_excluded": out["n_excluded"],
        "n_used": out["n_used"],
        "concordance_index": out["concordance_index"],
        "formula_used": out["formula_used"],
        "training_df": out["training_df"],
    }
