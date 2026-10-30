# DICOM SEG Export

This example writes a model segmentation as a DICOM SEG object. Use this when masks must stay connected to original DICOM images and be readable by DICOM-aware viewers.

## Install

```bash
uv add "fyron[dicom-seg]"
```

```bash
uv add "fyron[dicom-seg]"
```

## Example

```python
from pathlib import Path

import numpy as np
from fyron.dicom.seg import load_source_dicom_series, summarize_dicom_seg, write_dicom_seg

dicom_dir = Path("data/case_001/source_dicom")
source_images = load_source_dicom_series(dicom_dir)

label_map = np.load("outputs/case_001/organ_labels.npy")

seg_path = write_dicom_seg(
    mask=label_map,
    source_images=source_images,
    output_path="outputs/case_001/organs.seg.dcm",
    segment_descriptions=[
        {"label": "spleen", "label_value": 1},
        {"label": "liver", "label_value": 5},
        {"label": "pancreas", "label_value": 10},
    ],
    series_description="Fyron organ segmentation",
    algorithm_name="Fyron organ model",
)

info = summarize_dicom_seg(seg_path, source_images=source_images)
print(info["number_of_segments"])
print(info["segment_labels"])
```

## Notes

- The mask must be aligned with the source image order.
- `load_source_dicom_series` sorts by geometry first, then instance number, then path.
- A DICOM SEG is for segmentation masks, not generated CT intensities.
- Segment labels should be clinically meaningful and stable across exports.
