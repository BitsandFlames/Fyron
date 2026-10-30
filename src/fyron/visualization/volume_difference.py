"""Slice-wise CT/MR volume difference heatmaps."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import SimpleITK as sitk

from fyron.imaging.nifti_io import read_nifti
from fyron.imaging.normalize import normalize_mr
from fyron.plotting_palettes import resolve_colormap
from fyron.visualization._slices import (
    Orientation,
    extract_slice,
    resolve_slice_index_for_shape,
    resolve_slice_indices,
)

StrPath = Union[str, Path]
VolumeInput = StrPath | sitk.Image | np.ndarray
DataType = Literal["ct_hu", "ct_uint16", "mr"]


def plot_volume_difference_heatmap(
    volume_a: VolumeInput,
    volume_b: VolumeInput,
    *,
    data_type: DataType = "ct_hu",
    orientation: Orientation = "axial",
    slice_index: int | None = None,
    slice_indices: Sequence[int] | None = None,
    slice_fraction: float | None = None,
    label_a: str = "Volume A",
    label_b: str = "Volume B",
    window_center: float = 40.0,
    window_width: float = 400.0,
    rescale_slope: float = 1.0,
    rescale_intercept: float = -1024.0,
    mr_normalization: str = "percentile",
    mr_percentile: float = 99.0,
    diff_vmax: float | None = None,
    diff_percentile: float = 99.0,
    diff_cmap: str = "fyron_diverging_blue_red",
    figsize: tuple[float, float] | None = None,
    title: str | None = None,
    save_path: StrPath | None = None,
) -> tuple[plt.Figure, np.ndarray, pd.DataFrame]:
    """Plot aligned CT/MR slices with a zero-centered difference heatmap.

    Parameters
    ----------
    volume_a, volume_b
        NIfTI path, ``SimpleITK.Image``, or NumPy array in ``(z, y, x)`` order.
        Path and SimpleITK inputs are checked for matching spacing, origin, and
        direction. NumPy arrays are checked for shape only.
    data_type
        ``"ct_hu"`` assumes arrays are already Hounsfield units. ``"ct_uint16"``
        converts stored values with ``arr * rescale_slope + rescale_intercept``.
        ``"mr"`` normalizes each volume to a ``[0, 1]`` scale before comparison.
    orientation
        Slice plane: ``"axial"``, ``"coronal"``, or ``"sagittal"``.
    slice_index, slice_indices, slice_fraction
        Select one absolute slice, several absolute slices, or one relative
        slice location in ``[0, 1]``. If none is provided, the center slice is
        shown.
    label_a, label_b
        Column labels for the first two panels.
    window_center, window_width
        CT display window for ``ct_hu`` and ``ct_uint16`` inputs.
    rescale_slope, rescale_intercept
        Conversion from stored CT values to HU for ``data_type="ct_uint16"``.
    mr_normalization, mr_percentile
        MR normalization mode and percentile passed to ``normalize_mr``.
    diff_vmax
        Symmetric absolute limit for the difference map. When omitted, it is
        estimated from ``diff_percentile`` of the absolute full-volume
        difference.
    diff_percentile
        Percentile used for automatic ``diff_vmax``.
    diff_cmap
        Matplotlib colormap name or Fyron named diverging colormap.
    figsize
        Optional figure size. Defaults to a readable size based on slice count.
    title
        Optional figure title.
    save_path
        Optional output image path. Parent directories are created.

    Returns
    -------
    tuple
        ``(fig, axes, table)`` where ``axes`` is an ``n_slices x 3`` array and
        ``table`` contains slice-level difference summary statistics.

    Raises
    ------
    ValueError
        If shapes differ, path/SimpleITK geometry differs, slice arguments are
        inconsistent, or an unsupported ``data_type`` is requested.
    """
    loaded_a = _load_volume(volume_a, label="volume_a")
    loaded_b = _load_volume(volume_b, label="volume_b")
    _validate_same_shape_and_geometry(loaded_a, loaded_b)

    arr_a, arr_b, units = _prepare_intensity_arrays(
        loaded_a["array"],
        loaded_b["array"],
        data_type=data_type,
        rescale_slope=rescale_slope,
        rescale_intercept=rescale_intercept,
        mr_normalization=mr_normalization,
        mr_percentile=mr_percentile,
    )
    diff = arr_a - arr_b
    indices = _resolve_requested_slices(
        arr_a.shape,
        orientation,
        slice_index=slice_index,
        slice_indices=slice_indices,
        slice_fraction=slice_fraction,
    )

    vmax = _resolve_diff_vmax(diff, diff_vmax=diff_vmax, percentile=diff_percentile)
    cmap = resolve_colormap(diff_cmap)
    n_rows = len(indices)
    if figsize is None:
        figsize = (10.5, max(3.2, 3.0 * n_rows))
    fig, axes = plt.subplots(n_rows, 3, figsize=figsize, squeeze=False, constrained_layout=True)

    rows: list[dict[str, Any]] = []
    for row_idx, idx in enumerate(indices):
        slice_a = extract_slice(arr_a, orientation, idx)
        slice_b = extract_slice(arr_b, orientation, idx)
        slice_diff = extract_slice(diff, orientation, idx)

        _imshow_anatomy(
            axes[row_idx, 0],
            slice_a,
            data_type=data_type,
            window_center=window_center,
            window_width=window_width,
        )
        axes[row_idx, 0].set_title(label_a if row_idx == 0 else "")
        _imshow_anatomy(
            axes[row_idx, 1],
            slice_b,
            data_type=data_type,
            window_center=window_center,
            window_width=window_width,
        )
        axes[row_idx, 1].set_title(label_b if row_idx == 0 else "")
        im = axes[row_idx, 2].imshow(slice_diff, cmap=cmap, vmin=-vmax, vmax=vmax)
        axes[row_idx, 2].set_title(f"Difference ({label_a} - {label_b})" if row_idx == 0 else "")

        for ax in axes[row_idx, :]:
            ax.set_xticks([])
            ax.set_yticks([])
        axes[row_idx, 0].set_ylabel(f"{orientation}={idx}", fontsize=9)

        finite = slice_diff[np.isfinite(slice_diff)]
        rows.append(
            {
                "slice_index": idx,
                "orientation": orientation,
                "units": units,
                "mean_difference": float(np.mean(finite)) if finite.size else np.nan,
                "median_difference": float(np.median(finite)) if finite.size else np.nan,
                "mean_absolute_difference": float(np.mean(np.abs(finite))) if finite.size else np.nan,
                "rmse": float(np.sqrt(np.mean(finite**2))) if finite.size else np.nan,
                "min_difference": float(np.min(finite)) if finite.size else np.nan,
                "max_difference": float(np.max(finite)) if finite.size else np.nan,
                "diff_vmax": float(vmax),
            }
        )

    cbar = fig.colorbar(im, ax=axes[:, 2], shrink=0.82)
    cbar.set_label(f"Difference ({units})")
    if title:
        fig.suptitle(title)

    if save_path is not None:
        out = Path(save_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, bbox_inches="tight", dpi=300)

    return fig, axes, pd.DataFrame(rows)


def _load_volume(volume: VolumeInput, *, label: str) -> dict[str, Any]:
    if isinstance(volume, (str, Path)):
        path = Path(volume).expanduser().resolve()
        image, arr = read_nifti(path, return_array=True)
        return {"array": np.asarray(arr), "geometry": _geometry_from_image(image), "source": path}
    if isinstance(volume, sitk.Image):
        return {
            "array": sitk.GetArrayFromImage(volume),
            "geometry": _geometry_from_image(volume),
            "source": "SimpleITK.Image",
        }
    arr = np.asarray(volume)
    if arr.ndim != 3:
        raise ValueError(f"{label} must be a 3D volume in (z, y, x) order, got shape {arr.shape}.")
    return {"array": arr, "geometry": None, "source": "numpy.ndarray"}


def _geometry_from_image(image: sitk.Image) -> dict[str, tuple[float, ...]]:
    return {
        "spacing": tuple(float(v) for v in image.GetSpacing()),
        "origin": tuple(float(v) for v in image.GetOrigin()),
        "direction": tuple(float(v) for v in image.GetDirection()),
    }


def _validate_same_shape_and_geometry(a: dict[str, Any], b: dict[str, Any]) -> None:
    shape_a = tuple(a["array"].shape)
    shape_b = tuple(b["array"].shape)
    if shape_a != shape_b:
        raise ValueError(f"Volume shape mismatch: volume_a shape {shape_a} vs volume_b shape {shape_b}.")

    geom_a = a["geometry"]
    geom_b = b["geometry"]
    if geom_a is None or geom_b is None:
        return
    for key in ("spacing", "origin", "direction"):
        if not np.allclose(geom_a[key], geom_b[key], rtol=1e-5, atol=1e-5):
            raise ValueError(
                f"Volume geometry mismatch for {key}: volume_a={geom_a[key]} "
                f"vs volume_b={geom_b[key]}. Resample explicitly before plotting."
            )


def _prepare_intensity_arrays(
    arr_a: np.ndarray,
    arr_b: np.ndarray,
    *,
    data_type: str,
    rescale_slope: float,
    rescale_intercept: float,
    mr_normalization: str,
    mr_percentile: float,
) -> tuple[np.ndarray, np.ndarray, str]:
    dtype = data_type.lower().strip()
    if dtype == "ct_hu":
        return arr_a.astype(np.float32), arr_b.astype(np.float32), "HU"
    if dtype == "ct_uint16":
        a = arr_a.astype(np.float32) * float(rescale_slope) + float(rescale_intercept)
        b = arr_b.astype(np.float32) * float(rescale_slope) + float(rescale_intercept)
        return a, b, "HU"
    if dtype == "mr":
        a = normalize_mr(
            arr_a,
            mode=mr_normalization,
            percentile=mr_percentile,
            ignore_zeros=True,
            clip=True,
        )
        b = normalize_mr(
            arr_b,
            mode=mr_normalization,
            percentile=mr_percentile,
            ignore_zeros=True,
            clip=True,
        )
        return np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32), "normalized intensity"
    raise ValueError("data_type must be one of 'ct_hu', 'ct_uint16', or 'mr'.")


def _resolve_requested_slices(
    shape: tuple[int, ...],
    orientation: Orientation,
    *,
    slice_index: int | None,
    slice_indices: Sequence[int] | None,
    slice_fraction: float | None,
) -> list[int]:
    if slice_fraction is not None:
        if slice_index is not None or slice_indices is not None:
            raise ValueError("Pass only one of slice_index, slice_indices, or slice_fraction.")
        return [
            resolve_slice_index_for_shape(
                shape,
                orientation,
                slice_index=None,
                slice_fraction=slice_fraction,
            )
        ]
    return resolve_slice_indices(
        shape,
        orientation,
        slice_index=slice_index,
        slice_indices=list(slice_indices) if slice_indices is not None else None,
    )


def _resolve_diff_vmax(diff: np.ndarray, *, diff_vmax: float | None, percentile: float) -> float:
    if diff_vmax is not None:
        if diff_vmax <= 0:
            raise ValueError("diff_vmax must be positive when provided.")
        return float(diff_vmax)
    if not 0 < percentile <= 100:
        raise ValueError(f"diff_percentile must be in (0, 100]; got {percentile}.")
    abs_diff = np.abs(diff[np.isfinite(diff)])
    if abs_diff.size == 0:
        return 1.0
    vmax = float(np.percentile(abs_diff, percentile))
    if not np.isfinite(vmax) or vmax <= 0:
        return 1.0
    return vmax


def _imshow_anatomy(
    ax: plt.Axes,
    image_slice: np.ndarray,
    *,
    data_type: str,
    window_center: float,
    window_width: float,
) -> None:
    if data_type.startswith("ct_"):
        if window_width <= 0:
            raise ValueError("window_width must be positive.")
        low = window_center - window_width / 2.0
        high = window_center + window_width / 2.0
        display = np.clip((image_slice - low) / (high - low), 0.0, 1.0)
        ax.imshow(display, cmap="gray", vmin=0.0, vmax=1.0)
    else:
        ax.imshow(image_slice, cmap="gray", vmin=0.0, vmax=1.0)
