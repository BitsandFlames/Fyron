"""Reference checks for survival predictions, metrics, and Cox workflows."""

import numpy as np
import pandas as pd
import pytest
from lifelines import CoxPHFitter, CoxTimeVaryingFitter

from fyron.survival import (
    train_gradient_survival_boosting, survival_prediction_table,
    fit_multivariate_cox, fit_time_varying_cox, fit_cox_time_interactions,
    run_survival_sensitivity_analysis, check_ph_assumptions,
)
from fyron.survival.time_varying import expand_time_interaction_dataframe
from fyron.validation import (
    brier_score_at_time, survival_calibration_at_time, external_survival_validation,
    bootstrap_concordance_index, time_dependent_auc_table,
)


@pytest.mark.parametrize("loss", ["coxph", "squared", "ipcwls"])
def test_boosting_score_direction(loss):
    pytest.importorskip("sksurv")
    X = np.arange(1, 21).reshape(-1, 1)
    t = np.arange(1, 21)
    out = train_gradient_survival_boosting(X, t, np.ones(20), X, t, np.ones(20), loss=loss, n_estimators=30)
    assert out["concordance_index"] == pytest.approx(out["model"].score(X, out["y_eval"]))
    assert out["train_concordance_index"] == pytest.approx(out["model"].score(X, out["y_train"]))
    assert out["concordance_index"] > .95


@pytest.mark.parametrize("event", [[0, 2, 1], [0, np.nan, 1]])
def test_boosting_rejects_invalid_events(event):
    pytest.importorskip("sksurv")
    with pytest.raises(ValueError, match="binary"):
        train_gradient_survival_boosting([[1], [2], [3]], [1, 2, 3], event)


def test_boosting_partial_test_arguments():
    pytest.importorskip("sksurv")
    with pytest.raises(ValueError, match="together"):
        train_gradient_survival_boosting([[1], [2], [3]], [1, 2, 3], [1, 1, 1], duration_test=[1])


def test_score_only_model_is_not_a_survival_distribution():
    class Score:
        def predict(self, X):
            return np.zeros(len(X))
    with pytest.raises(TypeError, match="risk scores"):
        survival_prediction_table(Score(), pd.DataFrame({"x": [1]}), [1, 10])


def test_dataframe_survival_uses_step_values():
    class Steps:
        def predict_survival_function(self, X):
            return pd.DataFrame({0: [.8, .3]}, index=[1., 3.])
    out = survival_prediction_table(Steps(), pd.DataFrame({"x": [1]}), [.5, 2.8, 3.])
    np.testing.assert_allclose(out.survival_probability, [1, .8, .3])


def test_survival_predictions_reject_model_nan():
    class Invalid:
        def predict_survival_function(self, X, times):
            return pd.DataFrame({0: [np.nan] * len(times)}, index=times)
    with pytest.raises(ValueError, match="finite"):
        survival_prediction_table(Invalid(), pd.DataFrame({"x": [1]}), [1])


@pytest.fixture
def censored():
    return pd.DataFrame({"t": [1, 2, 3, 4], "e": [0, 1, 1, 0], "p": [.9, .8, .2, .1]})


def test_ipcw_and_km_reference(censored):
    pytest.importorskip("sksurv")
    summary, table = survival_calibration_at_time(censored, "t", "e", "p", 2.5, n_bins=1)
    assert summary["brier_score"] == pytest.approx(.03)
    assert summary["observed_event_rate"] == pytest.approx(1 / 3)
    assert table.observed.iloc[0] == pytest.approx(1 / 3)
    reference = censored.assign(e=1)
    score = brier_score_at_time(censored, "t", "e", "p", 2.5, censoring_df=reference)
    assert score["brier_score"] == pytest.approx((.04 + .04 + .01) / 4)
    uncensored = censored.assign(e=1)
    expected = np.mean(((uncensored.t <= 2.5).astype(float) - uncensored.p)**2)
    assert brier_score_at_time(uncensored, "t", "e", "p", 2.5)["brier_score"] == pytest.approx(expected)


def test_invalid_survival_validation(censored):
    pytest.importorskip("sksurv")
    for col, value in [("e", 2), ("e", np.nan), ("t", np.inf), ("p", 1.2)]:
        bad = censored.astype(float).copy()
        bad.loc[0, col] = value
        with pytest.raises(ValueError):
            brier_score_at_time(bad, "t", "e", "p", 2.5)
    for time in [np.nan, np.inf, -1, 5]:
        with pytest.raises(ValueError):
            brier_score_at_time(censored, "t", "e", "p", time)
    with pytest.raises(ValueError, match="Calibration horizon"):
        survival_calibration_at_time(censored, "t", "e", "p", 2.5, n_bins=4)
    with pytest.raises(ValueError):
        brier_score_at_time(censored, "t", "e", "p", 2.5, censoring_df=pd.DataFrame({"t": [1, 2], "e": [0, 0]}))
    nullable = censored.astype({"t": "Float64", "e": "Int64", "p": "Float64"})
    assert brier_score_at_time(nullable, "t", "e", "p", 2.5)["brier_score"] == pytest.approx(.03)
    nullable.loc[0, "p"] = pd.NA
    with pytest.raises(ValueError, match="finite"):
        brier_score_at_time(nullable, "t", "e", "p", 2.5)


def test_concordance_ties_and_bootstrap():
    pytest.importorskip("sksurv")
    df = pd.DataFrame({"t": [1, 1, 2], "e": [1, 0, 1], "r": [2, 3, 1]})
    out = bootstrap_concordance_index(df, "t", "e", "r", n_rounds=50)
    assert out["estimate"] == .5
    assert out["valid_rounds"] + out["dropped_rounds"] == 50
    assert out["dropped_rounds"] > 0
    assert np.isnan(external_survival_validation({}, df.assign(e=0), duration_col="t", event_col="e", risk_col="r")["concordance_index"])
    with pytest.raises(ValueError, match="No bootstrap"):
        bootstrap_concordance_index(df.assign(e=0), "t", "e", "r", n_rounds=5)


def test_auc_time_alignment():
    pytest.importorskip("sksurv")
    df = pd.DataFrame({"t": [1, 2, 3, 4, 5, 6], "e": 1, "r": [6, 5, 3, 4, 2, 1]})
    out = time_dependent_auc_table(df, df.iloc[:5], duration_col="t", event_col="e", risk_col="r", times=[3.5, 1.5, 3.5])
    np.testing.assert_allclose(out.auc, [5 / 6, 1, 5 / 6])
    assert list(out.time) == [3.5, 1.5, 3.5]


@pytest.fixture
def cox_data():
    rng = np.random.default_rng(18)
    return pd.DataFrame({"t": rng.uniform(.5, 8, 100), "e": rng.binomial(1, .7, 100), "x": rng.normal(size=100), "s": ["a", "b"] * 50}, index=np.arange(100) + 1000)


def test_cox_strata_formula_and_cohort(cox_data):
    df = cox_data.assign(unused=np.nan)
    for args in [{"covariates": ["x"]}, {"formula": "x + I(x ** 2)"}]:
        out = fit_multivariate_cox(df, "t", "e", strata="s", **args)
        ref = CoxPHFitter().fit(df.drop(columns="unused"), "t", "e", strata="s", formula=out["formula_used"])
        np.testing.assert_allclose(out["fitter"].params_, ref.params_)
        assert out["training_df"].index.equals(df.index)
    out = run_survival_sensitivity_analysis(df, "t", "e", covariates=["x"], fit_time_interactions=False, fit_aft=False, fit_rmst=False)
    assert out["cox"]["n_used"] == len(df)
    missing = df.copy()
    missing.loc[1003, "x"] = np.nan
    out = fit_multivariate_cox(missing, "t", "e", formula="x + C(s)")
    assert out["n_used"] == len(df) - 1
    assert out["training_df"].index.equals(df.index.drop(1003))


def test_time_varying_formula_and_common_grid(cox_data):
    long = cox_data.assign(start=0, stop=cox_data.t, unused=np.nan)
    out = fit_time_varying_cox(long, "e", formula="x + C(s)")
    ref = CoxTimeVaryingFitter().fit(long, event_col="e", start_col="start", stop_col="stop", formula="x + C(s)")
    np.testing.assert_allclose(out["fitter"].params_, ref.params_)
    baseline = pd.DataFrame({"t": [1, 3, 4], "e": [1, 1, 0], "x": 1.})
    expanded = expand_time_interaction_dataframe(baseline, "t", "e", covariates=["x"], time_interaction_covariates=["x"], n_intervals=1)["data"]
    np.testing.assert_allclose(expanded.x__x_log_time, np.log(4))


def test_time_interaction_matches_independent_expansion(cox_data):
    out = fit_cox_time_interactions(cox_data, "t", "e", covariates=["x"], strata="s", breakpoints=[2, 5], time_transform="identity")
    rows = []
    for subject, (_, row) in enumerate(cox_data.iterrows()):
        start = 0
        for end in [2, 5, cox_data.t.max()]:
            stop = min(row.t, end)
            rows.append({"id": subject, "start": start, "stop": stop, "e": row.e if stop == row.t else 0, "x": row.x, "xt": row.x * end, "s": row.s})
            if stop == row.t:
                break
            start = stop
    ref = CoxTimeVaryingFitter().fit(pd.DataFrame(rows), id_col="id", start_col="start", stop_col="stop", event_col="e", strata="s", formula="x + xt")
    np.testing.assert_allclose(out["fitter"].params_, ref.params_, rtol=1e-8)


def test_ph_flags_follow_adjustment(monkeypatch, cox_data):
    import fyron.survival.ph_diagnostics as ph
    out = fit_multivariate_cox(cox_data, "t", "e", covariates=["x"])
    monkeypatch.setattr(ph, "schoenfeld_test_table", lambda *a, **kw: pd.DataFrame({"covariate": ["x"], "p_value": [.03], "p_adjusted": [.06]}))
    assert check_ph_assumptions(out["training_df"], out["fitter"], p_adjust="holm")["violations"] == []
    assert check_ph_assumptions(out["training_df"], out["fitter"], p_adjust=None)["violations"] == ["x"]


def test_survival_dependency_is_lazy(monkeypatch, censored):
    import builtins
    original = builtins.__import__

    def without_sksurv(name, *args, **kwargs):
        if name.startswith("sksurv"):
            raise ImportError("unavailable")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_sksurv)
    with pytest.raises(ImportError, match="survival-ml"):
        brier_score_at_time(censored, "t", "e", "p", 2.5)
    from fyron.validation import calibration_summary
    summary, _ = calibration_summary([0, 1], [.2, .8])
    assert summary["brier_score"] == pytest.approx(.04)


def test_external_censoring_reference_and_finite_scores(censored):
    pytest.importorskip("sksurv")
    df = censored.assign(p=.5, r=[4., 3., 2., 1.])
    out = external_survival_validation({}, df, duration_col="t", event_col="e", risk_col="r", prediction_col="p", time_horizon=2.5, censoring_df=df.assign(e=1))
    assert out["calibration"]["brier_score"] == pytest.approx(.1875)
    with pytest.raises(ValueError, match="finite"):
        external_survival_validation({}, df.assign(r=np.inf), duration_col="t", event_col="e", risk_col="r")
