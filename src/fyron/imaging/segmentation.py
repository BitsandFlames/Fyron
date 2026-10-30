"""Segmentation metric helpers for aligned masks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from ._spacing import validate_spacing as _validate_spacing, voxel_volume_ml as _voxel_volume_ml


def dice_score(mask_true: Any, mask_pred: Any, *, label: int | None = None) -> float:
    """Return Dice score for binary masks or one label in label maps."""

    a, b = _binary_pair(mask_true, mask_pred, label=label)
    denom = int(a.sum() + b.sum())
    if denom == 0:
        return 1.0
    return float(2 * np.logical_and(a, b).sum() / denom)


def hausdorff_distance(
    mask_true: Any,
    mask_pred: Any,
    *,
    label: int | None = None,
    spacing: Sequence[float] | None = None,
    percentile: float | None = None,
) -> float:
    """Return symmetric Hausdorff distance between mask surfaces."""

    if percentile is not None and (not np.isfinite(percentile) or not 0 <= percentile <= 100):
        raise ValueError("percentile must be finite and between 0 and 100.")
    a, b = _binary_pair(mask_true, mask_pred, label=label)
    coords_a = _surface_coordinates(a, spacing)
    coords_b = _surface_coordinates(b, spacing)
    if len(coords_a) == 0 or len(coords_b) == 0:
        return float("nan")
    dists = np.concatenate([_min_distances(coords_a, coords_b), _min_distances(coords_b, coords_a)])
    if percentile is not None:
        return float(np.percentile(dists, percentile))
    return float(np.max(dists))


def surface_dice(
    mask_true: Any,
    mask_pred: Any,
    *,
    label: int | None = None,
    tolerance: float = 1.0,
    spacing: Sequence[float] | None = None,
) -> float:
    """Return surface Dice at a distance tolerance."""

    _validate_tolerance(tolerance)
    a, b = _binary_pair(mask_true, mask_pred, label=label)
    coords_a = _surface_coordinates(a, spacing)
    coords_b = _surface_coordinates(b, spacing)
    if len(coords_a) == 0 and len(coords_b) == 0:
        return 1.0
    if len(coords_a) == 0 or len(coords_b) == 0:
        return 0.0
    close_a = (_min_distances(coords_a, coords_b) <= tolerance).sum()
    close_b = (_min_distances(coords_b, coords_a) <= tolerance).sum()
    return float((close_a + close_b) / (len(coords_a) + len(coords_b)))


def volume_difference(
    mask_true: Any,
    mask_pred: Any,
    *,
    label: int | None = None,
    spacing: Sequence[float] | None = None,
) -> dict[str, float]:
    """Return absolute and relative volume differences."""

    a, b = _binary_pair(mask_true, mask_pred, label=label)
    voxel_ml = _voxel_volume_ml(spacing, a.ndim)
    true_ml = float(a.sum() * voxel_ml)
    pred_ml = float(b.sum() * voxel_ml)
    diff = pred_ml - true_ml
    return {
        "true_volume_ml": true_ml,
        "pred_volume_ml": pred_ml,
        "absolute_difference_ml": float(abs(diff)),
        "signed_difference_ml": float(diff),
        "relative_difference_percent": float(100 * diff / true_ml) if true_ml else float("nan"),
    }


def label_overlap_table(
    mask_true: Any,
    mask_pred: Any,
    *,
    labels: Sequence[int] | Mapping[int, str] | None = None,
    spacing: Sequence[float] | None = None,
) -> pd.DataFrame:
    """Return label-wise overlap and volume metrics."""

    arr_true = np.asarray(mask_true)
    arr_pred = np.asarray(mask_pred)
    _require_same_shape(arr_true, arr_pred)
    _voxel_volume_ml(spacing, arr_true.ndim)
    rows = []
    for label, name in _resolve_labels(arr_true, arr_pred, labels):
        rows.append(
            {
                "label": int(label),
                "label_name": name,
                "dice": dice_score(arr_true, arr_pred, label=label),
                **volume_difference(arr_true, arr_pred, label=label, spacing=spacing),
            }
        )
    return pd.DataFrame(rows)


def segmentation_metric_table(
    mask_true: Any,
    mask_pred: Any,
    *,
    labels: Sequence[int] | Mapping[int, str] | None = None,
    spacing: Sequence[float] | None = None,
    surface_tolerance: float = 1.0,
) -> pd.DataFrame:
    """Return label-wise Dice, Hausdorff, surface Dice, and volume metrics."""

    _validate_tolerance(surface_tolerance)
    table = label_overlap_table(mask_true, mask_pred, labels=labels, spacing=spacing)
    rows = []
    for _, row in table.iterrows():
        label = int(row["label"])
        rows.append(
            {
                **row.to_dict(),
                "hausdorff_distance": hausdorff_distance(mask_true, mask_pred, label=label, spacing=spacing),
                "surface_dice": surface_dice(
                    mask_true,
                    mask_pred,
                    label=label,
                    tolerance=surface_tolerance,
                    spacing=spacing,
                ),
                "surface_tolerance": float(surface_tolerance),
            }
        )
    return pd.DataFrame(rows)


def _binary_pair(mask_true: Any, mask_pred: Any, *, label: int | None) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(mask_true)
    b = np.asarray(mask_pred)
    _require_same_shape(a, b)
    if label is None:
        return a.astype(bool), b.astype(bool)
    return a == label, b == label


def _surface_coordinates(mask: np.ndarray, spacing: Sequence[float] | None) -> np.ndarray:
    surface = _surface_mask(mask.astype(bool))
    coords = np.argwhere(surface).astype(float)
    if spacing is not None:
        coords *= _validate_spacing(spacing, mask.ndim)
    return coords


def _surface_mask(mask: np.ndarray) -> np.ndarray:
    if mask.ndim < 2:
        return mask.astype(bool)
    padded = np.pad(mask.astype(bool), 1, constant_values=False)
    center = tuple(slice(1, -1) for _ in range(mask.ndim))
    interior = padded[center].copy()
    for axis in range(mask.ndim):
        before = [slice(1, -1)] * mask.ndim
        after = [slice(1, -1)] * mask.ndim
        before[axis] = slice(0, -2)
        after[axis] = slice(2, None)
        interior &= padded[tuple(before)]
        interior &= padded[tuple(after)]
    return mask & ~interior


def _min_distances(coords_a: np.ndarray, coords_b: np.ndarray) -> np.ndarray:
    chunks = []
    for start in range(0, len(coords_a), 1024):
        chunk = coords_a[start : start + 1024]
        dists = np.sqrt(((chunk[:, None, :] - coords_b[None, :, :]) ** 2).sum(axis=2))
        chunks.append(dists.min(axis=1))
    return np.concatenate(chunks) if chunks else np.asarray([], dtype=float)


def _validate_tolerance(value: float) -> None:
    if not np.isfinite(value) or value < 0:
        raise ValueError("tolerance must be finite and non-negative.")


def _resolve_labels(
    mask_true: np.ndarray,
    mask_pred: np.ndarray,
    labels: Sequence[int] | Mapping[int, str] | None,
) -> list[tuple[int, str]]:
    if labels is None:
        values = sorted(set(np.unique(mask_true)).union(np.unique(mask_pred)) - {0})
        return [(int(label), str(int(label))) for label in values]
    if isinstance(labels, Mapping):
        return [(int(label), str(name)) for label, name in labels.items()]
    return [(int(label), str(int(label))) for label in labels]


def _require_same_shape(a: np.ndarray, b: np.ndarray) -> None:
    if a.shape != b.shape:
        raise ValueError(f"Masks must have identical shape, got {a.shape} and {b.shape}.")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Masks must contain only finite values.")
