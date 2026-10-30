# FHIR BOA Measurements To Bundle

This example maps BOA-style body-composition measurements to FHIR observations linked to an imaging study and series.

```python
import pandas as pd
from fyron.fhir.mapping import build_imaging_measurements_from_dataframe

df = pd.DataFrame(
    {
        "patient_id": ["123", "123", "123"],
        "study_uid": ["1.2.3", "1.2.3", "1.2.3"],
        "series_uid": ["1.2.3.4", "1.2.3.4", "1.2.3.4"],
        "measurement_id": ["l3-sma", "vat-volume", "vat-sat-ratio"],
        "measurement": ["L3 skeletal muscle area", "Visceral adipose tissue volume", "VAT/SAT ratio"],
        "value": [123.4, 820.5, 0.74],
        "unit": ["cm2", "ml", "ratio"],
    }
)

mapping = {
    "code_col": "measurement",
    "value_col": "value",
    "unit_col": "unit",
    "model_name": "Fyron BOA extraction",
    "model_endpoint_url": "https://models.example.org/fyron/boa",
}

result = build_imaging_measurements_from_dataframe(
    df,
    mapping,
    subject_col="patient_id",
    study_uid_col="study_uid",
    series_uid_col="series_uid",
    id_col="measurement_id",
)

bundle = result["bundle"]
```

The bundle contains an `ImagingStudy`, one `Observation` per measurement, a grouping `DiagnosticReport`, and `Provenance`.
