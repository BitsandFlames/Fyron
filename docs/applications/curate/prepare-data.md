# Prepare Your Data for Curate

Use an ordinary image folder or a DICOM series folder for direct upload. For NIfTI and other volume formats, first generate PNG previews with Fyron.

## Accepted uploads and preview limits

| Input | Direct upload | Preview guidance |
| --- | --- | --- |
| PNG, JPEG/JPG | Yes | Recommended for portable image review. |
| WebP, GIF, BMP | Yes | Browser decoding determines display. Do not rely on GIF playback to review every frame. |
| TIFF/TIF | Yes | Accepted by the importer, but browser display varies. Convert to PNG for reliable previews. |
| DICOM `.dcm`, `.dicom`, `.ima` | Yes | Files are grouped by study and series. Common uncompressed data works best; compressed transfer syntaxes may not decode. |
| Extensionless DICOM | Candidate files are accepted | Files must contain readable DICOM data. An extensionless file is not necessarily DICOM. |
| NIfTI `.nii`, `.nii.gz` | No | Generate PNG previews first. |
| MHA/MHD, NRRD/NHDR | No | Generate previews first; retain any referenced companion data files. |
| ZIP, PDF, CSV, other documents | No image review | Unzip image archives before upload. Keep CSV manifests for your own traceability. |

Accepted extensions do not guarantee valid contents or a decodable preview. Files outside the importer's supported candidates are filtered out. Invalid image data and unreadable DICOM can cause an upload failure; do not treat a partially uploaded cohort as complete.

## Organize an image folder

No special folder names or labels file are required. Use stable synthetic or approved study identifiers and keep filenames meaningful:

```text
review_images/
  case_001/
    axial.png
    coronal.png
  case_002/
    axial.png
    coronal.png
```

Drop `review_images/` into **Add cohort**. Nested relative paths are preserved, so the two `axial.png` files remain distinct. Conflicting content at the same relative path is rejected. Identical re-uploads preserve existing review history.

General preparation is straightforward: export the views you want to assess as PNG or JPEG, put them into this structure, and inspect the images before importing. Export with deliberate windowing and scaling. A preview is a display image, not a replacement for the original quantitative data.

## Organize DICOM series

Keep complete series together and retain their original files:

```text
dicom_review/
  case_001/
    series_01/
      instance_001.dcm
      instance_002.dcm
    series_02/
      instance_001.dcm
  case_002/
    series_01/
      instance_001.dcm
```

Study and series grouping uses DICOM metadata rather than these folder names. Import the full intended series before reviewing it. Adding instances to a series that has already been reviewed requires a new cohort. DICOM thumbnails support series selection; they are not a diagnostic viewer for every slice or frame.

## Upload limits and retries

Each file may be at most **32 MiB**, and each request batch at most **128 MiB**. The browser automatically divides larger folder selections into batches. Raster images must also pass content validation and the 100-million-pixel dimension limit.

If an upload fails, keep the same selection and retry **Create cohort** so completed batches can be reused. API callers should retry the same batch. Incomplete uploads block exports. Resolve any damaged DICOM metadata before exporting selected series.

## Prepare volume previews with Fyron

Install the preview helpers alongside Curate:

```bash
uv add "fyron[visualization,curate]"
```

Use separate source and output directories. For example:

```text
study_volumes/
  case_001/
    ct.nii.gz
  case_002/
    mr.nii.gz
```

### Bash

```bash
uv run fyron dataset-curate-previews \
  --input-dir study_volumes/ \
  --output-dir curate_previews/
```

For a CT-only folder, a fixed display window can be supplied explicitly. This example is an illustrative soft-tissue window; choose a window appropriate to your review task:

```bash
uv run fyron dataset-curate-previews \
  --input-dir ct_volumes/ \
  --output-dir ct_previews/ \
  --window-center 40 \
  --window-width 400
```

### Python

```python
from fyron.visualization import prepare_curate_image_previews

result = prepare_curate_image_previews(
    input_dir="study_volumes",
    output_dir="curate_previews",
    percentile_clip=(1.0, 99.0),
    overwrite=False,
)

errors = [row for row in result["rows"] if row["status"] == "error"]
if errors:
    raise RuntimeError(
        f"Preview generation failed for {len(errors)} sources. "
        "Inspect the manifest locally before importing."
    )
if result["sources_found"] == 0:
    raise RuntimeError("No supported image sources were found.")

print(result["manifest_csv"])
print(result["images_written"], result["images_skipped"])
```

For CT windowing in Python, supply both `window_center=40` and `window_width=400`. Without a fixed window, the helper uses the 1st and 99th percentiles for display scaling, including MRI. This changes the preview display, not the original image.

The helper scans nested folders by default. It accepts NIfTI, MHA/MHD, NRRD/NHDR, common PNG/JPEG/BMP/TIFF images, and discoverable DICOM series. For recursive DICOM discovery, use `.dcm`, `.dicom`, or `.ima` filenames. If a source directory contains only extensionless instances, point the helper at that series directory explicitly and check `sources_found`. The preview helper's raster list differs from Curate's upload list: WebP and GIF are direct-upload formats, not inputs to this helper.

### Inspect the output

Three-dimensional sources produce middle axial, coronal, and sagittal PNGs. Two-dimensional sources produce one PNG. Preview names are generated from the source name or series identity, with orientation suffixes; nested folders are retained:

```text
curate_previews/
  case_001/
    ct.nii.gz_axial.png
    ct.nii.gz_coronal.png
    ct.nii.gz_sagittal.png
  case_002/
    mr.nii.gz_axial.png
    mr.nii.gz_coronal.png
    mr.nii.gz_sagittal.png
  manifest.csv
```

Inspect `manifest.csv` before uploading. It records source and output paths, series identity where applicable, orientation, slice index, shape, and per-source status. A returned result or written manifest does not mean every source succeeded. Existing previews are skipped unless overwrite is requested; use a fresh output folder when source data or display settings change.

Drop the generated preview folder into Curate. Keep the manifest locally under the same access controls as the source data: it can contain identifying paths and metadata.

## Understand what a preview decision means

Reviewing generated PNGs selects **those PNG files**. Clean-folder export does not automatically select or copy their original NIfTI volumes or DICOM series.

To apply decisions to source volumes, use the manifest to map PNG paths back to sources and define a rule, such as requiring all three views to be accepted. Record that rule in your methods. Middle slices can miss findings elsewhere in a volume; they are not complete-volume quality assessment.

[Review and export](review-export.md) · [Preview API reference](../../modules/visualization.md#preparecurateimagepreviews) · [Synthetic example cohort](../curate.md#explore-curate-with-example-data)
