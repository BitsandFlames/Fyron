"""Numerical and adversarial regressions for statistical inference."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from fyron import statistics as fst
from fyron.descriptive import compare_descriptive_groups


@pytest.mark.parametrize("method", ["auto", "paired_ttest", "wilcoxon"])
def test_joint_pair_filter(method):
    a = [1, np.nan, 3, 8, 10]
    b = [2, 5, np.nan, 4, 7]
    out = fst.compare_two_groups(a, b, paired=method == "auto", method=method)
    expected = stats.wilcoxon([1, 8, 10], [2, 4, 7]) if method == "wilcoxon" else stats.ttest_rel([1, 8, 10], [2, 4, 7])
    assert out.p_value == pytest.approx(expected.pvalue)
    assert out.n == 3
    assert out.details["paired"] is True


def test_paired_validation():
    with pytest.raises(ValueError, match="equal length"):
        fst.compare_two_groups([1, 2, np.nan], [2, 3], method="paired_ttest")
    with pytest.raises(ValueError, match="conflicts"):
        fst.compare_two_groups([1, 2], [2, 3], paired=True, method="ttest")


def test_undefined_effects_are_not_balance():
    assert np.isnan(fst.cohens_d([1, 1], [2, 2]))
    assert np.isnan(fst.standardized_mean_difference([1, 1], [0, 0], categorical=True))
    assert fst.compare_two_groups([1, 2, 3], [2, 3, 4], paired=True).effect_size is None
    df = pd.DataFrame({"g": ["a", "a", "b", "b"], "x": [1, 1, 2, 2]})
    out = compare_descriptive_groups(df, group_col="g", numeric=["x"])
    assert np.isnan(out.loc[out.variable == "x", "smd"]).all()


def test_ols_against_scipy():
    x = np.arange(10, dtype=float)
    y = 2 + 1.5 * x + np.array([1, -1, 0, 2, -2, 1, 0, -1, 2, 0])
    ref = stats.linregress(x, y)
    out = fst.fit_linear_regression_table(pd.DataFrame({"x": x, "y": y}), outcome_col="y", covariates=["x"]).set_index("term")
    np.testing.assert_allclose(out.beta, [ref.intercept, ref.slope])
    np.testing.assert_allclose(out.std_error, [ref.intercept_stderr, ref.stderr])
    assert out.loc["x", "p_value"] == pytest.approx(ref.pvalue)
    crit = stats.t.ppf(.975, 8)
    np.testing.assert_allclose(out.ci_lower, out.beta - crit * out.std_error)
    np.testing.assert_allclose(out.ci_upper, out.beta + crit * out.std_error)


def test_logistic_against_closed_form():
    df = pd.DataFrame({"x": [0] * 40 + [1] * 40, "y": [1] * 10 + [0] * 30 + [1] * 24 + [0] * 16})
    out = fst.fit_logistic_regression_table(df, outcome_col="y", covariates=["x"]).set_index("term")
    beta = np.array([np.log(10 / 30), np.log(24 / 16) - np.log(10 / 30)])
    se = np.sqrt([1 / 10 + 1 / 30, 1 / 10 + 1 / 30 + 1 / 24 + 1 / 16])
    np.testing.assert_allclose(out.log_odds, beta, atol=1e-6)
    np.testing.assert_allclose(out.std_error, se, atol=1e-6)
    np.testing.assert_allclose(out.p_value, 2 * stats.norm.sf(abs(beta / se)), rtol=1e-5)
    np.testing.assert_allclose(out.ci_lower, np.exp(beta - stats.norm.ppf(.975) * se), rtol=1e-5)
    np.testing.assert_allclose(out.ci_upper, np.exp(beta + stats.norm.ppf(.975) * se), rtol=1e-5)


@pytest.mark.parametrize("fit", [fst.fit_linear_regression_table, fst.fit_logistic_regression_table])
def test_reject_rank_deficiency_and_alpha(fit):
    df = pd.DataFrame({"x": range(8), "duplicate": range(8), "y": [0, 1] * 4})
    with pytest.raises(ValueError, match="rank"):
        fit(df, outcome_col="y", covariates=["x", "duplicate"])
    with pytest.raises(ValueError, match="alpha"):
        fit(df, outcome_col="y", covariates=["x"], alpha=1)
    with pytest.raises(ValueError, match="finite"):
        fit(df.assign(y=np.inf), outcome_col="y", covariates=["x"])


def test_logistic_rejects_fractional_labels_and_separation():
    df = pd.DataFrame({"x": range(20), "y": [.2, 1.2] * 10})
    with pytest.raises(ValueError, match="0/1"):
        fst.fit_logistic_regression_table(df, outcome_col="y", covariates=["x"])
    with pytest.raises(ValueError):
        fst.fit_logistic_regression_table(df.assign(y=[0] * 10 + [1] * 10), outcome_col="y", covariates=["x"])
