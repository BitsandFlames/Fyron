"""Tests for fyron.ml."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

pytest.importorskip("sklearn")

from fyron import ml


@pytest.fixture
def binary_data() -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(42)
    n = 80
    X = pd.DataFrame(
        {
            "age": rng.normal(55, 10, n),
            "score": rng.normal(0, 1, n),
            "noise": rng.normal(0, 1, n),
        }
    )
    logits = -1.0 + 0.05 * X["age"] + 1.5 * X["score"]
    prob = 1 / (1 + np.exp(-logits))
    y = pd.Series((rng.random(n) < prob).astype(int), name="label")
    return X, y


def test_train_test_split_data(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, y = binary_data
    X_train, X_test, y_train, y_test = ml.train_test_split_data(
        X, y, test_size=0.25, stratify=True, random_state=0
    )
    assert len(X_train) + len(X_test) == len(X)
    assert len(y_train) == len(X_train)


def test_compute_class_weights_imbalance() -> None:
    weights = ml.compute_class_weights([0, 0, 0, 1])
    assert weights[1] > weights[0]


def test_compute_scale_pos_weight() -> None:
    assert ml.compute_scale_pos_weight([0, 0, 0, 1]) == 3.0


def test_calculate_classification_metrics_with_and_without_prob() -> None:
    m = ml.calculate_classification_metrics([0, 1, 1, 0], [0, 1, 0, 0], [0.1, 0.9, 0.4, 0.2])
    assert m["tp"] == 1
    assert m["auc"] is not None
    m2 = ml.calculate_classification_metrics([0, 1, 1, 0], [0, 1, 0, 0])
    assert m2["auc"] is None
    assert m2["sensitivity"] is not None


def test_train_random_forest(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, y = binary_data
    X_train, X_test, y_train, y_test = ml.train_test_split_data(X, y, random_state=0)
    out = ml.train_random_forest(
        X_train,
        y_train,
        X_test,
        y_test,
        class_weight=ml.compute_class_weights(y_train),
        n_estimators=50,
        random_state=0,
    )
    assert out["model"] is not None
    assert len(out["y_pred"]) == len(y_test)
    assert "accuracy" in out["metrics"]


def test_train_xgboost(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    xgb = pytest.importorskip("xgboost")
    assert xgb is not None
    X, y = binary_data
    X_train, X_test, y_train, y_test = ml.train_test_split_data(X, y, random_state=0)
    out = ml.train_xgboost(
        X_train,
        y_train,
        X_test,
        y_test,
        scale_pos_weight=ml.compute_scale_pos_weight(y_train),
        n_estimators=50,
        random_state=0,
    )
    assert out["y_prob"] is not None


def test_cross_validate_model(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, y = binary_data
    out = ml.cross_validate_model(
        RandomForestClassifier(n_estimators=20, random_state=0),
        X,
        y,
        cv=3,
        return_oof_predictions=True,
    )
    assert len(out["fold_metrics"]) == 3
    assert "f1" in out["mean_metrics"]


def test_plot_roc_and_confusion_matrix(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, y = binary_data
    result = ml.train_random_forest(X, y, n_estimators=20, random_state=0)
    fig1, _ = ml.plot_roc_curve(y, result["y_prob"])
    fig2, _ = ml.plot_confusion_matrix(y, result["y_pred"])
    fig3, _ = ml.plot_precision_recall_curve(y, result["y_prob"])
    fig4, _ = ml.plot_calibration_curve(y, result["y_prob"], n_bins=4)
    plt.close(fig1)
    plt.close(fig2)
    plt.close(fig3)
    plt.close(fig4)


def test_clinical_summary_plots(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, _ = binary_data
    fig1, _, corr = ml.plot_correlation_heatmap(X, columns=["age", "score", "noise"])
    assert corr.shape == (3, 3)

    metric_df = pd.DataFrame(
        {
            "model": ["RF", "XGB", "RF", "XGB"],
            "metric": ["auc", "auc", "f1", "f1"],
            "value": [0.82, 0.86, 0.74, 0.76],
        }
    )
    fig2, _ = ml.plot_patterned_bar(
        metric_df,
        x="metric",
        y="value",
        group="model",
        title="Metrics",
    )
    fig3, _ = ml.plot_metric_bars({"RF": {"auc": 0.82, "f1": 0.74}})
    risk_df = pd.DataFrame(
        {
            "risk_score": [0.12, 0.24, 0.35, 0.61, 0.72, 0.89],
            "event": [0, 0, 0, 1, 1, 1],
        }
    )
    fig4, _ = ml.plot_risk_score_distribution(risk_df, event_col="event")
    coef_df = pd.DataFrame(
        {
            "feature": ["age", "sarcopenia", "vat", "albumin"],
            "coef": [0.42, 0.78, -0.31, -0.52],
        }
    )
    fig5, _ = ml.plot_signed_feature_weights(coef_df, top_n=3)
    p_df = pd.DataFrame(
        {
            "label": ["L3 SMA", "VAT", "Albumin"],
            "p_value": [0.003, 0.048, 0.21],
        }
    )
    fig6, _, table = ml.plot_significance_bars(p_df)
    assert "minus_log10_p" in table.columns
    forest_df = pd.DataFrame(
        {
            "label": ["Low", "Intermediate", "High"],
            "estimate": [0.82, 1.0, 1.74],
            "ci_lower": [0.52, 0.73, 1.15],
            "ci_upper": [1.29, 1.37, 2.61],
            "p_value": [0.37, 0.99, 0.008],
        }
    )
    fig7, _ = ml.plot_forest_estimates(forest_df, p_col="p_value")
    ratio_df = pd.DataFrame(
        {
            "feature": ["Sarcopenia", "Albumin", "Stage IV"],
            "hazard_ratio": [1.74, 0.68, 2.16],
            "ci_lower": [1.15, 0.49, 1.44],
            "ci_upper": [2.61, 0.94, 3.24],
            "p_value": [0.008, 0.018, 0.0004],
            "category": ["Body composition", "Laboratory", "Clinical"],
            "n": [96, 188, 97],
        }
    )
    fig11, _ = ml.plot_directional_ratio_rows(
        ratio_df,
        ratio_col="hazard_ratio",
        p_col="p_value",
        group_col="category",
        n_col="n",
        ratio_label="Hazard ratio",
    )
    clinical_df = pd.DataFrame(
        {
            "risk_group": ["Low", "Low", "Low", "High", "High", "High"],
            "sex": ["F", "M", "F", "F", "M", "M"],
            "l3_sma": [42.0, 39.5, 44.2, 35.1, 33.8, 37.4],
            "risk_score": [0.12, 0.24, 0.35, 0.61, 0.72, 0.89],
        }
    )
    fig8, _ = ml.plot_grouped_boxplot(
        clinical_df,
        x="risk_group",
        y="l3_sma",
        hue="sex",
    )
    fig9, _ = ml.plot_density(
        clinical_df,
        x="risk_score",
        hue="risk_group",
    )
    stat_bar_df = pd.DataFrame(
        {
            "risk_group": ["Low"] * 6 + ["High"] * 6,
            "sex": ["F", "F", "F", "M", "M", "M"] * 2,
            "sma": [44.0, 45.0, 43.0, 40.0, 39.5, 40.5, 34.0, 35.0, 33.0, 31.0, 32.0, 30.5],
        }
    )
    fig10, _, stat_table = ml.plot_grouped_bar_with_significance(
        stat_bar_df,
        x="risk_group",
        y="sma",
        hue="sex",
    )
    assert {"summary", "comparison"}.issubset(set(stat_table["row_type"]))
    assert "p_value" in stat_table.columns
    survival_df = pd.DataFrame(
        {
            "time": [5, 8, 10, 12, 15, 18],
            "event": [1, 0, 1, 1, 0, 1],
            "risk_group": ["Low", "Low", "Low", "High", "High", "High"],
        }
    )
    km = ml.plot_kaplan_meier(
        survival_df,
        duration_col="time",
        event_col="event",
        group_col="risk_group",
        title="KM by risk group",
    )
    assert set(km.fitters) == {"High", "Low"}
    plt.close(fig1)
    plt.close(fig2)
    plt.close(fig3)
    plt.close(fig4)
    plt.close(fig5)
    plt.close(fig6)
    plt.close(fig7)
    plt.close(fig8)
    plt.close(fig9)
    plt.close(fig10)
    plt.close(fig11)
    plt.close(km.figure)


def test_grid_search_model(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, y = binary_data
    gs = ml.grid_search_model(
        RandomForestClassifier(random_state=0),
        {"n_estimators": [10, 20]},
        X,
        y,
        cv=2,
        n_jobs=1,
    )
    assert gs["best_estimator"] is not None
    assert len(gs["cv_results_df"]) > 0


def test_get_feature_importance(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, y = binary_data
    model = RandomForestClassifier(n_estimators=20, random_state=0).fit(X, y)
    imp = ml.get_feature_importance(model, list(X.columns))
    assert list(imp.columns) == ["feature", "importance"]


def test_run_classification_pipeline(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    X, y = binary_data
    out = ml.run_classification_pipeline(
        X, y, model="random_forest", n_estimators=30, random_state=0
    )
    assert "metrics" in out


def test_save_load_estimator(binary_data: tuple[pd.DataFrame, pd.Series], tmp_path) -> None:
    X, y = binary_data
    model = RandomForestClassifier(n_estimators=5, random_state=0).fit(X, y)
    path = tmp_path / "model.joblib"
    ml.save_estimator(model, path)
    loaded = ml.load_estimator(path)
    assert list(loaded.predict(X.head(1))) == list(model.predict(X.head(1)))


def test_run_boruta_feature_selection(binary_data: tuple[pd.DataFrame, pd.Series]) -> None:
    pytest.importorskip("boruta")
    X, y = binary_data
    out = ml.run_boruta_feature_selection(X, y, max_iter=15, random_state=0)
    assert "selected_features" in out
    assert len(out["ranking_df"]) == X.shape[1]
