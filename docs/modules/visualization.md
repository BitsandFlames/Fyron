# BOA Visualization

`fyron.visualization` provides medical imaging figures for clinical review, reports, and publication figures. It includes BOA segmentation collages, CT/MR Curate preview preparation, and aligned CT/MR volume-difference heatmaps.

For the combined BOA workflow overview, see [BOA](boa.md). For feature-table extraction from the same folders, see [BOA Extraction](boa-extraction.md). For local image I/O and normalization, see [Imaging](imaging.md).

Use this module when the clinical question benefits from seeing anatomy and segmentation context together. The collage helpers are designed for review boards, quality control, and report figures where several patients or segmentation layers need to be compared in one visual artifact.

Before building a final figure, confirm orientation, slice position, windowing, and label colors on a small subset. A visually clean collage is only useful if each row represents the intended patient, slice, and segmentation layer.

## Install

```bash
uv add "fyron[visualization]"
```

This installs OpenCV for rendering. NIfTI I/O uses the imaging stack already included with Fyron.

## Imports

```python
from fyron.visualization import (
    SegmentationLayer,
    create_boa_segmentation_collage,
    create_segmentation_collage,
    create_segmentation_collages_from_cases,
    prepare_curate_image_previews,
    plot_volume_difference_heatmap,
)
```

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | BOA folder paths for BOA collages; arbitrary CT/segmentation NIfTI paths or arrays for generic segmentation collages; CT/MR image directories for Curate previews; NIfTI paths, `SimpleITK.Image`, or NumPy volumes for difference heatmaps. |
| Required columns/files | Collages need image and segmentation volumes with matching shapes; heatmaps need two same-shape and same-geometry volumes. |
| Return shape | Collage helpers write an image and return metadata; heatmaps return `(fig, axes, table)`. |
| Saved artifacts | PNG collage/review images, Curate preview folders, CSV manifests, volume-difference figures, and slice-level difference summary tables. |
| Failure modes | Missing files, incompatible geometry, unsupported orientation, invalid slice selection, failed image loading, or misleading comparisons without prior alignment. |

## Function Parameter Reference

The tables below distinguish required inputs from optional configuration through the `Required` column.

### `SegmentationLayer`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `kind` | yes | none | One of `body_regions`, `tissues`, or `total`. |
| `display_mode` | no | layer default | `ct`, `ct_overlay`, or `segmentation`. |
| `title` | no | default layer title | Column title. |
| `filename` | no | default BOA filename | Override mask filename. |
| `opacity` | no | global opacity | Per-layer overlay opacity. |

### `create_boa_segmentation_collage`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `boa_folders` | yes | none | One BOA output folder per patient. |
| `output_path` | yes | none | Destination image path. |
| `orientation` | no | `"axial"` | `axial`, `sagittal`, or `coronal`. |
| `segmentation_layers` | no | default layers | Strings or `SegmentationLayer` objects. |
| `patient_labels` | no | `Patient A`, ... | Row labels. |
| `slice_index` | no | center | Absolute slice index. |
| `slice_indices` | no | `None` | Multiple absolute slices. |
| `slice_fraction` | no | `None` | Relative slice position in `[0, 1]`. |
| `ct_filename` | no | auto-detect | Explicit CT file in each folder. |
| `window_center` | no | `40.0` | CT window center. |
| `window_width` | no | `400.0` | CT window width. |
| `segmentation_opacity` | no | `0.45` | Global overlay opacity. |
| `overlay_alpha` | no | `None` | Deprecated alias for opacity. |
| `panel_width` | no | `320` | Width of each panel in pixels. |
| `row_label_prefix` | no | orientation label | Prefix for multi-slice labels. |
| `crop_body_region` | no | `None` | BOA region id/name for automatic crop. |
| `body_region_padding_mm` | no | `15.0` | Crop padding in millimetres. |
| `body_region_slices` | no | `"best"` | `best`, `center`, or `all`. |

Returns a metadata dict and writes the image to `output_path`.

### `create_segmentation_collage`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `image` | yes | none | NIfTI path, `SimpleITK.Image`, or NumPy array in `(z, y, x)` order. |
| `segmentation` | yes | none | Matching segmentation volume. |
| `output_path` | yes | none | Destination image path, usually `.png`. |
| `labels` | no | `None` | Label id or ids to display; `None` displays all non-zero labels. |
| `orientation` | no | `"axial"` | `axial`, `sagittal`, or `coronal`. |
| `slice_strategy` | no | `"segmentation_extent"` | Use slices containing selected labels, or `"full_extent"` for the whole volume. |
| `slice_indices` | no | `None` | Explicit absolute slice indices. |
| `every_n_slices` | no | `None` | Step size across the selected extent. |
| `max_slices` | no | `None` | Downsample selected slices to at most this number. |
| `n_cols` | no | auto | Number of grid columns. |
| `window_center`, `window_width` | no | `40.0`, `400.0` | CT display window. |
| `segmentation_opacity` | no | `0.40` | Overlay opacity. |
| `label_colors` | no | default palette | RGB colors by label id or color sequence. |
| `title`, `show_slice_labels` | no | `None`, `True` | Optional header and per-panel slice labels. |
| `panel_width` | no | `256` | Width of each panel in pixels. |

Returns a metadata dict and writes a pure OpenCV PNG collage.

### `create_segmentation_collages_from_cases`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `input_root` | yes | none | Folder containing case directories. |
| `output_dir` | yes | none | Destination folder for one PNG per case. |
| `case_glob` | no | `"case-*"` | Case directory pattern. |
| `image_relpath` | no | `"A/image.nii.gz"` | Image path relative to each case folder. |
| `segmentation_relpath` | no | `"A/segmentation.nii.gz"` | Segmentation path relative to each case folder. |
| `output_suffix` | no | `".png"` | Output suffix; filenames use the case directory name. |
| `continue_on_error` | no | `True` | Record failed cases in the summary table instead of stopping. |

All rendering parameters from `create_segmentation_collage` are forwarded. The return value is a DataFrame with `case_id`, input paths, `output_path`, `status`, `message`, selected slices, and slice counts.

### `prepare_curate_image_previews`

For folder layouts and complete Bash/Python examples, see [Prepare your data for Curate](../applications/curate/prepare-data.md).

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `input_dir` | yes | none | Directory containing CT/MRI volumes, DICOM series, or 2-D images. |
| `output_dir` | yes | none | Curate-ready folder for PNG previews. |
| `recursive` | no | `True` | Scan nested folders. |
| `include_dicom` | no | `True` | Discover DICOM series below the input directory. |
| `include_image_files` | no | `True` | Read NIfTI/MHA/NRRD and common 2-D raster files. |
| `panel_width` | no | `384` | Output PNG width. |
| `window_center`, `window_width` | no | `None` | Optional fixed CT-style window. |
| `percentile_clip` | no | `(1.0, 99.0)` | Robust auto-windowing for CT/MRI when no fixed window is passed. |
| `overwrite` | no | `False` | Overwrite existing PNG previews. |
| `manifest_csv` | no | `output_dir/manifest.csv` | Preview manifest path. |

Returns a metadata dict and writes PNG previews plus a CSV manifest.

### `plot_volume_difference_heatmap`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `volume_a`, `volume_b` | yes | none | NIfTI path, `SimpleITK.Image`, or NumPy array in `(z, y, x)` order. |
| `data_type` | no | `"ct_hu"` | `"ct_hu"`, `"ct_uint16"`, or `"mr"`. |
| `orientation` | no | `"axial"` | `axial`, `sagittal`, or `coronal`. |
| `slice_index` | no | center | One absolute slice index. |
| `slice_indices` | no | `None` | Multiple absolute slices. |
| `slice_fraction` | no | `None` | One relative slice position in `[0, 1]`. |
| `label_a`, `label_b` | no | `Volume A`, `Volume B` | Column labels. |
| `window_center`, `window_width` | no | `40.0`, `400.0` | CT display window. |
| `rescale_slope`, `rescale_intercept` | no | `1.0`, `-1024.0` | Stored CT value to HU conversion for `ct_uint16`. |
| `mr_normalization`, `mr_percentile` | no | `percentile`, `99.0` | MR scaling before difference calculation. |
| `diff_vmax` | no | auto | Symmetric absolute limit for the difference map. |
| `diff_percentile` | no | `99.0` | Percentile used when `diff_vmax` is automatic. |
| `diff_cmap` | no | `fyron_diverging_blue_red` | Matplotlib or Fyron diverging colormap. |
| `figsize`, `title`, `save_path` | no | `None` | Layout and optional export settings. |

Returns `(fig, axes, table)`. The table has one row per rendered slice with difference summaries such as mean difference, mean absolute difference, RMSE, min/max difference, and the symmetric heatmap limit.

## What The Collage Shows

The collage layout is optimized for comparing patients and mask layers:

- columns represent segmentation layers, such as body regions, tissues, and organs,
- rows represent patients or selected slices,
- patient labels are displayed on the row axis,
- CT backgrounds can be windowed and overlaid with segmentation colors,
- voxel spacing is respected when sizing panels,
- optional body-region cropping keeps anatomy framed consistently.

## Expected BOA Folder

Each patient folder should contain a CT NIfTI and one or more mask files:

| File | Meaning |
| --- | --- |
| CT NIfTI | Auto-detected as the largest non-mask NIfTI unless `ct_filename` is passed |
| `body-regions.nii.gz` | BOA body region labels |
| `tissues.nii.gz` | tissue labels |
| `total.nii.gz` | organ / TotalSegmentator-style labels |

The CT and mask arrays must have matching shapes.

## Basic Multi-Patient Collage

```python
result = create_boa_segmentation_collage(
    boa_folders=["/data/patient_a", "/data/patient_b"],
    output_path="figures/boa_axial.png",
    orientation="axial",
    segmentation_layers=["body_regions", "tissues", "total"],
    patient_labels=["Patient A", "Patient B"],
    slice_fraction=0.5,
)

result["output_path"]
result["image_shape"]
```

The function returns metadata including output path, patient paths, layers used, orientation, image shape, and selected slice indices.

## Generic Segmentation Collage

Use `create_segmentation_collage` for arbitrary CT plus segmentation volumes when the masks are not in BOA folders. The helper renders overlays with OpenCV, so it is suitable for headless servers and batch jobs.

```python
from fyron.visualization import create_segmentation_collage

result = create_segmentation_collage(
    image="/data/case-0001/A/image.nii.gz",
    segmentation="/data/case-0001/A/segmentation.nii.gz",
    output_path="/data/collages/case-0001.png",
    labels=(11, 12),
    orientation="axial",
    every_n_slices=5,
    n_cols=5,
    window_center=40,
    window_width=400,
    segmentation_opacity=0.40,
    title="case-0001",
)

result["slice_indices_used"]
```

By default, Fyron finds the first and last slice containing the selected labels and samples over that z-extent. This keeps the collage focused on the segmentation while still showing the spatial spread of the mask.

For many cases with the layout `case-0001/A/image.nii.gz` and `case-0001/A/segmentation.nii.gz`, use the batch helper:

```python
from pathlib import Path
from fyron.visualization import create_segmentation_collages_from_cases

summary = create_segmentation_collages_from_cases(
    input_root=Path("/raid/work/katborys/LAG_prediction_data/nifti_seg"),
    output_dir=Path("/raid/work/katborys/LAG_prediction_data/collages"),
    case_glob="case-*",
    image_relpath="A/image.nii.gz",
    segmentation_relpath="A/segmentation.nii.gz",
    labels=(11, 12),
    orientation="axial",
    every_n_slices=5,
    n_cols=5,
)

summary[["case_id", "status", "output_path", "n_slices"]]
```

Failed cases remain in the summary table with `status="error"` and an explanatory `message`, which makes large cohort runs easier to audit.

## Curate Preview Preparation

Use `prepare_curate_image_previews` when a folder of CT/MRI volumes should be turned into PNGs that can be dropped directly into Fyron Curate. 3-D volumes produce middle axial, coronal, and sagittal slices. 2-D images such as X-rays or topograms produce one preview.

```python
from fyron.visualization import prepare_curate_image_previews

result = prepare_curate_image_previews(
    input_dir="/data/ct_exports",
    output_dir="curate_previews",
    recursive=True,
    panel_width=384,
)

result["manifest_csv"]
result["images_written"]
```

The equivalent CLI command is:

```bash
fyron dataset-curate-previews --input-dir /data/ct_exports --output-dir curate_previews
```

After the previews are written, launch the review app and drop the generated folder into the **Add cohort** dialog:

```bash
fyron curate
```

The generated `manifest.csv` is for traceability; Curate indexes the PNG files themselves and preserves their relative folder paths.

## Layer Configuration

Use strings for common defaults:

```python
create_boa_segmentation_collage(
    ["/data/patient_a"],
    "boa_default.png",
    segmentation_layers=["body_regions", "tissues", "total"],
)
```

Use `SegmentationLayer` for display modes and opacity:

```python
create_boa_segmentation_collage(
    ["/data/patient_a"],
    "boa_custom.png",
    segmentation_layers=[
        SegmentationLayer("body_regions", display_mode="ct_overlay", opacity=0.55),
        SegmentationLayer("tissues", display_mode="ct_overlay", opacity=0.4),
        SegmentationLayer("total", display_mode="segmentation"),
    ],
    slice_index=90,
)
```

Display modes:

| Mode | Use |
| --- | --- |
| `ct` | CT only, useful as an anatomical reference |
| `ct_overlay` | CT with semi-transparent segmentation |
| `segmentation` | segmentation colors without CT background |

## Slice Selection

Choose one absolute slice:

```python
create_boa_segmentation_collage(
    ["/data/patient_a"],
    "slice_90.png",
    orientation="axial",
    slice_index=90,
)
```

Choose relative position per patient:

```python
create_boa_segmentation_collage(
    ["/data/patient_a", "/data/patient_b"],
    "middle_slice.png",
    orientation="axial",
    slice_fraction=0.5,
)
```

Choose multiple slices:

```python
create_boa_segmentation_collage(
    ["/data/patient_a"],
    "multi_slice.png",
    orientation="coronal",
    slice_indices=[80, 100, 120],
)
```

## Body-Region Cropping

Cropping is useful when the clinical figure should focus on one anatomical region.

```python
create_boa_segmentation_collage(
    ["/data/patient_a", "/data/patient_b"],
    "abdomen.png",
    orientation="axial",
    crop_body_region="Abdominal Cavity",
    body_region_padding_mm=20,
    body_region_slices="best",
)
```

`body_region_slices` options:

| Option | Behavior |
| --- | --- |
| `best` | slice with largest in-plane region area |
| `center` | middle slice of the region extent |
| `all` | every slice containing the region |

When `crop_body_region` is used, do not pass `slice_index`, `slice_indices`, or `slice_fraction`; slices are selected automatically.

## CT Windowing And Opacity

```python
create_boa_segmentation_collage(
    ["/data/patient_a"],
    "lung_window.png",
    window_center=-600,
    window_width=1500,
    segmentation_opacity=0.35,
)
```

Per-layer opacity overrides the global `segmentation_opacity`.

## Output Metadata

```python
result = create_boa_segmentation_collage(...)

{
    "output_path": result["output_path"],
    "patient_paths": result["patient_paths"],
    "slice_indices_used": result["slice_indices_used"],
    "orientation": result["orientation"],
    "image_shape": result["image_shape"],
}
```

Use this metadata to track exactly which slices and layers were used in a manuscript figure.

## Volume Difference Heatmaps

Use `plot_volume_difference_heatmap` when two already-aligned volumes should be visually compared slice by slice. Typical use cases include GAN output review, reconstruction checks, registration QC after explicit resampling, and model-output comparison against a reference volume.

The figure always has three columns:

| Column | Meaning |
| --- | --- |
| Volume A | Reference or baseline volume. |
| Volume B | Comparison volume. |
| Difference | `Volume A - Volume B`, shown with a zero-centered diverging heatmap. |

```python
from fyron.visualization import plot_volume_difference_heatmap

fig, axes, diff_table = plot_volume_difference_heatmap(
    "reference_ct.nii.gz",
    "generated_ct.nii.gz",
    data_type="ct_hu",
    orientation="axial",
    slice_indices=[70, 90, 110],
    label_a="Reference CT",
    label_b="Generated CT",
    window_center=40,
    window_width=400,
    title="CT difference review",
    save_path="figures/ct_difference.png",
)

diff_table.to_csv("figures/ct_difference_summary.csv", index=False)
```

### CT HU, CT UInt16, And MR Inputs

Use `data_type="ct_hu"` when both arrays are already in Hounsfield units. Use `data_type="ct_uint16"` for stored integer CT values that need conversion to HU:

```python
plot_volume_difference_heatmap(
    stored_ct_a,
    stored_ct_b,
    data_type="ct_uint16",
    rescale_slope=1.0,
    rescale_intercept=-1024.0,
)
```

Use `data_type="mr"` for MRI volumes. Fyron normalizes each volume to `[0, 1]` before computing the difference:

```python
plot_volume_difference_heatmap(
    "baseline_mr.nii.gz",
    "followup_mr.nii.gz",
    data_type="mr",
    mr_normalization="percentile",
    mr_percentile=99,
)
```

### Geometry Requirement

V1 is deliberately strict. Volumes must have the same shape. When both inputs carry SimpleITK/NIfTI geometry, spacing, origin, and direction must also match. Fyron does not auto-resample inside the plot function because interpolation choices are clinical assumptions. Resample explicitly before plotting and keep that operation in your provenance manifest.

### Interpreting The Difference Map

The difference panel is centered at `0`: one color direction means Volume A is brighter/higher, the other means Volume B is brighter/higher. For CT this is in HU. For MR this is normalized intensity. Use `diff_vmax` to lock a fixed scale across several cases or let Fyron estimate a robust symmetric scale from `diff_percentile`.

## Troubleshooting

| Problem | Likely cause | Fix |
| --- | --- | --- |
| CT file not found | folder contains no non-mask NIfTI or ambiguous files | pass `ct_filename` |
| shape mismatch | CT and masks are not in the same geometry | resample/align masks before rendering |
| region crop empty | body-region label is absent | choose another region or inspect `body-regions.nii.gz` |
| image too small/large | default `panel_width` is not right for the output | set `panel_width` |
| overlay too strong | opacity too high | lower `segmentation_opacity` or layer opacity |
| difference heatmap geometry error | volumes are not already aligned | resample explicitly before plotting |
| difference colors look saturated | automatic `diff_vmax` is too small for outliers | pass a fixed `diff_vmax` |
