from fyron import (
    FHIR_PATH_PRESETS,
    extract_patient,
    get_fhir_path_preset,
    process_imaging_study_bundle,
    process_observation_bundle,
)


def test_extract_patient_basic():
    patient = {
        "resourceType": "Patient",
        "id": "p1",
        "name": [{"given": ["Ada"], "family": "Lovelace"}],
        "gender": "female",
        "birthDate": "1815-12-10",
    }
    row = extract_patient(patient)
    assert row["id"] == "p1"
    assert row["name"] == "Ada Lovelace"
    assert row["gender"] == "female"


def test_process_imaging_study_bundle_series_rows():
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "ImagingStudy",
                    "id": "study-1",
                    "uid": "1.2.3",
                    "series": [
                        {"uid": "1.2.3.1", "number": 1, "description": "Series A"},
                        {"uid": "1.2.3.2", "number": 2, "description": "Series B"},
                    ],
                }
            }
        ],
    }
    out = process_imaging_study_bundle(bundle)
    rows = out["ImagingStudy"]
    assert len(rows) == 2
    assert rows[0]["study_instance_uid"] == "1.2.3"
    assert rows[0]["series_instance_uid"] == "1.2.3.1"
    assert rows[1]["series_instance_uid"] == "1.2.3.2"


def test_process_observation_bundle_minimal():
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-1",
                    "status": "final",
                    "code": {"coding": [{"code": "789-8", "system": "loinc"}]},
                }
            }
        ],
    }
    out = process_observation_bundle(bundle)
    rows = out["Observation"]
    assert len(rows) == 1
    assert rows[0]["id"] == "obs-1"


def test_fhir_path_presets_are_copyable():
    paths = get_fhir_path_preset("Observation")
    assert ("observation_id", "id") in paths
    assert any(name == "value" for name, _ in paths)

    paths.append(("local_extension", "extension.valueString"))
    assert ("local_extension", "extension.valueString") not in FHIR_PATH_PRESETS["Observation"]


def test_unknown_fhir_path_preset_lists_available_resources():
    try:
        get_fhir_path_preset("UnknownResource")
    except ValueError as exc:
        assert "Observation" in str(exc)
        assert "Patient" in str(exc)
    else:
        raise AssertionError("expected ValueError")
