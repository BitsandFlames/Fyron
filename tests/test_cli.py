"""Tests for the unified Fyron CLI."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
import pytest

from fyron.cli import main
from fyron.datasets import make_dicom_series, make_nifti_pair


def test_cli_help_commands(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "fhir-rest" in help_text
    assert "curate" in help_text
    assert "dataset-curate-previews" in help_text

    for command in ["fhir-rest", "fhir-build-bundle", "dicom-download", "document-download", "curate", "dataset-curate-previews"]:
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0

    with pytest.raises(SystemExit) as exc:
        main(["dicom-seg", "--help"])
    assert exc.value.code == 0
    dicom_seg_help = capsys.readouterr().out
    assert "--algorithm-name" in dicom_seg_help
    assert "--algorithm-type" in dicom_seg_help
    assert "--manufacturer" in dicom_seg_help
    assert "--validate" in dicom_seg_help
    assert "--summary-json" in dicom_seg_help


def test_cli_banner(capsys) -> None:
    assert main(["banner"]) == 0
    assert "Fyron" in capsys.readouterr().out

    assert main(["spark"]) == 0
    assert "Fyron" in capsys.readouterr().out


def test_cli_docs_build() -> None:
    assert main(["docs-build"]) == 0
    assert Path("site/index.html").exists()


def test_cli_quiet_verbose_and_no_color(capsys) -> None:
    assert main(["--quiet", "docs-build"]) == 0
    assert capsys.readouterr().out == ""

    assert main(["--verbose", "docs-build"]) == 0
    assert logging.getLogger("fyron").level == logging.DEBUG

    assert main(["--no-color", "banner"]) == 0
    assert "\033[" not in capsys.readouterr().out

    assert main(["banner", "--no-color"]) == 0
    assert "\033[" not in capsys.readouterr().out


def test_cli_imaging_qc_and_synthetic_dicom(tmp_path) -> None:
    pair = make_nifti_pair(tmp_path / "nifti")
    dicom_dir = tmp_path / "dicom"
    make_dicom_series(dicom_dir)

    qc_out = tmp_path / "qc.csv"
    assert main(["imaging-qc", "--dicom-dir", str(dicom_dir), "--nifti", str(pair["image"]), "--mask", str(pair["mask"]), "--output", str(qc_out)]) == 0
    assert pd.read_csv(qc_out).shape[0] >= 1

    synthetic_dir = tmp_path / "synthetic"
    manifest = tmp_path / "synthetic_manifest.csv"
    assert main([
        "synthetic-dicom",
        "--volume",
        str(pair["image"]),
        "--reference-dicom",
        str(dicom_dir),
        "--output-dir",
        str(synthetic_dir),
        "--manifest-csv",
        str(manifest),
    ]) == 0
    assert manifest.exists()
    assert list(synthetic_dir.glob("*.dcm"))


def test_cli_dataset_preparation_commands(tmp_path) -> None:
    pair = make_nifti_pair(tmp_path / "nifti")
    nnunet_manifest = tmp_path / "nnunet_manifest.csv"
    pd.DataFrame(
        {
            "case_id": ["case001"],
            "split": ["train"],
            "image_path": [pair["image"]],
            "label_path": [pair["mask"]],
        }
    ).to_csv(nnunet_manifest, index=False)
    nnunet_out = tmp_path / "nnunet"
    nnunet_written = tmp_path / "nnunet_written.csv"

    assert main([
        "dataset-nnunetv2",
        "--manifest",
        str(nnunet_manifest),
        "--output-dir",
        str(nnunet_out),
        "--dataset-id",
        "501",
        "--dataset-name",
        "Demo",
        "--output-manifest",
        str(nnunet_written),
    ]) == 0
    assert (nnunet_out / "Dataset501_Demo" / "imagesTr" / "case001_0000.nii.gz").exists()
    assert nnunet_written.exists()

    yolo_cls_manifest = tmp_path / "yolo_cls_manifest.csv"
    pd.DataFrame(
        {
            "image_path": [pair["image"]],
            "class": ["tumor"],
            "split": ["train"],
            "sample_id": ["case001"],
        }
    ).to_csv(yolo_cls_manifest, index=False)
    yolo_cls_out = tmp_path / "yolo_cls"
    assert main([
        "dataset-yolo-classify",
        "--manifest",
        str(yolo_cls_manifest),
        "--output-dir",
        str(yolo_cls_out),
        "--sample-id-col",
        "sample_id",
    ]) == 0
    assert (yolo_cls_out / "train" / "tumor" / "case001_z0002.png").exists()

    yolo_det_manifest = tmp_path / "yolo_det_manifest.csv"
    pd.DataFrame(
        {
            "image_path": [pair["image"]],
            "class": ["lesion"],
            "split": ["train"],
            "sample_id": ["case001"],
            "x_min": [1],
            "y_min": [1],
            "x_max": [5],
            "y_max": [5],
        }
    ).to_csv(yolo_det_manifest, index=False)
    yolo_det_out = tmp_path / "yolo_det"
    assert main([
        "dataset-yolo-detect",
        "--manifest",
        str(yolo_det_manifest),
        "--output-dir",
        str(yolo_det_out),
        "--sample-id-col",
        "sample_id",
    ]) == 0
    assert (yolo_det_out / "labels" / "train" / "case001_z0002.txt").exists()


def test_cli_audit_manifest(tmp_path) -> None:
    inp = tmp_path / "input.csv"
    inp.write_text("x\n1\n", encoding="utf-8")
    out = tmp_path / "manifest.json"
    assert main([
        "audit-manifest",
        "--title",
        "Analysis",
        "--input",
        str(inp),
        "--output",
        "results.csv",
        "--parameter",
        "model=random_forest",
        "--write",
        str(out),
    ]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["title"] == "Analysis"
    assert payload["parameters"]["model"] == "random_forest"


def test_cli_fhir_build_bundle_writes_outputs(tmp_path) -> None:
    data = tmp_path / "observations.csv"
    mapping = tmp_path / "mapping.json"
    bundle = tmp_path / "bundle.json"
    summary = tmp_path / "summary.json"
    validation = tmp_path / "validation.json"
    pd.DataFrame({"patient_id": ["1"], "obs_id": ["obs-1"], "code": ["718-7"], "value": [13.4], "unit": ["g/dL"]}).to_csv(data, index=False)
    mapping.write_text(json.dumps({"code_col": "code", "code_system": "http://loinc.org", "value_col": "value", "unit_col": "unit"}), encoding="utf-8")

    assert main([
        "fhir-build-bundle",
        "--input",
        str(data),
        "--mapping",
        str(mapping),
        "--resource",
        "Observation",
        "--subject-col",
        "patient_id",
        "--id-col",
        "obs_id",
        "--bundle-type",
        "transaction",
        "--transaction-method",
        "PUT",
        "--output",
        str(bundle),
        "--summary-json",
        str(summary),
        "--validation-json",
        str(validation),
    ]) == 0

    payload = json.loads(bundle.read_text(encoding="utf-8"))
    assert payload["type"] == "transaction"
    assert payload["entry"][0]["request"] == {"method": "PUT", "url": "Observation/obs-1"}
    assert json.loads(summary.read_text(encoding="utf-8"))["resource_types"] == {"Observation": 1}
    assert json.loads(validation.read_text(encoding="utf-8"))["valid"] is True


def test_cli_fhir_build_bundle_submit_requires_transaction(tmp_path) -> None:
    data = tmp_path / "observations.csv"
    mapping = tmp_path / "mapping.json"
    pd.DataFrame({"patient_id": ["1"], "code": ["SMA"], "value": [42.0]}).to_csv(data, index=False)
    mapping.write_text(json.dumps({"code_col": "code", "value_col": "value"}), encoding="utf-8")

    with pytest.raises(SystemExit, match="transaction"):
        main([
            "fhir-build-bundle",
            "--input",
            str(data),
            "--mapping",
            str(mapping),
            "--resource",
            "Observation",
            "--subject-col",
            "patient_id",
            "--output",
            str(tmp_path / "bundle.json"),
            "--submit",
        ])


def test_cli_fhir_build_bundle_submit_uses_rest_client(tmp_path, monkeypatch) -> None:
    import fyron

    data = tmp_path / "observations.csv"
    mapping = tmp_path / "mapping.json"
    pd.DataFrame({"patient_id": ["1"], "obs_id": ["obs-1"], "code": ["SMA"], "value": [42.0]}).to_csv(data, index=False)
    mapping.write_text(json.dumps({"code_col": "code", "value_col": "value"}), encoding="utf-8")
    calls = {}

    class FakeClient:
        def __init__(self, base_url: str, bearer_token: str | None = None) -> None:
            calls["base_url"] = base_url
            calls["bearer_token"] = bearer_token

        def submit_bundle(self, bundle: dict) -> object:
            calls["bundle_type"] = bundle["type"]
            return type("Result", (), {"status_code": 200, "location": "Bundle/1", "resource_type": "Bundle", "resource_id": "1", "response_json": {}})()

    monkeypatch.setattr(fyron, "FHIRRestClient", FakeClient)

    assert main([
        "fhir-build-bundle",
        "--input",
        str(data),
        "--mapping",
        str(mapping),
        "--resource",
        "Observation",
        "--subject-col",
        "patient_id",
        "--id-col",
        "obs_id",
        "--bundle-type",
        "transaction",
        "--output",
        str(tmp_path / "bundle.json"),
        "--submit",
        "--base-url",
        "https://fhir.example.org/fhir",
        "--bearer-token",
        "token",
    ]) == 0
    assert calls == {"base_url": "https://fhir.example.org/fhir", "bearer_token": "token", "bundle_type": "transaction"}


def test_cli_dicom_seg_when_extra_available(tmp_path) -> None:
    pytest.importorskip("highdicom")
    pair = make_nifti_pair(tmp_path / "nifti")
    dicom_dir = tmp_path / "dicom"
    make_dicom_series(dicom_dir, shape=(4, 8, 8))
    segments = tmp_path / "segments.json"
    segments.write_text(json.dumps([{"label": "demo_mask", "label_value": 1}]), encoding="utf-8")
    out = tmp_path / "mask.seg.dcm"
    summary = tmp_path / "summary.json"

    assert main([
        "dicom-seg",
        "--mask",
        str(pair["mask"]),
        "--source-dicom",
        str(dicom_dir),
        "--segments",
        str(segments),
        "--output",
        str(out),
        "--algorithm-name",
        "Fyron demo model",
        "--validate",
        "--summary-json",
        str(summary),
    ]) == 0
    assert out.exists()
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["modality"] == "SEG"
    assert payload["segment_labels"] == ["demo_mask"]
