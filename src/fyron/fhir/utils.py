"""FHIR resource extraction helpers."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .types import FHIRObj


def _ensure_fhir_obj(resource: Any) -> FHIRObj:
    if isinstance(resource, FHIRObj):
        return resource
    if isinstance(resource, dict):
        return FHIRObj(**resource)
    raise TypeError("resource must be a dict or FHIRObj")


def safe_get(resource: Any, path: str | List[Any] | tuple[Any, ...], default: Any = None) -> Any:
    """Safely extract a value from nested FHIR JSON or FHIRObj by path.

    Path examples:
    - "code.coding[0].code"
    - "subject.reference"
    - ["name", 0, "family"]
    """
    if resource is None:
        return default
    if isinstance(path, (list, tuple)):
        tokens: List[Any] = list(path)
    else:
        tokens = []
        for segment in str(path).split("."):
            if not segment:
                continue
            for match in re.finditer(r"([^\[\]]+)|\[(\d+)\]", segment):
                key = match.group(1)
                index = match.group(2)
                if key is not None:
                    tokens.append(key)
                elif index is not None:
                    tokens.append(int(index))
    current: Any = resource
    for token in tokens:
        if current is None:
            return default
        if isinstance(token, int):
            if isinstance(current, (list, tuple)) and 0 <= token < len(current):
                current = current[token]
            else:
                return default
        else:
            if isinstance(current, dict):
                current = current.get(token)
            else:
                current = getattr(current, token, None)
    return current if current is not None else default


def _first(items: Optional[List[Any]]) -> Any:
    if not items:
        return None
    return items[0]


def _join_tokens(tokens: Optional[List[str]]) -> Optional[str]:
    if not tokens:
        return None
    return " ".join([t for t in tokens if t]) or None


def _ref(ref: Any) -> Optional[str]:
    if ref is None:
        return None
    if isinstance(ref, str):
        return ref
    return getattr(ref, "reference", None)


def _codeable(concept: Any) -> Dict[str, Optional[str]]:
    if concept is None:
        return {
            "code": None,
            "system": None,
            "display": None,
            "text": None,
        }
    coding = _first(getattr(concept, "coding", None) or [])
    return {
        "code": getattr(coding, "code", None),
        "system": getattr(coding, "system", None),
        "display": getattr(coding, "display", None),
        "text": getattr(concept, "text", None),
    }


def _period(period: Any) -> Dict[str, Optional[str]]:
    if period is None:
        return {"start": None, "end": None}
    return {
        "start": getattr(period, "start", None),
        "end": getattr(period, "end", None),
    }


def extract_patient(resource: Any) -> Dict[str, Any]:
    patient = _ensure_fhir_obj(resource)
    name = _first(getattr(patient, "name", None) or [])
    identifier = _first(getattr(patient, "identifier", None) or [])
    telecom = getattr(patient, "telecom", None) or []
    phone = _first([t for t in telecom if getattr(t, "system", None) == "phone"])  # type: ignore[list-item]
    email = _first([t for t in telecom if getattr(t, "system", None) == "email"])  # type: ignore[list-item]
    full_name = getattr(name, "text", None)
    if not full_name:
        given = _join_tokens(getattr(name, "given", None))
        family = getattr(name, "family", None)
        full_name = " ".join([t for t in [given, family] if t]) or None

    return {
        "id": getattr(patient, "id", None),
        "identifier": getattr(identifier, "value", None),
        "identifier_system": getattr(identifier, "system", None),
        "name": full_name,
        "gender": getattr(patient, "gender", None),
        "birthDate": getattr(patient, "birthDate", None),
        "deceased": getattr(patient, "deceasedBoolean", None) or getattr(patient, "deceasedDateTime", None),
        "phone": getattr(phone, "value", None),
        "email": getattr(email, "value", None),
    }


def extract_encounter(resource: Any) -> Dict[str, Any]:
    encounter = _ensure_fhir_obj(resource)
    enc_class = getattr(encounter, "class", None)
    enc_type = _first(getattr(encounter, "type", None) or [])
    period = _period(getattr(encounter, "period", None))
    return {
        "id": getattr(encounter, "id", None),
        "status": getattr(encounter, "status", None),
        "class_code": getattr(enc_class, "code", None),
        "class_display": getattr(enc_class, "display", None),
        "type_code": _codeable(enc_type)["code"],
        "type_display": _codeable(enc_type)["display"],
        "subject": _ref(getattr(encounter, "subject", None)),
        "start": period["start"],
        "end": period["end"],
        "serviceProvider": _ref(getattr(encounter, "serviceProvider", None)),
    }


def extract_observation(resource: Any) -> Dict[str, Any]:
    obs = _ensure_fhir_obj(resource)
    code = _codeable(getattr(obs, "code", None))
    value_quantity = getattr(obs, "valueQuantity", None)
    value_codeable = _codeable(getattr(obs, "valueCodeableConcept", None))
    effective_period = _period(getattr(obs, "effectivePeriod", None))
    return {
        "id": getattr(obs, "id", None),
        "status": getattr(obs, "status", None),
        "code": code["code"],
        "code_system": code["system"],
        "code_display": code["display"],
        "subject": _ref(getattr(obs, "subject", None)),
        "encounter": _ref(getattr(obs, "encounter", None)),
        "effective": getattr(obs, "effectiveDateTime", None) or effective_period["start"],
        "issued": getattr(obs, "issued", None),
        "value": getattr(value_quantity, "value", None) if value_quantity else None,
        "value_unit": getattr(value_quantity, "unit", None) if value_quantity else None,
        "value_code": getattr(value_quantity, "code", None) if value_quantity else None,
        "value_string": getattr(obs, "valueString", None),
        "value_codeable": value_codeable["code"],
    }


def extract_condition(resource: Any) -> Dict[str, Any]:
    cond = _ensure_fhir_obj(resource)
    code = _codeable(getattr(cond, "code", None))
    clinical = _codeable(getattr(cond, "clinicalStatus", None))
    verification = _codeable(getattr(cond, "verificationStatus", None))
    onset_period = _period(getattr(cond, "onsetPeriod", None))
    return {
        "id": getattr(cond, "id", None),
        "clinical_status": clinical["code"],
        "verification_status": verification["code"],
        "code": code["code"],
        "code_system": code["system"],
        "code_display": code["display"],
        "subject": _ref(getattr(cond, "subject", None)),
        "encounter": _ref(getattr(cond, "encounter", None)),
        "onset": getattr(cond, "onsetDateTime", None) or onset_period["start"],
        "recordedDate": getattr(cond, "recordedDate", None),
    }


def extract_procedure(resource: Any) -> Dict[str, Any]:
    proc = _ensure_fhir_obj(resource)
    code = _codeable(getattr(proc, "code", None))
    outcome = _codeable(getattr(proc, "outcome", None))
    performed_period = _period(getattr(proc, "performedPeriod", None))
    return {
        "id": getattr(proc, "id", None),
        "status": getattr(proc, "status", None),
        "code": code["code"],
        "code_system": code["system"],
        "code_display": code["display"],
        "subject": _ref(getattr(proc, "subject", None)),
        "encounter": _ref(getattr(proc, "encounter", None)),
        "performed": getattr(proc, "performedDateTime", None) or performed_period["start"],
        "outcome": outcome["code"],
    }


def extract_imaging_study(resource: Any, series: Any = None) -> Dict[str, Any]:
    study = _ensure_fhir_obj(resource)
    modality = getattr(study, "modality", None) or []
    modality_codes = ",".join([m.code for m in modality if getattr(m, "code", None)]) or None
    series = _ensure_fhir_obj(series) if series is not None else None
    return {
        "id": getattr(study, "id", None),
        "status": getattr(study, "status", None),
        "subject": _ref(getattr(study, "subject", None)),
        "started": getattr(study, "started", None),
        "numberOfSeries": getattr(study, "numberOfSeries", None),
        "numberOfInstances": getattr(study, "numberOfInstances", None),
        "modality_codes": modality_codes,
        "description": getattr(study, "description", None),
        "study_instance_uid": getattr(study, "uid", None),
        "series_instance_uid": getattr(series, "uid", None) if series else None,
        "series_number": getattr(series, "number", None) if series else None,
        "series_modality": getattr(series, "modality", None).code
        if series and getattr(series, "modality", None)
        else None,
        "series_description": getattr(series, "description", None) if series else None,
        "series_started": getattr(series, "started", None) if series else None,
    }


def extract_diagnostic_report(resource: Any) -> Dict[str, Any]:
    report = _ensure_fhir_obj(resource)
    code = _codeable(getattr(report, "code", None))
    effective_period = _period(getattr(report, "effectivePeriod", None))
    results = getattr(report, "result", None) or []
    imaging = getattr(report, "imagingStudy", None) or []
    return {
        "id": getattr(report, "id", None),
        "status": getattr(report, "status", None),
        "code": code["code"],
        "code_system": code["system"],
        "code_display": code["display"],
        "subject": _ref(getattr(report, "subject", None)),
        "encounter": _ref(getattr(report, "encounter", None)),
        "effective": getattr(report, "effectiveDateTime", None) or effective_period["start"],
        "issued": getattr(report, "issued", None),
        "result_count": len(results),
        "imaging_study_count": len(imaging),
        "conclusion": getattr(report, "conclusion", None),
    }


def _process_bundle(bundle: Any, resource_type: str, extractor) -> Dict[str, List[Dict[str, Any]]]:
    b = _ensure_fhir_obj(bundle)
    rows: List[Dict[str, Any]] = []
    for entry in getattr(b, "entry", None) or []:
        resource = getattr(entry, "resource", None)
        if resource is None:
            continue
        if getattr(resource, "resourceType", None) and getattr(resource, "resourceType", None) != resource_type:
            continue
        rows.append(extractor(resource))
    return {resource_type: rows}


def process_patient_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]:
    return _process_bundle(bundle, "Patient", extract_patient)


def process_encounter_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]:
    return _process_bundle(bundle, "Encounter", extract_encounter)


def process_observation_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]:
    return _process_bundle(bundle, "Observation", extract_observation)


def process_condition_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]:
    return _process_bundle(bundle, "Condition", extract_condition)


def process_procedure_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]:
    return _process_bundle(bundle, "Procedure", extract_procedure)


def process_imaging_study_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]:
    b = _ensure_fhir_obj(bundle)
    rows: List[Dict[str, Any]] = []
    for entry in getattr(b, "entry", None) or []:
        resource = getattr(entry, "resource", None)
        if resource is None:
            continue
        if getattr(resource, "resourceType", None) and getattr(resource, "resourceType", None) != "ImagingStudy":
            continue
        series_list = getattr(resource, "series", None) or []
        for series in series_list:
            rows.append(extract_imaging_study(resource, series=series))
    return {"ImagingStudy": rows}


def process_diagnostic_report_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]:
    return _process_bundle(bundle, "DiagnosticReport", extract_diagnostic_report)
