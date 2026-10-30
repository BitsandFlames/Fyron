"""OpenCV rendering for BOA segmentation collages."""

from __future__ import annotations

from typing import Literal

import cv2
import numpy as np

from fyron.visualization._boa_labels import SegmentationKind, color_lut_for_kind
from fyron.visualization._slices import Orientation, slice_pixel_aspect

DisplayMode = Literal["ct", "ct_overlay", "segmentation"]

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_BG_BGR = (0, 0, 0)
_TEXT_BGR = (255, 255, 255)


def window_ct_uint8(
    ct_slice: np.ndarray,
    *,
    window_center: float = 40.0,
    window_width: float = 400.0,
) -> np.ndarray:
    """Return uint8 grayscale CT slice after windowing."""
    low = window_center - window_width / 2.0
    high = window_center + window_width / 2.0
    clipped = np.clip(ct_slice.astype(np.float32), low, high)
    if high <= low:
        return np.zeros(ct_slice.shape, dtype=np.uint8)
    norm = (clipped - low) / (high - low)
    return (norm * 255.0).astype(np.uint8)


def _colorize_labels(seg_slice: np.ndarray, lut: np.ndarray) -> np.ndarray:
    labels = np.rint(seg_slice).astype(np.int32)
    labels = np.clip(labels, 0, lut.shape[0] - 1)
    return lut[labels]


def _blend_segmentation_bgr(
    base_bgr: np.ndarray,
    seg_slice: np.ndarray,
    *,
    kind: SegmentationKind,
    opacity: float,
) -> np.ndarray:
    overlay_rgb = _colorize_labels(seg_slice, color_lut_for_kind(kind))
    overlay_bgr = cv2.cvtColor(overlay_rgb, cv2.COLOR_RGB2BGR)
    mask = (np.rint(seg_slice).astype(np.int32) > 0).astype(np.float32)[..., None]
    alpha = float(np.clip(opacity, 0.0, 1.0))
    blended = (
        base_bgr.astype(np.float32) * (1.0 - alpha * mask)
        + overlay_bgr.astype(np.float32) * (alpha * mask)
    )
    return np.clip(blended, 0, 255).astype(np.uint8)


def render_panel_bgr(
    ct_slice: np.ndarray,
    seg_slice: np.ndarray,
    *,
    kind: SegmentationKind,
    display_mode: DisplayMode,
    spacing: tuple[float, float, float],
    orientation: Orientation,
    panel_width: int = 320,
    window_center: float = 40.0,
    window_width: float = 400.0,
    segmentation_opacity: float = 0.45,
) -> np.ndarray:
    """Render one panel as a BGR uint8 image with correct pixel aspect ratio."""
    aspect = slice_pixel_aspect(orientation, spacing, ct_slice.shape)
    height_f = panel_width * aspect
    panel_height = max(1, int(round(height_f)))

    if display_mode == "ct":
        gray = window_ct_uint8(ct_slice, window_center=window_center, window_width=window_width)
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif display_mode == "segmentation":
        base = np.zeros((*seg_slice.shape, 3), dtype=np.uint8)
        rgb = _blend_segmentation_bgr(base, seg_slice, kind=kind, opacity=segmentation_opacity)
    elif display_mode == "ct_overlay":
        gray = window_ct_uint8(ct_slice, window_center=window_center, window_width=window_width)
        base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        rgb = _blend_segmentation_bgr(base, seg_slice, kind=kind, opacity=segmentation_opacity)
    else:
        raise ValueError(f"Unknown display_mode: {display_mode!r}")

    return cv2.resize(rgb, (panel_width, panel_height), interpolation=cv2.INTER_AREA)


def _text_size(text: str, *, font_scale: float = 0.55, thickness: int = 1) -> tuple[int, int]:
    (width, height), _ = cv2.getTextSize(text, _FONT, font_scale, thickness)
    return width, height


def _rotated_label_width(text: str, *, font_scale: float = 0.55) -> int:
    text_w, text_h = _text_size(text, font_scale=font_scale)
    return max(32, text_w + 12)


def draw_rotated_row_label(
    text: str,
    *,
    height: int,
    width: int | None = None,
    font_scale: float = 0.55,
) -> np.ndarray:
    """Draw patient ID rotated 90° counter-clockwise on a black strip."""
    label_w = width if width is not None else _rotated_label_width(text, font_scale=font_scale)
    canvas = np.zeros((height, label_w, 3), dtype=np.uint8)
    text_w, text_h = _text_size(text, font_scale=font_scale)
    pad = 4
    text_img = np.zeros((text_h + 2 * pad, text_w + 2 * pad, 3), dtype=np.uint8)
    cv2.putText(
        text_img,
        text,
        (pad, text_h + pad),
        _FONT,
        font_scale,
        _TEXT_BGR,
        1,
        cv2.LINE_AA,
    )
    rotated = cv2.rotate(text_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    rh, rw = rotated.shape[:2]
    y0 = max(0, (height - rh) // 2)
    x0 = max(0, (label_w - rw) // 2)
    y1 = min(height, y0 + rh)
    x1 = min(label_w, x0 + rw)
    canvas[y0:y1, x0:x1] = rotated[: y1 - y0, : x1 - x0]
    return canvas


def draw_column_header_row(
    col_widths: list[int],
    headers: list[str],
    *,
    label_width: int,
    height: int = 32,
    font_scale: float = 0.55,
) -> np.ndarray:
    """Draw the top header row with column names."""
    total_w = label_width + sum(col_widths)
    row = np.zeros((height, total_w, 3), dtype=np.uint8)
    x = label_width
    for col_w, header in zip(col_widths, headers):
        text_w, text_h = _text_size(header, font_scale=font_scale)
        tx = x + max(0, (col_w - text_w) // 2)
        ty = (height + text_h) // 2
        cv2.putText(row, header, (tx, ty), _FONT, font_scale, _TEXT_BGR, 1, cv2.LINE_AA)
        x += col_w
    return row


def compose_collage(
    panels: list[list[np.ndarray]],
    *,
    column_headers: list[str],
    row_labels: list[str],
    header_height: int = 32,
    label_font_scale: float = 0.55,
) -> np.ndarray:
    """Stack panels with a header row and rotated patient IDs on the left."""
    if not panels or not panels[0]:
        raise ValueError("panels must be a non-empty 2-D list")
    if len(row_labels) != len(panels):
        raise ValueError("row_labels length must match number of panel rows")
    if len(column_headers) != len(panels[0]):
        raise ValueError("column_headers length must match number of columns")

    row_heights = [max(p.shape[0] for p in row) for row in panels]
    col_widths = [max(panels[r][c].shape[1] for r in range(len(panels))) for c in range(len(panels[0]))]
    label_width = max(
        (_rotated_label_width(lbl, font_scale=label_font_scale) for lbl in row_labels),
        default=32,
    )

    header = draw_column_header_row(
        col_widths,
        column_headers,
        label_width=label_width,
        height=header_height,
        font_scale=label_font_scale,
    )
    body_h = sum(row_heights)
    body_w = label_width + sum(col_widths)
    body = np.zeros((body_h, body_w, 3), dtype=np.uint8)

    y = 0
    for row_idx, row in enumerate(panels):
        row_h = row_heights[row_idx]
        body[y : y + row_h, 0:label_width] = draw_rotated_row_label(
            row_labels[row_idx],
            height=row_h,
            width=label_width,
            font_scale=label_font_scale,
        )
        x = label_width
        for col_idx, panel in enumerate(row):
            h, w = panel.shape[:2]
            body[y : y + h, x : x + w] = panel
            x += col_widths[col_idx]
        y += row_h

    return np.vstack([header, body])


# Backwards-compatible alias used in tests if any
compose_grid = compose_collage
