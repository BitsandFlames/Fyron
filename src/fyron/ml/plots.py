"""Publication-friendly plots for clinical data science workflows."""

from __future__ import annotations

from pathlib import Path
from statistics import NormalDist
from typing import Any, Literal, Mapping, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.ticker import FuncFormatter
from numpy.typing import ArrayLike
from sklearn import metrics as sk_metrics
from sklearn.calibration import calibration_curve

from fyron.ml._arrays import ArrayLikeInput, resolve_pos_label, to_numpy_1d
from fyron.plotting_palettes import get_palette, resolve_colormap, resolve_palette, set_plot_style

PlotReturn = Tuple[Figure, Axes]
TablePlotReturn = Tuple[Figure, Axes, pd.DataFrame]
Orientation = Literal["vertical", "horizontal"]
AnnotationFormat = Literal["star", "pvalue", "simple"]
StatTestName = Literal[
    "mannwhitney",
    "welch",
    "ttest",
    "paired_ttest",
    "wilcoxon",
    "kruskal",
    "brunner_munzel",
]

DEFAULT_COLORS = [
    "#000000",
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
]
DEFAULT_HATCHES = ["", "///", "\\\\\\", "xx", "..", "++", "--", "oo"]
BOARISK_PALETTE = {
    "blue": "#4D9ED8",
    "red": "#E56B6F",
    "purple": "#8E7CC3",
    "orange": "#F2A65A",
    "ink": "#000000",
    "muted": "#5F6872",
    "grid": "#E8EBF0",
    "paper": "#FFFFFF",
    "wash": "#F7F8FA",
}
DEFAULT_REFERENCE_BAND_COLORS = {
    "Below -1 SD": "#8BCB88",
    "+/- 1 SD": "#B9F2A0",
    "+1 to +2 SD": "#F3F95F",
    "+2 to +3 SD": "#F1C96D",
    "Above +3 SD": "#F46F7B",
}
REFERENCE_BAND_PRESETS = {
    "sd": {
        "order": ["Below -1 SD", "+/- 1 SD", "+1 to +2 SD", "+2 to +3 SD", "Above +3 SD"],
        "colors": DEFAULT_REFERENCE_BAND_COLORS,
    },
    "survival": {
        "order": ["Favorable", "Intermediate", "Poor"],
        "colors": {"Favorable": "#8BCB88", "Intermediate": "#F3F95F", "Poor": "#F46F7B"},
    },
    "risk": {
        "order": ["Low", "Intermediate", "High"],
        "colors": {"Low": "#8BCB88", "Intermediate": "#F3F95F", "High": "#F46F7B"},
    },
    "percentile": {
        "order": ["<P5", "P5-P25", "P25-P75", "P75-P95", ">P95"],
        "colors": {
            "<P5": "#F46F7B",
            "P5-P25": "#F1C96D",
            "P25-P75": "#B9F2A0",
            "P75-P95": "#F1C96D",
            ">P95": "#F46F7B",
        },
    },
}


def _apply_plot_style() -> None:
    set_plot_style("paper", palette="okabe_ito")


def _maybe_save(fig: Figure, save_path: str | Path | None, *, fmt: str = "png") -> None:
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, format=fmt, bbox_inches="tight")


def plot_kaplan_meier(*args: Any, **kwargs: Any):
    """Clinical plotting alias for Kaplan-Meier curves.

    The statistical implementation lives in :mod:`fyron.survival`. This wrapper
    keeps Kaplan-Meier available from ``fyron.ml`` next to the other clinical
    plotting helpers while preserving the optional ``fyron[survival]``
    dependency boundary.
    """
    try:
        from fyron.survival import plot_kaplan_meier as _plot_kaplan_meier
    except ImportError as exc:  # pragma: no cover - only exercised without survival extra
        raise ImportError(
            "Kaplan-Meier plotting requires the survival extra. "
            'Install it with: uv add "fyron[survival]"'
        ) from exc
    return _plot_kaplan_meier(*args, **kwargs)


def _resolve_color_sequence(n: int, palette: str | Sequence[str] | None = None) -> list[str]:
    return resolve_palette(palette, n=n, default="okabe_ito")


def _resolve_hatch_sequence(n: int, hatches: Sequence[str] | None = None) -> list[str]:
    patterns = list(hatches or DEFAULT_HATCHES)
    if not patterns:
        patterns = DEFAULT_HATCHES
    return [patterns[i % len(patterns)] for i in range(n)]


def _require_columns(df: pd.DataFrame, columns: Sequence[str | None]) -> None:
    missing = [c for c in columns if c is not None and c not in df.columns]
    if missing:
        raise ValueError(f"columns not found in data: {missing}")


def _p_value_label(p_value: Any) -> str:
    try:
        p = float(p_value)
    except (TypeError, ValueError):
        return "p = n/a"
    if not np.isfinite(p):
        return "p = n/a"
    if p < 0.001:
        return "p < 0.001"
    return f"p = {p:.3f}"


def _p_value_compact(p_value: Any) -> str:
    try:
        p = float(p_value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(p):
        return "n/a"
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def _ratio_estimate_header(ratio_label: str) -> str:
    label = ratio_label.lower()
    if "hazard" in label:
        return "HR"
    if "odds" in label:
        return "OR"
    if "risk" in label:
        return "RR"
    return ratio_label


def format_p_value_annotation(
    p_value: Any,
    *,
    text_format: AnnotationFormat = "star",
    thresholds: Sequence[tuple[float, str]] = ((0.001, "***"), (0.01, "**"), (0.05, "*")),
    ns_label: str = "ns",
) -> str:
    """Format a p-value for manuscript-style plot annotations.

    Parameters
    ----------
    p_value
        Raw or adjusted p-value.
    text_format
        ``"star"`` for significance stars, ``"pvalue"`` for explicit p-values,
        or ``"simple"`` for compact values such as ``p<0.001``.
    thresholds
        P-value thresholds used for star labels.
    ns_label
        Label for non-significant comparisons in ``"star"`` mode.

    Returns
    -------
    str
        Text label suitable for plot brackets.
    """

    try:
        p = float(p_value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(p):
        return "n/a"
    if text_format == "pvalue":
        return _p_value_label(p)
    if text_format == "simple":
        return "p<0.001" if p < 0.001 else f"p={p:.3f}"
    if text_format != "star":
        raise ValueError("text_format must be 'star', 'pvalue', or 'simple'.")
    for threshold, label in sorted(thresholds, key=lambda item: item[0]):
        if p < threshold:
            return label
    return ns_label


def _ordered_string_values(series: pd.Series, order: Sequence[Any] | None = None) -> list[str]:
    if order is not None:
        return [str(value) for value in order]
    return list(dict.fromkeys(series.astype(str)))


def stat_test_pairs(
    data: Any,
    *,
    x: str,
    y: str,
    pairs: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]],
    hue: str | None = None,
    test: StatTestName = "mannwhitney",
    p_adjust: str = "none",
    alpha: float = 0.05,
    p_values: Sequence[float] | Mapping[tuple[Any, Any], float] | pd.DataFrame | None = None,
    label_col: str = "label",
    p_col: str = "p_value",
    text_format: AnnotationFormat = "star",
    hide_ns: bool = False,
) -> pd.DataFrame:
    """Run pairwise statistical tests for plot annotations.

    Parameters
    ----------
    data
        Tabular data coercible to a DataFrame.
    x, y
        Categorical grouping column and numeric value column.
    pairs
        Comparisons. Without ``hue`` use ``("A", "B")``. With ``hue`` use
        ``(("A", "F"), ("A", "M"))`` keys.
    hue
        Optional second grouping column.
    test
        Statistical test name.
    p_adjust
        Multiple-testing correction method accepted by
        :func:`fyron.statistics.p_value_correction_table`.
    p_values
        Optional custom p-values. When provided, no statistical test is run.
    text_format
        Annotation label style: ``"star"``, ``"pvalue"``, or ``"simple"``.
    hide_ns
        If True, non-significant comparisons receive an empty annotation.

    Returns
    -------
    pandas.DataFrame
        One row per comparison with test, statistic, raw/adjusted p-values,
        reject flag, annotation, and group sizes.
    """

    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, y, hue])
    df[y] = pd.to_numeric(df[y], errors="coerce")
    df = df.dropna(subset=[x, y] + ([hue] if hue else []))
    custom = _custom_p_lookup(p_values, pairs=pairs, p_col=p_col, label_col=label_col)
    rows: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs):
        left_key, right_key = _pair_keys(pair, hue=hue)
        left = _comparison_values(df, x=x, y=y, hue=hue, key=left_key)
        right = _comparison_values(df, x=x, y=y, hue=hue, key=right_key)
        custom_p = custom.get(index, custom.get((_format_comparison_key(left_key), _format_comparison_key(right_key))))
        if custom_p is None:
            p_value, used_test, statistic = _run_annotation_test(left, right, test=test)
        else:
            p_value, used_test, statistic = float(custom_p), "custom", float("nan")
        rows.append(
            {
                "comparison": f"{_format_comparison_key(left_key)} vs {_format_comparison_key(right_key)}",
                "group_a": _format_comparison_key(left_key),
                "group_b": _format_comparison_key(right_key),
                "x_a": left_key[0],
                "hue_a": None if left_key[1] == "__single__" else left_key[1],
                "x_b": right_key[0],
                "hue_b": None if right_key[1] == "__single__" else right_key[1],
                "n_a": int(left.size),
                "n_b": int(right.size),
                "test": used_test,
                "statistic": statistic,
                "p_value": p_value,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    try:
        from fyron.statistics import p_value_correction_table
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'Statistical annotation correction requires scipy. Install with: uv add "fyron[statistics]"'
        ) from exc
    out = p_value_correction_table(out, p_col="p_value", method=p_adjust, alpha=alpha)
    label_p = out["p_adjusted"] if "p_adjusted" in out else out["p_value"]
    out["annotation"] = [format_p_value_annotation(p, text_format=text_format) for p in label_p]
    if hide_ns and "rejected" in out:
        out.loc[~out["rejected"].fillna(False), "annotation"] = ""
    return out


def add_stat_annotations(
    ax: Axes,
    stats_table: pd.DataFrame,
    *,
    positions: Mapping[tuple[str, str], float] | None = None,
    heights: Mapping[tuple[str, str], float] | None = None,
    annotation_col: str = "annotation",
    line_color: str = BOARISK_PALETTE["ink"],
    text_color: str = BOARISK_PALETTE["ink"],
    fontsize: float = 9,
    loc: Literal["outside", "inside"] = "outside",
) -> Axes:
    """Add bracket-style statistical annotations to an existing categorical plot."""

    if stats_table is None or stats_table.empty:
        return ax
    pos = dict(positions or _positions_from_xticks(ax))
    y0, y1 = ax.get_ylim()
    span = max(abs(y1 - y0), 1e-6)
    default_height = y1 - span * 0.05
    item_heights = dict(heights or {})
    current_y = (y1 + span * 0.06) if loc == "outside" else (y1 - span * 0.18)
    step = span * 0.08
    for _, row in stats_table.iterrows():
        label = str(row.get(annotation_col, ""))
        if not label:
            continue
        left = (str(row["x_a"]), str(row.get("hue_a") or "__single__"))
        right = (str(row["x_b"]), str(row.get("hue_b") or "__single__"))
        if left not in pos or right not in pos:
            continue
        x1, x2 = pos[left], pos[right]
        if x1 > x2:
            x1, x2 = x2, x1
        base = max(item_heights.get(left, default_height), item_heights.get(right, default_height), current_y)
        y = base if loc == "inside" else current_y
        h = step * 0.25
        ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color=line_color, linewidth=0.9, clip_on=False)
        ax.text((x1 + x2) / 2, y + h * 1.12, label, ha="center", va="bottom", color=text_color, fontsize=fontsize)
        current_y = y + step
    if loc == "outside":
        ax.set_ylim(y0, max(ax.get_ylim()[1], current_y + step * 0.4))
    return ax


def _gaussian_kde_numpy(
    values: np.ndarray,
    grid: np.ndarray,
    *,
    bandwidth: float | None = None,
) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        raise ValueError("density plots require at least two numeric values per plotted group.")
    std = float(np.std(values, ddof=1))
    if bandwidth is None:
        bandwidth = 1.06 * std * (values.size ** (-1 / 5))
    if bandwidth is None or not np.isfinite(bandwidth) or bandwidth <= 0:
        bandwidth = max(float(np.ptp(grid)) / 100, 1e-6)
    scaled = (grid[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * scaled * scaled).sum(axis=1)
    return density / (values.size * bandwidth * np.sqrt(2 * np.pi))


def _gaussian_kde_2d_numpy(
    x_values: np.ndarray,
    y_values: np.ndarray,
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    *,
    bandwidth: float | tuple[float, float] | None = None,
) -> np.ndarray:
    x_values = np.asarray(x_values, dtype=float)
    y_values = np.asarray(y_values, dtype=float)
    mask = np.isfinite(x_values) & np.isfinite(y_values)
    x_values = x_values[mask]
    y_values = y_values[mask]
    if x_values.size < 3:
        raise ValueError(
            "filled KDE plots require at least three complete numeric rows per plotted group."
        )
    if isinstance(bandwidth, tuple):
        bw_x, bw_y = float(bandwidth[0]), float(bandwidth[1])
    else:
        std_x = float(np.std(x_values, ddof=1))
        std_y = float(np.std(y_values, ddof=1))
        if bandwidth is None:
            factor = x_values.size ** (-1 / 6)
            bw_x = std_x * factor
            bw_y = std_y * factor
        else:
            bw_x = bw_y = float(bandwidth)
    if not np.isfinite(bw_x) or bw_x <= 0:
        bw_x = max(float(np.ptp(x_grid)) / 100, 1e-6)
    if not np.isfinite(bw_y) or bw_y <= 0:
        bw_y = max(float(np.ptp(y_grid)) / 100, 1e-6)
    x_scaled = (x_grid[:, :, None] - x_values[None, None, :]) / bw_x
    y_scaled = (y_grid[:, :, None] - y_values[None, None, :]) / bw_y
    density = np.exp(-0.5 * (x_scaled * x_scaled + y_scaled * y_scaled)).sum(axis=2)
    return density / (x_values.size * 2 * np.pi * bw_x * bw_y)


def plot_roc_curve(
    y_true: ArrayLikeInput,
    y_prob: ArrayLike,
    *,
    title: str = "ROC curve",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
    pos_label: Any | None = None,
) -> PlotReturn:
    """Plot an ROC curve and return the figure and axis.

    Examples
    --------
    >>> from fyron.ml import plot_roc_curve
    >>> fig, ax = plot_roc_curve([0, 1, 1], [0.1, 0.8, 0.6], title="Model ROC")
    >>> plt.close(fig)
    """
    _apply_plot_style()
    y_true_arr = to_numpy_1d(y_true)
    y_prob_arr = to_numpy_1d(y_prob)
    pos = resolve_pos_label(y_true_arr, pos_label)
    fpr, tpr, _ = sk_metrics.roc_curve(y_true_arr, y_prob_arr, pos_label=pos)
    auc = sk_metrics.roc_auc_score(y_true_arr, y_prob_arr)
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5))
    else:
        fig = ax.figure
    ax.plot(fpr, tpr, linewidth=2, label=f"AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(title)
    ax.legend(loc="lower right")
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_confusion_matrix(
    y_true: ArrayLikeInput,
    y_pred: ArrayLikeInput,
    *,
    title: str = "Confusion matrix",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
    pos_label: Any | None = None,
) -> PlotReturn:
    """Plot a confusion matrix heatmap.

    Examples
    --------
    >>> from fyron.ml import plot_confusion_matrix
    >>> fig, ax = plot_confusion_matrix([0, 1, 1, 0], [0, 1, 0, 0])
    >>> plt.close(fig)
    """
    _apply_plot_style()
    y_true_arr = to_numpy_1d(y_true)
    y_pred_arr = to_numpy_1d(y_pred)
    pos = resolve_pos_label(y_true_arr, pos_label)
    labels = sorted(np.unique(np.concatenate([y_true_arr, y_pred_arr])), key=lambda v: (v == pos, v))
    if pos in labels and labels[-1] != pos:
        labels = [x for x in labels if x != pos] + [pos]
    cm = sk_metrics.confusion_matrix(y_true_arr, y_pred_arr, labels=labels)
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 4))
    else:
        fig = ax.figure
    im = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(labels)), labels=[str(x) for x in labels])
    ax.set_yticks(range(len(labels)), labels=[str(x) for x in labels])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_precision_recall_curve(
    y_true: ArrayLikeInput,
    y_prob: ArrayLike,
    *,
    title: str = "Precision-recall curve",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
    pos_label: Any | None = None,
) -> PlotReturn:
    """Plot a precision-recall curve for binary classification.

    Examples
    --------
    >>> from fyron.ml import plot_precision_recall_curve
    >>> fig, ax = plot_precision_recall_curve([0, 1, 1], [0.1, 0.8, 0.6])
    >>> plt.close(fig)
    """
    _apply_plot_style()
    y_true_arr = to_numpy_1d(y_true)
    y_prob_arr = to_numpy_1d(y_prob)
    pos = resolve_pos_label(y_true_arr, pos_label)
    precision, recall, _ = sk_metrics.precision_recall_curve(
        y_true_arr,
        y_prob_arr,
        pos_label=pos,
    )
    ap = sk_metrics.average_precision_score(y_true_arr, y_prob_arr, pos_label=pos)
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5))
    else:
        fig = ax.figure
    ax.plot(recall, precision, linewidth=2, label=f"AP = {ap:.3f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(title)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower left")
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_cross_validated_roc(
    data: Any,
    *,
    y_true_col: str = "y_true",
    y_prob_col: str = "y_prob",
    fold_col: str = "fold",
    mean_grid_points: int = 101,
    palette: str | Sequence[str] | None = "okabe_ito",
    title: str | None = None,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> TablePlotReturn:
    """Plot ROC curves from cross-validation fold predictions.

    Parameters
    ----------
    data
        DataFrame-like table with one row per out-of-fold prediction.
    y_true_col, y_prob_col, fold_col
        Columns containing the binary label, predicted probability, and fold ID.
    mean_grid_points
        Number of false-positive-rate grid points used for the mean ROC curve.
    palette
        Named Fyron palette or explicit color sequence for fold curves.

    Returns
    -------
    tuple
        ``(fig, ax, table)`` where ``table`` contains per-fold AUC values and
        mean/std summary rows.
    """

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [y_true_col, y_prob_col, fold_col])
    df[y_prob_col] = pd.to_numeric(df[y_prob_col], errors="coerce")
    df = df.dropna(subset=[y_true_col, y_prob_col, fold_col])
    if df.empty:
        raise ValueError("data must contain at least one valid prediction row.")
    if mean_grid_points < 3:
        raise ValueError("mean_grid_points must be at least 3.")

    folds = list(dict.fromkeys(df[fold_col].astype(str)))
    colors = _resolve_color_sequence(len(folds), palette)
    mean_fpr = np.linspace(0.0, 1.0, mean_grid_points)
    interp_tprs: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []

    if ax is None:
        fig, ax = plt.subplots(figsize=(6.1, 5.0))
    else:
        fig = ax.figure

    for index, fold in enumerate(folds):
        sub = df[df[fold_col].astype(str) == fold]
        y_true = to_numpy_1d(sub[y_true_col])
        y_prob = to_numpy_1d(sub[y_prob_col])
        classes = np.unique(y_true)
        if classes.size != 2:
            raise ValueError(f"fold {fold!r} must contain exactly two outcome classes for ROC plotting.")
        fpr, tpr, _ = sk_metrics.roc_curve(y_true, y_prob)
        auc = float(sk_metrics.roc_auc_score(y_true, y_prob))
        interp = np.interp(mean_fpr, fpr, tpr)
        interp[0] = 0.0
        interp[-1] = 1.0
        interp_tprs.append(interp)
        rows.append({"fold": fold, "auc": auc, "n": int(len(sub)), "kind": "fold"})
        ax.plot(
            fpr,
            tpr,
            color=colors[index],
            linewidth=1.25,
            alpha=0.52,
            label=f"{fold} AUC {auc:.2f}",
        )

    tpr_matrix = np.vstack(interp_tprs)
    mean_tpr = tpr_matrix.mean(axis=0)
    std_tpr = tpr_matrix.std(axis=0, ddof=0)
    mean_auc = float(np.mean([row["auc"] for row in rows]))
    std_auc = float(np.std([row["auc"] for row in rows], ddof=0))
    ax.plot(mean_fpr, mean_tpr, color="#111827", linewidth=2.4, label=f"Mean AUC {mean_auc:.2f}")
    ax.fill_between(
        mean_fpr,
        np.clip(mean_tpr - std_tpr, 0, 1),
        np.clip(mean_tpr + std_tpr, 0, 1),
        color="#111827",
        alpha=0.12,
        linewidth=0,
        label="Mean +/- 1 SD",
    )
    ax.plot([0, 1], [0, 1], linestyle="--", color="#6B7280", linewidth=1.0)
    rows.extend(
        [
            {"fold": "mean", "auc": mean_auc, "n": int(len(df)), "kind": "summary"},
            {"fold": "std", "auc": std_auc, "n": int(len(df)), "kind": "summary"},
        ]
    )
    table = pd.DataFrame(rows)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(title or "Cross-validated ROC")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax, table


def plot_calibration_curve(
    y_true: ArrayLikeInput,
    y_prob: ArrayLike,
    *,
    n_bins: int = 10,
    strategy: Literal["uniform", "quantile"] = "uniform",
    title: str = "Calibration curve",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
    pos_label: Any | None = None,
) -> PlotReturn:
    """Plot observed event frequency against predicted probability.

    This is useful for clinical risk models where probability calibration matters
    as much as discrimination.

    Examples
    --------
    >>> from fyron.ml import plot_calibration_curve
    >>> fig, ax = plot_calibration_curve([0, 1, 1, 0], [0.1, 0.8, 0.7, 0.2], n_bins=2)
    >>> plt.close(fig)
    """
    _apply_plot_style()
    y_true_arr = to_numpy_1d(y_true)
    y_prob_arr = to_numpy_1d(y_prob)
    pos = resolve_pos_label(y_true_arr, pos_label)
    y_binary = (y_true_arr == pos).astype(int)
    prob_true, prob_pred = calibration_curve(
        y_binary,
        y_prob_arr,
        n_bins=n_bins,
        strategy=strategy,
    )
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5))
    else:
        fig = ax.figure
    ax.plot(prob_pred, prob_true, marker="o", linewidth=2, label="Model")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1, label="Perfect")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed event frequency")
    ax.set_title(title)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left")
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_correlation_heatmap(
    data: Any,
    *,
    columns: Sequence[str] | None = None,
    method: Literal["pearson", "spearman", "kendall"] = "spearman",
    group_col: str | None = None,
    title: str = "Correlation heatmap",
    annotate: bool = True,
    annotate_significance: bool = False,
    p_adjust: str | None = "fdr_bh",
    mask_upper: bool = False,
    cmap: str = "fyron_diverging_blue_red",
    vmin: float = -1.0,
    vmax: float = 1.0,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> tuple[Figure, Axes, pd.DataFrame]:
    """Plot a numeric correlation heatmap and return the correlation table.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.ml import plot_correlation_heatmap
    >>> df = pd.DataFrame({"age": [50, 60, 70], "score": [1.0, 2.0, 2.5]})
    >>> fig, ax, corr = plot_correlation_heatmap(df)
    >>> corr.shape
    (2, 2)
    >>> plt.close(fig)
    """
    _apply_plot_style()
    df = pd.DataFrame(data)
    if group_col is not None:
        return plot_grouped_correlation_heatmaps(
            df,
            columns=columns,
            group_col=group_col,
            method=method,
            title=title,
            annotate=annotate,
            annotate_significance=annotate_significance,
            p_adjust=p_adjust,
            mask_upper=mask_upper,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            save_path=save_path,
            fmt=fmt,
        )  # type: ignore[return-value]
    if columns is not None:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(f"columns not found in data: {missing}")
        df = df.loc[:, list(columns)]
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        raise ValueError("At least two numeric columns are required.")
    corr = numeric.corr(method=method)
    values = corr.to_numpy(dtype=float)
    if mask_upper:
        values = values.copy()
        values[np.triu_indices_from(values, k=1)] = np.nan

    if ax is None:
        size = max(4.5, 0.45 * len(corr.columns))
        fig, ax = plt.subplots(figsize=(size, size))
    else:
        fig = ax.figure
    im = ax.imshow(values, cmap=resolve_colormap(cmap), vmin=vmin, vmax=vmax)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label=f"{method.title()} r")
    labels = [str(c) for c in corr.columns]
    ax.set_xticks(range(len(labels)), labels=labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_title(title)
    if annotate:
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                if np.isnan(values[i, j]):
                    continue
                ax.text(
                    j,
                    i,
                    f"{values[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="white" if abs(values[i, j]) > 0.55 else "black",
                    fontsize=9,
                )
    if annotate_significance:
        _annotate_correlation_significance(
            ax,
            numeric,
            columns=list(corr.columns),
            method=method,
            p_adjust=p_adjust,
            mask_upper=mask_upper,
        )
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax, corr


def plot_grouped_correlation_heatmaps(
    data: Any,
    *,
    group_col: str,
    columns: Sequence[str] | None = None,
    method: Literal["pearson", "spearman", "kendall"] = "spearman",
    title: str = "Grouped correlation heatmaps",
    annotate: bool = True,
    annotate_significance: bool = False,
    p_adjust: str | None = "fdr_bh",
    mask_upper: bool = False,
    cmap: str = "fyron_diverging_blue_red",
    vmin: float = -1.0,
    vmax: float = 1.0,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> tuple[Figure, np.ndarray, pd.DataFrame]:
    """Plot one correlation heatmap per group and return a long correlation table."""

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [group_col])
    selected = list(columns or df.select_dtypes(include="number").columns)
    _require_columns(df, selected)
    groups = _ordered_string_values(df[group_col].astype(str))
    if not groups:
        raise ValueError("group_col must contain at least one group.")
    n_groups = len(groups)
    fig, axes = plt.subplots(1, n_groups, figsize=(max(4.0 * n_groups, 5.0), max(4.0, 0.45 * len(selected))))
    axes_arr = np.asarray(axes).reshape(-1)
    rows: list[pd.DataFrame] = []
    for ax_i, group_value in zip(axes_arr, groups):
        sub = df.loc[df[group_col].astype(str) == group_value, selected]
        if sub.select_dtypes(include="number").shape[1] < 2:
            raise ValueError(f"Group {group_value!r} has fewer than two numeric columns.")
        corr = sub.corr(method=method)
        vals = corr.to_numpy(dtype=float)
        if mask_upper:
            vals = vals.copy()
            vals[np.triu_indices_from(vals, k=1)] = np.nan
        im = ax_i.imshow(vals, cmap=resolve_colormap(cmap), vmin=vmin, vmax=vmax)
        labels = [str(c) for c in corr.columns]
        ax_i.set_xticks(range(len(labels)), labels=labels, rotation=45, ha="right")
        ax_i.set_yticks(range(len(labels)), labels=labels)
        ax_i.set_title(str(group_value))
        if annotate:
            for r in range(vals.shape[0]):
                for c in range(vals.shape[1]):
                    if np.isnan(vals[r, c]):
                        continue
                    ax_i.text(c, r, f"{vals[r, c]:.2f}", ha="center", va="center", color="white" if abs(vals[r, c]) > 0.55 else "black", fontsize=8)
        if annotate_significance:
            _annotate_correlation_significance(ax_i, sub, columns=labels, method=method, p_adjust=p_adjust, mask_upper=mask_upper)
        long = corr.stack().reset_index()
        long.columns = ["variable_a", "variable_b", "correlation"]
        long[group_col] = group_value
        rows.append(long)
    fig.colorbar(im, ax=axes_arr.tolist(), fraction=0.025, pad=0.04, label=f"{method.title()} r")
    fig.suptitle(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, axes_arr, pd.concat(rows, ignore_index=True)


def _annotate_correlation_significance(
    ax: Axes,
    df: pd.DataFrame,
    *,
    columns: Sequence[str],
    method: str,
    p_adjust: str | None,
    mask_upper: bool,
) -> None:
    try:
        from fyron.statistics import correlation_pvalue_table
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'Correlation significance overlays require scipy. Install with: uv add "fyron[statistics]"'
        ) from exc
    tests = correlation_pvalue_table(df, list(columns), method=method, p_adjust=p_adjust)
    if tests.empty:
        return
    p_lookup: dict[tuple[str, str], float] = {}
    p_col = "p_adjusted" if "p_adjusted" in tests.columns else "p_value"
    for _, row in tests.iterrows():
        a, b = str(row["variable_a"]), str(row["variable_b"])
        p_lookup[(a, b)] = float(row[p_col])
        p_lookup[(b, a)] = float(row[p_col])
    index = {str(col): i for i, col in enumerate(columns)}
    for a in columns:
        for b in columns:
            if a == b:
                continue
            i, j = index[str(a)], index[str(b)]
            if mask_upper and j > i:
                continue
            p = p_lookup.get((str(a), str(b)))
            label = format_p_value_annotation(p, text_format="star") if p is not None else ""
            if label and label != "ns":
                ax.text(j, i + 0.28, label, ha="center", va="center", fontsize=8, color=BOARISK_PALETTE["ink"])


def plot_grouped_boxplot(
    data: Any,
    *,
    x: str,
    y: str,
    hue: str | None = None,
    title: str = "Grouped boxplot",
    xlabel: str | None = None,
    ylabel: str | None = None,
    order: Sequence[Any] | None = None,
    hue_order: Sequence[Any] | None = None,
    palette: Sequence[str] | None = None,
    show_points: bool = True,
    point_alpha: float = 0.55,
    random_state: int = 42,
    comparisons: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]] | None = None,
    stat_test: StatTestName = "mannwhitney",
    p_adjust: str = "none",
    annotation_format: AnnotationFormat = "star",
    hide_ns: bool = False,
    return_stats: bool = False,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn | TablePlotReturn:
    """Plot a clinical grouped boxplot with optional hue and jittered patients.

    Parameters
    ----------
    data
        Tabular data coercible to a DataFrame.
    x, y
        Categorical grouping column and numeric value column.
    hue
        Optional second grouping column, for example sex, treatment, cohort, or event status.
    order, hue_order
        Optional display order for the x groups and hue groups.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.ml import plot_grouped_boxplot
    >>> df = pd.DataFrame({"group": ["A", "A", "B"], "sex": ["F", "M", "F"], "sma": [42, 39, 51]})
    >>> fig, ax = plot_grouped_boxplot(df, x="group", y="sma", hue="sex")
    >>> plt.close(fig)
    """
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, y, hue])
    df[y] = pd.to_numeric(df[y], errors="coerce")
    df = df.dropna(subset=[x, y] + ([hue] if hue else []))
    if df.empty:
        raise ValueError("data must contain at least one complete numeric boxplot row.")

    df["_fyron_x"] = df[x].astype(str)
    x_values = _ordered_string_values(df["_fyron_x"], order)
    hue_values = (
        _ordered_string_values(df[hue].astype(str), hue_order) if hue else ["__single__"]
    )
    colors = _resolve_color_sequence(len(hue_values), palette)
    x_positions = np.arange(len(x_values), dtype=float)
    total_width = 0.72
    box_width = total_width / max(len(hue_values), 1)

    if ax is None:
        width = max(5.8, 0.82 * len(x_values) * max(1, len(hue_values)))
        fig, ax = plt.subplots(figsize=(width, 4.8))
    else:
        fig = ax.figure

    rng = np.random.default_rng(random_state)
    legend_handles = []
    positions: dict[tuple[str, str], float] = {}
    heights: dict[tuple[str, str], float] = {}
    for hue_index, hue_value in enumerate(hue_values):
        color = colors[hue_index]
        offset = (hue_index - (len(hue_values) - 1) / 2) * box_width
        for x_index, x_value in enumerate(x_values):
            if hue:
                mask = (df["_fyron_x"] == x_value) & (df[hue].astype(str) == hue_value)
            else:
                mask = df["_fyron_x"] == x_value
            values = df.loc[mask, y].to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            if values.size == 0:
                continue
            position = x_positions[x_index] + offset
            key = (x_value, hue_value)
            positions[key] = float(position)
            heights[key] = float(np.nanmax(values))
            box = ax.boxplot(
                [values],
                positions=[position],
                widths=box_width * 0.78,
                patch_artist=True,
                showfliers=False,
                manage_ticks=False,
            )
            for patch in box["boxes"]:
                patch.set_facecolor(color)
                patch.set_alpha(0.5)
                patch.set_edgecolor(BOARISK_PALETTE["ink"])
                patch.set_linewidth(0.9)
            for element in ["whiskers", "caps", "medians"]:
                for artist in box[element]:
                    artist.set_color(BOARISK_PALETTE["ink"])
                    artist.set_linewidth(1.0 if element != "medians" else 1.6)
            if show_points:
                jitter = rng.normal(position, box_width * 0.08, values.size)
                ax.scatter(
                    jitter,
                    values,
                    s=17,
                    color=color if hue else BOARISK_PALETTE["ink"],
                    alpha=point_alpha,
                    edgecolors="none",
                    zorder=3,
                )
        if hue:
            legend_handles.append(
                plt.Rectangle(
                    (0, 0),
                    1,
                    1,
                    facecolor=color,
                    edgecolor=BOARISK_PALETTE["ink"],
                    alpha=0.5,
                    label=hue_value,
                )
            )

    ax.set_xticks(x_positions, labels=x_values)
    if any(len(label) > 12 for label in x_values):
        ax.tick_params(axis="x", labelrotation=30)
        for label in ax.get_xticklabels():
            label.set_ha("right")
    ax.set_xlabel(xlabel or x.replace("_", " ").title())
    ax.set_ylabel(ylabel or y.replace("_", " ").title())
    ax.set_title(title)
    if hue:
        ax.legend(handles=legend_handles, title=hue, frameon=False)
    stats_table = pd.DataFrame()
    if comparisons is not None or return_stats:
        requested = list(comparisons or _default_annotation_pairs(x_values, hue_values, hue=hue))
        if requested:
            stats_table = stat_test_pairs(
                df,
                x=x,
                y=y,
                hue=hue,
                pairs=requested,
                test=stat_test,
                p_adjust=p_adjust,
                text_format=annotation_format,
                hide_ns=hide_ns,
            )
            add_stat_annotations(ax, stats_table, positions=positions, heights=heights)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    if return_stats:
        return fig, ax, stats_table
    return fig, ax


def plot_density(
    data: Any,
    *,
    x: str,
    hue: str | None = None,
    title: str = "Density plot",
    xlabel: str | None = None,
    ylabel: str = "Density",
    hue_order: Sequence[Any] | None = None,
    palette: Sequence[str] | None = None,
    fill: bool = True,
    alpha: float = 0.22,
    rug: bool = False,
    bandwidth: float | None = None,
    gridsize: int = 256,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot one or more smoothed clinical density curves.

    The implementation uses a lightweight NumPy Gaussian kernel density estimate,
    so the function stays available with the normal ``fyron[ml]`` dependencies.

    Parameters
    ----------
    data
        Tabular data coercible to a DataFrame.
    x
        Numeric variable to plot.
    hue
        Optional grouping column for separate density curves.
    bandwidth
        Optional Gaussian kernel bandwidth. When omitted, Silverman's rule is used.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.ml import plot_density
    >>> df = pd.DataFrame({"score": [0.1, 0.2, 0.3, 0.7, 0.8], "event": [0, 0, 0, 1, 1]})
    >>> fig, ax = plot_density(df, x="score", hue="event")
    >>> plt.close(fig)
    """
    _apply_plot_style()
    if gridsize < 32:
        raise ValueError("gridsize must be at least 32.")
    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, hue])
    df[x] = pd.to_numeric(df[x], errors="coerce")
    df = df.dropna(subset=[x] + ([hue] if hue else []))
    if df.empty:
        raise ValueError("data must contain at least one numeric density row.")

    groups = _ordered_string_values(df[hue].astype(str), hue_order) if hue else ["__all__"]
    all_values = df[x].to_numpy(dtype=float)
    all_values = all_values[np.isfinite(all_values)]
    if all_values.size < 2:
        raise ValueError("density plots require at least two numeric values.")
    value_min = float(np.min(all_values))
    value_max = float(np.max(all_values))
    spread = value_max - value_min
    pad = max(spread * 0.08, float(np.std(all_values, ddof=1)) * 0.3, 1e-6)
    grid = np.linspace(value_min - pad, value_max + pad, gridsize)
    colors = _resolve_color_sequence(len(groups), palette)

    if ax is None:
        fig, ax = plt.subplots(figsize=(6.4, 4.8))
    else:
        fig = ax.figure

    plotted = 0
    for index, group_value in enumerate(groups):
        if hue:
            values = df.loc[df[hue].astype(str) == group_value, x].to_numpy(dtype=float)
            label = group_value
        else:
            values = df[x].to_numpy(dtype=float)
            label = x.replace("_", " ").title()
        values = values[np.isfinite(values)]
        if values.size < 2:
            continue
        density = _gaussian_kde_numpy(values, grid, bandwidth=bandwidth)
        color = colors[index]
        ax.plot(grid, density, color=color, linewidth=2.0, label=label)
        if fill:
            ax.fill_between(grid, density, color=color, alpha=alpha)
        if rug:
            y0 = np.zeros_like(values)
            ax.plot(values, y0 - 0.012 * (index + 1), "|", color=color, alpha=0.55, markersize=8, clip_on=False)
        plotted += 1
    if plotted == 0:
        raise ValueError("no density group contained at least two numeric values.")

    ax.set_xlabel(xlabel or x.replace("_", " ").title())
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if hue:
        ax.legend(title=hue, frameon=False)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_filled_kde(
    data: Any,
    *,
    x: str,
    y: str,
    hue: str | None = None,
    title: str = "Filled KDE plot",
    xlabel: str | None = None,
    ylabel: str | None = None,
    hue_order: Sequence[Any] | None = None,
    palette: str | Sequence[str] | None = None,
    fill: bool = True,
    alpha: float = 0.36,
    levels: int = 8,
    thresh: float = 0.05,
    bandwidth: float | tuple[float, float] | None = None,
    gridsize: int = 96,
    show_points: bool = False,
    point_size: float = 10,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot filled two-dimensional Gaussian KDE contours.

    This Matplotlib-native helper mirrors the common Seaborn pattern
    ``sns.kdeplot(data=df, x=..., y=..., hue=..., fill=True)`` while keeping
    Fyron's core plotting stack free of a Seaborn dependency.

    Parameters
    ----------
    data
        Tabular data coercible to a DataFrame.
    x
        Numeric column plotted on the horizontal axis.
    y
        Numeric column plotted on the vertical axis.
    hue
        Optional categorical column for separate filled KDE contours.
    title
        Plot title.
    xlabel
        Optional x-axis label. Defaults to a title-cased version of ``x``.
    ylabel
        Optional y-axis label. Defaults to a title-cased version of ``y``.
    hue_order
        Optional explicit order for hue groups.
    palette
        Named Fyron palette or explicit color sequence.
    fill
        If True, draw filled contours. If False, draw contour lines only.
    alpha
        Fill transparency.
    levels
        Number of contour levels to draw.
    thresh
        Relative density threshold between 0 and 1 for the first contour.
    bandwidth
        Optional shared bandwidth or ``(x_bandwidth, y_bandwidth)`` tuple.
        When omitted, a Scott-style rule is used for each axis.
    gridsize
        Number of grid points per axis used to evaluate the density.
    show_points
        If True, overlay source points.
    point_size
        Marker size used when ``show_points`` is True.
    ax
        Optional Matplotlib axes to draw into.
    save_path
        Optional path for saving the figure.
    fmt
        Output format used when ``save_path`` is provided.
    """
    _apply_plot_style()
    if gridsize < 32:
        raise ValueError("gridsize must be at least 32.")
    if levels < 2:
        raise ValueError("levels must be at least 2.")
    if not 0 <= thresh < 1:
        raise ValueError("thresh must be in the interval [0, 1).")
    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, y, hue])
    df[x] = pd.to_numeric(df[x], errors="coerce")
    df[y] = pd.to_numeric(df[y], errors="coerce")
    df = df.dropna(subset=[x, y] + ([hue] if hue else []))
    if df.empty:
        raise ValueError("data must contain at least one complete numeric KDE row.")

    groups = _ordered_string_values(df[hue].astype(str), hue_order) if hue else ["__all__"]
    complete = df[[x, y]].to_numpy(dtype=float)
    complete = complete[np.isfinite(complete).all(axis=1)]
    if complete.shape[0] < 3:
        raise ValueError("filled KDE plots require at least three complete numeric rows.")

    x_min, x_max = float(np.min(complete[:, 0])), float(np.max(complete[:, 0]))
    y_min, y_max = float(np.min(complete[:, 1])), float(np.max(complete[:, 1]))
    x_spread = x_max - x_min
    y_spread = y_max - y_min
    x_pad = max(x_spread * 0.08, float(np.std(complete[:, 0], ddof=1)) * 0.3, 1e-6)
    y_pad = max(y_spread * 0.08, float(np.std(complete[:, 1], ddof=1)) * 0.3, 1e-6)
    x_axis = np.linspace(x_min - x_pad, x_max + x_pad, gridsize)
    y_axis = np.linspace(y_min - y_pad, y_max + y_pad, gridsize)
    x_grid, y_grid = np.meshgrid(x_axis, y_axis)
    colors = _resolve_color_sequence(len(groups), palette)

    if ax is None:
        fig, ax = plt.subplots(figsize=(6.4, 5.2))
    else:
        fig = ax.figure

    handles: list[Line2D] = []
    plotted = 0
    for index, group_value in enumerate(groups):
        if hue:
            group_df = df.loc[df[hue].astype(str) == group_value]
            label = group_value
        else:
            group_df = df
            label = f"{x} vs {y}"
        values = group_df[[x, y]].to_numpy(dtype=float)
        values = values[np.isfinite(values).all(axis=1)]
        if values.shape[0] < 3:
            continue
        density = _gaussian_kde_2d_numpy(
            values[:, 0],
            values[:, 1],
            x_grid,
            y_grid,
            bandwidth=bandwidth,
        )
        max_density = float(np.nanmax(density))
        if not np.isfinite(max_density) or max_density <= 0:
            continue
        contour_levels = np.linspace(max_density * thresh, max_density, levels)
        color = colors[index]
        if fill:
            ax.contourf(
                x_grid,
                y_grid,
                density,
                levels=contour_levels,
                colors=[color],
                alpha=alpha,
            )
            ax.contour(
                x_grid,
                y_grid,
                density,
                levels=contour_levels,
                colors=[color],
                linewidths=0.75,
                alpha=min(alpha + 0.35, 0.9),
            )
        else:
            ax.contour(
                x_grid,
                y_grid,
                density,
                levels=contour_levels,
                colors=[color],
                linewidths=1.35,
            )
        if show_points:
            ax.scatter(
                values[:, 0],
                values[:, 1],
                s=point_size,
                color=color,
                alpha=0.32,
                edgecolors="none",
            )
        handles.append(Line2D([0], [0], color=color, linewidth=3, label=label))
        plotted += 1
    if plotted == 0:
        raise ValueError("no KDE group contained at least three complete numeric rows.")

    ax.set_xlabel(xlabel or x.replace("_", " ").title())
    ax.set_ylabel(ylabel or y.replace("_", " ").title())
    ax.set_title(title)
    if hue:
        ax.legend(handles=handles, title=hue, frameon=False)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_histogram(
    data: Any,
    *,
    x: str,
    hue: str | None = None,
    group: str | None = None,
    bins: int | str | Sequence[float] = "auto",
    stat: Literal["count", "density", "percent"] = "count",
    multiple: Literal["layer", "stack", "dodge"] = "layer",
    title: str = "Histogram",
    xlabel: str | None = None,
    ylabel: str | None = None,
    hue_order: Sequence[Any] | None = None,
    palette: Sequence[str] | None = None,
    alpha: float = 0.55,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot manuscript-friendly histograms with optional hue/group strata."""

    _apply_plot_style()
    if stat not in {"count", "density", "percent"}:
        raise ValueError("stat must be 'count', 'density', or 'percent'.")
    if multiple not in {"layer", "stack", "dodge"}:
        raise ValueError("multiple must be 'layer', 'stack', or 'dodge'.")
    hue_col = hue or group
    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, hue_col])
    df[x] = pd.to_numeric(df[x], errors="coerce")
    df = df.dropna(subset=[x] + ([hue_col] if hue_col else []))
    if df.empty:
        raise ValueError("data must contain at least one numeric histogram row.")
    groups = _ordered_string_values(df[hue_col].astype(str), hue_order) if hue_col else ["__all__"]
    colors = _resolve_color_sequence(len(groups), palette)
    values_by_group = [df.loc[df[hue_col].astype(str) == g, x].to_numpy(dtype=float) if hue_col else df[x].to_numpy(dtype=float) for g in groups]
    all_values = np.concatenate([v[np.isfinite(v)] for v in values_by_group])
    edges = np.histogram_bin_edges(all_values, bins=bins)
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.4, 4.6))
    else:
        fig = ax.figure
    if multiple == "stack" and hue_col:
        weights = None
        if stat == "percent":
            weights = [np.ones_like(v) * 100.0 / max(len(all_values), 1) for v in values_by_group]
        ax.hist(values_by_group, bins=edges, stacked=True, density=stat == "density", color=colors, label=groups, edgecolor=BOARISK_PALETTE["ink"], linewidth=0.55, weights=weights)
    elif multiple == "dodge" and hue_col:
        width = np.diff(edges)
        centers = edges[:-1] + width / 2.0
        for i, (g, values) in enumerate(zip(groups, values_by_group)):
            counts, _ = np.histogram(values, bins=edges, density=stat == "density")
            if stat == "percent":
                counts = counts * 100.0 / max(len(values), 1)
            bar_width = width / len(groups)
            ax.bar(centers - width / 2 + i * bar_width + bar_width / 2, counts, width=bar_width * 0.94, color=colors[i], alpha=alpha, edgecolor=BOARISK_PALETTE["ink"], linewidth=0.55, label=g)
    else:
        for i, (g, values) in enumerate(zip(groups, values_by_group)):
            weights = np.ones_like(values) * 100.0 / max(len(values), 1) if stat == "percent" else None
            ax.hist(values, bins=edges, density=stat == "density", weights=weights, color=colors[i], alpha=alpha, edgecolor=BOARISK_PALETTE["ink"], linewidth=0.55, label=None if not hue_col else g)
    ax.set_xlabel(xlabel or x.replace("_", " ").title())
    ax.set_ylabel(ylabel or ("Percent" if stat == "percent" else stat.title()))
    ax.set_title(title)
    if hue_col:
        ax.legend(title=hue_col, frameon=False)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_swarmplot(
    data: Any,
    *,
    x: str,
    y: str,
    hue: str | None = None,
    order: Sequence[Any] | None = None,
    hue_order: Sequence[Any] | None = None,
    dodge: bool = True,
    title: str = "Swarm plot",
    xlabel: str | None = None,
    ylabel: str | None = None,
    palette: Sequence[str] | None = None,
    point_size: float = 24,
    point_alpha: float = 0.72,
    random_state: int = 42,
    comparisons: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]] | None = None,
    stat_test: StatTestName = "mannwhitney",
    p_adjust: str = "none",
    annotation_format: AnnotationFormat = "star",
    hide_ns: bool = False,
    return_stats: bool = False,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn | TablePlotReturn:
    """Plot patient-level values with jitter/dodge and optional statistics."""

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, y, hue])
    df[y] = pd.to_numeric(df[y], errors="coerce")
    df = df.dropna(subset=[x, y] + ([hue] if hue else []))
    if df.empty:
        raise ValueError("data must contain at least one complete numeric swarm row.")
    df["_fyron_x"] = df[x].astype(str)
    x_values = _ordered_string_values(df["_fyron_x"], order)
    hue_values = _ordered_string_values(df[hue].astype(str), hue_order) if hue else ["__single__"]
    colors = _resolve_color_sequence(len(hue_values), palette)
    x_positions = np.arange(len(x_values), dtype=float)
    width = 0.64 / max(len(hue_values), 1) if dodge else 0.16
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(5.8, 0.82 * len(x_values) * max(1, len(hue_values))), 4.8))
    else:
        fig = ax.figure
    rng = np.random.default_rng(random_state)
    positions: dict[tuple[str, str], float] = {}
    heights: dict[tuple[str, str], float] = {}
    for hue_index, hue_value in enumerate(hue_values):
        offset = (hue_index - (len(hue_values) - 1) / 2) * width if hue and dodge else 0.0
        for x_index, x_value in enumerate(x_values):
            mask = df["_fyron_x"] == x_value
            if hue:
                mask &= df[hue].astype(str) == hue_value
            values = df.loc[mask, y].to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            if values.size == 0:
                continue
            center = x_positions[x_index] + offset
            positions[(x_value, hue_value)] = float(center)
            heights[(x_value, hue_value)] = float(np.nanmax(values))
            jitter = rng.normal(center, width * 0.16, values.size)
            ax.scatter(jitter, values, s=point_size, color=colors[hue_index], alpha=point_alpha, edgecolors=BOARISK_PALETTE["ink"], linewidths=0.35, label=hue_value if hue and x_index == 0 else None)
    ax.set_xticks(x_positions, labels=x_values)
    ax.set_xlabel(xlabel or x.replace("_", " ").title())
    ax.set_ylabel(ylabel or y.replace("_", " ").title())
    ax.set_title(title)
    if hue:
        ax.legend(title=hue, frameon=False)
    stats_table = pd.DataFrame()
    if comparisons is not None or return_stats:
        requested = list(comparisons or _default_annotation_pairs(x_values, hue_values, hue=hue))
        if requested:
            stats_table = stat_test_pairs(df, x=x, y=y, hue=hue, pairs=requested, test=stat_test, p_adjust=p_adjust, text_format=annotation_format, hide_ns=hide_ns)
            add_stat_annotations(ax, stats_table, positions=positions, heights=heights)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    if return_stats:
        return fig, ax, stats_table
    return fig, ax


def plot_patterned_bar(
    data: Any,
    *,
    x: str,
    y: str,
    group: str | None = None,
    error: str | None = None,
    title: str = "Bar plot",
    xlabel: str | None = None,
    ylabel: str | None = None,
    orientation: Orientation = "vertical",
    palette: Sequence[str] | None = None,
    hatches: Sequence[str] | None = None,
    annotate: bool = False,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot grouped bars with hatch patterns for grayscale-safe figures.

    Parameters
    ----------
    data
        Tabular data coercible to a DataFrame.
    x, y
        Category and value columns.
    group
        Optional grouping column. Each group receives a distinct color/hatch.
    error
        Optional symmetric error-bar column.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.ml import plot_patterned_bar
    >>> df = pd.DataFrame({"model": ["RF", "XGB"], "auc": [0.82, 0.86]})
    >>> fig, ax = plot_patterned_bar(df, x="model", y="auc")
    >>> plt.close(fig)
    """
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    required = [x, y] + ([group] if group else []) + ([error] if error else [])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"columns not found in data: {missing}")
    if df.empty:
        raise ValueError("data must contain at least one row.")

    x_values = list(dict.fromkeys(df[x].astype(str)))
    groups = list(dict.fromkeys(df[group].astype(str))) if group else ["__single__"]
    colors = _resolve_color_sequence(len(groups), palette)
    patterns = _resolve_hatch_sequence(len(groups), hatches)
    positions = np.arange(len(x_values), dtype=float)
    total_width = 0.8
    bar_width = total_width / len(groups)

    if ax is None:
        width = max(5.5, 0.65 * len(x_values) * max(1, len(groups)))
        fig, ax = plt.subplots(figsize=(width, 4.8))
    else:
        fig = ax.figure

    for idx, group_value in enumerate(groups):
        if group:
            sub = df[df[group].astype(str) == group_value]
        else:
            sub = df
        y_lookup = {str(row[x]): float(row[y]) for _, row in sub.iterrows()}
        err_lookup = (
            {str(row[x]): float(row[error]) for _, row in sub.iterrows()} if error else None
        )
        heights = [y_lookup.get(v, np.nan) for v in x_values]
        yerr = [err_lookup.get(v, 0.0) for v in x_values] if err_lookup else None
        offset = (idx - (len(groups) - 1) / 2) * bar_width
        bar_pos = positions + offset
        label = group_value if group else None
        if orientation == "vertical":
            bars = ax.bar(
                bar_pos,
                heights,
                width=bar_width * 0.92,
                yerr=yerr,
                label=label,
                color=colors[idx],
                edgecolor="black",
                linewidth=0.8,
                hatch=patterns[idx],
                capsize=3 if yerr is not None else 0,
            )
            if annotate:
                ax.bar_label(bars, fmt="%.2g", padding=3, fontsize=9)
        elif orientation == "horizontal":
            bars = ax.barh(
                bar_pos,
                heights,
                height=bar_width * 0.92,
                xerr=yerr,
                label=label,
                color=colors[idx],
                edgecolor="black",
                linewidth=0.8,
                hatch=patterns[idx],
                capsize=3 if yerr is not None else 0,
            )
            if annotate:
                ax.bar_label(bars, fmt="%.2g", padding=3, fontsize=9)
        else:
            raise ValueError("orientation must be 'vertical' or 'horizontal'.")

    if orientation == "vertical":
        ax.set_xticks(positions, labels=x_values, rotation=0)
        ax.set_xlabel(xlabel or x)
        ax.set_ylabel(ylabel or y)
    else:
        ax.set_yticks(positions, labels=x_values)
        ax.set_ylabel(xlabel or x)
        ax.set_xlabel(ylabel or y)
    ax.set_title(title)
    if group:
        ax.legend(title=group)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_likert_scale(
    data: Any,
    *,
    item_col: str = "item",
    response_col: str = "response",
    count_col: str | None = None,
    order: Sequence[Any] | None = None,
    response_order: Sequence[Any] | None = None,
    neutral_values: Sequence[Any] | None = None,
    normalize: bool = True,
    palette: str | Sequence[str] | None = "okabe_ito",
    title: str | None = None,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> TablePlotReturn:
    """Plot a diverging Likert scale summary.

    Parameters
    ----------
    data
        Long table with one row per response or one row per response count.
    item_col, response_col
        Columns containing survey item names and ordered Likert responses.
    count_col
        Optional count column. If omitted, rows are counted.
    order, response_order
        Explicit item and response order for stable manuscript figures.
    neutral_values
        Responses that should be centered around zero. If omitted and the
        response order has odd length, the middle response is treated as neutral.
    normalize
        If True, show percentages per item. If False, show counts.

    Returns
    -------
    tuple
        ``(fig, ax, table)`` where ``table`` contains counts, percentages, and
        the assigned negative/neutral/positive side for each response.
    """

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    required = [item_col, response_col] + ([count_col] if count_col else [])
    _require_columns(df, required)
    df = df.dropna(subset=[item_col, response_col])
    if df.empty:
        raise ValueError("data must contain at least one Likert response.")
    if count_col is None:
        grouped = df.groupby([item_col, response_col], dropna=False).size().reset_index(name="count")
    else:
        grouped = df.copy()
        grouped[count_col] = pd.to_numeric(grouped[count_col], errors="coerce")
        grouped = grouped.dropna(subset=[count_col])
        grouped = (
            grouped.groupby([item_col, response_col], dropna=False)[count_col]
            .sum()
            .reset_index(name="count")
        )
    grouped["count"] = grouped["count"].astype(float)
    if (grouped["count"] < 0).any():
        raise ValueError("Likert counts must be non-negative.")

    items = [str(value) for value in (order if order is not None else dict.fromkeys(grouped[item_col].astype(str)))]
    responses = [
        str(value)
        for value in (
            response_order
            if response_order is not None
            else dict.fromkeys(grouped[response_col].astype(str))
        )
    ]
    if not items or not responses:
        raise ValueError("data must contain at least one item and one response category.")
    neutral = {str(value) for value in neutral_values} if neutral_values is not None else set()
    if neutral_values is None and len(responses) % 2 == 1:
        neutral.add(responses[len(responses) // 2])
    response_index = {response: index for index, response in enumerate(responses)}
    neutral_indices = [response_index[value] for value in neutral if value in response_index]
    center = float(np.mean(neutral_indices)) if neutral_indices else (len(responses) - 1) / 2

    full = pd.MultiIndex.from_product([items, responses], names=[item_col, response_col]).to_frame(index=False)
    grouped[item_col] = grouped[item_col].astype(str)
    grouped[response_col] = grouped[response_col].astype(str)
    table = full.merge(grouped, on=[item_col, response_col], how="left")
    table["count"] = table["count"].fillna(0.0)
    totals = table.groupby(item_col)["count"].transform("sum")
    table["percent"] = np.where(totals > 0, table["count"] / totals * 100.0, 0.0)
    table["response_order"] = table[response_col].map(response_index)
    table["side"] = np.where(
        table[response_col].isin(neutral),
        "neutral",
        np.where(table["response_order"] < center, "negative", "positive"),
    )
    table["plot_value"] = table["percent"] if normalize else table["count"]

    colors = _resolve_color_sequence(len(responses), palette)
    color_lookup = {response: colors[index] for index, response in enumerate(responses)}
    for neutral_value in neutral:
        if neutral_value in color_lookup:
            color_lookup[neutral_value] = "#D1D5DB"

    if ax is None:
        fig, ax = plt.subplots(figsize=(7.2, max(3.2, 0.56 * len(items) + 1.2)))
    else:
        fig = ax.figure
    y_positions = np.arange(len(items), dtype=float)
    max_extent = 0.0
    for y_pos, item in zip(y_positions, items, strict=True):
        sub = table[table[item_col] == item]
        neutral_width = float(sub.loc[sub["side"] == "neutral", "plot_value"].sum())
        if neutral_width > 0:
            ax.barh(
                y_pos,
                neutral_width,
                left=-neutral_width / 2,
                color="#D1D5DB",
                edgecolor="#111827",
                linewidth=0.45,
            )
        neg_left = -neutral_width / 2
        for response in reversed([r for r in responses if r not in neutral and response_index[r] < center]):
            value = float(sub.loc[sub[response_col] == response, "plot_value"].sum())
            if value <= 0:
                continue
            ax.barh(
                y_pos,
                value,
                left=neg_left - value,
                color=color_lookup[response],
                edgecolor="#111827",
                linewidth=0.45,
                label=response,
            )
            neg_left -= value
        pos_left = neutral_width / 2
        for response in [r for r in responses if r not in neutral and response_index[r] > center]:
            value = float(sub.loc[sub[response_col] == response, "plot_value"].sum())
            if value <= 0:
                continue
            ax.barh(
                y_pos,
                value,
                left=pos_left,
                color=color_lookup[response],
                edgecolor="#111827",
                linewidth=0.45,
                label=response,
            )
            pos_left += value
        max_extent = max(max_extent, abs(neg_left), abs(pos_left))

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=color_lookup[response], edgecolor="#111827", label=response)
        for response in responses
    ]
    ax.axvline(0, color="#111827", linewidth=0.9)
    ax.set_yticks(y_positions, labels=items)
    ax.invert_yaxis()
    ax.set_xlabel("Percent of responses" if normalize else "Response count")
    ax.set_title(title or "Likert scale")
    ax.set_xlim(-max_extent * 1.08, max_extent * 1.08)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{abs(value):.0f}"))
    ax.legend(
        handles=handles,
        title="Response",
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        frameon=False,
        fontsize=9,
        title_fontsize=9,
    )
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax, table


def plot_waffle(
    data: Any,
    *,
    category_col: str = "category",
    value_col: str = "value",
    total: int = 100,
    rows: int = 10,
    palette: str | Sequence[str] | None = "bf_vibrant_muted",
    title: str | None = None,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> TablePlotReturn:
    """Plot a waffle chart for cohort composition or endpoint mix.

    Parameters
    ----------
    data
        Table with category labels and non-negative values.
    category_col, value_col
        Columns containing categories and values to allocate into waffle cells.
    total
        Number of cells in the waffle chart.
    rows
        Number of waffle rows. Columns are derived from ``total`` and ``rows``.

    Returns
    -------
    tuple
        ``(fig, ax, table)`` where ``table`` contains category proportions,
        allocated cell counts, and source values.
    """

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [category_col, value_col])
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[category_col, value_col])
    if df.empty:
        raise ValueError("data must contain at least one waffle category.")
    if total <= 0 or rows <= 0:
        raise ValueError("total and rows must be positive integers.")
    if (df[value_col] < 0).any():
        raise ValueError("waffle values must be non-negative.")
    summary = df.groupby(category_col, dropna=False)[value_col].sum().reset_index()
    value_sum = float(summary[value_col].sum())
    if value_sum <= 0:
        raise ValueError("waffle values must sum to a positive number.")

    raw_cells = summary[value_col].to_numpy(dtype=float) / value_sum * total
    cells = np.floor(raw_cells).astype(int)
    remainder = int(total - cells.sum())
    if remainder > 0:
        order = np.argsort(-(raw_cells - cells))
        for index in order[:remainder]:
            cells[index] += 1
    elif remainder < 0:
        order = np.argsort(raw_cells - cells)
        for index in order[: abs(remainder)]:
            cells[index] -= 1
    summary["proportion"] = summary[value_col] / value_sum
    summary["cells"] = cells

    cols = int(np.ceil(total / rows))
    colors = _resolve_color_sequence(len(summary), palette)
    assignments: list[int] = []
    for index, count in enumerate(cells):
        assignments.extend([index] * int(count))
    assignments = assignments[:total]
    while len(assignments) < total:
        assignments.append(-1)

    if ax is None:
        fig, ax = plt.subplots(figsize=(max(4.8, cols * 0.34 + 2.2), rows * 0.32 + 1.5))
    else:
        fig = ax.figure
    for cell_index, category_index in enumerate(assignments):
        row = rows - 1 - (cell_index // cols)
        col = cell_index % cols
        face = "#F3F4F6" if category_index < 0 else colors[category_index]
        ax.add_patch(
            plt.Rectangle(
                (col, row),
                0.88,
                0.88,
                facecolor=face,
                edgecolor="#111827",
                linewidth=0.35,
            )
        )
    ax.set_xlim(-0.05, cols)
    ax.set_ylim(-0.05, rows)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(title or "Waffle plot", loc="left")
    handles = [
        plt.Rectangle(
            (0, 0),
            1,
            1,
            facecolor=colors[index],
            edgecolor="#111827",
            label=f"{row[category_col]} ({row['proportion']:.0%})",
        )
        for index, row in summary.iterrows()
    ]
    ax.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=min(2, len(handles)),
        frameon=False,
        fontsize=9,
    )
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax, summary


def plot_metric_bars(
    metrics: Mapping[str, Mapping[str, float]] | pd.DataFrame,
    *,
    metrics_to_plot: Sequence[str] | None = None,
    model_col: str = "model",
    title: str = "Model metrics",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot model metrics with grouped patterned bars.

    ``metrics`` may be a nested mapping like ``{"RF": {"auc": 0.82}}`` or a
    DataFrame with one row per model.

    Examples
    --------
    >>> from fyron.ml import plot_metric_bars
    >>> fig, ax = plot_metric_bars({"RF": {"auc": 0.8, "f1": 0.7}})
    >>> plt.close(fig)
    """
    if isinstance(metrics, pd.DataFrame):
        wide = metrics.copy()
        if model_col not in wide.columns:
            raise ValueError(f"metrics DataFrame must contain {model_col!r}.")
    else:
        wide = pd.DataFrame.from_dict(metrics, orient="index").reset_index()
        wide = wide.rename(columns={"index": model_col})
    metric_cols = [
        c
        for c in wide.columns
        if c != model_col and pd.api.types.is_numeric_dtype(wide[c])
    ]
    if metrics_to_plot is not None:
        missing = [m for m in metrics_to_plot if m not in metric_cols]
        if missing:
            raise ValueError(f"metrics not found or non-numeric: {missing}")
        metric_cols = list(metrics_to_plot)
    if not metric_cols:
        raise ValueError("No numeric metric columns available to plot.")
    long = wide.melt(
        id_vars=[model_col],
        value_vars=metric_cols,
        var_name="metric",
        value_name="value",
    )
    return plot_patterned_bar(
        long,
        x="metric",
        y="value",
        group=model_col,
        title=title,
        xlabel="Metric",
        ylabel="Value",
        annotate=True,
        ax=ax,
        save_path=save_path,
        fmt=fmt,
    )


def plot_risk_score_distribution(
    data: Any,
    *,
    risk_col: str = "risk_score",
    event_col: str | None = None,
    event_labels: Mapping[Any, str] | Sequence[str] | None = None,
    title: str = "Risk score distribution",
    ylabel: str | None = None,
    jitter: bool = True,
    violin: bool = True,
    palette: Sequence[str] | None = None,
    random_state: int = 42,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot risk scores as a BOARISK-style violin/jitter distribution.

    ``event_col`` is optional. When provided, Fyron draws one distribution per
    event group, which is useful for checking whether a clinical score separates
    patients with observed events from censored or non-event patients.
    """
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [risk_col, event_col])
    df[risk_col] = pd.to_numeric(df[risk_col], errors="coerce")
    df = df.dropna(subset=[risk_col])
    if df.empty:
        raise ValueError("data must contain at least one numeric risk score.")

    if event_col is None:
        group_values = ["__all__"]
        group_labels = [risk_col.replace("_", " ").title()]
        groups = [df[risk_col].to_numpy(dtype=float)]
    else:
        df = df.dropna(subset=[event_col])
        if df.empty:
            raise ValueError("data must contain at least one non-missing event group.")
        group_values = list(dict.fromkeys(sorted(df[event_col].unique())))
        if isinstance(event_labels, Mapping):
            group_labels = [str(event_labels.get(value, value)) for value in group_values]
        elif event_labels is not None:
            labels = list(event_labels)
            group_labels = [
                str(labels[index]) if index < len(labels) else str(value)
                for index, value in enumerate(group_values)
            ]
        else:
            default_labels = {0: "Censored", 1: "Event", False: "Censored", True: "Event"}
            group_labels = [str(default_labels.get(value, value)) for value in group_values]
        groups = [
            df.loc[df[event_col] == value, risk_col].to_numpy(dtype=float)
            for value in group_values
        ]

    positions = np.arange(1, len(groups) + 1)
    colors = _resolve_color_sequence(len(groups), palette)
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(5.2, 1.25 * len(groups)), 4.8))
    else:
        fig = ax.figure

    if violin:
        parts = ax.violinplot(
            groups,
            positions=positions,
            widths=0.75,
            showmeans=False,
            showmedians=True,
            showextrema=False,
        )
        for body, color in zip(parts["bodies"], colors):
            body.set_facecolor(color)
            body.set_edgecolor(BOARISK_PALETTE["ink"])
            body.set_alpha(0.48)
            body.set_linewidth(0.9)
        if "cmedians" in parts:
            parts["cmedians"].set_color(BOARISK_PALETTE["ink"])
            parts["cmedians"].set_linewidth(1.8)
    else:
        box = ax.boxplot(groups, positions=positions, widths=0.55, patch_artist=True)
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.45)
            patch.set_edgecolor(BOARISK_PALETTE["ink"])

    if jitter:
        rng = np.random.default_rng(random_state)
        for index, values in enumerate(groups, start=1):
            x = rng.normal(index, 0.055, len(values))
            ax.scatter(
                x,
                values,
                s=18,
                color=BOARISK_PALETTE["ink"],
                alpha=0.58,
                linewidths=0,
                zorder=3,
            )

    ax.set_xticks(positions, labels=group_labels)
    ax.set_ylabel(ylabel or risk_col.replace("_", " ").title())
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_signed_feature_weights(
    data: Any,
    *,
    feature_col: str = "feature",
    weight_col: str = "coef",
    top_n: int = 20,
    title: str = "Signed feature weights",
    xlabel: str = "Model coefficient",
    positive_label: str = "Higher risk",
    negative_label: str = "Lower risk",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot signed coefficients or feature weights with BOARISK hatches."""
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [feature_col, weight_col])
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    df = df.dropna(subset=[feature_col, weight_col])
    if df.empty:
        raise ValueError("data must contain at least one numeric feature weight.")
    df["_abs_weight"] = df[weight_col].abs()
    df = df.sort_values("_abs_weight", ascending=False).head(top_n)
    df = df.sort_values(weight_col, ascending=True)

    colors = np.where(
        df[weight_col].to_numpy(dtype=float) >= 0,
        BOARISK_PALETTE["red"],
        BOARISK_PALETTE["blue"],
    )
    hatches = ["///" if value >= 0 else "\\\\\\" for value in df[weight_col]]
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.2, max(4.0, 0.34 * len(df))))
    else:
        fig = ax.figure
    bars = ax.barh(
        df[feature_col].astype(str),
        df[weight_col],
        color=colors,
        edgecolor=BOARISK_PALETTE["ink"],
        linewidth=0.75,
    )
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    ax.axvline(0, color=BOARISK_PALETTE["ink"], linewidth=1.0)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, facecolor=BOARISK_PALETTE["blue"], edgecolor="black", hatch="\\\\\\", label=negative_label),
            plt.Rectangle((0, 0), 1, 1, facecolor=BOARISK_PALETTE["red"], edgecolor="black", hatch="///", label=positive_label),
        ],
        frameon=False,
        loc="lower right",
    )
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_significance_bars(
    data: Any,
    *,
    label_col: str = "label",
    p_col: str = "p_value",
    threshold: float = 0.05,
    title: str = "Statistical significance",
    xlabel: str = "-log10(p)",
    annotate: bool = True,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> TablePlotReturn:
    """Plot p-values as ``-log10(p)`` bars and return the computed table."""
    _apply_plot_style()
    if threshold <= 0 or threshold > 1:
        raise ValueError("threshold must be in the interval (0, 1].")
    df = pd.DataFrame(data).copy()
    _require_columns(df, [label_col, p_col])
    df[p_col] = pd.to_numeric(df[p_col], errors="coerce")
    df = df.dropna(subset=[label_col, p_col])
    df = df[df[p_col] > 0].copy()
    if df.empty:
        raise ValueError("data must contain at least one positive numeric p-value.")
    df["minus_log10_p"] = -np.log10(np.clip(df[p_col].to_numpy(dtype=float), 1e-300, 1.0))
    df = df.sort_values("minus_log10_p", ascending=True)

    colors = [
        BOARISK_PALETTE["orange"] if p < threshold else BOARISK_PALETTE["purple"]
        for p in df[p_col]
    ]
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.0, max(3.8, 0.36 * len(df))))
    else:
        fig = ax.figure
    bars = ax.barh(
        df[label_col].astype(str),
        df["minus_log10_p"],
        color=colors,
        edgecolor=BOARISK_PALETTE["ink"],
        linewidth=0.75,
    )
    for index, bar in enumerate(bars):
        bar.set_hatch(DEFAULT_HATCHES[index % len(DEFAULT_HATCHES)])
    cutoff = -np.log10(threshold)
    ax.axvline(cutoff, color=BOARISK_PALETTE["ink"], linestyle="--", linewidth=1)
    ax.text(
        cutoff,
        1.01,
        f"p = {threshold:g}",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="bottom",
        fontsize=8,
        color=BOARISK_PALETTE["muted"],
    )
    if annotate:
        x_pad = max(df["minus_log10_p"].max() * 0.015, 0.03)
        for y_pos, (_, row) in enumerate(df.iterrows()):
            ax.text(
                row["minus_log10_p"] + x_pad,
                y_pos,
                _p_value_label(row[p_col]),
                va="center",
                fontsize=8,
                color=BOARISK_PALETTE["muted"],
            )
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax, df


def plot_volcano(
    data: Any,
    *,
    feature_col: str = "feature",
    effect_col: str = "log2_fold_change",
    p_col: str = "p_value",
    group_col: str | None = None,
    p_threshold: float = 0.05,
    effect_threshold: float = 1.0,
    top_n_labels: int = 8,
    title: str = "Volcano plot",
    xlabel: str | None = None,
    ylabel: str = "-log10(p)",
    palette: str | Sequence[str] | None = "bf_vibrant_muted",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot feature effects against statistical significance."""
    _apply_plot_style()
    if not 0 < p_threshold <= 1:
        raise ValueError("p_threshold must be in the interval (0, 1].")
    df = pd.DataFrame(data).copy()
    _require_columns(df, [feature_col, effect_col, p_col, group_col])
    df[effect_col] = pd.to_numeric(df[effect_col], errors="coerce")
    df[p_col] = pd.to_numeric(df[p_col], errors="coerce")
    df = df.dropna(subset=[feature_col, effect_col, p_col])
    df = df[df[p_col] > 0].copy()
    if df.empty:
        raise ValueError("data must contain at least one positive p-value and numeric effect row.")
    df["_minus_log10_p"] = -np.log10(np.clip(df[p_col].to_numpy(dtype=float), 1e-300, 1.0))
    df["_significant"] = (df[p_col] <= p_threshold) & (df[effect_col].abs() >= effect_threshold)

    if ax is None:
        fig, ax = plt.subplots(figsize=(7.0, 4.8))
    else:
        fig = ax.figure

    if group_col is None:
        colors = np.where(df["_significant"], BOARISK_PALETTE["red"], BOARISK_PALETTE["muted"])
        ax.scatter(df[effect_col], df["_minus_log10_p"], s=28, c=colors, alpha=0.82, edgecolors="none")
    else:
        groups = _ordered_string_values(df[group_col].astype(str))
        colors = _resolve_color_sequence(len(groups), palette)
        for group, color in zip(groups, colors):
            subset = df[df[group_col].astype(str) == group]
            ax.scatter(subset[effect_col], subset["_minus_log10_p"], s=28, color=color, alpha=0.82, edgecolors="none", label=group)
        ax.legend(frameon=False, loc="upper right")
    ax.axhline(-np.log10(p_threshold), color=BOARISK_PALETTE["ink"], linestyle="--", linewidth=0.9)
    ax.axvline(-effect_threshold, color=BOARISK_PALETTE["muted"], linestyle=":", linewidth=0.9)
    ax.axvline(effect_threshold, color=BOARISK_PALETTE["muted"], linestyle=":", linewidth=0.9)
    if top_n_labels:
        label_rows = df.sort_values(["_significant", "_minus_log10_p"], ascending=[False, False]).head(top_n_labels)
        for _, row in label_rows.iterrows():
            ax.text(row[effect_col], row["_minus_log10_p"], str(row[feature_col]), fontsize=8, color=BOARISK_PALETTE["ink"], ha="left", va="bottom")
    ax.set_xlabel(xlabel or effect_col.replace("_", " ").title())
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_swimmer(
    data: Any,
    *,
    patient_col: str = "patient",
    start_col: str = "start",
    end_col: str = "end",
    group_col: str | None = None,
    event_time_col: str | None = "event_time",
    event_col: str | None = "event",
    title: str = "Swimmer plot",
    xlabel: str = "Time",
    palette: str | Sequence[str] | None = "bf_vibrant_muted",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot patient-level duration bars with optional event markers."""
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [patient_col, start_col, end_col, group_col, event_time_col, event_col])
    for col in [start_col, end_col, event_time_col]:
        if col is not None and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[patient_col, start_col, end_col])
    if df.empty:
        raise ValueError("data must contain at least one complete swimmer row.")
    df = df.sort_values([group_col, end_col] if group_col else [end_col], ascending=True)
    patients = df[patient_col].astype(str).to_list()
    y_pos = np.arange(len(df))
    colors = _resolve_color_sequence(len(df[group_col].astype(str).unique()) if group_col else 1, palette)
    color_lookup = dict(zip(_ordered_string_values(df[group_col].astype(str)) if group_col else ["__single__"], colors))
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.2, max(3.8, 0.36 * len(df))))
    else:
        fig = ax.figure
    for y, (_, row) in zip(y_pos, df.iterrows()):
        group = str(row[group_col]) if group_col else "__single__"
        ax.barh(y, row[end_col] - row[start_col], left=row[start_col], height=0.62, color=color_lookup[group], edgecolor=BOARISK_PALETTE["ink"], linewidth=0.75, alpha=0.72)
        if event_time_col and event_col and pd.notna(row.get(event_time_col)):
            ax.scatter(row[event_time_col], y, s=42, color=BOARISK_PALETTE["ink"], marker="D", zorder=3)
            ax.text(row[event_time_col], y + 0.22, str(row[event_col]), fontsize=7, ha="center", va="bottom", color=BOARISK_PALETTE["muted"])
    ax.set_yticks(y_pos, patients)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    if group_col:
        handles = [plt.Rectangle((0, 0), 1, 1, facecolor=color_lookup[group], edgecolor=BOARISK_PALETTE["ink"], label=group) for group in color_lookup]
        ax.legend(handles=handles, title=group_col, frameon=False, loc="lower right")
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_raincloud(
    data: Any,
    *,
    x: str = "group",
    y: str = "value",
    order: Sequence[Any] | None = None,
    title: str = "Raincloud plot",
    ylabel: str | None = None,
    palette: str | Sequence[str] | None = "bf_vibrant_muted",
    random_state: int = 7,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot half-violin distributions with box summaries and patient-level points."""
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, y])
    df[y] = pd.to_numeric(df[y], errors="coerce")
    df = df.dropna(subset=[x, y])
    if df.empty:
        raise ValueError("data must contain at least one complete numeric row.")
    groups = _ordered_string_values(df[x].astype(str), order)
    values = [df.loc[df[x].astype(str) == group, y].to_numpy(dtype=float) for group in groups]
    colors = _resolve_color_sequence(len(groups), palette)
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(5.8, 1.1 * len(groups)), 4.6))
    else:
        fig = ax.figure
    parts = ax.violinplot(values, positions=np.arange(len(groups)), widths=0.75, showmeans=False, showmedians=False, showextrema=False)
    for index, (body, color) in enumerate(zip(parts["bodies"], colors)):
        vertices = body.get_paths()[0].vertices
        vertices[:, 0] = np.minimum(vertices[:, 0], index)
        body.set_facecolor(color)
        body.set_edgecolor(BOARISK_PALETTE["ink"])
        body.set_alpha(0.42)
        body.set_linewidth(0.8)
    box = ax.boxplot(values, positions=np.arange(len(groups)) + 0.12, widths=0.18, patch_artist=True, showfliers=False)
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
        patch.set_edgecolor(BOARISK_PALETTE["ink"])
    rng = np.random.default_rng(random_state)
    for index, vals in enumerate(values):
        x_jitter = rng.normal(index + 0.28, 0.035, len(vals))
        ax.scatter(x_jitter, vals, s=16, color=BOARISK_PALETTE["ink"], alpha=0.55, linewidths=0, zorder=3)
    ax.set_xticks(np.arange(len(groups)), groups)
    ax.set_ylabel(ylabel or y)
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_alluvial_flow(
    data: Any,
    *,
    path_col: str = "path",
    stage_col: str = "stage",
    category_col: str = "category",
    value_col: str | None = "value",
    stage_order: Sequence[Any] | None = None,
    title: str = "Alluvial flow",
    palette: str | Sequence[str] | None = "bf_vibrant_muted",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot categorical flows across ordered stages."""
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [path_col, stage_col, category_col, value_col])
    if value_col is None:
        df["_fyron_value"] = 1.0
        value_col = "_fyron_value"
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[path_col, stage_col, category_col, value_col])
    if df.empty:
        raise ValueError("data must contain at least one complete alluvial row.")
    stages = _ordered_string_values(df[stage_col].astype(str), stage_order)
    if len(stages) < 2:
        raise ValueError("alluvial flow requires at least two stages.")
    categories = _ordered_string_values(df[category_col].astype(str))
    colors = dict(zip(categories, _resolve_color_sequence(len(categories), palette)))
    totals = {(stage, category): float(df.loc[(df[stage_col].astype(str) == stage) & (df[category_col].astype(str) == category), value_col].sum()) for stage in stages for category in categories}
    offsets: dict[tuple[str, str], float] = {}
    for stage in stages:
        y_cursor = 0.0
        for category in categories:
            offsets[(stage, category)] = y_cursor
            y_cursor += totals[(stage, category)]
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(6.4, 1.5 * len(stages)), 4.8))
    else:
        fig = ax.figure
    band_offsets = offsets.copy()
    paths = _ordered_string_values(df[path_col].astype(str))
    for path in paths:
        path_df = df[df[path_col].astype(str) == path]
        row_by_stage = {str(row[stage_col]): row for _, row in path_df.iterrows()}
        for left_stage, right_stage in zip(stages[:-1], stages[1:]):
            if left_stage not in row_by_stage or right_stage not in row_by_stage:
                continue
            left = row_by_stage[left_stage]
            right = row_by_stage[right_stage]
            value = min(float(left[value_col]), float(right[value_col]))
            if value <= 0:
                continue
            left_cat = str(left[category_col])
            right_cat = str(right[category_col])
            y0 = band_offsets[(left_stage, left_cat)]
            y1 = band_offsets[(right_stage, right_cat)]
            band_offsets[(left_stage, left_cat)] += value
            band_offsets[(right_stage, right_cat)] += value
            x0 = stages.index(left_stage)
            x1 = stages.index(right_stage)
            xs = np.linspace(x0 + 0.08, x1 - 0.08, 20)
            t = np.linspace(0, 1, 20)
            top = (1 - t) * (y0 + value) + t * (y1 + value)
            bottom = (1 - t) * y0 + t * y1
            polygon = Polygon(np.c_[np.r_[xs, xs[::-1]], np.r_[top, bottom[::-1]]], closed=True, facecolor=colors[left_cat], edgecolor="none", alpha=0.28)
            ax.add_patch(polygon)
    for stage_index, stage in enumerate(stages):
        for category in categories:
            total = totals[(stage, category)]
            if total <= 0:
                continue
            y0 = offsets[(stage, category)]
            ax.bar(stage_index, total, bottom=y0, width=0.16, color=colors[category], edgecolor=BOARISK_PALETTE["ink"], linewidth=0.7)
            if total > 0:
                ax.text(stage_index, y0 + total / 2, category, ha="center", va="center", fontsize=7, color=BOARISK_PALETTE["ink"])
    ax.set_xticks(np.arange(len(stages)), stages)
    ax.set_xlim(-0.45, len(stages) - 0.55)
    ax.set_ylabel("Count")
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_binned_marker_heatmap(
    data: Any,
    *,
    row_col: str = "feature",
    col_col: str = "sample",
    value_col: str = "bin",
    row_order: Sequence[Any] | None = None,
    col_order: Sequence[Any] | None = None,
    title: str = "Binned marker heatmap",
    cmap: str = "fyron_diverging_teal_orange",
    missing_color: str = "#F7F8FA",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot a discrete patient-feature marker heatmap."""
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [row_col, col_col, value_col])
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[row_col, col_col])
    if df.empty:
        raise ValueError("data must contain at least one marker heatmap row.")
    matrix = df.pivot_table(index=row_col, columns=col_col, values=value_col, aggfunc="first")
    rows = [value for value in row_order if value in matrix.index] if row_order is not None else list(matrix.index)
    cols = [value for value in col_order if value in matrix.columns] if col_order is not None else list(matrix.columns)
    if not rows or not cols:
        raise ValueError("row_order and col_order must leave at least one visible row and column.")
    matrix = matrix.loc[rows, cols]
    values = matrix.to_numpy(dtype=float)
    masked = np.ma.masked_invalid(values)
    colormap = resolve_colormap(cmap).copy()
    colormap.set_bad(missing_color)
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(5.4, 0.42 * len(cols)), max(3.6, 0.28 * len(rows))))
    else:
        fig = ax.figure
    im = ax.imshow(masked, aspect="auto", cmap=colormap, interpolation="nearest")
    ax.set_xticks(np.arange(len(cols)), [str(col) for col in cols], rotation=45, ha="right")
    ax.set_yticks(np.arange(len(rows)), [str(row) for row in rows])
    ax.set_title(title)
    ax.set_xlabel(col_col)
    ax.set_ylabel(row_col)
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label=value_col)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_reference_band_grid(
    data: Any,
    *,
    x: str,
    lower_col: str = "lower",
    upper_col: str = "upper",
    band_col: str = "band",
    col: str = "feature",
    row: str | None = None,
    line_df: Any | None = None,
    line_y: str | None = None,
    feature_order: Sequence[Any] | None = None,
    row_order: Sequence[Any] | None = None,
    band_preset: Literal["sd", "survival", "risk", "percentile"] | None = None,
    band_order: Sequence[Any] | None = None,
    band_colors: Mapping[Any, str] | Sequence[str] | None = None,
    title: str = "Reference band grid",
    xlabel: str | None = None,
    ylabel: str | None = None,
    sharex: bool = True,
    sharey: bool | Literal["row", "col"] = False,
    legend: bool = True,
    figsize: tuple[float, float] | None = None,
    line_color: str = "#1F2933",
    line_width: float = 1.35,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> tuple[Figure, np.ndarray]:
    """Plot faceted clinical reference bands with an optional trend line.

    ``data`` should contain precomputed band intervals. Fyron visualizes those
    intervals as provided and does not estimate normative limits or SD curves.

    Parameters
    ----------
    data
        Long-form table with one row per x value, reference band, and facet.
    x
        Numeric x-axis column, such as age, biological age, follow-up month, or dose.
    lower_col
        Numeric lower bound for each reference band interval.
    upper_col
        Numeric upper bound for each reference band interval.
    band_col
        Column containing the reference band label.
    col
        Facet column shown across plot columns, usually a feature or measurement name.
    row
        Optional facet column shown across plot rows, such as sex, cohort, scanner, or modality.
    line_df
        Optional long-form table with the same x and facet columns for an overlaid trend line.
    line_y
        Numeric y column in ``line_df``. Required when ``line_df`` is provided.
    feature_order
        Optional explicit order for column facets.
    row_order
        Optional explicit order for row facets.
    band_preset
        Optional named preset for common band labels and colors: ``"sd"``,
        ``"survival"``, ``"risk"``, or ``"percentile"``.
    band_order
        Optional explicit order for drawing bands and the legend.
    band_colors
        Optional mapping from band label to color, or a color sequence matching ``band_order``.
    title
        Figure title.
    xlabel
        X-axis label.
    ylabel
        Y-axis label. When ``row`` is provided, the row label is combined with the y-axis label.
    sharex
        Whether column facets share the x-axis.
    sharey
        Matplotlib y-axis sharing control for facets.
    legend
        Whether to draw a shared band legend below the grid.
    figsize
        Optional figure size in inches.
    line_color
        Color used for the optional trend line.
    line_width
        Width used for the optional trend line.
    save_path
        Optional path for saving the figure.
    fmt
        Output format used with ``save_path``.

    Returns
    -------
    tuple[Figure, np.ndarray]
        Matplotlib figure and two-dimensional array of axes.
    """

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, lower_col, upper_col, band_col, col, row])
    for numeric_col in [x, lower_col, upper_col]:
        df[numeric_col] = pd.to_numeric(df[numeric_col], errors="coerce")
    drop_cols = [x, lower_col, upper_col, band_col, col] + ([row] if row else [])
    df = df.dropna(subset=drop_cols)
    if df.empty:
        raise ValueError("data must contain at least one complete reference band row.")
    if (df[lower_col] > df[upper_col]).any():
        raise ValueError("reference band rows must satisfy lower_col <= upper_col.")

    df["_fyron_col"] = df[col].astype(str)
    df["_fyron_row"] = df[row].astype(str) if row else "__single__"
    df["_fyron_band"] = df[band_col].astype(str)

    col_values = _ordered_string_values(df["_fyron_col"], feature_order)
    row_values = _ordered_string_values(df["_fyron_row"], row_order) if row else ["__single__"]
    preset_order, preset_colors = _resolve_reference_band_preset(band_preset)
    if band_order is None:
        band_order = preset_order
    if band_colors is None:
        band_colors = preset_colors
    band_values = _ordered_string_values(df["_fyron_band"], band_order)
    if not col_values or not row_values or not band_values:
        raise ValueError("orders must leave at least one visible row, column, and band.")

    missing_bands = [band for band in band_values if band not in set(df["_fyron_band"])]
    if len(missing_bands) == len(band_values):
        raise ValueError("band_order must include at least one band present in data.")

    if band_colors is None:
        default_colors = [DEFAULT_REFERENCE_BAND_COLORS.get(band) for band in band_values]
        fallback = _resolve_color_sequence(len(band_values), "bf_vibrant_muted")
        colors = [color or fallback[index] for index, color in enumerate(default_colors)]
        color_lookup = dict(zip(band_values, colors))
    elif isinstance(band_colors, Mapping):
        color_lookup = {str(key): value for key, value in band_colors.items()}
        fallback = _resolve_color_sequence(len(band_values), "bf_vibrant_muted")
        color_lookup = {band: color_lookup.get(band, fallback[index]) for index, band in enumerate(band_values)}
    else:
        colors = list(band_colors)
        if len(colors) < len(band_values):
            raise ValueError("band_colors must provide at least one color per visible band.")
        color_lookup = dict(zip(band_values, colors))

    line_data: pd.DataFrame | None = None
    if line_df is not None:
        if line_y is None:
            raise ValueError("line_y must be provided when line_df is used.")
        line_data = pd.DataFrame(line_df).copy()
        _require_columns(line_data, [x, line_y, col, row])
        for numeric_col in [x, line_y]:
            line_data[numeric_col] = pd.to_numeric(line_data[numeric_col], errors="coerce")
        line_drop_cols = [x, line_y, col] + ([row] if row else [])
        line_data = line_data.dropna(subset=line_drop_cols)
        line_data["_fyron_col"] = line_data[col].astype(str)
        line_data["_fyron_row"] = line_data[row].astype(str) if row else "__single__"

    n_rows = len(row_values)
    n_cols = len(col_values)
    if figsize is None:
        figsize = (max(3.0 * n_cols, 4.8), max(2.55 * n_rows, 3.2))
    fig, axes_raw = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=sharex, sharey=sharey, squeeze=False)
    axes = np.asarray(axes_raw)
    x_label = xlabel or x.replace("_", " ").title()

    for row_index, row_value in enumerate(row_values):
        for col_index, col_value in enumerate(col_values):
            ax = axes[row_index, col_index]
            facet = df[(df["_fyron_row"] == row_value) & (df["_fyron_col"] == col_value)]
            if facet.empty:
                ax.set_visible(False)
                continue
            for band_value in band_values:
                band_df = facet[facet["_fyron_band"] == band_value].sort_values(x)
                if band_df.empty:
                    continue
                ax.fill_between(
                    band_df[x].to_numpy(dtype=float),
                    band_df[lower_col].to_numpy(dtype=float),
                    band_df[upper_col].to_numpy(dtype=float),
                    color=color_lookup[band_value],
                    alpha=0.82,
                    linewidth=0,
                    label=band_value,
                    zorder=1,
                )
            if line_data is not None and not line_data.empty:
                line_subset = line_data[(line_data["_fyron_row"] == row_value) & (line_data["_fyron_col"] == col_value)].sort_values(x)
                if not line_subset.empty:
                    ax.plot(
                        line_subset[x].to_numpy(dtype=float),
                        line_subset[line_y].to_numpy(dtype=float),
                        color=line_color,
                        linewidth=line_width,
                        zorder=3,
                    )
            ax.set_title(col_value, fontsize=10, fontweight="bold")
            ax.grid(True, axis="x", color=BOARISK_PALETTE["grid"], linewidth=0.8, alpha=0.55)
            ax.grid(False, axis="y")
            ax.spines[["top", "right"]].set_visible(False)
            if col_index == 0:
                if row:
                    ax.set_ylabel(f"{row_value}\n{ylabel or ''}".rstrip(), fontweight="bold")
                else:
                    ax.set_ylabel(ylabel or "")
            if row_index == n_rows - 1 and n_cols == 1:
                ax.set_xlabel(x_label)
                ax.xaxis.labelpad = 6

    if title:
        fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
    if n_cols > 1:
        fig.supxlabel(x_label, y=0.085 if legend else 0.025)
    bottom = 0.13 if legend and n_cols > 1 else 0.16 if legend else 0.08
    top = 0.92 if title else 0.98
    if legend:
        handles = [
            plt.Rectangle((0, 0), 1, 1, facecolor=color_lookup[band], edgecolor="none", label=band, alpha=0.82)
            for band in band_values
            if band not in missing_bands
        ]
        fig.legend(handles=handles, loc="lower center", ncol=min(len(handles), 5), frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, bottom, 1, top))
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, axes


def plot_qq(
    data: Any,
    *,
    value_col: str | None = None,
    columns: Sequence[str] | None = None,
    group_col: str | None = None,
    theoretical: Literal["normal"] = "normal",
    line: Literal["quartile", "fit", "identity"] | None = "quartile",
    facet: bool = False,
    title: str = "Q-Q plot",
    xlabel: str = "Theoretical quantiles",
    ylabel: str = "Observed quantiles",
    palette: str | Sequence[str] | None = "okabe_ito",
    point_size: float = 24.0,
    alpha: float = 0.82,
    marker: str = "o",
    line_color: str = "#1F2933",
    line_width: float = 1.35,
    sharex: bool = True,
    sharey: bool = True,
    figsize: tuple[float, float] | None = None,
    legend: bool = True,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> tuple[Figure, np.ndarray, pd.DataFrame]:
    """Plot configurable normal Q-Q diagnostics.

    Use this helper to compare observed clinical values, residuals, model
    scores, or biomarker features with theoretical normal quantiles. Points
    close to the reference line indicate compatibility with the chosen
    distribution, while systematic curvature or tail departures suggest
    skewness, heavy tails, outliers, or mixed subgroups.

    Parameters
    ----------
    data
        Vector-like values or a table containing numeric columns.
    value_col
        Single numeric DataFrame column to plot.
    columns
        Optional list of numeric DataFrame columns to plot.
    group_col
        Optional grouping column. Groups are overlaid by default or faceted
        when ``facet=True``.
    theoretical
        Theoretical distribution. Version 1 supports ``"normal"``.
    line
        Reference line mode: ``"quartile"``, ``"fit"``, ``"identity"``, or ``None``.
    facet
        Draw one panel per variable/group series instead of overlaying series.
    title
        Figure title.
    xlabel
        X-axis label.
    ylabel
        Y-axis label.
    palette
        Fyron palette name or explicit color sequence.
    point_size
        Scatter point size.
    alpha
        Scatter point transparency.
    marker
        Matplotlib marker used for points.
    line_color
        Reference line color.
    line_width
        Reference line width.
    sharex
        Whether faceted panels share the x-axis.
    sharey
        Whether faceted panels share the y-axis.
    figsize
        Optional figure size.
    legend
        Whether to show a legend for overlaid series.
    ax
        Optional axis for a single overlaid panel.
    save_path
        Optional path for saving the figure.
    fmt
        Output format used with ``save_path``.

    Returns
    -------
    tuple[Figure, np.ndarray, pandas.DataFrame]
        Matplotlib figure, two-dimensional axes array, and long-form Q-Q table.
    """

    _apply_plot_style()
    if theoretical != "normal":
        raise ValueError("theoretical must be 'normal'.")
    if line not in {"quartile", "fit", "identity", None}:
        raise ValueError("line must be 'quartile', 'fit', 'identity', or None.")
    if point_size <= 0:
        raise ValueError("point_size must be positive.")
    if not 0 <= alpha <= 1:
        raise ValueError("alpha must be between 0 and 1.")
    if line_width <= 0:
        raise ValueError("line_width must be positive.")

    series_specs = _qq_series_specs(data, value_col=value_col, columns=columns, group_col=group_col)
    qq_table = pd.concat(
        [_qq_table_for_values(values, variable=variable, group=group) for variable, group, values in series_specs],
        ignore_index=True,
    )
    series_keys = list(dict.fromkeys(zip(qq_table["variable"], qq_table["group"], strict=False)))
    n_series = len(series_keys)
    colors = _resolve_color_sequence(n_series, palette)
    color_lookup = dict(zip(series_keys, colors))

    if facet:
        if ax is not None:
            raise ValueError("ax cannot be used with facet=True.")
        n_cols = min(3, n_series)
        n_rows = int(np.ceil(n_series / n_cols))
        if figsize is None:
            figsize = (max(4.2 * n_cols, 4.8), max(3.4 * n_rows, 3.6))
        fig, axes_raw = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=sharex, sharey=sharey, squeeze=False)
        axes = np.asarray(axes_raw)
        flat_axes = list(axes.ravel())
    else:
        if ax is not None:
            fig = ax.figure
            axes = np.asarray([[ax]])
        else:
            fig, axes_raw = plt.subplots(1, 1, figsize=figsize or (5.4, 4.4), squeeze=False)
            axes = np.asarray(axes_raw)
        flat_axes = [axes[0, 0]]

    for index, key in enumerate(series_keys):
        variable, group = key
        series_table = qq_table[(qq_table["variable"] == variable) & (qq_table["group"] == group)]
        plot_ax = flat_axes[index] if facet else flat_axes[0]
        color = color_lookup[key]
        label = _qq_series_label(variable, group, include_variable=len({k[0] for k in series_keys}) > 1)
        plot_ax.scatter(
            series_table["theoretical_quantile"],
            series_table["observed_quantile"],
            s=point_size,
            alpha=alpha,
            color=color,
            marker=marker,
            edgecolor="white",
            linewidth=0.35,
            label=label,
            zorder=3,
        )
        if line is not None:
            x_line, y_line = _qq_reference_line(series_table, line)
            plot_ax.plot(x_line, y_line, color=line_color, linewidth=line_width, alpha=0.92, zorder=2)
        if facet:
            plot_ax.set_title(label, fontsize=10, fontweight="bold")

    if facet:
        for extra_ax in flat_axes[n_series:]:
            extra_ax.set_visible(False)

    for plot_ax in flat_axes[:n_series if facet else 1]:
        plot_ax.set_xlabel(xlabel)
        plot_ax.set_ylabel(ylabel)
        plot_ax.grid(True, color=BOARISK_PALETTE["grid"], linewidth=0.8, alpha=0.72)
        plot_ax.spines[["top", "right"]].set_visible(False)
    if title:
        if facet:
            fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
        else:
            axes[0, 0].set_title(title, loc="left", fontsize=12, fontweight="bold")
    if legend and not facet and n_series > 1:
        axes[0, 0].legend(frameon=False, loc="best")

    fig.tight_layout(rect=(0, 0, 1, 0.94) if facet and title else None)
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, axes, qq_table


def _qq_series_specs(
    data: Any,
    *,
    value_col: str | None,
    columns: Sequence[str] | None,
    group_col: str | None,
) -> list[tuple[str, str, np.ndarray]]:
    if columns is not None and value_col is not None:
        raise ValueError("Use either value_col or columns, not both.")
    if columns is not None and len(columns) == 0:
        raise ValueError("columns must contain at least one column name.")
    specs: list[tuple[str, str, np.ndarray]] = []

    if value_col is None and columns is None and group_col is None:
        if isinstance(data, pd.DataFrame):
            numeric_columns = [col for col in data.columns if pd.api.types.is_numeric_dtype(data[col])]
            if len(numeric_columns) != 1:
                raise ValueError("DataFrame input without value_col or columns must contain exactly one numeric column.")
            column = numeric_columns[0]
            specs.append((str(column), "All", pd.to_numeric(data[column], errors="coerce").to_numpy(dtype=float)))
        else:
            values = pd.to_numeric(pd.Series(data), errors="coerce").to_numpy(dtype=float)
            specs.append(("value", "All", values))
        return specs

    df = pd.DataFrame(data).copy()
    if columns is not None:
        selected_columns = list(columns)
    elif value_col is not None:
        selected_columns = [value_col]
    else:
        numeric_columns = []
        for col in df.columns:
            if col == group_col:
                continue
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().any():
                numeric_columns.append(col)
        if len(numeric_columns) != 1:
            raise ValueError("DataFrame input with group_col requires value_col or exactly one numeric value column.")
        selected_columns = [numeric_columns[0]]
    _require_columns(df, [*selected_columns, group_col])
    group_values = _ordered_string_values(df[group_col]) if group_col else ["All"]
    for column in selected_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if group_col:
            group_series = df[group_col].astype(str)
            for group in group_values:
                values = df.loc[group_series == group, column].to_numpy(dtype=float)
                specs.append((str(column), str(group), values))
        else:
            specs.append((str(column), "All", df[column].to_numpy(dtype=float)))
    return specs


def _qq_table_for_values(values: np.ndarray, *, variable: str, group: str) -> pd.DataFrame:
    observed = np.asarray(values, dtype=float)
    observed = observed[np.isfinite(observed)]
    if observed.size < 3:
        label = variable if group == "All" else f"{variable}/{group}"
        raise ValueError(f"Q-Q plot series '{label}' must contain at least 3 finite values.")
    observed = np.sort(observed)
    ranks = np.arange(1, observed.size + 1, dtype=float)
    probabilities = (ranks - 0.5) / observed.size
    normal = NormalDist()
    theoretical = np.array([normal.inv_cdf(float(probability)) for probability in probabilities], dtype=float)
    return pd.DataFrame(
        {
            "variable": variable,
            "group": group,
            "rank": ranks.astype(int),
            "probability": probabilities,
            "theoretical": "normal",
            "theoretical_quantile": theoretical,
            "observed_quantile": observed,
        }
    )


def _qq_reference_line(table: pd.DataFrame, line: Literal["quartile", "fit", "identity"]) -> tuple[np.ndarray, np.ndarray]:
    x = table["theoretical_quantile"].to_numpy(dtype=float)
    y = table["observed_quantile"].to_numpy(dtype=float)
    x_line = np.array([np.nanmin(x), np.nanmax(x)], dtype=float)
    if line == "identity":
        return x_line, x_line
    if line == "fit":
        slope, intercept = np.polyfit(x, y, 1)
    else:
        x_q1, x_q3 = np.quantile(x, [0.25, 0.75])
        y_q1, y_q3 = np.quantile(y, [0.25, 0.75])
        slope = (y_q3 - y_q1) / (x_q3 - x_q1)
        intercept = y_q1 - slope * x_q1
    return x_line, intercept + slope * x_line


def _qq_series_label(variable: str, group: str, *, include_variable: bool) -> str:
    if group == "All":
        return variable
    if include_variable:
        return f"{variable} - {group}"
    return group


def _resolve_reference_band_preset(
    preset: Literal["sd", "survival", "risk", "percentile"] | None,
) -> tuple[Sequence[str] | None, Mapping[str, str] | None]:
    if preset is None:
        return None, None
    if preset not in REFERENCE_BAND_PRESETS:
        valid = ", ".join(sorted(REFERENCE_BAND_PRESETS))
        raise ValueError(f"band_preset must be one of: {valid}.")
    spec = REFERENCE_BAND_PRESETS[preset]
    return list(spec["order"]), dict(spec["colors"])


def plot_grouped_bar_with_significance(
    data: Any,
    *,
    x: str,
    y: str,
    hue: str | None = None,
    order: Sequence[Any] | None = None,
    hue_order: Sequence[Any] | None = None,
    estimator: Literal["mean", "median"] = "mean",
    error: Literal["sem", "sd", "ci", "none"] = "sem",
    ci: float = 0.95,
    test: Literal["auto", "mannwhitney", "ttest", "kruskal"] = "auto",
    comparisons: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]] | None = None,
    p_thresholds: Sequence[tuple[float, str]] = ((0.001, "***"), (0.01, "**"), (0.05, "*")),
    title: str = "Grouped outcome summary",
    ylabel: str | None = None,
    xlabel: str | None = None,
    palette: Sequence[str] | None = None,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> TablePlotReturn:
    """Plot grouped bars with statistical significance brackets.

    The returned table contains both bar-level summaries and comparison rows.
    Use this for manuscript-style summaries where groups/hues need explicit
    p-value notation on the plot.
    """

    _apply_plot_style()
    if estimator not in {"mean", "median"}:
        raise ValueError("estimator must be 'mean' or 'median'.")
    if error not in {"sem", "sd", "ci", "none"}:
        raise ValueError("error must be one of 'sem', 'sd', 'ci', or 'none'.")
    if test not in {"auto", "mannwhitney", "ttest", "kruskal"}:
        raise ValueError("test must be 'auto', 'mannwhitney', 'ttest', or 'kruskal'.")
    if not 0 < ci < 1:
        raise ValueError("ci must be in the interval (0, 1).")

    df = pd.DataFrame(data).copy()
    _require_columns(df, [x, y, hue])
    df[y] = pd.to_numeric(df[y], errors="coerce")
    df = df.dropna(subset=[x, y] + ([hue] if hue else []))
    if df.empty:
        raise ValueError("data must contain at least one complete numeric row.")

    df["_fyron_x"] = df[x].astype(str)
    x_values = _ordered_string_values(df["_fyron_x"], order)
    hue_values = _ordered_string_values(df[hue].astype(str), hue_order) if hue else ["__single__"]
    colors = _resolve_color_sequence(len(hue_values), palette)
    hatches = _resolve_hatch_sequence(len(hue_values))
    width_total = 0.74
    bar_width = width_total / max(len(hue_values), 1)

    summary_rows: list[dict[str, Any]] = []
    bar_positions: dict[tuple[str, str], float] = {}
    bar_heights: dict[tuple[str, str], float] = {}
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(6.2, 1.0 * len(x_values) * max(1, len(hue_values))), 4.8))
    else:
        fig = ax.figure

    for hue_index, hue_value in enumerate(hue_values):
        offsets = []
        heights = []
        errors = []
        for x_index, x_value in enumerate(x_values):
            if hue:
                values = df.loc[(df["_fyron_x"] == x_value) & (df[hue].astype(str) == hue_value), y].to_numpy(dtype=float)
            else:
                values = df.loc[df["_fyron_x"] == x_value, y].to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            center = x_index + (hue_index - (len(hue_values) - 1) / 2) * bar_width
            stat = float(np.nan) if values.size == 0 else float(np.mean(values) if estimator == "mean" else np.median(values))
            err = _summary_error(values, error=error, ci=ci)
            offsets.append(center)
            heights.append(stat)
            errors.append(err)
            bar_positions[(x_value, hue_value)] = center
            bar_heights[(x_value, hue_value)] = stat + (err if np.isfinite(err) else 0.0)
            summary_rows.append(
                {
                    "row_type": "summary",
                    x: x_value,
                    "hue": None if hue is None else hue_value,
                    "n": int(values.size),
                    estimator: stat,
                    "error": err,
                    "error_method": error,
                }
            )
        bars = ax.bar(
            offsets,
            heights,
            yerr=None if error == "none" else errors,
            width=bar_width * 0.88,
            color=colors[hue_index],
            edgecolor=BOARISK_PALETTE["ink"],
            linewidth=0.8,
            capsize=3 if error != "none" else 0,
            label=None if hue is None else hue_value,
        )
        for bar in bars:
            bar.set_hatch(hatches[hue_index])

    comparison_rows = _compute_grouped_bar_comparisons(
        df,
        x=x,
        y=y,
        hue=hue,
        x_values=x_values,
        hue_values=hue_values,
        comparisons=comparisons,
        test=test,
        p_thresholds=p_thresholds,
    )
    _annotate_grouped_bar_significance(
        ax,
        comparison_rows,
        bar_positions=bar_positions,
        bar_heights=bar_heights,
    )

    ax.set_xticks(np.arange(len(x_values)))
    ax.set_xticklabels(x_values)
    ax.set_ylabel(ylabel or y)
    ax.set_xlabel(xlabel or x)
    ax.set_title(title)
    if hue:
        ax.legend(title=hue, frameon=False)
    ax.margins(y=0.18)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    out_table = pd.concat([pd.DataFrame(summary_rows), pd.DataFrame(comparison_rows)], ignore_index=True, sort=False)
    return fig, ax, out_table


def _summary_error(values: np.ndarray, *, error: str, ci: float) -> float:
    values = values[np.isfinite(values)]
    if error == "none" or values.size == 0:
        return 0.0
    if values.size == 1:
        return 0.0
    sd = float(np.std(values, ddof=1))
    if error == "sd":
        return sd
    sem = sd / float(np.sqrt(values.size))
    if error == "sem":
        return sem
    try:
        from scipy import stats
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'Confidence intervals require scipy. Install with: uv add "fyron[statistics]"'
        ) from exc
    alpha = 1.0 - ci
    return float(stats.t.ppf(1.0 - alpha / 2.0, values.size - 1) * sem)


def _compute_grouped_bar_comparisons(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    hue: str | None,
    x_values: Sequence[str],
    hue_values: Sequence[str],
    comparisons: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]] | None,
    test: str,
    p_thresholds: Sequence[tuple[float, str]],
) -> list[dict[str, Any]]:
    requested = list(comparisons or _default_grouped_bar_comparisons(x_values, hue_values, hue=hue))
    rows = []
    for left, right in requested:
        left_key = _normalize_comparison_key(left, hue=hue)
        right_key = _normalize_comparison_key(right, hue=hue)
        left_values = _comparison_values(df, x=x, y=y, hue=hue, key=left_key)
        right_values = _comparison_values(df, x=x, y=y, hue=hue, key=right_key)
        p_value, used_test, statistic = _run_group_comparison(left_values, right_values, test=test)
        rows.append(
            {
                "row_type": "comparison",
                "group_a": _format_comparison_key(left_key),
                "group_b": _format_comparison_key(right_key),
                "x_a": left_key[0],
                "hue_a": left_key[1],
                "x_b": right_key[0],
                "hue_b": right_key[1],
                "n_a": int(left_values.size),
                "n_b": int(right_values.size),
                "test": used_test,
                "statistic": statistic,
                "p_value": p_value,
                "notation": _significance_notation(p_value, p_thresholds),
            }
        )
    return rows


def _default_grouped_bar_comparisons(
    x_values: Sequence[str],
    hue_values: Sequence[str],
    *,
    hue: str | None,
) -> list[tuple[Any, Any]]:
    if hue is not None and len(hue_values) == 2:
        return [((x_value, hue_values[0]), (x_value, hue_values[1])) for x_value in x_values]
    if len(x_values) == 2:
        if hue is None:
            return [(x_values[0], x_values[1])]
        return [((x_values[0], hue_value), (x_values[1], hue_value)) for hue_value in hue_values]
    return []


def _normalize_comparison_key(value: Any, *, hue: str | None) -> tuple[str, str]:
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError("comparison tuple keys must have shape (x, hue).")
        return (str(value[0]), str(value[1]))
    if hue is not None:
        raise ValueError("comparisons must use (x, hue) tuple keys when hue is provided.")
    return (str(value), "__single__" if hue is None else str(value))


def _pair_keys(
    pair: tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]],
    *,
    hue: str | None,
) -> tuple[tuple[str, str], tuple[str, str]]:
    if not isinstance(pair, tuple) or len(pair) != 2:
        raise ValueError("Each comparison pair must contain exactly two group keys.")
    return (_normalize_comparison_key(pair[0], hue=hue), _normalize_comparison_key(pair[1], hue=hue))


def _custom_p_lookup(
    p_values: Sequence[float] | Mapping[tuple[Any, Any], float] | pd.DataFrame | None,
    *,
    pairs: Sequence[Any],
    p_col: str,
    label_col: str,
) -> dict[Any, float]:
    if p_values is None:
        return {}
    if isinstance(p_values, pd.DataFrame):
        if p_col not in p_values.columns:
            raise ValueError(f"custom p-value table must contain {p_col!r}.")
        if label_col in p_values.columns:
            return {str(row[label_col]): float(row[p_col]) for _, row in p_values.iterrows()}
        return {i: float(value) for i, value in enumerate(p_values[p_col].to_list())}
    if isinstance(p_values, Mapping):
        out = {}
        for key, value in p_values.items():
            if isinstance(key, tuple) and len(key) == 2:
                out[(str(key[0]), str(key[1]))] = float(value)
            else:
                out[str(key)] = float(value)
        return out
    values = list(p_values)
    if len(values) != len(pairs):
        raise ValueError("custom p_values must have the same length as pairs.")
    return {i: float(value) for i, value in enumerate(values)}


def _comparison_values(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    hue: str | None,
    key: tuple[str, str],
) -> np.ndarray:
    x_value, hue_value = key
    mask = df[x].astype(str) == x_value
    if hue is not None:
        mask &= df[hue].astype(str) == hue_value
    values = df.loc[mask, y].to_numpy(dtype=float)
    return values[np.isfinite(values)]


def _run_group_comparison(left: np.ndarray, right: np.ndarray, *, test: str) -> tuple[float, str, float]:
    if left.size < 2 or right.size < 2:
        return (float("nan"), test if test != "auto" else "insufficient_n", float("nan"))
    try:
        from scipy import stats
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'Statistical bar annotations require scipy. Install with: uv add "fyron[statistics]"'
        ) from exc
    chosen = "mannwhitney" if test == "auto" else test
    if chosen == "mannwhitney":
        result = stats.mannwhitneyu(left, right, alternative="two-sided")
    elif chosen == "ttest":
        result = stats.ttest_ind(left, right, equal_var=False, nan_policy="omit")
    elif chosen == "kruskal":
        result = stats.kruskal(left, right, nan_policy="omit")
    else:
        raise ValueError(f"Unsupported comparison test: {chosen}")
    return (float(result.pvalue), chosen, float(result.statistic))


def _run_annotation_test(left: np.ndarray, right: np.ndarray, *, test: str) -> tuple[float, str, float]:
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 1 or right.size < 1:
        return (float("nan"), "insufficient_n", float("nan"))
    try:
        from scipy import stats
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'Statistical plot annotations require scipy. Install with: uv add "fyron[statistics]"'
        ) from exc
    if test == "mannwhitney":
        result = stats.mannwhitneyu(left, right, alternative="two-sided")
    elif test == "welch":
        result = stats.ttest_ind(left, right, equal_var=False, nan_policy="omit")
    elif test == "ttest":
        result = stats.ttest_ind(left, right, equal_var=True, nan_policy="omit")
    elif test == "paired_ttest":
        if left.size != right.size:
            raise ValueError("paired_ttest requires equal group sizes.")
        result = stats.ttest_rel(left, right, nan_policy="omit")
    elif test == "wilcoxon":
        if left.size != right.size:
            raise ValueError("wilcoxon requires equal group sizes.")
        result = stats.wilcoxon(left, right)
    elif test == "kruskal":
        result = stats.kruskal(left, right, nan_policy="omit")
    elif test == "brunner_munzel":
        result = stats.brunnermunzel(left, right, nan_policy="omit")
    else:
        raise ValueError(
            "test must be one of mannwhitney, welch, ttest, paired_ttest, "
            "wilcoxon, kruskal, or brunner_munzel."
        )
    return (float(result.pvalue), test, float(result.statistic))


def _positions_from_xticks(ax: Axes) -> dict[tuple[str, str], float]:
    labels = [label.get_text() for label in ax.get_xticklabels()]
    return {(label, "__single__"): float(pos) for label, pos in zip(labels, ax.get_xticks())}


def _default_annotation_pairs(
    x_values: Sequence[str],
    hue_values: Sequence[str],
    *,
    hue: str | None,
) -> list[tuple[Any, Any]]:
    return _default_grouped_bar_comparisons(x_values, hue_values, hue=hue)


def _significance_notation(p_value: float, thresholds: Sequence[tuple[float, str]]) -> str:
    if not np.isfinite(p_value):
        return "n/a"
    for threshold, label in sorted(thresholds, key=lambda item: item[0]):
        if p_value < threshold:
            return label
    return "ns"


def _format_comparison_key(key: tuple[str, str]) -> str:
    return key[0] if key[1] == "__single__" else f"{key[0]} | {key[1]}"


def _annotate_grouped_bar_significance(
    ax: Axes,
    comparison_rows: Sequence[dict[str, Any]],
    *,
    bar_positions: Mapping[tuple[str, str], float],
    bar_heights: Mapping[tuple[str, str], float],
) -> None:
    valid = [row for row in comparison_rows if row.get("notation") not in {None, "n/a"}]
    if not valid:
        return
    finite_heights = [height for height in bar_heights.values() if np.isfinite(height)]
    if not finite_heights:
        return
    y_min = min(0.0, min(finite_heights))
    y_max = max(finite_heights)
    step = max((y_max - y_min) * 0.08, 0.08)
    current_y = y_max + step
    for row in valid:
        left = (str(row["x_a"]), str(row["hue_a"]) if row["hue_a"] is not None else "__single__")
        right = (str(row["x_b"]), str(row["hue_b"]) if row["hue_b"] is not None else "__single__")
        if left not in bar_positions or right not in bar_positions:
            continue
        x1 = bar_positions[left]
        x2 = bar_positions[right]
        if x1 > x2:
            x1, x2 = x2, x1
        ax.plot([x1, x1, x2, x2], [current_y, current_y + step * 0.3, current_y + step * 0.3, current_y], color=BOARISK_PALETTE["ink"], linewidth=0.9)
        ax.text((x1 + x2) / 2, current_y + step * 0.34, str(row["notation"]), ha="center", va="bottom", color=BOARISK_PALETTE["ink"], fontsize=9)
        current_y += step


def plot_directional_ratio_rows(
    data: Any,
    *,
    feature_col: str = "feature",
    ratio_col: str = "ratio",
    lower_col: str | None = "ci_lower",
    upper_col: str | None = "ci_upper",
    p_col: str | None = None,
    group_col: str | None = None,
    n_col: str | None = None,
    ratio_label: str = "Hazard / odds ratio",
    title: str = "Directional ratio rows",
    protective_label: str = "Protective",
    hazardous_label: str = "Hazardous",
    reference: float = 1.0,
    log_scale: bool = True,
    xlim: tuple[float, float] | None = None,
    annotate: bool = True,
    estimate_label: str | None = None,
    ci_label: str = "95% CI",
    p_label: str = "p value",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot odds or hazard ratios with protective and hazardous direction bands."""
    _apply_plot_style()
    if reference <= 0 and log_scale:
        raise ValueError("reference must be positive when log_scale=True.")
    df = pd.DataFrame(data).copy()
    _require_columns(df, [feature_col, ratio_col, p_col, group_col, n_col])
    has_ci = lower_col is not None and upper_col is not None and lower_col in df.columns and upper_col in df.columns
    if lower_col is not None and upper_col is not None and (lower_col in df.columns) != (upper_col in df.columns):
        raise ValueError("lower_col and upper_col must both be present to draw confidence intervals.")
    if (lower_col is None) != (upper_col is None):
        raise ValueError("lower_col and upper_col must both be provided, or both be None.")
    numeric_cols = [ratio_col, p_col]
    if has_ci:
        numeric_cols.extend([lower_col, upper_col])
    numeric_cols = [col for col in numeric_cols if col is not None]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    required_numeric = [ratio_col]
    if has_ci:
        required_numeric.extend([lower_col, upper_col])
    df = df.dropna(subset=[feature_col, *required_numeric])
    if df.empty:
        raise ValueError("data must contain at least one complete numeric ratio row.")
    if log_scale:
        positive_cols = [ratio_col]
        if has_ci:
            positive_cols.extend([lower_col, upper_col])
        for col in positive_cols:
            if (df[col] <= 0).any():
                raise ValueError(f"{col} must be positive when log_scale=True.")

    labels = df[feature_col].astype(str).to_list()
    if n_col is not None:
        labels = [f"{label} (n={n})" for label, n in zip(labels, df[n_col])]
    if group_col is not None:
        labels = [f"{group} | {label}" for group, label in zip(df[group_col].astype(str), labels)]

    ratio = df[ratio_col].to_numpy(dtype=float)
    y_pos = np.arange(len(df))[::-1]
    lower = df[lower_col].to_numpy(dtype=float) if has_ci else ratio
    upper = df[upper_col].to_numpy(dtype=float) if has_ci else ratio
    if has_ci and ((lower > ratio).any() or (upper < ratio).any()):
        raise ValueError("confidence interval bounds must satisfy lower <= ratio <= upper.")

    if xlim is None:
        values = np.concatenate([ratio, lower, upper]) if has_ci else ratio
        values = values[np.isfinite(values)]
        if values.size == 0:
            raise ValueError("ratio columns must contain finite values.")
        if log_scale:
            low = float(np.nanmin(values[values > 0]))
            high = float(np.nanmax(values[values > 0]))
            span = max(np.log(high / reference), np.log(reference / low), 0.35)
            xlim = (reference / float(np.exp(span * 1.25)), reference * float(np.exp(span * 1.25)))
        else:
            distance = max(float(np.nanmax(np.abs(values - reference))), 0.25)
            xlim = (reference - distance * 1.25, reference + distance * 1.25)
    if xlim[0] >= xlim[1]:
        raise ValueError("xlim must be an increasing (min, max) tuple.")
    if log_scale and (xlim[0] <= 0 or xlim[1] <= 0):
        raise ValueError("xlim values must be positive when log_scale=True.")

    if ax is None:
        fig, ax = plt.subplots(figsize=(9.8 if annotate else 8.0, max(3.8, 0.42 * len(df))))
    else:
        fig = ax.figure

    ax.set_xlim(*xlim)
    if log_scale:
        ax.set_xscale("log")
    ax.axvspan(xlim[0], reference, color="#D7F3F3", alpha=0.82, zorder=0)
    ax.axvspan(reference, xlim[1], color="#FFE1E5", alpha=0.82, zorder=0)
    ax.axvline(reference, color=BOARISK_PALETTE["ink"], linewidth=1.1, zorder=2)
    for y in y_pos:
        ax.axhline(y, color=BOARISK_PALETTE["grid"], linewidth=0.8, zorder=1)

    if has_ci:
        xerr = np.vstack([ratio - lower, upper - ratio])
        ax.errorbar(
            ratio,
            y_pos,
            xerr=xerr,
            fmt="none",
            ecolor=BOARISK_PALETTE["muted"],
            elinewidth=1.5,
            capsize=3,
            zorder=3,
        )
    colors = np.where(ratio < reference, BOARISK_PALETTE["blue"], BOARISK_PALETTE["red"])
    ax.scatter(
        ratio,
        y_pos,
        s=42,
        color=colors,
        edgecolor=BOARISK_PALETTE["ink"],
        linewidth=0.75,
        zorder=4,
    )

    ax.set_yticks(y_pos, labels=labels)
    ax.set_ylim(-0.7, len(df) - 0.3)
    ax.set_xlabel(ratio_label)
    ax.set_title(title)
    ax.text(0.02, 0.98, protective_label, transform=ax.transAxes, ha="left", va="top", fontsize=9, color=BOARISK_PALETTE["blue"])
    ax.text(0.98, 0.98, hazardous_label, transform=ax.transAxes, ha="right", va="top", fontsize=9, color=BOARISK_PALETTE["red"])

    if annotate:
        table_transform = ax.get_yaxis_transform()
        columns: list[tuple[str, float]] = [(estimate_label or _ratio_estimate_header(ratio_label), 1.02)]
        if has_ci:
            columns.append((ci_label, 1.16))
        if p_col is not None:
            columns.append((p_label, 1.39 if has_ci else 1.16))
        header_y = float(np.max(y_pos) + 0.48)
        for header, x_pos in columns:
            ax.text(
                x_pos,
                header_y,
                header,
                transform=table_transform,
                ha="left",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
                color=BOARISK_PALETTE["ink"],
                clip_on=False,
            )
        ax.plot(
            [1.0, columns[-1][1] + 0.13],
            [header_y - 0.08, header_y - 0.08],
            transform=table_transform,
            color=BOARISK_PALETTE["grid"],
            linewidth=0.8,
            clip_on=False,
        )
        for y, (_, row) in zip(y_pos, df.iterrows()):
            ax.text(
                columns[0][1],
                y,
                f"{float(row[ratio_col]):.2f}",
                transform=table_transform,
                ha="left",
                va="center",
                fontsize=8,
                color=BOARISK_PALETTE["muted"],
                clip_on=False,
            )
            col_index = 1
            if has_ci:
                ax.text(
                    columns[col_index][1],
                    y,
                    f"{float(row[lower_col]):.2f}-{float(row[upper_col]):.2f}",
                    transform=table_transform,
                    ha="left",
                    va="center",
                    fontsize=8,
                    color=BOARISK_PALETTE["muted"],
                    clip_on=False,
                )
                col_index += 1
            if p_col is not None:
                ax.text(
                    columns[col_index][1],
                    y,
                    _p_value_compact(row[p_col]),
                    transform=table_transform,
                    ha="left",
                    va="center",
                    fontsize=8,
                    color=BOARISK_PALETTE["muted"],
                    clip_on=False,
                )

    ax.grid(axis="x", color=BOARISK_PALETTE["grid"], linewidth=0.8)
    ax.grid(axis="y", visible=False)
    if annotate and ax is fig.axes[0]:
        fig.subplots_adjust(right=0.72)
    else:
        fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_forest_estimates(
    data: Any,
    *,
    label_col: str = "label",
    estimate_col: str = "estimate",
    lower_col: str = "ci_lower",
    upper_col: str = "ci_upper",
    p_col: str | None = None,
    p_adjust_col: str | None = None,
    n_col: str | None = None,
    group_col: str | None = None,
    table_columns: bool = False,
    reference: float = 1.0,
    log_scale: bool = True,
    title: str = "Forest plot",
    xlabel: str = "Hazard ratio",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot estimates with confidence intervals in a compact forest layout."""
    _apply_plot_style()
    if reference <= 0 and log_scale:
        raise ValueError("reference must be positive when log_scale=True.")
    df = pd.DataFrame(data).copy()
    _require_columns(df, [label_col, estimate_col, lower_col, upper_col, p_col, p_adjust_col, n_col, group_col])
    for col in [estimate_col, lower_col, upper_col]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[label_col, estimate_col, lower_col, upper_col])
    if df.empty:
        raise ValueError("data must contain at least one complete estimate row.")
    if log_scale and (df[estimate_col] <= 0).any():
        raise ValueError("estimate column must be positive when log_scale=True.")

    labels = df[label_col].astype(str).to_list()
    if group_col is not None:
        labels = [f"{group} | {label}" for group, label in zip(df[group_col].astype(str), labels)]
    if table_columns:
        p_display = p_adjust_col or p_col
        extra = []
        for _, row in df.iterrows():
            text = f"{float(row[estimate_col]):.2f} ({float(row[lower_col]):.2f}-{float(row[upper_col]):.2f})"
            if p_display is not None:
                text += f"  {p_display}={float(row[p_display]):.3g}" if pd.notna(row[p_display]) else f"  {p_display}=n/a"
            extra.append(text)
        labels = [f"{label}    {text}" for label, text in zip(labels, extra)]
    if n_col is not None:
        labels = [f"{label} (n={n})" for label, n in zip(labels, df[n_col])]
    y_pos = np.arange(len(df))[::-1]
    estimate = df[estimate_col].to_numpy(dtype=float)
    lower = df[lower_col].to_numpy(dtype=float)
    upper = df[upper_col].to_numpy(dtype=float)
    if log_scale:
        finite_positive = np.concatenate([estimate[np.isfinite(estimate) & (estimate > 0)], lower[np.isfinite(lower) & (lower > 0)], upper[np.isfinite(upper) & (upper > 0)]])
        if finite_positive.size == 0:
            raise ValueError("estimate and interval columns must contain finite positive values when log_scale=True.")
        floor = max(float(np.nanmin(finite_positive)) * 0.5, 1e-12)
        ceiling = float(np.nanmax(finite_positive)) * 2.0
        lower = np.where(np.isfinite(lower) & (lower > 0), lower, floor)
        upper = np.where(np.isfinite(upper) & (upper > 0), upper, ceiling)
    xerr = np.vstack([estimate - lower, upper - estimate])

    if ax is None:
        fig, ax = plt.subplots(figsize=(7.2, max(3.8, 0.42 * len(df))))
    else:
        fig = ax.figure
    ax.errorbar(
        estimate,
        y_pos,
        xerr=xerr,
        fmt="o",
        color=BOARISK_PALETTE["ink"],
        ecolor=BOARISK_PALETTE["muted"],
        elinewidth=1.5,
        capsize=3,
        markersize=5.5,
    )
    ax.axvline(reference, color=BOARISK_PALETTE["red"], linestyle="--", linewidth=1)
    ax.set_yticks(y_pos, labels=labels)
    if log_scale:
        ax.set_xscale("log")
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    if p_col is not None:
        for y, p_value in zip(y_pos, df[p_col]):
            ax.text(
                0.98,
                y,
                _p_value_label(p_value),
                transform=ax.get_yaxis_transform(),
                ha="right",
                va="center",
                fontsize=8,
                color=BOARISK_PALETTE["muted"],
            )
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_hazard_ratios(
    cox_result: Any,
    *,
    label_col: str = "label",
    title: str = "Hazard ratios",
    xlabel: str = "Hazard ratio",
    table_columns: bool = True,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot Cox hazard ratios from a Fyron Cox result or lifelines fitter."""

    try:
        from fyron.survival import cox_forest_table
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Hazard ratio plots require the survival extra. "
            'Install it with: uv add "fyron[survival]"'
        ) from exc
    table = cox_forest_table(cox_result)
    use_label = label_col if label_col in table.columns else "covariate"
    return plot_forest_estimates(
        table,
        label_col=use_label,
        estimate_col="hazard_ratio",
        lower_col="ci_lower",
        upper_col="ci_upper",
        p_col="p_value",
        reference=1.0,
        log_scale=True,
        title=title,
        xlabel=xlabel,
        table_columns=table_columns,
        ax=ax,
        save_path=save_path,
        fmt=fmt,
    )


def plot_missingness_bar(
    data: Any,
    *,
    column_col: str = "column",
    missing_col: str = "missing_percent",
    group_col: str | None = None,
    title: str = "Missingness",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot missingness percentages from a preprocessing summary table."""
    df = pd.DataFrame(data).copy()
    if group_col:
        return plot_patterned_bar(df, x=column_col, y=missing_col, group=group_col, title=title, ylabel="Missing (%)", ax=ax, save_path=save_path, fmt=fmt)
    return plot_patterned_bar(df, x=column_col, y=missing_col, title=title, ylabel="Missing (%)", ax=ax, save_path=save_path, fmt=fmt)


def plot_feature_selection_summary(
    data: Any,
    *,
    feature_col: str = "feature",
    selected_col: str = "selected",
    score_col: str | None = None,
    title: str = "Feature selection summary",
    top_n: int = 25,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot selected versus rejected features from a selection summary table."""
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [feature_col, selected_col])
    if score_col and score_col in df.columns:
        df["_score"] = pd.to_numeric(df[score_col], errors="coerce").abs()
    elif "n_selected_methods" in df.columns:
        df["_score"] = pd.to_numeric(df["n_selected_methods"], errors="coerce")
    else:
        df["_score"] = df[selected_col].astype(bool).astype(int)
    df = df.sort_values(["_score", selected_col], ascending=[False, False]).head(top_n).sort_values("_score")
    colors = np.where(df[selected_col].astype(bool), BOARISK_PALETTE["blue"], BOARISK_PALETTE["muted"])
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, max(3.8, 0.32 * len(df))))
    else:
        fig = ax.figure
    ax.barh(df[feature_col].astype(str), df["_score"], color=colors, edgecolor=BOARISK_PALETTE["ink"], linewidth=0.75)
    ax.set_xlabel(score_col or "Selection score")
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_stability_selection(
    data: Any,
    *,
    feature_col: str = "feature",
    frequency_col: str = "selection_frequency",
    threshold: float = 0.6,
    title: str = "Stability selection",
    top_n: int = 25,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot feature-selection frequencies from stability selection."""
    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [feature_col, frequency_col])
    df[frequency_col] = pd.to_numeric(df[frequency_col], errors="coerce")
    df = df.dropna(subset=[frequency_col]).sort_values(frequency_col, ascending=False).head(top_n).sort_values(frequency_col)
    colors = np.where(df[frequency_col] >= threshold, BOARISK_PALETTE["orange"], BOARISK_PALETTE["purple"])
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, max(3.8, 0.32 * len(df))))
    else:
        fig = ax.figure
    ax.barh(df[feature_col].astype(str), df[frequency_col], color=colors, edgecolor=BOARISK_PALETTE["ink"], linewidth=0.75)
    ax.axvline(threshold, color=BOARISK_PALETTE["ink"], linestyle="--", linewidth=1)
    ax.set_xlabel("Selection frequency")
    ax.set_xlim(0, 1)
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_bland_altman(
    method_a: ArrayLike,
    method_b: ArrayLike,
    *,
    title: str = "Bland-Altman plot",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot agreement between two measurements."""
    _apply_plot_style()
    a = np.asarray(method_a, dtype=float)
    b = np.asarray(method_b, dtype=float)
    if len(a) != len(b):
        raise ValueError("method_a and method_b must have the same length.")
    mask = np.isfinite(a) & np.isfinite(b)
    mean = (a[mask] + b[mask]) / 2
    diff = b[mask] - a[mask]
    bias = float(np.mean(diff))
    sd = float(np.std(diff, ddof=1))
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.4, 4.8))
    else:
        fig = ax.figure
    ax.scatter(mean, diff, color=BOARISK_PALETTE["blue"], alpha=0.75, edgecolors="none")
    for value, label in [(bias, "Bias"), (bias + 1.96 * sd, "+1.96 SD"), (bias - 1.96 * sd, "-1.96 SD")]:
        ax.axhline(value, color=BOARISK_PALETTE["ink"], linestyle="--" if label != "Bias" else "-", linewidth=1)
        ax.text(0.99, value, label, transform=ax.get_yaxis_transform(), ha="right", va="bottom", fontsize=8)
    ax.set_xlabel("Mean of methods")
    ax.set_ylabel("Difference")
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_waterfall(
    values: ArrayLike,
    *,
    labels: Sequence[Any] | None = None,
    title: str = "Waterfall plot",
    ylabel: str = "Change",
    threshold: float | None = None,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot ordered patient-level changes or response scores."""
    _apply_plot_style()
    arr = np.asarray(values, dtype=float)
    order = np.argsort(arr)
    arr = arr[order]
    labels_arr = np.asarray(labels, dtype=object)[order] if labels is not None else np.arange(1, len(arr) + 1)
    colors = np.where(arr >= 0, BOARISK_PALETTE["red"], BOARISK_PALETTE["blue"])
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(6, 0.12 * len(arr)), 4.8))
    else:
        fig = ax.figure
    ax.bar(np.arange(len(arr)), arr, color=colors, edgecolor=BOARISK_PALETTE["ink"], linewidth=0.4)
    ax.axhline(0, color=BOARISK_PALETTE["ink"], linewidth=1)
    if threshold is not None:
        ax.axhline(threshold, color=BOARISK_PALETTE["muted"], linestyle="--", linewidth=1)
    if len(arr) <= 40:
        ax.set_xticks(np.arange(len(arr)), labels=[str(x) for x in labels_arr], rotation=90)
    else:
        ax.set_xticks([])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_table_one_summary(
    data: Any,
    *,
    variable_col: str = "variable",
    p_col: str = "p_value",
    title: str = "Table 1 summary",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot Table 1 p-values as a compact overview."""
    df = pd.DataFrame(data).drop_duplicates(subset=[variable_col]).copy()
    _require_columns(df, [variable_col, p_col])
    plot_df = df[[variable_col, p_col]].rename(columns={variable_col: "label", p_col: "p_value"})
    fig, ax, _ = plot_significance_bars(plot_df, title=title, ax=ax, save_path=save_path, fmt=fmt)
    return fig, ax


def plot_survival_calibration(
    calibration_table: Any,
    *,
    observed_col: str = "observed",
    predicted_col: str = "predicted",
    title: str = "Survival calibration",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot fixed-horizon observed versus predicted survival/event risk."""

    _apply_plot_style()
    df = pd.DataFrame(calibration_table).copy()
    _require_columns(df, [observed_col, predicted_col])
    if ax is None:
        fig, ax = plt.subplots(figsize=(5.2, 5.2))
    else:
        fig = ax.figure
    ax.plot([0, 1], [0, 1], color=BOARISK_PALETTE["ink"], linestyle="--", linewidth=1)
    ax.scatter(df[predicted_col], df[observed_col], s=60, color=BOARISK_PALETTE["blue"], edgecolor=BOARISK_PALETTE["ink"])
    ax.plot(df[predicted_col], df[observed_col], color=BOARISK_PALETTE["blue"], linewidth=1)
    ax.set_xlabel("Predicted risk")
    ax.set_ylabel("Observed risk")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_decision_curve(
    data: Any,
    *,
    threshold_col: str = "threshold",
    model_col: str = "net_benefit_model",
    treat_all_col: str = "net_benefit_treat_all",
    treat_none_col: str = "net_benefit_treat_none",
    title: str = "Decision curve",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot net benefit over decision thresholds."""

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [threshold_col, model_col, treat_all_col, treat_none_col])
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.4, 4.8))
    else:
        fig = ax.figure
    ax.plot(df[threshold_col], df[model_col], label="Model", color=BOARISK_PALETTE["blue"], linewidth=2)
    ax.plot(df[threshold_col], df[treat_all_col], label="Treat all", color=BOARISK_PALETTE["orange"], linestyle="--")
    ax.plot(df[threshold_col], df[treat_none_col], label="Treat none", color=BOARISK_PALETTE["ink"], linestyle=":")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_time_dependent_auc(
    data: Any,
    *,
    time_col: str = "time",
    auc_col: str = "auc",
    title: str = "Time-dependent AUC",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot time-dependent AUC values from a precomputed table."""

    _apply_plot_style()
    df = pd.DataFrame(data).copy()
    _require_columns(df, [time_col, auc_col])
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.4, 4.2))
    else:
        fig = ax.figure
    ax.plot(df[time_col], df[auc_col], marker="o", color=BOARISK_PALETTE["purple"], linewidth=2)
    ax.axhline(0.5, color=BOARISK_PALETTE["ink"], linestyle="--", linewidth=1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Time")
    ax.set_ylabel("AUC")
    ax.set_title(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax


def plot_cohort_flow(
    data: Any,
    *,
    step_col: str = "step",
    n_col: str = "n",
    title: str = "Cohort flow",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot cohort counts across inclusion/exclusion steps."""

    return plot_patterned_bar(
        pd.DataFrame(data),
        x=step_col,
        y=n_col,
        title=title,
        ylabel="Patients",
        ax=ax,
        save_path=save_path,
        fmt=fmt,
    )


def plot_segmentation_overlay_grid(
    image: Any,
    mask: Any,
    *,
    slice_indices: Sequence[int] | None = None,
    label: int | None = None,
    alpha: float = 0.35,
    title: str = "Segmentation overlay",
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> tuple[Figure, np.ndarray]:
    """Plot CT/image slices with a mask overlay."""

    _apply_plot_style()
    img = np.asarray(image)
    seg = np.asarray(mask)
    if img.shape != seg.shape or img.ndim != 3:
        raise ValueError("image and mask must be aligned 3D arrays.")
    if slice_indices is None:
        indices = list(np.linspace(0, img.shape[0] - 1, min(6, img.shape[0]), dtype=int))
    else:
        indices = list(slice_indices)
    fig, axes = plt.subplots(1, len(indices), figsize=(max(6, 2.2 * len(indices)), 2.8))
    axes_arr = np.atleast_1d(axes)
    for ax_i, slice_idx in zip(axes_arr, indices):
        overlay = seg[slice_idx] == label if label is not None else seg[slice_idx].astype(bool)
        ax_i.imshow(img[slice_idx], cmap="gray")
        ax_i.imshow(np.ma.masked_where(~overlay, overlay), cmap="autumn", alpha=alpha)
        ax_i.set_title(f"slice {slice_idx}", fontsize=9)
        ax_i.axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, axes_arr


def plot_dice_by_label(
    data: Any,
    *,
    label_col: str = "label_name",
    dice_col: str = "dice",
    title: str = "Dice by label",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot Dice scores by segmentation label."""

    df = pd.DataFrame(data).copy()
    _require_columns(df, [label_col, dice_col])
    return plot_patterned_bar(df, x=label_col, y=dice_col, title=title, ylabel="Dice", ax=ax, save_path=save_path, fmt=fmt)


def plot_external_validation_metrics(
    data: Any,
    *,
    metric_col: str = "metric",
    value_col: str = "value",
    title: str = "External validation",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot external validation metrics from a dict or long table."""

    if isinstance(data, Mapping):
        df = pd.DataFrame({"metric": list(data.keys()), "value": list(data.values())})
    else:
        df = pd.DataFrame(data).copy()
    _require_columns(df, [metric_col, value_col])
    return plot_patterned_bar(df, x=metric_col, y=value_col, title=title, ylabel="Metric value", ax=ax, save_path=save_path, fmt=fmt)


def plot_feature_importance(
    importance_df: Any,
    *,
    top_n: int = 20,
    title: str = "Feature importance",
    ax: Axes | None = None,
    save_path: str | Path | None = None,
    fmt: str = "png",
) -> PlotReturn:
    """Plot top-N features from a feature-importance DataFrame.

    Expects columns ``feature`` and ``importance``.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.ml import plot_feature_importance
    >>> df = pd.DataFrame({"feature": ["a", "b"], "importance": [0.7, 0.3]})
    >>> fig, ax = plot_feature_importance(df, top_n=2)
    >>> plt.close(fig)
    """
    import pandas as pd

    _apply_plot_style()
    df = importance_df.head(top_n).sort_values("importance", ascending=True)
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * len(df))))
    else:
        fig = ax.figure
    ax.barh(df["feature"].astype(str), df["importance"])
    ax.set_xlabel("Importance")
    ax.set_title(title)
    _maybe_save(fig, save_path, fmt=fmt)
    return fig, ax
