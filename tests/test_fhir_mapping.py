"""Tests for DataFrame-to-FHIR mapping helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from fyron.fhir.mapping import (
    build_bundle_from_dataframe,
    build_conditions_from_dataframe,
    build_imaging_measurements_from_dataframe,
    build_observations_from_dataframe,
    extract_coding_summary,
    fhir_validation_report,
    read_fhir_mapping,
    validate_fhir_mapping,
    validate_fhir_payload,
    write_fhir_mapping,
)


def test_mapping_validation_rejects_missing_columns() -> None:
    df = pd.DataFrame({"patient_id": ["1"], "value": [1.0]})
    report = validate_fhir_mapping({"code_col": "missing_code", "value_col": "value"}, df=df, required_columns=["patient_id"])

    assert report["valid"] is False
    assert "missing DataFrame column: missing_code" in report["errors"]


def test_observation_dataframe_conversion_handles_values_and_missing() -> None:
    df = pd.DataFrame(
        {
            "patient_id": ["1", "2"],
            "obs_id": ["obs-1", "obs-2"],
            "code": ["718-7", "33747-0"],
            "display": ["Hemoglobin", "Status"],
            "value": [13.4, None],
            "unit": ["g/dL", None],
        }
    )
    result = build_observations_from_dataframe(
        df,
        {"code_col": "code", "code_display_col": "display", "code_system": "http://loinc.org", "value_col": "value", "unit_col": "unit"},
        subject_col="patient_id",
        id_col="obs_id",
    )

    assert result["validation"]["valid"] is True
    assert result["summary"]["resource_types"] == {"Observation": 2}
    assert result["resources"][0]["valueQuantity"]["value"] == 13.4
    assert result["resources"][1]["dataAbsentReason"]["text"] == "unknown"
    assert extract_coding_summary(result["bundle"]).shape[0] >= 2


def test_condition_dataframe_conversion_links_evidence() -> None:
    df = pd.DataFrame({"patient_id": ["1"], "condition_id": ["cond-1"], "code": ["C34"], "evidence": ["DocumentReference/doc-1"]})
    result = build_conditions_from_dataframe(
        df,
        {"condition_code_col": "code", "condition_code_system": "http://hl7.org/fhir/sid/icd-10", "evidence_col": "evidence"},
        subject_col="patient_id",
        id_col="condition_id",
    )

    assert result["resources"][0]["evidence"][0]["detail"][0]["reference"] == "DocumentReference/doc-1"
    assert fhir_validation_report(result["bundle"])["valid"] is False


def test_imaging_measurement_mapping_creates_context_resources() -> None:
    df = pd.DataFrame(
        {
            "patient_id": ["1", "1"],
            "study_uid": ["1.2.3", "1.2.3"],
            "series_uid": ["1.2.3.4", "1.2.3.4"],
            "measurement_id": ["l3-sma", "vat"],
            "code": ["L3 SMA", "VAT volume"],
            "value": [123.4, 820.5],
            "unit": ["cm2", "ml"],
        }
    )
    result = build_imaging_measurements_from_dataframe(
        df,
        {"code_col": "code", "value_col": "value", "unit_col": "unit", "model_name": "Fyron imaging"},
        subject_col="patient_id",
        study_uid_col="study_uid",
        series_uid_col="series_uid",
        id_col="measurement_id",
    )
    resource_types = result["summary"]["resource_types"]

    assert resource_types["ImagingStudy"] == 1
    assert resource_types["Observation"] == 2
    assert resource_types["DiagnosticReport"] == 1
    assert resource_types["Provenance"] == 1


def test_bundle_from_dataframe_dispatch_and_transaction_put() -> None:
    df = pd.DataFrame({"patient_id": ["1"], "obs_id": ["obs-1"], "code": ["SMA"], "value": [42.0]})
    result = build_bundle_from_dataframe(
        df,
        "Observation",
        {"code_col": "code", "value_col": "value"},
        subject_col="patient_id",
        id_col="obs_id",
        bundle_type="transaction",
        transaction_method="PUT",
    )

    assert result["bundle"]["entry"][0]["request"] == {"method": "PUT", "url": "Observation/obs-1"}
    assert validate_fhir_payload(result["bundle"])["valid"] is True
    with pytest.raises(ValueError, match="resource_type"):
        build_bundle_from_dataframe(df, "Medication", {}, subject_col="patient_id")


def test_mapping_json_roundtrip(tmp_path: Path) -> None:
    mapping = {"code_col": "code", "value_col": "value"}
    path = write_fhir_mapping(mapping, tmp_path / "mapping.json")

    assert json.loads(path.read_text(encoding="utf-8")) == mapping
    assert read_fhir_mapping(path) == mapping
