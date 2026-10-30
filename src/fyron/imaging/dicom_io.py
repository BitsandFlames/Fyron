"""DICOM header reading and series I/O via pydicom and SimpleITK."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import numpy as np
import pydicom
import SimpleITK as sitk
from pydicom.errors import InvalidDicomError

from fyron.imaging._helpers import (
    dataset_to_plain_dict,
    parse_dicom_tag_spec,
    require_dir,
    require_file,
)

if TYPE_CHECKING:
    import pandas as pd

StrPath = Union[str, Path]


def read_dicom_header(
    dicom_path: StrPath,
    *,
    stop_before_pixels: bool = True,
    force: bool = False,
    as_dict: bool = False,
    selected_tags: list[str] | None = None,
) -> Union[pydicom.Dataset, dict[str, Any]]:
    """Read a DICOM file header with pydicom.

    Parameters
    ----------
    dicom_path
        Path to a DICOM part-10 file.
    stop_before_pixels
        If True (default), skip loading pixel data for faster IO.
    force
        If True, attempt to read non-standard files (passed to ``dcmread``).
    as_dict
        If True, return a flat ``dict`` of tag keyword (or string tag) to value.
    selected_tags
        Optional list of DICOM keywords (e.g. ``\"PatientID\"``) or hex tags
        (``\"0010,0020\"`` / ``\"00100020\"``).

    Returns
    -------
    pydicom.dataset.Dataset or dict
        Full dataset, a subset dataset (only when ``selected_tags`` is set and
        ``as_dict`` is False), or a dict view.

    Raises
    ------
    FileNotFoundError
        If the path does not exist.
    ValueError
        If the path is not a file or the file is not valid DICOM.
    KeyError
        If ``selected_tags`` requests a missing element.

    Examples
    --------
    >>> from fyron.imaging import read_dicom_header
    >>> # ds = read_dicom_header(\"image.dcm\", stop_before_pixels=True)
    >>> # meta = read_dicom_header(\"image.dcm\", as_dict=True, selected_tags=[\"Modality\"])
    """
    path = require_file(dicom_path, what="DICOM file")
    try:
        ds = pydicom.dcmread(
            path,
            stop_before_pixels=stop_before_pixels,
            force=force,
        )
    except InvalidDicomError as exc:
        raise ValueError(f"Not a valid DICOM file: {path}") from exc
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to read DICOM file: {path}: {exc}") from exc

    if not selected_tags:
        if as_dict:
            return dataset_to_plain_dict(ds, skip_pixel_data=stop_before_pixels)
        return ds

    slim: dict[str, Any] = {}
    subset = pydicom.Dataset()
    for name in selected_tags:
        tag = parse_dicom_tag_spec(name)
        elem = ds.get(tag)
        if elem is None:
            raise KeyError(f"Tag not present in dataset {path}: {name!r}")
        key = elem.keyword if elem.keyword else str(elem.tag)
        try:
            slim[key] = elem.value
        except Exception:  # noqa: BLE001
            slim[key] = str(elem.value)
        subset.add_new(elem.tag, elem.VR, elem.value)

    if as_dict:
        return slim
    return subset


def get_dicom_series_ids(
    dicom_dir: StrPath,
    *,
    include_metadata: bool = False,
    recursive: bool = False,
) -> Union[list[str], "pd.DataFrame"]:
    """List DICOM series IDs under a directory using GDCM (via SimpleITK).

    Parameters
    ----------
    dicom_dir
        Directory containing DICOM files (or subdirectories when ``recursive``).
    include_metadata
        If True, return a ``pandas.DataFrame`` summary; otherwise a list of series UIDs.
    recursive
        If True, scan subfolders for ``*.dcm`` files and aggregate series IDs found in
        each directory that contains DICOM (can be slower on large trees).

    Returns
    -------
    list[str] or pandas.DataFrame
        Series instance UIDs, or a metadata table when ``include_metadata`` is True.
        Empty input yields ``[]`` or an empty DataFrame with the expected columns.

    Examples
    --------
    >>> from fyron.imaging import get_dicom_series_ids
    >>> # ids = get_dicom_series_ids(\"/path/to/study\")
    >>> # df = get_dicom_series_ids(\"/path/to/study\", include_metadata=True, recursive=True)
    """
    import pandas as pd

    root = require_dir(dicom_dir, what="DICOM directory")
    dirs_to_scan = _collect_dicom_dirs(root, recursive=recursive)
    seen: dict[str, Path] = {}
    for d in dirs_to_scan:
        try:
            ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(d))
        except RuntimeError:
            continue
        for sid in ids:
            if sid and sid not in seen:
                seen[sid] = d

    series_list = sorted(seen.keys())
    if not include_metadata:
        return series_list

    columns = [
        "series_id",
        "number_of_files",
        "first_file",
        "modality",
        "series_description",
        "study_instance_uid",
        "series_instance_uid",
    ]
    if not series_list:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, Any]] = []
    for sid in series_list:
        study_dir = seen[sid]
        files = list(sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(study_dir), sid))
        n_files = len(files)
        first = files[0] if files else None
        modality = series_description = study_uid = series_uid = pd.NA
        if first is not None:
            try:
                hdr = read_dicom_header(first, stop_before_pixels=True)
                if isinstance(hdr, dict):
                    modality = hdr.get("Modality", pd.NA)
                    series_description = hdr.get("SeriesDescription", pd.NA)
                    study_uid = hdr.get("StudyInstanceUID", pd.NA)
                    series_uid = hdr.get("SeriesInstanceUID", pd.NA)
                else:
                    modality = getattr(hdr, "Modality", pd.NA)
                    series_description = getattr(hdr, "SeriesDescription", pd.NA)
                    study_uid = getattr(hdr, "StudyInstanceUID", pd.NA)
                    series_uid = getattr(hdr, "SeriesInstanceUID", pd.NA)
            except (ValueError, KeyError, OSError):
                pass
        rows.append(
            {
                "series_id": sid,
                "number_of_files": n_files,
                "first_file": first,
                "modality": modality,
                "series_description": series_description,
                "study_instance_uid": study_uid,
                "series_instance_uid": series_uid,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _collect_dicom_dirs(root: Path, *, recursive: bool) -> list[Path]:
    if not recursive:
        return [root]
    dirs: set[Path] = {root}
    for p in root.rglob("*.dcm"):
        dirs.add(p.parent)
    return sorted(dirs)


def read_dicom_series(
    study_path: StrPath,
    series_id: str,
    *,
    return_array: bool = False,
) -> Union[sitk.Image, tuple[sitk.Image, np.ndarray]]:
    """Read a DICOM series as a ``SimpleITK.Image``.

    Parameters
    ----------
    study_path
        Directory passed to ``GetGDCMSeriesFileNames`` (must contain the series).
    series_id
        Series instance UID as returned by ``get_dicom_series_ids``.
    return_array
        If True, also return ``numpy`` array in **Z, Y, X** order (``GetArrayFromImage``).

    Returns
    -------
    SimpleITK.Image or tuple
        Image, or ``(image, array)`` when ``return_array`` is True.

    Raises
    ------
    FileNotFoundError
        If ``study_path`` does not exist.
    ValueError
        If the series ID is unknown or files cannot be read.

    Examples
    --------
    >>> from fyron.imaging import read_dicom_series
    >>> # img = read_dicom_series(\"/path/study\", \"1.2.3.4.5\")
    >>> # img, arr = read_dicom_series(\"/path/study\", \"1.2.3.4.5\", return_array=True)
    """
    root = require_dir(study_path, what="study directory")
    ids = list(sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(root)))
    if series_id not in ids:
        preview = ", ".join(ids[:10])
        more = f" (+{len(ids) - 10} more)" if len(ids) > 10 else ""
        raise ValueError(
            f"Series ID not found under {root!r}: {series_id!r}. "
            f"Available IDs ({len(ids)}): {preview}{more}"
        )
    files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(root), series_id)
    if not files:
        raise ValueError(f"No files for series {series_id!r} under {root}")
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    try:
        image = reader.Execute()
    except RuntimeError as exc:
        raise ValueError(f"Failed to read DICOM series {series_id!r}: {exc}") from exc
    if return_array:
        return image, sitk.GetArrayFromImage(image)
    return image
