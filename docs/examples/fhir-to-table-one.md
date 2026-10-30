# FHIR To Cohort To Table One

This tutorial uses synthetic FHIR-like rows to show the analysis shape without needing server credentials.

```python
import pandas as pd

from fyron.cohort import build_time_to_event_endpoint, cohort_profile
from fyron import descriptive as fd

patients = pd.DataFrame(
    {
        "patient_id": ["p1", "p2", "p3"],
        "sex": ["F", "M", "F"],
        "age": [61, 72, 55],
        "stage": ["II", "III", "I"],
        "diagnosis_date": pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"]),
        "death_date": pd.to_datetime(["2021-01-01", None, None]),
        "last_followup_date": pd.to_datetime(["2021-01-01", "2021-06-01", "2021-02-01"]),
    }
)

cohort = build_time_to_event_endpoint(
    patients,
    index_date_col="diagnosis_date",
    event_date_col="death_date",
    censor_date_col="last_followup_date",
)

profile = cohort_profile(cohort, endpoint_cols=["event"], group_col="stage")

table_one = fd.create_table_one(
    cohort,
    group_col="event",
    numeric=["age", "time"],
    categorical=["sex", "stage"],
)
```

In a live FHIR project, the upstream table would usually come from `FHIRRestClient.search_df`, `search_df_partitioned`, or `FHIRSQLClient.query_df`. The downstream contract stays the same: one row per patient, explicit index date, explicit endpoint dates, and saved descriptive artifacts.
