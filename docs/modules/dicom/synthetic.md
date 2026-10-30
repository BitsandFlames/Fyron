# Synthetic DICOM/NIfTI Export

`fyron.dicom.synthetic` writes generated or transformed image volumes back to research-friendly files. It is meant for GAN studies, augmentation audits, synthetic cohort experiments, and reproducibility checks where geometry and identifiers must stay explicit.

Use this when the volume is synthetic or derived. Use `fyron.imaging.write_nifti` for ordinary local NIfTI I/O, and use [DICOM SEG](seg.md) when the output is a segmentation object that must reference source DICOM images.

## What This Module Is For

Synthetic image export has two jobs:

- preserve clinically meaningful geometry from original images,
- avoid accidentally writing generated images with real patient identifiers.

The default behavior is intentionally cautious. DICOM outputs get new Study, Series, and SOP Instance UIDs; patient tags are replaced by synthetic values; and the series is marked as derived synthetic data.

## Required Inputs

| Function | Required | Meaning |
| --- | --- | --- |
| `write_synthetic_nifti` | `volume`, `output_path` | 3D array or SimpleITK image plus destination `.nii` / `.nii.gz` |
| `write_synthetic_dicom_series` | `volume`, `output_dir` | 3D volume in `(z, y, x)` order plus output folder |

## Optional Inputs

| Parameter | Function | Default | Description |
| --- | --- | --- | --- |
| `reference_image` | `write_synthetic_nifti` | `None` | SimpleITK image or path whose geometry is copied. |
| `spacing`, `origin`, `direction` | `write_synthetic_nifti` | `None` | Explicit geometry overrides. |
| `dtype` | `write_synthetic_nifti` | `"float32"` | Output image pixel type. |
| `metadata` | `write_synthetic_nifti` | `None` | Extra SimpleITK metadata fields, when the target image format preserves them. |
| `reference_dicom_dir` | `write_synthetic_dicom_series` | `None` | Original DICOM folder used for geometry. |
| `reference_datasets` | `write_synthetic_dicom_series` | `None` | pydicom datasets or paths used for geometry. |
| `patient_id` | `write_synthetic_dicom_series` | `"SYNTHETIC"` | Synthetic PatientID written by default. |
| `copy_patient_tags` | `write_synthetic_dicom_series` | `False` | Explicit opt-in to copy patient tags from references. |
| `intensity_mode` | `write_synthetic_dicom_series` | `"hu"` | `"hu"` applies rescale slope/intercept; `"raw"` stores raw intensities. |

## Returned Outputs

`write_synthetic_nifti` returns the resolved output `Path`.

`write_synthetic_dicom_series` returns a manifest DataFrame with one row per slice:

| Column | Meaning |
| --- | --- |
| `slice_index` | zero-based volume slice index |
| `path` | written DICOM file |
| `sop_instance_uid` | generated SOP Instance UID |
| `study_instance_uid` | generated or supplied Study UID |
| `series_instance_uid` | generated or supplied Series UID |
| `z_position` | DICOM ImagePositionPatient z value |
| `rows`, `columns` | pixel matrix size |

## Minimal NIfTI Example

```python
import numpy as np
import SimpleITK as sitk

from fyron.dicom.synthetic import write_synthetic_nifti

reference = sitk.ReadImage("original_ct.nii.gz")
generated = np.zeros((128, 256, 256), dtype="float32")

write_synthetic_nifti(
    volume=generated,
    output_path="synthetic_ct.nii.gz",
    reference_image=reference,
    metadata={"generator": "gan_v1"},
)
```

## Minimal DICOM Example

```python
import numpy as np

from fyron.dicom.synthetic import write_synthetic_dicom_series

generated_hu = np.zeros((96, 512, 512), dtype="float32")

manifest = write_synthetic_dicom_series(
    volume=generated_hu,
    output_dir="dicom_synthetic/case_001",
    reference_dicom_dir="dicom_original/case_001",
    patient_id="SYN_CASE_001",
    series_description="Synthetic GAN CT",
)
```

## Clinical Research Example

```python
from fyron.audit import create_provenance_manifest, write_manifest
from fyron.dicom.synthetic import write_synthetic_dicom_series

manifest = write_synthetic_dicom_series(
    volume=gan_volume_hu,
    output_dir="outputs/synthetic_dicom/patient_0001",
    reference_dicom_dir="inputs/original_dicom/patient_0001",
    patient_id="SYN_PATIENT_0001",
    series_description="Synthetic abdomen CT generated for GAN audit",
)

audit = create_provenance_manifest(
    title="Synthetic GAN CT export",
    inputs=["inputs/original_dicom/patient_0001"],
    outputs=manifest["path"].tolist(),
    parameters={
        "intensity_mode": "hu",
        "copy_patient_tags": False,
    },
)

write_manifest(audit, "outputs/synthetic_dicom/patient_0001/manifest.json")
```

## Common Pitfalls

- Generated DICOM slices should not reuse original patient identifiers unless this is explicitly required and ethically approved.
- A synthetic DICOM series is not a DICOM SEG. Use `fyron.dicom.seg` for masks.
- For HU-like CT data, keep `intensity_mode="hu"` so `RescaleIntercept` and `RescaleSlope` describe the stored pixel values.
- If reference geometry is missing, the writer uses simple axial geometry. That is useful for simulations, not for source-linked clinical export.

## Function Table

| Function | Purpose |
| --- | --- |
| `write_synthetic_nifti(volume, output_path, ...)` | Write synthetic volume to `.nii` / `.nii.gz`. |
| `write_synthetic_dicom_series(volume, output_dir, ...)` | Write synthetic volume as a DICOM slice series and return a manifest. |

## Related Modules

- [DICOM](../../dicom/index.html) for DICOMweb acquisition.
- [DICOM SEG](seg.md) for standards-compliant segmentation objects.
- [Imaging](../../imaging/index.html) for local DICOM/NIfTI reading and normalization.
- [Audit & Provenance](../../audit/index.html) for recording generated outputs.
