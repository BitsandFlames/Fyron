"""Kaplan–Meier estimation, inference, and plotting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, MutableMapping, Sequence

import matplotlib.pyplot as plt
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts
from lifelines.statistics import logrank_test, multivariate_logrank_test

from fyron.survival._validate import (
    require_columns,
    validate_duration_column,
    validate_event_column,
    validate_positive_tau,
)
from fyron.survival.groups import SplitMethod, create_survival_groups, default_tau_from_observed_times
from fyron.survival.rmst import calculate_rmst
from fyron.plotting_palettes import get_palette

DEFAULT_KM_REFERENCE_BAND_COLORS = {
    "Favorable": "#8BCB88",
    "Intermediate": "#F3F95F",
    "Poor": "#F46F7B",
}
KM_REFERENCE_BAND_PRESETS = {
    "survival": {
        "order": ["Favorable", "Intermediate", "Poor"],
        "colors": DEFAULT_KM_REFERENCE_BAND_COLORS,
    },
    "risk": {
        "order": ["Low", "Intermediate", "High"],
        "colors": {"Low": "#8BCB88", "Intermediate": "#F3F95F", "High": "#F46F7B"},
    },
    "percentile": {
        "order": ["P75-P100", "P25-P75", "P0-P25"],
        "colors": {"P75-P100": "#8BCB88", "P25-P75": "#F3F95F", "P0-P25": "#F46F7B"},
    },
}


@dataclass
class KaplanMeierPlotResult:
    """Outputs from :func:`plot_kaplan_meier`."""

    fitters: dict[str, KaplanMeierFitter]
    figure: plt.Figure
    axes: plt.Axes
    logrank: dict[str, Any] | None
    n_per_group: dict[str, int]
    data: pd.DataFrame
    group_column: str | None


def plot_kaplan_meier(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    group_col: str | None = None,
    *,
    split_column: str | None = None,
    split_method: SplitMethod | None = None,
    split_bins: int | Sequence[float] | None = None,
    split_labels: Sequence[str] | bool | None = None,
    confidence_interval: bool = True,
    ci_alpha: float = 0.05,
    at_risk_counts: bool = False,
    at_risk_rows: Literal["all", "at_risk", "censored", "events"] | Sequence[str] = "all",
    show_censors: bool = False,
    censor_styles: Mapping[str, Any] | None = None,
    xlim: tuple[float, float] | None = None,
    reference_bands: Any | None = None,
    reference_band_time_col: str = "time",
    reference_band_lower_col: str = "lower",
    reference_band_upper_col: str = "upper",
    reference_band_label_col: str = "band",
    reference_band_preset: Literal["survival", "risk", "percentile"] | None = None,
    reference_band_order: Sequence[str] | None = None,
    reference_band_colors: Mapping[str, str] | Sequence[str] | None = None,
    reference_band_alpha: float = 0.22,
    reference_band_legend: bool = True,
    annotate_logrank: bool = False,
    palette: str | Sequence[str] | None = None,
    colors: Mapping[str, str] | Sequence[str] | None = None,
    linestyles: str | Sequence[str] | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str = "Survival probability",
    legend_title: str | None = None,
    legend_kwargs: MutableMapping[str, Any] | None = None,
    figsize: tuple[float, float] | None = None,
    save_path: str | Path | None = None,
    save_format: Literal["png", "pdf", "svg"] | None = None,
    dpi: int | None = None,
    annotate_rmst: bool = False,
    rmst_tau: float | None = None,
    rmst_group_col: str | None = None,
) -> KaplanMeierPlotResult:
    """Fit Kaplan–Meier curves, optionally compare groups, and plot.

    Parameters
    ----------
    df
        Survival dataset.
    duration_col, event_col
        Follow-up time and event indicator (1 = event, 0 = censored).
    group_col
        Optional categorical column defining cohorts.
    split_column, split_method, split_bins, split_labels
        When ``split_column`` is set, groups are created with
        :func:`fyron.survival.create_survival_groups` into a temporary column
        (``split_method`` must be ``\"median\"``, ``\"tertile\"``, ``\"quartile\"``, or
        ``\"custom\"`` with ``split_bins`` for custom edges).
    confidence_interval
        If True, shaded pointwise intervals are drawn.
    at_risk_counts
        If True, lifelines' at-risk table is drawn under the x-axis.
    at_risk_rows
        Rows to show when ``at_risk_counts=True``. Use ``"all"`` for lifelines'
        default rows (at risk, censored, events) or ``"at_risk"`` to show only
        the at-risk row. A custom sequence can contain ``"at_risk"``,
        ``"censored"``, and ``"events"`` aliases, or lifelines row labels such
        as ``"At risk"``, ``"Censored"``, and ``"Events"``. Sequence order is
        preserved in the rendered table.
    show_censors
        If True, censor marks are drawn on the survival curves.
    xlim
        Optional x-axis limits.
    reference_bands
        Optional long-form table with precomputed survival reference intervals.
    reference_band_time_col
        Time column in ``reference_bands``.
    reference_band_lower_col
        Lower survival probability bound in ``reference_bands``.
    reference_band_upper_col
        Upper survival probability bound in ``reference_bands``.
    reference_band_label_col
        Band label column in ``reference_bands``.
    reference_band_preset
        Optional named preset for common survival band labels and colors:
        ``"survival"``, ``"risk"``, or ``"percentile"``.
    reference_band_order
        Optional explicit order for drawing reference bands and legend entries.
    reference_band_colors
        Optional mapping from band label to color, or a color sequence matching ``reference_band_order``.
    reference_band_alpha
        Transparency used for reference bands.
    reference_band_legend
        If True, include reference-band entries in the KM legend.
    annotate_logrank
        If True, annotate the plot with the log-rank p-value when groups are present.
    palette
        Named Fyron palette or explicit colors used when ``colors`` is not supplied.
    colors
        Per-group colors as a dict ``{label: color}`` or a list applied in sorted label order.
    linestyles
        Matplotlib linestyle or one linestyle per sorted group label.
    annotate_rmst
        If True, draw a vertical line at ``rmst_tau`` (default from data) and annotate RMST.
    rmst_tau
        Truncation time for RMST text; defaults to :func:`fyron.survival.default_tau_from_observed_times`.
    rmst_group_col
        Group column passed to RMST helper when annotating (defaults to effective group column).

    Returns
    -------
    KaplanMeierPlotResult
        Fitted ``KaplanMeierFitter`` instances, figure/axes, and log-rank summary (if applicable).

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.survival.kaplan_meier import plot_kaplan_meier
    >>> df = pd.DataFrame({"t": [1, 3, 5, 2], "e": [1, 0, 1, 1], "g": ["A", "A", "B", "B"]})
    >>> res = plot_kaplan_meier(df, "t", "e", group_col="g", title="KM")
    >>> len(res.fitters)
    2
    """
    require_columns(df, [duration_col, event_col])
    plot_df = df.copy()
    validate_duration_column(plot_df[duration_col], name=duration_col)
    plot_df[event_col] = validate_event_column(plot_df[event_col], name=event_col)

    effective_group: str | None = group_col
    if split_column is not None:
        if split_method is None:
            raise ValueError("split_method is required when split_column is set.")
        if split_method == "categorical":
            raise ValueError(
                'split_method="categorical" is not supported with split_column; pass group_col instead.'
            )
        auto_group = f"{split_column}_surv_group"
        if auto_group in plot_df.columns:
            raise ValueError(f"Derived group column {auto_group!r} already exists; rename split_column or drop column.")
        plot_df = create_survival_groups(
            plot_df,
            split_column,
            split_method,
            auto_group,
            bins=split_bins,
            labels=split_labels,
        )
        effective_group = auto_group
    elif group_col is not None:
        require_columns(plot_df, [group_col])

    legend_kwargs = dict(legend_kwargs or {})
    if legend_title is not None:
        legend_kwargs.setdefault("title", legend_title)

    label_col: str
    if effective_group is None:
        label_col = "__cohort__"
        plot_df = plot_df.copy()
        plot_df[label_col] = "__cohort__"
        effective_group = label_col
        groups = ["__cohort__"]
    else:
        if plot_df[effective_group].isna().any():
            raise ValueError(f"Group column {effective_group!r} contains NaN.")
        groups = sorted(str(g) for g in plot_df[effective_group].unique())
        label_col = effective_group

    n_per_group = {g: int((plot_df[effective_group].astype(str) == g).sum()) for g in groups}

    fitters: dict[str, KaplanMeierFitter] = {}
    for g in groups:
        mask = plot_df[effective_group].astype(str) == g
        kmf = KaplanMeierFitter(label=g)
        kmf.fit(
            plot_df.loc[mask, duration_col],
            plot_df.loc[mask, event_col],
        )
        fitters[g] = kmf

    logrank_summary = _compute_logrank(plot_df, duration_col, event_col, effective_group, groups)

    figsize = figsize or (8.0, 5.0)
    fig, ax = plt.subplots(figsize=figsize)
    color_map = _resolve_colors(groups, colors if colors is not None else palette)
    ls_cycle = _resolve_linestyles(groups, linestyles)
    if reference_bands is not None:
        _draw_reference_bands(
            ax,
            reference_bands,
            time_col=reference_band_time_col,
            lower_col=reference_band_lower_col,
            upper_col=reference_band_upper_col,
            label_col=reference_band_label_col,
            preset=reference_band_preset,
            order=reference_band_order,
            colors=reference_band_colors,
            alpha=reference_band_alpha,
            legend=reference_band_legend,
        )

    for i, g in enumerate(groups):
        fitters[g].plot_survival_function(
            ax=ax,
            ci_show=confidence_interval,
            ci_alpha=ci_alpha,
            label=g,
            color=color_map[g],
            linestyle=ls_cycle[i],
            show_censors=show_censors,
            censor_styles=dict(censor_styles or {"marker": "+", "ms": 5, "mew": 1.0}),
        )

    ax.set_xlabel(xlabel or duration_col)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(True, alpha=0.3)
    if xlim is not None:
        ax.set_xlim(*xlim)

    if at_risk_counts:
        rows_to_show = _resolve_at_risk_rows(at_risk_rows)
        add_at_risk_counts(
            *[fitters[g] for g in groups],
            ax=ax,
            labels=groups,
            rows_to_show=rows_to_show,
        )
        fig.subplots_adjust(bottom=0.22 if rows_to_show == ["At risk"] else 0.28)

    if annotate_logrank and logrank_summary is not None:
        ax.text(
            0.98,
            0.04,
            "log-rank " + _format_plot_p_value(logrank_summary.get("p_value")),
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=9,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
        )

    if annotate_rmst:
        g_for_rmst = rmst_group_col
        if g_for_rmst is None:
            if len(groups) == 1 and groups[0] == "__cohort__":
                g_for_rmst = None
            else:
                g_for_rmst = effective_group
        tau = rmst_tau if rmst_tau is not None else default_tau_from_observed_times(plot_df, duration_col, g_for_rmst)
        validate_positive_tau(tau, name="rmst_tau")
        rmst_df = calculate_rmst(plot_df, duration_col, event_col, group_col=g_for_rmst, tau=tau)
        ax.axvline(tau, color="0.35", linestyle="--", linewidth=1.0)
        lines = [rf"$\tau$={tau:.3g}"]
        for _, row in rmst_df.iterrows():
            gname = str(row["group"])
            rmst_val = float(row["rmst"])
            lines.append(f"{gname}: RMST={rmst_val:.3g}")
        ax.text(
            0.02,
            0.02,
            "\n".join(lines),
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment="bottom",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
        )

    ax.legend(**legend_kwargs)

    if save_path is not None:
        path = Path(save_path)
        fmt = save_format or path.suffix.lstrip(".").lower()  # type: ignore[assignment]
        if fmt not in {"png", "pdf", "svg"}:
            raise ValueError("save_format must be one of png, pdf, svg (or infer from save_path suffix).")
        fig.savefig(path, format=fmt, bbox_inches="tight", dpi=dpi)

    out_group_name: str | None
    if len(groups) == 1 and groups[0] == "__cohort__":
        out_group_name = None
    else:
        out_group_name = effective_group

    return KaplanMeierPlotResult(
        fitters=fitters,
        figure=fig,
        axes=ax,
        logrank=logrank_summary,
        n_per_group=n_per_group,
        data=plot_df,
        group_column=out_group_name,
    )


_AT_RISK_ROW_ALIASES = {
    "at_risk": "At risk",
    "at risk": "At risk",
    "At risk": "At risk",
    "censored": "Censored",
    "Censored": "Censored",
    "events": "Events",
    "event": "Events",
    "Events": "Events",
}


def _resolve_at_risk_rows(
    rows: Literal["all", "at_risk", "censored", "events"] | Sequence[str],
) -> list[str] | None:
    if isinstance(rows, str):
        if rows == "all":
            return None
        if rows in _AT_RISK_ROW_ALIASES:
            return [_AT_RISK_ROW_ALIASES[rows]]
        raise ValueError(
            'at_risk_rows must be "all", "at_risk", "censored", "events", '
            "or a sequence of these row labels."
        )
    raw_rows = list(rows)
    normalized = [_AT_RISK_ROW_ALIASES.get(row, row) for row in raw_rows]
    invalid = [row for row in raw_rows if row not in _AT_RISK_ROW_ALIASES]
    if invalid:
        raise ValueError(
            f"Unsupported at_risk_rows entries: {invalid}. "
            f"Valid entries are {sorted(_AT_RISK_ROW_ALIASES)}."
        )
    if not normalized:
        raise ValueError("at_risk_rows cannot be empty.")
    return normalized


def _compute_logrank(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    group_col: str,
    groups: list[str],
) -> dict[str, Any] | None:
    if len(groups) < 2:
        return None
    if len(groups) == 2:
        g1, g2 = groups
        m1 = df[group_col].astype(str) == g1
        m2 = df[group_col].astype(str) == g2
        res = logrank_test(
            df.loc[m1, duration_col],
            df.loc[m2, duration_col],
            df.loc[m1, event_col],
            df.loc[m2, event_col],
        )
        return {
            "test": "logrank_test",
            "groups": (g1, g2),
            "test_statistic": float(res.test_statistic),
            "p_value": float(res.p_value),
            "summary": res.summary,
        }
    res = multivariate_logrank_test(
        df[duration_col],
        df[group_col].astype(str),
        df[event_col],
    )
    return {
        "test": "multivariate_logrank_test",
        "groups": tuple(groups),
        "test_statistic": float(res.test_statistic),
        "p_value": float(res.p_value),
        "degrees_of_freedom": int(res.degrees_of_freedom) if hasattr(res, "degrees_of_freedom") else None,
        "summary": res.summary,
    }


def _format_plot_p_value(p_value: Any) -> str:
    try:
        p = float(p_value)
    except (TypeError, ValueError):
        return "p = n/a"
    if not pd.notna(p):
        return "p = n/a"
    if p < 0.001:
        return "p < 0.001"
    return f"p = {p:.3f}"


def _draw_reference_bands(
    ax: plt.Axes,
    reference_bands: Any,
    *,
    time_col: str,
    lower_col: str,
    upper_col: str,
    label_col: str,
    preset: Literal["survival", "risk", "percentile"] | None,
    order: Sequence[str] | None,
    colors: Mapping[str, str] | Sequence[str] | None,
    alpha: float,
    legend: bool,
) -> None:
    if not 0 <= alpha <= 1:
        raise ValueError("reference_band_alpha must be between 0 and 1.")
    band_df = pd.DataFrame(reference_bands).copy()
    required = [time_col, lower_col, upper_col, label_col]
    missing = [column for column in required if column not in band_df.columns]
    if missing:
        raise ValueError(f"reference_bands missing required columns: {missing}")
    for column in [time_col, lower_col, upper_col]:
        band_df[column] = pd.to_numeric(band_df[column], errors="coerce")
    band_df = band_df.dropna(subset=[time_col, lower_col, upper_col, label_col])
    if band_df.empty:
        raise ValueError("reference_bands must contain at least one complete interval row.")
    if (band_df[lower_col] > band_df[upper_col]).any():
        raise ValueError("reference band rows must satisfy lower <= upper.")
    band_df["_fyron_band"] = band_df[label_col].astype(str)
    preset_order, preset_colors = _resolve_km_reference_band_preset(preset)
    if order is None:
        order = preset_order
    if colors is None:
        colors = preset_colors
    band_labels = _ordered_labels(band_df["_fyron_band"], order)
    color_lookup = _resolve_reference_band_colors(band_labels, colors)
    for band_label in band_labels:
        subset = band_df[band_df["_fyron_band"] == band_label].sort_values(time_col)
        if subset.empty:
            continue
        ax.fill_between(
            subset[time_col].to_numpy(dtype=float),
            subset[lower_col].clip(0, 1).to_numpy(dtype=float),
            subset[upper_col].clip(0, 1).to_numpy(dtype=float),
            color=color_lookup[band_label],
            alpha=alpha,
            linewidth=0,
            label=band_label if legend else "_nolegend_",
            zorder=0,
        )


def _ordered_labels(series: pd.Series, order: Sequence[str] | None = None) -> list[str]:
    present = list(dict.fromkeys(series.astype(str)))
    if order is None:
        return present
    requested = [str(value) for value in order]
    visible = [value for value in requested if value in present]
    if not visible:
        raise ValueError("reference_band_order must include at least one band present in reference_bands.")
    return visible


def _resolve_km_reference_band_preset(
    preset: Literal["survival", "risk", "percentile"] | None,
) -> tuple[Sequence[str] | None, Mapping[str, str] | None]:
    if preset is None:
        return None, None
    if preset not in KM_REFERENCE_BAND_PRESETS:
        valid = ", ".join(sorted(KM_REFERENCE_BAND_PRESETS))
        raise ValueError(f"reference_band_preset must be one of: {valid}.")
    spec = KM_REFERENCE_BAND_PRESETS[preset]
    return list(spec["order"]), dict(spec["colors"])


def _resolve_reference_band_colors(
    labels: Sequence[str],
    colors: Mapping[str, str] | Sequence[str] | None,
) -> dict[str, str]:
    if colors is None:
        fallback = get_palette("bf_vibrant_muted", n=len(labels))
        return {label: DEFAULT_KM_REFERENCE_BAND_COLORS.get(label, fallback[index]) for index, label in enumerate(labels)}
    if isinstance(colors, Mapping):
        fallback = get_palette("bf_vibrant_muted", n=len(labels))
        mapped = {str(key): value for key, value in colors.items()}
        return {label: mapped.get(label, fallback[index]) for index, label in enumerate(labels)}
    if len(colors) < len(labels):
        raise ValueError("reference_band_colors must provide at least one color per reference band.")
    return {label: str(colors[index]) for index, label in enumerate(labels)}


def _resolve_colors(groups: list[str], colors: Mapping[str, str] | Sequence[str] | str | None) -> dict[str, str]:
    if colors is None:
        palette = get_palette("okabe_ito", n=len(groups))
        return {g: palette[i] for i, g in enumerate(groups)}
    if isinstance(colors, Mapping):
        missing = [g for g in groups if g not in colors]
        if missing:
            raise KeyError(f"colors dict missing entries for groups: {missing}")
        return {g: colors[g] for g in groups}
    if isinstance(colors, str):
        palette = get_palette(colors, n=len(groups))
        return {g: palette[i] for i, g in enumerate(groups)}
    if len(colors) < len(groups):
        raise ValueError(f"colors list length {len(colors)} < number of groups {len(groups)}.")
    return {g: colors[i] for i, g in enumerate(groups)}


def _resolve_linestyles(groups: list[str], linestyles: str | Sequence[str] | None) -> list[str]:
    if linestyles is None:
        return ["-"] * len(groups)
    if isinstance(linestyles, str):
        return [linestyles] * len(groups)
    if len(linestyles) < len(groups):
        raise ValueError("linestyles sequence shorter than number of groups.")
    return [str(linestyles[i]) for i in range(len(groups))]
