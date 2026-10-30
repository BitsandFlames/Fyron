"""Tests for FHIR JSON builders and write helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from fyron import FHIRRestClient
from fyron.fhir.builder import (
    attachment,
    build_bundle,
    build_condition,
    build_diagnostic_report,
    build_document_reference,
    build_encounter,
    build_imaging_measurement_bundle,
    build_llm_extraction_bundle,
    build_medication_statement,
    build_observation,
    build_observation_component,
    build_procedure,
    codeable_concept,
    coding,
    dicom_code,
    icd10,
    identifier,
    loinc,
    quantity,
    read_fhir_json,
    reference,
    snomed,
    summarize_fhir_bundle,
    summarize_fhir_resource,
    build_service_request,
    build_specimen,
    ucum_quantity,
    validate_fhir_bundle,
    validate_fhir_references,
    validate_fhir_resource,
    write_fhir_json,
)
from fyron.fhir.rest import FHIRRequestError


def test_primitive_builders() -> None:
    assert reference("Patient/123") == {"reference": "Patient/123"}
    assert identifier("ABC", system="urn:mrn") == {"value": "ABC", "system": "urn:mrn"}
    assert coding("718-7", system="http://loinc.org") == {"code": "718-7", "system": "http://loinc.org"}
    assert codeable_concept("718-7", system="http://loinc.org")["coding"][0]["code"] == "718-7"
    assert quantity(12.3, "mm")["value"] == 12.3
    assert attachment(url="report.pdf", content_type="application/pdf")["url"] == "report.pdf"


def test_common_coding_helpers() -> None:
    assert loinc("718-7") == {"code": "718-7", "system": "http://loinc.org"}
    assert snomed("44054006")["system"] == "http://snomed.info/sct"
    assert icd10("C34")["system"] == "http://hl7.org/fhir/sid/icd-10"
    assert dicom_code("CT")["system"] == "http://dicom.nema.org/resources/ontology/DCM"
    assert ucum_quantity(13.4, "g/dL")["system"] == "http://unitsofmeasure.org"


def test_observation_value_variants() -> None:
    numeric = build_observation(subject="Patient/1", code="SMA", value=42.0, unit="cm2")
    text = build_observation(subject="Patient/1", code="summary", value="stable", value_type="string")
    coded = build_observation(subject="Patient/1", code="risk", value="high", value_type="codeable")

    assert numeric["valueQuantity"]["unit"] == "cm2"
    assert text["valueString"] == "stable"
    assert coded["valueCodeableConcept"]["text"] == "high"


def test_observation_components_and_data_absent_reason() -> None:
    systolic = build_observation_component(code=loinc("8480-6", "Systolic blood pressure"), value=124, unit="mm[Hg]")
    diastolic = build_observation_component(code=loinc("8462-4", "Diastolic blood pressure"), value=77, unit="mm[Hg]")
    blood_pressure = build_observation(
        subject="Patient/1",
        code=loinc("85354-9", "Blood pressure panel"),
        components=[systolic, diastolic],
        performer=["Practitioner/radiologist-1"],
        encounter="Encounter/enc-1",
        interpretation="normal",
        note="Measured during structured review.",
    )
    missing = build_observation(
        subject="Patient/1",
        code="Tumor marker",
        data_absent_reason="not measured",
    )

    assert len(blood_pressure["component"]) == 2
    assert blood_pressure["performer"][0]["reference"] == "Practitioner/radiologist-1"
    assert blood_pressure["encounter"]["reference"] == "Encounter/enc-1"
    assert blood_pressure["note"][0]["text"] == "Measured during structured review."
    assert missing["dataAbsentReason"]["text"] == "not measured"
    with pytest.raises(ValueError, match="data_absent_reason"):
        build_observation(subject="Patient/1", code="marker", value=1, data_absent_reason="not measured")


def test_condition_document_reference_and_diagnostic_report() -> None:
    doc = build_document_reference(
        subject="Patient/1",
        url="reports/source.pdf",
        title="Source report",
        content_type="application/pdf",
        document_id="doc-1",
    )
    condition = build_condition(
        subject="Patient/1",
        code=codeable_concept("C34", system="http://hl7.org/fhir/sid/icd-10"),
        condition_id="cond-1",
        evidence=[doc],
    )
    observation = build_observation(subject="Patient/1", code="marker", value=1.2, observation_id="obs-1")
    report = build_diagnostic_report(
        subject="Patient/1",
        code="AI extracted report",
        results=[observation],
        report_id="report-1",
    )

    assert doc["resourceType"] == "DocumentReference"
    assert condition["evidence"][0]["detail"][0]["reference"] == "DocumentReference/doc-1"
    assert report["result"][0]["reference"] == "Observation/obs-1"


def test_builder_profile_metadata_and_additional_resources() -> None:
    obs = build_observation(
        subject="Patient/1",
        code="SMA",
        value=42.0,
        profile="https://example.org/fhir/StructureDefinition/sma-observation",
        identifier={"system": "urn:test", "value": "obs-1"},
        meta_source="https://fyron.test/run/1",
    )
    resources = [
        build_encounter(subject="Patient/1", encounter_id="enc-1"),
        build_procedure(subject="Patient/1", code="CT-guided biopsy", procedure_id="proc-1"),
        build_medication_statement(subject="Patient/1", medication="Pembrolizumab", medication_statement_id="med-1"),
        build_service_request(subject="Patient/1", code="CT abdomen", service_request_id="req-1"),
        build_specimen(subject="Patient/1", specimen_type="Blood", specimen_id="spec-1"),
    ]

    assert obs["meta"]["profile"] == ["https://example.org/fhir/StructureDefinition/sma-observation"]
    assert obs["identifier"][0]["value"] == "obs-1"
    assert obs["meta"]["source"] == "https://fyron.test/run/1"
    assert [resource["resourceType"] for resource in resources] == [
        "Encounter",
        "Procedure",
        "MedicationStatement",
        "ServiceRequest",
        "Specimen",
    ]
    for resource in resources:
        assert validate_fhir_resource(resource)["resourceType"] == resource["resourceType"]


def test_collection_and_transaction_bundle_differ() -> None:
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0, observation_id="obs-1")
    collection = build_bundle([obs], bundle_type="collection")
    transaction = build_bundle([obs], bundle_type="transaction")

    assert collection["type"] == "collection"
    assert "request" not in collection["entry"][0]
    assert transaction["type"] == "transaction"
    assert transaction["entry"][0]["request"] == {"method": "POST", "url": "Observation"}


def test_transaction_bundle_supports_put_and_conditional_create() -> None:
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0, observation_id="obs-1")
    put_bundle = build_bundle([obs], bundle_type="transaction", transaction_method="PUT")
    conditional_bundle = build_bundle([obs], bundle_type="transaction", if_none_exist={"Observation": "identifier=obs-1"})

    assert put_bundle["entry"][0]["request"] == {"method": "PUT", "url": "Observation/obs-1"}
    assert conditional_bundle["entry"][0]["request"]["ifNoneExist"] == "identifier=obs-1"
    with pytest.raises(ValueError, match="require resource ids"):
        build_bundle([build_observation(subject="Patient/1", code="SMA", value=42.0)], bundle_type="transaction", transaction_method="PUT")


def test_bundle_generates_deterministic_uuid_full_urls() -> None:
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0)

    one = build_bundle([obs], bundle_type="collection")
    two = build_bundle([obs], bundle_type="collection")

    assert one["entry"][0]["fullUrl"].startswith("urn:uuid:")
    assert one["entry"][0]["fullUrl"] == two["entry"][0]["fullUrl"]


def test_imaging_measurement_bundle_links_study_series_and_report() -> None:
    bundle = build_imaging_measurement_bundle(
        subject="Patient/1",
        study_instance_uid="1.2.3",
        series_instance_uid="1.2.3.4",
        measurements=[{"id": "sma-l3", "code": "L3 SMA", "value": 123.4, "unit": "cm2"}],
        model_name="Fyron imaging model",
        model_endpoint_url="https://models.example.org/fyron",
        bundle_type="collection",
    )
    resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]

    assert "ImagingStudy" in resource_types
    assert "Observation" in resource_types
    assert "DiagnosticReport" in resource_types
    assert "Provenance" in resource_types


def test_workflow_bundles_support_id_prefixes() -> None:
    llm_bundle = build_llm_extraction_bundle(
        subject="Patient/1",
        source_report_url="reports/report.pdf",
        observations=[build_observation(subject="Patient/1", code="Hemoglobin", value=13.2, observation_id="hgb")],
        model_name="Fyron LLM extractor",
        id_prefix="report-001",
        bundle_type="collection",
    )
    imaging_bundle = build_imaging_measurement_bundle(
        subject="Patient/1",
        study_instance_uid="1.2.3",
        measurements=[{"id": "sma-l3", "code": "L3 SMA", "value": 123.4, "unit": "cm2"}],
        id_prefix="study-001",
        bundle_type="collection",
    )

    llm_ids = {entry["resource"].get("id") for entry in llm_bundle["entry"]}
    imaging_ids = {entry["resource"].get("id") for entry in imaging_bundle["entry"]}
    assert "report-001-source-report" in llm_ids
    assert "report-001-llm-extraction-provenance" in llm_ids
    assert "study-001-source-imaging-study" in imaging_ids
    assert "study-001-imaging-measurement-report" in imaging_ids


def test_llm_extraction_bundle_contains_evidence_model_and_provenance() -> None:
    obs = build_observation(subject="Patient/1", code="Hemoglobin", value=13.2, observation_id="hgb")
    cond = build_condition(subject="Patient/1", code="Pneumonia", condition_id="pneumonia")
    bundle = build_llm_extraction_bundle(
        subject="Patient/1",
        source_report_url="reports/report.pdf",
        observations=[obs],
        conditions=[cond],
        summary_text="No new acute finding.",
        model_name="Fyron LLM extractor",
        model_endpoint_url="https://models.example.org/extract",
        model_version="2026.06",
        prompt_version="prompt-v1",
        bundle_type="collection",
    )
    resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]

    assert "DocumentReference" in resource_types
    assert "Observation" in resource_types
    assert "Condition" in resource_types
    assert "Device" in resource_types
    assert "Endpoint" in resource_types
    assert "Provenance" in resource_types


def test_validation_and_json_roundtrip(tmp_path: Path) -> None:
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0)
    bundle = build_bundle([obs], bundle_type="collection")
    path = write_fhir_json(bundle, tmp_path / "bundle.json")

    assert read_fhir_json(path)["resourceType"] == "Bundle"
    assert validate_fhir_resource(obs)["resourceType"] == "Observation"
    assert validate_fhir_bundle(bundle)["type"] == "collection"
    with pytest.raises(ValueError, match="resourceType"):
        validate_fhir_resource({})
    with pytest.raises(ValueError, match="bundle_type"):
        build_bundle([obs], bundle_type="document")


def test_required_field_validation_and_reference_summary() -> None:
    with pytest.raises(ValueError, match="Observation is missing required"):
        validate_fhir_resource({"resourceType": "Observation", "code": codeable_concept(text="SMA")})

    obs = build_observation(subject="Patient/1", code="SMA", value=42.0, observation_id="obs-1")
    report = build_diagnostic_report(
        subject="Patient/1",
        code="Report",
        results=["Observation/missing", obs],
        report_id="report-1",
    )
    bundle = build_bundle([obs, report], bundle_type="collection")
    refs = validate_fhir_references(bundle)

    assert refs["valid"] is False
    assert refs["missing_references"] == ["Observation/missing"]
    with pytest.raises(ValueError, match="Broken local reference"):
        validate_fhir_bundle(bundle)


def test_fhir_summaries_are_inspectable() -> None:
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0, observation_id="obs-1")
    bundle = build_bundle([obs], bundle_type="transaction")
    resource_summary = summarize_fhir_resource(obs)
    bundle_summary = summarize_fhir_bundle(bundle)

    assert resource_summary["resource_type"] == "Observation"
    assert resource_summary["reference"] == "Observation/obs-1"
    assert bundle_summary["entry_count"] == 1
    assert bundle_summary["resource_types"] == {"Observation": 1}
    assert bundle_summary["transaction_methods"] == {"POST": 1}
    assert bundle_summary["local_references_valid"] is True


def test_r6_mode_marks_resources_experimental() -> None:
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0, version="R6")
    codes = [tag["code"] for tag in obs["meta"]["tag"]]

    assert "fhir-r6" in codes
    assert "experimental-r6" in codes


class _FakeResponse:
    def __init__(self, status_code: int = 201, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("boom")

    def json(self) -> dict[str, Any]:
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class _FakeSession(requests.Session):
    def __init__(self, response: _FakeResponse | None = None) -> None:
        super().__init__()
        self.response = response or _FakeResponse(payload={"resourceType": "Observation", "id": "obs-1"})
        self.calls: list[dict[str, Any]] = []
        self.headers: dict[str, str] = {}

    def request(self, method: str, url: str, json: dict[str, Any], timeout: int) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, "json": json, "timeout": timeout})
        return self.response


def test_rest_client_create_update_and_submit_bundle() -> None:
    session = _FakeSession()
    client = FHIRRestClient(base_url="https://fhir.example.org/fhir", auth=session)
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0, observation_id="obs-1")
    bundle = build_bundle([obs], bundle_type="transaction")

    create_result = client.create_resource(obs)
    update_result = client.update_resource(obs)
    bundle_result = client.submit_bundle(bundle)

    assert create_result.status_code == 201
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["url"] == "https://fhir.example.org/fhir/Observation"
    assert session.calls[1]["method"] == "PUT"
    assert session.calls[1]["url"] == "https://fhir.example.org/fhir/Observation/obs-1"
    assert session.calls[2]["method"] == "POST"
    assert session.calls[2]["url"] == "https://fhir.example.org/fhir"
    assert bundle_result.resource_type == "Observation"
    assert update_result.resource_id == "obs-1"


def test_rest_client_write_errors_are_clear() -> None:
    class ErrorResponse(_FakeResponse):
        def raise_for_status(self) -> None:
            import requests

            raise requests.HTTPError("bad")

    client = FHIRRestClient(base_url="https://fhir.example.org/fhir", auth=_FakeSession(ErrorResponse(status_code=500)))
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0)

    with pytest.raises(FHIRRequestError):
        client.create_resource(obs)


def test_rest_client_non_json_write_response_returns_metadata() -> None:
    response = _FakeResponse(status_code=204, payload=None, headers={"Location": "Observation/obs-1/_history/1"})
    client = FHIRRestClient(base_url="https://fhir.example.org/fhir", auth=_FakeSession(response))
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0, observation_id="obs-1")

    result = client.update_resource(obs)

    assert result.status_code == 204
    assert result.location == "Observation/obs-1/_history/1"
    assert result.resource_type == "Observation"
    assert result.resource_id == "obs-1"
    assert result.response_json is None


def test_broken_local_reference_is_rejected() -> None:
    obs = build_observation(subject="Patient/1", code="SMA", value=42.0)
    obs["derivedFrom"] = [{"reference": "urn:uuid:missing"}]
    bundle = build_bundle([obs], bundle_type="collection")

    with pytest.raises(ValueError, match="Broken local reference"):
        validate_fhir_bundle(bundle)
