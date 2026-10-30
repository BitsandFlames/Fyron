"""Synthetic installed-package probes; copied outside the checkout by check_wheel."""

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

import numpy as np
import pandas as pd
import fyron


def base():
    from fyron.datasets import make_clinical_cohort
    from fyron.dataframe import date_difference
    from fyron.dicom.synthetic import write_synthetic_nifti
    import SimpleITK as sitk
    assert len(make_clinical_cohort(n=8)) == 8
    assert date_difference("2020-01-01", "2020-01-03").iloc[0] == 2
    path = Path("synthetic.nii.gz")
    write_synthetic_nifti(np.zeros((3, 4, 5), dtype=np.float32), path)
    assert sitk.ReadImage(str(path)).GetSize() == (5, 4, 3)
    executable = Path(sys.executable).parent / ("fyron.exe" if os.name == "nt" else "fyron")
    subprocess.run([str(executable), "--help"], check=True, capture_output=True)
    subprocess.run([str(executable), "curate", "--help"], check=True, capture_output=True)
    help_text = subprocess.run([str(executable), "document-download", "--help"],
                               check=True, capture_output=True, text=True).stdout
    assert all(flag in help_text for flag in ("--id-col", "--document-id", "--token-cache", "--flat-output"))
    # Exercise document publication from the installed package, without a server.
    import io
    import requests
    from unittest.mock import patch
    from fyron import DocumentDownloader
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/pdf"
    response.raw = io.BytesIO(b"%PDF-1.4\n% synthetic\n%%EOF\n")
    with requests.Session() as session:
        with patch.object(session, "get", return_value=response):
            with DocumentDownloader(auth=session, output_dir="documents", flat_output=True,
                                    require_pdf=True, write_completion_record=False) as loader:
                results = loader.download_from_df(
                    pd.DataFrame({"document_url": ["https://documents.example.test/demo"],
                                  "id": ["00123"]}), id_col="id", results_csv="documents.csv")
    assert results.error.isna().all() and results.document_id.tolist() == ["00123"]
    saved = Path(results.path.iloc[0])
    assert saved.is_absolute() and saved.name == "00123.pdf" and saved.read_bytes().startswith(b"%PDF-")
    assert list(saved.parent.iterdir()) == [saved]


def excel():
    from fyron import read_excel, write_excel
    frame = pd.DataFrame({"value": [1, 2]})
    write_excel(frame, "roundtrip.xlsx")
    pd.testing.assert_frame_equal(read_excel("roundtrip.xlsx"), frame)


def survival():
    from fyron.survival import calculate_rmst, plot_kaplan_meier
    frame = pd.DataFrame({"time": [1, 2, 3, 4], "event": [1] * 4, "group": ["synthetic"] * 4})
    result = calculate_rmst(frame, "time", "event", tau=4)
    assert np.isclose(result["rmst"].iloc[0], 2.5)
    plot = plot_kaplan_meier(frame, "time", "event", group_col="group")
    plot.figure.savefig("km.png")
    assert Path("km.png").stat().st_size > 0


def ml():
    from fyron.ml import train_random_forest
    X = np.arange(40).reshape(-1, 1)
    result = train_random_forest(X, [0] * 20 + [1] * 20, n_estimators=10, random_state=0)
    assert len(result["y_pred"]) == 40 and result["metrics"]["auc"] > .9


def boruta():
    from fyron.ml import run_boruta_feature_selection
    X = pd.DataFrame(np.random.default_rng(3).normal(size=(40, 3)))
    result = run_boruta_feature_selection(X, (X[0] > 0).astype(int), max_iter=3, random_state=0)
    assert "selected_features" in result


def statistics():
    from fyron.statistics import cohens_d
    assert np.isfinite(cohens_d([1, 2, 3], [3, 4, 5]))


def validation():
    from fyron.validation import calibration_summary
    summary, bins = calibration_summary([0, 0, 1, 1], [.1, .2, .8, .9])
    assert np.isclose(summary["brier_score"], .025) and bins["n"].sum() == 4


def explainability():
    from sklearn.ensemble import RandomForestClassifier
    from fyron.explainability import permutation_importance_table, shap_values_table
    X = pd.DataFrame({"x": range(20), "y": [0, 1] * 10})
    y = (X.x > 10).astype(int)
    model = RandomForestClassifier(n_estimators=5, random_state=0).fit(X, y)
    assert len(permutation_importance_table(model, X, y, n_repeats=2)) == 2
    values = shap_values_table(model, X)
    assert len(values) == 40 and np.isfinite(values.shap_value).all()


def feature_selection():
    from fyron.feature_selection import variance_filter
    result = variance_filter(pd.DataFrame({"x": [1, 2, 3], "constant": [1] * 3}))
    assert result["selected_features"] == ["x"]


def descriptive():
    from fyron.descriptive import create_table_one
    assert not create_table_one(pd.DataFrame({"age": [20, 30, 40]}), numeric=["age"]).empty


def reporting():
    from fyron.reporting import dataframe_to_markdown
    assert "value" in dataframe_to_markdown(pd.DataFrame({"value": [1]}))


def audit():
    from fyron.audit import hash_file
    Path("hash.txt").write_text("synthetic")
    assert len(hash_file("hash.txt")) == 64


def curate():
    from fyron.curate import default_app_dir, build_compose_command
    app = default_app_dir()
    for relative in ("docker-compose.yml", "backend/package.json", "frontend/package.json"):
        assert (app / relative).is_file(), relative
    assert build_compose_command()[:2] == ["docker", "compose"]


def s3():
    from botocore.stub import Stubber
    from fyron.core.s3 import S3Storage
    storage = S3Storage(bucket="synthetic", access_key_id="fake", secret_access_key="fake", region_name="us-east-1")
    with Stubber(storage.client) as stub:
        stub.add_response("head_object", {}, {"Bucket": "synthetic", "Key": "record"})
        assert storage.exists("record")
        stub.assert_no_pending_responses()


def visualization():
    from fyron.visualization import plot_volume_difference_heatmap
    volume = np.zeros((3, 4, 5), dtype=np.float32)
    figure, axes, table = plot_volume_difference_heatmap(volume, volume + 1)
    figure.savefig("difference.png")
    assert not table.empty and Path("difference.png").stat().st_size > 0


def radiomics():
    import SimpleITK as sitk
    from radiomics.featureextractor import RadiomicsFeatureExtractor
    from fyron.boa_radiomics import extract_case_radiomics_features
    case = Path("radiomics-case")
    case.mkdir()
    image = np.arange(125, dtype=np.float32).reshape(5, 5, 5)
    mask = np.zeros_like(image, dtype=np.uint8)
    mask[1:4, 1:4, 1:4] = 1
    sitk.WriteImage(sitk.GetImageFromArray(image), str(case / "ct.nii.gz"))
    sitk.WriteImage(sitk.GetImageFromArray(mask), str(case / "total.nii.gz"))
    extractor = RadiomicsFeatureExtractor()
    extractor.disableAllFeatures()
    extractor.enableFeatureClassByName("firstorder")
    row = extract_case_radiomics_features(case, segmentation_kind="total", labels={"organ": 1}, extractor=extractor)
    assert row["radiomics_total_organ_voxel_count"] == 27


def dicom_seg():
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.uid import generate_uid, CTImageStorage, ExplicitVRLittleEndian
    from fyron.dicom.seg import write_dicom_seg, validate_dicom_seg
    study, series, frame = (generate_uid() for _ in range(3))
    sources = []
    for i in range(2):
        ds = Dataset()
        ds.file_meta = FileMetaDataset()
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        for key, value in dict(
            SOPClassUID=CTImageStorage, SOPInstanceUID=generate_uid(), StudyInstanceUID=study,
            SeriesInstanceUID=series, FrameOfReferenceUID=frame, Modality="CT", PatientName="Synthetic^Example",
            PatientID="synthetic", PatientBirthDate="", PatientSex="O", AccessionNumber="",
            StudyID="1", StudyDate="20200101", StudyTime="120000", SeriesNumber=1,
            InstanceNumber=i+1, Rows=4, Columns=5, ImagePositionPatient=[0., 0., float(i)],
            ImageOrientationPatient=[1., 0., 0., 0., 1., 0.], PixelSpacing=[1., 1.],
            SliceThickness=1., SamplesPerPixel=1, PhotometricInterpretation="MONOCHROME2",
            BitsAllocated=16, BitsStored=16, HighBit=15, PixelRepresentation=1,
        ).items():
            setattr(ds, key, value)
        sources.append(ds)
    mask = np.zeros((2, 4, 5), dtype=np.uint8)
    mask[:, 1:3, 2:4] = 1
    path = write_dicom_seg(mask, source_images=sources, output_path="mask.dcm",
                           segment_descriptions=[{"label": "synthetic", "label_value": 1}])
    assert validate_dicom_seg(path, source_images=sources)["number_of_segments"] == 1


CASES = {"base": base, "excel": excel, "survival": survival, "survival-ml": survival,
         "ml": ml, "boruta": boruta, "statistics": statistics, "validation": validation,
         "explainability": explainability, "feature-selection": feature_selection,
         "descriptive": descriptive, "reporting": reporting, "audit": audit,
         "curate": curate, "s3": s3, "visualization": visualization,
         "radiomics": radiomics, "dicom-seg": dicom_seg}


def main(extra):
    package = Path(fyron.__file__).resolve()
    site = Path(sysconfig.get_paths()["purelib"]).resolve()
    assert package.is_relative_to(site), f"Not an installed wheel: {package}"
    direct = importlib.metadata.distribution("fyron").read_text("direct_url.json") or "{}"
    assert not json.loads(direct).get("dir_info", {}).get("editable", False)
    assert sys.prefix != sys.base_prefix, "Probe must run inside its disposable environment"
    if extra == "base":
        for name in ("lifelines", "sklearn", "matplotlib", "boto3", "shap"):
            assert importlib.util.find_spec(name) is None, f"Unexpected optional package in base environment: {name}"
    if extra == "survival":
        assert importlib.util.find_spec("sklearn") is None
    base()
    selected = [extra] if extra != "all" else [key for key in CASES if key != "base"]
    for key in selected:
        if key == "radiomics" and sys.version_info >= (3, 12) and extra == "all":
            continue  # Declared Python-version marker, not a failed probe.
        if key != "base":
            CASES[key]()
    print(f"Installed wheel operations passed: {extra}; Python {sys.version.split()[0]}")


if __name__ == "__main__":
    main(sys.argv[1])
