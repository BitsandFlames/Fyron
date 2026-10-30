"""Slice selection and 2-D cropping by BOA body-region label."""

from __future__ import annotations

from typing import Literal

import numpy as np

from fyron.visualization._boa_labels import BODY_REGION_NAMES
from fyron.visualization._slices import Orientation, extract_slice, orientation_axis

BodyRegionSliceMode = Literal["best", "center", "all"]


def resolve_body_region_label(value: int | str) -> int:
    """Resolve a body-region label id from an integer or BOA region name."""
    if isinstance(value, int):
        if value in BODY_REGION_NAMES:
            return value
        raise ValueError(
            f"Unknown body region label id {value}. "
            f"Valid ids: {sorted(BODY_REGION_NAMES)}."
        )
    key = value.strip().lower().replace("_", " ")
    for label_id, name in BODY_REGION_NAMES.items():
        if name.lower() == key:
            return label_id
    raise ValueError(
        f"Unknown body region name {value!r}. "
        f"Valid names: {list(BODY_REGION_NAMES.values())}."
    )


def _in_plane_counts(
    body_regions: np.ndarray,
    label_id: int,
    orientation: Orientation,
) -> np.ndarray:
    mask = np.rint(body_regions).astype(np.int32) == label_id
    axis = orientation_axis(orientation)
    axes = tuple(i for i in range(mask.ndim) if i != axis)
    return mask.sum(axis=axes)


def slices_with_body_region(
    body_regions: np.ndarray,
    label_id: int,
    orientation: Orientation,
) -> list[int]:
    """Return slice indices along ``orientation`` that contain ``label_id``."""
    counts = _in_plane_counts(body_regions, label_id, orientation)
    return [int(i) for i, count in enumerate(counts) if count > 0]


def select_body_region_slices(
    body_regions: np.ndarray,
    label_id: int,
    orientation: Orientation,
    *,
    mode: BodyRegionSliceMode = "best",
) -> list[int]:
    """Pick slice index(es) where a body region is present."""
    available = slices_with_body_region(body_regions, label_id, orientation)
    if not available:
        name = BODY_REGION_NAMES.get(label_id, str(label_id))
        raise ValueError(
            f"Body region {name!r} (label {label_id}) not found for "
            f"orientation {orientation!r}."
        )
    if mode == "all":
        return available
    if mode == "center":
        return [available[len(available) // 2]]
    counts = _in_plane_counts(body_regions, label_id, orientation)
    best = max(available, key=lambda i: int(counts[i]))
    return [best]


def padding_voxels_for_orientation(
    orientation: Orientation,
    spacing: tuple[float, float, float],
    padding_mm: float,
) -> tuple[int, int]:
    """Return row/column padding in voxels for a 2-D slice."""
    sx, sy, sz = spacing
    pad_mm = max(0.0, float(padding_mm))
    if orientation == "axial":
        return int(round(pad_mm / sy)), int(round(pad_mm / sx))
    if orientation == "coronal":
        return int(round(pad_mm / sz)), int(round(pad_mm / sx))
    if orientation == "sagittal":
        return int(round(pad_mm / sz)), int(round(pad_mm / sy))
    raise ValueError(f"Unknown orientation: {orientation!r}")


def bbox_for_label_on_slice(
    slice_2d: np.ndarray,
    label_id: int,
    *,
    pad_rows: int = 0,
    pad_cols: int = 0,
) -> tuple[int, int, int, int]:
    """Return ``(row0, row1, col0, col1)`` bounding box for ``label_id``."""
    labels = np.rint(slice_2d).astype(np.int32)
    rows, cols = np.where(labels == label_id)
    if rows.size == 0:
        raise ValueError(f"Body region label {label_id} not present on slice.")
    r0 = max(0, int(rows.min()) - pad_rows)
    r1 = min(slice_2d.shape[0], int(rows.max()) + 1 + pad_rows)
    c0 = max(0, int(cols.min()) - pad_cols)
    c1 = min(slice_2d.shape[1], int(cols.max()) + 1 + pad_cols)
    if r1 <= r0 or c1 <= c0:
        raise ValueError(f"Invalid crop for body region label {label_id}.")
    return r0, r1, c0, c1


def crop_slice_2d(slice_2d: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    r0, r1, c0, c1 = bbox
    return slice_2d[r0:r1, c0:c1]


def extract_and_crop_slice(
    volume: np.ndarray,
    body_regions: np.ndarray,
    *,
    orientation: Orientation,
    slice_index: int,
    label_id: int,
    spacing: tuple[float, float, float],
    padding_mm: float,
) -> np.ndarray:
    """Extract a display slice and crop it to a body-region bounding box."""
    seg_sl = extract_slice(body_regions, orientation, slice_index)
    pad_rows, pad_cols = padding_voxels_for_orientation(orientation, spacing, padding_mm)
    bbox = bbox_for_label_on_slice(
        seg_sl,
        label_id,
        pad_rows=pad_rows,
        pad_cols=pad_cols,
    )
    sl = extract_slice(volume, orientation, slice_index)
    return crop_slice_2d(sl, bbox)
