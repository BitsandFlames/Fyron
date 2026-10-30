"""Tests for expanded clinical plotting functions."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from fyron import plotting as fp
from fyron.survival import fit_multivariate_cox


def test_expanded_plotting_functions_render() -> None:
    figs = []
    figs.append(fp.plot_survival_calibration(pd.DataFrame({"observed": [0.1, 0.4], "predicted": [0.2, 0.5]}))[0])
    figs.append(fp.plot_decision_curve(pd.DataFrame({"threshold": [0.1, 0.2], "net_benefit_model": [0.2, 0.1], "net_benefit_treat_all": [0.1, 0.0], "net_benefit_treat_none": [0.0, 0.0]}))[0])
    figs.append(fp.plot_time_dependent_auc(pd.DataFrame({"time": [12, 24], "auc": [0.7, 0.75]}))[0])
    figs.append(fp.plot_cohort_flow(pd.DataFrame({"step": ["screened", "included"], "n": [100, 80]}))[0])
    figs.append(fp.plot_dice_by_label(pd.DataFrame({"label_name": ["liver"], "dice": [0.91]}))[0])
    figs.append(fp.plot_external_validation_metrics({"auc": 0.8, "sensitivity": 0.7})[0])
    fig, _ = fp.plot_segmentation_overlay_grid(
        np.zeros((2, 4, 4)),
        np.ones((2, 4, 4)),
        slice_indices=np.array([0, 1]),
    )
    figs.append(fig)
    for item in figs:
        assert item is not None
        plt.close(item)


def test_stat_annotations_and_distribution_plots() -> None:
    df = pd.DataFrame(
        {
            "group": ["Low"] * 8 + ["High"] * 8,
            "sex": ["F", "M"] * 8,
            "value": [1.0, 1.1, 1.2, 1.1, 1.3, 1.2, 1.1, 1.0, 2.0, 2.1, 2.2, 2.0, 2.3, 2.1, 2.2, 2.4],
            "score": np.linspace(0.1, 0.9, 16),
        }
    )
    stats = fp.stat_test_pairs(
        df,
        x="group",
        y="value",
        pairs=[("Low", "High")],
        p_adjust="fdr_bh",
    )
    assert {"p_value", "p_adjusted", "annotation", "n_a", "n_b"}.issubset(stats.columns)
    assert fp.format_p_value_annotation(0.0005) == "***"

    fig1, ax1, table1 = fp.plot_grouped_boxplot(
        df,
        x="group",
        y="value",
        comparisons=[("Low", "High")],
        p_adjust="fdr_bh",
        return_stats=True,
    )
    assert "annotation" in table1.columns
    assert len(ax1.texts) >= 1
    fig2, _ = fp.plot_histogram(df, x="score", hue="group", stat="percent", multiple="dodge")
    kde2d = pd.DataFrame(
        {
            "waiting": np.r_[np.linspace(48, 64, 24), np.linspace(68, 92, 24)],
            "duration": np.r_[np.linspace(1.7, 3.0, 24), np.linspace(3.3, 5.0, 24)],
            "kind": ["short"] * 24 + ["long"] * 24,
        }
    )
    fig_kde, ax_kde = fp.plot_filled_kde(
        kde2d,
        x="waiting",
        y="duration",
        hue="kind",
        fill=True,
    )
    assert ax_kde.get_xlabel() == "Waiting"
    assert len(ax_kde.collections) >= 1
    fig3, ax3, table3 = fp.plot_swarmplot(
        df,
        x="group",
        y="value",
        hue="sex",
        comparisons=[(("Low", "F"), ("High", "F"))],
        return_stats=True,
    )
    assert "p_value" in table3.columns
    assert len(ax3.collections) >= 1
    for fig in [fig1, fig2, fig_kde, fig3]:
        plt.close(fig)


def test_grouped_correlation_and_hazard_ratio_plots() -> None:
    df = pd.DataFrame(
        {
            "group": ["A"] * 8 + ["B"] * 8,
            "x1": np.arange(16, dtype=float),
            "x2": np.arange(16, dtype=float) * 1.5,
            "x3": np.r_[np.arange(8), np.arange(8)[::-1]].astype(float),
        }
    )
    fig1, axes, corr = fp.plot_grouped_correlation_heatmaps(
        df,
        group_col="group",
        columns=["x1", "x2", "x3"],
        annotate_significance=True,
    )
    assert len(axes) == 2
    assert {"variable_a", "variable_b", "correlation", "group"}.issubset(corr.columns)

    survival = pd.DataFrame(
        {
            "time": [5, 7, 9, 11, 13, 15, 17, 19],
            "event": [1, 1, 0, 1, 0, 1, 1, 0],
            "age": [50, 54, 58, 61, 64, 66, 70, 74],
            "risk": [0, 0, 0, 1, 1, 1, 1, 0],
        }
    )
    cox = fit_multivariate_cox(survival, duration_col="time", event_col="event", covariates=["age", "risk"])
    fig2, _ = fp.plot_hazard_ratios(cox)
    plt.close(fig1)
    plt.close(fig2)


def test_directional_ratio_rows_render_and_validate() -> None:
    ratios = pd.DataFrame(
        {
            "feature": ["Low albumin", "High VAT", "Immunotherapy"],
            "odds_ratio": [1.82, 1.36, 0.72],
            "ci_lower": [1.12, 0.98, 0.51],
            "ci_upper": [2.94, 1.88, 1.02],
            "p_value": [0.015, 0.061, 0.068],
            "category": ["Laboratory", "Body composition", "Treatment"],
        }
    )
    fig, ax = fp.plot_directional_ratio_rows(
        ratios,
        ratio_col="odds_ratio",
        p_col="p_value",
        group_col="category",
        ratio_label="Odds ratio",
        title="Feature odds ratios",
    )
    assert ax.get_xlabel() == "Odds ratio"
    assert ax.get_title() == "Feature odds ratios"
    assert len(ax.collections) >= 1
    assert {"OR", "95% CI", "p value"}.issubset({text.get_text() for text in ax.texts})
    assert fp.plot_directional_ratio_rows is not None
    plt.close(fig)

    point_fig, point_ax = fp.plot_directional_ratio_rows(
        pd.DataFrame({"feature": ["Albumin", "VAT"], "ratio": [0.74, 1.32]}),
        ratio_label="Odds ratio",
    )
    assert point_ax.get_xlabel() == "Odds ratio"
    plt.close(point_fig)

    bare_fig, bare_ax = fp.plot_directional_ratio_rows(
        ratios,
        ratio_col="odds_ratio",
        p_col="p_value",
        annotate=False,
    )
    assert "OR" not in {text.get_text() for text in bare_ax.texts}
    plt.close(bare_fig)

    with pytest.raises(ValueError, match="columns not found"):
        fp.plot_directional_ratio_rows(ratios.drop(columns=["odds_ratio"]), ratio_col="odds_ratio")
    with pytest.raises(ValueError, match="positive"):
        fp.plot_directional_ratio_rows(pd.DataFrame({"feature": ["x"], "ratio": [0.0]}))
    with pytest.raises(ValueError, match="at least one"):
        fp.plot_directional_ratio_rows(pd.DataFrame({"feature": ["x"], "ratio": [float("nan")]}))


def test_journal_style_plot_helpers_render_and_validate() -> None:
    volcano = pd.DataFrame(
        {
            "feature": [f"gene_{i}" for i in range(10)],
            "log2_fold_change": np.linspace(-2.2, 2.4, 10),
            "p_value": [0.0008, 0.002, 0.03, 0.2, 0.7, 0.4, 0.04, 0.012, 0.003, 0.0005],
            "contrast": ["A"] * 5 + ["B"] * 5,
        }
    )
    fig1, ax1 = fp.plot_volcano(volcano, group_col="contrast", top_n_labels=3)
    assert ax1.get_title() == "Volcano plot"

    swimmer = pd.DataFrame(
        {
            "patient": ["P1", "P2", "P3"],
            "start": [0, 0, 0],
            "end": [8, 12, 5],
            "arm": ["Control", "Treatment", "Treatment"],
            "event_time": [6, 10, 4],
            "event": ["PD", "CR", "PR"],
        }
    )
    fig2, ax2 = fp.plot_swimmer(swimmer, group_col="arm")
    assert ax2.get_xlabel() == "Time"

    rain = pd.DataFrame(
        {
            "group": ["Low"] * 8 + ["High"] * 8,
            "value": np.r_[np.linspace(1.0, 1.8, 8), np.linspace(2.0, 3.1, 8)],
        }
    )
    fig3, ax3 = fp.plot_raincloud(rain)
    assert ax3.get_title() == "Raincloud plot"

    flow = pd.DataFrame(
        {
            "path": ["a", "a", "a", "b", "b", "b", "c", "c", "c"],
            "stage": ["Screen", "Review", "Export"] * 3,
            "category": ["Eligible", "Accepted", "Clean", "Eligible", "Rejected", "Rejected", "Excluded", "Rejected", "Rejected"],
            "value": [20, 20, 20, 8, 8, 8, 5, 5, 5],
        }
    )
    fig4, ax4 = fp.plot_alluvial_flow(flow)
    assert ax4.get_title() == "Alluvial flow"

    heat = pd.DataFrame(
        {
            "feature": ["Age", "Age", "Albumin", "Albumin"],
            "sample": ["P1", "P2", "P1", "P2"],
            "bin": [-1, 1, 0, -1],
        }
    )
    fig5, ax5 = fp.plot_binned_marker_heatmap(heat)
    assert ax5.get_title() == "Binned marker heatmap"

    for fig in [fig1, fig2, fig3, fig4, fig5]:
        plt.close(fig)

    with pytest.raises(ValueError, match="positive p-value"):
        fp.plot_volcano(pd.DataFrame({"feature": ["x"], "log2_fold_change": [1.0], "p_value": [0.0]}))
    with pytest.raises(ValueError, match="at least two stages"):
        fp.plot_alluvial_flow(pd.DataFrame({"path": ["a"], "stage": ["only"], "category": ["x"], "value": [1]}))
    with pytest.raises(ValueError, match="at least one complete numeric row"):
        fp.plot_raincloud(pd.DataFrame({"group": ["x"], "value": [float("nan")]}))


def test_reference_band_grid_renders_and_validates(tmp_path) -> None:
    ages = np.array([20, 40, 60], dtype=float)
    bands = []
    lines = []
    band_specs = [
        ("Below -1 SD", -3.0, -1.0),
        ("+/- 1 SD", -1.0, 1.0),
        ("+1 to +2 SD", 1.0, 2.0),
    ]
    for sex, sex_offset in [("Male", 0.4), ("Female", -0.2)]:
        for feature, feature_offset in [("VAT", 0.0), ("Muscle", 2.0)]:
            center = 4.0 + feature_offset + sex_offset + 0.02 * (ages - 40)
            for age, center_value in zip(ages, center, strict=True):
                for band, low_delta, high_delta in band_specs:
                    bands.append(
                        {
                            "age": age,
                            "sex": sex,
                            "feature": feature,
                            "band": band,
                            "lower": center_value + low_delta,
                            "upper": center_value + high_delta,
                        }
                    )
                lines.append({"age": age, "sex": sex, "feature": feature, "value": center_value + 0.2})

    save_path = tmp_path / "reference-bands.png"
    fig, axes = fp.plot_reference_band_grid(
        pd.DataFrame(bands),
        x="age",
        row="sex",
        col="feature",
        line_df=pd.DataFrame(lines),
        line_y="value",
        feature_order=["VAT", "Muscle"],
        row_order=["Male", "Female"],
        band_preset="sd",
        band_colors={"Below -1 SD": "#99D98C", "+/- 1 SD": "#E9F66D", "+1 to +2 SD": "#F4A261"},
        xlabel="Age (years)",
        ylabel="Volume (L)",
        title="Body composition reference bands",
        save_path=save_path,
    )
    assert axes.shape == (2, 2)
    assert axes[0, 0].get_title() == "VAT"
    assert any(text.get_text() == "Age (years)" for text in fig.texts)
    assert axes[0, 0].get_ylabel() == "Male\nVolume (L)"
    assert len(axes[0, 0].collections) == 3
    assert len(axes[0, 0].lines) == 1
    assert save_path.exists()
    plt.close(fig)

    with pytest.raises(ValueError, match="columns not found"):
        fp.plot_reference_band_grid(pd.DataFrame(bands).drop(columns=["lower"]), x="age")
    bad_bounds = pd.DataFrame(bands).copy()
    bad_bounds.loc[0, "lower"] = bad_bounds.loc[0, "upper"] + 1
    with pytest.raises(ValueError, match="lower_col <= upper_col"):
        fp.plot_reference_band_grid(bad_bounds, x="age")
    with pytest.raises(ValueError, match="line_y must be provided"):
        fp.plot_reference_band_grid(pd.DataFrame(bands), x="age", line_df=pd.DataFrame(lines))
    with pytest.raises(ValueError, match="band_preset"):
        fp.plot_reference_band_grid(pd.DataFrame(bands), x="age", band_preset="unknown")


def test_qq_plot_renders_input_modes_and_validates(tmp_path) -> None:
    rng = np.random.default_rng(21)
    residuals = pd.DataFrame(
        {
            "cohort": ["Train"] * 28 + ["External"] * 28,
            "residual": np.r_[rng.normal(0.0, 1.0, 28), rng.standard_t(4, 28) * 1.15],
            "score": np.r_[rng.normal(0.4, 0.12, 28), rng.normal(0.52, 0.18, 28)],
        }
    )
    residuals.loc[0, "residual"] = np.nan
    residuals.loc[3, "score"] = np.inf

    save_path = tmp_path / "qq.png"
    fig, axes, table = fp.plot_qq(
        residuals,
        value_col="residual",
        group_col="cohort",
        title="Residual normality",
        save_path=save_path,
    )
    assert axes.shape == (1, 1)
    assert set(table["group"]) == {"Train", "External"}
    assert table["observed_quantile"].notna().all()
    assert np.isfinite(table["observed_quantile"]).all()
    assert save_path.exists()
    assert len(axes[0, 0].collections) == 2
    plt.close(fig)

    for line in ["quartile", "fit", "identity", None]:
        fig, axes, table = fp.plot_qq([0.1, 0.4, 0.9, 1.1, 1.4, 1.8], line=line)
        assert axes.shape == (1, 1)
        assert len(table) == 6
        if line is None:
            assert len(axes[0, 0].lines) == 0
        else:
            assert len(axes[0, 0].lines) == 1
        plt.close(fig)

    fig, axes, table = fp.plot_qq(residuals, columns=["residual", "score"], group_col="cohort", facet=True)
    assert axes.shape == (2, 3)
    assert set(table["variable"]) == {"residual", "score"}
    plt.close(fig)

    fig, _, table = fp.plot_qq(residuals[["cohort", "residual"]], group_col="cohort")
    assert set(table["variable"]) == {"residual"}
    plt.close(fig)

    with pytest.raises(ValueError, match="columns not found"):
        fp.plot_qq(residuals, value_col="missing")
    with pytest.raises(ValueError, match="columns must contain"):
        fp.plot_qq(residuals, columns=[])
    with pytest.raises(ValueError, match="theoretical"):
        fp.plot_qq(residuals["residual"], theoretical="lognormal")
    with pytest.raises(ValueError, match="line"):
        fp.plot_qq(residuals["residual"], line="bad")
    with pytest.raises(ValueError, match="at least 3 finite values"):
        fp.plot_qq([1.0, np.nan, 2.0])
    with pytest.raises(ValueError, match="either value_col or columns"):
        fp.plot_qq(residuals, value_col="residual", columns=["score"])
    with pytest.raises(ValueError, match="ax cannot be used"):
        fig, ax = plt.subplots()
        try:
            fp.plot_qq(residuals, value_col="residual", group_col="cohort", facet=True, ax=ax)
        finally:
            plt.close(fig)


def test_scientific_palettes_and_named_palette_rendering(tmp_path) -> None:
    colors = fp.get_palette("okabe_ito", n=3)
    assert colors == ["#000000", "#E69F00", "#56B4E9"]
    assert fp.get_palette("okabe_ito", n=2, reverse=True) == ["#CC79A7", "#D55E00"]
    with pytest.warns(UserWarning):
        cycled = fp.get_palette("nature_cool", n=5)
    assert len(cycled) == 5
    with pytest.raises(ValueError):
        fp.get_palette("not_a_palette")

    palettes = fp.list_palettes()
    assert {"name", "kind", "max_recommended", "colorblind_safe", "source_note"}.issubset(palettes.columns)
    assert "okabe_ito" in set(palettes["name"])
    assert {"bf", "bf_core", "bf_flames", "bf_embers", "bf_vibrant", "bf_vibrant_muted"}.issubset(set(palettes["name"]))
    assert fp.get_palette("bf_core", n=2) == ["#243B53", "#4D9ED8"]
    assert fp.get_palette("bf_vibrant", n=5) == ["#D72660", "#4E2284", "#FFC845", "#009DE0", "#1C163D"]
    assert fp.get_palette("bf_vibrant_muted", n=5) == ["#B84A6D", "#66508D", "#E6B65A", "#3F9FCB", "#332E55"]
    cmap = fp.get_colormap("fyron_diverging_blue_red")
    assert cmap.name == "fyron_diverging_blue_red"
    lum = fp.palette_luminance_table("okabe_ito")
    contrast = fp.palette_grayscale_contrast("okabe_ito")
    assert {"hex", "relative_luminance", "recommended_text_color"}.issubset(lum.columns)
    assert "luminance_delta" in contrast.columns
    fig0, _ = fp.preview_palette("okabe_ito", save_path=tmp_path / "palette.png")
    assert (tmp_path / "palette.png").exists()

    df = pd.DataFrame(
        {
            "group": ["Low"] * 6 + ["High"] * 6,
            "value": [1.0, 1.2, 1.1, 1.3, 1.2, 1.0, 2.0, 2.1, 2.3, 2.2, 2.0, 2.4],
            "score": np.linspace(0.1, 0.9, 12),
            "x2": np.linspace(1.0, 2.0, 12),
        }
    )
    fig1, _ = fp.plot_grouped_boxplot(df, x="group", y="value", palette="okabe_ito")
    fig2, _ = fp.plot_swarmplot(df, x="group", y="value", palette="bf")
    fig3, _ = fp.plot_histogram(df, x="score", hue="group", palette="muted_scientific")
    fig4, _ = fp.plot_density(df, x="score", hue="group", palette="nature_cool")
    fig5, _, _ = fp.plot_correlation_heatmap(df, columns=["value", "score", "x2"], cmap="fyron_diverging_teal_orange")
    survival = pd.DataFrame(
        {
            "time": [5, 7, 9, 11, 13, 15],
            "event": [1, 0, 1, 1, 0, 1],
            "group": ["Low", "Low", "Low", "High", "High", "High"],
        }
    )
    km = fp.plot_kaplan_meier(survival, duration_col="time", event_col="event", group_col="group", palette="okabe_ito")
    for fig in [fig0, fig1, fig2, fig3, fig4, fig5, km.figure]:
        plt.close(fig)


def test_likert_waffle_and_cross_validated_roc_plots() -> None:
    likert = pd.DataFrame(
        {
            "item": ["Clarity", "Clarity", "Clarity", "Trust", "Trust", "Trust"],
            "response": ["Disagree", "Neutral", "Agree", "Disagree", "Neutral", "Agree"],
            "count": [8, 12, 30, 14, 16, 20],
        }
    )
    fig1, ax1, likert_table = fp.plot_likert_scale(
        likert,
        count_col="count",
        response_order=["Disagree", "Neutral", "Agree"],
        title="Reader survey",
    )
    assert {"item", "response", "count", "percent", "side", "plot_value"}.issubset(likert_table.columns)
    assert likert_table.groupby("item")["percent"].sum().round(6).eq(100).all()
    assert "Neutral" in set(likert_table.loc[likert_table["side"] == "neutral", "response"])
    assert ax1.get_title() == "Reader survey"

    waffle = pd.DataFrame({"category": ["Eligible", "Excluded", "Pending"], "value": [64, 28, 8]})
    fig2, _, waffle_table = fp.plot_waffle(waffle, total=100, rows=10, title="Cohort mix")
    assert {"category", "value", "proportion", "cells"}.issubset(waffle_table.columns)
    assert int(waffle_table["cells"].sum()) == 100

    rng = np.random.default_rng(11)
    folds = []
    for fold in range(3):
        y_true = np.r_[np.zeros(18, dtype=int), np.ones(18, dtype=int)]
        y_prob = np.r_[rng.normal(0.32, 0.12, 18), rng.normal(0.68, 0.12, 18)].clip(0.01, 0.99)
        folds.append(pd.DataFrame({"fold": f"fold {fold + 1}", "y_true": y_true, "y_prob": y_prob}))
    cv = pd.concat(folds, ignore_index=True)
    fig3, _, roc_table = fp.plot_cross_validated_roc(cv, title="CV ROC")
    assert {"fold", "auc", "n", "kind"}.issubset(roc_table.columns)
    assert {"mean", "std"}.issubset(set(roc_table["fold"]))
    assert roc_table.loc[roc_table["kind"] == "fold", "auc"].between(0, 1).all()

    bad = pd.DataFrame({"fold": ["a", "a"], "y_true": [1, 1], "y_prob": [0.8, 0.9]})
    with pytest.raises(ValueError, match="exactly two outcome classes"):
        fp.plot_cross_validated_roc(bad)

    from fyron import ml
    from fyron import plotting

    assert ml.plot_likert_scale is plotting.plot_likert_scale
    assert ml.plot_waffle is plotting.plot_waffle
    assert ml.plot_cross_validated_roc is plotting.plot_cross_validated_roc
    assert ml.plot_filled_kde is plotting.plot_filled_kde

    for fig in [fig1, fig2, fig3]:
        plt.close(fig)
