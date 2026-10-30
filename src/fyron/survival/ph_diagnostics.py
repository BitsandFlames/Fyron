"""Proportional hazards diagnostics for Cox models."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pandas as pd
from lifelines import CoxPHFitter
from lifelines.statistics import proportional_hazard_test

from fyron.statistics import p_value_correction_table
from fyron.survival._validate import assert_unique_index, require_columns

PlotReturn = tuple[Any, Any]


def check_ph_assumptions(
    training_df: pd.DataFrame,
    fitter: CoxPHFitter,
    *,
    p_value_threshold: float = 0.05,
    show_plots: bool = False,
    columns: Sequence[str] | None = None,
    advice: bool = False,
    p_adjust: str | None = "fdr_bh",
    include_residuals: bool = False,
) -> dict[str, Any]:
    """Schoenfeld-based proportional hazards diagnostics.

    Wraps ``lifelines.statistics.proportional_hazard_test`` for a tabular summary and
    optionally delegates plotting to ``CoxPHFitter.check_assumptions``.

    Parameters
    ----------
    training_df
        The same (or row-aligned) dataframe used in ``fitter.fit``.
    fitter
        A fitted ``CoxPHFitter``.
    p_value_threshold
        Flag covariates whose minimum adjusted p-value across time transforms
        falls below this level (raw p-values when adjustment is disabled).
    p_adjust
        Multiple-testing correction for the test table and violation flags.
        Lifelines' optional diagnostic plots/advice use its raw-test convention.
    show_plots
        If True, scaled Schoenfeld residual plots are produced (can be slow).
    columns
        Optional subset of covariates to summarize.
    advice
        Forwarded to lifelines ``check_assumptions`` when ``show_plots`` is True (verbose console advice).

    Returns
    -------
    dict
        ``summary`` — long-form test table; ``violations`` — covariates failing the threshold;
        ``warnings`` / ``suggestions`` — narrative guidance.

    Examples
    --------
    >>> from lifelines.datasets import load_rossi
    >>> from lifelines import CoxPHFitter
    >>> from fyron.survival.ph_diagnostics import check_ph_assumptions
    >>> rossi = load_rossi()
    >>> cph = CoxPHFitter().fit(rossi, "week", "arrest", formula="age + prio", show_progress=False)
    >>> out = check_ph_assumptions(rossi, cph, show_plots=False)
    >>> "summary" in out and "violations" in out
    True
    """
    require_columns(training_df, [fitter.duration_col, fitter.event_col])
    assert_unique_index(training_df)

    summary = schoenfeld_test_table(
        fitter,
        training_df,
        method=["rank", "km"],
        p_adjust=p_adjust,
        alpha=p_value_threshold,
    )

    covariates = list(columns) if columns is not None else sorted(summary["covariate"].unique())
    violations: list[str] = []
    for cov in covariates:
        p_column = "p_adjusted" if p_adjust not in (None, "none") else "p_value"
        sub = summary.loc[summary["covariate"] == cov, p_column]
        if sub.empty:
            continue
        if float(sub.min()) < p_value_threshold:
            violations.append(str(cov))

    warnings_list: list[str] = []
    suggestions: list[str] = [
        "Consider stratification for categorical variables with few levels.",
        "Explore time-varying covariates or interactions with functions of time if effects evolve.",
        "Parametric AFT models (e.g., Weibull AFT) do not rely on the PH assumption for interpretation.",
    ]
    if violations:
        warnings_list.append(
            "Covariates with potential PH violations (low p-values on Schoenfeld tests): "
            + ", ".join(violations)
        )

    plot_axes: list[Any] = []
    if show_plots:
        plot_axes = fitter.check_assumptions(
            training_df,
            p_value_threshold=p_value_threshold,
            show_plots=True,
            advice=advice,
        )

    return {
        "summary": summary,
        "violations": violations,
        "warnings": warnings_list,
        "suggestions": suggestions,
        "plot_axes": plot_axes,
        "p_value_threshold": p_value_threshold,
        "residuals": schoenfeld_residuals_table(fitter, training_df) if include_residuals else None,
    }


def schoenfeld_residuals_table(
    fitter: CoxPHFitter,
    training_df: pd.DataFrame,
    *,
    scaled: bool = True,
) -> pd.DataFrame:
    """Return Schoenfeld residuals in long tabular form.

    Parameters
    ----------
    fitter
        Fitted lifelines ``CoxPHFitter``.
    training_df
        Row-aligned DataFrame used for fitting.
    scaled
        If True, use scaled Schoenfeld residuals; otherwise raw residuals.

    Returns
    -------
    pandas.DataFrame
        Long table with event row index, covariate, residual, and event time.
    """
    require_columns(training_df, [fitter.duration_col, fitter.event_col])
    kind = "scaled_schoenfeld" if scaled else "schoenfeld"
    residuals = fitter.compute_residuals(training_df, kind=kind)
    rows = []
    for row_index, row in residuals.iterrows():
        event_time = training_df.loc[row_index, fitter.duration_col] if row_index in training_df.index else pd.NA
        for covariate, value in row.items():
            rows.append(
                {
                    "row_index": row_index,
                    "time": event_time,
                    "covariate": covariate,
                    "residual": value,
                    "scaled": bool(scaled),
                }
            )
    return pd.DataFrame(rows)


def schoenfeld_test_table(
    fitter: CoxPHFitter,
    training_df: pd.DataFrame,
    *,
    method: str | Sequence[str] = "rank",
    p_adjust: str | None = "fdr_bh",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Run Schoenfeld proportional-hazards tests and return a clean table."""
    require_columns(training_df, [fitter.duration_col, fitter.event_col])
    assert_unique_index(training_df)
    test = proportional_hazard_test(fitter, training_df, time_transform=method)
    summary = test.summary.reset_index()
    if "covariate" not in summary.columns:
        if "level_0" in summary.columns and "level_1" in summary.columns:
            summary = summary.rename(columns={"level_0": "covariate", "level_1": "time_transform"})
        else:
            summary = summary.rename(columns={summary.columns[0]: "covariate"})
    summary = summary.rename(columns={"test_statistic": "statistic", "p": "p_value"})
    if "time_transform" not in summary.columns:
        summary["time_transform"] = method if isinstance(method, str) else ",".join(method)
    keep = [col for col in ["covariate", "time_transform", "statistic", "p_value", "-log2(p)"] if col in summary.columns]
    summary = summary[keep]
    if p_adjust is not None and not summary.empty:
        summary = p_value_correction_table(summary, p_col="p_value", method=p_adjust, alpha=alpha)
    return summary


def plot_schoenfeld_residuals(
    residuals: pd.DataFrame,
    *,
    covariates: Sequence[str] | None = None,
    time_col: str = "time",
    residual_col: str = "residual",
    covariate_col: str = "covariate",
    title: str = "Schoenfeld residuals",
    ax: Any | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot Schoenfeld residuals for selected covariates."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise ImportError('Schoenfeld residual plots require matplotlib. Install with: uv add "fyron[survival]"') from exc
    require_columns(residuals, [time_col, residual_col, covariate_col])
    data = residuals.copy()
    selected = list(covariates or data[covariate_col].dropna().unique())
    data = data[data[covariate_col].isin(selected)]
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4))
    else:
        fig = ax.figure
    for covariate, sub in data.groupby(covariate_col, dropna=False):
        ax.scatter(sub[time_col], sub[residual_col], s=18, alpha=0.75, label=str(covariate))
    ax.axhline(0, color="black", linewidth=1, linestyle="--")
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Scaled Schoenfeld residual" if bool(data.get("scaled", pd.Series([True])).iloc[0]) else "Schoenfeld residual")
    ax.legend(loc="best")
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, format=fmt, bbox_inches="tight")
    return fig, ax
