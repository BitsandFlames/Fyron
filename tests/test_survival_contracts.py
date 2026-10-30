"""API-preserving preparation and numerical parity contracts."""

import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from fyron._survival_data import outcome_arrays, concordance, positive_horizon
from fyron.survival import fit_multivariate_cox, fit_weibull_aft, calculate_rmst


def baseline():
    random = np.random.default_rng(732)
    x = random.normal(size=80)
    times = random.exponential(np.exp(-.4*x))*10+1
    events = random.binomial(1, .7, 80)
    return pd.DataFrame({"time": times, "event": events, "x": x})


def test_pre_refactor_numerical_baselines():
    frame = baseline()
    cox = fit_multivariate_cox(frame, "time", "event", covariates=["x"])
    np.testing.assert_allclose(
        cox["results"][["hazard_ratio", "ci_lower", "ci_upper", "p_value"]].to_numpy(),
        [[1.52444847170737, 1.14539084348674, 2.02895208749574, .00384504557933]], rtol=1e-6,
    )
    aft = fit_weibull_aft(frame, "time", "event", covariates=["x"])
    np.testing.assert_allclose(
        aft["results"][["coef", "ci_lower", "ci_upper"]].to_numpy(),
        [[2.67976174505796, 2.47480160390102, 2.8847218862149],
         [-.44118094553087, -.64652736621064, -.23583452485111],
         [.22540333138991, .03031004114909, .42049662163074]], rtol=1e-6,
    )


@pytest.mark.parametrize("fit", [fit_multivariate_cox, fit_weibull_aft])
def test_formula_cohort_index_and_missingness(fit):
    frame = baseline()
    frame.index += 1000
    frame["x"] = np.exp(frame.x)
    frame["group"] = np.where(np.arange(len(frame)) % 2, "a", "b")
    frame["unrelated"] = np.nan
    frame.loc[1001, "x"] = np.nan
    frame.loc[1003, "group"] = None
    original = frame.copy(deep=True)
    result = fit(frame, "time", "event", formula="np.log(x) + C(group)")
    expected = frame.drop(index=[1001, 1003])
    assert result["training_df"].index.equals(expected.index)
    assert "unrelated" not in result["training_df"]
    assert result["n_used"] == 78 and result["n_excluded"] == 2
    pd.testing.assert_frame_equal(frame, original)
    reference = fit(expected.drop(columns="unrelated"), "time", "event", formula="np.log(x) + C(group)")
    pd.testing.assert_frame_equal(result["results"], reference["results"])


def test_strata_and_zero_policy():
    frame = baseline()
    frame["stratum"] = np.arange(len(frame)) % 2
    frame.loc[0, "time"] = 0
    result = fit_multivariate_cox(frame, "time", "event", covariates=["x"], strata="stratum")
    assert "stratum" in result["training_df"]
    with pytest.raises(ValueError, match="positive"):
        fit_weibull_aft(frame, "time", "event", covariates=["x"])
    assert not calculate_rmst(frame, "time", "event", tau=4).empty


@pytest.mark.parametrize("event", [[1, 2], [1, np.nan], [1, .5]])
def test_invalid_events_before_conversion(event):
    with pytest.raises(ValueError, match="binary"):
        outcome_arrays([1, 2], event)


@pytest.mark.parametrize("value", [float("inf"), float("nan"), 0, -1])
def test_horizons(value):
    with pytest.raises(ValueError):
        positive_horizon(value)


def test_concordance_consistent_across_entrypoints():
    pytest.importorskip("sksurv")
    from fyron.survival.boosting import _concordance_index as boosting
    from fyron.validation.survival import _concordance_index as validation
    for function in (concordance, boosting, validation):
        assert np.isnan(function([1, 2], [0, 0], [2, 1]))
        assert np.isnan(function([1, 1], [1, 1], [2, 1]))
        assert function([1, 2, 2], [1, 1, 0], [3, 1, 1]) == pytest.approx(5/6)
        with pytest.raises(ValueError):
            function([1, 2], [1, 2], [2, 1])
        with pytest.raises(ValueError):
            function([1, 2], [1, 0], [np.inf, 1])


def test_dependency_light_import():
    code = '''
import sys
for name in ("lifelines", "formulaic", "sksurv"):
    sys.modules[name] = None
from fyron._survival_data import outcome_arrays, concordance
from fyron.cohort import build_time_to_event_endpoint
outcome_arrays([1, 2], [1, 0])
try:
    concordance([1, 2], [1, 0], [2, 1])
except ImportError as error:
    assert "fyron[survival-ml]" in str(error)
else:
    raise AssertionError("Expected targeted dependency error")
'''
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)


@pytest.mark.parametrize("fit", [fit_multivariate_cox, fit_weibull_aft])
@pytest.mark.parametrize("column,value", [("time", np.nan), ("time", np.inf), ("event", 2)])
def test_invalid_outcomes_cannot_hide_behind_missing_predictors(fit, column, value):
    frame = baseline()
    frame.loc[0, "x"] = np.nan
    frame.loc[0, column] = value
    with pytest.raises(ValueError):
        fit(frame, "time", "event", covariates=["x"])


def test_duplicate_indices_and_nonfinite_formula():
    from fyron._survival_data import prepare_fitting_cohort
    frame = baseline()
    frame.index = [0] * len(frame)
    with pytest.raises(IndexError, match="unique"):
        prepare_fitting_cohort(frame, "time", "event", ["x"])
    frame = baseline()
    frame.loc[0, "x"] = np.inf
    with pytest.raises(ValueError, match="finite"):
        prepare_fitting_cohort(frame, "time", "event", formula="x")


def test_plotting_compatibility_import(monkeypatch):
    from fyron.plotting import plot_kaplan_meier as canonical
    from fyron.ml import plot_kaplan_meier as compatibility
    import fyron.survival

    sentinel = object()
    calls = []

    def implementation(*args, **kwargs):
        calls.append((args, kwargs))
        return sentinel

    monkeypatch.setattr(fyron.survival, "plot_kaplan_meier", implementation)
    for function in (canonical, compatibility):
        assert function("data", duration_col="time") is sentinel
    assert calls == [(("data",), {"duration_col": "time"})] * 2


@pytest.mark.parametrize("fit", [fit_multivariate_cox, fit_weibull_aft])
def test_formula_and_covariates_remain_mutually_exclusive(fit):
    frame = baseline()
    with pytest.raises(ValueError, match="only one"):
        fit(frame, "time", "event", formula="x", covariates=["not_present"])
