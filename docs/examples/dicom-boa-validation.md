# DICOM And BOA Feature Validation

This tutorial shows the table shape for imaging-derived validation workflows. It uses synthetic rows so the example is readable without a DICOMweb server.

```python
import pandas as pd

from fyron.dicom import DICOMDownloader
from fyron import preprocessing as fp
from fyron import validation as fv

imaging = pd.DataFrame(
    {
        "patient_id": ["p1", "p2", "p3", "p4"],
        "study_instance_uid": ["1.2.1", "1.2.2", "1.2.3", "1.2.4"],
        "series_instance_uid": ["1.3.1", "1.3.2", "1.3.3", "1.3.4"],
        "muscle_volume_ml": [1200, 900, 1400, 800],
        "vat_volume_ml": [300, 600, 250, 700],
        "event": [0, 1, 0, 1],
        "risk_probability": [0.2, 0.8, 0.3, 0.7],
    }
)

imaging["download_id"] = imaging.apply(
    lambda row: DICOMDownloader.download_id(
        row["study_instance_uid"],
        row["series_instance_uid"],
    ),
    axis=1,
)

feature_qc = fp.feature_matrix_report(
    imaging[["muscle_volume_ml", "vat_volume_ml"]],
    imaging["event"],
)

calibration, bins = fv.calibration_summary(
    imaging["event"],
    imaging["risk_probability"],
    n_bins=2,
)
```

For real downloads, use `output_format="nifti", save_reference_dicom=True` when downstream processing runs on NIfTI but a source DICOM header should remain available for metadata and provenance checks.
