# Quickstart: FHIR REST To DataFrame

Use this when you want to test a FHIR endpoint and inspect resources as a table.

## Install

```bash
uv add fyron
```

## Query A Small Page

```python
from fyron import FHIRRestClient

client = FHIRRestClient("https://hapi.fhir.org/baseR4")

patients = client.search_df(
    "Patient",
    params={"_count": 20},
    max_pages=1,
)

print(patients.head())
```

## Partition Broad Searches

For local or institutional servers, prefer bounded searches during exploration. Use partitioned searches when a resource type is too large for one query.

```python
observations = client.search_df_partitioned(
    "Observation",
    partition_param="date",
    start="2024-01-01",
    end="2024-02-01",
    freq="7D",
    params={"_count": 100},
    max_pages_per_partition=2,
)
```

## Next Steps

- Use [FHIR REST](../modules/fhir/rest.md) for pagination, partitioning, authentication, and custom extraction.
- Use [FHIR Paths & Custom Extraction](../examples/fhir-paths-custom-extraction.md) to extract nested fields without preprocessing callbacks.
- Keep private endpoints, credentials, and real payloads out of notebooks shared publicly.
