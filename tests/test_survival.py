"""Tests for fyron.survival."""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from fyron.survival import (
    calculate_rmst,
    check_ph_assumptions,
    compare_rmst,
    cox_forest_table,
    create_survival_groups,
    fit_cox_time_interactions,
    fit_multivariate_cox,
    fit_time_varying_cox,
    fit_univariate_cox,
    fit_weibull_aft,
    plot_aft_survival_curves,
    plot_kaplan_meier,
    plot_schoenfeld_residuals,
    run_survival_sensitivity_analysis,
    schoenfeld_residuals_table,
    schoenfeld_test_table,
    survival_prediction_table,
    train_gradient_survival_boosting,
)


@pytest.fixture
def survival_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 120
    time = rng.exponential(scale=8.0, size=n) + 0.5
    event = rng.binomial(1, 0.65, size=n)
    age = rng.normal(55, 12, size=n)
    sex = rng.choice(["F", "M"], size=n)
    tumor_stage = rng.choice(["I", "II", "III"], size=n, p=[0.35, 0.4, 0.25])
    risk_score = rng.normal(0, 1, size=n)
    return pd.DataFrame(
        {
            "time": time,
            "event": event,
            "age": age,
            "sex": sex,
            "tumor_stage": tumor_stage,
            "risk_score": risk_score,
        }
    )


def test_create_survival_groups_categorical(survival_df: pd.DataFrame) -> None:
    out = create_survival_groups(survival_df, "tumor_stage", "categorical", "g")
    assert out["g"].nunique() == survival_df["tumor_stage"].nunique()


def test_create_survival_groups_median(survival_df: pd.DataFrame) -> None:
    out = create_survival_groups(survival_df, "risk_score", "median", "g")
    assert set(out["g"].unique()) == {"below_median", "above_median"}


def test_create_survival_groups_tertile(survival_df: pd.DataFrame) -> None:
    out = create_survival_groups(survival_df, "risk_score", "tertile", "g")
    assert out["g"].nunique() == 3


def test_create_survival_groups_quartile(survival_df: pd.DataFrame) -> None:
    out = create_survival_groups(survival_df, "risk_score", "quartile", "g")
    assert out["g"].nunique() == 4


def test_create_survival_groups_custom_bins(survival_df: pd.DataFrame) -> None:
    out = create_survival_groups(
        survival_df,
        "age",
        "custom",
        "g",
        bins=[0, 50, 65, 100],
        labels=["young", "mid", "older"],
    )
    assert out["g"].nunique() == 3


def test_plot_kaplan_meier_basic(survival_df: pd.DataFrame) -> None:
    res = plot_kaplan_meier(
        survival_df,
        "time",
        "event",
        group_col="tumor_stage",
        title="KM by stage",
        figsize=(6, 4),
    )
    assert len(res.fitters) == survival_df["tumor_stage"].nunique()
    assert res.logrank is not None
    plt.close(res.figure)


def test_plot_kaplan_meier_risk_counts(survival_df: pd.DataFrame) -> None:
    res = plot_kaplan_meier(
        survival_df,
        "time",
        "event",
        group_col="sex",
        at_risk_counts=True,
        show_censors=True,
        xlim=(0, 10),
        annotate_logrank=True,
    )
    assert res.logrank is not None
    assert tuple(round(v) for v in res.axes.get_xlim()) == (0, 10)
    plt.close(res.figure)


def test_plot_kaplan_meier_reference_bands(survival_df: pd.DataFrame) -> None:
    reference_bands = pd.DataFrame(
        {
            "time": [0, 4, 8, 12] * 3,
            "lower": [0.82, 0.72, 0.62, 0.52, 0.58, 0.44, 0.32, 0.20, 0.0, 0.0, 0.0, 0.0],
            "upper": [1.0, 0.92, 0.84, 0.74, 0.82, 0.72, 0.62, 0.52, 0.58, 0.44, 0.32, 0.20],
            "band": ["Favorable"] * 4 + ["Intermediate"] * 4 + ["Poor"] * 4,
        }
    )
    res = plot_kaplan_meier(
        survival_df,
        "time",
        "event",
        group_col="sex",
        reference_bands=reference_bands,
        reference_band_preset="survival",
        reference_band_colors={"Favorable": "#9AD29A", "Intermediate": "#F6E27A", "Poor": "#F28B82"},
        reference_band_alpha=0.3,
        xlim=(0, 12),
    )
    assert len(res.axes.collections) >= 3
    legend_labels = [text.get_text() for text in res.axes.get_legend().get_texts()]
    assert {"Favorable", "Intermediate", "Poor", "F", "M"}.issubset(set(legend_labels))
    plt.close(res.figure)


def test_plot_kaplan_meier_reference_bands_validate(survival_df: pd.DataFrame) -> None:
    reference_bands = pd.DataFrame(
        {
            "time": [0, 6],
            "lower": [0.4, 0.3],
            "upper": [0.8, 0.7],
            "band": ["Reference", "Reference"],
        }
    )
    with pytest.raises(ValueError, match="columns"):
        plot_kaplan_meier(
            survival_df,
            "time",
            "event",
            reference_bands=reference_bands.drop(columns=["lower"]),
        )
    bad_bounds = reference_bands.copy()
    bad_bounds.loc[0, "lower"] = 0.9
    with pytest.raises(ValueError, match="lower <= upper"):
        plot_kaplan_meier(survival_df, "time", "event", reference_bands=bad_bounds)
    with pytest.raises(ValueError, match="reference_band_alpha"):
        plot_kaplan_meier(survival_df, "time", "event", reference_bands=reference_bands, reference_band_alpha=1.5)
    with pytest.raises(ValueError, match="reference_band_preset"):
        plot_kaplan_meier(survival_df, "time", "event", reference_bands=reference_bands, reference_band_preset="unknown")


def test_plot_kaplan_meier_at_risk_only_row(survival_df: pd.DataFrame) -> None:
    res = plot_kaplan_meier(
        survival_df,
        "time",
        "event",
        group_col="sex",
        at_risk_counts=True,
        at_risk_rows=["at_risk"],
    )
    res.figure.canvas.draw()
    table_text = "\n".join(
        label.get_text() for axis in res.figure.axes for label in axis.get_xticklabels()
    )
    assert "At risk" in table_text
    assert "Censored" not in table_text
    assert "Events" not in table_text
    plt.close(res.figure)


def test_plot_kaplan_meier_selected_at_risk_rows(survival_df: pd.DataFrame) -> None:
    res = plot_kaplan_meier(
        survival_df,
        "time",
        "event",
        group_col="sex",
        at_risk_counts=True,
        at_risk_rows=["at_risk", "events"],
    )
    res.figure.canvas.draw()
    table_text = "\n".join(
        label.get_text() for axis in res.figure.axes for label in axis.get_xticklabels()
    )
    assert "At risk" in table_text
    assert "Events" in table_text
    assert "Censored" not in table_text
    plt.close(res.figure)


def test_plot_kaplan_meier_invalid_at_risk_rows(survival_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="at_risk_rows"):
        plot_kaplan_meier(
            survival_df,
            "time",
            "event",
            group_col="sex",
            at_risk_counts=True,
            at_risk_rows="patients",
        )


def test_plot_kaplan_meier_savefig(survival_df: pd.DataFrame) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "km.png"
        res = plot_kaplan_meier(survival_df, "time", "event", group_col="sex", save_path=path)
        assert path.exists()
    plt.close(res.figure)


def test_plot_kaplan_meier_quartile_split(survival_df: pd.DataFrame) -> None:
    res = plot_kaplan_meier(
        survival_df,
        "time",
        "event",
        split_column="risk_score",
        split_method="quartile",
        figsize=(6, 4),
    )
    assert len(res.fitters) == 4
    plt.close(res.figure)


def test_plot_kaplan_meier_rmst_annotation(survival_df: pd.DataFrame) -> None:
    res = plot_kaplan_meier(
        survival_df,
        "time",
        "event",
        group_col="sex",
        annotate_rmst=True,
        rmst_tau=4.0,
        figsize=(5, 3),
    )
    plt.close(res.figure)


def test_rmst_no_grouping(survival_df: pd.DataFrame) -> None:
    out = calculate_rmst(survival_df, "time", "event", tau=6.0)
    assert len(out) == 1
    assert out.iloc[0]["group"] == "__all__"
    assert out.iloc[0]["tau"] == 6.0


def test_rmst_by_group(survival_df: pd.DataFrame) -> None:
    out = calculate_rmst(survival_df, "time", "event", group_col="sex", tau=5.0)
    assert len(out) == survival_df["sex"].nunique()


def test_rmst_after_median_split(survival_df: pd.DataFrame) -> None:
    gdf = create_survival_groups(survival_df, "risk_score", "median", "rsplit")
    out = calculate_rmst(gdf, "time", "event", group_col="rsplit")
    assert len(out) == 2


def test_compare_rmst_pairwise(survival_df: pd.DataFrame) -> None:
    tab = compare_rmst(survival_df, "time", "event", "sex", reference="F", tau=5.0)
    assert not tab.empty
    assert "p_value" in tab.columns


def test_compare_rmst_custom_tau(survival_df: pd.DataFrame) -> None:
    tab = compare_rmst(survival_df, "time", "event", "sex", reference="F", tau=3.0)
    assert (tab["tau"] == 3.0).all()


def test_cox_regression_output_table(survival_df: pd.DataFrame) -> None:
    out = fit_multivariate_cox(
        survival_df,
        "time",
        "event",
        covariates=["age", "risk_score"],
    )
    cols = set(out["results"].columns)
    assert {"covariate", "hazard_ratio", "ci_lower", "ci_upper", "p_value"}.issubset(cols)
    assert out["n_excluded"] >= 0
    assert "concordance_index" in out

    forest = cox_forest_table(out)
    assert {"covariate", "hazard_ratio", "ci_lower", "ci_upper", "label"}.issubset(forest.columns)

    predictions = survival_prediction_table(
        out["fitter"],
        survival_df[["age", "risk_score"]].head(3),
        times=[2.0, 4.0],
    )
    assert predictions.shape[0] == 6
    assert {"survival_probability", "event_risk"}.issubset(predictions.columns)


def test_cox_missing_data_handling() -> None:
    df = pd.DataFrame(
        {
            "time": [1.0, 2.0, 3.0, 4.0],
            "event": [1, 1, 0, 1],
            "x": [1.0, np.nan, 3.0, 4.0],
        }
    )
    out = fit_multivariate_cox(df, "time", "event", covariates=["x"])
    assert out["n_excluded"] == 1
    assert out["n_used"] == 3


def test_univariate_cox(survival_df: pd.DataFrame) -> None:
    out = fit_univariate_cox(survival_df, "time", "event", ["age", "risk_score"])
    assert "model" in out["results"].columns
    assert len(out["fitters"]) == 2


def test_ph_assumption_check(survival_df: pd.DataFrame) -> None:
    cox = fit_multivariate_cox(
        survival_df,
        "time",
        "event",
        covariates=["age", "risk_score"],
    )["fitter"]
    out = check_ph_assumptions(survival_df.dropna(), cox, show_plots=False)
    assert "summary" in out and "violations" in out
    assert "p_adjusted" in out["summary"].columns


def test_schoenfeld_tables_and_plot(survival_df: pd.DataFrame) -> None:
    cox = fit_multivariate_cox(
        survival_df,
        "time",
        "event",
        covariates=["age", "risk_score"],
    )["fitter"]
    clean = survival_df.dropna()
    residuals = schoenfeld_residuals_table(cox, clean)
    assert {"row_index", "time", "covariate", "residual"}.issubset(residuals.columns)
    assert set(residuals["covariate"]).issubset({"age", "risk_score"})

    tests = schoenfeld_test_table(cox, clean, method="rank")
    assert {"covariate", "statistic", "p_value", "p_adjusted"}.issubset(tests.columns)

    fig, ax = plot_schoenfeld_residuals(residuals, covariates=["age"])
    assert ax.get_title() == "Schoenfeld residuals"
    plt.close(fig)

    out = check_ph_assumptions(clean, cox, show_plots=False, include_residuals=True)
    assert out["residuals"] is not None


def test_weibull_aft_fitting(survival_df: pd.DataFrame) -> None:
    out = fit_weibull_aft(survival_df, "time", "event", covariates=["age"])
    assert not out["results"].empty
    assert "AIC" in out


def test_weibull_plot(survival_df: pd.DataFrame) -> None:
    m = fit_weibull_aft(survival_df, "time", "event", covariates=["age"])
    out = plot_aft_survival_curves(
        m["fitter"],
        "age",
        [{"age": 40.0}, {"age": 70.0}],
        figsize=(5, 3),
    )
    plt.close("all")


def test_fit_time_varying_cox_long_format() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 1, 2, 2, 3, 3, 4, 4],
            "start": [0, 2, 0, 3, 0, 2, 0, 4],
            "stop": [2, 5, 3, 7, 2, 6, 4, 8],
            "event": [0, 1, 0, 0, 0, 1, 0, 1],
            "x": [0.2, 0.5, 1.0, 1.2, -0.3, -0.1, 0.8, 1.1],
        }
    )
    out = fit_time_varying_cox(df, "event", id_col="id", covariates=["x"])
    assert {"covariate", "hazard_ratio", "p_value"}.issubset(out["results"].columns)
    assert out["n_used"] == len(df)
    assert out["formula_used"] == "x"


def test_fit_time_varying_cox_validation_errors() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "start": [0, 2, 3],
            "stop": [2, 1, 5],
            "event": [0, 1, 1],
            "x": [0.2, 0.5, 1.0],
        }
    )
    with pytest.raises(ValueError, match="start < stop"):
        fit_time_varying_cox(df, "event", id_col="id", covariates=["x"])
    with pytest.raises(KeyError, match="Missing"):
        fit_time_varying_cox(df.drop(columns=["x"]), "event", id_col="id", covariates=["x"])


def test_fit_cox_time_interactions_generates_long_data(survival_df: pd.DataFrame) -> None:
    out = fit_cox_time_interactions(
        survival_df,
        "time",
        "event",
        covariates=["age", "risk_score"],
        time_interaction_covariates=["risk_score"],
        time_transform="sqrt",
        n_intervals=4,
    )
    assert "risk_score__x_sqrt_time" in out["interaction_columns"]
    assert out["expanded_data"].shape[0] > survival_df.shape[0]
    assert {"covariate", "hazard_ratio", "p_value"}.issubset(out["results"].columns)


def test_survival_sensitivity_analysis_returns_alternatives(survival_df: pd.DataFrame) -> None:
    out = run_survival_sensitivity_analysis(
        survival_df,
        "time",
        "event",
        covariates=["age", "risk_score"],
        group_col="sex",
        rmst_tau=4.0,
        time_interaction_covariates=["risk_score"],
        n_intervals=4,
    )
    assert {"cox", "ph_diagnostics", "weibull_aft", "rmst", "recommendations"}.issubset(out)
    assert out["time_interaction_cox"] is not None
    assert "risk_score__x_log_time" in out["time_interaction_cox"]["interaction_columns"]
    assert not out["weibull_aft"]["results"].empty
    assert len(out["rmst"]) == survival_df["sex"].nunique()


def test_survival_sensitivity_formula_skips_automatic_time_interactions(survival_df: pd.DataFrame) -> None:
    out = run_survival_sensitivity_analysis(
        survival_df,
        "time",
        "event",
        formula="age + risk_score",
        group_col="sex",
        rmst_tau=4.0,
    )
    assert out["time_interaction_cox"] is None
    assert any("Time-interaction Cox was skipped" in item for item in out["recommendations"]) or not out["violating_covariates"]


def test_gradient_survival_boosting(survival_df: pd.DataFrame) -> None:
    pytest.importorskip("sksurv")
    X = survival_df[["age", "risk_score"]]
    out = train_gradient_survival_boosting(
        X,
        survival_df["time"],
        survival_df["event"],
        n_estimators=10,
        max_depth=1,
        random_state=0,
    )
    assert out["model"] is not None
    assert len(out["risk_score"]) == len(survival_df)
    assert 0 <= out["concordance_index"] <= 1
