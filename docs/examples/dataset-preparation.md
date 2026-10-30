# Dataset Preparation

This example prepares three common imaging AI dataset structures from synthetic local files:

- [nnU-Net v2 segmentation](#nnu-net-v2-dataset)
- [YOLO classification](#yolo-classification-dataset)
- [YOLO object detection](#yolo-detection-dataset)

The example uses synthetic data only. Replace the manifest paths with reviewed local files from your study.

See the [dataset workflow guide](../modules/datasets.md#choose-a-dataset-workflow) for input requirements and [official tool repositories](../modules/datasets.md#tools-and-repositories) for framework installation and training.

## Create Synthetic Files

```python
import pandas as pd
from fyron.datasets import make_nifti_pair, make_dicom_series

pair_a = make_nifti_pair("scratch/case_a")
pair_b = make_nifti_pair("scratch/case_b")
make_dicom_series("scratch/case_c_dicom", shape=(4, 8, 8))
```

## nnU-Net v2 Dataset

```python
from fyron.datasets import prepare_nnunetv2_dataset

nnunet_manifest = pd.DataFrame(
    {
        "case_id": ["case_a", "case_b", "case_c"],
        "split": ["train", "val", "test"],
        "image_path": [pair_a["image"], pair_b["image"], "scratch/case_c_dicom"],
        "label_path": [pair_a["mask"], pair_b["mask"], ""],
    }
)

nnunet_written = prepare_nnunetv2_dataset(
    nnunet_manifest,
    output_dir="datasets/nnunet",
    dataset_id=501,
    dataset_name="DemoTumor",
)
```

Result:

```text
datasets/nnunet/Dataset501_DemoTumor/
  imagesTr/case_a_0000.nii.gz
  labelsTr/case_a.nii.gz
  imagesTs/case_c_0000.nii.gz
  dataset.json
```

## YOLO Classification Dataset

```python
from fyron.datasets import prepare_yolo_classification_dataset

classification_manifest = pd.DataFrame(
    {
        "patient_id": ["case_a", "case_b", "case_c"],
        "split": ["train", "val", "test"],
        "image_path": [pair_a["image"], pair_b["image"], "scratch/case_c_dicom"],
        "class": ["benign", "malignant", "benign"],
    }
)

yolo_cls = prepare_yolo_classification_dataset(
    classification_manifest,
    output_dir="datasets/yolo_cls",
    sample_id_col="patient_id",
    nifti_slice="middle",
)
```

Result:

```text
datasets/yolo_cls/
  train/benign/case_a_z0002.png
  val/malignant/case_b_z0002.png
  test/benign/case_c_z0002.png
```

## YOLO Detection Dataset

```python
from fyron.datasets import prepare_yolo_detection_dataset

boxes = pd.DataFrame(
    {
        "image_id": ["case_a", "case_a", "case_b"],
        "split": ["train", "train", "val"],
        "image_path": [pair_a["image"], pair_a["image"], pair_b["image"]],
        "class": ["lesion", "device", "lesion"],
        "x_min": [1, 4, None],
        "y_min": [1, 4, None],
        "x_max": [5, 7, None],
        "y_max": [5, 7, None],
    }
)

yolo_det = prepare_yolo_detection_dataset(
    boxes,
    output_dir="datasets/yolo_det",
    sample_id_col="image_id",
)
```

Result:

```text
datasets/yolo_det/
  images/train/case_a_z0002.png
  labels/train/case_a_z0002.txt
  images/val/case_b_z0002.png
  labels/val/case_b_z0002.txt
  data.yaml
```

The empty box row for `case_b` creates an empty label file, which YOLO uses for negative images.

## Validate Outputs

```python
from fyron.datasets import validate_nnunetv2_dataset, validate_yolo_dataset

nnunet_qc = validate_nnunetv2_dataset("datasets/nnunet/Dataset501_DemoTumor")
yolo_cls_qc = validate_yolo_dataset("datasets/yolo_cls", task="classify")
yolo_det_qc = validate_yolo_dataset("datasets/yolo_det", task="detect")
```

Keep the returned manifests and validation tables beside the training data so the exact preparation step is reproducible.

## CLI Version

```bash
fyron dataset-nnunetv2 \
  --manifest nnunet_manifest.csv \
  --output-dir datasets/nnunet \
  --dataset-id 501 \
  --dataset-name DemoTumor
```

```bash
fyron dataset-yolo-classify \
  --manifest classification_manifest.csv \
  --output-dir datasets/yolo_cls \
  --sample-id-col patient_id
```

```bash
fyron dataset-yolo-detect \
  --manifest boxes.csv \
  --output-dir datasets/yolo_det \
  --sample-id-col image_id
```

## Related Modules

- [Datasets](../modules/datasets.md)
- [Imaging](../modules/imaging.md)
- [DICOMDownloader](../modules/dicom/downloader.md)
