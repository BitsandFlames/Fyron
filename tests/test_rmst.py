"""Numerical regression tests for RMST inference."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from fyron.survival import calculate_rmst, compare_rmst


@pytest.fixture
def censored_cohort():
    return pd.DataFrame({
        "t": [1, 2, 2, 4, 5, 6, 1, 3, 3, 4, 6, 7],
        "e": [1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0],
        "g": ["A"] * 6 + ["B"] * 6,
    })


def test_censored_reference_values(censored_cohort):
    # survRM2::rmst1 at commit 044089fcdd77b46e754cd18ac6d7f21498ce5e73.
    # Independently evaluated from its area/Greenwood formula:
    # A: RMST=65/18, variance=(47/18)^2/30+(16/9)^2/20+(4/9)^2/6.
    # B: RMST=21/5, variance=(6/5)^2 * 2/(5*3).
    expected = [
        [3.611111111111111, 0.6466914848234898, 2.34361909174834, 4.878603130473882],
        [4.2, 0.4381780460041329, 3.3411868110157648, 5.058813188984235],
    ]
    columns = ["rmst", "rmst_se", "rmst_lower", "rmst_upper"]
    grouped = calculate_rmst(censored_cohort, "t", "e", group_col="g", tau=5)
    np.testing.assert_allclose(grouped[columns], expected, rtol=1e-12)
    for i, group in enumerate(["A", "B"]):
        single = calculate_rmst(censored_cohort.query("g == @group"), "t", "e", tau=5)
        np.testing.assert_allclose(single[columns].iloc[0], expected[i], rtol=1e-12)


def test_censored_comparison_and_reference_swap(censored_cohort):
    forward = compare_rmst(censored_cohort, "t", "e", "g", "A", tau=5).iloc[0]
    reverse = compare_rmst(censored_cohort, "t", "e", "g", "B", tau=5).iloc[0]
    np.testing.assert_allclose(
        forward[["difference", "diff_lower", "diff_upper", "p_value"]].astype(float),
        [0.5888888888888889, -0.9421552361191353, 2.119933013896913, 0.450930118614172],
        rtol=1e-12,
    )
    assert reverse.difference == pytest.approx(-forward.difference)
    assert reverse.diff_lower == pytest.approx(-forward.diff_upper)
    assert reverse.diff_upper == pytest.approx(-forward.diff_lower)
    assert reverse.p_value == pytest.approx(forward.p_value)


@pytest.mark.parametrize("times", [[1, 2, 3, 4], [0, 0, 2, 4], [1, 1, 2, 2], [0], [2]])
@pytest.mark.parametrize("tau", [0.5, 1, 2.5, 4, 6])
def test_uncensored_empirical_mean_and_variance(times, tau):
    df = pd.DataFrame({"t": times, "e": 1})
    row = calculate_rmst(df, "t", "e", tau=tau).iloc[0]
    truncated = np.minimum(times, tau)
    assert row.rmst == pytest.approx(np.mean(truncated))
    assert row.rmst_se**2 == pytest.approx(np.var(truncated, ddof=0) / len(times))


def test_replication_halves_standard_error(censored_cohort):
    original = calculate_rmst(censored_cohort, "t", "e", group_col="g", tau=5)
    replicated = calculate_rmst(pd.concat([censored_cohort] * 4), "t", "e", group_col="g", tau=5)
    np.testing.assert_allclose(replicated.rmst, original.rmst)
    np.testing.assert_allclose(replicated.rmst_se, original.rmst_se / 2)


@pytest.mark.parametrize("events", [[0, 0, 0, 0], [1, 1, 1, 1]])
def test_zero_variance_comparison(events):
    df = pd.DataFrame({"t": [2, 2, 2, 2], "e": events, "g": ["A", "A", "B", "B"]})
    base = calculate_rmst(df, "t", "e", group_col="g", tau=3)
    assert (base.rmst_se == 0).all()
    np.testing.assert_array_equal(base.rmst_lower, base.rmst_upper)
    row = compare_rmst(df, "t", "e", "g", "A", tau=3).iloc[0]
    assert row.diff_lower == row.diff_upper == row.difference == 0
    assert np.isnan(row.p_value)


def test_zero_time_with_tied_censoring():
    df = pd.DataFrame({"t": [0, 0, 2, 4], "e": [1, 0, 1, 0]})
    row = calculate_rmst(df, "t", "e", tau=3).iloc[0]
    assert row.rmst == pytest.approx(1.875)
    assert row.rmst_se**2 == pytest.approx(1.875**2 / 12 + 0.375**2 / 2)


def test_continued_km_tail():
    df = pd.DataFrame({"t": [1, 2], "e": [1, 0]})
    row = calculate_rmst(df, "t", "e", tau=4).iloc[0]
    assert row.rmst == pytest.approx(2.5)
    assert row.rmst_se**2 == pytest.approx(1.125)


def test_small_p_value_is_not_rounded_to_zero():
    df = pd.DataFrame({"t": [1, 2, 8, 9], "e": 1, "g": ["A", "A", "B", "B"]})
    row = compare_rmst(df, "t", "e", "g", "A", tau=9).iloc[0]
    assert 0 < row.p_value < 1e-40
    assert row.p_value == pytest.approx(2 * norm.sf(14), rel=1e-12, abs=0)


@pytest.mark.parametrize("tau", [np.inf, -np.inf, np.nan, 0, -1])
def test_invalid_tau(tau):
    df = pd.DataFrame({"t": [1, 2], "e": [1, 0]})
    with pytest.raises(ValueError, match="finite positive"):
        calculate_rmst(df, "t", "e", tau=tau)
