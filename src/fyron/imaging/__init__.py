"""Medical imaging I/O and normalization (DICOM, NIfTI, CT/MR scaling)."""

from __future__ import annotations

from fyron.imaging.dicom_io import get_dicom_series_ids, read_dicom_header, read_dicom_series
from fyron.imaging.nifti_io import read_nifti, write_nifti
from fyron.imaging.normalize import normalize_ct, normalize_mr
from fyron.imaging.qc import (
    check_image_mask_alignment,
    summarize_dicom_series_geometry,
    summarize_intensity_range,
    summarize_mask_volume,
    summarize_nifti_geometry,
)
from fyron.imaging.segmentation import (
    dice_score,
    hausdorff_distance,
    label_overlap_table,
    segmentation_metric_table,
    surface_dice,
    volume_difference,
)

__all__ = [
    "check_image_mask_alignment",
    "dice_score",
    "get_dicom_series_ids",
    "hausdorff_distance",
    "label_overlap_table",
    "normalize_ct",
    "normalize_mr",
    "read_dicom_header",
    "read_dicom_series",
    "read_nifti",
    "segmentation_metric_table",
    "surface_dice",
    "summarize_dicom_series_geometry",
    "summarize_intensity_range",
    "summarize_mask_volume",
    "summarize_nifti_geometry",
    "volume_difference",
    "write_nifti",
]
