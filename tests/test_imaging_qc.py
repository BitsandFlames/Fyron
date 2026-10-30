"""Tests for imaging QC helpers."""

from __future__ import annotations

import numpy as np
import SimpleITK as sitk

from fyron.datasets import make_dicom_series, make_nifti_pair
from fyron.imaging.qc import (
    check_image_mask_alignment,
    summarize_dicom_series_geometry,
    summarize_intensity_range,
    summarize_mask_volume,
    summarize_nifti_geometry,
)


def test_nifti_geometry_alignment_mask_volume_and_intensity(tmp_path) -> None:
    paths = make_nifti_pair(tmp_path)

    geom = summarize_nifti_geometry(paths["image"])
    assert geom.loc[0, "shape_zyx"] == (4, 8, 8)

    alignment = check_image_mask_alignment(paths["image"], paths["mask"])
    assert alignment["aligned"] is True

    mask_volume = summarize_mask_volume(paths["mask"])
    assert int(mask_volume.loc[0, "voxel_count"]) > 0

    intensity = summarize_intensity_range(paths["image"], mask=paths["mask"])
    assert intensity["n_voxels"] > 0
    assert intensity["max"] >= intensity["min"]

    shifted = sitk.ReadImage(str(paths["mask"]))
    shifted.SetOrigin((99.0, 0.0, 0.0))
    assert check_image_mask_alignment(sitk.ReadImage(str(paths["image"])), shifted)["aligned"] is False


def test_dicom_series_geometry(tmp_path) -> None:
    make_dicom_series(tmp_path)
    table = summarize_dicom_series_geometry(tmp_path)
    assert len(table) == 1
    assert int(table.loc[0, "number_of_files"]) == 3
    assert int(table.loc[0, "rows"]) == 8


def test_mask_volume_from_array() -> None:
    mask = np.array([[[0, 1], [2, 2]]], dtype=np.uint8)
    table = summarize_mask_volume(mask, spacing=(1.0, 1.0, 5.0))
    assert set(table["label"]) == {1, 2}
    assert float(table.loc[table["label"] == 2, "volume_ml"].iloc[0]) == 0.01
