from __future__ import annotations

import json

from fyron import audit as fa


def test_audit_manifest(tmp_path) -> None:
    data = tmp_path / "features.csv"
    data.write_text("patient_id,age\np1,60\n", encoding="utf-8")

    digest = fa.hash_file(data)
    assert len(digest) == 64

    manifest = fa.create_provenance_manifest(
        title="Test analysis",
        inputs=[data],
        outputs=[tmp_path / "model.joblib"],
        parameters={"seed": 42},
    )
    assert manifest["inputs"][0]["sha256"] == digest
    assert manifest["parameters"]["seed"] == 42

    path = fa.write_manifest(manifest, tmp_path / "manifest.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["title"] == "Test analysis"


def test_analysis_run_manifest(tmp_path) -> None:
    data = tmp_path / "cohort.csv"
    data.write_text("patient_id,event\np1,1\n", encoding="utf-8")

    manifest = fa.analysis_run_manifest(
        title="Locked validation",
        analysis_type="classification",
        cohort_id="cohort-v1",
        inputs=[data],
        parameters={"threshold": 0.4},
        random_seed=42,
    )
    assert manifest["analysis_type"] == "classification"
    assert manifest["cohort_id"] == "cohort-v1"
    assert manifest["parameters"]["random_seed"] == 42
    assert manifest["inputs"][0]["sha256"] == fa.hash_file(data)
