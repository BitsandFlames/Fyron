"""BOA segmentation collage visualization (OpenCV)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence, Union

import cv2
import numpy as np

from fyron.imaging.nifti_io import read_nifti
from fyron.visualization._boa_discovery import discover_ct_path, discover_mask_path
from fyron.visualization._boa_labels import (
    BODY_REGION_NAMES,
    SegmentationKind,
    SegmentationLayer,
    parse_segmentation_layers,
)
from fyron.visualization._body_region_crop import (
    BodyRegionSliceMode,
    extract_and_crop_slice,
    resolve_body_region_label,
    select_body_region_slices,
)
from fyron.visualization._cv_render import compose_collage, render_panel_bgr
from fyron.visualization._slices import (
    Orientation,
    extract_slice,
    orientation_label,
    resolve_slice_index_for_shape,
    resolve_slice_indices,
)

StrPath = Union[str, Path]
DisplayMode = Literal["ct", "ct_overlay", "segmentation"]
CollageResult = dict[str, Any]


def _default_patient_labels(n: int) -> list[str]:
    return [f"Patient {chr(ord('A') + i)}" for i in range(n)]


def _load_volume(path: Path) -> tuple[np.ndarray, tuple[float, float, float]]:
    image, arr = read_nifti(path, return_array=True)
    spacing = tuple(float(v) for v in image.GetSpacing())
    return arr, spacing


def create_boa_segmentation_collage(
    boa_folders: Sequence[StrPath],
    output_path: StrPath,
    *,
    orientation: Orientation = "axial",
    segmentation_layers: Sequence[SegmentationLayer | SegmentationKind | str] | None = None,
    patient_labels: Sequence[str] | None = None,
    slice_index: int | None = None,
    slice_indices: Sequence[int] | None = None,
    slice_fraction: float | None = None,
    ct_filename: str | None = None,
    window_center: float = 40.0,
    window_width: float = 400.0,
    segmentation_opacity: float = 0.45,
    overlay_alpha: float | None = None,
    panel_width: int = 320,
    row_label_prefix: str | None = None,
    crop_body_region: int | str | None = None,
    body_region_padding_mm: float = 15.0,
    body_region_slices: BodyRegionSliceMode = "best",
) -> CollageResult:
    """Create a multi-patient BOA collage with OpenCV.

    The first row lists column names (Body Regions, Tissues, Organs). Each
    patient occupies one **row** with a rotated patient ID on the left.
    Multiple patients are stacked vertically. Colors follow the
    `UMEssen Body-and-Organ-Analysis <https://github.com/UMEssen/Body-and-Organ-Analysis>`_
    definitions.

    Parameters
    ----------
    boa_folders
        One BOA output directory per patient.
    output_path
        Destination image path (``.png`` recommended).
    orientation
        ``axial``, ``sagittal``, or ``coronal``.
    segmentation_layers
        Which masks to show and how. Pass kinds (``"body_regions"``,
        ``"tissues"``, ``"total"``) or ``SegmentationLayer`` objects with
        ``display_mode`` of ``ct``, ``ct_overlay``, or ``segmentation``.
    patient_labels
        Patient ID shown rotated at the start of each row (e.g. ``Patient A``).
    slice_index
        Absolute slice index along the orientation axis.
    slice_indices
        Multiple slice rows (absolute indices). Not combined with
        ``slice_fraction``.
    slice_fraction
        Relative slice position in ``[0, 1]`` per patient (handles different
        volume depths). Ignored when ``slice_indices`` is set.
    ct_filename
        Optional explicit CT filename inside each folder.
    window_center, window_width
        CT window for grayscale / overlay backgrounds.
    segmentation_opacity
        Opacity of segmentation colors in ``ct_overlay`` and ``segmentation``
        panels, in ``[0, 1]``. Per-layer override via
        ``SegmentationLayer(opacity=...)``.
    overlay_alpha
        Deprecated alias for ``segmentation_opacity``.
    panel_width
        Panel width in pixels; height follows voxel spacing.
    crop_body_region
        BOA body-region label id or name (e.g. ``3`` or ``"Abdominal Cavity"``).
        Selects only slices containing this region and crops each panel to its
        bounding box (plus ``body_region_padding_mm``).
    body_region_padding_mm
        Padding around the cropped body region in millimetres.
    body_region_slices
        ``best`` (default): slice with largest in-plane region area;
        ``center``: middle slice of the region extent; ``all``: every slice
        that contains the region.

    Returns
    -------
    dict
        ``output_path``, ``patient_paths``, ``segmentation_layers``,
        ``slice_indices_used``, ``orientation``, ``image_shape``, and when
        cropping is enabled ``crop_body_region``.

    Examples
    --------
    >>> from fyron.visualization import create_boa_segmentation_collage
    >>> # create_boa_segmentation_collage(
    >>> #     ["/data/p1", "/data/p2"],
    >>> #     "collage.png",
    >>> #     segmentation_layers=["body_regions", "tissues", "total"],
    >>> # )
    """
    if not boa_folders:
        raise ValueError("boa_folders must contain at least one folder path.")
    if slice_indices is not None and slice_fraction is not None:
        raise ValueError("Pass only one of slice_indices or slice_fraction.")
    if crop_body_region is not None and any(
        v is not None for v in (slice_index, slice_indices, slice_fraction)
    ):
        raise ValueError(
            "crop_body_region selects slices automatically; do not pass "
            "slice_index, slice_indices, or slice_fraction."
        )
    if overlay_alpha is not None:
        segmentation_opacity = overlay_alpha

    crop_label_id: int | None = None
    if crop_body_region is not None:
        crop_label_id = resolve_body_region_label(crop_body_region)

    layers = parse_segmentation_layers(segmentation_layers)
    n_patients = len(boa_folders)
    labels = list(patient_labels) if patient_labels is not None else _default_patient_labels(n_patients)
    if len(labels) != n_patients:
        raise ValueError(
            f"patient_labels length ({len(labels)}) must match boa_folders ({n_patients})."
        )

    patients: list[dict[str, Any]] = []
    for folder in boa_folders:
        ct_path = discover_ct_path(folder, ct_filename=ct_filename)
        ct_arr, spacing = _load_volume(ct_path)
        masks: dict[str, np.ndarray] = {}
        for layer in layers:
            mask_path = discover_mask_path(folder, kind=layer.kind, segmentation_filename=layer.filename)
            mask_arr, _ = _load_volume(mask_path)
            if mask_arr.shape != ct_arr.shape:
                raise ValueError(
                    f"Shape mismatch for {layer.kind} in {folder}: "
                    f"CT {ct_arr.shape} vs mask {mask_arr.shape}"
                )
            masks[layer.kind] = mask_arr

        body_regions_arr = masks.get("body_regions")
        if body_regions_arr is None:
            body_regions_path = discover_mask_path(folder, kind="body_regions")
            body_regions_arr, _ = _load_volume(body_regions_path)

        if crop_label_id is not None:
            indices = select_body_region_slices(
                body_regions_arr,
                crop_label_id,
                orientation,
                mode=body_region_slices,
            )
        elif slice_indices is not None:
            indices = resolve_slice_indices(
                ct_arr.shape,
                orientation,
                slice_indices=list(slice_indices),
            )
        else:
            idx = resolve_slice_index_for_shape(
                ct_arr.shape,
                orientation,
                slice_index=slice_index,
                slice_fraction=slice_fraction,
            )
            indices = [idx]

        patients.append(
            {
                "folder": Path(folder).expanduser().resolve(),
                "ct": ct_arr,
                "spacing": spacing,
                "masks": masks,
                "body_regions": body_regions_arr,
                "slice_indices": indices,
            }
        )

    axis_label = orientation_label(orientation)
    max_slice_rows = max(len(p["slice_indices"]) for p in patients)
    show_slice_labels = max_slice_rows > 1 or body_region_slices == "all"

    grid: list[list[np.ndarray]] = []
    grid_row_labels: list[str] = []
    slice_indices_used: list[list[int]] = []
    column_headers = [layer.title for layer in layers]

    for slice_row in range(max_slice_rows):
        for patient, label in zip(patients, labels):
            if slice_row >= len(patient["slice_indices"]):
                continue
            idx = patient["slice_indices"][slice_row]
            row_panels: list[np.ndarray] = []
            spacing = patient["spacing"]
            body_regions = patient["body_regions"]
            for layer in layers:
                if crop_label_id is not None:
                    ct_sl = extract_and_crop_slice(
                        patient["ct"],
                        body_regions,
                        orientation=orientation,
                        slice_index=idx,
                        label_id=crop_label_id,
                        spacing=spacing,
                        padding_mm=body_region_padding_mm,
                    )
                    seg_sl = extract_and_crop_slice(
                        patient["masks"][layer.kind],
                        body_regions,
                        orientation=orientation,
                        slice_index=idx,
                        label_id=crop_label_id,
                        spacing=spacing,
                        padding_mm=body_region_padding_mm,
                    )
                else:
                    ct_sl = extract_slice(patient["ct"], orientation, idx)
                    seg_sl = extract_slice(patient["masks"][layer.kind], orientation, idx)
                layer_opacity = (
                    layer.opacity if layer.opacity is not None else segmentation_opacity
                )
                panel = render_panel_bgr(
                    ct_sl,
                    seg_sl,
                    kind=layer.kind,
                    display_mode=layer.display_mode,
                    spacing=spacing,
                    orientation=orientation,
                    panel_width=panel_width,
                    window_center=window_center,
                    window_width=window_width,
                    segmentation_opacity=layer_opacity,
                )
                row_panels.append(panel)
            grid.append(row_panels)
            slice_indices_used.append([idx])
            row_label = label
            if show_slice_labels:
                row_label = f"{label} ({row_label_prefix or axis_label}={idx})"
            grid_row_labels.append(row_label)

    canvas = compose_collage(
        grid,
        column_headers=column_headers,
        row_labels=grid_row_labels,
    )
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), canvas)

    result: CollageResult = {
        "output_path": out,
        "patient_paths": [p["folder"] for p in patients],
        "segmentation_layers": layers,
        "slice_indices_used": slice_indices_used,
        "orientation": orientation,
        "image_shape": canvas.shape,
    }
    if crop_label_id is not None:
        result["crop_body_region"] = {
            "label_id": crop_label_id,
            "name": BODY_REGION_NAMES[crop_label_id],
            "slice_mode": body_region_slices,
            "padding_mm": body_region_padding_mm,
        }
    return result
