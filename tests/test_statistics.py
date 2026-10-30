"""Tests for fyron.statistics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

from fyron import statistics as fst


def test_normality_and_group_tests() -> None:
    values = [1.0, 1.2, 0.9, 1.1, 1.3, 1.0, 0.95, 1.05]
    normal = fst.normality_test(values)
    assert normal.test == "shapiro"
    assert 0 <= normal.p_value <= 1

    group_a = [1.0, 1.2, 1.1, 1.3]
    group_b = [2.0, 2.1, 1.9, 2.2]
    two_group = fst.compare_two_groups(group_a, group_b)
    assert two_group.test == "welch_ttest"
    assert two_group.details["n_a"] == 4

    multi = fst.compare_multiple_groups([group_a, group_b, [1.4, 1.5, 1.6]], method="kruskal")
    assert multi.test == "kruskal_wallis"
    assert multi.n == 11


def test_categorical_and_correlation_tests() -> None:
    fisher = fst.categorical_test([[1, 9], [8, 2]])
    assert fisher.test == "fisher_exact"
    assert 0 <= fisher.p_value <= 1

    chi2 = fst.categorical_test([[12, 8, 5], [4, 16, 10]], method="chi2")
    assert chi2.test == "chi_square"
    assert chi2.details["dof"] == 2

    corr = fst.correlation_test([1, 2, 3, 4], [1, 3, 2, 5], method="spearman")
    assert corr.test == "spearman_correlation"
    assert corr.n == 4


def test_bootstrap_summary_and_metric() -> None:
    summary = fst.bootstrap_summary(
        [1, 2, 3, 4, 5],
        statistic="mean",
        n_rounds=100,
        random_state=42,
    )
    assert summary.statistic == "mean"
    assert summary.n_rounds == 100
    assert summary.ci_low <= summary.estimate <= summary.ci_high

    def mean_difference(a, b):
        return float(np.mean(a) - np.mean(b))

    result = fst.bootstrap_metric(
        [1, 2, 3, 4],
        [0, 1, 1, 2],
        metric_func=mean_difference,
        metric_name="mean_difference",
        n_rounds=80,
        random_state=1,
    )
    assert result.statistic == "mean_difference"
    assert result.details["n"] == 4


def test_bootstrap_binary_classification_metrics() -> None:
    y_true = [0, 0, 1, 1, 1, 0, 1, 0]
    y_pred = [0, 0, 1, 0, 1, 1, 1, 0]
    y_prob = [0.1, 0.2, 0.9, 0.45, 0.8, 0.7, 0.75, 0.05]

    table = fst.bootstrap_binary_classification_metrics(
        y_true,
        y_pred,
        y_prob,
        metrics=["sensitivity", "specificity", "auc"],
        n_rounds=120,
        random_state=7,
    )
    assert isinstance(table, pd.DataFrame)
    assert set(table["metric"]) == {"sensitivity", "specificity", "auc"}
    assert table["ci_low"].le(table["ci_high"]).all()


def test_p_value_correction_helpers() -> None:
    p = [0.01, 0.04, 0.03, np.nan]
    adjusted = fst.adjust_p_values(p, method="fdr_bh", alpha=0.05)
    assert adjusted.loc[0, "p_adjusted"] == pytest.approx(0.03)
    assert adjusted.loc[1, "p_adjusted"] == pytest.approx(0.04)
    assert pd.isna(adjusted.loc[3, "p_adjusted"])

    bonferroni = fst.adjust_p_values([0.01, 0.2], method="bonferroni")
    assert bonferroni["p_adjusted"].tolist() == pytest.approx([0.02, 0.4])

    holm = fst.adjust_p_values([0.01, 0.04, 0.03], method="holm")
    assert holm["p_adjusted"].max() <= 1.0

    table = fst.p_value_correction_table(pd.DataFrame({"term": ["a", "b"], "p_value": [0.01, 0.5]}))
    assert {"p_adjusted", "rejected", "p_adjust_method"}.issubset(table.columns)


def test_model_comparison_statistics() -> None:
    y_true = [0, 0, 1, 1, 1, 0, 1, 0]
    pred_a = [0, 0, 1, 0, 1, 1, 1, 0]
    pred_b = [0, 1, 1, 1, 1, 0, 0, 0]
    mc = fst.mcnemar_test(y_true, pred_a, pred_b)
    assert mc.loc[0, "discordant"] >= 0
    assert 0 <= mc.loc[0, "p_value"] <= 1

    auc = fst.bootstrap_auc_difference(
        y_true,
        [0.1, 0.2, 0.9, 0.45, 0.8, 0.7, 0.75, 0.05],
        [0.2, 0.4, 0.8, 0.75, 0.7, 0.2, 0.35, 0.1],
        n_rounds=50,
        random_state=42,
    )
    assert auc.loc[0, "metric"] == "auc_difference"
    assert auc.loc[0, "n_rounds"] > 0
