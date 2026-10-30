# DICOM SEG

`fyron.dicom.seg` writes segmentation masks as DICOM SEG objects. DICOM SEG is the correct container when a mask must reference original DICOM source images and remain usable in PACS/viewer ecosystems.

This module is intentionally stricter than a simple mask writer. A valid SEG needs source images, segment metadata, frame references, and coded segment descriptions. Fyron uses optional `highdicom` for this because standards-compliant SEG objects should not be hand-assembled casually.

## Installation

```bash
uv add "fyron[dicom-seg]"
```

```bash
uv add "fyron[dicom-seg]"
```

The base package can import `fyron.dicom.seg`, but writing a SEG requires the extra.

## What This Module Is For

- export model or manual segmentation masks as DICOM SEG,
- keep segmentation labels and algorithm metadata explicit,
- link masks back to original DICOM images,
- validate that a file is readable as DICOM Segmentation Storage.

Use [Synthetic Export](synthetic.md) for generated intensity images. Use `fyron.imaging.write_nifti` for simple NIfTI masks that do not need DICOM references.

## Pre-Flight Checklist

Before writing a DICOM SEG, confirm:

- the original DICOM source series is available, not only a NIfTI conversion,
- the mask is aligned to the source image order,
- the mask shape is `(z, y, x)` for a label map or `(segment, z, y, x)` for a binary stack,
- every exported label has a stable clinical name,
- optional coded concepts are explicit when the SEG will be used outside your local workflow.

## Required Inputs

| Function | Required | Meaning |
| --- | --- | --- |
| `write_dicom_seg` | `mask`, `source_images`, `output_path`, `segment_descriptions` | Mask data, original DICOM images, destination file, and segment metadata. |
| `label_map_to_segments` | `label_map`, `labels` | Integer label map and label values to convert. |
| `validate_dicom_seg` | `path` | DICOM SEG file to inspect. |
| `load_source_dicom_series` | `source_dicom_dir` | Source DICOM folder sorted in SEG-safe order. |
| `read_segment_descriptions` | `path` | JSON segment description file. |
| `validate_segment_descriptions` | `segment_descriptions` | Segment metadata list to check before export. |
| `summarize_dicom_seg` | `path` | Validation-style metadata summary for reports/CLI output. |

## Optional Inputs

| Parameter | Default | Description |
| --- | --- | --- |
| `series_description` | `"Fyron DICOM SEG"` | DICOM SeriesDescription for the SEG object. |
| `manufacturer` | `"Bits & Flames"` | Manufacturer tag. |
| `algorithm_type` | `"AUTOMATIC"` | Segment algorithm type for generated masks. |
| `algorithm_name` | `"Fyron"` | Algorithm name in segment metadata. |

## Segment Description Shape

Each segment description is a dictionary. Minimal:

```python
segment_descriptions = [
    {"label": "liver", "label_value": 1},
    {"label": "spleen", "label_value": 2},
]
```

As JSON for the CLI:

```json
[
  {"label": "spleen", "label_value": 1},
  {"label": "liver", "label_value": 5},
  {"label": "pancreas", "label_value": 10}
]
```

With coded concepts:

```python
segment_descriptions = [
    {
        "segment_number": 1,
        "label": "liver",
        "label_value": 1,
        "category": ("T-D0050", "SRT", "Tissue"),
        "type": ("T-62000", "SRT", "Liver"),
        "algorithm_name": "Fyron TotalSegmentator workflow",
        "algorithm_version": "2026.06",
    }
]
```

## Minimal Example

```python
import numpy as np

from fyron.dicom.seg import load_source_dicom_series, write_dicom_seg

source_images = load_source_dicom_series("data/case_001/source_dicom")

label_map = np.zeros((len(source_images), 512, 512), dtype="uint8")
label_map[:, 120:180, 130:210] = 1

write_dicom_seg(
    mask=label_map,
    source_images=source_images,
    output_path="segmentation/liver.seg.dcm",
    segment_descriptions=[
        {"label": "liver", "label_value": 1},
    ],
    series_description="Fyron liver segmentation",
)
```

## BOA Or TotalSegmentator-Style Example

Use this pattern when you have an organ label map from BOA, TotalSegmentator, or a model workflow and want a source-referenced DICOM SEG.

```python
import SimpleITK as sitk

from fyron.dicom.seg import load_source_dicom_series, summarize_dicom_seg, write_dicom_seg

source_images = load_source_dicom_series(
    "original_dicom/case_001",
    sort_by="geometry",
)
label_map = sitk.GetArrayFromImage(sitk.ReadImage("segmentations/total.nii.gz"))

seg_path = write_dicom_seg(
    mask=label_map,
    source_images=source_images,
    output_path="segmentations/case_001.total.seg.dcm",
    segment_descriptions=[
        {"label": "spleen", "label_value": 1},
        {"label": "liver", "label_value": 5},
        {"label": "pancreas", "label_value": 10},
    ],
    series_description="Fyron total segmentation",
    algorithm_name="Fyron BOA/TotalSegmentator workflow",
)

summary = summarize_dicom_seg(seg_path, source_images=source_images)
print(summary["segment_labels"])
```

## Binary Segment Stack Example

```python
from fyron.dicom.seg import label_map_to_segments, write_dicom_seg

segments = label_map_to_segments(
    label_map=organ_label_map,
    labels=[1, 5, 10],
)

write_dicom_seg(
    mask=segments,
    source_images=source_images,
    output_path="segmentation/organs.seg.dcm",
    segment_descriptions=[
        {"label": "spleen"},
        {"label": "liver"},
        {"label": "pancreas"},
    ],
)
```

## Validation Example

```python
from fyron.dicom.seg import summarize_dicom_seg

info = summarize_dicom_seg("segmentation/organs.seg.dcm")

print(info["number_of_segments"])
print(info["segment_labels"])
```

## CLI Workflow

```bash
fyron dicom-seg \
  --mask total.nii.gz \
  --source-dicom original_dicom/case_001 \
  --segments segments.json \
  --output segmentations/case_001.seg.dcm \
  --algorithm-name "Fyron organ model" \
  --validate \
  --summary-json segmentations/case_001.seg.summary.json
```

The CLI uses `load_source_dicom_series(..., sort_by="geometry")` so source slices are sorted by `ImagePositionPatient`, then `InstanceNumber`, then path. This is safer than filename sorting when PACS exports use inconsistent names.

## Common Pitfalls

- DICOM SEG needs source DICOM images. A NIfTI mask alone is not enough to create a source-referenced SEG.
- Keep mask slice order aligned with the source image order.
- Use explicit segment descriptions. A label value like `1` is not scientific metadata.
- Treat model-generated masks as algorithmic outputs, not validated annotations.
- PACS/viewer support varies. Validate the SEG and test one viewer round-trip before scaling a batch export.
- DICOM SEG stores segment metadata, not clinical truth. Keep algorithm name/version and provenance with your analysis.

## Function Table

| Function | Purpose |
| --- | --- |
| `write_dicom_seg(mask, source_images, output_path, segment_descriptions, ...)` | Write a DICOM SEG object. |
| `label_map_to_segments(label_map, labels)` | Convert integer labels to binary segment stack. |
| `validate_dicom_seg(path, source_images=None)` | Read and summarize core SEG metadata. |
| `summarize_dicom_seg(path, source_images=None)` | Return validation metadata for reports or CLI JSON. |
| `load_source_dicom_series(source_dicom_dir, sort_by="geometry")` | Read source DICOM files in deterministic SEG order. |
| `read_segment_descriptions(path)` | Read and validate CLI-style segment JSON. |
| `validate_segment_descriptions(segment_descriptions)` | Validate segment labels, label values, coded concepts, and duplicates. |

## Related Modules

- [DICOM](../../dicom/index.html) for source image acquisition.
- [Synthetic Export](synthetic.md) for generated intensity volumes.
- [Imaging](../../imaging/index.html) for local array/NIfTI work before export.
