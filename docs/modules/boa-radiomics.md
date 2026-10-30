# BOA Radiomics

`fyron.boa_radiomics` extracts PyRadiomics features from BOA cohort folders. It is designed for cases where BOA has already produced CT images and segmentation masks such as `body-regions.nii.gz` or `total.nii.gz`, and you want model-ready radiomics features per patient.

For the combined BOA workflow overview, see [BOA](boa.md). For JSON measurement features, see [BOA Extraction](boa-extraction.md). For visual quality-control collages, see [BOA Visualization](visualization.md).

Upstream references: [PyRadiomics documentation](https://pyradiomics.readthedocs.io/en/latest/), [PyRadiomics on GitHub](https://github.com/AIM-Harvard/pyradiomics), and [BOA CT / BOA MR repositories](boa.md#upstream-tools-and-repositories).

## Install

```bash
uv add "fyron[radiomics]"
```

Use Python 3.11 for Fyron's PyRadiomics 3.0.1 workflow. Python 3.12 is not supported by this dependency configuration. Source builds can also fail because upstream build requirements omit NumPy; see the tested build workaround and environment evidence in [Research Reliability](../reliability.md). The installation command alone is not a guarantee that an upstream source build will succeed.

This installs PyRadiomics. Fyron's imaging stack already uses SimpleITK.

## Expected Folder Layout

```text
boa-cohort/
  patient0001/
    ct.nii.gz
    body-regions.nii.gz
    total.nii.gz
  patient0002/
    image.nii.gz
    body-regions.nii.gz
    total.nii.gz
```

The default CT lookup tries several common names:

```text
ct.nii.gz
CT.nii.gz
image.nii.gz
CT/image.nii.gz
ct.nii
image.nii
```

You can pass your own `image_filename` if your BOA export uses a different layout.

## Imports

```python
from fyron.boa_radiomics import (
    discover_boa_radiomics_cases,
    extract_case_radiomics_features,
    extract_boa_radiomics_features,
)
```

## Function Parameter Reference

### `discover_boa_radiomics_cases`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `cohort_folder` | yes | none | Root folder containing BOA patient folders. |
| `segmentation_filename` | no | `"total.nii.gz"` | Segmentation file used to identify completed cases. |

Returns a sorted list of patient folders.

### `extract_case_radiomics_features`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `case_folder` | yes | none | Patient folder containing CT and segmentation files. |
| `image_filename` | no | common CT candidates | CT image filename, path, or fallback sequence. |
| `segmentation_kind` | no | `"total"` | `"total"` or `"body_regions"`. |
| `segmentation_filename` | no | based on kind | Explicit segmentation filename. |
| `labels` | no | default labels | Mapping of label name to integer label value, or a sequence of label integers. |
| `extractor` | no | `None` | Preconfigured PyRadiomics extractor. |
| `extractor_settings` | no | `None` | Keyword settings passed to `RadiomicsFeatureExtractor`. |
| `feature_prefix` | no | `"radiomics"` | Prefix used for output columns. |
| `download_id` | no | folder name | Explicit case identifier. |
| `include_paths` | no | `True` | Include image and segmentation paths in the output row. |
| `exclude_diagnostics` | no | `True` | Drop PyRadiomics diagnostic metadata columns. |
| `minimum_voxels` | no | `1` | Skip labels with fewer voxels. |
| `resample_mask` | no | `True` | Resample segmentation to the CT grid when geometry differs. |
| `on_error` | no | `"skip"` | `"skip"` or `"raise"`. |

Returns one wide feature dictionary or `None` when required inputs are missing.

### `extract_boa_radiomics_features`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `cohort_folder_or_cases` | yes | none | Cohort root, one case folder, or a list of case folders. |
| `image_filename` | no | common CT candidates | CT image filename or fallback sequence. |
| `segmentation_kind` | no | `"total"` | `"total"` or `"body_regions"`. |
| `segmentation_filename` | no | based on kind | Explicit segmentation filename. |
| `labels` | no | default labels | Label mapping or sequence. |
| `extractor_settings` | no | `None` | PyRadiomics settings. |
| `feature_prefix` | no | `"radiomics"` | Prefix used for output columns. |
| `include_paths` | no | `True` | Include source paths. |
| `minimum_voxels` | no | `1` | Skip tiny/empty labels. |
| `exclude_diagnostics` | no | `True` | Omit PyRadiomics diagnostic columns from returned feature rows. |
| `resample_mask` | no | `True` | Resample mismatched masks to the image grid with nearest-neighbor interpolation. |
| `on_error` | no | `"skip"` | Skip failed cases/labels, or use `"raise"` to stop on an error. |
| `num_workers` | no | `1` | Number of multiprocessing workers. |
| `show_progress` | no | `True` | Show tqdm progress. |
| `return_report` | no | `False` | Return `data` plus case/label `rows` and aggregate `summary` tables. |

Returns a `pandas.DataFrame` of retained cases; unique folder basenames are required for a unique `download_id`. Missing inputs may remove a case under `on_error="skip"`, while label failures or small masks can leave a row containing voxel counts but no extracted radiomics features. Inspect feature columns as well as row counts. An entirely empty result may have no columns.

Resampling aligns a mask to a reference grid, not to a different anatomy. It is not image registration. Use `resample_mask=False, on_error="raise"` when validating whether inputs already share a grid. Fyron-owned failure logs use controlled categories without source paths or exception text. Third-party logs and explicitly raised exceptions may still contain diagnostic details; keep them within the research environment. `include_paths=False` removes path columns from feature rows, not from the explicit case report. See [report interpretation](boa.md#check-coverage-before-joining).

## CLI Workflow

Use the CLI when radiomics extraction should run as a batch job.

```bash
fyron boa-radiomics \
  --cohort-folder /data/boa-cohort \
  --segmentation total \
  --output boa_total_radiomics.csv \
  --num-workers 8
```

For body-region radiomics:

```bash
fyron boa-radiomics \
  --cohort-folder /data/boa-cohort \
  --segmentation body_regions \
  --output boa_body_region_radiomics.csv
```

## Extract Total-Segmentation Radiomics

Use total segmentation radiomics when you want organ-level texture and shape features from `total.nii.gz`.

```python
from fyron.boa_radiomics import extract_boa_radiomics_features

features = extract_boa_radiomics_features(
    cohort_folder_or_cases="/data/boa-cohort",
    segmentation_kind="total",
    segmentation_filename="total.nii.gz",
    image_filename=("ct.nii.gz", "image.nii.gz", "CT/image.nii.gz"),
    labels={
        "liver": 5,
        "spleen": 1,
        "pancreas": 10,
    },
    extractor_settings={
        "binWidth": 25,
        "resampledPixelSpacing": [1, 1, 1],
    },
    num_workers=8,
)

features.to_csv("boa_total_radiomics.csv", index=False)
```

Output columns follow this pattern:

```text
radiomics_total_liver_original_firstorder_Mean
radiomics_total_liver_original_glcm_Contrast
radiomics_total_liver_original_shape_VoxelVolume
```

## Extract Body-Region Radiomics

Use body-region radiomics when you want features from regions in `body-regions.nii.gz`, such as abdominal cavity (3), thoracic cavity (4), and bone (5). BOA does not define a pelvis label in this mask.

```python
features = extract_boa_radiomics_features(
    cohort_folder_or_cases="/data/boa-cohort",
    segmentation_kind="body_regions",
    segmentation_filename="body-regions.nii.gz",
    labels={
        "thoracic_cavity": 4,
        "abdominal_cavity": 3,
        "bone": 5,
    },
    num_workers=8,
)
```

If your BOA label map differs, pass your own `labels` mapping.

With `labels=None`, all eleven upstream anatomical regions are selected, using
their names from `DEFAULT_BODY_REGION_LABELS`. Pass a subset as above to extract
only dedicated regions. Earlier defaults incorrectly named labels 3, 4, and 5
as thorax, abdomen, and pelvis. Re-extract affected results; renaming columns
alone does not repair analyses that selected the wrong region.

## Extract One Patient For Validation

Always validate a single patient before launching a full cohort job.

```python
from fyron.boa_radiomics import extract_case_radiomics_features

row = extract_case_radiomics_features(
    case_folder="/data/boa-cohort/patient0001",
    segmentation_kind="total",
    labels={"liver": 5},
    include_paths=True,
    on_error="raise",
)

sorted(row.keys())[:10]
```

Check the voxel count and a few features against the mask before scaling:

```python
row["radiomics_total_liver_voxel_count"]
row["radiomics_total_liver_original_firstorder_Mean"]
```

## Custom PyRadiomics Extractor

For full control, create a PyRadiomics extractor yourself and pass it to the single-case helper.

```python
from radiomics import featureextractor
from fyron.boa_radiomics import extract_case_radiomics_features

extractor = featureextractor.RadiomicsFeatureExtractor(
    binWidth=25,
    resampledPixelSpacing=[1, 1, 1],
    correctMask=False,
)
extractor.disableAllFeatures()
extractor.enableFeatureClassByName("firstorder")
extractor.enableFeatureClassByName("shape")

row = extract_case_radiomics_features(
    case_folder="/data/boa-cohort/patient0001",
    segmentation_kind="total",
    labels={"liver": 5},
    extractor=extractor,
)
```

For multiprocessing, prefer `extractor_settings` instead of passing an extractor object. Each worker can then construct its own extractor.

## Join With BOA Measurements

Radiomics features can be merged with the measurement features from `fyron.boa_extraction`.

```python
from fyron.boa_extraction import extract_boa_features
from fyron.boa_radiomics import extract_boa_radiomics_features

measurements = extract_boa_features(
    cohort_folder_or_cases="/data/boa-cohort",
    num_workers=8,
)

radiomics = extract_boa_radiomics_features(
    cohort_folder_or_cases="/data/boa-cohort",
    segmentation_kind="total",
    labels={"liver": 5, "spleen": 1},
    num_workers=8,
)

features = measurements.merge(
    radiomics,
    on="download_id",
    how="left",
    validate="one_to_one",
)
```

## Practical Guidance

- Start with one label and one patient.
- Keep `include_paths=True` while validating so every row can be traced back to image and mask files.
- Check `radiomics_<kind>_<label>_voxel_count` before trusting texture features.
- Use `minimum_voxels` to skip tiny masks.
- Keep PyRadiomics settings versioned with your analysis.
- Use the same CT preprocessing and resampling choices for every cohort.
- Treat body-region label values as project-specific unless your BOA export defines them explicitly.
