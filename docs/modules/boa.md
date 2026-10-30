# BOA

BOA outputs are a starting point for research, not yet a finished analysis table. Fyron helps you turn those outputs into inspectable features, review the masks behind them, and connect imaging cases to a clinical cohort. It consumes existing Body-and-Organ-Analysis outputs; these helpers do not run the upstream BOA segmentation pipeline.

Fyron organizes this work into three focused submodules:

- `fyron.boa_extraction` turns BOA cohort folders into case-level feature tables.
- `fyron.boa_radiomics` extracts PyRadiomics texture and shape features from BOA masks.
- `fyron.visualization` turns BOA CT and segmentation folders into review collages.

Keeping the Python modules separate is intentional. Extraction creates measurement features from JSON outputs. Radiomics creates texture and shape features from image-mask pairs. Visualization creates images for quality control, reports, and publication figures. They often use the same patient folders, but they have different outputs, dependencies, and failure modes.

Radiomics extraction reports mark labels and cases as partial when the extractor returns no measurements or nonfinite numeric measurements. Label identifiers and diagnostic metadata alone do not count as successful extraction.

## Upstream Tools and Repositories

BOA CT and BOA MR are developed by the SHIP-AI group at University Medicine Essen and the Institute for Artificial Intelligence in Medicine (IKIM). Their official repositories provide installation instructions, model details, and citation guidance.

| Tool | Purpose | Official repository and documentation |
| --- | --- | --- |
| BOA CT | Body and organ analysis of CT scans, combining organ segmentation and body-composition analysis | [UMEssen/Body-and-Organ-Analysis](https://github.com/UMEssen/Body-and-Organ-Analysis) |
| BOA MR | Body-composition analysis of T2-weighted MRI | [UMEssen/BOA-MR](https://github.com/UMEssen/BOA-MR) |
| TotalSegmentator | Anatomical segmentation, used within the BOA CT workflow | [wasserth/TotalSegmentator](https://github.com/wasserth/TotalSegmentator) |
| PyRadiomics | Feature extraction from images and masks | [AIM-Harvard/pyradiomics](https://github.com/AIM-Harvard/pyradiomics) · [Documentation](https://pyradiomics.readthedocs.io/en/latest/) |

Run the upstream tool to create segmentations and measurements, then use the matching Fyron workflow below. The examples on this page document **BOA CT output conventions**. BOA MR is a separate upstream project; its presence here does not establish compatibility with Fyron's CT measurement schemas, tissue labels, or HU-based features. For MR images and masks, start with [imaging QC](imaging.md#imaging-qc-helpers) and [generic segmentation visualization](visualization.md#generic-segmentation-collage), with explicit geometry and label checks.

### Choose a Fyron Workflow

- [Measurement extraction](boa-extraction.md#extract-a-cohort-table): combine existing BOA measurements into a cohort table.
- [Body-region radiomics](boa-radiomics.md#extract-body-region-radiomics): select regions for image-mask feature extraction.
- [Segmentation collages](visualization.md#basic-multi-patient-collage): review CT images and overlay masks.
- [Training datasets](datasets.md#choose-a-dataset-workflow): prepare reviewed images and labels for nnU-Net v2 or YOLO.

## BOA Folder Pattern

Use one folder per imaging case. A case can represent a study or series, and one patient can have several cases. The names below are illustrative; do not use a patient identifier as the only key for repeated imaging.

```text
boa-cohort/
  patient0001/
    bca-measurements.json
    total-measurements.json
    ct.nii.gz
    body-regions.nii.gz
    tissues.nii.gz
    total.nii.gz
  patient0002/
    bca-measurements.json
    total-measurements.json
    ct.nii.gz
    body-regions.nii.gz
    tissues.nii.gz
    total.nii.gz
```

The final folder name is used as `download_id` by default in extraction, and as the row label source in visualization unless you pass explicit labels. Folder basenames must be unique across the selected cohort, even if folders live under different parent directories. Discovery does not enforce this.

Keep a separate mapping from `download_id` to your patient, study, series, and acquisition date. Decide which examination belongs in the analysis before joining patient-level outcomes. Fyron does not automatically select a baseline scan or resolve repeated examinations.

## Installation

```bash
uv add fyron
uv add "fyron[visualization]"
```

The base package provides measurement extraction. Add `visualization` for collages. Radiomics is optional and uses `fyron[radiomics]`; follow the [radiomics installation guidance](boa-radiomics.md#install) and [compatibility notes](../reliability.md) before creating that environment. It currently requires a separate Python 3.11 setup in Fyron's supported radiomics workflow, not Python 3.12.

## Inputs By Task

| Task | Inputs | Important boundary |
| --- | --- | --- |
| Body-composition volumes and ratios | `bca-measurements.json` with an `aggregated` mapping | Reads `measurements_no_extremities`; missing measurements are not zero. |
| Vertebral slice areas | BCA vertebral slice indices and a correctly labeled segmentation | Verify label meanings and alignment with the exported slice indices. |
| Organ measurements | `total-measurements.json` with `segmentations.total` | Reads existing `volume_ml`, `mean_hu`, and `cnr`; does not recompute them from CT. |
| Radiomics | CT image and selected segmentation mask | Requires valid geometry, label definitions, and explicit extraction settings. |
| Review collages | CT and the selected overlay masks | A visual QC aid, not an automated segmentation-quality verdict. |

Not every task needs every file shown above. In particular, JSON-only extraction can run with `include_sma=False` without loading segmentation masks.

## Try It Without Patient Data

This self-contained example creates a small synthetic BOA-like folder in a temporary directory. The fixture is for API testing, not anatomical or clinical validation. It does not provide total-organ measurements.

```python
from tempfile import TemporaryDirectory

from fyron.datasets import make_boa_like_folder
from fyron.boa_extraction import extract_boa_features

with TemporaryDirectory() as directory:
    root = make_boa_like_folder(directory)
    features = extract_boa_features(
        root,
        include_body_regions=True,
        include_total=False,
        body_region_kwargs={"include_sma": False},
        num_workers=1,
        show_progress=False,
    )
    assert len(features) == 1
    assert features.loc[0, "abdominal_cavity_muscle_sum_ml"] == 101.0
    print(features[["download_id", "abdominal_cavity_muscle_sum_ml"]])
```

## Choose The Right Submodule

| Goal | Use | Output |
| --- | --- | --- |
| Find folders containing a measurement file | `fyron.boa_extraction.discover_boa_cases` | list of case folder paths, not a completion audit |
| Extract body-region tissue volumes | `fyron.boa_extraction.extract_body_region_features` | feature dictionary or DataFrame |
| Extract organ volume, HU, CNR, ratios | `fyron.boa_extraction.extract_total_segmentation_features` | feature dictionary or DataFrame |
| Extract experimental aortic calcification burden | `fyron.boa_extraction.extract_experimental_aortic_calcification_features` | feature dictionary or DataFrame |
| Build one modeling table from BOA outputs | `fyron.boa_extraction.extract_boa_features` | `pandas.DataFrame` |
| Extract radiomics from `total.nii.gz` or `body-regions.nii.gz` | `fyron.boa_radiomics.extract_boa_radiomics_features` | case-level radiomics DataFrame |
| Create visual QC collages | `fyron.visualization.create_boa_segmentation_collage` | PNG and metadata |
| Configure collage layers | `fyron.visualization.SegmentationLayer` | layer configuration object |

## Typical Clinical Data Science Workflow

```python
from fyron.boa_extraction import discover_boa_cases, extract_boa_features
from fyron.boa_radiomics import extract_boa_radiomics_features
from fyron.visualization import create_boa_segmentation_collage

root = "/data/boa-cohort"
cases = sorted(set(discover_boa_cases(root)) | set(
    discover_boa_cases(root, measurement_filename="total-measurements.json")
))
if not cases:
    raise ValueError("No measurement files discovered.")
if len({case.name for case in cases}) != len(cases):
    raise ValueError("Case folder names must be unique before extraction.")

features = extract_boa_features(
    cases,
    num_workers=1,
    show_progress=True,
)

features.to_csv("boa_features.csv", index=False)

radiomics = extract_boa_radiomics_features(
    cases,
    segmentation_kind="total",
    labels={"liver": 5, "spleen": 1},
    num_workers=1,
    on_error="raise",
)

create_boa_segmentation_collage(
    boa_folders=cases[:6],
    output_path="boa_qc.png",
    segmentation_layers=["body_regions", "tissues", "total"],
    slice_fraction=0.5,
)
```

This example assumes the selected cases also contain the CT and masks required for radiomics and visualization. The organ label values are examples, not a guarantee about your export: verify them against its label map. Discovering the union of both measurement filenames avoids dropping total-only cases just because their BCA JSON is absent.

Start with one case and one worker. For a larger run, increase `num_workers` inside a script protected by `if __name__ == "__main__":`. Multiprocessing output order can differ from input order; join on `download_id`, never row position. CT volumes and masks can be large, so choose worker counts according to available memory rather than CPU count alone.

Use measurement and radiomics outputs for cohort joins, survival analysis, ML models, and correlation plots. Use the collage output to inspect whether the segmentations and selected slices are clinically plausible.

## Check Coverage Before Joining

All BOA cohort extraction helpers accept keyword-only `return_report=True`,
including radiomics and experimental aortic extraction:

```python
result = extract_boa_features(cases, return_report=True, num_workers=1)
features = result["data"]
decisions = result["report"]["rows"]
counts = result["report"]["summary"]
```

Default calls still return only the feature DataFrame. Reports record
`download_id`, `case_path`, `family`, optional radiomics `label`, and controlled
`status` values. These are sensitive research outputs, not shareable logs.
Summary counts are grouped by `family`, `scope` (`case` or `label`), and `status`;
do not add case and label counts together as a count of patients.

Statuses distinguish `success`, `partial`, `missing_inputs`,
`invalid_measurements`, `empty_label`, `undersized_label`, and
`extraction_failure`. Not every family produces every status. A partial case
can retain useful measurements. Label rows explain radiomics outcomes separately
from the case-level result; failed labels can leave voxel counts without features.

Explicit case lists are resolved once, including generators, and every requested
case is evaluated for each selected family. Directory discovery uses the union
of the selected measurement filenames; it cannot report cases with no discoverable
measurement file at all. Supply an expected case list when auditing omissions.
Duplicate folder basenames are rejected before extraction. `on_error="raise"`
still raises rather than returning a report after a radiomics failure.

Measurement extraction omits cases for which the selected extractor returns `None`. The combined helper outer-joins available feature families: a case can therefore have body-composition values but missing organ measurements, or the reverse. An output row is not proof that all requested features were extracted.

```python
import pandas as pd

expected = pd.DataFrame({"download_id": [case.name for case in cases]})
if features.empty:
    raise ValueError("No feature rows were extracted.")
if features["download_id"].isna().any() or features["download_id"].duplicated().any():
    raise ValueError("Feature keys are missing or duplicated.")

coverage = expected.merge(
    features, on="download_id", how="left",
    validate="one_to_one", indicator=True,
)
missing_cases = coverage.loc[coverage["_merge"] == "left_only", ["download_id"]]
missingness = features.drop(columns="download_id").isna().mean().sort_values(ascending=False)
```

Review `missing_cases` and feature-level `missingness` before defining exclusions. Keep these tables inside the research environment. File paths, case identifiers, masks, and images can all be sensitive.

When a clinical table has one row per selected imaging case, use an explicitly validated join:

```python
clinical_features = clinical.merge(
    features, on="download_id", how="left", validate="one_to_one",
)
```

Here `clinical` is your already-selected case cohort. For different cardinalities, first use [cohort join auditing](cohort.md) and choose a relationship that matches the study design; do not drop duplicate patients just to make a merge pass.

## Interpret Features Carefully

- Body-region `*_sum_ml` values come from the BOA JSON, not a new volume calculation.
- `<organ>_total` contains `volume_ml`; `<organ>_hu` contains `mean_hu`. Total measurements are rounded to two decimals by default; use `total_kwargs={"round_digits": None}` to retain source precision.
- Slice-area outputs such as `l3_sma_cm2` are in square centimetres. Legacy names such as `l3_smi` are area-based in this implementation, not automatically height-normalized. Only the explicit `*_cm2_per_m2` columns use supplied height. See the [extraction feature definitions](boa-extraction.md).
- A missing value is not evidence of absent tissue, and a derived marker name is not a clinical diagnosis or a validated decision threshold.
- Radiomics settings, mask resampling, scanner/reconstruction differences, and scan selection belong in the analysis protocol. Feature extraction alone does not establish comparability between cohorts.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No discovered cases | Root path and measurement filename. Discovery searches recursively for that file, not for proof of a completed BOA run. |
| Fewer rows than expected | Missing/malformed JSON, missing required JSON branches, or radiomics inputs skipped under `on_error="skip"`. Compare expected IDs with returned IDs. |
| Many missing feature values | Requested region/organ names, export schema, absent labels, missing slice masks, and unsupported slice indices. |
| Unexpected row multiplication | Duplicate folder basenames or repeated clinical join keys. Validate keys before extraction and merges. |
| Radiomics row but no texture features | Inspect voxel counts and actual feature columns; a row may survive with counts only. Use `on_error="raise"` during validation. |
| Grid mismatch | Inspect image/mask geometry. Radiomics resamples masks by default; resampling is not registration and cannot repair a wrong source image. |
| Slow run or excessive memory | Try one case, fewer workers, fewer labels, and a smaller feature set before scaling. |

## Record And Cite The Workflow

Record the Fyron and upstream BOA versions, case-selection rules, feature families,
label map, JSON branch, units, height handling, radiomics settings, resampling,
missing-data decisions, and QC exclusions. Preserve your configuration alongside
the exported table.

If Fyron contributes to scientific work, please cite it using the
[project citation](https://github.com/BitsandFlames/Fyron#citation). Also acknowledge
the upstream BOA, segmentation, and radiomics tools actually used according to
their own citation guidance. Fyron's citation does not replace theirs.

## CLI Workflow

Run BOA feature extraction as a repeatable terminal step when patient folders already exist on disk:

```bash
fyron boa-extract \
  --cohort-folder data/boa \
  --output boa_features.csv \
  --include-body-regions \
  --include-total \
  --num-workers 8
```

Radiomics can be exported from the same folder structure:

```bash
fyron boa-radiomics \
  --cohort-folder data/boa \
  --segmentation total \
  --output boa_radiomics.csv \
  --num-workers 8
```

Experimental aortic calcification is a separate opt-in feature family, enabled
with `--include-aortic-experimental`. Review its assumptions and required masks
on the [extraction page](boa-extraction.md#experimental-aortic-calcification-extraction)
before including it; it is deliberately absent from the standard example above.

## Submodule Documentation

Start with the subpage that matches the task:

- [BOA Extraction](boa-extraction.md) for features, measurements, DataFrames, and model-ready tables.
- [BOA Radiomics](boa-radiomics.md) for PyRadiomics features from `body-regions.nii.gz` and `total.nii.gz`.
- [BOA Visualization](visualization.md) for segmentation collages, CT overlays, slice selection, and body-region cropping.

## Design Boundary

The combined BOA docs page is a workflow map, not a fourth API layer. Keeping the actual package APIs as `fyron.boa_extraction`, `fyron.boa_radiomics`, and `fyron.visualization` prevents ambiguous function names and keeps imports explicit in notebooks:

```python
from fyron.boa_extraction import extract_boa_features
from fyron.boa_radiomics import extract_boa_radiomics_features
from fyron.visualization import create_boa_segmentation_collage
```
