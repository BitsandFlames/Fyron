from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from fyron import explainability as fe


class _FakeShapExplainer:
    def __call__(self, X):
        rows = len(X)
        return np.tile(np.array([[0.2, -0.1]]), (rows, 1))


def test_explainability_tables() -> None:
    X = pd.DataFrame(
        {
            "age": [40.0, 50.0, 60.0, 70.0, 80.0, 90.0],
            "score": [0.0, 1.0, 1.0, 2.0, 2.0, 3.0],
        }
    )
    y = [0, 0, 0, 1, 1, 1]
    model = RandomForestClassifier(n_estimators=20, random_state=0).fit(X, y)

    importance = fe.permutation_importance_table(
        model,
        X,
        y,
        n_repeats=2,
        random_state=0,
    )
    assert set(importance["feature"]) == {"age", "score"}

    pdp = fe.partial_dependence_table(model, X, features=["age"], grid_resolution=3)
    assert set(pdp["feature"]) == {"age"}
    assert "partial_dependence" in pdp.columns

    shap_long = fe.shap_values_table(model, X, explainer=_FakeShapExplainer(), max_rows=3)
    assert set(shap_long["feature"]) == {"age", "score"}
    assert shap_long.shape[0] == 6
    assert "abs_shap_value" in shap_long.columns

    shap_summary = fe.shap_summary_table(model, X, explainer=_FakeShapExplainer(), max_rows=3)
    assert list(shap_summary["feature"]) == ["age", "score"]
    assert "mean_abs_shap" in shap_summary.columns


def test_explain_model_summary_merges_importance_shap_qc_metrics_and_notes():
    importance = pd.DataFrame(
        {
            "feature": ["age", "stage"],
            "importance_mean": [0.12, 0.30],
        }
    )
    shap_summary = pd.DataFrame(
        {
            "feature": ["age", "stage"],
            "mean_abs_shap": [0.40, 0.10],
            "mean_shap": [0.05, -0.03],
        }
    )
    qc = pd.DataFrame(
        {
            "feature": ["age", "stage"],
            "missing_percent": [0.0, 5.0],
            "leakage_flag": [False, False],
        }
    )

    summary = fe.explain_model_summary(
        importance=importance,
        shap_summary=shap_summary,
        feature_qc=qc,
        metrics={"auc": 0.82},
        notes={"stage": "Clinically expected direction"},
    )

    assert summary.loc[0, "feature"] == "age"
    assert "importance.importance_mean" in summary.columns
    assert "shap.mean_abs_shap" in summary.columns
    assert "qc.missing_percent" in summary.columns
    assert "metric.auc" in summary.columns
    assert summary.loc[summary["feature"] == "stage", "note"].iloc[0] == "Clinically expected direction"


def test_explain_model_summary_requires_feature_level_input():
    try:
        fe.explain_model_summary(metrics={"auc": 0.8})
    except ValueError as exc:
        assert "At least one" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_explain_patient_prediction_returns_top_signed_drivers():
    contributions = pd.DataFrame(
        {
            "row_index": [0, 0, 0, 0, 1],
            "feature": ["age", "stage", "sma", "vat", "age"],
            "feature_value": [70, "III", 120.0, 200.0, 50],
            "shap_value": [0.2, -0.5, 0.1, -0.05, 1.0],
        }
    )

    drivers = fe.explain_patient_prediction(contributions, row_index=0, top_n=1)

    assert drivers["feature"].tolist() == ["age", "stage"]
    assert drivers["direction"].tolist() == ["positive", "negative"]
    assert drivers["abs_contribution"].tolist() == [0.2, 0.5]
