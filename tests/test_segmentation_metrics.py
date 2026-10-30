"""Tests for segmentation metrics."""

from __future__ import annotations

import numpy as np

from fyron.imaging import (
    dice_score,
    hausdorff_distance,
    label_overlap_table,
    segmentation_metric_table,
    surface_dice,
    volume_difference,
)


def test_segmentation_metrics_for_tiny_masks() -> None:
    true = np.zeros((3, 5, 5), dtype=int)
    pred = np.zeros_like(true)
    true[:, 1:3, 1:3] = 1
    pred[:, 1:3, 1:4] = 1

    assert 0 < dice_score(true, pred, label=1) < 1
    assert hausdorff_distance(true, pred, label=1) >= 0
    assert 0 <= surface_dice(true, pred, label=1, tolerance=1.0) <= 1
    assert volume_difference(true, pred, label=1, spacing=(1, 1, 1))["pred_volume_ml"] > volume_difference(true, pred, label=1, spacing=(1, 1, 1))["true_volume_ml"]

    overlap = label_overlap_table(true, pred, labels={1: "lesion"}, spacing=(1, 1, 1))
    assert overlap.loc[0, "label_name"] == "lesion"
    metrics = segmentation_metric_table(true, pred, labels=[1], spacing=(1, 1, 1))
    assert "surface_dice" in metrics.columns
