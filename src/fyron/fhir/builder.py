"""FHIR JSON resource and bundle builders."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Sequence

StrPath = str | Path

FHIR_R4 = "R4"
FHIR_R6 = "R6"
SUPPORTED_FHIR_VERSIONS = {FHIR_R4, FHIR_R6}
FYRON_MODEL_SYSTEM = "https://bitsandflames.com/fyron"
FYRON_SERIES_UID_EXTENSION = "https://bitsandflames.com/fhir/StructureDefinition/imaging-series-uid"
FYRON_MODEL_VERSION_EXTENSION = "https://bitsandflames.com/fhir/StructureDefinition/model-version"
FYRON_PROMPT_VERSION_EXTENSION = "https://bitsandflames.com/fhir/StructureDefinition/prompt-version"
LOINC_SYSTEM = "http://loinc.org"
SNOMED_SYSTEM = "http://snomed.info/sct"
ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10"
DICOM_SYSTEM = "http://dicom.nema.org/resources/ontology/DCM"
UCUM_SYSTEM = "http://unitsofmeasure.org"


def reference(target: str | dict[str, Any], display: str | None = None) -> dict[str, Any]:
    """Build a FHIR Reference."""
    if isinstance(target, dict):
        ref = _resource_reference(target)
    else:
        ref = str(target)
    out = {"reference": ref}
    if display:
        out["display"] = display
    return out


def identifier(value: str, system: str | None = None, use: str | None = None) -> dict[str, Any]:
    """Build a FHIR Identifier."""
    out = {"value": str(value)}
    if system:
        out["system"] = system
    if use:
        out["use"] = use
    return out


def coding(code: str, system: str | None = None, display: str | None = None) -> dict[str, Any]:
    """Build a FHIR Coding."""
    out = {"code": str(code)}
    if system:
        out["system"] = system
    if display:
        out["display"] = display
    return out


def loinc(code: str, display: str | None = None) -> dict[str, Any]:
    """Build a LOINC Coding."""
    return coding(code, system=LOINC_SYSTEM, display=display)


def snomed(code: str, display: str | None = None) -> dict[str, Any]:
    """Build a SNOMED CT Coding."""
    return coding(code, system=SNOMED_SYSTEM, display=display)


def icd10(code: str, display: str | None = None) -> dict[str, Any]:
    """Build an ICD-10 Coding."""
    return coding(code, system=ICD10_SYSTEM, display=display)


def dicom_code(code: str, display: str | None = None) -> dict[str, Any]:
    """Build a DICOM ontology Coding."""
    return coding(code, system=DICOM_SYSTEM, display=display)


def codeable_concept(
    code: str | None = None,
    *,
    system: str | None = None,
    display: str | None = None,
    text: str | None = None,
    codings: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a FHIR CodeableConcept."""
    coding_items = list(codings or [])
    if code is not None:
        coding_items.append(coding(code=code, system=system, display=display))
    out: dict[str, Any] = {}
    if coding_items:
        out["coding"] = coding_items
    if text:
        out["text"] = text
    if not out:
        raise ValueError("codeable_concept requires code, codings, or text")
    return out


def quantity(
    value: int | float,
    unit: str | None = None,
    *,
    system: str = "http://unitsofmeasure.org",
    code: str | None = None,
) -> dict[str, Any]:
    """Build a FHIR Quantity."""
    out: dict[str, Any] = {"value": value}
    if unit:
        out["unit"] = unit
    if system:
        out["system"] = system
    if code or unit:
        out["code"] = code or unit
    return out


def ucum_quantity(value: int | float, unit: str, code: str | None = None) -> dict[str, Any]:
    """Build a UCUM Quantity."""
    return quantity(value, unit=unit, system=UCUM_SYSTEM, code=code)


def attachment(
    url: str | None = None,
    *,
    content_type: str | None = None,
    title: str | None = None,
    data: str | None = None,
    creation: str | None = None,
) -> dict[str, Any]:
    """Build a FHIR Attachment."""
    out: dict[str, Any] = {}
    if url:
        out["url"] = url
    if content_type:
        out["contentType"] = content_type
    if title:
        out["title"] = title
    if data:
        out["data"] = data
    if creation:
        out["creation"] = creation
    if not out:
        raise ValueError("attachment requires at least one value")
    return out


def build_observation(
    *,
    subject: str | dict[str, Any],
    code: dict[str, Any] | str,
    value: Any | None = None,
    status: str = "final",
    observation_id: str | None = None,
    effective: str | None = None,
    issued: str | None = None,
    category: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    unit: str | None = None,
    value_type: str = "quantity",
    derived_from: Sequence[str | dict[str, Any]] | None = None,
    method: dict[str, Any] | str | None = None,
    body_site: dict[str, Any] | str | None = None,
    imaging_series_uid: str | None = None,
    components: Sequence[dict[str, Any]] | None = None,
    data_absent_reason: dict[str, Any] | str | None = None,
    performer: Sequence[str | dict[str, Any]] | None = None,
    encounter: str | dict[str, Any] | None = None,
    interpretation: dict[str, Any] | str | Sequence[dict[str, Any] | str] | None = None,
    note: str | Sequence[str] | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR Observation for extracted or measured values."""
    _normalize_version(version)
    obs: dict[str, Any] = {
        "resourceType": "Observation",
        "status": status,
        "subject": reference(subject),
        "code": _as_codeable(code),
    }
    _set_id(obs, observation_id)
    if effective:
        obs["effectiveDateTime"] = effective
    if issued:
        obs["issued"] = issued
    if category:
        obs["category"] = list(category) if isinstance(category, Sequence) and not isinstance(category, dict) else [category]
    if value is not None:
        _add_observation_value(obs, value=value, unit=unit, value_type=value_type)
    if data_absent_reason:
        if value is not None:
            raise ValueError("data_absent_reason cannot be used when value is provided")
        obs["dataAbsentReason"] = _as_codeable(data_absent_reason)
    if components:
        obs["component"] = list(components)
    if derived_from:
        obs["derivedFrom"] = [reference(item) for item in derived_from]
    if performer:
        obs["performer"] = [reference(item) for item in performer]
    if encounter:
        obs["encounter"] = reference(encounter)
    if method:
        obs["method"] = _as_codeable(method)
    if body_site:
        obs["bodySite"] = _as_codeable(body_site)
    if interpretation:
        values = list(interpretation) if isinstance(interpretation, Sequence) and not isinstance(interpretation, (str, dict)) else [interpretation]
        obs["interpretation"] = [_as_codeable(item) for item in values if item is not None]
    if note:
        notes = list(note) if isinstance(note, Sequence) and not isinstance(note, str) else [note]
        obs["note"] = [{"text": str(item)} for item in notes if item]
    if imaging_series_uid:
        obs.setdefault("extension", []).append({"url": FYRON_SERIES_UID_EXTENSION, "valueString": imaging_series_uid})
    _mark_version(obs, version)
    _apply_resource_metadata(obs, profile=profile, identifier=identifier, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return obs


def build_observation_component(
    *,
    code: dict[str, Any] | str,
    value: Any | None = None,
    unit: str | None = None,
    value_type: str = "quantity",
    data_absent_reason: dict[str, Any] | str | None = None,
    interpretation: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Build a FHIR Observation.component item."""
    component = {"code": _as_codeable(code)}
    if value is not None:
        _add_observation_value(component, value=value, unit=unit, value_type=value_type)
    if data_absent_reason:
        if value is not None:
            raise ValueError("data_absent_reason cannot be used when value is provided")
        component["dataAbsentReason"] = _as_codeable(data_absent_reason)
    if interpretation:
        component["interpretation"] = [_as_codeable(interpretation)]
    return component


def build_condition(
    *,
    subject: str | dict[str, Any],
    code: dict[str, Any] | str,
    condition_id: str | None = None,
    clinical_status: dict[str, Any] | str | None = None,
    verification_status: dict[str, Any] | str | None = None,
    onset: str | None = None,
    recorded_date: str | None = None,
    evidence: Sequence[str | dict[str, Any]] | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR Condition with optional evidence links."""
    _normalize_version(version)
    condition: dict[str, Any] = {
        "resourceType": "Condition",
        "subject": reference(subject),
        "code": _as_codeable(code),
    }
    _set_id(condition, condition_id)
    if clinical_status:
        condition["clinicalStatus"] = _as_codeable(clinical_status)
    if verification_status:
        condition["verificationStatus"] = _as_codeable(verification_status)
    if onset:
        condition["onsetDateTime"] = onset
    if recorded_date:
        condition["recordedDate"] = recorded_date
    if evidence:
        condition["evidence"] = [{"detail": [reference(item) for item in evidence]}]
    _mark_version(condition, version)
    _apply_resource_metadata(condition, profile=profile, identifier=identifier, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return condition


def build_document_reference(
    *,
    subject: str | dict[str, Any],
    url: str | None = None,
    title: str | None = None,
    content_type: str | None = None,
    document_id: str | None = None,
    status: str = "current",
    doc_status: str | None = None,
    type_code: dict[str, Any] | str | None = None,
    date: str | None = None,
    description: str | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR DocumentReference for source reports or generated summaries."""
    _normalize_version(version)
    doc: dict[str, Any] = {
        "resourceType": "DocumentReference",
        "status": status,
        "subject": reference(subject),
        "content": [{"attachment": attachment(url=url, title=title, content_type=content_type)}],
    }
    _set_id(doc, document_id)
    if doc_status:
        doc["docStatus"] = doc_status
    if type_code:
        doc["type"] = _as_codeable(type_code)
    if date:
        doc["date"] = date
    if description:
        doc["description"] = description
    _mark_version(doc, version)
    _apply_resource_metadata(doc, profile=profile, identifier=identifier, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return doc


def build_diagnostic_report(
    *,
    subject: str | dict[str, Any],
    code: dict[str, Any] | str,
    results: Sequence[str | dict[str, Any]] | None = None,
    report_id: str | None = None,
    status: str = "final",
    effective: str | None = None,
    issued: str | None = None,
    imaging_study: Sequence[str | dict[str, Any]] | None = None,
    conclusion: str | None = None,
    presented_form: Sequence[dict[str, Any]] | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR DiagnosticReport that groups observations or summaries."""
    _normalize_version(version)
    report: dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "status": status,
        "subject": reference(subject),
        "code": _as_codeable(code),
    }
    _set_id(report, report_id)
    if results:
        report["result"] = [reference(item) for item in results]
    if effective:
        report["effectiveDateTime"] = effective
    if issued:
        report["issued"] = issued
    if imaging_study:
        report["imagingStudy"] = [reference(item) for item in imaging_study]
    if conclusion:
        report["conclusion"] = conclusion
    if presented_form:
        report["presentedForm"] = list(presented_form)
    _mark_version(report, version)
    _apply_resource_metadata(report, profile=profile, identifier=identifier, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return report


def build_imaging_study_reference(
    *,
    subject: str | dict[str, Any],
    study_instance_uid: str,
    imaging_study_id: str | None = None,
    series_instance_uid: str | None = None,
    series_description: str | None = None,
    modality_code: str | None = None,
    started: str | None = None,
    profile: str | Sequence[str] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a minimal FHIR ImagingStudy resource with optional series context."""
    _normalize_version(version)
    study: dict[str, Any] = {
        "resourceType": "ImagingStudy",
        "status": "available",
        "subject": reference(subject),
        "identifier": [identifier(study_instance_uid, system="urn:dicom:uid")],
    }
    _set_id(study, imaging_study_id)
    study["uid"] = study_instance_uid
    if started:
        study["started"] = started
    if series_instance_uid:
        series: dict[str, Any] = {"uid": series_instance_uid}
        if series_description:
            series["description"] = series_description
        if modality_code:
            series["modality"] = coding(modality_code, system="http://dicom.nema.org/resources/ontology/DCM")
        study["series"] = [series]
    _mark_version(study, version)
    _apply_resource_metadata(study, profile=profile, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return study


def build_model_device(
    *,
    model_name: str,
    model_version: str | None = None,
    device_id: str | None = None,
    manufacturer: str = "Bits & Flames",
    endpoint: str | dict[str, Any] | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR Device resource for an AI/model system."""
    _normalize_version(version)
    device: dict[str, Any] = {
        "resourceType": "Device",
        "manufacturer": manufacturer,
        "deviceName": [{"name": model_name, "type": "user-friendly-name"}],
    }
    _set_id(device, device_id)
    if model_version:
        device.setdefault("extension", []).append({"url": FYRON_MODEL_VERSION_EXTENSION, "valueString": model_version})
        device["version"] = [{"value": model_version}]
    if endpoint:
        device.setdefault("extension", []).append({"url": "https://bitsandflames.com/fhir/StructureDefinition/model-endpoint", "valueReference": reference(endpoint)})
    _mark_version(device, version)
    _apply_resource_metadata(device, profile=profile, identifier=identifier, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return device


def build_endpoint(
    *,
    address: str,
    endpoint_id: str | None = None,
    name: str | None = None,
    status: str = "active",
    connection_type_code: str = "hl7-fhir-rest",
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR Endpoint resource for a model or FHIR API endpoint."""
    _normalize_version(version)
    endpoint = {
        "resourceType": "Endpoint",
        "status": status,
        "connectionType": coding(connection_type_code, system="http://terminology.hl7.org/CodeSystem/endpoint-connection-type"),
        "address": address,
    }
    _set_id(endpoint, endpoint_id)
    if name:
        endpoint["name"] = name
    _mark_version(endpoint, version)
    _apply_resource_metadata(endpoint, profile=profile, identifier=identifier, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return endpoint


def build_provenance(
    *,
    targets: Sequence[str | dict[str, Any]],
    agent: str | dict[str, Any] | None = None,
    entity: Sequence[str | dict[str, Any]] | None = None,
    provenance_id: str | None = None,
    recorded: str | None = None,
    activity: dict[str, Any] | str | None = None,
    prompt_version: str | None = None,
    profile: str | Sequence[str] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR Provenance resource linking generated outputs to evidence."""
    _normalize_version(version)
    provenance: dict[str, Any] = {
        "resourceType": "Provenance",
        "target": [reference(item) for item in targets],
        "agent": [{"who": reference(agent or "Device/fyron")}],
    }
    _set_id(provenance, provenance_id)
    if recorded:
        provenance["recorded"] = recorded
    if activity:
        provenance["activity"] = _as_codeable(activity)
    if entity:
        provenance["entity"] = [{"role": "source", "what": reference(item)} for item in entity]
    if prompt_version:
        provenance.setdefault("extension", []).append({"url": FYRON_PROMPT_VERSION_EXTENSION, "valueString": prompt_version})
    _mark_version(provenance, version)
    _apply_resource_metadata(provenance, profile=profile, meta_source=meta_source, tag=tag, security=security, extension=extension)
    return provenance


def build_encounter(
    *,
    subject: str | dict[str, Any],
    status: str = "finished",
    encounter_class: dict[str, Any] | str | None = None,
    encounter_id: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    reason_code: dict[str, Any] | str | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a minimal FHIR Encounter resource."""
    _normalize_version(version)
    encounter: dict[str, Any] = {"resourceType": "Encounter", "status": status, "subject": reference(subject)}
    _set_id(encounter, encounter_id)
    if encounter_class:
        encounter["class"] = encounter_class if isinstance(encounter_class, dict) else coding(str(encounter_class))
    if period_start or period_end:
        encounter["period"] = {}
        if period_start:
            encounter["period"]["start"] = period_start
        if period_end:
            encounter["period"]["end"] = period_end
    if reason_code:
        encounter["reasonCode"] = [_as_codeable(reason_code)]
    _mark_version(encounter, version)
    _apply_resource_metadata(encounter, profile=profile, identifier=identifier)
    return encounter


def build_procedure(
    *,
    subject: str | dict[str, Any],
    code: dict[str, Any] | str,
    procedure_id: str | None = None,
    status: str = "completed",
    performed: str | None = None,
    encounter: str | dict[str, Any] | None = None,
    reason_code: dict[str, Any] | str | None = None,
    body_site: dict[str, Any] | str | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a minimal FHIR Procedure resource."""
    _normalize_version(version)
    procedure: dict[str, Any] = {"resourceType": "Procedure", "status": status, "subject": reference(subject), "code": _as_codeable(code)}
    _set_id(procedure, procedure_id)
    if performed:
        procedure["performedDateTime"] = performed
    if encounter:
        procedure["encounter"] = reference(encounter)
    if reason_code:
        procedure["reasonCode"] = [_as_codeable(reason_code)]
    if body_site:
        procedure["bodySite"] = [_as_codeable(body_site)]
    _mark_version(procedure, version)
    _apply_resource_metadata(procedure, profile=profile, identifier=identifier)
    return procedure


def build_medication_statement(
    *,
    subject: str | dict[str, Any],
    medication: dict[str, Any] | str,
    medication_statement_id: str | None = None,
    status: str = "active",
    effective: str | None = None,
    date_asserted: str | None = None,
    reason_code: dict[str, Any] | str | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a minimal FHIR MedicationStatement resource."""
    _normalize_version(version)
    statement: dict[str, Any] = {
        "resourceType": "MedicationStatement",
        "status": status,
        "subject": reference(subject),
        "medicationCodeableConcept": _as_codeable(medication),
    }
    _set_id(statement, medication_statement_id)
    if effective:
        statement["effectiveDateTime"] = effective
    if date_asserted:
        statement["dateAsserted"] = date_asserted
    if reason_code:
        statement["reasonCode"] = [_as_codeable(reason_code)]
    _mark_version(statement, version)
    _apply_resource_metadata(statement, profile=profile, identifier=identifier)
    return statement


def build_service_request(
    *,
    subject: str | dict[str, Any],
    code: dict[str, Any] | str,
    service_request_id: str | None = None,
    status: str = "active",
    intent: str = "order",
    authored_on: str | None = None,
    requester: str | dict[str, Any] | None = None,
    reason_code: dict[str, Any] | str | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a minimal FHIR ServiceRequest resource."""
    _normalize_version(version)
    request: dict[str, Any] = {"resourceType": "ServiceRequest", "status": status, "intent": intent, "subject": reference(subject), "code": _as_codeable(code)}
    _set_id(request, service_request_id)
    if authored_on:
        request["authoredOn"] = authored_on
    if requester:
        request["requester"] = reference(requester)
    if reason_code:
        request["reasonCode"] = [_as_codeable(reason_code)]
    _mark_version(request, version)
    _apply_resource_metadata(request, profile=profile, identifier=identifier)
    return request


def build_specimen(
    *,
    subject: str | dict[str, Any],
    specimen_type: dict[str, Any] | str | None = None,
    specimen_id: str | None = None,
    status: str = "available",
    received_time: str | None = None,
    collection_time: str | None = None,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a minimal FHIR Specimen resource."""
    _normalize_version(version)
    specimen: dict[str, Any] = {"resourceType": "Specimen", "status": status, "subject": reference(subject)}
    _set_id(specimen, specimen_id)
    if specimen_type:
        specimen["type"] = _as_codeable(specimen_type)
    if received_time:
        specimen["receivedTime"] = received_time
    if collection_time:
        specimen["collection"] = {"collectedDateTime": collection_time}
    _mark_version(specimen, version)
    _apply_resource_metadata(specimen, profile=profile, identifier=identifier)
    return specimen


def build_bundle(
    resources: Sequence[dict[str, Any]],
    *,
    bundle_type: str,
    bundle_id: str | None = None,
    transaction_method: str = "POST",
    if_none_exist: str | dict[str, str] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a collection or transaction FHIR Bundle."""
    _normalize_version(version)
    if bundle_type not in {"collection", "transaction"}:
        raise ValueError("bundle_type must be 'collection' or 'transaction'")
    bundle = {
        "resourceType": "Bundle",
        "type": bundle_type,
        "entry": [
            _bundle_entry(
                resource,
                bundle_type=bundle_type,
                transaction_method=transaction_method,
                if_none_exist=if_none_exist,
            )
            for resource in resources
        ],
    }
    _set_id(bundle, bundle_id)
    _mark_version(bundle, version)
    return bundle


def build_llm_extraction_bundle(
    *,
    subject: str | dict[str, Any],
    source_report_url: str,
    observations: Sequence[dict[str, Any]] | None = None,
    conditions: Sequence[dict[str, Any]] | None = None,
    summary_text: str | None = None,
    model_name: str,
    model_endpoint_url: str | None = None,
    model_version: str | None = None,
    prompt_version: str | None = None,
    id_prefix: str | None = None,
    bundle_type: str,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR bundle for LLM-extracted report evidence."""
    prefix = f"{id_prefix}-" if id_prefix else ""
    doc = build_document_reference(
        subject=subject,
        url=source_report_url,
        title="Source clinical report",
        content_type="application/pdf",
        document_id=f"{prefix}source-report",
        version=version,
    )
    endpoint_resource = (
        build_endpoint(address=model_endpoint_url, endpoint_id=f"{prefix}model-endpoint", name=f"{model_name} endpoint", version=version)
        if model_endpoint_url
        else None
    )
    device = build_model_device(
        model_name=model_name,
        model_version=model_version,
        device_id=f"{prefix}model-device",
        endpoint=endpoint_resource,
        version=version,
    )
    resources: list[dict[str, Any]] = [doc]
    resources.extend(_with_source_links(observations or [], source=doc))
    resources.extend(_with_condition_evidence(conditions or [], source=doc))
    if summary_text:
        resources.append(
            build_diagnostic_report(
                subject=subject,
                code=codeable_concept(text="LLM generated report summary"),
                report_id=f"{prefix}llm-summary",
                conclusion=summary_text,
                presented_form=[attachment(data=summary_text, content_type="text/plain", title="Generated summary")],
                version=version,
            )
        )
    if endpoint_resource:
        resources.append(endpoint_resource)
    resources.append(device)
    provenance_targets = [resource for resource in resources if resource["resourceType"] in {"Observation", "Condition", "DiagnosticReport"}]
    if provenance_targets:
        resources.append(
            build_provenance(
                targets=provenance_targets,
                agent=device,
                entity=[doc],
                provenance_id=f"{prefix}llm-extraction-provenance",
                activity=codeable_concept(text="LLM extraction"),
                prompt_version=prompt_version,
                version=version,
            )
        )
    return build_bundle(resources, bundle_type=bundle_type, version=version)


def build_imaging_measurement_bundle(
    *,
    subject: str | dict[str, Any],
    study_instance_uid: str,
    measurements: Sequence[dict[str, Any]],
    series_instance_uid: str | None = None,
    series_description: str | None = None,
    model_name: str | None = None,
    model_endpoint_url: str | None = None,
    id_prefix: str | None = None,
    bundle_type: str,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build a FHIR bundle for imaging-derived quantitative measurements."""
    prefix = f"{id_prefix}-" if id_prefix else ""
    imaging = build_imaging_study_reference(
        subject=subject,
        study_instance_uid=study_instance_uid,
        imaging_study_id=f"{prefix}source-imaging-study",
        series_instance_uid=series_instance_uid,
        series_description=series_description,
        version=version,
    )
    observations = [
        build_observation(
            subject=subject,
            code=item["code"],
            value=item.get("value"),
            unit=item.get("unit"),
            observation_id=item.get("id"),
            effective=item.get("effective"),
            method=item.get("method"),
            body_site=item.get("body_site"),
            derived_from=[imaging],
            imaging_series_uid=series_instance_uid,
            version=version,
        )
        for item in measurements
    ]
    report = build_diagnostic_report(
        subject=subject,
        code=codeable_concept(text="Imaging-derived measurements"),
        results=observations,
        report_id=f"{prefix}imaging-measurement-report",
        imaging_study=[imaging],
        version=version,
    )
    resources: list[dict[str, Any]] = [imaging, *observations, report]
    endpoint_resource = None
    device = None
    if model_name:
        endpoint_resource = (
            build_endpoint(address=model_endpoint_url, endpoint_id=f"{prefix}model-endpoint", name=f"{model_name} endpoint", version=version)
            if model_endpoint_url
            else None
        )
        device = build_model_device(model_name=model_name, device_id=f"{prefix}model-device", endpoint=endpoint_resource, version=version)
        if endpoint_resource:
            resources.append(endpoint_resource)
        resources.append(device)
    resources.append(
        build_provenance(
            targets=[*observations, report],
            agent=device or "Device/fyron",
            entity=[imaging],
            provenance_id=f"{prefix}imaging-measurement-provenance",
            activity=codeable_concept(text="Imaging measurement extraction"),
            version=version,
        )
    )
    return build_bundle(resources, bundle_type=bundle_type, version=version)


def write_fhir_json(payload: dict[str, Any], path: StrPath) -> Path:
    """Write a FHIR JSON payload to disk."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    return out.resolve()


def read_fhir_json(path: StrPath) -> dict[str, Any]:
    """Read a FHIR JSON payload from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize_fhir_resource(resource: dict[str, Any]) -> dict[str, Any]:
    """Return a compact, inspectable summary for one FHIR resource."""
    validate_fhir_resource(resource)
    return {
        "resource_type": resource["resourceType"],
        "id": resource.get("id"),
        "reference": _resource_reference(resource),
        "profile": [item for item in resource.get("meta", {}).get("profile", [])],
        "version_tags": [
            tag.get("code")
            for tag in resource.get("meta", {}).get("tag", [])
            if tag.get("system") == FYRON_MODEL_SYSTEM
        ],
        "references": _iter_references(resource),
    }


def validate_fhir_references(bundle: dict[str, Any]) -> dict[str, Any]:
    """Inspect local references inside a FHIR Bundle without mutating it."""
    if bundle.get("resourceType") != "Bundle":
        raise ValueError("FHIR bundle must have resourceType='Bundle'")
    entries = bundle.get("entry") or []
    known_refs = _known_bundle_references(entries)
    references: list[dict[str, Any]] = []
    missing: list[str] = []
    for entry in entries:
        resource = entry.get("resource")
        if not isinstance(resource, dict):
            continue
        source = _resource_reference(resource)
        for ref in _iter_references(resource):
            local = _is_local_reference(ref)
            resolved = (not local) or ref in known_refs
            references.append({"source": source, "reference": ref, "local": local, "resolved": resolved})
            if local and not resolved:
                missing.append(ref)
    return {"valid": not missing, "references": references, "missing_references": sorted(set(missing))}


def summarize_fhir_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return bundle counts, request methods, and local-reference status."""
    validate_fhir_bundle(bundle)
    entries = bundle.get("entry") or []
    resource_types: dict[str, int] = {}
    request_methods: dict[str, int] = {}
    resource_summaries = []
    for entry in entries:
        resource = entry.get("resource")
        if isinstance(resource, dict):
            resource_type = resource.get("resourceType", "Unknown")
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
            resource_summaries.append(summarize_fhir_resource(resource))
        request = entry.get("request") or {}
        method = request.get("method")
        if method:
            request_methods[method] = request_methods.get(method, 0) + 1
    reference_summary = validate_fhir_references(bundle)
    return {
        "resource_type": "Bundle",
        "bundle_type": bundle.get("type"),
        "id": bundle.get("id"),
        "entry_count": len(entries),
        "resource_types": resource_types,
        "transaction_methods": request_methods,
        "local_references_valid": reference_summary["valid"],
        "missing_references": reference_summary["missing_references"],
        "resources": resource_summaries,
    }


def validate_fhir_resource(resource: dict[str, Any], version: str = FHIR_R4) -> dict[str, Any]:
    """Lightweight structural validation for a FHIR resource dictionary."""
    resolved_version = _normalize_version(version)
    if not isinstance(resource, dict):
        raise ValueError("FHIR resource must be a dictionary")
    resource_type = resource.get("resourceType")
    if not resource_type:
        raise ValueError("FHIR resource is missing resourceType")
    if resource_type == "Bundle":
        return validate_fhir_bundle(resource, version=version)
    _validate_required_fields(resource)
    if resolved_version == FHIR_R6:
        _mark_version(resource, FHIR_R6)
    return resource


def validate_fhir_bundle(bundle: dict[str, Any], version: str = FHIR_R4) -> dict[str, Any]:
    """Lightweight structural validation for a FHIR Bundle."""
    _normalize_version(version)
    if bundle.get("resourceType") != "Bundle":
        raise ValueError("FHIR bundle must have resourceType='Bundle'")
    bundle_type = bundle.get("type")
    if bundle_type not in {"collection", "transaction"}:
        raise ValueError("FHIR bundle type must be 'collection' or 'transaction'")
    entries = bundle.get("entry") or []
    known_refs = _known_bundle_references(entries)
    for entry in entries:
        resource = entry.get("resource")
        validate_fhir_resource(resource, version=version)
        if bundle_type == "transaction" and "request" not in entry:
            raise ValueError("transaction bundle entries must include request")
        for ref in _iter_references(resource):
            if _is_local_reference(ref) and ref not in known_refs:
                raise ValueError(f"Broken local reference: {ref}")
    return bundle


def _bundle_entry(
    resource: dict[str, Any],
    *,
    bundle_type: str,
    transaction_method: str = "POST",
    if_none_exist: str | dict[str, str] | None = None,
) -> dict[str, Any]:
    validate_fhir_resource(resource)
    full_url = _entry_full_url(resource)
    entry = {"fullUrl": full_url, "resource": resource}
    if bundle_type == "transaction":
        method = transaction_method.upper()
        if method not in {"POST", "PUT"}:
            raise ValueError("transaction_method must be 'POST' or 'PUT'")
        request = {"method": method, "url": _transaction_url(resource, method)}
        conditional = _if_none_exist_for_resource(resource, if_none_exist)
        if conditional:
            if method != "POST":
                raise ValueError("if_none_exist is only supported for POST transaction entries")
            request["ifNoneExist"] = conditional
        entry["request"] = request
    return entry


def _transaction_url(resource: dict[str, Any], method: str) -> str:
    resource_type = resource["resourceType"]
    if method == "POST":
        return resource_type
    resource_id = resource.get("id")
    if not resource_id:
        raise ValueError("PUT transaction entries require resource ids")
    return f"{resource_type}/{resource_id}"


def _if_none_exist_for_resource(resource: dict[str, Any], if_none_exist: str | dict[str, str] | None) -> str | None:
    if isinstance(if_none_exist, str):
        return if_none_exist
    if isinstance(if_none_exist, dict):
        return if_none_exist.get(_resource_reference(resource)) or if_none_exist.get(resource["resourceType"]) or if_none_exist.get(resource.get("id", ""))
    return None


def _known_bundle_references(entries: Sequence[dict[str, Any]]) -> set[str]:
    local_refs = {entry.get("fullUrl") for entry in entries if entry.get("fullUrl")}
    resource_refs = {
        _resource_reference(entry["resource"])
        for entry in entries
        if isinstance(entry.get("resource"), dict)
    }
    return {ref for ref in local_refs | resource_refs if ref}


def _is_local_reference(ref: str) -> bool:
    if ref.startswith("urn:uuid:"):
        return True
    resource_type = ref.split("/", 1)[0]
    return resource_type in {
        "Observation",
        "Condition",
        "DocumentReference",
        "DiagnosticReport",
        "Encounter",
        "Procedure",
        "MedicationStatement",
        "ServiceRequest",
        "Specimen",
        "Provenance",
        "Bundle",
    }


def _validate_required_fields(resource: dict[str, Any]) -> None:
    resource_type = resource.get("resourceType")
    required_by_type = {
        "Observation": ("status", "code", "subject"),
        "Condition": ("code", "subject"),
        "DocumentReference": ("status", "content"),
        "DiagnosticReport": ("status", "code", "subject"),
        "ImagingStudy": ("status", "subject", "uid"),
        "Device": ("deviceName",),
        "Endpoint": ("status", "connectionType", "address"),
        "Provenance": ("target", "agent"),
        "Encounter": ("status", "subject"),
        "Procedure": ("status", "code", "subject"),
        "MedicationStatement": ("status", "medicationCodeableConcept", "subject"),
        "ServiceRequest": ("status", "intent", "code", "subject"),
        "Specimen": ("status", "subject"),
    }
    missing = [field for field in required_by_type.get(resource_type, ()) if not resource.get(field)]
    if missing:
        raise ValueError(f"{resource_type} is missing required field(s): {', '.join(missing)}")


def _apply_resource_metadata(
    resource: dict[str, Any],
    *,
    profile: str | Sequence[str] | None = None,
    identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    meta_source: str | None = None,
    tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    security: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
    extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None,
) -> None:
    if profile:
        profiles = [profile] if isinstance(profile, str) else list(profile)
        resource.setdefault("meta", {})["profile"] = profiles
    if meta_source:
        resource.setdefault("meta", {})["source"] = meta_source
    if tag:
        resource.setdefault("meta", {}).setdefault("tag", []).extend(_as_list(tag))
    if security:
        resource.setdefault("meta", {}).setdefault("security", []).extend(_as_list(security))
    if identifier:
        resource.setdefault("identifier", []).extend(_as_list(identifier))
    if extension:
        resource.setdefault("extension", []).extend(_as_list(extension))


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _entry_full_url(resource: dict[str, Any]) -> str:
    resource_id = resource.get("id")
    if resource_id:
        return _resource_reference(resource)
    seed = json.dumps(resource, sort_keys=True, default=str)
    return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, seed)}"


def _resource_reference(resource: dict[str, Any]) -> str:
    resource_type = resource.get("resourceType")
    resource_id = resource.get("id")
    if resource_type and resource_id:
        return f"{resource_type}/{resource_id}"
    return _entry_full_url(resource)


def _set_id(resource: dict[str, Any], resource_id: str | None) -> None:
    if resource_id:
        resource["id"] = resource_id


def _as_codeable(value: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, dict):
        if "coding" in value or "text" in value:
            return value
        if "code" in value:
            return codeable_concept(code=value.get("code"), system=value.get("system"), display=value.get("display"), text=value.get("text"))
    return codeable_concept(text=str(value))


def _add_observation_value(obs: dict[str, Any], *, value: Any, unit: str | None, value_type: str) -> None:
    if value_type == "quantity":
        obs["valueQuantity"] = quantity(value, unit=unit)
    elif value_type == "string":
        obs["valueString"] = str(value)
    elif value_type == "codeable":
        obs["valueCodeableConcept"] = _as_codeable(value)
    elif value_type == "boolean":
        obs["valueBoolean"] = bool(value)
    else:
        raise ValueError("value_type must be one of: quantity, string, codeable, boolean")


def _normalize_version(version: str) -> str:
    resolved = str(version).upper()
    if resolved not in SUPPORTED_FHIR_VERSIONS:
        raise ValueError("version must be 'R4' or 'R6'")
    return resolved


def _mark_version(resource: dict[str, Any], version: str) -> None:
    resolved = _normalize_version(version)
    resource.setdefault("meta", {})
    resource["meta"]["tag"] = [
        tag for tag in resource["meta"].get("tag", [])
        if not (tag.get("system") == FYRON_MODEL_SYSTEM and tag.get("code", "").startswith("fhir-"))
    ]
    resource["meta"]["tag"].append(coding(f"fhir-{resolved.lower()}", system=FYRON_MODEL_SYSTEM, display=f"FHIR {resolved}"))
    if resolved == FHIR_R6:
        resource["meta"]["tag"].append(coding("experimental-r6", system=FYRON_MODEL_SYSTEM, display="FHIR R6 experimental/ballot-aware"))


def _with_source_links(resources: Sequence[dict[str, Any]], *, source: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for resource in resources:
        copy = dict(resource)
        if copy.get("resourceType") == "Observation":
            refs = list(copy.get("derivedFrom", []))
            refs.append(reference(source))
            copy["derivedFrom"] = refs
        out.append(copy)
    return out


def _with_condition_evidence(resources: Sequence[dict[str, Any]], *, source: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for resource in resources:
        copy = dict(resource)
        if copy.get("resourceType") == "Condition":
            evidence = list(copy.get("evidence", []))
            evidence.append({"detail": [reference(source)]})
            copy["evidence"] = evidence
        out.append(copy)
    return out


def _iter_references(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        ref = value.get("reference")
        if isinstance(ref, str):
            refs.append(ref)
        for item in value.values():
            refs.extend(_iter_references(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(_iter_references(item))
    return refs


__all__ = [
    "FHIR_R4",
    "FHIR_R6",
    "DICOM_SYSTEM",
    "ICD10_SYSTEM",
    "LOINC_SYSTEM",
    "SNOMED_SYSTEM",
    "SUPPORTED_FHIR_VERSIONS",
    "UCUM_SYSTEM",
    "attachment",
    "build_bundle",
    "build_condition",
    "build_diagnostic_report",
    "build_document_reference",
    "build_encounter",
    "build_endpoint",
    "build_imaging_measurement_bundle",
    "build_imaging_study_reference",
    "build_llm_extraction_bundle",
    "build_medication_statement",
    "build_model_device",
    "build_observation",
    "build_observation_component",
    "build_procedure",
    "build_provenance",
    "build_service_request",
    "build_specimen",
    "codeable_concept",
    "coding",
    "dicom_code",
    "icd10",
    "identifier",
    "loinc",
    "quantity",
    "read_fhir_json",
    "reference",
    "snomed",
    "summarize_fhir_bundle",
    "summarize_fhir_resource",
    "ucum_quantity",
    "validate_fhir_bundle",
    "validate_fhir_references",
    "validate_fhir_resource",
    "write_fhir_json",
]
