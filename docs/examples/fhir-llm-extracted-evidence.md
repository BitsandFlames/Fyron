# FHIR LLM Extracted Evidence

This example packages LLM-extracted findings from a clinical report as FHIR JSON. It keeps the source document, extracted facts, generated summary, model endpoint, and provenance together in one inspectable Bundle.

Use this for review, validation, and handoff to a FHIR server after your local clinical QA process.

## Build The Bundle

```python
from fyron.fhir.builder import (
    build_condition,
    build_llm_extraction_bundle,
    build_observation,
    codeable_concept,
    summarize_fhir_bundle,
    validate_fhir_bundle,
    validate_fhir_references,
    write_fhir_json,
)

hemoglobin = build_observation(
    subject="Patient/123",
    code=codeable_concept("718-7", system="http://loinc.org", display="Hemoglobin"),
    value=13.4,
    unit="g/dL",
    observation_id="obs-hgb-report-001",
)

condition = build_condition(
    subject="Patient/123",
    code=codeable_concept("C34", system="http://hl7.org/fhir/sid/icd-10", display="Lung cancer"),
    condition_id="condition-lung-cancer-report-001",
)

bundle = build_llm_extraction_bundle(
    subject="Patient/123",
    source_report_url="https://reports.example.org/report-001.pdf",
    observations=[hemoglobin],
    conditions=[condition],
    summary_text="LLM-generated summary for clinical review.",
    model_name="Fyron report extraction model",
    model_endpoint_url="https://models.example.org/fyron/report-extract",
    model_version="2026.06",
    prompt_version="report-extraction-v1",
    id_prefix="report-001",
    bundle_type="collection",
)

reference_report = validate_fhir_references(bundle)
summary = summarize_fhir_bundle(bundle)
validate_fhir_bundle(bundle)
write_fhir_json(bundle, "outputs/fhir/report_001_extracted_evidence.json")

print(reference_report["valid"])
print(summary["resource_types"])
```

## Submit As A Transaction

```python
from fyron import FHIRRestClient
from fyron.fhir.builder import build_bundle

client = FHIRRestClient("https://fhir.example.org/fhir")

transaction = build_bundle(
    [entry["resource"] for entry in bundle["entry"]],
    bundle_type="transaction",
)

result = client.submit_bundle(transaction)
print(result.status_code, result.location)
```

## Review Notes

- `DocumentReference` points to the source report.
- Extracted `Observation` resources use `derivedFrom`.
- Extracted `Condition` resources use evidence links.
- `Device` and `Endpoint` identify the model system.
- `Provenance` links the generated outputs back to the source report and prompt/model metadata.

Fyron validates structure and local references. Use your implementation guide and official FHIR validation for production write-back.
