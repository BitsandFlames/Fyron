# FHIR Imaging Measurement Bundle

This example packages imaging-derived measurements as FHIR JSON. It is useful when BOA, radiomics, segmentation, or model outputs should remain linked to the source imaging study and series.

## Build The Bundle

```python
from fyron.fhir.builder import (
    build_imaging_measurement_bundle,
    codeable_concept,
    summarize_fhir_bundle,
    validate_fhir_bundle,
    validate_fhir_references,
    write_fhir_json,
)

bundle = build_imaging_measurement_bundle(
    subject="Patient/123",
    study_instance_uid="1.2.840.113619.2.55.3.604688654.123",
    series_instance_uid="1.2.840.113619.2.55.3.604688654.123.4",
    series_description="CT abdomen portal venous",
    measurements=[
        {
            "id": "l3-sma",
            "code": codeable_concept(text="L3 skeletal muscle area"),
            "value": 123.4,
            "unit": "cm2",
            "body_site": codeable_concept(text="L3"),
            "method": codeable_concept(text="Fyron BOA segmentation"),
        },
        {
            "id": "vat-volume",
            "code": codeable_concept(text="Visceral adipose tissue volume"),
            "value": 820.5,
            "unit": "ml",
            "body_site": codeable_concept(text="Abdomen"),
            "method": codeable_concept(text="Fyron body-composition extraction"),
        },
        {
            "id": "vat-sat-ratio",
            "code": codeable_concept(text="VAT/SAT ratio"),
            "value": 0.74,
            "unit": "ratio",
            "body_site": codeable_concept(text="Abdomen"),
            "method": codeable_concept(text="Fyron body-composition extraction"),
        },
    ],
    model_name="Fyron imaging feature extractor",
    model_endpoint_url="https://models.example.org/fyron/imaging",
    id_prefix="study-001",
    bundle_type="collection",
)

reference_report = validate_fhir_references(bundle)
summary = summarize_fhir_bundle(bundle)
validate_fhir_bundle(bundle)
write_fhir_json(bundle, "outputs/fhir/case_001_imaging_measurements.json")

print(reference_report["valid"])
print(summary["resource_types"])
```

## What The Bundle Contains

- `ImagingStudy` with study UID and optional series UID.
- `Observation` resources for each measurement.
- A `DiagnosticReport` grouping the measurements.
- Optional `Device` and `Endpoint` resources for the model system.
- `Provenance` linking measurements to source imaging and model metadata.

## Server Upload

For server write-back, rebuild the same resources as a transaction bundle:

```python
from fyron import FHIRRestClient
from fyron.fhir.builder import build_bundle

client = FHIRRestClient("https://fhir.example.org/fhir")

transaction = build_bundle(
    [entry["resource"] for entry in bundle["entry"]],
    bundle_type="transaction",
)

result = client.submit_bundle(transaction)
print(result.status_code)
```

Confirm the target server accepts your local codes, extensions, and profiles before production upload.
