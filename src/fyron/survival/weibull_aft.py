"""Weibull accelerated failure time (AFT) regression."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fyron._survival_data import prepare_fitting_cohort
from lifelines import WeibullAFTFitter


def _prepare_df(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    covariates: Sequence[str] | None,
) -> tuple[pd.DataFrame, int, int]:
    return prepare_fitting_cohort(df, duration_col, event_col, covariates,
                                  allow_zero=False)


def _aft_summary_table(fitter: WeibullAFTFitter) -> pd.DataFrame:
    summ = fitter.summary.reset_index()
    if "param" in summ.columns:
        summ["covariate"] = summ["param"].astype(str) + ":" + summ["covariate"].astype(str)
    elif "covariate" not in summ.columns:
        summ = summ.rename(columns={summ.columns[0]: "covariate"})
    summ = summ.rename(
        columns={
            "exp(coef)": "exp_coef",
            "exp(coef) lower 95%": "exp_ci_lower",
            "exp(coef) upper 95%": "exp_ci_upper",
            "p": "p_value",
        }
    )
    summ = summ.rename(
        columns={
            "coef lower 95%": "ci_lower",
            "coef upper 95%": "ci_upper",
        }
    )
    keep = [
        "covariate",
        "coef",
        "exp_coef",
        "ci_lower",
        "ci_upper",
        "exp_ci_lower",
        "exp_ci_upper",
        "p_value",
    ]
    return summ[[c for c in keep if c in summ.columns]]


def fit_weibull_aft(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    *,
    covariates: Sequence[str] | None = None,
    formula: str | None = None,
    robust: bool = False,
) -> dict[str, Any]:
    """Fit a Weibull AFT model with ``lifelines.WeibullAFTFitter``.

    Stratification is **not** supported by this helper (the lifelines AFT API differs from Cox).

    Parameters
    ----------
    df, duration_col, event_col
        Survival data.
    covariates
        List of column names joined into a formula.
    formula
        Patsy-like lifelines formula string.
    robust
        Passed through to ``fit`` when supported.

    Returns
    -------
    dict
        ``results`` — coefficient table; ``fitter``; ``AIC``; ``concordance_index`` (if available);
        ``n_excluded`` / ``n_used`` and ``training_df`` with the exact fitting
        rows and original index. Formula-specific missing predictors are excluded;
        unrelated missing columns do not affect the fitting cohort.

    Examples
    --------
    >>> from lifelines.datasets import load_rossi
    >>> from fyron.survival.weibull_aft import fit_weibull_aft
    >>> rossi = load_rossi()
    >>> out = fit_weibull_aft(rossi, "week", "arrest", covariates=["age", "prio"])
    >>> "coef" in out["results"].columns
    True
    """
    if formula is not None and covariates is not None:
        raise ValueError("Pass only one of ``formula`` or ``covariates``.")
    if formula is None and covariates is None:
        raise ValueError("One of ``formula`` or ``covariates`` is required.")

    work, n_before, n_after = prepare_fitting_cohort(
        df, duration_col, event_col, covariates, formula=formula,
        allow_zero=False,
    )
    fit_formula = formula if formula is not None else " + ".join(covariates)

    if n_after < 5:
        raise ValueError("Too few complete rows remain after dropping missing data.")

    aft = WeibullAFTFitter()
    aft.fit(
        work,
        duration_col=duration_col,
        event_col=event_col,
        formula=fit_formula,
        robust=robust,
        show_progress=False,
    )

    c_index = getattr(aft, "concordance_index_", float("nan"))
    aic = float(getattr(aft, "AIC_", float("nan")))

    return {
        "results": _aft_summary_table(aft),
        "fitter": aft,
        "n_excluded": int(n_before - n_after),
        "n_used": int(n_after),
        "AIC": aic,
        "concordance_index": float(c_index) if c_index == c_index else float("nan"),
        "formula_used": fit_formula,
        "training_df": work.copy(),
    }


def plot_aft_survival_curves(
    fitter: WeibullAFTFitter,
    covariates: str | Sequence[str],
    profiles: Sequence[Mapping[str, float]],
    *,
    plot_baseline: bool = True,
    figsize: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
    plot_kwargs: MutableMapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Plot predicted survival curves for covariate profiles (partial effects).

    Parameters
    ----------
    fitter
        Fitted ``WeibullAFTFitter``.
    covariates
        Names to vary (order must match each profile mapping).
    profiles
        Iterable of dicts mapping covariate name to numeric level.
    plot_baseline
        Include the baseline curve at central values.
    figsize
        Used when ``ax`` is not provided.
    ax
        Optional matplotlib axes.
    plot_kwargs
        Extra kwargs forwarded to ``plot_partial_effects_on_outcome``.

    Returns
    -------
    dict
        ``figure``, ``axes``, ``fitter``.

    Examples
    --------
    >>> from lifelines.datasets import load_rossi
    >>> from fyron.survival.weibull_aft import fit_weibull_aft, plot_aft_survival_curves
    >>> rossi = load_rossi()
    >>> m = fit_weibull_aft(rossi, "week", "arrest", covariates=["prio"])
    >>> out = plot_aft_survival_curves(
    ...     m["fitter"], "prio", [{"prio": 0}, {"prio": 10}], figsize=(6, 4)
    ... )
    >>> out["axes"] is not None
    True
    """
    names = [covariates] if isinstance(covariates, str) else list(covariates)
    if not profiles:
        raise ValueError("profiles must contain at least one mapping.")
    plot_kwargs = dict(plot_kwargs or {})

    values = np.array([[float(p[c]) for c in names] for p in profiles], dtype=float)

    created_fig = False
    if ax is None:
        figsize = figsize or (7.0, 4.5)
        fig, ax = plt.subplots(figsize=figsize)
        created_fig = True
    else:
        fig = ax.figure

    ax_out = fitter.plot_partial_effects_on_outcome(
        names,
        values,
        plot_baseline=plot_baseline,
        ax=ax,
        y="survival_function",
        **plot_kwargs,
    )
    if created_fig:
        fig.tight_layout()
    return {"figure": fig, "axes": ax_out, "fitter": fitter}
