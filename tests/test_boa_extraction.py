from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from fyron.boa_extraction import (
    discover_boa_cases,
    extract_boa_features,
    extract_body_region_features,
    extract_cohort_body_region_features,
    extract_experimental_aortic_calcification_features,
    extract_experimental_cohort_aortic_calcification_features,
    extract_total_segmentation_features,
)


def _write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_nifti(path, array, spacing=(1.0, 1.0, 2.0)):
    sitk = pytest.importorskip("SimpleITK")
    image = sitk.GetImageFromArray(array)
    image.SetSpacing(spacing)
    sitk.WriteImage(image, str(path))


def test_extract_body_region_features_from_boa_folder(tmp_path):
    sitk = pytest.importorskip("SimpleITK")
    case = tmp_path / "patient0001"
    case.mkdir()

    _write_json(
        case / "bca-measurements.json",
        {
            "aggregated": {
                "abdominal_cavity": {
                    "measurements_no_extremities": {
                        "muscle": {"sum": 123.4},
                        "bone": {"sum": 12.0},
                        "tat": {"sum": 40.0},
                        "imat": {"sum": 10.0},
                        "vat": {"sum": 15.0},
                        "sat": {"sum": 30.0},
                    }
                },
                "thoracic_cavity": {
                    "measurements_no_extremities": {
                        "eat": {"sum": 6.0},
                        "pat": {"sum": 3.0},
                    }
                },
                "ventral_cavity": {
                    "measurements_no_extremities": {
                        "eat": {"sum": 5.0},
                        "pat": {"sum": 2.0},
                    }
                },
                "l3": {"min_slice_idx": 0, "max_slice_idx": 2},
            }
        },
    )

    segmentation = np.zeros((3, 4, 4), dtype=np.uint8)
    # Upstream BOA Tissue labels, independently specified here.
    segmentation[1, :2, :2] = 1
    segmentation[1, 2:, :1] = 5
    segmentation[1, 2:, 1:3] = 4
    segmentation[1, 2:, 3:] = 3
    image = sitk.GetImageFromArray(segmentation)
    image.SetSpacing((2.0, 2.0, 5.0))
    sitk.WriteImage(image, str(case / "tissues.nii.gz"))

    row = extract_body_region_features(case, vertebrae=["l3"], missing_value=0)

    assert row is not None
    assert row["download_id"] == "patient0001"
    assert row["abdominal_cavity_muscle_sum_ml"] == 123.4
    assert row["abdominal_cavity_bone_sum_ml"] == 12.0
    assert row["l3_sma"] == pytest.approx(0.16)
    assert row["l3_sma_cm2"] == pytest.approx(0.16)
    assert row["l3_smi"] == pytest.approx(0.16)
    assert row["l3_imat_area_cm2"] == pytest.approx(0.08)
    assert row["l3_vat_area_cm2"] == pytest.approx(0.16)
    assert row["l3_sat_area_cm2"] == pytest.approx(0.08)
    assert row["l3_imati"] == pytest.approx(0.08)
    assert row["l3_vati"] == pytest.approx(0.16)
    assert row["l3_sati"] == pytest.approx(0.08)
    assert "l3_imati_cm2_per_m2" not in row
    assert row["abdominal_cavity_sarcopenia_index_si"] == pytest.approx(123.4 / 12.0)
    assert row["abdominal_cavity_myosteatosis_fat_index_mfi"] == pytest.approx((10.0 / 40.0) * 100)
    assert row["abdominal_cavity_visceral_fat_index_vfi"] == pytest.approx(15.0 / 30.0)
    assert "abdominal_cavity_vat_sat_ratio" not in row
    assert "abdominal_cavity_eat_pat_ratio" not in row
    assert row["thoracic_cavity_eat_pat_ratio"] == pytest.approx(2.0)
    assert row["ventral_cavity_eat_pat_ratio"] == pytest.approx(2.5)

    height_normalized = extract_body_region_features(case, vertebrae=["l3"], height_m=2.0, missing_value=0)
    assert height_normalized["l3_smi"] == pytest.approx(0.16)
    assert height_normalized["l3_imati"] == pytest.approx(0.08)
    assert height_normalized["l3_vati"] == pytest.approx(0.16)
    assert height_normalized["l3_smi_cm2_per_m2"] == pytest.approx(0.04)
    assert height_normalized["l3_imati_cm2_per_m2"] == pytest.approx(0.02)
    assert height_normalized["l3_vati_cm2_per_m2"] == pytest.approx(0.04)


def test_extract_total_segmentation_features_from_boa_folder(tmp_path):
    case = tmp_path / "patient0002"
    case.mkdir()
    _write_json(
        case / "total-measurements.json",
        {
            "segmentations": {
                "total": {
                    "spleen": {"cnr": 1.234, "volume_ml": 50.0, "mean_hu": 42.345},
                    "liver": {"cnr": 2.0, "volume_ml": 100.0, "mean_hu": 60.0},
                }
            }
        },
    )

    row = extract_total_segmentation_features(case, labels={"spleen": 1, "liver": 5})

    assert row == {
        "download_id": "patient0002",
        "spleen_cnr": 1.23,
        "spleen_total": 50.0,
        "spleen_hu": 42.34,
        "liver_cnr": 2.0,
        "liver_total": 100.0,
        "liver_hu": 60.0,
        "spleen_liver_ratio": 0.5,
    }


def test_discover_and_batch_extract_boa_features(tmp_path):
    case_a = tmp_path / "patient0001"
    case_b = tmp_path / "patient0002"
    case_a.mkdir()
    case_b.mkdir()
    _write_json(
        case_a / "bca-measurements.json",
        {"aggregated": {"abdominal_cavity": {"measurements_no_extremities": {"muscle": {"sum": 1}}}}},
    )
    _write_json(
        case_b / "bca-measurements.json",
        {"aggregated": {"abdominal_cavity": {"measurements_no_extremities": {"muscle": {"sum": 2}}}}},
    )
    _write_json(
        case_a / "total-measurements.json",
        {"segmentations": {"total": {"spleen": {"cnr": 1, "volume_ml": 4, "mean_hu": 5}}}},
    )

    assert discover_boa_cases(tmp_path) == [case_a, case_b]

    body = extract_cohort_body_region_features(
        tmp_path,
        body_regions=["abdominal_cavity"],
        tissues=["muscle"],
        include_sma=False,
        show_progress=False,
    )
    assert isinstance(body, pd.DataFrame)
    assert set(body["download_id"]) == {"patient0001", "patient0002"}

    merged = extract_boa_features(
        [case_a, case_b],
        body_region_kwargs={
            "body_regions": ["abdominal_cavity"],
            "tissues": ["muscle"],
            "include_sma": False,
        },
        total_kwargs={"labels": {"spleen": 1}, "ratios": []},
        show_progress=False,
    )
    assert set(merged["download_id"]) == {"patient0001", "patient0002"}
    assert "spleen_total" in merged.columns


def test_extract_experimental_aortic_calcification_features(tmp_path):
    case = tmp_path / "patient0003"
    case.mkdir()

    ct = np.zeros((2, 3, 3), dtype=np.float32)
    ct[0, 0, 0] = 180
    ct[0, 0, 1] = 90
    ct[0, 1, 0] = 250
    ct[1, 0, 0] = 140
    ct[1, 2, 2] = 300
    _write_nifti(case / "ct.nii.gz", ct)

    aorta = np.zeros_like(ct, dtype=np.uint8)
    aorta[0, 0, 0] = 1
    aorta[0, 0, 1] = 1
    aorta[0, 1, 0] = 1
    aorta[1, 0, 0] = 1
    _write_nifti(case / "aorta.nii.gz", aorta)

    thoracic = np.zeros_like(ct, dtype=np.uint8)
    thoracic[0, :, :] = 1
    _write_nifti(case / "thoracic_cavity.nii.gz", thoracic)

    abdominal = np.zeros_like(ct, dtype=np.uint8)
    abdominal[1, :, :] = 1
    _write_nifti(case / "abdominal_cavity.nii.gz", abdominal)

    iliac = np.zeros_like(ct, dtype=np.uint8)
    iliac[1, 2, 2] = 1
    _write_nifti(case / "left_iliac_artery.nii.gz", iliac)

    row = extract_experimental_aortic_calcification_features(case)

    assert row is not None
    assert row["download_id"] == "patient0003"
    assert row["aortic_calcification_total_aorta_mask_voxel_count"] == 4
    assert row["aortic_calcification_total_aorta_calcium_voxel_count"] == 3
    assert row["aortic_calcification_total_aorta_calcified_volume_ml"] == pytest.approx(0.006)
    assert row["aortic_calcification_total_aorta_calcium_max_hu"] == pytest.approx(250)
    assert row["aortic_calcification_total_aorta_calcium_mean_hu"] == pytest.approx(190)
    assert row["aortic_calcification_total_aorta_normalized_calcified_volume"] == pytest.approx(0.75)
    assert row["aortic_calcification_thoracic_aorta_calcium_voxel_count"] == 2
    assert row["aortic_calcification_abdominal_aorta_calcium_voxel_count"] == 1
    assert row["aortic_calcification_iliac_extension_calcium_voxel_count"] == 1
    assert row["aortic_calcification_total_aortoiliac_calcium_voxel_count"] == 4


def test_extract_experimental_aortic_calcification_total_fallback_and_batch(tmp_path):
    case = tmp_path / "patient0004"
    case.mkdir()

    ct = np.zeros((1, 3, 3), dtype=np.float32)
    ct[0, 0, 0] = 131
    ct[0, 0, 1] = 80
    _write_nifti(case / "ct.nii.gz", ct)

    total = np.zeros_like(ct, dtype=np.uint8)
    total[0, 0, 0] = 52
    total[0, 0, 1] = 52
    _write_nifti(case / "total.nii.gz", total)

    frame = extract_experimental_cohort_aortic_calcification_features(
        tmp_path,
        show_progress=False,
    )

    assert list(frame["download_id"]) == ["patient0004"]
    assert frame.loc[0, "aortic_calcification_total_aorta_mask_voxel_count"] == 2
    assert frame.loc[0, "aortic_calcification_total_aorta_calcium_voxel_count"] == 1
