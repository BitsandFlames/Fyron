"""Paired model-comparison statistics for manuscript reporting."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from ._deps import require_numpy, require_scipy_stats


def mcnemar_test(
    y_true: Sequence[Any],
    pred_a: Sequence[Any],
    pred_b: Sequence[Any],
    *,
    exact: bool = False,
) -> pd.DataFrame:
    """Run McNemar's paired test for two classifiers.

    Parameters
    ----------
    y_true
        Ground-truth class labels.
    pred_a
        Predicted class labels from model A.
    pred_b
        Predicted class labels from model B on the same samples.
    exact
        If True, use the exact binomial version; otherwise use the continuity
        corrected chi-square approximation.

    Returns
    -------
    pandas.DataFrame
        One-row table with the test name, statistic, p-value, total sample size,
        discordant-pair counts, and exact-test flag.
    """
    np = require_numpy()
    stats = require_scipy_stats()
    yt = np.asarray(y_true)
    a = np.asarray(pred_a)
    b = np.asarray(pred_b)
    if len({len(yt), len(a), len(b)}) != 1:
        raise ValueError("y_true, pred_a, and pred_b must have the same length.")
    correct_a = a == yt
    correct_b = b == yt
    b01 = int(np.sum(correct_a & ~correct_b))
    b10 = int(np.sum(~correct_a & correct_b))
    discordant = b01 + b10
    if exact:
        p_value = float(stats.binomtest(min(b01, b10), discordant, p=0.5).pvalue) if discordant else 1.0
        statistic = float(min(b01, b10))
        test = "mcnemar_exact"
    else:
        statistic = float((abs(b01 - b10) - 1) ** 2 / discordant) if discordant else 0.0
        p_value = float(stats.chi2.sf(statistic, df=1))
        test = "mcnemar_chi_square"
    return pd.DataFrame(
        [
            {
                "test": test,
                "statistic": statistic,
                "p_value": p_value,
                "n": int(len(yt)),
                "a_correct_b_wrong": b01,
                "a_wrong_b_correct": b10,
                "discordant": discordant,
                "exact": bool(exact),
            }
        ]
    )


def bootstrap_auc_difference(
    y_true: Sequence[Any],
    prob_a: Sequence[Any],
    prob_b: Sequence[Any],
    *,
    pos_label: Any = 1,
    n_rounds: int = 1000,
    alpha: float = 0.05,
    random_state: int | None = None,
    drop_invalid: bool = True,
) -> pd.DataFrame:
    """Bootstrap the paired AUC difference between two models.

    Parameters
    ----------
    y_true
        Ground-truth binary labels.
    prob_a
        Predicted probabilities or scores from model A.
    prob_b
        Predicted probabilities or scores from model B on the same samples.
    pos_label
        Label treated as the positive class.
    n_rounds
        Number of bootstrap resamples.
    alpha
        Two-sided confidence interval width, where ``0.05`` gives 95% intervals.
    random_state
        Optional random seed for reproducible resampling.
    drop_invalid
        If True, skip bootstrap rounds that contain only one class.

    Returns
    -------
    pandas.DataFrame
        One-row table with AUC for both models, paired AUC difference,
        bootstrap confidence interval, requested rounds, valid rounds, dropped
        rounds, and alpha.
    """
    np = require_numpy()
    yt = np.asarray(y_true)
    a = np.asarray(prob_a, dtype=float)
    b = np.asarray(prob_b, dtype=float)
    if len({len(yt), len(a), len(b)}) != 1:
        raise ValueError("y_true, prob_a, and prob_b must have the same length.")
    if n_rounds <= 0:
        raise ValueError("n_rounds must be positive.")
    estimate_a = _auc_from_ranks(yt, a, pos_label=pos_label)
    estimate_b = _auc_from_ranks(yt, b, pos_label=pos_label)
    rng = np.random.default_rng(random_state)
    diffs: list[float] = []
    dropped = 0
    for _ in range(n_rounds):
        idx = rng.integers(0, len(yt), size=len(yt))
        try:
            diff = _auc_from_ranks(yt[idx], a[idx], pos_label=pos_label) - _auc_from_ranks(yt[idx], b[idx], pos_label=pos_label)
        except Exception:
            if drop_invalid:
                dropped += 1
                continue
            raise
        if np.isfinite(diff):
            diffs.append(float(diff))
        elif drop_invalid:
            dropped += 1
        else:
            raise ValueError("bootstrap round produced a non-finite AUC difference.")
    if not diffs:
        raise ValueError("no valid bootstrap rounds were produced.")
    arr = np.asarray(diffs, dtype=float)
    low, high = np.percentile(arr, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return pd.DataFrame(
        [
            {
                "metric": "auc_difference",
                "auc_a": float(estimate_a),
                "auc_b": float(estimate_b),
                "estimate": float(estimate_a - estimate_b),
                "ci_low": float(low),
                "ci_high": float(high),
                "n_rounds": int(len(arr)),
                "requested_rounds": int(n_rounds),
                "dropped_rounds": int(dropped),
                "alpha": float(alpha),
            }
        ]
    )


def _auc_from_ranks(y_true, y_score, *, pos_label: Any = 1) -> float:
    np = require_numpy()
    stats = require_scipy_stats()
    yt = np.asarray(y_true)
    score = np.asarray(y_score, dtype=float)
    positive = yt == pos_label
    n_pos = int(np.sum(positive))
    n_neg = int(np.sum(~positive))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = stats.rankdata(score)
    rank_sum_pos = float(np.sum(ranks[positive]))
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))
