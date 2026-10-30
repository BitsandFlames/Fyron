# FHIR LLM Table To Bundle

This example starts from a reviewed LLM extraction table. The table is converted into FHIR `Condition` resources with evidence links back to source `DocumentReference` resources.

```python
import pandas as pd
from fyron.fhir.mapping import build_conditions_from_dataframe

df = pd.DataFrame(
    {
        "patient_id": ["123"],
        "condition_id": ["condition-lung-cancer-123"],
        "icd10": ["C34"],
        "label": ["Malignant neoplasm of bronchus and lung"],
        "source_document": ["DocumentReference/report-123"],
    }
)

mapping = {
    "condition_code_col": "icd10",
    "condition_code_display_col": "label",
    "condition_code_system": "http://hl7.org/fhir/sid/icd-10",
    "evidence_col": "source_document",
}

result = build_conditions_from_dataframe(
    df,
    mapping,
    subject_col="patient_id",
    id_col="condition_id",
)

print(result["validation"])
```

If the referenced `DocumentReference` is not included in the same bundle, Fyron reports it as a missing local reference. Keep that warning visible during review.
