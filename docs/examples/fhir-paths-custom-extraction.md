# FHIR Paths And Custom Extraction

This chapter shows how to use FHIRPath-style field extraction with `FHIRRestClient` and how to write your own preprocessing functions when a server uses local profiles, extensions, or resource layouts that need study-specific handling.

Use FHIR paths when the table is mostly a direct projection of resource fields. Use custom preprocessing when you need logic: multiple codings, extension parsing, date windows, unit normalization, study-specific flags, or one output row per nested component.

## FHIRPath Support

FHIRPath extraction uses `fhirpathpy`, which is installed as a Fyron package dependency. If `fhir_paths=...` raises an import error, reinstall or update Fyron so the package environment is complete.

## The Two Extraction Modes

| Mode | Use When | Fyron Parameters |
| --- | --- | --- |
| Flattened resources | You are exploring an unknown server and want broad nested columns | `mode="flatten"` |
| FHIR paths | You know the exact resource fields you want | `fhir_paths=[...]` |
| Custom preprocessing | You need local logic, extension parsing, unit conversion, or nested rows | `mode="custom"`, `process_function=...` |

All three modes can be used after fetching bundles or directly through `search_df`.

## Quick FHIRPath Query

`fhir_paths` accepts a list of expressions. Each expression is evaluated against every resource in the returned bundles.

```python
from fyron import FHIRRestClient

client = FHIRRestClient(base_url="https://hapi.fhir.org/baseR4")

patients = client.search_df(
    resource_type="Patient",
    params={"_count": 25, "_sort": "_id"},
    max_pages=1,
    fhir_paths=[
        "id",
        "gender",
        "birthDate",
        "name.family",
        "name.given",
    ],
    use_multiprocessing=False,
)
```

When the search returns one resource type, `search_df` returns one DataFrame. When a bundle contains multiple resource types, Fyron returns a dictionary of DataFrames keyed by resource type.

## Default FHIRPath Presets

Fyron ships common FHIRPath presets for resources that frequently appear in clinical research pipelines. Use them as a starting point, inspect the generated columns, and then adapt them to your local FHIR profile.

```python
from fyron import FHIRRestClient, get_fhir_path_preset

client = FHIRRestClient(base_url="https://fhir.example.org/r4")

observations = client.search_df(
    resource_type="Observation",
    params={"code": "http://loinc.org|718-7", "_count": 100},
    max_pages=2,
    fhir_paths=get_fhir_path_preset("Observation"),
)
```

Preset resources:

| Resource | Good first extraction columns |
| --- | --- |
| `Patient` | patient id, identifiers, gender, birth date, death fields, name fields |
| `Encounter` | encounter id, patient reference, status, class, type, period start/end |
| `Condition` | condition id, patient/encounter references, status, code, recorded date, onset |
| `Observation` | observation id, patient/encounter references, code, effective date, value, unit, components |
| `Procedure` | procedure id, patient/encounter references, status, code, performed date/period |
| `DiagnosticReport` | report id, patient/encounter references, code, effective/issued dates, results, conclusion |
| `ImagingStudy` | study UID, series UID, modality, series description, SOP instance identifiers |
| `MedicationStatement` | medication code/display, patient, status, effective period, assertion date |
| `ServiceRequest` | request id, patient/encounter references, status, intent, code, authored date |
| `Specimen` | specimen id, patient, type, collection time, body site |
| `DocumentReference` | document id, patient/encounter references, type, date, content URL/title |

Presets are returned as copies, so you can add local extensions without mutating the package default:

```python
paths = get_fhir_path_preset("Condition")
paths.append(("molecular_marker", "extension.where(url = 'https://example.org/fhir/molecular-marker').valueString"))
```

## Naming FHIRPath Columns

FHIRPath expressions can be passed as `(column_name, expression)` tuples. This keeps DataFrame columns readable and avoids dots in final column names.

```python
observations = client.search_df(
    resource_type="Observation",
    params={
        "code": "http://loinc.org|718-7",
        "_count": 100,
    },
    max_pages=2,
    fhir_paths=[
        ("observation_id", "id"),
        ("patient_ref", "subject.reference"),
        ("encounter_ref", "encounter.reference"),
        ("loinc_code", "code.coding.where(system = 'http://loinc.org').code"),
        ("display", "code.coding.display"),
        ("effective_datetime", "effectiveDateTime"),
        ("value", "valueQuantity.value"),
        ("unit", "valueQuantity.unit"),
    ],
    use_multiprocessing=False,
)
```

FHIRPath results follow these rules:

- no result becomes `None`,
- one result becomes a scalar,
- multiple results stay as a list,
- fields with `None` are omitted from the row.

## Good Path Patterns

| Goal | FHIRPath Expression |
| --- | --- |
| Resource id | `id` |
| Patient reference | `subject.reference` |
| First coding code | `code.coding[0].code` |
| LOINC code only | `code.coding.where(system = 'http://loinc.org').code` |
| Quantity value | `valueQuantity.value` |
| Quantity unit | `valueQuantity.unit` |
| Observation components | `component.code.coding.code` |
| Extension values | `extension.where(url = 'https://example.org/fhir/StructureDefinition/foo').valueString` |

Start with a small query and inspect the output before using the path in a cohort pipeline.

```python
observations.head()
observations.columns
```

## Row-Wise REST Queries From A Cohort

Use `search_df_from` when you already have a cohort table and need one REST search per row. This is common when a cohort contains patient IDs, encounter IDs, or accession numbers.

```python
import pandas as pd
from fyron import FHIRRestClient

cohort = pd.DataFrame(
    {
        "patient_id": ["123", "456"],
    }
)

client = FHIRRestClient(base_url="https://fhir.example.org/fhir")

labs = client.search_df_from(
    df=cohort,
    resource_type="Observation",
    column_map={"subject": "patient_id"},
    param_prefix={"subject": "Patient/"},
    params={
        "code": "http://loinc.org|718-7",
        "_count": 100,
    },
    max_pages=1,
    fhir_paths=[
        ("patient_ref", "subject.reference"),
        ("observation_id", "id"),
        ("effective_datetime", "effectiveDateTime"),
        ("value", "valueQuantity.value"),
        ("unit", "valueQuantity.unit"),
    ],
    include_column_map_columns=True,
    use_multiprocessing=False,
)
```

Important parameters:

| Parameter | Required | Meaning |
| --- | --- | --- |
| `df` | yes | Input cohort or lookup table. |
| `resource_type` | yes | FHIR resource to query, e.g. `Observation`. |
| `column_map` | yes | Maps FHIR search parameters to columns in `df`. |
| `param_prefix` | no | Adds prefixes such as `Patient/` before values. |
| `params` | no | Static search filters applied to every row. |
| `include_column_map_columns` | no | Adds the query values back to result rows for traceability. |

## Custom Preprocessing Contract

Custom preprocessing functions receive one FHIR bundle and must return this structure:

```python
{
    "ResourceType": [
        {"column": "value", "another_column": 123},
        {"column": "next value", "another_column": 456},
    ]
}
```

For a single resource type, return one key. For multiple output tables, return multiple keys.

```python
from fyron.fhir import safe_get

def process_observation_bundle_for_labs(bundle):
    rows = []

    for entry in bundle.get("entry", []) or []:
        resource = entry.get("resource") or {}
        if resource.get("resourceType") != "Observation":
            continue

        rows.append(
            {
                "observation_id": safe_get(resource, "id"),
                "patient_ref": safe_get(resource, "subject.reference"),
                "encounter_ref": safe_get(resource, "encounter.reference"),
                "code": safe_get(resource, "code.coding[0].code"),
                "code_system": safe_get(resource, "code.coding[0].system"),
                "effective_datetime": safe_get(resource, "effectiveDateTime"),
                "value": safe_get(resource, "valueQuantity.value"),
                "unit": safe_get(resource, "valueQuantity.unit"),
            }
        )

    return {"Observation": rows}
```

Use it directly in `search_df`:

```python
labs = client.search_df(
    resource_type="Observation",
    params={
        "code": "http://loinc.org|718-7",
        "_count": 100,
    },
    max_pages=2,
    mode="custom",
    process_function=process_observation_bundle_for_labs,
    use_multiprocessing=False,
)
```

## Custom Extraction For Components

Some FHIR resources contain repeated nested values. For example, a blood pressure `Observation` may have systolic and diastolic values in `component`. In that case, a custom function can emit one row per component.

```python
from fyron.fhir import safe_get

def process_observation_components(bundle):
    rows = []

    for entry in bundle.get("entry", []) or []:
        resource = entry.get("resource") or {}
        if resource.get("resourceType") != "Observation":
            continue

        base = {
            "observation_id": safe_get(resource, "id"),
            "patient_ref": safe_get(resource, "subject.reference"),
            "effective_datetime": safe_get(resource, "effectiveDateTime"),
        }

        for component in resource.get("component", []) or []:
            rows.append(
                {
                    **base,
                    "component_code": safe_get(component, "code.coding[0].code"),
                    "component_display": safe_get(component, "code.coding[0].display"),
                    "value": safe_get(component, "valueQuantity.value"),
                    "unit": safe_get(component, "valueQuantity.unit"),
                }
            )

    return {"ObservationComponent": rows}
```

Then query normally:

```python
blood_pressure = client.search_df(
    resource_type="Observation",
    params={
        "code": "http://loinc.org|85354-9",
        "_count": 100,
    },
    max_pages=2,
    mode="custom",
    process_function=process_observation_components,
    use_multiprocessing=False,
)
```

## Parsing Local Extensions

FHIR extensions are normal in real clinical systems. Keep extension URLs explicit and put the logic in one named function.

```python
from fyron.fhir import extract_patient, safe_get

ETHNICITY_EXTENSION = (
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
)

def first_extension(resource, url):
    for extension in resource.get("extension", []) or []:
        if extension.get("url") == url:
            return extension
    return None

def extract_patient_for_site(resource):
    row = extract_patient(resource)
    ethnicity = first_extension(resource, ETHNICITY_EXTENSION)

    row["ethnicity_text"] = safe_get(
        ethnicity,
        "extension[0].valueCoding.display",
        default=None,
    )
    row["source_profile"] = safe_get(
        resource,
        "meta.profile[0]",
        default=None,
    )
    return row
```

Wrap it in a bundle processor:

```python
def process_patient_bundle_for_site(bundle):
    rows = []

    for entry in bundle.get("entry", []) or []:
        resource = entry.get("resource") or {}
        if resource.get("resourceType") == "Patient":
            rows.append(extract_patient_for_site(resource))

    return {"Patient": rows}
```

## Multiprocessing Notes

During development, set `use_multiprocessing=False`. It makes stack traces easier to read and avoids pickling surprises with functions defined inside notebooks.

```python
df = client.search_df(
    resource_type="Patient",
    max_pages=1,
    mode="custom",
    process_function=process_patient_bundle_for_site,
    use_multiprocessing=False,
)
```

For larger production pulls, move custom processors into a normal Python module so multiprocessing can import them cleanly.

## Validate Your Custom Extractor

Test a custom extractor on a tiny representative bundle before running it against the server.

```python
example_bundle = {
    "resourceType": "Bundle",
    "entry": [
        {
            "resource": {
                "resourceType": "Observation",
                "id": "obs-1",
                "subject": {"reference": "Patient/123"},
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "718-7",
                            "display": "Hemoglobin",
                        }
                    ]
                },
                "valueQuantity": {
                    "value": 13.4,
                    "unit": "g/dL",
                },
            }
        }
    ],
}

out = process_observation_bundle_for_labs(example_bundle)
assert "Observation" in out
assert out["Observation"][0]["patient_ref"] == "Patient/123"
assert out["Observation"][0]["value"] == 13.4
```

## Recommended Workflow

1. Start with `mode="flatten"` on one page to inspect the resource shape.
2. Switch to `fhir_paths` when fields are direct resource projections.
3. Switch to `mode="custom"` when extraction needs clinical or site-specific logic.
4. Keep raw bundles or raw DataFrames until the extractor is validated.
5. Write a tiny test bundle for each custom extractor.
6. Name output columns by clinical meaning, not by raw JSON path.

## Common Pitfalls

| Pitfall | Fix |
| --- | --- |
| FHIRPath returns lists unexpectedly | Name the column as plural or handle it in custom preprocessing. |
| Search query returns no rows | Test the exact search URL against one patient and confirm server-supported search parameters. |
| `subject` joins fail | Normalize references such as `Patient/123`, full URLs, and bare IDs before joining. |
| Custom function works in notebook but fails with multiprocessing | Set `use_multiprocessing=False` or move the function into an importable module. |
| Extension parsing is repeated across notebooks | Put extension URLs and extraction logic in a named preprocessing function. |
