from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from fyron import feature_selection as fs
from fyron import ml


def _data() -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(0)
    signal = np.r_[rng.normal(0, 0.2, 20), rng.normal(2, 0.2, 20)]
    X = pd.DataFrame(
        {
            "signal": signal,
            "signal_copy": signal + rng.normal(0, 0.01, 40),
            "noise": rng.normal(0, 1, 40),
            "constant": 1.0,
        }
    )
    y = np.array([0] * 20 + [1] * 20)
    return X, y


def test_univariate_variance_and_correlation_filters() -> None:
    X, y = _data()
    uni = fs.univariate_feature_screening(X, y)
    assert "signal" in uni["selected_features"]
    assert {"q_value", "selected"}.issubset(uni["summary_table"].columns)

    var = fs.variance_filter(X)
    assert "constant" not in var["selected_features"]

    corr = fs.correlation_filter(X[["signal", "signal_copy", "noise"]], threshold=0.9)
    assert "signal_copy" in corr["dropped_features"]


def test_model_permutation_stability_and_consensus() -> None:
    X, y = _data()
    estimator = RandomForestClassifier(n_estimators=30, random_state=0)

    model = fs.model_importance_selection(estimator, X, y, top_n=2)
    assert len(model["selected_features"]) == 2

    perm = fs.permutation_importance_selection(estimator, X, y, n_repeats=2, top_n=2, random_state=0)
    assert "importance_mean" in perm["summary_table"].columns

    stable = fs.stability_selection(estimator, X, y, n_rounds=5, sample_fraction=0.75, random_state=0)
    assert stable["summary_table"]["selection_frequency"].between(0, 1).all()

    combined = fs.combine_feature_selection_results({"model": model, "stable": stable}, strategy="union")
    assert set(model["selected_features"]).issubset(set(combined["selected_features"]))


def test_boruta_wrapper_skips_without_optional_dependency() -> None:
    X, y = _data()
    try:
        out = fs.boruta_feature_selection(X, y, max_iter=5, random_state=0)
    except ImportError:
        pytest.skip("Boruta optional dependency not installed")
    assert "summary_table" in out


def test_feature_selection_plots() -> None:
    X, y = _data()
    stable = fs.stability_selection(
        RandomForestClassifier(n_estimators=10, random_state=0),
        X,
        y,
        n_rounds=3,
        random_state=0,
    )
    fig1, _ = ml.plot_feature_selection_summary(stable["summary_table"])
    fig2, _ = ml.plot_stability_selection(stable["summary_table"])
    import matplotlib.pyplot as plt

    plt.close(fig1)
    plt.close(fig2)
