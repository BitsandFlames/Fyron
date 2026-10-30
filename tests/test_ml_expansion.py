"""Tests for expanded ML validation helpers."""

from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from fyron.datasets import make_classification_cohort
from fyron.ml import (
    apply_probability_calibrator,
    evaluate_external_validation,
    evaluate_locked_threshold,
    fit_probability_calibrator,
    model_card_summary,
    nested_cross_validate_model,
)


def test_ml_expansion_helpers() -> None:
    X, y = make_classification_cohort(n=60)
    estimator = LogisticRegression(max_iter=500)
    nested = nested_cross_validate_model(estimator, {"C": [0.5, 1.0]}, X, y, outer_cv=3, inner_cv=2, n_jobs=1)
    assert len(nested["fold_metrics"]) == 3

    model = RandomForestClassifier(n_estimators=20, random_state=42).fit(X, y)
    external = evaluate_external_validation(model, X, y, threshold=0.5)
    assert external["n"] == len(y)

    prob = model.predict_proba(X)[:, 1]
    locked = evaluate_locked_threshold(y, prob, threshold=0.5)
    assert locked["threshold"] == 0.5

    calibrator = fit_probability_calibrator(model, X, y)
    calibrated = apply_probability_calibrator(calibrator, X)
    assert len(calibrated) == len(y)

    card = model_card_summary(model, X=X, y=y, metrics=external["metrics"], intended_use="test")
    assert card["model_type"] == "RandomForestClassifier"
