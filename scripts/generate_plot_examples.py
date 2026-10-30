#!/usr/bin/env python3
"""Generate deterministic figure gallery assets used by the documentation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fyron import ml
from fyron.ml.plots import plot_feature_importance as plot_feature_importance_table
from fyron.plotting_palettes import PALETTES, get_colormap, get_palette
from fyron.survival import plot_kaplan_meier


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"


def _save(fig, filename: str, *aliases: str) -> None:
    for name in (filename, *aliases):
        fig.savefig(ASSETS / name, bbox_inches="tight", dpi=150)
    plt.close(fig)


def _polish(fig, *, width: float | None = None, height: float | None = None) -> None:
    if width is not None and height is not None:
        fig.set_size_inches(width, height, forward=True)
    fig.tight_layout()


def _asset_slug(name: str) -> str:
    return name.replace("_", "-")


def _palette_preview(name: str):
    spec = PALETTES[name]
    colors = get_palette(name)
    if spec.kind in {"sequential", "diverging"}:
        fig, ax = plt.subplots(figsize=(5.6, 1.25))
        gradient = np.linspace(0, 1, 512).reshape(1, -1)
        ax.imshow(gradient, aspect="auto", cmap=get_colormap(name))
        ax.set_axis_off()
        ax.set_title(name, loc="left", fontsize=10, pad=8)
        fig.tight_layout(pad=0.4)
        return fig

    fig, ax = plt.subplots(figsize=(5.6, 1.35))
    for index, color in enumerate(colors):
        ax.add_patch(plt.Rectangle((index, 0), 1, 1, facecolor=color, edgecolor="#1F2933", linewidth=0.55))
        ax.text(index + 0.5, -0.16, color.upper(), ha="center", va="top", fontsize=6.8, rotation=45)
    ax.set_xlim(0, len(colors))
    ax.set_ylim(-0.52, 1.05)
    ax.set_axis_off()
    ax.set_title(name, loc="left", fontsize=10, pad=8)
    fig.tight_layout(pad=0.4)
    return fig


def _palette_overview() -> None:
    names = list(PALETTES)
    fig, axes = plt.subplots(len(names), 1, figsize=(7.2, 0.46 * len(names) + 1.1))
    if len(names) == 1:
        axes = [axes]
    for ax, name in zip(axes, names, strict=True):
        spec = PALETTES[name]
        ax.set_axis_off()
        ax.text(-0.02, 0.5, name, ha="right", va="center", fontsize=8.5, transform=ax.transAxes)
        if spec.kind in {"sequential", "diverging"}:
            gradient = np.linspace(0, 1, 512).reshape(1, -1)
            ax.imshow(gradient, aspect="auto", cmap=get_colormap(name), extent=(0, 1, 0, 1))
        else:
            for index, color in enumerate(spec.colors):
                left = index / len(spec.colors)
                right = (index + 1) / len(spec.colors)
                ax.add_patch(plt.Rectangle((left, 0), right - left, 1, transform=ax.transAxes, facecolor=color, edgecolor="#1F2933", linewidth=0.35))
        ax.text(1.02, 0.5, spec.kind, ha="left", va="center", fontsize=8, color="#475569", transform=ax.transAxes)
    fig.suptitle("Fyron scientific palettes", x=0.09, ha="left", fontsize=12, y=0.995)
    fig.subplots_adjust(left=0.25, right=0.82, top=0.91, bottom=0.04, hspace=0.28)
    _save(fig, "palette-gallery-all.png")


def _hatch_preview() -> None:
    hatches = ["", "///", "\\\\\\", "xx", "..", "++", "--", "oo"]
    labels = ["none", "///", "\\\\\\", "xx", "..", "++", "--", "oo"]
    palette = get_palette("bf_vibrant_muted")
    colors = [palette[index % len(palette)] for index in range(len(hatches))]
    fig, ax = plt.subplots(figsize=(7.2, 2.2))
    x = np.arange(len(hatches))
    bars = ax.bar(x, np.ones(len(hatches)), color=colors, edgecolor="#111827", linewidth=0.85)
    for bar, hatch in zip(bars, hatches, strict=True):
        bar.set_hatch(hatch)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_yticks([])
    ax.set_ylim(0, 1.18)
    ax.set_title("Default Fyron hatch styles", loc="left", fontsize=11)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#CBD5E1")
    ax.tick_params(axis="x", length=0, pad=7)
    fig.tight_layout()
    _save(fig, "plotting-hatch-styles.png")


def _clinical_dataframe(rng: np.random.Generator) -> pd.DataFrame:
    rows = 156
    arm = rng.choice(["Control", "Treatment"], size=rows, p=[0.48, 0.52])
    event = rng.binomial(1, np.where(arm == "Treatment", 0.36, 0.50))
    stage = rng.choice(["II", "III", "IV"], size=rows, p=[0.28, 0.43, 0.29])
    risk = np.clip(
        rng.normal(0.43 + 0.18 * event + 0.08 * (stage == "IV"), 0.12, rows),
        0.02,
        0.98,
    )
    sma = rng.normal(49 - 5.2 * event + 2.0 * (arm == "Treatment"), 6.8, rows)
    vat = rng.normal(3.1 + 1.0 * event + 0.35 * (stage == "IV"), 0.9, rows).clip(0.4)
    albumin = rng.normal(4.0 - 0.28 * event, 0.35, rows)
    tumor_volume = rng.lognormal(mean=2.6 + 0.28 * event, sigma=0.45, size=rows)
    duration = rng.exponential(scale=np.where(event == 1, 350, 520), size=rows) + 45
    observed = rng.binomial(1, np.where(arm == "Treatment", 0.42, 0.56))
    return pd.DataFrame(
        {
            "arm": arm,
            "event": event,
            "stage": stage,
            "risk_score": risk,
            "sma": sma,
            "vat": vat,
            "albumin": albumin,
            "tumor_volume": tumor_volume,
            "time": duration.clip(20, 1080),
            "os_event": observed,
        }
    )


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    _palette_overview()
    for palette_name in PALETTES:
        fig = _palette_preview(palette_name)
        _save(fig, f"palette-{_asset_slug(palette_name)}.png")
    _hatch_preview()

    rng = np.random.default_rng(7)
    df = _clinical_dataframe(rng)

    y_true = rng.binomial(1, 0.42, size=180)
    y_prob = np.clip(rng.beta(2.2 + 2.0 * y_true, 3.0 - 0.6 * y_true, size=180), 0.02, 0.98)
    y_pred = (y_prob >= 0.5).astype(int)

    fig, _ = ml.plot_roc_curve(y_true, y_prob, title="ROC curve")
    _polish(fig, width=5.3, height=4.2)
    _save(fig, "figure-gallery-roc-curve.png")

    cv_rows = []
    for fold in range(5):
        fold_true = np.r_[np.zeros(32, dtype=int), np.ones(32, dtype=int)]
        fold_prob = np.r_[
            rng.normal(0.30 + fold * 0.01, 0.13, 32),
            rng.normal(0.68 - fold * 0.01, 0.13, 32),
        ].clip(0.01, 0.99)
        cv_rows.append(pd.DataFrame({"fold": f"Fold {fold + 1}", "y_true": fold_true, "y_prob": fold_prob}))
    cv_predictions = pd.concat(cv_rows, ignore_index=True)
    fig, _, _ = ml.plot_cross_validated_roc(cv_predictions, title="Cross-validated ROC")
    _polish(fig, width=5.6, height=4.4)
    _save(fig, "figure-gallery-cv-roc.png")

    fig, _ = ml.plot_precision_recall_curve(y_true, y_prob, title="Precision-recall")
    _polish(fig, width=5.3, height=4.2)
    _save(fig, "figure-gallery-precision-recall.png")

    fig, _ = ml.plot_calibration_curve(y_true, y_prob, n_bins=8, title="Calibration")
    _polish(fig, width=5.2, height=4.2)
    _save(fig, "figure-gallery-calibration.png")

    fig, _ = ml.plot_confusion_matrix(y_true, y_pred, title="Confusion matrix")
    _polish(fig, width=4.8, height=4.2)
    _save(fig, "figure-gallery-confusion-matrix.png")

    importance = pd.DataFrame(
        {
            "feature": ["Risk score", "Tumor volume", "Albumin", "L3 SMA", "VAT", "Age"],
            "importance": [0.31, 0.22, 0.16, 0.13, 0.10, 0.08],
        }
    )
    fig, _ = plot_feature_importance_table(importance, top_n=6, title="Feature importance")
    _polish(fig, width=6.2, height=3.7)
    _save(fig, "figure-gallery-feature-importance.png")

    missingness = pd.DataFrame(
        {
            "column": ["Albumin", "ECOG", "Smoking", "PD-L1", "Genomics"],
            "missing_percent": [4.5, 8.2, 12.5, 24.0, 38.0],
        }
    )
    fig, _ = ml.plot_missingness_bar(missingness, title="Missingness")
    _polish(fig, width=6.0, height=3.9)
    _save(fig, "figure-gallery-missingness-bar.png")

    selection = pd.DataFrame(
        {
            "feature": ["Risk score", "Tumor volume", "Albumin", "L3 SMA", "VAT", "Age", "SAT"],
            "selected": [True, True, True, True, False, False, False],
            "n_selected_methods": [5, 4, 4, 3, 2, 1, 1],
        }
    )
    fig, _ = ml.plot_feature_selection_summary(selection, top_n=7, title="Selection summary")
    _polish(fig, width=6.2, height=3.9)
    _save(fig, "figure-gallery-feature-selection-summary.png")

    stability = pd.DataFrame(
        {
            "feature": ["Risk score", "Tumor volume", "Albumin", "L3 SMA", "VAT", "Age", "SAT"],
            "selection_frequency": [0.92, 0.84, 0.76, 0.66, 0.48, 0.34, 0.28],
        }
    )
    fig, _ = ml.plot_stability_selection(stability, threshold=0.6, top_n=7, title="Stability selection")
    _polish(fig, width=6.2, height=3.9)
    _save(fig, "figure-gallery-stability-selection.png")

    method_a = rng.normal(42, 7.5, size=80)
    method_b = method_a + rng.normal(0.8, 3.0, size=80)
    fig, _ = ml.plot_bland_altman(method_a, method_b, title="Bland-Altman")
    _polish(fig, width=5.8, height=4.2)
    _save(fig, "figure-gallery-bland-altman.png")

    response = np.sort(rng.normal(-12, 24, size=42))
    response[::9] += 34
    fig, _ = ml.plot_waterfall(response, title="Tumor response", ylabel="Change (%)", threshold=-30)
    _polish(fig, width=6.4, height=4.0)
    _save(fig, "figure-gallery-waterfall.png")

    table_one = pd.DataFrame(
        {
            "variable": ["Age", "Sex", "Stage", "Albumin", "L3 SMA", "Tumor volume"],
            "p_value": [0.41, 0.74, 0.018, 0.06, 0.004, 0.031],
        }
    )
    fig, _ = ml.plot_table_one_summary(table_one, title="Table 1 p-values")
    _polish(fig, width=6.2, height=3.8)
    _save(fig, "figure-gallery-table-one-summary.png")

    survival_calibration = pd.DataFrame(
        {
            "predicted": [0.12, 0.24, 0.36, 0.48, 0.60, 0.72],
            "observed": [0.10, 0.22, 0.40, 0.46, 0.66, 0.70],
        }
    )
    fig, _ = ml.plot_survival_calibration(survival_calibration, title="Survival calibration")
    _polish(fig, width=5.0, height=4.4)
    _save(fig, "figure-gallery-survival-calibration.png")

    thresholds = np.linspace(0.05, 0.75, 24)
    decision_curve = pd.DataFrame(
        {
            "threshold": thresholds,
            "net_benefit_model": 0.18 * np.exp(-1.45 * thresholds) + 0.018,
            "net_benefit_treat_all": 0.10 - 0.14 * thresholds,
            "net_benefit_treat_none": np.zeros_like(thresholds),
        }
    )
    fig, _ = ml.plot_decision_curve(decision_curve, title="Decision curve")
    _polish(fig, width=5.8, height=4.0)
    _save(fig, "figure-gallery-decision-curve.png")

    td_auc = pd.DataFrame({"time": [6, 12, 18, 24, 36, 48], "auc": [0.68, 0.73, 0.75, 0.77, 0.74, 0.72]})
    fig, _ = ml.plot_time_dependent_auc(td_auc, title="Time-dependent AUC")
    _polish(fig, width=5.8, height=3.8)
    _save(fig, "figure-gallery-time-dependent-auc.png")

    dice = pd.DataFrame(
        {
            "label_name": ["Liver", "Spleen", "Kidney", "Muscle", "VAT"],
            "dice": [0.96, 0.94, 0.91, 0.87, 0.82],
        }
    )
    fig, _ = ml.plot_dice_by_label(dice, title="Dice by label")
    _polish(fig, width=5.8, height=3.8)
    _save(fig, "figure-gallery-dice-by-label.png")

    fig, _ = ml.plot_external_validation_metrics(
        {"AUC": 0.81, "Sensitivity": 0.74, "Specificity": 0.69, "F1": 0.71},
        title="External validation",
    )
    _polish(fig, width=5.8, height=4.0)
    _save(fig, "figure-gallery-external-validation.png")

    likert = pd.DataFrame(
        {
            "item": [
                "Image quality",
                "Image quality",
                "Image quality",
                "Image quality",
                "Workflow fit",
                "Workflow fit",
                "Workflow fit",
                "Workflow fit",
                "Trust",
                "Trust",
                "Trust",
                "Trust",
            ],
            "response": [
                "Disagree",
                "Neutral",
                "Agree",
                "Strongly agree",
                "Disagree",
                "Neutral",
                "Agree",
                "Strongly agree",
                "Disagree",
                "Neutral",
                "Agree",
                "Strongly agree",
            ],
            "count": [5, 9, 28, 18, 8, 14, 25, 13, 12, 16, 21, 11],
        }
    )
    fig, _, _ = ml.plot_likert_scale(
        likert,
        count_col="count",
        response_order=["Disagree", "Neutral", "Agree", "Strongly agree"],
        neutral_values=["Neutral"],
        title="Reader study Likert",
        palette="okabe_ito",
    )
    _polish(fig, width=8.0, height=3.8)
    _save(fig, "figure-gallery-likert-scale.png")

    waffle = pd.DataFrame(
        {
            "category": ["Final cohort", "Excluded", "Pending review"],
            "value": [62, 31, 7],
        }
    )
    fig, _, _ = ml.plot_waffle(waffle, title="Cohort composition", palette="bf_vibrant_muted")
    _polish(fig, width=5.8, height=4.3)
    _save(fig, "figure-gallery-waffle.png")

    fig, _ = ml.plot_risk_score_distribution(
        data=df,
        risk_col="risk_score",
        event_col="event",
        event_labels={0: "No event", 1: "Event"},
        title="Risk score distribution",
        ylabel="Predicted risk score",
        palette="bf_vibrant_muted",
    )
    _polish(fig, width=5.8, height=4.2)
    _save(fig, "figure-gallery-risk-score-distribution.png", "dummy-risk-score-distribution.png")

    coef_df = pd.DataFrame(
        {
            "feature": ["L3 SMA", "VAT", "Age", "Albumin", "Tumor volume", "SAT"],
            "coef": [-0.42, 0.38, 0.29, -0.31, 0.67, -0.18],
        }
    )
    fig, _ = ml.plot_signed_feature_weights(
        data=coef_df,
        feature_col="feature",
        weight_col="coef",
        top_n=6,
        title="Signed feature weights",
        xlabel="Model coefficient",
    )
    _polish(fig, width=6.8, height=3.8)
    _save(fig, "figure-gallery-signed-feature-weights.png", "dummy-signed-feature-weights.png")

    p_values = pd.DataFrame(
        {
            "comparison": ["L3 SMA", "VAT", "Albumin", "Age", "Tumor volume"],
            "p_value": [0.003, 0.048, 0.021, 0.19, 0.0008],
        }
    )
    fig, _, _ = ml.plot_significance_bars(
        data=p_values,
        label_col="comparison",
        p_col="p_value",
        threshold=0.05,
        title="Screening p-values",
    )
    _polish(fig, width=6.4, height=3.7)
    _save(fig, "figure-gallery-significance-bars.png", "dummy-significance-bars.png")

    volcano = pd.DataFrame(
        {
            "feature": [f"marker {i}" for i in range(1, 31)],
            "log2_fold_change": np.r_[np.linspace(-2.4, -0.2, 15), np.linspace(0.2, 2.6, 15)],
            "p_value": np.r_[np.linspace(0.0008, 0.18, 15), np.linspace(0.16, 0.0006, 15)],
            "contrast": ["Immune"] * 10 + ["Metabolic"] * 10 + ["Imaging"] * 10,
        }
    )
    fig, _ = ml.plot_volcano(volcano, group_col="contrast", top_n_labels=5, title="Feature screening volcano")
    _polish(fig, width=6.6, height=4.4)
    _save(fig, "figure-gallery-volcano.png")

    swimmer = pd.DataFrame(
        {
            "patient": [f"P{i:02d}" for i in range(1, 9)],
            "start": [0] * 8,
            "end": [7, 9, 12, 5, 15, 11, 8, 14],
            "arm": ["Control", "Control", "Treatment", "Treatment", "Treatment", "Control", "Treatment", "Control"],
            "event_time": [6, 8, 11, 4, 14, 9, 7, 13],
            "event": ["PD", "SD", "CR", "PR", "CR", "PD", "PR", "SD"],
        }
    )
    fig, _ = ml.plot_swimmer(swimmer, group_col="arm", xlabel="Months", title="Patient treatment timeline")
    _polish(fig, width=6.8, height=4.2)
    _save(fig, "figure-gallery-swimmer.png")

    rain = pd.DataFrame(
        {
            "group": np.repeat(["Low risk", "Intermediate", "High risk"], 24),
            "value": np.r_[rng.normal(1.1, 0.22, 24), rng.normal(1.65, 0.26, 24), rng.normal(2.25, 0.32, 24)],
        }
    )
    fig, _ = ml.plot_raincloud(rain, title="Biomarker raincloud", ylabel="Marker value")
    _polish(fig, width=6.4, height=4.2)
    _save(fig, "figure-gallery-raincloud.png")

    flow = pd.DataFrame(
        {
            "path": ["a", "a", "a", "b", "b", "b", "c", "c", "c", "d", "d", "d"],
            "stage": ["Screen", "Review", "Export"] * 4,
            "category": ["Eligible", "Accepted", "Clean", "Eligible", "Rejected", "Rejected", "Excluded", "Rejected", "Rejected", "Eligible", "Accepted", "Clean"],
            "value": [44, 44, 44, 18, 18, 18, 12, 12, 12, 26, 26, 26],
        }
    )
    fig, _ = ml.plot_alluvial_flow(flow, title="Cohort review flow")
    _polish(fig, width=6.8, height=4.4)
    _save(fig, "figure-gallery-alluvial-flow.png")

    heat_rows = []
    for feature in ["Age", "Albumin", "VAT", "SMA", "CRP", "Stage"]:
        for patient in [f"P{i}" for i in range(1, 7)]:
            heat_rows.append({"feature": feature, "sample": patient, "bin": rng.integers(-2, 3)})
    fig, _ = ml.plot_binned_marker_heatmap(pd.DataFrame(heat_rows), title="Binned marker heatmap")
    _polish(fig, width=6.6, height=4.2)
    _save(fig, "figure-gallery-binned-marker-heatmap.png")

    ages = np.arange(20, 81, 10)
    reference_rows = []
    trend_rows = []
    features = [
        ("ASAT", 4.0, 0.7, 0.020, 1.0),
        ("GFAT", 8.0, 1.4, -0.018, 1.3),
        ("VAT", 2.2, 0.9, 0.026, 0.9),
        ("Muscle", 5.8, -0.5, -0.010, 0.7),
        ("Liver Fat", 0.32, 0.04, 0.0014, 0.04),
    ]
    band_specs = [
        ("Below -1 SD", -3.0, -1.0),
        ("+/- 1 SD", -1.0, 1.0),
        ("+1 to +2 SD", 1.0, 2.0),
        ("+2 to +3 SD", 2.0, 3.0),
        ("Above +3 SD", 3.0, 5.0),
    ]
    for sex, sex_shift in [("Male", 0.45), ("Female", -0.35)]:
        for feature, base, curve, slope, spread in features:
            center = base + sex_shift * spread + curve * np.sin((ages - 24) / 24) + slope * (ages - 50)
            for age, center_value in zip(ages, center, strict=True):
                for band, low_delta, high_delta in band_specs:
                    reference_rows.append(
                        {
                            "age": age,
                            "sex": sex,
                            "feature": feature,
                            "band": band,
                            "lower": max(0.0, center_value + low_delta * spread),
                            "upper": max(0.0, center_value + high_delta * spread),
                        }
                    )
                trend_rows.append({"age": age, "sex": sex, "feature": feature, "value": center_value})
    fig, _ = ml.plot_reference_band_grid(
        pd.DataFrame(reference_rows),
        x="age",
        row="sex",
        col="feature",
        line_df=pd.DataFrame(trend_rows),
        line_y="value",
        feature_order=[feature[0] for feature in features],
        row_order=["Male", "Female"],
        band_preset="sd",
        title="Body composition reference bands",
        xlabel="Age (years)",
        ylabel="Value",
        figsize=(9.8, 5.6),
    )
    _save(fig, "figure-gallery-reference-band-grid.png")

    qq_df = pd.DataFrame(
        {
            "cohort": np.repeat(["Training residuals", "External residuals"], 80),
            "residual": np.r_[rng.normal(0.0, 1.0, 80), rng.standard_t(df=4, size=80) * 1.18 + 0.18],
        }
    )
    fig, _, _ = ml.plot_qq(
        qq_df,
        value_col="residual",
        group_col="cohort",
        title="Residual Q-Q plot",
        ylabel="Observed residual quantiles",
        palette="bf_vibrant_muted",
    )
    _polish(fig, width=5.8, height=4.5)
    _save(fig, "figure-gallery-qq-plot.png")

    forest_df = pd.DataFrame(
        {
            "subgroup": ["Low sarcopenia", "Intermediate", "High sarcopenia", "High VAT"],
            "hazard_ratio": [0.82, 1.0, 1.74, 1.42],
            "ci_lower": [0.52, 0.73, 1.15, 1.02],
            "ci_upper": [1.29, 1.37, 2.61, 1.98],
            "p_value": [0.37, 0.99, 0.008, 0.041],
            "n": [118, 142, 96, 104],
        }
    )
    fig, _ = ml.plot_forest_estimates(
        data=forest_df,
        label_col="subgroup",
        estimate_col="hazard_ratio",
        lower_col="ci_lower",
        upper_col="ci_upper",
        p_col="p_value",
        n_col="n",
        table_columns=False,
        title="Subgroup hazard ratios",
        xlabel="Hazard ratio",
    )
    _polish(fig, width=6.8, height=3.7)
    _save(fig, "figure-gallery-forest-estimates.png", "dummy-forest-estimates.png")

    ratio_df = pd.DataFrame(
        {
            "feature": ["Sarcopenia", "High VAT", "Albumin", "Age > 70", "Stage IV", "Immunotherapy"],
            "category": ["Body composition", "Body composition", "Laboratory", "Clinical", "Clinical", "Treatment"],
            "hazard_ratio": [1.78, 1.41, 0.68, 1.24, 2.16, 0.74],
            "ci_lower": [1.18, 1.03, 0.49, 0.92, 1.44, 0.53],
            "ci_upper": [2.68, 1.94, 0.94, 1.68, 3.24, 1.04],
            "p_value": [0.006, 0.031, 0.018, 0.15, 0.0004, 0.08],
            "n": [156, 142, 188, 201, 97, 121],
        }
    )
    fig, _ = ml.plot_directional_ratio_rows(
        data=ratio_df,
        feature_col="feature",
        ratio_col="hazard_ratio",
        lower_col="ci_lower",
        upper_col="ci_upper",
        p_col="p_value",
        group_col="category",
        n_col="n",
        ratio_label="Hazard ratio",
        title="Directional hazard ratios",
    )
    _polish(fig, width=9.8, height=4.2)
    _save(fig, "figure-gallery-directional-ratio-rows.png", "dummy-directional-ratio-rows.png")

    fig, _, _ = ml.plot_grouped_boxplot(
        df,
        x="arm",
        y="sma",
        comparisons=[("Control", "Treatment")],
        p_adjust="fdr_bh",
        annotation_format="star",
        return_stats=True,
        title="SMA by treatment arm",
        ylabel="L3 SMA",
        palette="okabe_ito",
    )
    _polish(fig, width=5.8, height=4.2)
    _save(fig, "figure-gallery-grouped-boxplot.png")

    fig, _ = ml.plot_density(
        df,
        x="risk_score",
        hue="event",
        title="Risk score density",
        xlabel="Risk score",
        rug=True,
        palette="okabe_ito",
    )
    _polish(fig, width=5.8, height=4.0)
    _save(fig, "figure-gallery-density.png")

    geyser_like = pd.concat(
        [
            pd.DataFrame(
                {
                    "waiting": rng.normal(58, 5.5, 90),
                    "duration": rng.normal(2.2, 0.35, 90),
                    "kind": "short",
                }
            ),
            pd.DataFrame(
                {
                    "waiting": rng.normal(80, 7.0, 110),
                    "duration": rng.normal(4.1, 0.45, 110),
                    "kind": "long",
                }
            ),
        ],
        ignore_index=True,
    )
    fig, _ = ml.plot_filled_kde(
        geyser_like,
        x="waiting",
        y="duration",
        hue="kind",
        title="Filled KDE by group",
        xlabel="Waiting time",
        ylabel="Duration",
        palette="okabe_ito",
    )
    _polish(fig, width=5.8, height=4.4)
    _save(fig, "figure-gallery-filled-kde.png")

    fig, _ = ml.plot_histogram(
        df,
        x="tumor_volume",
        hue="event",
        stat="percent",
        multiple="layer",
        title="Tumor volume histogram",
        xlabel="Tumor volume",
        palette="okabe_ito",
    )
    _polish(fig, width=5.8, height=4.0)
    _save(fig, "figure-gallery-histogram.png")

    fig, _ = ml.plot_swarmplot(
        df.sample(72, random_state=7),
        x="stage",
        y="vat",
        hue="event",
        title="VAT by stage",
        ylabel="VAT volume",
        palette="okabe_ito",
    )
    _polish(fig, width=5.8, height=4.0)
    _save(fig, "figure-gallery-swarmplot.png")

    fig, _, _ = ml.plot_correlation_heatmap(
        df,
        columns=["risk_score", "sma", "vat", "albumin", "tumor_volume"],
        title="Feature correlation",
        mask_upper=True,
        cmap="fyron_diverging_teal_orange",
    )
    _polish(fig, width=5.4, height=5.0)
    _save(fig, "figure-gallery-correlation-heatmap.png")

    fig, _ = ml.plot_metric_bars(
        {
            "RF": {"auc": 0.82, "sensitivity": 0.74, "specificity": 0.71, "f1": 0.70},
            "XGB": {"auc": 0.85, "sensitivity": 0.77, "specificity": 0.73, "f1": 0.74},
        },
        metrics_to_plot=["auc", "sensitivity", "specificity", "f1"],
        title="Validation metrics",
    )
    _polish(fig, width=6.1, height=4.1)
    _save(fig, "figure-gallery-metric-bars.png")

    flow = pd.DataFrame(
        {
            "step": ["Raw export", "Eligible diagnosis", "Baseline CT", "Complete endpoint", "Final cohort"],
            "n": [420, 318, 246, 221, 208],
        }
    )
    fig, _ = ml.plot_cohort_flow(flow, title="Cohort inclusion flow")
    _polish(fig, width=7.0, height=4.2)
    _save(fig, "figure-gallery-cohort-flow.png")

    patterned = pd.DataFrame(
        {
            "endpoint": ["Response", "Response", "Toxicity", "Toxicity"],
            "cohort": ["Control", "Treatment", "Control", "Treatment"],
            "rate": [0.31, 0.46, 0.12, 0.18],
            "ci_half_width": [0.05, 0.06, 0.03, 0.04],
        }
    )
    fig, _ = ml.plot_patterned_bar(
        patterned,
        x="endpoint",
        y="rate",
        group="cohort",
        error="ci_half_width",
        title="Endpoint rates",
        ylabel="Rate",
        palette="bf_vibrant_muted",
        hatches=["", "///"],
        annotate=True,
    )
    _polish(fig, width=5.8, height=4.0)
    _save(fig, "figure-gallery-patterned-bar.png")

    km = plot_kaplan_meier(
        df,
        duration_col="time",
        event_col="os_event",
        group_col="arm",
        at_risk_counts=True,
        annotate_logrank=True,
        palette="okabe_ito",
        xlim=(0, 900),
        title="Overall survival",
        figsize=(7.2, 5.1),
    )
    _polish(km.figure, width=7.0, height=5.0)
    _save(km.figure, "figure-gallery-km-at-risk.png")

    reference_time = np.array([0, 180, 360, 540, 720, 900], dtype=float)
    km_reference_bands = pd.DataFrame(
        {
            "time": np.tile(reference_time, 3),
            "lower": np.r_[
                [0.78, 0.72, 0.64, 0.55, 0.47, 0.39],
                [0.48, 0.40, 0.32, 0.24, 0.17, 0.11],
                [0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
            ],
            "upper": np.r_[
                [1.00, 0.94, 0.86, 0.77, 0.68, 0.59],
                [0.78, 0.72, 0.64, 0.55, 0.47, 0.39],
                [0.48, 0.40, 0.32, 0.24, 0.17, 0.11],
            ],
            "band": ["Favorable"] * len(reference_time)
            + ["Intermediate"] * len(reference_time)
            + ["Poor"] * len(reference_time),
        }
    )
    km_bands = plot_kaplan_meier(
        df,
        duration_col="time",
        event_col="os_event",
        group_col="arm",
        confidence_interval=False,
        annotate_logrank=True,
        palette="okabe_ito",
        xlim=(0, 900),
        xlabel="Days",
        title="Overall survival with reference bands",
        figsize=(7.0, 5.0),
        reference_bands=km_reference_bands,
        reference_band_preset="survival",
        reference_band_alpha=0.28,
    )
    _polish(km_bands.figure, width=7.0, height=5.0)
    _save(km_bands.figure, "figure-gallery-km-reference-bands.png")


if __name__ == "__main__":
    main()
