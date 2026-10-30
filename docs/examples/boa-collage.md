# Example: BOA Collages

Create a multi-patient BOA segmentation figure with consistent columns and patient labels.

Use this pattern for review slides, quality-control sheets, or manuscript-ready overviews where several patients need to be compared with the same segmentation layers. Keep orientation, slice selection, and crop settings fixed across patients whenever you want visual comparison to be fair.

## Before Exporting Final Figures

- Check that every folder contains the expected CT and segmentation files.
- Confirm the selected orientation matches the clinical anatomy being reviewed.
- Use patient labels that are de-identified for external sharing.
- Inspect one or two individual panels before rendering a large cohort.
- Save the returned metadata next to the exported image.

```python
from fyron.visualization import SegmentationLayer, create_boa_segmentation_collage

result = create_boa_segmentation_collage(
    boa_folders=[
        "/data/boa/patient_a",
        "/data/boa/patient_b",
        "/data/boa/patient_c",
    ],
    output_path="figures/boa_overview.png",
    orientation="axial",
    patient_labels=["Patient A", "Patient B", "Patient C"],
    segmentation_layers=[
        SegmentationLayer("body_regions", display_mode="ct_overlay", opacity=0.5),
        SegmentationLayer("tissues", display_mode="ct_overlay", opacity=0.4),
        SegmentationLayer("total", display_mode="segmentation"),
    ],
    slice_fraction=0.5,
)

result["output_path"]
```

Crop all panels to a body region:

```python
create_boa_segmentation_collage(
    boa_folders=["/data/boa/patient_a", "/data/boa/patient_b"],
    output_path="figures/abdomen_crop.png",
    orientation="axial",
    crop_body_region="Abdominal Cavity",
    body_region_padding_mm=20,
    body_region_slices="best",
)
```
