# FHIR REST Agent Notes

Use `fyron.FHIRRestClient` for live FHIR APIs.

Basic search:

```python
from fyron import FHIRRestClient

client = FHIRRestClient(base_url="https://fhir.example.org/fhir", bearer_token=token)
patients = client.search_df("Patient", params={"_count": "100"}, max_pages=2)
```

Cohort-driven search:

```python
observations = client.search_df_from(
    df=cohort,
    resource="Observation",
    column_map={"subject": "patient_id"},
    params={"code": "http://loinc.org|718-7"},
    max_pages=1,
)
```

Long-running authenticated extraction:

```python
from fyron import FHIRRestClient

client = FHIRRestClient(
    base_url=os.environ["FHIR_BASE_URL"],
    num_processes=4,
    token_auth_method="basic",
)
```

Expected environment variables for token-env authentication:

```bash
FHIR_BASE_URL=...
FHIR_AUTH_URL=...
FHIR_REFRESH_URL=...
FHIR_USER=...
FHIR_PASSWORD=...
```

Rules:

- Do not put private endpoint URLs, usernames, passwords, or bearer tokens in generated examples.
- Prefer environment variables and `.env.example` placeholders.
- For multiprocessing, every worker must be able to refresh or recreate auth from environment credentials.
- Log URLs only when the user explicitly wants traceability and endpoint privacy is acceptable.
- If a server returns a FHIR `OperationOutcome`, surface the diagnostic message instead of hiding it.
- Do not write back to a live server unless the user explicitly confirms bundle type, endpoint, and review state.

