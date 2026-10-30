# FHIR

For site-specific access setup, see [Authentication](../authentication/fhir-rest.md). Choose the method and permissions approved by your administrator.

`fyron.fhir` is the interoperability layer for FHIR extraction, SQL-backed FHIR warehouses, resource builders, bundle mapping, and lightweight JSON validation. The parent module keeps the decision simple: choose REST for live endpoints, SQL for warehouse tables, Builder for explicit resources, and Mapping for reviewed DataFrames.

FHIR servers vary by institution and implementation guide. Fyron keeps transport, extraction, table construction, and write-back separated so each step stays inspectable.

Requests-based FHIR, DICOMweb, document, and LLM clients follow redirects only within the same scheme, host, and port. Cross-origin redirects, HTTPS downgrades, and URLs containing user credentials are blocked before forwarding request bodies or custom authentication headers. Configure the approved final endpoint directly when a service redirects elsewhere. This guard is also installed on supplied sessions, while preserving existing response hooks.

## FHIR Submodules

| Chapter | Use it for |
| --- | --- |
| [FHIR REST](fhir/rest.md) | Live endpoint searches, pagination, row-wise cohort lookups, and write-back. |
| [FHIR SQL](fhir/sql.md) | SQL-backed FHIR warehouses, joins, streaming, and parallel query jobs. |
| [FHIR Builder](fhir/builder.md) | Hand-building R4/R6 resources and evidence bundles. |
| [FHIR Mapping](fhir/mapping.md) | Turning reviewed DataFrames into FHIR bundles. |

## Choose The Right Path

| Need | Prefer |
| --- | --- |
| Pull resources from a FHIR server | [FHIR REST](fhir/rest.md) |
| Query a relational FHIR warehouse | [FHIR SQL](fhir/sql.md) |
| Build one resource or a small evidence bundle by hand | [FHIR Builder](fhir/builder.md) |
| Convert an LLM/BOA/review CSV table into FHIR JSON | [FHIR Mapping](fhir/mapping.md) |
| Extract specific nested fields from REST resources | [FHIR Paths & Custom Extraction](../examples/fhir-paths-custom-extraction.md) |
| Reuse common FHIRPath extraction columns | `get_fhir_path_preset(...)` in [FHIR REST](fhir/rest.md#fhirpath-extraction-presets) |

## Imports

```python
from fyron import Auth, FHIRRestClient, FHIRSQLClient
from fyron.fhir import FHIRObj, get_fhir_path_preset, safe_get
from fyron.fhir.builder import build_observation, build_bundle
from fyron.fhir.mapping import build_observations_from_dataframe
```

## Minimal REST Example

```python
from fyron import FHIRRestClient

client = FHIRRestClient("https://hapi.fhir.org/baseR4")
patients = client.search_df("Patient", params={"_count": 25}, max_pages=1)
```

## Minimal SQL Example

```python
from fyron import FHIRSQLClient

client = FHIRSQLClient(dsn="postgresql://user:password@localhost/fhir")
patients = client.query_df("select id as patient_id from patient limit 100")
```

## Build Or Map FHIR JSON

```python
from fyron.fhir.builder import build_bundle, build_observation

observation = build_observation(
    subject="Patient/123",
    code="L3 skeletal muscle area",
    value=123.4,
    unit="cm2",
)
bundle = build_bundle([observation], bundle_type="collection")
```

Use [FHIR Mapping](fhir/mapping.md) when the same information already exists as a reviewed DataFrame or CSV.

## Common Pitfalls

- FHIR references can be bare, relative, or absolute; normalize identifiers before cohort joins.
- Search parameter support differs across FHIR servers.
- Resource JSON may differ by implementation guide; keep local extraction assumptions visible.
- Fyron validation is structural and lightweight, not a replacement for server/profile validation.

## Related Modules

- [Core I/O](core.md) for `.env`, local tables, Teable, and S3.
- [Cohort Tables](cohort.md) for joining extracted features to outcomes.
- [Unified CLI](cli.md) for repeatable `fyron fhir-rest` and `fyron fhir-build-bundle` jobs.
