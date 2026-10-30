"""Tests for fyron.visualization BOA collages."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from fyron.imaging.nifti_io import write_nifti
from fyron.visualization import (
    SegmentationLayer,
    create_boa_segmentation_collage,
    create_segmentation_collage,
    create_segmentation_collages_from_cases,
)
from fyron.visualization._boa_discovery import discover_boa_volumes, discover_ct_path
from fyron.visualization._boa_labels import color_lut_for_kind, label_name
from fyron.visualization._body_region_crop import (
    resolve_body_region_label,
    select_body_region_slices,
    slices_with_body_region,
)
from fyron.visualization._slices import extract_slice, slice_pixel_aspect


def _write_boa_folder(
    folder: Path,
    *,
    ct_name: str = "study_Axial.nii.gz",
    shape: tuple[int, int, int] = (8, 16, 16),
    spacing: tuple[float, float, float] = (0.8, 0.8, 1.5),
) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    z, y, x = shape
    ct = np.linspace(-200, 400, num=z * y * x, dtype=np.float32).reshape(z, y, x)
    seg_regions = np.zeros(shape, dtype=np.int16)
    seg_regions[z // 2, y // 4 : 3 * y // 4, x // 4 : 3 * x // 4] = 1
    seg_regions[z // 2, y // 2, x // 2] = 2
    seg_regions[z // 2 - 1 : z // 2 + 2, y // 3 : 2 * y // 3, x // 3 : 2 * x // 3] = 3
    tissues = np.zeros(shape, dtype=np.int16)
    tissues[z // 2, y // 3 : 2 * y // 3, x // 3 : 2 * x // 3] = 3
    total = np.zeros(shape, dtype=np.int16)
    total[z // 2, y // 2 - 1 : y // 2 + 2, x // 2 - 1 : x // 2 + 2] = 5
    import SimpleITK as sitk

    def _write(arr: np.ndarray, name: str) -> None:
        img = sitk.GetImageFromArray(arr)
        img.SetSpacing(spacing)
        write_nifti(img, folder / name)

    _write(ct, ct_name)
    _write(seg_regions, "body-regions.nii.gz")
    _write(tissues, "tissues.nii.gz")
    _write(total, "total.nii.gz")
    _write(np.zeros(shape, dtype=np.int16), "body-parts.nii.gz")


def test_discover_ct_path(tmp_path: Path) -> None:
    folder = tmp_path / "case1"
    _write_boa_folder(folder)
    assert discover_ct_path(folder).name == "study_Axial.nii.gz"
    paths = discover_boa_volumes(folder)
    assert paths.segmentation_path.name == "body-regions.nii.gz"


def test_boa_label_lut_stable() -> None:
    assert label_name("body_regions", 2) == "Muscle"
    lut = color_lut_for_kind("body_regions")
    assert tuple(lut[2]) == (238, 193, 112)


def test_coronal_slice_vertical_flip() -> None:
    vol = np.arange(3 * 4 * 5, dtype=np.int16).reshape(3, 4, 5)
    sl = extract_slice(vol, "coronal", 2)
    assert np.array_equal(sl, np.flipud(vol[:, 2, :]))


def test_slice_pixel_aspect() -> None:
    spacing = (0.7, 0.7, 2.0)
    assert slice_pixel_aspect("axial", spacing, (16, 16)) == pytest.approx(1.0)
    assert slice_pixel_aspect("coronal", spacing, (8, 16)) == pytest.approx((8 * 2.0) / (16 * 0.7))
    assert slice_pixel_aspect("sagittal", spacing, (8, 16)) == pytest.approx((8 * 2.0) / (16 * 0.7))


def test_shape_mismatch_raises(tmp_path: Path) -> None:
    folder = tmp_path / "case_bad"
    _write_boa_folder(folder)
    bad = np.zeros((4, 8, 8), dtype=np.int16)
    write_nifti(bad, folder / "body-regions.nii.gz")
    with pytest.raises(ValueError, match="Shape mismatch"):
        create_boa_segmentation_collage([folder], tmp_path / "out.png", slice_index=2)


@pytest.mark.parametrize("orientation", ["axial", "sagittal", "coronal"])
def test_create_collage_orientations(tmp_path: Path, orientation: str) -> None:
    folder = tmp_path / "case1"
    _write_boa_folder(folder)
    out = tmp_path / f"collage_{orientation}.png"
    result = create_boa_segmentation_collage(
        [folder],
        out,
        orientation=orientation,  # type: ignore[arg-type]
        segmentation_layers=["body_regions"],
        slice_index=3,
    )
    assert out.is_file() and out.stat().st_size > 0
    img = cv2.imread(str(out))
    assert img is not None
    assert result["image_shape"][0] > 0


def test_default_three_segmentation_layers(tmp_path: Path) -> None:
    folder = tmp_path / "case1"
    _write_boa_folder(folder)
    out = tmp_path / "layers.png"
    result = create_boa_segmentation_collage([folder], out, slice_index=4)
    img = cv2.imread(str(out))
    assert img is not None
    assert len(result["segmentation_layers"]) == 3


def test_multi_patient_custom_layers(tmp_path: Path) -> None:
    f1 = tmp_path / "p1"
    f2 = tmp_path / "p2"
    _write_boa_folder(f1)
    _write_boa_folder(f2, shape=(10, 16, 16))
    out = tmp_path / "multi.png"
    result = create_boa_segmentation_collage(
        [f1, f2],
        out,
        patient_labels=["Patient A", "Patient B"],
        segmentation_layers=[
            SegmentationLayer("body_regions", display_mode="segmentation"),
            SegmentationLayer("tissues", display_mode="ct_overlay"),
        ],
        slice_fraction=0.5,
    )
    assert out.exists()
    assert len(result["segmentation_layers"]) == 2


def test_resolve_body_region_label() -> None:
    assert resolve_body_region_label("Abdominal Cavity") == 3
    assert resolve_body_region_label(3) == 3


def test_body_region_slice_selection() -> None:
    vol = np.zeros((6, 8, 8), dtype=np.int16)
    vol[2, 2:6, 2:6] = 3
    vol[3, 2:6, 2:6] = 3
    vol[4, 2:7, 2:7] = 3
    assert slices_with_body_region(vol, 3, "axial") == [2, 3, 4]
    assert select_body_region_slices(vol, 3, "axial", mode="best") == [4]
    assert select_body_region_slices(vol, 3, "axial", mode="center") == [3]
    assert select_body_region_slices(vol, 3, "axial", mode="all") == [2, 3, 4]


def test_crop_body_region_collage(tmp_path: Path) -> None:
    folder = tmp_path / "case1"
    _write_boa_folder(folder)
    out = tmp_path / "crop.png"
    result = create_boa_segmentation_collage(
        [folder],
        out,
        orientation="axial",
        segmentation_layers=["body_regions"],
        crop_body_region="Abdominal Cavity",
        body_region_padding_mm=0.0,
    )
    assert out.exists()
    assert result["crop_body_region"]["label_id"] == 3
    img = cv2.imread(str(out))
    assert img is not None
    assert img.shape[0] > 0


def test_slice_indices_rows(tmp_path: Path) -> None:
    folder = tmp_path / "case1"
    _write_boa_folder(folder)
    out = tmp_path / "rows.png"
    result = create_boa_segmentation_collage(
        [folder],
        out,
        segmentation_layers=["body_regions"],
        slice_indices=[2, 4, 6],
    )
    assert result["slice_indices_used"] == [[2], [4], [6]]


def _write_generic_case(
    folder: Path,
    *,
    shape: tuple[int, int, int] = (10, 16, 16),
    labels: tuple[int, ...] = (11, 12),
    write_segmentation: bool = True,
) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    z, y, x = shape
    image = np.linspace(-300, 500, num=z * y * x, dtype=np.float32).reshape(shape)
    segmentation = np.zeros(shape, dtype=np.int16)
    if labels:
        segmentation[2:6, 4:10, 4:10] = labels[0]
    if len(labels) > 1:
        segmentation[7, 6:12, 6:12] = labels[1]

    import SimpleITK as sitk

    def _write(arr: np.ndarray, path: Path) -> None:
        img = sitk.GetImageFromArray(arr)
        img.SetSpacing((0.8, 0.8, 1.5))
        write_nifti(img, path)

    _write(image, folder / "image.nii.gz")
    if write_segmentation:
        _write(segmentation, folder / "segmentation.nii.gz")


def test_generic_segmentation_collage_extent_every_n(tmp_path: Path) -> None:
    case = tmp_path / "case-0001" / "A"
    _write_generic_case(case)
    out = tmp_path / "case-0001.png"

    result = create_segmentation_collage(
        case / "image.nii.gz",
        case / "segmentation.nii.gz",
        out,
        labels=(11, 12),
        every_n_slices=2,
        n_cols=2,
        title="case-0001",
    )

    assert out.is_file() and out.stat().st_size > 0
    assert result["slice_indices_used"] == [2, 4, 6, 7]
    assert result["n_panels"] == 4
    img = cv2.imread(str(out))
    assert img is not None and img.shape[0] > 0 and img.shape[1] > 0


def test_generic_segmentation_collage_auto_grid_from_arrays(tmp_path: Path) -> None:
    image = np.zeros((8, 12, 12), dtype=np.float32)
    segmentation = np.zeros_like(image, dtype=np.int16)
    segmentation[1:7, 3:9, 3:9] = 11
    out = tmp_path / "array_collage.png"

    result = create_segmentation_collage(
        image,
        segmentation,
        out,
        labels=11,
        every_n_slices=3,
        panel_width=64,
    )

    assert out.exists()
    assert result["n_cols"] == 2
    assert result["slice_indices_used"] == [1, 4, 6]


def test_generic_segmentation_collage_missing_label_raises(tmp_path: Path) -> None:
    image = np.zeros((4, 8, 8), dtype=np.float32)
    segmentation = np.zeros_like(image, dtype=np.int16)
    with pytest.raises(ValueError, match="No segmentation voxels"):
        create_segmentation_collage(image, segmentation, tmp_path / "missing.png", labels=(11, 12))


def test_generic_segmentation_collage_shape_mismatch_raises(tmp_path: Path) -> None:
    image = np.zeros((4, 8, 8), dtype=np.float32)
    segmentation = np.zeros((5, 8, 8), dtype=np.int16)
    with pytest.raises(ValueError, match="Shape mismatch"):
        create_segmentation_collage(image, segmentation, tmp_path / "bad.png", labels=11)


def test_batch_segmentation_collages_case_layout(tmp_path: Path) -> None:
    root = tmp_path / "nifti_seg"
    _write_generic_case(root / "case-0001" / "A")
    _write_generic_case(root / "case-0002" / "A", write_segmentation=False)
    out_dir = tmp_path / "collages"

    summary = create_segmentation_collages_from_cases(
        root,
        out_dir,
        labels=(11, 12),
        every_n_slices=3,
        n_cols=3,
    )

    assert list(summary["case_id"]) == ["case-0001", "case-0002"]
    ok = summary.loc[summary["case_id"] == "case-0001"].iloc[0]
    bad = summary.loc[summary["case_id"] == "case-0002"].iloc[0]
    assert ok["status"] == "ok"
    assert (out_dir / "case-0001.png").is_file()
    assert bad["status"] == "error"
    assert "does not exist" in bad["message"]


def test_plot_volume_difference_heatmap_ct_numpy(tmp_path: Path) -> None:
    import matplotlib.pyplot as plt

    from fyron.visualization import plot_volume_difference_heatmap

    a = np.zeros((5, 8, 8), dtype=np.float32)
    b = np.zeros_like(a)
    a[2, 2:6, 2:6] = 100.0
    b[2, 2:6, 2:6] = 80.0
    out = tmp_path / "diff.png"

    fig, axes, table = plot_volume_difference_heatmap(
        a,
        b,
        data_type="ct_hu",
        slice_index=2,
        save_path=out,
    )

    assert axes.shape == (1, 3)
    assert out.is_file() and out.stat().st_size > 0
    assert table.loc[0, "slice_index"] == 2
    assert table.loc[0, "units"] == "HU"
    assert table.loc[0, "max_difference"] == pytest.approx(20.0)
    plt.close(fig)


def test_plot_volume_difference_heatmap_nifti_geometry(tmp_path: Path) -> None:
    import matplotlib.pyplot as plt
    import SimpleITK as sitk

    from fyron.imaging.nifti_io import write_nifti
    from fyron.visualization import plot_volume_difference_heatmap

    arr_a = np.full((4, 6, 7), 50.0, dtype=np.float32)
    arr_b = np.full((4, 6, 7), 40.0, dtype=np.float32)
    img_a = sitk.GetImageFromArray(arr_a)
    img_b = sitk.GetImageFromArray(arr_b)
    img_a.SetSpacing((0.8, 0.9, 1.5))
    img_b.SetSpacing((0.8, 0.9, 1.5))
    path_a = tmp_path / "a.nii.gz"
    path_b = tmp_path / "b.nii.gz"
    write_nifti(img_a, path_a)
    write_nifti(img_b, path_b)

    fig, axes, table = plot_volume_difference_heatmap(
        path_a,
        path_b,
        orientation="coronal",
        slice_fraction=0.5,
    )

    assert axes.shape == (1, 3)
    assert table.loc[0, "orientation"] == "coronal"
    assert table.loc[0, "mean_difference"] == pytest.approx(10.0)
    plt.close(fig)


def test_plot_volume_difference_heatmap_ct_uint16_conversion() -> None:
    import matplotlib.pyplot as plt

    from fyron.visualization import plot_volume_difference_heatmap

    a = np.full((3, 4, 4), 1124, dtype=np.uint16)
    b = np.full((3, 4, 4), 1024, dtype=np.uint16)
    fig, _axes, table = plot_volume_difference_heatmap(
        a,
        b,
        data_type="ct_uint16",
        slice_index=1,
        rescale_intercept=-1024,
        rescale_slope=1.0,
    )

    assert table.loc[0, "mean_difference"] == pytest.approx(100.0)
    assert table.loc[0, "units"] == "HU"
    plt.close(fig)


def test_plot_volume_difference_heatmap_mr_and_orientations() -> None:
    import matplotlib.pyplot as plt

    from fyron.visualization import plot_volume_difference_heatmap

    a = np.linspace(0, 100, num=5 * 6 * 7, dtype=np.float32).reshape(5, 6, 7)
    b = a * 0.8

    for orientation in ["axial", "coronal", "sagittal"]:
        fig, axes, table = plot_volume_difference_heatmap(
            a,
            b,
            data_type="mr",
            orientation=orientation,  # type: ignore[arg-type]
            slice_indices=[1, 2],
        )
        assert axes.shape == (2, 3)
        assert len(table) == 2
        assert table["units"].eq("normalized intensity").all()
        plt.close(fig)


def test_plot_volume_difference_heatmap_shape_and_geometry_errors() -> None:
    import SimpleITK as sitk

    from fyron.visualization import plot_volume_difference_heatmap

    a = np.zeros((3, 4, 5), dtype=np.float32)
    b = np.zeros((3, 4, 6), dtype=np.float32)
    with pytest.raises(ValueError, match="shape mismatch"):
        plot_volume_difference_heatmap(a, b)

    img_a = sitk.GetImageFromArray(np.zeros((3, 4, 5), dtype=np.float32))
    img_b = sitk.GetImageFromArray(np.zeros((3, 4, 5), dtype=np.float32))
    img_a.SetSpacing((1.0, 1.0, 1.0))
    img_b.SetSpacing((1.0, 1.0, 2.0))
    with pytest.raises(ValueError, match="geometry mismatch"):
        plot_volume_difference_heatmap(img_a, img_b)
