# Example: FHIR to Cohort

This pattern starts from FHIR resources, extracts tables, then builds a cohort for analysis.

The example uses public HAPI FHIR data and intentionally keeps extraction simple. In a real project, you would usually replace the basic groupby logic with study-specific feature definitions, terminology filters, date windows, and endpoint rules.

For precise REST field selection and site-specific preprocessing functions, read [FHIR Paths And Custom Extraction](fhir-paths-custom-extraction.md) next.

## What To Check Before Scaling

- Confirm resource references use the same patient identifier format.
- Limit pages while developing queries.
- Save raw extracts before aggregating features.
- Validate that features are measured before the outcome window.
- Keep implementation-guide-specific extraction code versioned.

```python
from fyron import FHIRRestClient
from fyron.cohort import join_cohort_tables, validate_cohort_table

client = FHIRRestClient("https://hapi.fhir.org/baseR4")

patients = client.search_df("Patient", params={"_count": 100}, max_pages=2)
conditions = client.search_df("Condition", params={"_count": 100}, max_pages=2)
observations = client.search_df("Observation", params={"_count": 100}, max_pages=2)

features = observations.groupby("subject.reference").agg(
    n_observations=("id", "count"),
).reset_index()

outcomes = conditions.groupby("subject.reference").agg(
    n_conditions=("id", "count"),
).reset_index()

cohort = join_cohort_tables(
    features,
    outcomes,
    on="subject.reference",
    how="inner",
)

validate_cohort_table(
    cohort,
    required_columns=["subject.reference", "n_observations", "n_conditions"],
)
```

FHIR schemas vary by server and implementation guide. Keep extraction logic explicit and version-controlled.
