"""Tests for synthetic Fyron demo datasets."""

from __future__ import annotations

from fyron.datasets import (
    make_boa_like_folder,
    make_classification_cohort,
    make_clinical_cohort,
    make_dicom_series,
    make_nifti_pair,
    make_survival_cohort,
    prepare_nnunetv2_dataset,
    prepare_yolo_classification_dataset,
    prepare_yolo_detection_dataset,
    validate_nnunetv2_dataset,
    validate_yolo_dataset,
)
from fyron.imaging import get_dicom_series_ids, read_nifti
import pandas as pd


def test_tabular_demo_datasets_are_deterministic() -> None:
    a = make_clinical_cohort(n=5, random_state=7)
    b = make_clinical_cohort(n=5, random_state=7)
    assert a.equals(b)

    survival = make_survival_cohort(n=8)
    assert {"time", "event", "risk_group"}.issubset(survival.columns)

    X, y = make_classification_cohort(n=10)
    assert X.shape == (10, 3)
    assert len(y) == 10


def test_file_demo_datasets_are_readable(tmp_path) -> None:
    pair = make_nifti_pair(tmp_path / "nifti")
    _, array = read_nifti(pair["image"], return_array=True)
    assert array.shape == (4, 8, 8)

    make_dicom_series(tmp_path / "dicom")
    assert get_dicom_series_ids(tmp_path / "dicom")

    boa = make_boa_like_folder(tmp_path / "boa")
    assert (boa / "patient0001" / "bca-measurements.json").exists()


def test_prepare_nnunetv2_dataset_from_nifti_and_dicom(tmp_path) -> None:
    pair = make_nifti_pair(tmp_path / "case_a")
    dicom_dir = tmp_path / "case_b_dicom"
    make_dicom_series(dicom_dir, shape=(4, 8, 8))
    manifest = pd.DataFrame(
        {
            "case_id": ["case_a", "case_b"],
            "split": ["train", "test"],
            "image_path": [pair["image"], dicom_dir],
            "label_path": [pair["mask"], ""],
        }
    )

    result = prepare_nnunetv2_dataset(
        manifest,
        tmp_path / "nnunet",
        dataset_id=501,
        dataset_name="LungTumor",
    )

    root = tmp_path / "nnunet" / "Dataset501_LungTumor"
    assert (root / "imagesTr" / "case_a_0000.nii.gz").exists()
    assert (root / "labelsTr" / "case_a.nii.gz").exists()
    assert (root / "imagesTs" / "case_b_0000.nii.gz").exists()
    assert (root / "dataset.json").exists()
    assert len(result) == 2
    assert set(validate_nnunetv2_dataset(root)["status"]) == {"ok"}


def test_prepare_nnunetv2_requires_train_labels(tmp_path) -> None:
    pair = make_nifti_pair(tmp_path / "case_a")
    manifest = pd.DataFrame({"case_id": ["case_a"], "split": ["train"], "image_path": [pair["image"]], "label_path": [""]})

    import pytest

    with pytest.raises(ValueError, match="requires a label path"):
        prepare_nnunetv2_dataset(manifest, tmp_path / "nnunet", dataset_id=1, dataset_name="Demo")


def test_prepare_yolo_classification_dataset_from_png_nifti_and_dicom(tmp_path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    png = tmp_path / "image.png"
    plt.imsave(png, np.ones((8, 8)), cmap="gray")
    pair = make_nifti_pair(tmp_path / "nifti")
    dicom_dir = tmp_path / "dicom"
    make_dicom_series(dicom_dir, shape=(3, 8, 8))
    manifest = pd.DataFrame(
        {
            "image_path": [png, pair["image"], dicom_dir],
            "class": ["benign", "malignant", "benign"],
            "split": ["train", "val", "test"],
            "sample_id": ["png_case", "nifti_case", "dicom_case"],
        }
    )

    result = prepare_yolo_classification_dataset(
        manifest,
        tmp_path / "yolo_cls",
        sample_id_col="sample_id",
        nifti_slice="middle",
    )

    assert (tmp_path / "yolo_cls" / "train" / "benign" / "png_case.png").exists()
    assert (tmp_path / "yolo_cls" / "val" / "malignant" / "nifti_case_z0002.png").exists()
    assert (tmp_path / "yolo_cls" / "test" / "benign" / "dicom_case_z0001.png").exists()
    assert len(result) == 3
    assert (validate_yolo_dataset(tmp_path / "yolo_cls", task="classify")["status"] == "ok").all()


def test_prepare_yolo_classification_all_slices(tmp_path) -> None:
    pair = make_nifti_pair(tmp_path / "nifti", shape=(4, 8, 8))
    manifest = pd.DataFrame({"image_path": [pair["image"]], "class": ["tumor"], "split": ["train"], "sample_id": ["vol"]})

    result = prepare_yolo_classification_dataset(manifest, tmp_path / "yolo_cls", sample_id_col="sample_id", nifti_slice="all")

    assert len(result) == 4
    assert (tmp_path / "yolo_cls" / "train" / "tumor" / "vol_z0003.png").exists()


def test_prepare_yolo_detection_dataset_writes_labels_and_yaml(tmp_path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    image = tmp_path / "det.png"
    plt.imsave(image, np.ones((20, 20)), cmap="gray")
    manifest = pd.DataFrame(
        {
            "sample_id": ["img1", "img1", "img2"],
            "image_path": [image, image, image],
            "split": ["train", "train", "val"],
            "class": ["lesion", "device", "lesion"],
            "x_min": [2, 10, pd.NA],
            "y_min": [3, 11, pd.NA],
            "x_max": [8, 18, pd.NA],
            "y_max": [9, 19, pd.NA],
        }
    )

    result = prepare_yolo_detection_dataset(
        manifest,
        tmp_path / "yolo_det",
        sample_id_col="sample_id",
        image_width_col=None,
        image_height_col=None,
    )

    label = tmp_path / "yolo_det" / "labels" / "train" / "img1.txt"
    assert label.exists()
    lines = label.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert lines[0].split()[0] in {"0", "1"}
    assert (tmp_path / "yolo_det" / "labels" / "val" / "img2.txt").read_text(encoding="utf-8") == ""
    assert "names:" in (tmp_path / "yolo_det" / "data.yaml").read_text(encoding="utf-8")
    assert len(result) == 2
    assert (validate_yolo_dataset(tmp_path / "yolo_det", task="detect")["status"] == "ok").all()


def test_prepare_yolo_detection_rejects_invalid_boxes(tmp_path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    import pytest

    image = tmp_path / "det.png"
    plt.imsave(image, np.ones((20, 20)), cmap="gray")
    manifest = pd.DataFrame(
        {
            "image_path": [image],
            "split": ["train"],
            "class": ["lesion"],
            "x_min": [18],
            "y_min": [3],
            "x_max": [8],
            "y_max": [9],
        }
    )

    with pytest.raises(ValueError, match="Invalid xyxy box"):
        prepare_yolo_detection_dataset(manifest, tmp_path / "yolo_det")
