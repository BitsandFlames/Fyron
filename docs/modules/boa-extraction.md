# BOA Extraction

`fyron.boa_extraction` converts Body-and-Organ-Analysis cohort folders into case-level feature tables. One patient can have multiple imaging cases; the extractor does not select a baseline examination or resolve repeated scans.

This module is designed for clinical data science workflows where imaging-derived features need to join cleanly with FHIR, outcome, survival, or ML tables. Every output column maps back to a body region, tissue, vertebral level, organ, or organ ratio.

For the combined BOA workflow overview, see [BOA](boa.md). For radiomics from the same masks, see [BOA Radiomics](boa-radiomics.md). For visual review collages, see [BOA Visualization](visualization.md).

For upstream segmentation software, installation, and attribution, see [BOA CT, BOA MR, and related tools](boa.md#upstream-tools-and-repositories). The measurement schemas and HU-based features on this page follow BOA CT conventions.

## Core Concepts

| Concept | Meaning |
| --- | --- |
| case folder | One BOA output folder for one patient, study, or image series. |
| `download_id` | Case identifier in Fyron outputs. Defaults to the case folder name unless passed explicitly. |
| `bca-measurements.json` | Body-region/tissue measurement file used for body-composition features. |
| `measurements_no_extremities` | BOA JSON branch used for body-region tissue volumes. |
| `total-measurements.json` | Total segmentation measurement file used for organ volume, HU, CNR, and ratio features. |
| `tissues.nii.gz` | Segmentation masks used for vertebral slice markers such as L3 SMA. |
| `total.nii.gz` | Total segmentation mask used by some workflows and visual checks. |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | BOA cohort root containing one case folder per patient, study, or image series. |
| Required columns/files | Expected BOA JSON files such as `bca-measurements.json` and optional segmentation NIfTI files for derived markers. |
| Return shape | Feature extraction returns a `pandas.DataFrame` keyed by `download_id`. |
| Saved artifacts | Caller decides CSV/Parquet export; `return_report=True` also returns case-level decision tables. |
| Failure modes | Missing BOA files, malformed JSON, missing segmentation masks, inconsistent case IDs, or no extractable measurements. |

The body-region extractor deliberately reads tissue volumes from `measurements_no_extremities`:

```text
aggregated -> <body_region> -> measurements_no_extremities -> <tissue> -> sum
```

This means columns such as `abdominal_cavity_muscle_sum_ml` and `thoracic_cavity_vat_sum_ml` exclude extremities according to the BOA JSON output. Total segmentation features are separate and come from `total-measurements.json`.

## Research Decision: BOA Measurement Branches

| Decision | Practical guidance |
| --- | --- |
| `download_id` | Keep it as the stable join key between DICOM downloads, BOA folders, and clinical cohorts. |
| `measurements_no_extremities` | Use this branch for body-composition tissue volumes when available. |
| total segmentation | Use total-organ/body labels when the study question needs organ or region presence/volume. |
| derived markers | Treat derived ratios and region summaries as features; record their source branch in the methods. |
| merging | Merge BOA features to clinical cohorts only after checking one row per `download_id`. |

## Expected Folder Layout

```text
boa-cohort/
  patient0001/
    bca-measurements.json
    total-measurements.json
    tissues.nii.gz
    body-regions.nii.gz
    total.nii.gz
  patient0002/
    bca-measurements.json
    total-measurements.json
    tissues.nii.gz
```

The patient folder name becomes `download_id` by default.

If the folders were created from Fyron DICOM downloads, the folder name is often the deterministic DICOM `download_id`. Keep a clinical mapping table with patient ID, study UID, series UID, and `download_id` so BOA features can be merged back into the cohort.

## Minimal Cohort Example

```python
from fyron.boa_extraction import extract_boa_features

features = extract_boa_features(
    "/data/boa-cohort",
    include_body_regions=True,
    include_total=True,
    num_workers=8,
)

features.head()
```

Returned rows are keyed by `download_id`. Merge with clinical data using that key or a mapping table:

```python
clinical = clinical.merge(features, on="download_id", how="left", validate="one_to_one")
```

## Imports

```python
from fyron.boa_extraction import (
    DEFAULT_BODY_REGION_DERIVED_MARKERS,
    DEFAULT_VERTEBRAL_SLICE_LABELS,
    discover_boa_cases,
    extract_body_region_features,
    extract_total_segmentation_features,
    extract_experimental_aortic_calcification_features,
    extract_experimental_cohort_aortic_calcification_features,
    extract_cohort_body_region_features,
    extract_cohort_total_features,
    extract_boa_features,
)
```

## Function Parameter Reference

### `discover_boa_cases`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `cohort_folder` | yes | none | Root folder containing patient folders. |
| `measurement_filename` | no | `"bca-measurements.json"` | File used to identify completed BOA cases. |

Returns a sorted list of folders found recursively that contain the measurement file. This is file discovery, not JSON validation or a completeness check. To find total-only cases, pass `measurement_filename="total-measurements.json"`. Ensure folder basenames are unique before using them as keys.

### `extract_body_region_features`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `case_folder_or_measurements` | yes | none | Patient folder or direct path to `bca-measurements.json`. |
| `body_regions` | no | abdominal cavity, thoracic cavity, L1-L5 | Keys read from `aggregated`. |
| `tissues` | no | bone, muscle, TAT, IMAT, EAT, PAT, VAT, SAT | Tissue measurements read per body region. |
| `vertebrae` | no | L1-L6, T1-T12 | Vertebral levels used for SMA slices. |
| `measurement_filename` | no | `"bca-measurements.json"` | Measurement filename when a folder is passed. |
| `sma_segmentation_filename` | no | `("tissues.nii.gz",)` | Mask file or fallback list used for vertebral skeletal muscle area. |
| `sma_label` | no | `None` | Infer muscle label 1 for `tissues.nii.gz`; explicit override for custom masks. |
| `slice_levels` | no | `("l3",)` | Vertebral levels used for richer axial area markers. |
| `slice_tissue_labels` | no | SMA/IMAT/VAT/SAT defaults | Tissue-label map used for axial markers. |
| `height_m` | no | `None` | Optional height in meters for explicit height-normalized `*_cm2_per_m2` outputs. Area-based SMI, IMATI, VATI, and SATI do not require height. |
| `include_derived_markers` | no | `True` | Whether to calculate body-region ratio markers. |
| `derived_markers` | no | default ratio marker set | Adjustable ratio definitions. |
| `download_id` | no | folder name | Explicit case identifier. |
| `include_sma` | no | `True` | Whether to calculate `<vertebra>_sma` columns. |
| `missing_value` | no | `numpy.nan` | Value used when JSON keys or masks are missing. |

Returns one feature dictionary or `None` when the measurement JSON is missing or malformed.

Standard BOA tissue masks use muscle=1, bone=2, SAT=3, VAT=4, IMAT=5,
PAT=6, and EAT=7. Anatomical `body-regions.nii.gz` masks use a different
label convention and do not supply HU-filtered tissue areas. The default
therefore uses only `tissues.nii.gz`; without it, slice markers remain missing.
Custom filenames require explicit `sma_label` or `slice_tissue_labels`, and
only supplied markers are measured. Ensure their meaning matches your mask.
Vertebral bounds use BOA's half-open interval `[min_slice_idx, max_slice_idx)`.
They must be integers with `0 <= min < max <= number_of_slices`; invalid bounds
remain missing and appear as `invalid_measurements` in extraction reports.

Recalculate slice markers made with the earlier default label mapping. Its
values could represent the wrong tissue even when they looked plausible.

### Default Body-Region Derived Markers

The body-region extractor now calculates configurable volumetric markers from the BOA JSON tissue volumes.

| Output suffix | Formula | Default regions |
| --- | --- | --- |
| `sarcopenia_index_si` | `muscle / bone` | all requested body regions |
| `myosteatosis_fat_index_mfi` | `100 * imat / tat` | all requested body regions |
| `visceral_fat_index_vfi` | `vat / sat` | `abdominal_cavity` |
| `eat_pat_ratio` | `eat / pat` | `thoracic_cavity`, `ventral_cavity` when available |

Output columns include the body-region prefix:

```text
abdominal_cavity_sarcopenia_index_si
abdominal_cavity_myosteatosis_fat_index_mfi
abdominal_cavity_visceral_fat_index_vfi
thoracic_cavity_eat_pat_ratio
ventral_cavity_eat_pat_ratio
```

### Default L3 Slice Markers

When `tissues.nii.gz` or another segmentation file is available, Fyron can calculate axial area markers at configured vertebral levels, usually L3.

| Output | Meaning |
| --- | --- |
| `l3_sma` | Backwards-compatible skeletal muscle area in cm². |
| `l3_sma_cm2` | Skeletal muscle area in cm². |
| `l3_imat_area_cm2` | Intramuscular adipose tissue area in cm². |
| `l3_vat_area_cm2` | Visceral adipose tissue area in cm². |
| `l3_sat_area_cm2` | Subcutaneous adipose tissue area in cm². |
| `l3_smi` | Area-based skeletal muscle marker in cm²; no height required. |
| `l3_imati` | Area-based intramuscular adipose tissue marker in cm²; no height required. |
| `l3_vati` | Area-based visceral adipose tissue marker in cm²; no height required. |
| `l3_sati` | Area-based subcutaneous adipose tissue marker in cm²; no height required. |
| `l3_smi_cm2_per_m2` | Height-normalized skeletal muscle area, only when `height_m` is passed. |
| `l3_imati_cm2_per_m2` | Height-normalized IMAT area, only when `height_m` is passed. |
| `l3_vati_cm2_per_m2` | Height-normalized VAT area, only when `height_m` is passed. |
| `l3_sati_cm2_per_m2` | Height-normalized SAT area, only when `height_m` is passed. |

The default tissue labels are adjustable:

```python
DEFAULT_VERTEBRAL_SLICE_LABELS
# {"sma": 1, "imat": 5, "vat": 4, "sat": 3}
```

### `extract_total_segmentation_features`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `case_folder` | yes | none | Patient folder containing `total-measurements.json`. |
| `labels` | no | common BOA/TotalSegmentator organs | Organ names to extract from `segmentations.total`. |
| `ratios` | no | spleen/liver | Organ volume ratios to compute. |
| `measurement_filename` | no | `"total-measurements.json"` | Total measurements filename. |
| `download_id` | no | folder name | Explicit case identifier. |
| `round_digits` | no | `2` | Decimal rounding for numeric outputs. |
| `missing_value` | no | `numpy.nan` | Value used when metrics are missing. |

Outputs `<organ>_cnr`, `<organ>_total`, `<organ>_hu`, and ratio columns such as `spleen_liver_ratio`.

### `extract_experimental_aortic_calcification_features`

This extractor is experimental. It belongs in `fyron.boa_extraction` because it derives tabular features from BOA-style CT masks, but aorta and iliac mask names can differ between segmentation pipelines. Always validate the masks and label IDs on a small sample before using the output in a study.

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `case_folder_or_masks_dir` | yes | none | Patient folder or mask folder. |
| `ct_path` | no | auto-detect common CT filenames | CT NIfTI in HU. Pass this explicitly when the CT is outside the mask folder. |
| `masks_dir` | no | `case_folder_or_masks_dir` | Folder containing BOA masks. |
| `download_id` | no | folder name | Explicit case identifier. |
| `hu_threshold` | no | `130.0` | HU threshold used to count calcified voxels. |
| `prefix` | no | `"aortic_calcification"` | Prefix for all output columns. |
| `aorta_mask_filenames` | no | `("aorta.nii.gz",)` | Binary aorta masks tried first. |
| `total_mask_filenames` | no | `("total.nii.gz",)` | Fallback multiclass total masks. |
| `total_aorta_labels` | no | `(52,)` | Label IDs counted as aorta in `total.nii.gz`; verify against your local label map. |
| `thoracic_mask_filename` | no | `"thoracic_cavity.nii.gz"` | Optional binary thoracic mask. |
| `abdominal_mask_filename` | no | `"abdominal_cavity.nii.gz"` | Optional binary abdominal mask. |
| `body_region_mask_filename` | no | `"body-regions.nii.gz"` | Multiclass body-region fallback. |
| `body_region_labels` | no | thoracic `3`, abdominal `4` | Body-region labels used when separate masks are absent. |
| `iliac_glob` | no | `"*iliac*.nii.gz"` | Glob used to discover iliac masks. |
| `include_iliac` | no | `True` | Add iliac-extension and total-aortoiliac features. |
| `missing_value` | no | `numpy.nan` | Value for unavailable optional regions. |

Returns one flat feature dictionary or `None` when CT or aorta inputs are unavailable.

Generated feature groups include:

```text
aortic_calcification_total_aorta_calcified_volume_ml
aortic_calcification_total_aorta_calcium_voxel_count
aortic_calcification_total_aorta_calcium_max_hu
aortic_calcification_total_aorta_calcium_mean_hu
aortic_calcification_total_aorta_normalized_calcified_volume
aortic_calcification_thoracic_aorta_*
aortic_calcification_abdominal_aorta_*
aortic_calcification_iliac_extension_*
aortic_calcification_total_aortoiliac_*
```

### Batch Helpers

| Function | Purpose |
| --- | --- |
| `extract_cohort_body_region_features(cohort_folder_or_cases, num_workers=1, show_progress=True, **kwargs)` | Body-region and SMA features for many patients. |
| `extract_cohort_total_features(cohort_folder_or_cases, num_workers=1, show_progress=True, **kwargs)` | Organ features for many patients. |
| `extract_experimental_cohort_aortic_calcification_features(cohort_folder_or_cases, num_workers=1, show_progress=True, **kwargs)` | Experimental aortic calcification features for many patients. |
| `extract_boa_features(cohort_folder_or_cases, include_body_regions=True, include_total=True, ...)` | Extract both feature families and outer-merge on `download_id`. |

`cohort_folder_or_cases` may be a cohort root folder, a single patient folder, or a list of patient folders. Set `num_workers` above `1` for multiprocessing.

## Return Values

| Output family | Example columns | Source |
| --- | --- | --- |
| Body-region volumes | `abdominal_cavity_muscle_sum_ml`, `thoracic_cavity_vat_sum_ml` | `bca-measurements.json` `measurements_no_extremities` |
| Derived ratios | `abdominal_cavity_sarcopenia_index_si`, `thoracic_cavity_eat_pat_ratio` | computed from body-region volume columns |
| Vertebral slice markers | `l3_sma_cm2`, `l3_imat_area_cm2`, `l3_vati` | segmentation masks and image spacing |
| Total organ metrics | `liver_total`, `liver_hu`, `liver_cnr` | `total-measurements.json` |
| Organ ratios | `spleen_liver_ratio` | computed from total organ metrics |
| Experimental calcification | `aortic_calcification_total_aorta_calcified_volume_ml` | CT volume and vascular masks |

## CLI Workflow

Use the CLI for cohort-wide extraction jobs that should produce a single auditable CSV.

```bash
fyron boa-extract \
  --cohort-folder /data/boa-cohort \
  --output boa_features.csv \
  --include-body-regions \
  --include-total \
  --include-aortic-experimental \
  --num-workers 8
```

Flags map to feature families:

| Flag | Adds |
| --- | --- |
| `--include-body-regions` | tissue volumes, derived ratios, L3 SMA/IMATI/VATI markers |
| `--include-total` | organ volumes, HU, CNR, organ ratios |
| `--include-aortic-experimental` | experimental aortic/iliac calcification features |

## Discover Completed Cases

```python
from fyron.boa_extraction import discover_boa_cases

cases = discover_boa_cases("/data/boa-cohort")
len(cases)
cases[:3]
```

## Extract One Patient

```python
from fyron.boa_extraction import (
    extract_body_region_features,
    extract_total_segmentation_features,
)

case = "/data/boa-cohort/patient0001"

body_row = extract_body_region_features(
    case,
    include_sma=True,
    sma_segmentation_filename=("tissues.nii.gz",),
    sma_label=1,
    slice_levels=("l3",),
)

total_row = extract_total_segmentation_features(case)
```

Use single-case extraction when validating a new BOA export format. Inspect `body_row.keys()` and compare a few values against the original JSON before launching a full cohort job.

## Experimental Aortic Calcification Extraction

Use this when a BOA-style folder contains a CT volume in HU and vascular masks. Fyron first tries `aorta.nii.gz`; if that is missing, it can use `total.nii.gz` with configurable aorta labels. Thoracic and abdominal aortic burden is calculated by intersecting the aorta mask with thoracic/abdominal body-region masks when available. Iliac-extension burden is calculated from masks matching `*iliac*.nii.gz`.

```python
from fyron.boa_extraction import extract_experimental_aortic_calcification_features

row = extract_experimental_aortic_calcification_features(
    case_folder_or_masks_dir="/data/boa-cohort/patient0001",
    ct_path="/data/boa-cohort/patient0001/ct.nii.gz",
    masks_dir="/data/boa-cohort/patient0001",
    hu_threshold=130,
    total_aorta_labels=(52,),
)
```

For a cohort:

```python
from fyron.boa_extraction import extract_experimental_cohort_aortic_calcification_features

aortic = extract_experimental_cohort_aortic_calcification_features(
    "/data/boa-cohort",
    num_workers=8,
    show_progress=True,
)

aortic.to_csv("experimental_aortic_calcification_features.csv", index=False)
```

Before modeling, inspect several cases visually with the BOA visualization tools and check that `aorta.nii.gz`, `total.nii.gz`, and any iliac masks use the expected label convention.

## Extract A Cohort Table

```python
from fyron.boa_extraction import extract_boa_features

features = extract_boa_features(
    "/data/boa-cohort",
    num_workers=8,
    show_progress=True,
)

features.to_csv("boa_features.csv", index=False)
```

The returned DataFrame contains one row per retained `download_id`. Duplicate case basenames are rejected before extraction; feature-family joins validate one-to-one keys. Missing or malformed measurement inputs are omitted, while missing individual values use `missing_value` (default `NaN`). If no family returns data, the result is an empty DataFrame without a guaranteed column schema. Use `return_report=True` to inspect omissions and the [coverage checks](boa.md#check-coverage-before-joining) before joining. Body-region columns follow this pattern:

```text
abdominal_cavity_muscle_sum_ml
thoracic_cavity_vat_sum_ml
l3_sma
l3_sma_cm2
l3_imati
l3_vati
abdominal_cavity_sarcopenia_index_si
abdominal_cavity_myosteatosis_fat_index_mfi
abdominal_cavity_visceral_fat_index_vfi
thoracic_cavity_eat_pat_ratio
```

Total segmentation columns follow this pattern:

```text
liver_total
liver_hu
liver_cnr
spleen_liver_ratio
```

## Customize Labels And Feature Families

```python
features = extract_boa_features(
    "/data/boa-cohort",
    body_region_kwargs={
        "body_regions": ["abdominal_cavity", "thoracic_cavity", "l3"],
        "tissues": ["bone", "muscle", "tat", "imat", "eat", "pat", "vat", "sat"],
        "vertebrae": ["l3"],
        "sma_segmentation_filename": ("tissues.nii.gz",),
        "sma_label": 1,
        "slice_levels": ("l3",),
        "slice_tissue_labels": {
            "sma": 1,
            "imat": 5,
            "vat": 4,
            "sat": 3,
        },
    },
    total_kwargs={
        "labels": {"spleen": 1, "liver": 5, "pancreas": 10},
        "ratios": [("spleen", "liver")],
    },
    num_workers=8,
)
```

This is useful when you want a compact feature table for modeling instead of the full default set.

## Customize Derived Markers

Derived markers are plain dictionaries. This makes the feature set easy to adjust when a project uses different body-region names or wants only selected formulas.
Use `multiplier` for scaled indices such as percent-style fat indices.

```python
custom_markers = [
    {
        "name": "sarcopenia_index_si",
        "numerator": "muscle",
        "denominator": "bone",
        "regions": ["l3", "abdominal_cavity"],
    },
    {
        "name": "eat_pat_ratio",
        "numerator": "eat",
        "denominator": "pat",
        "regions": ["thoracic_cavity", "ventral_cavity"],
    },
    {
        "name": "myosteatosis_fat_index_mfi",
        "numerator": "imat",
        "denominator": "tat",
        "regions": None,
        "multiplier": 100,
    },
]

row = extract_body_region_features(
    case,
    body_regions=["thoracic_cavity", "ventral_cavity", "abdominal_cavity", "l3"],
    tissues=["bone", "muscle", "tat", "imat", "eat", "pat"],
    derived_markers=custom_markers,
)
```

Set `include_derived_markers=False` when you only want raw tissue volumes.

## Join With Clinical Data

```python
clinical = clinical.merge(features, on="download_id", how="left", validate="one_to_one")
```

After joining, use `fyron.cohort` to validate patient identifiers and build survival columns, or use `fyron.ml` for classification workflows.
