# Datasets

`fyron.datasets` prepares practical dataset folders for clinical imaging AI workflows. It includes tiny synthetic demo data helpers and first-class preparation helpers for nnU-Net v2 segmentation, YOLO classification, and YOLO object detection.

Use this module when your cohort table already identifies local image files, masks, classes, boxes, and train/validation/test splits, and you need a reproducible folder structure with a manifest.

## Choose a Dataset Workflow

| Task | Preparation guide | Runnable example |
| --- | --- | --- |
| 3D image segmentation | [nnU-Net v2](#nnu-net-v2-preparation) | [Synthetic nnU-Net dataset](../examples/dataset-preparation.md#nnu-net-v2-dataset) |
| One class per image or slice | [YOLO classification](#yolo-classification-preparation) | [Synthetic classification dataset](../examples/dataset-preparation.md#yolo-classification-dataset) |
| Object detection with bounding boxes | [YOLO detection](#yolo-object-detection-preparation) | [Synthetic detection dataset](../examples/dataset-preparation.md#yolo-detection-dataset) |

Fyron prepares and validates dataset folders. Install and run the training framework separately using its [official documentation and repository](#tools-and-repositories).

## Install

Dataset preparation uses Fyron's base imaging stack:

Synthetic cohorts and NIfTI/nnU-Net preparation import with a base installation.
YOLO conversion of volume slices additionally needs `fyron[visualization]`;
Matplotlib is loaded only for rendering. Existing PNG/JPEG files use a bounded
decoder allowlist for dimension inspection and need no plotting extra.

```bash
uv add fyron
```

For a full local research environment:

```bash
uv add "fyron[all]"
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| manifest | DataFrame, CSV, or JSON table describing image paths, labels, classes, boxes, and splits. |
| split | `train`, `val`, or `test`; validation rows follow the target framework's expected folder layout. |
| copy mode | `copy`, `symlink`, or explicit `move`; default is `copy`. |
| conversion | NIfTI and DICOM can be converted into the target folder shape when needed. |
| output manifest | DataFrame recording source paths, written paths, split, status, and errors. |

## API Contract

Manifest identifiers must be nonmissing and output identifiers unique. Class names that collide after filename sanitization are rejected. YOLO annotations grouped under one sample must share the same image and split; partially missing boxes are errors, while four missing coordinates represent an image without boxes. Supplied dimensions must match the image.

With validation enabled, nnU-Net image/mask pairs must match in size, spacing, origin, and direction before any source files are moved. This helper writes channel 0 only. Uncompressed NIfTI inputs are compressed when written as `.nii.gz`.

Existing dataset metadata requires explicit `overwrite=True`. Individual output files are staged before publication; failed copies preserve existing files, and copying a file onto itself is rejected. A multi-file dataset preparation is not a transaction: a later failure can leave earlier completed files. Inspect the returned manifest and use a new output directory for each dataset build.

| Topic | Contract |
| --- | --- |
| Input shape | DataFrame, CSV, or JSON manifest describing images, labels, classes, boxes, case IDs, and splits. |
| Required columns/files | nnU-Net needs case/image/split and train/val labels; YOLO classification needs image/class/split; YOLO detection needs image/split/class/bounding-box columns. |
| Return shape | Output manifest DataFrame with source paths, written paths, split, status, and errors. |
| Saved artifacts | nnU-Net folders and `dataset.json`; YOLO image/label folders and `data.yaml`; dataset manifests. |
| Failure modes | Missing columns/files, invalid splits, unsupported image formats, malformed boxes, shape mismatches, overwrite conflicts, or conversion failures. |

## nnU-Net v2 Preparation

Use `prepare_nnunetv2_dataset` when you have 3D images and segmentation masks that should be trained with nnU-Net v2.

Fyron creates:

```text
Dataset501_LungTumor/
  imagesTr/
    case_0001_0000.nii.gz
  labelsTr/
    case_0001.nii.gz
  imagesTs/
    case_0002_0000.nii.gz
  dataset.json
```

The image suffix `_0000` is the nnU-Net channel suffix for channel 0. Label files do not include the channel suffix.

```python
import pandas as pd
from fyron.datasets import prepare_nnunetv2_dataset

manifest = pd.DataFrame(
    {
        "case_id": ["case_0001", "case_0002"],
        "split": ["train", "test"],
        "image_path": ["images/case_0001_ct.nii.gz", "images/case_0002_ct.nii.gz"],
        "label_path": ["masks/case_0001_mask.nii.gz", ""],
    }
)

written = prepare_nnunetv2_dataset(
    manifest,
    output_dir="datasets/nnunet",
    dataset_id=501,
    dataset_name="LungTumor",
)
```

### Parameters

| Parameter | Meaning |
| --- | --- |
| `dataset_id` | Numeric nnU-Net dataset ID; written as `DatasetXXX_Name`. |
| `dataset_name` | Dataset name sanitized into the output folder. |
| `image_col` | Manifest column with NIfTI file paths or DICOM series folders. |
| `label_col` | Manifest column with segmentation masks; required for `train` and `val`. |
| `case_id_col` | Stable case identifier used in output filenames. |
| `channel_names` | Optional channel mapping for `dataset.json`, default `{0: "CT"}`. |
| `labels` | Optional label mapping for `dataset.json`, default background/foreground. |

### Research Decisions

- Fyron does not resample images or masks for nnU-Net. Align them before calling the preparation helper.
- DICOM input is converted to NIfTI with SimpleITK using the first discovered series.
- `train` and `val` rows both go into nnU-Net's training folders. Keep your split table as the source of truth for cross-validation.
- Official references: [nnU-Net v2 dataset format](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/dataset_format.md) and [nnU-Net GitHub repository](https://github.com/MIC-DKFZ/nnUNet).

## YOLO Classification Preparation

Use `prepare_yolo_classification_dataset` when each image or slice has one class label.

Fyron creates:

```text
yolo_cls/
  train/
    benign/
      case_001.png
    malignant/
      case_002.png
  val/
    benign/
      case_003.png
```

```python
from fyron.datasets import prepare_yolo_classification_dataset

written = prepare_yolo_classification_dataset(
    "cohort.csv",
    output_dir="datasets/yolo_cls",
    image_col="image_path",
    class_col="class",
    split_col="split",
    sample_id_col="patient_id",
)
```

### Image Inputs

| Input | Behavior |
| --- | --- |
| `.png`, `.jpg`, `.jpeg` | copied into `split/class/`. |
| DICOM file or DICOM series folder | converted to axial PNG slice(s). |
| NIfTI volume | converted to axial PNG slice(s). |

For 3D input, `nifti_slice="middle"` writes one representative axial slice. Use `nifti_slice="all"` only when every slice should become a training image.

Official references: [Ultralytics YOLO classification datasets](https://docs.ultralytics.com/datasets/classify/) and [Ultralytics GitHub repository](https://github.com/ultralytics/ultralytics).

## YOLO Object Detection Preparation

Use `prepare_yolo_detection_dataset` when each image can have zero or more bounding boxes.

Fyron creates:

```text
yolo_det/
  images/train/
    case_001.png
  labels/train/
    case_001.txt
  data.yaml
```

YOLO label rows use normalized `xywh`:

```text
class_id x_center y_center width height
```

```python
from fyron.datasets import prepare_yolo_detection_dataset

written = prepare_yolo_detection_dataset(
    "boxes.csv",
    output_dir="datasets/yolo_det",
    image_col="image_path",
    class_col="class",
    bbox_cols=("x_min", "y_min", "x_max", "y_max"),
    split_col="split",
    sample_id_col="image_id",
)
```

### Box Rules

- Input boxes are pixel `xyxy` by default: `x_min`, `y_min`, `x_max`, `y_max`.
- Fyron converts boxes to normalized YOLO `xywh`.
- Multiple rows for the same image become multiple lines in the same label file.
- If a row has an image but empty box values, Fyron writes an empty label file for a negative image.
- Class IDs are zero-indexed and written to `data.yaml`.

Official references: [Ultralytics YOLO detection datasets](https://docs.ultralytics.com/datasets/detect/) and [Ultralytics GitHub repository](https://github.com/ultralytics/ultralytics).

## CLI

### nnU-Net v2 CLI

```bash
fyron dataset-nnunetv2 \
  --manifest cohort.csv \
  --output-dir datasets/nnunet \
  --dataset-id 501 \
  --dataset-name LungTumor \
  --image-col image_path \
  --label-col label_path \
  --case-id-col case_id \
  --split-col split
```

### YOLO Classification CLI

```bash
fyron dataset-yolo-classify \
  --manifest cohort.csv \
  --output-dir datasets/yolo_cls \
  --image-col image_path \
  --class-col label \
  --split-col split
```

### YOLO Detection CLI

```bash
fyron dataset-yolo-detect \
  --manifest boxes.csv \
  --output-dir datasets/yolo_det \
  --image-col image_path \
  --class-col class \
  --bbox-cols x_min,y_min,x_max,y_max \
  --split-col split
```

## Validation

```python
from fyron.datasets import validate_nnunetv2_dataset, validate_yolo_dataset

nnunet_qc = validate_nnunetv2_dataset("datasets/nnunet/Dataset501_LungTumor")
yolo_qc = validate_yolo_dataset("datasets/yolo_det", task="detect")
```

Validation returns a DataFrame with `path`, `check`, `status`, and `message`.

## Tools and Repositories

| Tool | Documentation | Source code |
| --- | --- | --- |
| nnU-Net v2 | [Dataset format and naming](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/dataset_format.md) | [MIC-DKFZ/nnUNet](https://github.com/MIC-DKFZ/nnUNet) |
| Ultralytics YOLO | [Classification format](https://docs.ultralytics.com/datasets/classify/) · [Detection format](https://docs.ultralytics.com/datasets/detect/) | [ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) |
| Fyron | [Dataset preparation example](../examples/dataset-preparation.md) · [Imaging QC](imaging.md#imaging-qc-helpers) | [BitsandFlames/Fyron](https://github.com/BitsandFlames/Fyron) |

For existing segmentation outputs, see [BOA CT and BOA MR](boa.md#upstream-tools-and-repositories). For image selection before dataset preparation, see [Curate](../applications/curate.md#review-workflow).

## Related Modules

- [Imaging](imaging.md) for DICOM/NIfTI reading and geometry checks.
- [DICOMDownloader](dicom/downloader.md) for acquiring source DICOM or NIfTI from DICOMweb.
- [DICOM SEG](dicom/seg.md) for source-referenced segmentation export.
- [Clinical AI Study Workflow](../clinical-ai-study-workflow.md) for study-level artifacts and provenance.

## Review prepared images

Use [Curate data preparation](../applications/curate/prepare-data.md) for upload formats, folder layouts, and CT/MRI preview examples, then follow [Review & export](../applications/curate/review-export.md).
