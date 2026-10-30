# FHIR DataFrame To Observations

This example converts a reviewed clinical table into FHIR `Observation` resources.

```python
import pandas as pd
from fyron.fhir.mapping import build_observations_from_dataframe, write_fhir_mapping

df = pd.DataFrame(
    {
        "patient_id": ["123", "124"],
        "observation_id": ["hgb-123", "hgb-124"],
        "loinc_code": ["718-7", "718-7"],
        "display": ["Hemoglobin", "Hemoglobin"],
        "value": [13.4, 11.2],
        "unit": ["g/dL", "g/dL"],
    }
)

mapping = {
    "code_col": "loinc_code",
    "code_display_col": "display",
    "code_system": "http://loinc.org",
    "value_col": "value",
    "unit_col": "unit",
}

result = build_observations_from_dataframe(
    df,
    mapping,
    subject_col="patient_id",
    id_col="observation_id",
    bundle_type="collection",
)

write_fhir_mapping(mapping, "outputs/fhir/observation_mapping.json")
```

Review `result["summary"]` and `result["validation"]` before server write-back.
