"""2-D slice extraction from Z,Y,X volumes."""

from __future__ import annotations

from typing import Literal

import numpy as np

Orientation = Literal["axial", "sagittal", "coronal"]


def orientation_axis(orientation: Orientation) -> int:
    """Return the NumPy axis index for the given orientation (Z,Y,X volume)."""
    if orientation == "axial":
        return 0
    if orientation == "coronal":
        return 1
    if orientation == "sagittal":
        return 2
    raise ValueError(f"Unknown orientation: {orientation!r}")


def orientation_label(orientation: Orientation) -> str:
    if orientation == "axial":
        return "z"
    if orientation == "coronal":
        return "y"
    if orientation == "sagittal":
        return "x"
    raise ValueError(f"Unknown orientation: {orientation!r}")


def center_slice_index(shape: tuple[int, ...], orientation: Orientation) -> int:
    axis = orientation_axis(orientation)
    return int(shape[axis] // 2)


def resolve_slice_indices(
    shape: tuple[int, ...],
    orientation: Orientation,
    *,
    slice_index: int | None = None,
    slice_indices: list[int] | None = None,
) -> list[int]:
    """Resolve one or more slice indices along the orientation axis."""
    axis = orientation_axis(orientation)
    max_idx = shape[axis] - 1
    if slice_indices is not None:
        if slice_index is not None:
            raise ValueError("Pass only one of slice_index or slice_indices.")
        indices = list(slice_indices)
    elif slice_index is not None:
        indices = [slice_index]
    else:
        indices = [center_slice_index(shape, orientation)]

    for idx in indices:
        if idx < 0 or idx > max_idx:
            raise ValueError(
                f"Slice index {idx} out of range for orientation {orientation!r} "
                f"(valid 0..{max_idx}, shape={shape})."
            )
    return indices


def extract_slice(volume: np.ndarray, orientation: Orientation, index: int) -> np.ndarray:
    """Extract a 2-D slice from a Z,Y,X volume for display.

    Coronal and sagittal rows follow the Z axis; they are flipped vertically
    so superior anatomy appears at the top (radiological convention).
    """
    if orientation == "axial":
        return volume[index, :, :]
    if orientation == "coronal":
        return np.flipud(volume[:, index, :])
    if orientation == "sagittal":
        return np.flipud(volume[:, :, index])
    raise ValueError(f"Unknown orientation: {orientation!r}")


def slice_pixel_aspect(
    orientation: Orientation,
    spacing: tuple[float, float, float],
    slice_shape: tuple[int, int],
) -> float:
    """Return display height/width ratio from physical slice extent.

    ``spacing`` is SimpleITK ``(sx, sy, sz)`` in mm. ``slice_shape`` is
    ``(rows, cols)`` after :func:`extract_slice` (Z,Y,X volume indexing).
    """
    sx, sy, sz = spacing
    n_rows, n_cols = slice_shape
    if orientation == "axial":
        physical_h = n_rows * sy
        physical_w = n_cols * sx
    elif orientation == "coronal":
        physical_h = n_rows * sz
        physical_w = n_cols * sx
    elif orientation == "sagittal":
        physical_h = n_rows * sz
        physical_w = n_cols * sy
    else:
        raise ValueError(f"Unknown orientation: {orientation!r}")
    if physical_w <= 0:
        raise ValueError(f"Invalid physical width for slice_shape={slice_shape}, spacing={spacing}")
    return physical_h / physical_w


def resolve_slice_index_for_shape(
    shape: tuple[int, ...],
    orientation: Orientation,
    *,
    slice_index: int | None,
    slice_fraction: float | None,
) -> int:
    """Resolve a single slice index, optionally using a relative fraction."""
    axis = orientation_axis(orientation)
    max_idx = shape[axis] - 1
    if slice_fraction is not None:
        if slice_index is not None:
            raise ValueError("Pass only one of slice_index or slice_fraction.")
        idx = int(round(slice_fraction * max_idx))
    elif slice_index is not None:
        idx = slice_index
    else:
        idx = center_slice_index(shape, orientation)
    if idx < 0 or idx > max_idx:
        raise ValueError(f"Slice index {idx} out of range 0..{max_idx} for shape {shape}.")
    return idx
