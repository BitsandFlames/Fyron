"""Tiny synthetic datasets for Fyron examples and tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import SimpleITK as sitk
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

from fyron.datasets.preparation import (
    prepare_nnunetv2_dataset,
    prepare_yolo_classification_dataset,
    prepare_yolo_detection_dataset,
    validate_nnunetv2_dataset,
    validate_yolo_dataset,
    write_dataset_manifest,
)


def make_clinical_cohort(n: int = 40, *, random_state: int = 42) -> pd.DataFrame:
    """Create a deterministic synthetic clinical cohort."""
    rng = np.random.default_rng(random_state)
    age = rng.normal(64, 9, n).round(1)
    sex = rng.choice(["Female", "Male"], size=n)
    stage = rng.choice(["I", "II", "III", "IV"], size=n, p=[0.2, 0.3, 0.3, 0.2])
    risk_score = np.clip((age - 45) / 45 + rng.normal(0, 0.18, n), 0, 1)
    event = rng.binomial(1, np.clip(0.15 + risk_score * 0.55, 0, 0.9))
    return pd.DataFrame(
        {
            "patient_id": [f"SYN{idx:04d}" for idx in range(1, n + 1)],
            "age": age,
            "sex": sex,
            "stage": stage,
            "risk_score": risk_score.round(3),
            "event": event,
        }
    )


def make_survival_cohort(n: int = 40, *, random_state: int = 42) -> pd.DataFrame:
    """Create a deterministic survival-ready cohort with time and event."""
    rng = np.random.default_rng(random_state)
    df = make_clinical_cohort(n=n, random_state=random_state)
    baseline_hazard = np.clip(0.02 + df["risk_score"].to_numpy() * 0.06, 0.01, 0.2)
    times = rng.exponential(1 / baseline_hazard).round(1)
    censor = rng.uniform(12, 60, n).round(1)
    df["time"] = np.minimum(times, censor)
    df["event"] = ((times <= censor) & (df["event"].to_numpy() == 1)).astype(int)
    df["risk_group"] = pd.cut(df["risk_score"], bins=[-0.01, 0.33, 0.66, 1.0], labels=["Low", "Intermediate", "High"])
    return df


def make_classification_cohort(n: int = 80, *, random_state: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    """Create a tiny tabular classification dataset."""
    rng = np.random.default_rng(random_state)
    age = rng.normal(63, 10, n)
    marker = rng.normal(0, 1, n)
    imaging_score = rng.beta(2, 4, n)
    logits = -1.2 + 0.03 * (age - 60) + 1.1 * marker + 1.8 * imaging_score
    prob = 1 / (1 + np.exp(-logits))
    y = pd.Series(rng.binomial(1, prob), name="endpoint")
    X = pd.DataFrame(
        {
            "age": age.round(1),
            "marker": marker.round(3),
            "imaging_score": imaging_score.round(3),
        }
    )
    return X, y


def make_nifti_pair(output_dir: str | Path, *, shape: tuple[int, int, int] = (4, 8, 8)) -> dict[str, Path]:
    """Write a tiny synthetic image/mask NIfTI pair."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    z, y, x = shape
    image_arr = np.linspace(-900, 300, z * y * x, dtype=np.float32).reshape(shape)
    mask_arr = np.zeros(shape, dtype=np.uint8)
    mask_arr[:, y // 4 : y // 2, x // 4 : x // 2] = 1
    image = sitk.GetImageFromArray(image_arr)
    mask = sitk.GetImageFromArray(mask_arr)
    image.SetSpacing((1.0, 1.0, 2.0))
    mask.CopyInformation(image)
    image_path = out / "image.nii.gz"
    mask_path = out / "mask.nii.gz"
    sitk.WriteImage(image, str(image_path))
    sitk.WriteImage(mask, str(mask_path))
    return {"image": image_path, "mask": mask_path}


def make_dicom_series(
    output_dir: str | Path,
    *,
    shape: tuple[int, int, int] = (3, 8, 8),
    patient_id: str = "SYNTHETIC",
) -> list[Path]:
    """Write a tiny synthetic CT DICOM series."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    study_uid = generate_uid()
    series_uid = generate_uid()
    frame_uid = generate_uid()
    paths: list[Path] = []
    for index in range(shape[0]):
        path = out / f"slice_{index + 1:04d}.dcm"
        _write_ct_slice(
            path,
            rows=shape[1],
            cols=shape[2],
            study_uid=study_uid,
            series_uid=series_uid,
            frame_uid=frame_uid,
            sop_uid=generate_uid(),
            patient_id=patient_id,
            z=float(index),
        )
        paths.append(path)
    return paths


def make_boa_like_folder(output_dir: str | Path) -> Path:
    """Create a minimal BOA-like cohort folder with one synthetic case."""
    root = Path(output_dir)
    case = root / "patient0001"
    case.mkdir(parents=True, exist_ok=True)
    measurements = {
        "aggregated": {
            "abdominal_cavity": {"measurements_no_extremities": _tissue_measurements(100.0)},
            "thoracic_cavity": {"measurements_no_extremities": _tissue_measurements(80.0)},
            "l3": {"min_slice_idx": 1, "max_slice_idx": 2, "measurements_no_extremities": _tissue_measurements(20.0)},
        }
    }
    (case / "bca-measurements.json").write_text(json.dumps(measurements), encoding="utf-8")
    pair = make_nifti_pair(case)
    Path(pair["mask"]).rename(case / "body-regions.nii.gz")
    return root


def _tissue_measurements(base: float) -> dict[str, dict[str, float]]:
    tissues = ["bone", "muscle", "tat", "imat", "eat", "pat", "vat", "sat"]
    return {name: {"sum": float(base + idx)} for idx, name in enumerate(tissues)}


def _write_ct_slice(
    path: Path,
    *,
    rows: int,
    cols: int,
    study_uid: str,
    series_uid: str,
    frame_uid: str,
    sop_uid: str,
    patient_id: str,
    z: float,
) -> None:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = CTImageStorage
    file_meta.MediaStorageSOPInstanceUID = sop_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()
    ds = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.is_implicit_VR = False
    ds.is_little_endian = True
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = sop_uid
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.FrameOfReferenceUID = frame_uid
    ds.Modality = "CT"
    ds.SeriesDescription = "Fyron synthetic demo CT"
    ds.PatientName = "Synthetic^Fyron"
    ds.PatientID = patient_id
    ds.PatientBirthDate = "19700101"
    ds.PatientSex = "O"
    ds.StudyDate = "20200101"
    ds.StudyTime = "120000"
    ds.AccessionNumber = ""
    ds.StudyID = "1"
    ds.ReferringPhysicianName = ""
    ds.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.RescaleIntercept = -1024.0
    ds.RescaleSlope = 1.0
    ds.PixelData = np.zeros((rows, cols), dtype=np.int16).tobytes()
    ds.ImagePositionPatient = [0.0, 0.0, z]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.PixelSpacing = [1.0, 1.0]
    ds.SliceThickness = 1.0
    ds.SpacingBetweenSlices = 1.0
    ds.InstanceNumber = int(z) + 1
    ds.save_as(str(path), write_like_original=False)


__all__ = [
    "make_boa_like_folder",
    "make_classification_cohort",
    "make_clinical_cohort",
    "make_dicom_series",
    "make_nifti_pair",
    "make_survival_cohort",
    "prepare_nnunetv2_dataset",
    "prepare_yolo_classification_dataset",
    "prepare_yolo_detection_dataset",
    "validate_nnunetv2_dataset",
    "validate_yolo_dataset",
    "write_dataset_manifest",
]
