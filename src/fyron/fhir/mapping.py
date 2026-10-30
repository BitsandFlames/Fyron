"""Map clinical DataFrames into inspectable FHIR resources and bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .builder import (
    FHIR_R4,
    build_bundle,
    build_condition,
    build_document_reference,
    build_imaging_measurement_bundle,
    build_observation,
    codeable_concept,
    summarize_fhir_bundle,
    validate_fhir_bundle,
    validate_fhir_references,
    validate_fhir_resource,
)

StrPath = str | Path


def read_fhir_mapping(path: StrPath) -> dict[str, Any]:
    """Read a Fyron FHIR mapping JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_fhir_mapping(mapping: dict[str, Any], path: StrPath) -> Path:
    """Write a Fyron FHIR mapping JSON file."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mapping, indent=2, sort_keys=False), encoding="utf-8")
    return out.resolve()


def build_observations_from_dataframe(
    df: pd.DataFrame,
    mapping: dict[str, Any],
    *,
    subject_col: str,
    id_col: str | None = None,
    bundle_type: str = "collection",
    transaction_method: str = "POST",
    if_none_exist: str | dict[str, str] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build Observation resources and a Bundle from a DataFrame."""
    validate_fhir_mapping(mapping, df=df, required_columns=[subject_col, id_col])
    resources = []
    for _, row in df.iterrows():
        value = _row_value(row, mapping, "value")
        kwargs: dict[str, Any] = {
            "subject": _patient_reference(row[subject_col]),
            "code": _codeable_from_mapping(row, mapping),
            "observation_id": _optional_row_value(row, id_col),
            "status": mapping.get("status", "final"),
            "value_type": mapping.get("value_type", "quantity"),
            "unit": _mapped_value(row, mapping, "unit"),
            "effective": _mapped_value(row, mapping, "effective"),
            "method": _mapped_codeable(row, mapping, "method"),
            "body_site": _mapped_codeable(row, mapping, "body_site"),
            "derived_from": _mapped_references(row, mapping, "derived_from"),
            "profile": mapping.get("profile"),
            "meta_source": mapping.get("meta_source"),
        }
        if _is_missing(value):
            kwargs["data_absent_reason"] = mapping.get("data_absent_reason", "unknown")
        else:
            kwargs["value"] = value
        resources.append(build_observation(**_drop_none(kwargs), version=version))
    return _mapping_result(resources, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)


def build_conditions_from_dataframe(
    df: pd.DataFrame,
    mapping: dict[str, Any],
    *,
    subject_col: str,
    id_col: str | None = None,
    bundle_type: str = "collection",
    transaction_method: str = "POST",
    if_none_exist: str | dict[str, str] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build Condition resources and a Bundle from a DataFrame."""
    validate_fhir_mapping(mapping, df=df, required_columns=[subject_col, id_col])
    resources = []
    for _, row in df.iterrows():
        resources.append(
            build_condition(
                subject=_patient_reference(row[subject_col]),
                code=_codeable_from_mapping(row, mapping, default_code_key="condition_code"),
                condition_id=_optional_row_value(row, id_col),
                clinical_status=_mapped_codeable(row, mapping, "clinical_status"),
                verification_status=_mapped_codeable(row, mapping, "verification_status"),
                onset=_mapped_value(row, mapping, "onset"),
                recorded_date=_mapped_value(row, mapping, "recorded_date"),
                evidence=_mapped_references(row, mapping, "evidence"),
                profile=mapping.get("profile"),
                meta_source=mapping.get("meta_source"),
                version=version,
            )
        )
    return _mapping_result(resources, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)


def build_document_references_from_dataframe(
    df: pd.DataFrame,
    mapping: dict[str, Any],
    *,
    subject_col: str,
    id_col: str | None = None,
    bundle_type: str = "collection",
    transaction_method: str = "POST",
    if_none_exist: str | dict[str, str] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build DocumentReference resources and a Bundle from a DataFrame."""
    validate_fhir_mapping(mapping, df=df, required_columns=[subject_col, id_col])
    resources = []
    for _, row in df.iterrows():
        resources.append(
            build_document_reference(
                subject=_patient_reference(row[subject_col]),
                url=_mapped_value(row, mapping, "document_url") or _mapped_value(row, mapping, "url"),
                title=_mapped_value(row, mapping, "title"),
                content_type=_mapped_value(row, mapping, "content_type") or mapping.get("content_type", "application/pdf"),
                document_id=_optional_row_value(row, id_col),
                type_code=_mapped_codeable(row, mapping, "type"),
                date=_mapped_value(row, mapping, "date"),
                description=_mapped_value(row, mapping, "description"),
                profile=mapping.get("profile"),
                meta_source=mapping.get("meta_source"),
                version=version,
            )
        )
    return _mapping_result(resources, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)


def build_imaging_measurements_from_dataframe(
    df: pd.DataFrame,
    mapping: dict[str, Any],
    *,
    subject_col: str,
    study_uid_col: str,
    series_uid_col: str | None = None,
    id_col: str | None = None,
    bundle_type: str = "collection",
    transaction_method: str = "POST",
    if_none_exist: str | dict[str, str] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Build imaging-measurement resources and a Bundle from a DataFrame."""
    validate_fhir_mapping(mapping, df=df, required_columns=[subject_col, study_uid_col, series_uid_col, id_col])
    resources: list[dict[str, Any]] = []
    group_cols = [subject_col, study_uid_col] + ([series_uid_col] if series_uid_col else [])
    for group_index, (keys, group) in enumerate(df.groupby(group_cols, dropna=False)):
        key_values = keys if isinstance(keys, tuple) else (keys,)
        subject = key_values[0]
        study_uid = key_values[1]
        series_uid = key_values[2] if series_uid_col else None
        measurements = []
        for _, row in group.iterrows():
            measurements.append(
                {
                    "id": _optional_row_value(row, id_col),
                    "code": _codeable_from_mapping(row, mapping),
                    "value": _row_value(row, mapping, "value"),
                    "unit": _mapped_value(row, mapping, "unit"),
                    "effective": _mapped_value(row, mapping, "effective"),
                    "body_site": _mapped_codeable(row, mapping, "body_site"),
                    "method": _mapped_codeable(row, mapping, "method"),
                }
            )
        sub_bundle = build_imaging_measurement_bundle(
            subject=_patient_reference(subject),
            study_instance_uid=str(study_uid),
            series_instance_uid=None if _is_missing(series_uid) else str(series_uid),
            series_description=mapping.get("series_description"),
            measurements=measurements,
            model_name=mapping.get("model_name"),
            model_endpoint_url=mapping.get("model_endpoint_url"),
            id_prefix=mapping.get("id_prefix") or f"imaging-{group_index + 1}",
            bundle_type="collection",
            version=version,
        )
        resources.extend([entry["resource"] for entry in sub_bundle["entry"]])
    return _mapping_result(resources, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)


def build_bundle_from_dataframe(
    df: pd.DataFrame,
    resource_type: str,
    mapping: dict[str, Any],
    *,
    subject_col: str,
    id_col: str | None = None,
    study_uid_col: str | None = None,
    series_uid_col: str | None = None,
    bundle_type: str = "collection",
    transaction_method: str = "POST",
    if_none_exist: str | dict[str, str] | None = None,
    version: str = FHIR_R4,
) -> dict[str, Any]:
    """Dispatch DataFrame-to-FHIR conversion by resource type."""
    normalized = resource_type.lower().replace("-", "").replace("_", "")
    if normalized == "observation":
        return build_observations_from_dataframe(df, mapping, subject_col=subject_col, id_col=id_col, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)
    if normalized == "condition":
        return build_conditions_from_dataframe(df, mapping, subject_col=subject_col, id_col=id_col, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)
    if normalized == "documentreference":
        return build_document_references_from_dataframe(df, mapping, subject_col=subject_col, id_col=id_col, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)
    if normalized == "imagingmeasurement":
        if not study_uid_col:
            raise ValueError("study_uid_col is required for ImagingMeasurement")
        return build_imaging_measurements_from_dataframe(df, mapping, subject_col=subject_col, study_uid_col=study_uid_col, series_uid_col=series_uid_col, id_col=id_col, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)
    raise ValueError("resource_type must be one of: Observation, Condition, DocumentReference, ImagingMeasurement")


def validate_fhir_mapping(mapping: dict[str, Any], df: pd.DataFrame | None = None, required_columns: list[str | None] | None = None) -> dict[str, Any]:
    """Validate a Fyron FHIR mapping dictionary and optional source DataFrame."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(mapping, dict):
        errors.append("mapping must be a dictionary")
        return _report(errors=errors, warnings=warnings)
    if not any(key in mapping for key in ("code_col", "code", "condition_code_col", "condition_code")):
        warnings.append("mapping does not define code_col/code; text fallback may be unavailable")
    if df is not None:
        columns = set(df.columns)
        for column in _mapping_columns(mapping) | {col for col in (required_columns or []) if col}:
            if column not in columns:
                errors.append(f"missing DataFrame column: {column}")
    return _report(errors=errors, warnings=warnings)


def validate_fhir_mapping_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate a mapping result object returned by this module."""
    payload = result.get("bundle")
    return validate_fhir_payload(payload) if isinstance(payload, dict) else _report(errors=["mapping result is missing bundle"])


def validate_fhir_payload(payload: dict[str, Any], *, version: str = FHIR_R4, strict: bool = False) -> dict[str, Any]:
    """Return a structured lightweight validation report for a resource or Bundle."""
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    try:
        if payload.get("resourceType") == "Bundle":
            validate_fhir_bundle(payload, version=version)
        else:
            validate_fhir_resource(payload, version=version)
    except Exception as exc:
        errors.append(str(exc))
    if payload.get("resourceType") == "Bundle":
        refs = validate_fhir_references(payload)
        if refs["missing_references"]:
            errors.extend([f"missing reference: {ref}" for ref in refs["missing_references"]])
        counts = _resource_counts(payload)
    else:
        counts = {payload.get("resourceType", "Unknown"): 1}
    coding_report = validate_coding_systems(payload)
    warnings.extend(coding_report["warnings"])
    if strict and warnings:
        errors.extend(warnings)
        warnings = []
    return _report(errors=errors, warnings=warnings, info=info, resource_counts=counts, missing_references=validate_fhir_references(payload)["missing_references"] if payload.get("resourceType") == "Bundle" else [])


def fhir_validation_report(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return a structured validation report for a FHIR Bundle."""
    return validate_fhir_payload(bundle)


def validate_coding_systems(payload: dict[str, Any], allowed_systems: set[str] | list[str] | None = None) -> dict[str, Any]:
    """Check coding-system presence and optional allow-list consistency."""
    allowed = set(allowed_systems or [])
    warnings: list[str] = []
    for item in _iter_codings(payload):
        system = item.get("system")
        code = item.get("code")
        if not system:
            warnings.append(f"coding {code or '<missing-code>'} is missing system")
        elif allowed and system not in allowed:
            warnings.append(f"coding system is not allowed: {system}")
    return _report(warnings=warnings)


def extract_coding_summary(payload: dict[str, Any]) -> pd.DataFrame:
    """Extract all Coding entries from a resource or Bundle into a DataFrame."""
    rows = []
    for item in _iter_codings(payload):
        rows.append({"system": item.get("system"), "code": item.get("code"), "display": item.get("display")})
    return pd.DataFrame(rows)


def _mapping_result(
    resources: list[dict[str, Any]],
    *,
    bundle_type: str,
    transaction_method: str,
    if_none_exist: str | dict[str, str] | None,
    version: str,
) -> dict[str, Any]:
    bundle = build_bundle(resources, bundle_type=bundle_type, transaction_method=transaction_method, if_none_exist=if_none_exist, version=version)
    validation = validate_fhir_payload(bundle, version=version)
    try:
        summary = summarize_fhir_bundle(bundle)
    except ValueError:
        summary = {
            "resource_type": "Bundle",
            "bundle_type": bundle.get("type"),
            "id": bundle.get("id"),
            "entry_count": len(bundle.get("entry", [])),
            "resource_types": _resource_counts(bundle),
            "transaction_methods": {},
            "local_references_valid": not validation["missing_references"],
            "missing_references": validation["missing_references"],
            "resources": [],
        }
    result = {"bundle": bundle, "resources": resources, "summary": summary, "validation": validation}
    return result


def _codeable_from_mapping(row: pd.Series, mapping: dict[str, Any], default_code_key: str = "code") -> dict[str, Any]:
    code = _mapped_value(row, mapping, default_code_key)
    display = _mapped_value(row, mapping, f"{default_code_key}_display") or _mapped_value(row, mapping, "display")
    system = mapping.get(f"{default_code_key}_system") or mapping.get("code_system") or mapping.get("system")
    if _is_missing(code):
        text = mapping.get("code_text") or mapping.get("text") or default_code_key
        return codeable_concept(text=str(text))
    return codeable_concept(str(code), system=system, display=None if _is_missing(display) else str(display))


def _mapped_codeable(row: pd.Series, mapping: dict[str, Any], key: str) -> dict[str, Any] | None:
    value = _mapped_value(row, mapping, key)
    if _is_missing(value):
        return None
    return codeable_concept(text=str(value))


def _row_value(row: pd.Series, mapping: dict[str, Any], key: str) -> Any:
    return _mapped_value(row, mapping, key)


def _mapped_value(row: pd.Series, mapping: dict[str, Any], key: str) -> Any:
    col_key = f"{key}_col"
    if col_key in mapping:
        return row.get(mapping[col_key])
    if key in mapping:
        value = mapping[key]
        if isinstance(value, dict):
            if "column" in value:
                return row.get(value["column"])
            if "value" in value:
                return value["value"]
        return value
    return None


def _mapped_references(row: pd.Series, mapping: dict[str, Any], key: str) -> list[str] | None:
    value = _mapped_value(row, mapping, key)
    if _is_missing(value):
        return None
    if isinstance(value, list):
        return [str(item) for item in value if not _is_missing(item)]
    return [str(value)]


def _optional_row_value(row: pd.Series, column: str | None) -> str | None:
    if not column:
        return None
    value = row.get(column)
    return None if _is_missing(value) else str(value)


def _patient_reference(value: Any) -> str:
    text = str(value)
    return text if text.startswith("Patient/") else f"Patient/{text}"


def _mapping_columns(mapping: dict[str, Any]) -> set[str]:
    columns = set()
    for key, value in mapping.items():
        if key.endswith("_col") and isinstance(value, str):
            columns.add(value)
        if isinstance(value, dict) and isinstance(value.get("column"), str):
            columns.add(value["column"])
    return columns


def _resource_counts(bundle: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in bundle.get("entry", []):
        resource_type = (entry.get("resource") or {}).get("resourceType", "Unknown")
        counts[resource_type] = counts.get(resource_type, 0) + 1
    return counts


def _iter_codings(value: Any) -> list[dict[str, Any]]:
    codings: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if "code" in value and ("system" in value or "display" in value):
            codings.append(value)
        for item in value.values():
            codings.extend(_iter_codings(item))
    elif isinstance(value, list):
        for item in value:
            codings.extend(_iter_codings(item))
    return codings


def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _report(
    *,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    info: list[str] | None = None,
    resource_counts: dict[str, int] | None = None,
    missing_references: list[str] | None = None,
) -> dict[str, Any]:
    errors = errors or []
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings or [],
        "info": info or [],
        "resource_counts": resource_counts or {},
        "missing_references": missing_references or [],
    }


__all__ = [
    "build_bundle_from_dataframe",
    "build_conditions_from_dataframe",
    "build_document_references_from_dataframe",
    "build_imaging_measurements_from_dataframe",
    "build_observations_from_dataframe",
    "extract_coding_summary",
    "fhir_validation_report",
    "read_fhir_mapping",
    "validate_coding_systems",
    "validate_fhir_mapping",
    "validate_fhir_mapping_result",
    "validate_fhir_payload",
    "write_fhir_mapping",
]
