"""Tests for Curate preview preparation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from fyron.cli import main
from fyron.datasets import make_dicom_series
from fyron.imaging.nifti_io import write_nifti
from fyron.visualization import prepare_curate_image_previews


def test_prepare_curate_previews_from_3d_volume(tmp_path: Path) -> None:
    source = tmp_path / "source" / "case_a"
    source.mkdir(parents=True)
    volume = np.arange(7 * 9 * 11, dtype=np.float32).reshape(7, 9, 11)
    write_nifti(volume, source / "ct.nii.gz")

    result = prepare_curate_image_previews(tmp_path / "source", tmp_path / "curate", panel_width=96)

    assert result["sources_found"] == 1
    assert result["images_written"] == 3
    previews = sorted((tmp_path / "curate" / "case_a").glob("*.png"))
    assert [path.name for path in previews] == [
        "ct.nii.gz_axial.png",
        "ct.nii.gz_coronal.png",
        "ct.nii.gz_sagittal.png",
    ]
    for preview in previews:
        image = cv2.imread(str(preview), cv2.IMREAD_GRAYSCALE)
        assert image is not None
        assert image.shape[1] == 96

    manifest = pd.read_csv(tmp_path / "curate" / "manifest.csv")
    assert set(manifest["orientation"]) == {"axial", "coronal", "sagittal"}
    assert set(manifest["status"]) == {"written"}


def test_prepare_curate_previews_from_2d_image(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    image = np.arange(12 * 16, dtype=np.uint8).reshape(12, 16)
    assert cv2.imwrite(str(source / "topogram.png"), image)

    result = prepare_curate_image_previews(source, tmp_path / "curate", panel_width=80)

    assert result["sources_found"] == 1
    assert result["images_written"] == 1
    preview = tmp_path / "curate" / "topogram.png_slice.png"
    assert preview.exists()
    manifest = pd.read_csv(tmp_path / "curate" / "manifest.csv")
    assert manifest["orientation"].tolist() == ["slice"]


def test_cli_dataset_curate_previews(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    volume = np.linspace(-100, 300, num=5 * 8 * 10, dtype=np.float32).reshape(5, 8, 10)
    write_nifti(volume, source / "mri.nii.gz")
    out = tmp_path / "curate"
    manifest = tmp_path / "manifest.csv"

    assert main([
        "dataset-curate-previews",
        "--input-dir",
        str(source),
        "--output-dir",
        str(out),
        "--panel-width",
        "72",
        "--manifest-csv",
        str(manifest),
    ]) == 0

    assert manifest.exists()
    table = pd.read_csv(manifest)
    assert table.shape[0] == 3
    assert all(Path(path).exists() for path in table["output_path"])


def test_prepare_curate_previews_from_nested_dicom_series(tmp_path: Path) -> None:
    dicom_dir = tmp_path / "source" / "patient_001" / "ct"
    make_dicom_series(dicom_dir, shape=(5, 8, 10))

    result = prepare_curate_image_previews(tmp_path / "source", tmp_path / "curate", panel_width=64)

    assert result["sources_found"] >= 1
    assert result["images_written"] >= 3
    table = pd.read_csv(tmp_path / "curate" / "manifest.csv")
    assert "dicom_series" in set(table["source_kind"])
    assert {"axial", "coronal", "sagittal"}.issubset(set(table["orientation"]))
