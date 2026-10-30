from __future__ import annotations

import pandas as pd

from fyron import validation as fv


def test_validation_helpers() -> None:
    y_true = [0, 0, 1, 1]
    y_prob = [0.1, 0.3, 0.7, 0.9]

    best = fv.find_best_threshold(y_true, y_prob)
    assert "threshold_table" in best
    assert best["threshold"] <= 0.7

    summary, bins = fv.calibration_summary(y_true, y_prob, n_bins=2)
    assert summary["brier_score"] >= 0
    assert len(bins) == 2

    dca = fv.decision_curve_table(y_true, y_prob, thresholds=[0.2, 0.5])
    assert set(dca["threshold"]) == {0.2, 0.5}

    df = pd.DataFrame(
        {
            "group": ["A", "A", "B", "B", "A", "B"],
            "truth": [0, 1, 0, 1, 0, 1],
            "pred": [0, 1, 0, 1, 0, 1],
            "prob": [0.1, 0.8, 0.2, 0.9, 0.3, 0.7],
        }
    )
    subgroup = fv.subgroup_metric_table(
        df,
        group_col="group",
        y_true_col="truth",
        y_pred_col="pred",
        y_prob_col="prob",
    )
    assert set(subgroup["group"]) == {"A", "B"}

    boot = fv.bootstrap_classification_metrics(
        y_true,
        [0, 0, 1, 1],
        y_prob,
        n_rounds=20,
        random_state=7,
    )
    assert {"metric", "estimate", "ci_lower", "ci_upper"}.issubset(boot.columns)
    assert "auc" in set(boot["metric"])
