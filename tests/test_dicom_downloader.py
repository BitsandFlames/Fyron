from __future__ import annotations

import pydicom
import pandas as pd
import pytest

from fyron.datasets import make_dicom_series
from fyron.dicom import DICOMDownloader
from fyron.dicom.client import DicomResult
from fyron.dicom.client import _build_tasks


@pytest.mark.parametrize("label", ["patient-1", "patient/1", "CON", "\u00e9" * 300])
def test_study_labels_remain_study_specific(label):
    first = DICOMDownloader._study_output_dir_name("1.2.3", label)
    second = DICOMDownloader._study_output_dir_name("1.2.4", label)
    assert first != second
    assert first.endswith("__" + DICOMDownloader.download_id("1.2.3"))
    assert len(first.encode("utf-8")) <= 240
    assert "/" not in first
    assert first == DICOMDownloader._study_output_dir_name("1.2.3", label)


@pytest.mark.parametrize("label", [None, "", "  ", float("nan")])
def test_empty_study_label_preserves_default_hash(label):
    assert DICOMDownloader._study_output_dir_name("1.2.3", label) == DICOMDownloader.download_id("1.2.3")


def test_batch_deduplicates_resolved_study_and_series_tasks():
    df = pd.DataFrame({
        "study": ["1.2.3", "1.2.3", "1.2.4"],
        "series": ["1.2.3.1", "1.2.3.1", "1.2.4.1"],
        "patient": ["p/1", "p\\1", "p/1"],
    })
    assert len(_build_tasks(df, "study", "series", True, "patient")) == 2
    assert len(_build_tasks(df, "study", "series", False)) == 2


def test_same_patient_studies_have_separate_manifests(tmp_path, monkeypatch):
    import json

    downloader = DICOMDownloader(dicom_web_url="https://example.invalid/dicomweb", output_format="dicom")
    calls = []

    def retrieve(study_uid, target_dir, skip_existing, study_layout):
        calls.append(study_uid)
        return [DicomResult(
            study_uid=study_uid, series_uid=study_uid + ".1",
            download_id=downloader.download_id(study_uid, study_uid + ".1"),
            path=str(target_dir), format="dicom", error=None,
        )]

    monkeypatch.setattr(downloader, "_download_study_via_iter_study", retrieve)
    legacy = tmp_path / "patient-1"
    legacy.mkdir()
    sentinel = legacy / "study_manifest.json"
    sentinel.write_text("existing data")
    results = downloader.download_from_dataframe(
        pd.DataFrame({"study": ["1.2.3", "1.2.3", "1.2.4"], "patient": ["patient-1"] * 3}),
        output_dir=tmp_path, study_uid_col="study", download_full_study=True,
        study_folder_name_col="patient", study_layout="flat",
    )
    assert calls == ["1.2.3", "1.2.4"]
    assert len(results) == 2
    assert results["path"].nunique() == 2
    for uid in calls:
        folder = tmp_path / downloader._study_output_dir_name(uid, "patient-1")
        manifest = json.loads((folder / "study_manifest.json").read_text())
        assert manifest["series"][0]["study_uid"] == uid
    assert sentinel.read_text() == "existing data"


def test_nifti_download_can_keep_reference_dicom(tmp_path) -> None:
    source_dir = tmp_path / "source"
    files = make_dicom_series(source_dir)
    first = pydicom.dcmread(files[0], stop_before_pixels=True)
    target_dir = tmp_path / "out"

    downloader = DICOMDownloader(
        dicom_web_url="http://localhost/dicomweb",
        output_format="nifti",
        save_reference_dicom=True,
    )

    result = downloader._store_series_files(
        study_uid=str(first.StudyInstanceUID),
        series_uid=str(first.SeriesInstanceUID),
        files=files,
        target_dir=target_dir,
    )

    assert result.error is None
    assert (target_dir / f"{first.SeriesInstanceUID}.nii.gz").is_file()
    reference = target_dir / "reference.dcm"
    assert reference.is_file()
    reference_ds = pydicom.dcmread(reference, stop_before_pixels=True)
    assert reference_ds.StudyInstanceUID == first.StudyInstanceUID
    assert reference_ds.SeriesInstanceUID == first.SeriesInstanceUID


def test_reference_dicom_name_is_file_name_only() -> None:
    try:
        DICOMDownloader(
            dicom_web_url="http://localhost/dicomweb",
            output_format="nifti",
            save_reference_dicom=True,
            reference_dicom_name="nested/reference",
        )
    except ValueError as exc:
        assert "file name" in str(exc)
    else:
        raise AssertionError("Expected invalid reference_dicom_name to fail")


def test_dataframe_download_accepts_per_call_reference_dicom_override(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_task(self, **kwargs):
        captured["save_reference_dicom"] = kwargs["save_reference_dicom"]
        captured["reference_dicom_name"] = kwargs["reference_dicom_name"]
        captured["instance_save_reference_dicom"] = self.save_reference_dicom
        captured["instance_reference_dicom_name"] = self.reference_dicom_name
        return [
            DicomResult(
                study_uid="1.2.3",
                series_uid="1.2.3.4",
                download_id="fake",
                path=str(tmp_path / "fake"),
                format="nifti",
            )
        ]

    monkeypatch.setattr(DICOMDownloader, "_run_task", fake_run_task)
    downloader = DICOMDownloader(
        dicom_web_url="http://localhost/dicomweb",
        output_format="nifti",
        save_reference_dicom=False,
        reference_dicom_name="reference.dcm",
    )
    df = pd.DataFrame(
        {"study_instance_uid": ["1.2.3"], "series_instance_uid": ["1.2.3.4"]}
    )

    result = downloader.download_from_dataframe(
        df=df,
        output_dir=tmp_path / "out",
        save_reference_dicom=True,
        reference_dicom_name="meta",
    )

    assert list(result["download_id"]) == ["fake"]
    assert captured["save_reference_dicom"] is True
    assert captured["reference_dicom_name"] == "meta.dcm"
    assert captured["instance_save_reference_dicom"] is False
    assert captured["instance_reference_dicom_name"] == "reference.dcm"
    assert downloader.save_reference_dicom is False
    assert downloader.reference_dicom_name == "reference.dcm"


def test_dataframe_download_accepts_deprecated_keep_reference_dicom_alias(
    tmp_path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_task(self, **kwargs):
        captured["save_reference_dicom"] = kwargs["save_reference_dicom"]
        return [
            DicomResult(
                study_uid="1.2.3",
                series_uid="1.2.3.4",
                download_id="fake",
                path=str(tmp_path / "fake"),
                format="nifti",
            )
        ]

    monkeypatch.setattr(DICOMDownloader, "_run_task", fake_run_task)
    downloader = DICOMDownloader(
        dicom_web_url="http://localhost/dicomweb",
        output_format="nifti",
    )
    df = pd.DataFrame(
        {"study_instance_uid": ["1.2.3"], "series_instance_uid": ["1.2.3.4"]}
    )

    with pytest.warns(DeprecationWarning, match="save_reference_dicom"):
        downloader.download_from_df(
            df=df,
            output_dir=tmp_path / "out",
            keep_reference_dicom=True,
        )

    assert captured["save_reference_dicom"] is True


def test_dataframe_download_rejects_conflicting_reference_dicom_aliases(tmp_path) -> None:
    downloader = DICOMDownloader(
        dicom_web_url="http://localhost/dicomweb",
        output_format="nifti",
    )
    df = pd.DataFrame(
        {"study_instance_uid": ["1.2.3"], "series_instance_uid": ["1.2.3.4"]}
    )

    with pytest.warns(DeprecationWarning, match="save_reference_dicom"):
        with pytest.raises(ValueError, match="disagree"):
            downloader.download_from_dataframe(
                df=df,
                output_dir=tmp_path / "out",
                save_reference_dicom=False,
                keep_reference_dicom=True,
            )
