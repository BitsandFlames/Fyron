"""Tests for effect-size helpers."""

from __future__ import annotations

from fyron.statistics import (
    cliffs_delta,
    cohens_d,
    cramers_v,
    odds_ratio_ci,
    risk_ratio_ci,
    standardized_mean_difference,
)


def test_effect_sizes_and_ratio_ci() -> None:
    assert cohens_d([2, 3, 4], [1, 2, 3]) > 0
    assert cliffs_delta([3, 4], [1, 2]) == 1.0
    assert cramers_v([[10, 5], [3, 12]]) > 0
    assert odds_ratio_ci([[10, 5], [3, 12]])["odds_ratio"] > 1
    assert risk_ratio_ci([[10, 5], [3, 12]])["risk_ratio"] > 1
    assert standardized_mean_difference([1, 1, 0], [0, 0, 1], categorical=True) > 0
