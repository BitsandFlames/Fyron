"""Regression coverage for the cross-module correctness review."""

import numpy as np
import pandas as pd
import pytest

from fyron.cohort.tables import (
    build_time_to_event_endpoint, join_cohort_tables, validate_cohort_table,
)
from fyron.preprocessing.encoding import fit_categorical_encoder, apply_categorical_encoder
from fyron.preprocessing.imputation import fit_imputer, apply_imputer
from fyron.phenotyping.rules import define_lab_threshold_phenotype


def test_missing_patient_ids_cannot_join():
    frame = pd.DataFrame({"patient_id": ["a", None]})
    for left, right in [(frame, frame), (frame, frame.iloc[:1]), (frame.iloc[:1], frame)]:
        with pytest.raises(ValueError, match="missing identifiers"):
            join_cohort_tables(left, right)
    with pytest.raises(ValueError, match="Missing identifiers"):
        validate_cohort_table(frame, required_columns=[], allow_duplicate_ids=True)
    assert validate_cohort_table(frame, required_columns=[], id_column=None) is frame


@pytest.mark.parametrize("column", ["event_date", "censor_date"])
def test_malformed_endpoint_dates_raise(column):
    frame = pd.DataFrame({"index": ["2020-01-01"], "event_date": [None],
                          "censor_date": ["2020-02-01"]})
    kwargs = dict(index_date_col="index", event_date_col="event_date", censor_date_col="censor_date")
    assert build_time_to_event_endpoint(frame, **kwargs)["event"].tolist() == [0]
    frame[column] = "not-a-date"
    with pytest.raises(ValueError, match="invalid dates"):
        build_time_to_event_endpoint(frame, require_endpoint=False, **kwargs)


def test_encoder_rejects_colliding_categories_and_columns():
    with pytest.raises(ValueError, match="collision"):
        fit_categorical_encoder(pd.DataFrame({"group": ["A/B", "A B"]}))
    frame = pd.DataFrame({"group": ["A"], "group__A": [7]})
    with pytest.raises(ValueError, match="collision"):
        fit_categorical_encoder(frame, columns=["group"])
    encoder = fit_categorical_encoder(frame[["group"]])
    with pytest.raises(ValueError, match="collision"):
        apply_categorical_encoder(frame, encoder)
    assert frame["group__A"].tolist() == [7]
    encoded = apply_categorical_encoder(frame[["group"]], encoder)
    assert encoded["group__A"].tolist() == [1]


def test_numeric_coercion_is_marked_as_imputed():
    train = pd.DataFrame({"x": [1, 3]})
    spec = fit_imputer(train, numeric=["x"], add_missing_indicators=True)
    result = apply_imputer(pd.DataFrame({"x": ["bad", None, "4"]}), spec)
    assert result["x"].tolist() == [2, 2, 4]
    assert result["x_was_missing"].tolist() == [1, 1, 0]


@pytest.mark.parametrize("direction", [">=", ">", "<=", "<", "==", "!="])
def test_invalid_lab_values_are_never_evidence(direction):
    frame = pd.DataFrame({"patient_id": range(6), "lab": [None, "bad", np.inf, -np.inf, 1, 2]})
    result = define_lab_threshold_phenotype(frame, "lab", 1, direction=direction)
    assert set(result["patient_id"]) <= {4, 5}
    if direction == "!=":
        assert result["patient_id"].tolist() == [5]


@pytest.mark.parametrize("index", [range(6), range(10, 16), ["a"] * 6])
def test_regression_screening_pairs_positionally(index):
    pytest.importorskip("scipy")
    pytest.importorskip("sklearn")
    from fyron.feature_selection.selection import univariate_feature_screening

    frame = pd.DataFrame({"x": [1, 2, 3, 4, "bad", np.inf]}, index=index)
    result = univariate_feature_screening(frame, [1, 2, 3, 4, 5, 6], task="regression")
    row = result["summary_table"].iloc[0]
    assert row["statistic"] == pytest.approx(1)
    assert row["n"] == 4


@pytest.mark.parametrize("bad_prob", [[[.2], [.8]], [np.nan, .8], [-.1, .8], [.2, 1.1]])
def test_decision_curve_rejects_invalid_probabilities(bad_prob):
    pytest.importorskip("sklearn")
    from fyron.validation.classification import decision_curve_table

    with pytest.raises(ValueError):
        decision_curve_table([0, 1], bad_prob, thresholds=[.5])


def test_decision_curve_counts_and_validation():
    pytest.importorskip("sklearn")
    from fyron.validation.classification import decision_curve_table

    result = decision_curve_table([0, 1], [.2, .8], thresholds=[.5]).iloc[0]
    assert (result["tp"], result["fp"], result["net_benefit_model"]) == (1, 0, .5)
    for thresholds in [[np.nan], [[.5]], [0], [1], []]:
        with pytest.raises(ValueError):
            decision_curve_table([0, 1], [.2, .8], thresholds=thresholds)
    for labels in [[[0], [1]], [], [0, None], [2, 3]]:
        with pytest.raises(ValueError):
            decision_curve_table(labels, [.2, .8])


@pytest.mark.parametrize("pos,neg", [(0, 1), ("case", "control")])
def test_positive_class_metrics_and_model_probabilities(pos, neg):
    pytest.importorskip("sklearn")
    import matplotlib.pyplot as plt
    from sklearn.ensemble import RandomForestClassifier
    from fyron.ml.metrics import calculate_classification_metrics
    from fyron.ml.training import train_random_forest
    from fyron.ml.cv import cross_validate_model
    from fyron.ml.evaluation import evaluate_external_validation, nested_cross_validate_model
    from fyron.ml.search import grid_search_model

    metrics = calculate_classification_metrics(
        [pos, pos, neg, neg], [pos, neg, neg, neg], [.9, .8, .2, .1], pos_label=pos,
    )
    assert metrics["f1"] == pytest.approx(2 / 3)
    assert metrics["auc"] == 1
    assert metrics["recall"] == metrics["sensitivity"] == .5
    X = np.arange(40).reshape(-1, 1)
    y = np.array([pos] * 20 + [neg] * 20)
    result = train_random_forest(X, y, pos_label=pos, n_estimators=10, plot=True)
    model = result["model"]
    expected = model.predict_proba(X)[:, list(model.classes_).index(pos)]
    np.testing.assert_allclose(result["y_prob"], expected)
    assert result["metrics"]["auc"] == 1
    assert set(result["figures"]) == {"roc", "precision_recall", "calibration", "confusion_matrix"}
    plt.close("all")
    external = evaluate_external_validation(model, X, y, threshold=.5, pos_label=pos)
    assert external["locked_threshold_metrics"]["accuracy"] == 1
    cv = cross_validate_model(RandomForestClassifier(n_estimators=5, random_state=0),
                              X, y, cv=2, pos_label=pos, return_oof_predictions=True)
    assert cv["oof_prob"][:10].mean() > .8
    assert cv["mean_metrics"]["auc"] == pytest.approx(.95)
    nested = nested_cross_validate_model(RandomForestClassifier(n_estimators=5, random_state=0),
                                        {"max_depth": [2]}, X, y, outer_cv=2, inner_cv=2,
                                        n_jobs=1, pos_label=pos)
    assert nested["mean_metrics"]["auc"] == pytest.approx(.95)
    search = grid_search_model(RandomForestClassifier(n_estimators=5, random_state=0), {"max_depth": [2]},
                               X, y, X, y, cv=2, n_jobs=1, pos_label=pos)
    assert search["val_metrics"]["auc"] == 1


class _FirstColumnSelector:
    def transform(self, X):
        return np.asarray(X)[:, :1]


@pytest.mark.parametrize("search", [False, True])
def test_boruta_only_sees_training_rows_including_cv(monkeypatch, search):
    pytest.importorskip("sklearn")
    import fyron.ml.pipeline as pipeline
    import fyron.ml.boruta_selection as boruta
    from fyron.ml.search import grid_search_model

    seen = []

    def select(X, y, **kwargs):
        seen.append(set(np.asarray(X)[:, 0]))
        return {"selected_features": ["row"], "selector": _FirstColumnSelector()}

    monkeypatch.setattr(boruta, "run_boruta_feature_selection", select)
    monkeypatch.setattr(pipeline, "grid_search_model",
                        lambda *args, **kwargs: grid_search_model(*args, **kwargs, n_jobs=1, cv=2))
    X = pd.DataFrame({"row": range(100), "noise": np.zeros(100)})
    result = pipeline.run_classification_pipeline(
        X, [0] * 50 + [1] * 50, use_boruta=True, use_grid_search=search,
        param_grid={"max_depth": [2, 3]}, n_estimators=5,
    )
    train_rows = set(result["X_train"]["row"])
    test_rows = set(result["X_test"]["row"])
    assert seen and all(rows <= train_rows and not rows & test_rows for rows in seen)
    assert seen[-1] == train_rows
    if search:
        assert len(seen) == 5  # Two candidates, two training folds, then full-training refit.
        assert all(len(rows) == 40 for rows in seen[:-1])
    model = result["model"]
    np.testing.assert_array_equal(result["y_pred"], model.predict(result["X_test"].to_numpy()))
    np.testing.assert_allclose(result["y_prob"], model.predict_proba(result["X_test"].to_numpy())[:, 1])


@pytest.mark.parametrize("model_name", ["random_forest", "xgboost"])
def test_grid_search_artifacts_and_parameters_match(monkeypatch, model_name):
    pytest.importorskip("sklearn")
    if model_name == "xgboost":
        pytest.importorskip("xgboost")
    import matplotlib.pyplot as plt
    import fyron.ml.pipeline as pipeline
    from fyron.ml.search import grid_search_model
    from fyron.ml.metrics import calculate_classification_metrics

    monkeypatch.setattr(pipeline, "grid_search_model",
                        lambda *args, **kwargs: grid_search_model(*args, **kwargs, n_jobs=1, cv=2))
    rng = np.random.default_rng(2)
    X = rng.normal(size=(80, 4))
    y = np.array([0] * 60 + [1] * 20)
    result = pipeline.run_classification_pipeline(
        X, y, model=model_name, use_grid_search=True, pos_label=0, plot=True,
        n_estimators=5, param_grid={"max_depth": [1, 2]}, n_jobs=1,
    )
    model = result["model"]
    assert model is result["grid_search"]["best_estimator"]
    assert model.get_params()["n_estimators"] == 5
    weight = "class_weight" if model_name == "random_forest" else "scale_pos_weight"
    assert model.get_params()[weight] == result[weight]
    pred = model.predict(result["X_test"])
    prob = model.predict_proba(result["X_test"])[:, 0]
    np.testing.assert_array_equal(result["y_pred"], pred)
    np.testing.assert_allclose(result["y_prob"], prob)
    assert result["metrics"] == calculate_classification_metrics(result["y_test"], pred, prob, pos_label=0)
    assert result["grid_search"]["val_metrics"] == result["metrics"]
    assert len(result["figures"]) == 4
    plt.close("all")
