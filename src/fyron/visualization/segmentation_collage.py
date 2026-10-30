"""Generic OpenCV segmentation collages for CT/NIfTI review."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence, Union

import cv2
import numpy as np
import pandas as pd
import SimpleITK as sitk

from fyron.imaging._helpers import is_sitk_image
from fyron.imaging.nifti_io import read_nifti
from fyron.visualization._cv_render import window_ct_uint8
from fyron.visualization._slices import (
    Orientation,
    extract_slice,
    orientation_axis,
    orientation_label,
    slice_pixel_aspect,
)

StrPath = Union[str, Path]
VolumeInput = Union[StrPath, np.ndarray, sitk.Image]
SliceStrategy = Literal["segmentation_extent", "full_extent"]
CollageResult = dict[str, Any]

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_DEFAULT_LABEL_COLORS_RGB: tuple[tuple[int, int, int], ...] = (
    (255, 107, 107),
    (78, 205, 196),
    (255, 209, 102),
    (17, 138, 178),
    (157, 78, 221),
    (6, 214, 160),
)


def _load_volume(
    volume: VolumeInput,
    *,
    default_spacing: tuple[float, float, float],
) -> tuple[np.ndarray, tuple[float, float, float]]:
    if isinstance(volume, (str, Path)):
        image, arr = read_nifti(volume, return_array=True)
        spacing = tuple(float(v) for v in image.GetSpacing())
        return np.asarray(arr), spacing
    if is_sitk_image(volume):
        spacing = tuple(float(v) for v in volume.GetSpacing())
        return sitk.GetArrayFromImage(volume), spacing
    arr = np.asarray(volume)
    return arr, default_spacing


def _normalize_labels(labels: Sequence[int] | int | None) -> tuple[int, ...] | None:
    if labels is None:
        return None
    if isinstance(labels, (int, np.integer)):
        return (int(labels),)
    out = tuple(int(v) for v in labels)
    if not out:
        raise ValueError("labels must contain at least one label when provided.")
    return out


def _label_colors_bgr(
    labels: tuple[int, ...] | None,
    label_colors: Mapping[int, tuple[int, int, int]] | Sequence[tuple[int, int, int]] | None,
) -> dict[int, tuple[int, int, int]]:
    if labels is None:
        labels = tuple()
    if isinstance(label_colors, Mapping):
        colors_rgb = {int(k): tuple(int(c) for c in v) for k, v in label_colors.items()}
    elif label_colors is not None:
        colors_rgb = {
            label: tuple(int(c) for c in label_colors[i % len(label_colors)])
            for i, label in enumerate(labels)
        }
    else:
        colors_rgb = {
            label: _DEFAULT_LABEL_COLORS_RGB[i % len(_DEFAULT_LABEL_COLORS_RGB)]
            for i, label in enumerate(labels)
        }
    return {label: (rgb[2], rgb[1], rgb[0]) for label, rgb in colors_rgb.items()}


def _select_label_mask(seg: np.ndarray, labels: tuple[int, ...] | None) -> np.ndarray:
    rounded = np.rint(seg).astype(np.int32)
    if labels is None:
        return rounded != 0
    return np.isin(rounded, labels)


def _indices_with_mask(mask: np.ndarray, orientation: Orientation) -> list[int]:
    axis = orientation_axis(orientation)
    reduce_axes = tuple(i for i in range(mask.ndim) if i != axis)
    return np.flatnonzero(np.any(mask, axis=reduce_axes)).astype(int).tolist()


def _sample_slice_indices(
    seg: np.ndarray,
    *,
    labels: tuple[int, ...] | None,
    orientation: Orientation,
    slice_strategy: SliceStrategy,
    slice_indices: Sequence[int] | None,
    every_n_slices: int | None,
    max_slices: int | None,
) -> list[int]:
    axis = orientation_axis(orientation)
    max_idx = seg.shape[axis] - 1
    if slice_indices is not None:
        indices = [int(v) for v in slice_indices]
    elif slice_strategy == "segmentation_extent":
        present = _indices_with_mask(_select_label_mask(seg, labels), orientation)
        if not present:
            label_text = "non-zero labels" if labels is None else ", ".join(str(v) for v in labels)
            raise ValueError(f"No segmentation voxels found for labels: {label_text}.")
        if every_n_slices is None:
            indices = present
        else:
            if every_n_slices <= 0:
                raise ValueError("every_n_slices must be a positive integer.")
            indices = list(range(present[0], present[-1] + 1, every_n_slices))
            if indices[-1] != present[-1]:
                indices.append(present[-1])
    elif slice_strategy == "full_extent":
        step = int(every_n_slices or 1)
        if step <= 0:
            raise ValueError("every_n_slices must be a positive integer.")
        indices = list(range(0, max_idx + 1, step))
        if indices[-1] != max_idx:
            indices.append(max_idx)
    else:
        raise ValueError("slice_strategy must be 'segmentation_extent' or 'full_extent'.")

    for idx in indices:
        if idx < 0 or idx > max_idx:
            raise ValueError(
                f"Slice index {idx} out of range for orientation {orientation!r} "
                f"(valid 0..{max_idx}, shape={seg.shape})."
            )
    if max_slices is not None and len(indices) > max_slices:
        if max_slices <= 0:
            raise ValueError("max_slices must be a positive integer.")
        positions = np.linspace(0, len(indices) - 1, max_slices, dtype=int)
        indices = [indices[int(pos)] for pos in positions]
    return list(dict.fromkeys(indices))


def _overlay_labels(
    base_bgr: np.ndarray,
    seg_slice: np.ndarray,
    *,
    labels: tuple[int, ...] | None,
    colors_bgr: dict[int, tuple[int, int, int]],
    opacity: float,
) -> np.ndarray:
    seg_int = np.rint(seg_slice).astype(np.int32)
    active_labels = labels if labels is not None else tuple(int(v) for v in np.unique(seg_int) if v != 0)
    overlay = base_bgr.copy()
    alpha = float(np.clip(opacity, 0.0, 1.0))
    for label in active_labels:
        mask = seg_int == int(label)
        if not np.any(mask):
            continue
        color = colors_bgr.get(int(label), (0, 0, 255))
        color_img = np.full_like(base_bgr, color, dtype=np.uint8)
        blended = cv2.addWeighted(base_bgr, 1.0 - alpha, color_img, alpha, 0)
        overlay[mask] = blended[mask]
    return overlay


def _put_label_bar(panel: np.ndarray, text: str, *, height: int = 24) -> np.ndarray:
    bar = np.zeros((height, panel.shape[1], 3), dtype=np.uint8)
    (tw, th), _ = cv2.getTextSize(text, _FONT, 0.48, 1)
    x = max(4, (panel.shape[1] - tw) // 2)
    y = (height + th) // 2
    cv2.putText(bar, text, (x, y), _FONT, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
    return np.vstack([bar, panel])


def _render_overlay_panel(
    image_slice: np.ndarray,
    seg_slice: np.ndarray,
    *,
    labels: tuple[int, ...] | None,
    colors_bgr: dict[int, tuple[int, int, int]],
    spacing: tuple[float, float, float],
    orientation: Orientation,
    panel_width: int,
    window_center: float,
    window_width: float,
    segmentation_opacity: float,
) -> np.ndarray:
    gray = window_ct_uint8(
        image_slice,
        window_center=window_center,
        window_width=window_width,
    )
    base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    overlay = _overlay_labels(
        base,
        seg_slice,
        labels=labels,
        colors_bgr=colors_bgr,
        opacity=segmentation_opacity,
    )
    aspect = slice_pixel_aspect(orientation, spacing, image_slice.shape)
    panel_height = max(1, int(round(panel_width * aspect)))
    return cv2.resize(overlay, (panel_width, panel_height), interpolation=cv2.INTER_AREA)


def _compose_grid(panels: list[np.ndarray], *, n_cols: int, title: str | None) -> np.ndarray:
    if not panels:
        raise ValueError("At least one panel is required.")
    n_cols = max(1, int(n_cols))
    n_rows = int(math.ceil(len(panels) / n_cols))
    h = max(p.shape[0] for p in panels)
    w = max(p.shape[1] for p in panels)
    canvas = np.zeros((n_rows * h, n_cols * w, 3), dtype=np.uint8)
    for i, panel in enumerate(panels):
        row, col = divmod(i, n_cols)
        y = row * h
        x = col * w
        canvas[y : y + panel.shape[0], x : x + panel.shape[1]] = panel
    if title:
        header_h = 36
        header = np.zeros((header_h, canvas.shape[1], 3), dtype=np.uint8)
        (tw, th), _ = cv2.getTextSize(title, _FONT, 0.7, 1)
        x = max(8, (header.shape[1] - tw) // 2)
        cv2.putText(header, title, (x, (header_h + th) // 2), _FONT, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        canvas = np.vstack([header, canvas])
    return canvas


def create_segmentation_collage(
    image: VolumeInput,
    segmentation: VolumeInput,
    output_path: StrPath,
    *,
    labels: Sequence[int] | int | None = None,
    orientation: Orientation = "axial",
    slice_strategy: SliceStrategy = "segmentation_extent",
    slice_indices: Sequence[int] | None = None,
    every_n_slices: int | None = None,
    max_slices: int | None = None,
    n_cols: int | None = None,
    window_center: float = 40.0,
    window_width: float = 400.0,
    segmentation_opacity: float = 0.40,
    label_colors: Mapping[int, tuple[int, int, int]] | Sequence[tuple[int, int, int]] | None = None,
    title: str | None = None,
    show_slice_labels: bool = True,
    panel_width: int = 256,
    spacing: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> CollageResult:
    """Create a generic OpenCV CT/segmentation overlay collage.

    Parameters
    ----------
    image
        Image volume as NIfTI path, ``SimpleITK.Image``, or 3-D NumPy array in
        ``(z, y, x)`` order.
    segmentation
        Segmentation volume as NIfTI path, ``SimpleITK.Image``, or matching
        3-D NumPy array in ``(z, y, x)`` order.
    output_path
        Destination image path, usually ``.png``.
    labels
        Label ids to display. ``None`` displays all non-zero labels.
    orientation
        ``axial``, ``sagittal``, or ``coronal``.
    slice_strategy
        ``segmentation_extent`` selects slices containing the requested labels;
        ``full_extent`` samples the complete volume.
    slice_indices
        Explicit absolute slice indices along the selected orientation axis.
    every_n_slices
        Step size over the selected extent. The last selected extent slice is
        included for ``segmentation_extent``.
    max_slices
        Optional maximum number of selected slices after slice sampling.
    n_cols
        Number of columns in the output grid. When omitted, a near-square grid
        is chosen automatically.
    window_center
        CT window center used for grayscale background rendering.
    window_width
        CT window width used for grayscale background rendering.
    segmentation_opacity
        Opacity of the colored segmentation overlay in ``[0, 1]``.
    label_colors
        RGB colors either as ``{label: (r, g, b)}`` mapping or sequence matched
        to ``labels`` order.
    title
        Optional title bar shown above the collage.
    show_slice_labels
        If True, add a small label bar with the orientation axis and slice index
        to each panel.
    panel_width
        Width of each rendered slice panel in pixels.
    spacing
        Fallback voxel spacing ``(sx, sy, sz)`` for NumPy array inputs.

    Returns
    -------
    dict
        Metadata including ``output_path``, ``slice_indices_used``, ``labels``,
        ``image_shape``, and ``orientation``.
    """
    labels_tuple = _normalize_labels(labels)
    img, img_spacing = _load_volume(image, default_spacing=spacing)
    seg, _ = _load_volume(segmentation, default_spacing=img_spacing)
    if img.ndim != 3 or seg.ndim != 3:
        raise ValueError("image and segmentation must be 3-D volumes.")
    if img.shape != seg.shape:
        raise ValueError(f"Shape mismatch: image {img.shape} vs segmentation {seg.shape}.")
    if panel_width <= 0:
        raise ValueError("panel_width must be a positive integer.")

    indices = _sample_slice_indices(
        seg,
        labels=labels_tuple,
        orientation=orientation,
        slice_strategy=slice_strategy,
        slice_indices=slice_indices,
        every_n_slices=every_n_slices,
        max_slices=max_slices,
    )
    colors_bgr = _label_colors_bgr(labels_tuple, label_colors)
    axis_label = orientation_label(orientation)
    panels: list[np.ndarray] = []
    for idx in indices:
        image_slice = extract_slice(img, orientation, idx)
        seg_slice = extract_slice(seg, orientation, idx)
        panel = _render_overlay_panel(
            image_slice,
            seg_slice,
            labels=labels_tuple,
            colors_bgr=colors_bgr,
            spacing=img_spacing,
            orientation=orientation,
            panel_width=panel_width,
            window_center=window_center,
            window_width=window_width,
            segmentation_opacity=segmentation_opacity,
        )
        if show_slice_labels:
            panel = _put_label_bar(panel, f"{axis_label}={idx}")
        panels.append(panel)

    columns = int(n_cols) if n_cols is not None else int(math.ceil(math.sqrt(len(panels))))
    canvas = _compose_grid(panels, n_cols=columns, title=title)
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(out), canvas)
    if not ok:
        raise OSError(f"Failed to write segmentation collage: {out}")

    return {
        "output_path": out,
        "slice_indices_used": indices,
        "labels": labels_tuple,
        "orientation": orientation,
        "image_shape": canvas.shape,
        "n_panels": len(panels),
        "n_cols": columns,
    }


def create_segmentation_collages_from_cases(
    input_root: StrPath,
    output_dir: StrPath,
    *,
    case_glob: str = "case-*",
    image_relpath: StrPath = "A/image.nii.gz",
    segmentation_relpath: StrPath = "A/segmentation.nii.gz",
    output_suffix: str = ".png",
    labels: Sequence[int] | int | None = None,
    orientation: Orientation = "axial",
    slice_strategy: SliceStrategy = "segmentation_extent",
    every_n_slices: int | None = None,
    max_slices: int | None = None,
    n_cols: int | None = None,
    window_center: float = 40.0,
    window_width: float = 400.0,
    segmentation_opacity: float = 0.40,
    label_colors: Mapping[int, tuple[int, int, int]] | Sequence[tuple[int, int, int]] | None = None,
    panel_width: int = 256,
    continue_on_error: bool = True,
) -> pd.DataFrame:
    """Create one segmentation collage per case folder and return a summary table.

    Parameters
    ----------
    input_root
        Folder containing case directories.
    output_dir
        Destination folder for generated collage PNGs.
    case_glob
        Glob pattern used to discover case directories below ``input_root``.
    image_relpath
        Image path relative to each case directory.
    segmentation_relpath
        Segmentation path relative to each case directory.
    output_suffix
        Suffix for output files; filenames use the case directory name.
    labels
        Label id or ids to display. ``None`` displays all non-zero labels.
    orientation
        ``axial``, ``sagittal``, or ``coronal``.
    slice_strategy
        ``segmentation_extent`` selects slices containing the requested labels;
        ``full_extent`` samples the complete volume.
    every_n_slices
        Step size over the selected extent.
    max_slices
        Optional maximum number of selected slices per case.
    n_cols
        Number of columns in each output grid.
    window_center
        CT window center used for grayscale background rendering.
    window_width
        CT window width used for grayscale background rendering.
    segmentation_opacity
        Opacity of the colored segmentation overlay in ``[0, 1]``.
    label_colors
        RGB colors either as mapping by label id or sequence matched to labels.
    panel_width
        Width of each rendered slice panel in pixels.
    continue_on_error
        If True, failed cases are recorded with ``status="error"``; otherwise
        the first failure is raised.

    Returns
    -------
    pandas.DataFrame
        One row per case with paths, status, message, selected slices, and
        slice count.
    """
    root = Path(input_root).expanduser().resolve()
    out_dir = Path(output_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Input root does not exist: {root}")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for case_dir in sorted(p for p in root.glob(case_glob) if p.is_dir()):
        case_id = case_dir.name
        image_path = case_dir / image_relpath
        segmentation_path = case_dir / segmentation_relpath
        output_path = out_dir / f"{case_id}{output_suffix}"
        row: dict[str, Any] = {
            "case_id": case_id,
            "image_path": image_path,
            "segmentation_path": segmentation_path,
            "output_path": output_path,
            "status": "ok",
            "message": "",
            "slice_indices_used": None,
            "n_slices": 0,
        }
        try:
            result = create_segmentation_collage(
                image_path,
                segmentation_path,
                output_path,
                labels=labels,
                orientation=orientation,
                slice_strategy=slice_strategy,
                every_n_slices=every_n_slices,
                max_slices=max_slices,
                n_cols=n_cols,
                window_center=window_center,
                window_width=window_width,
                segmentation_opacity=segmentation_opacity,
                label_colors=label_colors,
                title=case_id,
                panel_width=panel_width,
            )
            row["slice_indices_used"] = result["slice_indices_used"]
            row["n_slices"] = result["n_panels"]
        except Exception as exc:  # noqa: BLE001 - batch jobs should report per-case failures.
            if not continue_on_error:
                raise
            row["status"] = "error"
            row["message"] = str(exc)
        rows.append(row)
    return pd.DataFrame(rows)
