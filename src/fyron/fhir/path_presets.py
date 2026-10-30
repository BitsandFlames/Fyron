"""Reusable FHIRPath extraction presets for common FHIR R4 resources."""

from __future__ import annotations

from typing import Mapping


FHIRPathPreset = tuple[tuple[str, str], ...]


FHIR_PATH_PRESETS: Mapping[str, FHIRPathPreset] = {
    "Patient": (
        ("patient_id", "id"),
        ("identifier_system", "identifier.system"),
        ("identifier_value", "identifier.value"),
        ("gender", "gender"),
        ("birth_date", "birthDate"),
        ("deceased_boolean", "deceasedBoolean"),
        ("deceased_datetime", "deceasedDateTime"),
        ("family_name", "name.family"),
        ("given_name", "name.given"),
    ),
    "Encounter": (
        ("encounter_id", "id"),
        ("patient_reference", "subject.reference"),
        ("status", "status"),
        ("class_code", "class.code"),
        ("class_display", "class.display"),
        ("type_code", "type.coding.code"),
        ("period_start", "period.start"),
        ("period_end", "period.end"),
        ("service_provider_reference", "serviceProvider.reference"),
    ),
    "Condition": (
        ("condition_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "encounter.reference"),
        ("clinical_status", "clinicalStatus.coding.code"),
        ("verification_status", "verificationStatus.coding.code"),
        ("code_system", "code.coding.system"),
        ("code", "code.coding.code"),
        ("display", "code.coding.display"),
        ("recorded_date", "recordedDate"),
        ("onset_datetime", "onsetDateTime"),
        ("abatement_datetime", "abatementDateTime"),
    ),
    "Observation": (
        ("observation_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "encounter.reference"),
        ("status", "status"),
        ("code_system", "code.coding.system"),
        ("code", "code.coding.code"),
        ("display", "code.coding.display"),
        ("effective_datetime", "effectiveDateTime"),
        ("issued", "issued"),
        ("value", "valueQuantity.value"),
        ("unit", "valueQuantity.unit"),
        ("value_code", "valueCodeableConcept.coding.code"),
        ("value_string", "valueString"),
        ("component_code", "component.code.coding.code"),
        ("component_value", "component.valueQuantity.value"),
        ("component_unit", "component.valueQuantity.unit"),
    ),
    "Procedure": (
        ("procedure_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "encounter.reference"),
        ("status", "status"),
        ("code_system", "code.coding.system"),
        ("code", "code.coding.code"),
        ("display", "code.coding.display"),
        ("performed_datetime", "performedDateTime"),
        ("performed_start", "performedPeriod.start"),
        ("performed_end", "performedPeriod.end"),
    ),
    "DiagnosticReport": (
        ("report_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "encounter.reference"),
        ("status", "status"),
        ("category_code", "category.coding.code"),
        ("code_system", "code.coding.system"),
        ("code", "code.coding.code"),
        ("display", "code.coding.display"),
        ("effective_datetime", "effectiveDateTime"),
        ("issued", "issued"),
        ("result_reference", "result.reference"),
        ("conclusion", "conclusion"),
    ),
    "ImagingStudy": (
        ("imaging_study_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "encounter.reference"),
        ("study_instance_uid", "uid"),
        ("started", "started"),
        ("modality_code", "modality.code"),
        ("number_of_series", "numberOfSeries"),
        ("number_of_instances", "numberOfInstances"),
        ("series_instance_uid", "series.uid"),
        ("series_number", "series.number"),
        ("series_modality", "series.modality.code"),
        ("series_description", "series.description"),
        ("series_started", "series.started"),
        ("instance_sop_uid", "series.instance.uid"),
        ("instance_sop_class", "series.instance.sopClass.code"),
    ),
    "MedicationStatement": (
        ("medication_statement_id", "id"),
        ("patient_reference", "subject.reference"),
        ("status", "status"),
        ("medication_code", "medicationCodeableConcept.coding.code"),
        ("medication_display", "medicationCodeableConcept.coding.display"),
        ("effective_datetime", "effectiveDateTime"),
        ("effective_start", "effectivePeriod.start"),
        ("effective_end", "effectivePeriod.end"),
        ("date_asserted", "dateAsserted"),
    ),
    "ServiceRequest": (
        ("service_request_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "encounter.reference"),
        ("status", "status"),
        ("intent", "intent"),
        ("code_system", "code.coding.system"),
        ("code", "code.coding.code"),
        ("display", "code.coding.display"),
        ("authored_on", "authoredOn"),
        ("requester_reference", "requester.reference"),
    ),
    "Specimen": (
        ("specimen_id", "id"),
        ("patient_reference", "subject.reference"),
        ("type_code", "type.coding.code"),
        ("type_display", "type.coding.display"),
        ("collection_datetime", "collection.collectedDateTime"),
        ("collection_start", "collection.collectedPeriod.start"),
        ("collection_end", "collection.collectedPeriod.end"),
        ("body_site_code", "collection.bodySite.coding.code"),
        ("body_site_display", "collection.bodySite.coding.display"),
    ),
    "DocumentReference": (
        ("document_reference_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "context.encounter.reference"),
        ("status", "status"),
        ("type_code", "type.coding.code"),
        ("type_display", "type.coding.display"),
        ("date", "date"),
        ("author_reference", "author.reference"),
        ("content_type", "content.attachment.contentType"),
        ("content_url", "content.attachment.url"),
        ("content_title", "content.attachment.title"),
    ),
}


def get_fhir_path_preset(resource_type: str) -> list[tuple[str, str]]:
    """Return a copy of the default FHIRPath extraction preset for a resource.

    Parameters
    ----------
    resource_type:
        FHIR resource type name, for example ``"Patient"``, ``"Observation"``,
        ``"Condition"``, or ``"ImagingStudy"``.

    Returns
    -------
    list[tuple[str, str]]
        A mutable list of ``(column_name, fhir_path)`` pairs suitable for
        ``FHIRRestClient.search_df(..., fhir_paths=...)``.

    Raises
    ------
    ValueError
        If no preset is available for ``resource_type``.
    """
    key = resource_type.strip()
    if key not in FHIR_PATH_PRESETS:
        available = ", ".join(sorted(FHIR_PATH_PRESETS))
        raise ValueError(f"No FHIRPath preset for {resource_type!r}. Available presets: {available}.")
    return list(FHIR_PATH_PRESETS[key])


__all__ = ["FHIRPathPreset", "FHIR_PATH_PRESETS", "get_fhir_path_preset"]
