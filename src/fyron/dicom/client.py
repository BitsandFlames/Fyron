"""DICOM download utilities (DICOMweb) with optional NIfTI conversion."""

from __future__ import annotations

from .._diagnostics import event, safe_error, batch_report, error_event, completed_task

import hashlib
import logging
import os
import pathlib
import re
import shutil
import tempfile
import argparse
import json
import multiprocessing as mp
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, Sequence, Literal

import pandas as pd
import pydicom
import requests
import SimpleITK as sitk
from dicomweb_client.api import DICOMwebClient
from requests.auth import HTTPBasicAuth
from retrying import RetryError
from tqdm import tqdm

from ..fhir.auth import Auth, TokenAuth
from ..fhir._workers import managed_pool, positive_timeout, worker_auth as current_worker_auth
from ..fhir._client_credentials import _ClientCredentialsAuth
from ..fhir._device_auth import _DeviceAuth
from ..fhir._workers import PipeAuth as _WorkerAuth
from ..console import info
from .._completion import verified_files, publish_files

logger = logging.getLogger(__name__)


class DicomDownloadError(RuntimeError):
    """Raised when a DICOM download or conversion fails."""


def _filename_uid(value: object) -> str:
    uid = str(value)
    if len(uid) > 64 or not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*))*", uid):
        raise DicomDownloadError("Invalid DICOM UID; output was not published.")
    return uid


def _save_unique_instance(instance, directory: pathlib.Path, seen: set[str]) -> pathlib.Path:
    uid = _filename_uid(instance.SOPInstanceUID)
    if uid in seen:
        raise DicomDownloadError("Duplicate SOP Instance UID; output was not published.")
    seen.add(uid)
    destination = directory / f"{uid}.dcm"
    with destination.open("xb") as stream:
        instance.save_as(stream)
    return destination


@dataclass
class DicomResult:
    """Result metadata for one DICOM series download.

    Parameters
    ----------
    study_uid
        Requested DICOM ``StudyInstanceUID``.
    series_uid
        Requested or discovered DICOM ``SeriesInstanceUID``. This can be ``None``
        for study-level failures.
    download_id
        Deterministic Fyron identifier used as the default output folder name.
    path
        Local output path for the downloaded series or study folder.
    format
        Output format, usually ``"dicom"`` or ``"nifti"``.
    error
        ``None`` on success, otherwise a formatted error message.
    """

    study_uid: str
    series_uid: Optional[str]
    download_id: str
    path: str
    format: str
    error: Optional[str] = None
    skipped: bool = False


class DICOMDownloader:
    """Download DICOM studies/series via DICOMweb and optionally convert to NIfTI.

    Full-study downloads use WADO-RS ``iter_study`` (not QIDO series listing). Per-series
    downloads still use ``iter_series``.

    Parameters
    ----------
    auth
        Optional Auth or requests.Session to reuse.
    dicom_web_url
        Base DICOMweb endpoint (e.g., https://pacs.example.org/dicomweb).
        If omitted, uses DICOM_WEB_URL env.
    dicom_user
        Optional username for HTTP basic authentication. If omitted, uses
        ``DICOM_USER`` from the environment.
    dicom_password
        Optional password for HTTP basic authentication. If omitted, uses
        ``DICOM_PASSWORD`` from the environment.
    basic_auth
        Optional (user, password) tuple for basic auth (standalone).
    output_format
        "dicom" or "nifti" (default: nifti).
    use_compression
        Whether to compress NIfTI output.
    num_processes
        Number of worker processes for DataFrame downloads.
    log_downloads
        Emit progress-oriented log messages through the DICOM logger.
    save_reference_dicom
        When writing NIfTI output, keep one original DICOM slice beside the NIfTI
        as lightweight metadata/provenance.
    reference_dicom_name
        File name for the retained metadata DICOM.
    worker_auth_timeout
        Positive worker token-wait timeout in seconds (default 120).

    Returns
    -------
    DICOMDownloader
        Configured downloader that can fetch single series, full studies, or
        DataFrame-defined batches.
    """

    def __init__(
        self,
        auth: Optional[Union[Auth, requests.Session]] = None,
        dicom_web_url: Optional[str] = None,
        dicom_user: Optional[str] = None,
        dicom_password: Optional[str] = None,
        basic_auth: Optional[Tuple[str, str]] = None,
        output_format: str = "nifti",
        use_compression: bool = False,
        num_processes: int = 1,
        log_downloads: bool = False,
        save_reference_dicom: bool = False,
        reference_dicom_name: str = "reference.dcm",
        *,
        worker_auth_timeout: float = 120,
    ) -> None:
        """Initialize a reusable DICOMweb downloader.

        Parameters
        ----------
        auth
            Optional Fyron ``Auth`` object or existing ``requests.Session``. Use this
            when another part of the workflow already owns authentication.
        dicom_web_url
            Base DICOMweb endpoint. If omitted, Fyron reads ``DICOM_WEB_URL`` from
            the environment.
        dicom_user
            Optional username for HTTP basic authentication. If omitted, Fyron reads
            ``DICOM_USER`` from the environment.
        dicom_password
            Optional password for HTTP basic authentication. If omitted, Fyron reads
            ``DICOM_PASSWORD`` from the environment.
        basic_auth
            Optional ``(username, password)`` tuple. Do not combine this with
            ``dicom_user`` or ``dicom_password``.
        output_format
            Output type for downloaded series. Use ``"dicom"`` to preserve source
            slices or ``"nifti"`` to convert each series into a NIfTI volume.
        use_compression
            Whether NIfTI outputs should be compressed when ``output_format="nifti"``.
        num_processes
            Number of worker processes for DataFrame downloads. Supports Basic
            credentials or Fyron token/device auth with parent-coordinated refresh.
            Other custom sessions are restricted to sequential downloads.
        log_downloads
            Emit progress-oriented messages through the Fyron DICOM logger.
        save_reference_dicom
            When writing NIfTI output, copy one original source DICOM slice beside
            each NIfTI file as lightweight metadata and provenance.
        reference_dicom_name
            File name for the retained metadata DICOM. The value must be a file
            name, not a path; ``.dcm`` is appended when omitted.
        worker_auth_timeout
            Positive maximum worker wait for a token in seconds (default 120).

        Returns
        -------
        None
            The configured downloader instance is initialized in place.
        """
        self.dicom_web_url = dicom_web_url or os.environ.get("DICOM_WEB_URL")
        if not self.dicom_web_url:
            raise ValueError("dicom_web_url is required (or set DICOM_WEB_URL).")

        self.use_compression = use_compression
        self.output_format = self._normalize_format(output_format)
        self.num_processes = max(1, num_processes)
        self.worker_auth_timeout = positive_timeout(worker_auth_timeout, "worker_auth_timeout")
        self.log_downloads = log_downloads
        self.save_reference_dicom = bool(save_reference_dicom)
        self.reference_dicom_name = self._normalize_reference_dicom_name(reference_dicom_name)

        if basic_auth and (dicom_user or dicom_password):
            raise ValueError("Provide either basic_auth or dicom_user/dicom_password, not both.")

        if auth is not None and (
            basic_auth is not None or dicom_user is not None or dicom_password is not None
        ):
            raise ValueError("Provide auth or explicit basic credentials, not both.")
        env_user = os.environ.get("DICOM_USER") if auth is None else None
        env_password = os.environ.get("DICOM_PASSWORD") if auth is None else None
        if basic_auth:
            dicom_user, dicom_password = basic_auth
        else:
            dicom_user = dicom_user or env_user
            dicom_password = dicom_password or env_password
        self.dicom_user = dicom_user
        self.dicom_password = dicom_password

        if dicom_user or dicom_password:
            session = requests.Session()
            session.auth = HTTPBasicAuth(dicom_user or "", dicom_password or "")
            self.session = session
            self._close_session_on_exit = True
        elif isinstance(auth, Auth):
            self.session = auth.session
            self._close_session_on_exit = False
        elif isinstance(auth, requests.Session):
            self.session = auth
            self._close_session_on_exit = False
        else:
            self.session = requests.Session()
            self._close_session_on_exit = True

        from .._http import guard_redirects
        guard_redirects(self.session)
        self.client = DICOMwebClient(url=self.dicom_web_url, session=self.session)
        if self.log_downloads:
            event(logger, "dicom", "activity", level=logging.DEBUG)

    def __enter__(self) -> "DICOMDownloader":
        """Return self for context manager usage."""
        return self

    def close(self) -> None:
        """Close the underlying session if owned."""
        if self._close_session_on_exit:
            self.session.close()

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        """Close the session on context manager exit."""
        self.close()

    def _format_exception(self, exc: Exception) -> str:
        """Format an exception for logs, unwrapping RetryError and HTTP details when present."""
        return safe_error(exc)

    def _store_series_files(
        self,
        study_uid: str,
        series_uid: str,
        files: Sequence[pathlib.Path],
        target_dir: pathlib.Path,
        *,
        overwrite: bool = True,
    ) -> DicomResult:
        """Copy DICOM files to target_dir or convert them to NIfTI in target_dir."""
        download_id = self.download_id(study_uid, series_uid)
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            _filename_uid(series_uid)
            with tempfile.TemporaryDirectory(prefix=".fyron-stage-", dir=target_dir) as stage_dir:
                staging = pathlib.Path(stage_dir)
                if self.output_format == "dicom":
                    for src in files:
                        shutil.copy2(src, staging / src.name)
                else:
                    with tempfile.TemporaryDirectory() as convdir:
                        conv_path = pathlib.Path(convdir)
                        source_files = sorted(files)
                        if self.save_reference_dicom and source_files:
                            shutil.copy2(source_files[0], staging / self.reference_dicom_name)
                        for src in source_files:
                            shutil.copy2(src, conv_path / src.name)
                        series_reader = sitk.ImageSeriesReader()
                        gdcm_files = series_reader.GetGDCMSeriesFileNames(str(conv_path))
                        if not gdcm_files:
                            raise DicomDownloadError("No DICOM files found for series.")
                        series_reader.SetFileNames(gdcm_files)
                        image = series_reader.Execute()
                        out_path = staging / f"{series_uid}.nii.gz"
                        sitk.WriteImage(image, str(out_path), useCompression=self.use_compression)
                publish_files(staging, target_dir, f"{self.output_format}:{series_uid}", overwrite=overwrite)
        except Exception as exc:
            error_event(logger, "dicom", exc)
            return DicomResult(
                study_uid=study_uid,
                series_uid=series_uid,
                download_id=download_id,
                path=str(target_dir),
                format=self.output_format,
                error=("Existing output is unverified; review it before using skip_existing=False."
                       if isinstance(exc, FileExistsError) else safe_error(exc, default="conversion")),
            )
        return DicomResult(
            study_uid=study_uid,
            series_uid=series_uid,
            download_id=download_id,
            path=str(target_dir),
            format=self.output_format,
            error=None,
        )

    def _download_study_via_iter_study(
        self,
        study_uid: str,
        target_dir: pathlib.Path,
        skip_existing: bool = True,
        study_layout: str = "hierarchical",
    ) -> List[DicomResult]:
        """Download a full study via WADO-RS iter_study, group by SeriesInstanceUID, store output."""
        layout = self._normalize_study_layout(study_layout)
        results: List[DicomResult] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            seen_sop: set[str] = set()
            for instance in self.client.iter_study(study_instance_uid=study_uid):
                _save_unique_instance(instance, tmp_path, seen_sop)

            all_files = sorted(tmp_path.glob("*.dcm"))
            if not all_files:
                raise DicomDownloadError("No DICOM instances retrieved via iter_study.")

            by_series: Dict[str, List[pathlib.Path]] = {}
            for fp in all_files:
                try:
                    ds = pydicom.dcmread(fp, stop_before_pixels=True)
                except Exception as read_exc:
                    event(logger, "dicom", "warning", level=logging.WARNING)
                    continue
                suid = getattr(ds, "SeriesInstanceUID", None)
                if not suid:
                    event(logger, "dicom", "warning", level=logging.WARNING)
                    continue
                by_series.setdefault(str(suid), []).append(fp)

            if not by_series:
                raise DicomDownloadError("No series could be identified from iter_study download.")

            for ser_uid in sorted(by_series.keys()):
                series_files = by_series[ser_uid]
                series_dir = target_dir if layout == "flat" else target_dir / ser_uid
                download_id = self.download_id(study_uid, ser_uid)
                skip_series = False
                if skip_existing:
                    if layout == "flat":
                        skip_series = _flat_series_output_complete(
                            target_dir, ser_uid, series_files, self.output_format,
                            self.reference_dicom_name if self.save_reference_dicom and self.output_format == "nifti" else None,
                        )
                    else:
                        skip_series = _series_exists(series_dir, self.output_format, ser_uid,
                            self.reference_dicom_name if self.save_reference_dicom and self.output_format == "nifti" else None)
                if skip_series:
                    if self.log_downloads:
                        event(logger, "dicom", "activity", level=logging.DEBUG)
                    results.append(
                        DicomResult(
                            study_uid=study_uid,
                            series_uid=ser_uid,
                            download_id=download_id,
                            path=str(series_dir),
                            format=self.output_format,
                            error=None,
                            skipped=True,
                        )
                    )
                else:
                    results.append(
                        self._store_series_files(study_uid, ser_uid, series_files, series_dir, overwrite=not skip_existing)
                    )
        return results

    def _run_task(
        self,
        task: Tuple[str, Optional[str], bool, Optional[str]],
        output_dir: Union[str, pathlib.Path],
        skip_existing: bool,
        write_manifest: bool,
        study_layout: str = "hierarchical",
        save_study_manifest: Optional[bool] = None,
        save_reference_dicom: Optional[bool] = None,
        reference_dicom_name: Optional[str] = None,
    ) -> List[DicomResult]:
        """Execute a single download task (series or study)."""
        previous_save_reference = self.save_reference_dicom
        previous_reference_name = self.reference_dicom_name
        if save_reference_dicom is not None:
            self.save_reference_dicom = bool(save_reference_dicom)
        if reference_dicom_name is not None:
            self.reference_dicom_name = self._normalize_reference_dicom_name(reference_dicom_name)
        study_uid, series_uid, download_full_study, study_folder_name = task
        try:
            if download_full_study or series_uid is None:
                return self.download_study(
                    study_uid=study_uid,
                    output_dir=output_dir,
                    skip_existing=skip_existing,
                    write_manifest=write_manifest,
                    study_layout=study_layout,
                    study_folder_name=study_folder_name,
                    save_study_manifest=save_study_manifest,
                )
            return [
                self.download_series(
                    study_uid=study_uid,
                    series_uid=series_uid,
                    output_dir=output_dir,
                    skip_existing=skip_existing,
                )
            ]
        except Exception as exc:
            error_event(logger, "dicom", exc)
            return [
                DicomResult(
                    study_uid=study_uid,
                    series_uid=series_uid,
                    download_id=self.download_id(study_uid, series_uid),
                    path=str(output_dir),
                    format=self.output_format,
                    error=self._format_exception(exc),
                )
            ]
        finally:
            self.save_reference_dicom = previous_save_reference
            self.reference_dicom_name = previous_reference_name

    @staticmethod
    def download_id(study_uid: str, series_uid: Optional[str] = None) -> str:
        """Compute the deterministic output identifier for a study or series.

        Parameters
        ----------
        study_uid
            DICOM ``StudyInstanceUID``.
        series_uid
            Optional DICOM ``SeriesInstanceUID``. When provided, the identifier is
            based on ``"{study_uid}_{series_uid}"``; otherwise it is based on the
            study UID alone.

        Returns
        -------
        str
            SHA-256 hex digest used by Fyron as the default download folder name.
        """
        key = study_uid if series_uid is None else f"{study_uid}_{series_uid}"
        return hashlib.sha256(key.encode()).hexdigest()

    def download_series(
        self,
        study_uid: str,
        series_uid: str,
        output_dir: Union[str, pathlib.Path],
        skip_existing: bool = True,
    ) -> DicomResult:
        """Download one DICOM series into a deterministic output folder.

        Parameters
        ----------
        study_uid
            DICOM ``StudyInstanceUID`` containing the requested series.
        series_uid
            DICOM ``SeriesInstanceUID`` to download.
        output_dir
            Root output directory. Fyron writes the series under
            ``output_dir / download_id(study_uid, series_uid)``.
        skip_existing
            If True, return the existing output when a DICOM or NIfTI series
            already exists in the target folder.

        Returns
        -------
        DicomResult
            Result metadata with the local path, output format, deterministic
            download ID, and an error string when the operation failed.
        """
        download_id = self.download_id(study_uid, series_uid)
        target_dir = pathlib.Path(output_dir) / download_id
        return self._download_series_to_dir(
            study_uid=study_uid,
            series_uid=series_uid,
            target_dir=target_dir,
            skip_existing=skip_existing,
        )

    def download_study(
        self,
        study_uid: str,
        output_dir: Union[str, pathlib.Path],
        skip_existing: bool = True,
        write_manifest: bool = True,
        study_layout: Literal["hierarchical", "flat"] = "hierarchical",
        study_folder_name: Optional[object] = None,
        save_study_manifest: Optional[bool] = None,
    ) -> List[DicomResult]:
        """Download all series in a study under one study folder.

        Full-study retrieval uses WADO-RS ``iter_study`` only: instances are downloaded at
        study scope, grouped by ``SeriesInstanceUID``, then written to disk.

        Parameters
        ----------
        study_uid
            DICOM ``StudyInstanceUID`` to download.
        output_dir
            Root directory where the study folder is created.
        skip_existing
            If True, skip series whose output already exists.
        write_manifest
            Write ``study_manifest.json`` after a successful full-study download.
        study_layout
            ``"hierarchical"`` (default): ``{study_dir}/{series_uid}/`` holds that series
            (DICOM slices or one ``{series_uid}.nii.gz``).
            ``"flat"``: all DICOM files or all per-series NIfTI volumes live directly under
            ``study_dir`` (DICOM filenames are ``{SOPInstanceUID}.dcm``; NIfTI files are
            ``{series_uid}.nii.gz``).
        study_folder_name
            Optional readable prefix for the study directory. The sanitized label
            is followed by ``__{download_id(study_uid)}``, so different studies
            never share a directory merely because their patient label matches.
            Existing label-only directories are not reused or moved.
        save_study_manifest
            If not ``None``, overrides ``write_manifest`` for whether ``study_manifest.json``
            is written (use ``False`` to skip the manifest without changing ``write_manifest``).

        Returns
        -------
        list[DicomResult]
            One result per downloaded or skipped series. A study-level failure is
            raised as ``DicomDownloadError``.
        """
        study_id = self._study_output_dir_name(study_uid, study_folder_name)
        study_dir = pathlib.Path(output_dir) / study_id
        study_dir.mkdir(parents=True, exist_ok=True)
        layout = self._normalize_study_layout(study_layout)
        try:
            results = self._download_study_via_iter_study(
                study_uid=study_uid,
                target_dir=study_dir,
                skip_existing=skip_existing,
                study_layout=layout,
            )
        except Exception as exc:
            error_event(logger, "dicom", exc)
            raise DicomDownloadError(
                f"Failed to download study: {self._format_exception(exc)}"
            ) from None
        manifest_on = save_study_manifest if save_study_manifest is not None else write_manifest
        if manifest_on:
            _write_study_manifest(study_dir, results, study_layout=layout)
        return results

    @batch_report("dicom")
    def download_from_dataframe(
        self,
        df: pd.DataFrame,
        output_dir: Union[str, pathlib.Path],
        study_uid_col: str = "study_instance_uid",
        series_uid_col: str = "series_instance_uid",
        download_full_study: bool = False,
        skip_existing: bool = True,
        write_manifest: bool = True,
        study_layout: Literal["hierarchical", "flat"] = "hierarchical",
        study_folder_name_col: Optional[str] = None,
        save_study_manifest: Optional[bool] = None,
        results_csv: Optional[Union[str, pathlib.Path]] = None,
        save_reference_dicom: Optional[bool] = None,
        reference_dicom_name: Optional[str] = None,
        keep_reference_dicom: Optional[bool] = None,
    ) -> pd.DataFrame:
        """Download studies/series defined by a DataFrame.

        When ``download_full_study`` is True, ``study_layout`` controls folder layout (see
        :meth:`download_study`). ``write_manifest`` / ``save_study_manifest`` apply only to
        full-study rows. If ``study_folder_name_col`` is set, that column's string value
        (per row) prefixes the hashed study id under ``output_dir``. Repeated tasks
        for the same study/series and resolved output folder are downloaded once.

        Parameters
        ----------
        df
            Input manifest with one row per requested series, or one row per study
            when ``download_full_study=True``.
        output_dir
            Root directory for downloaded outputs.
        study_uid_col
            Column containing DICOM ``StudyInstanceUID`` values.
        series_uid_col
            Column containing DICOM ``SeriesInstanceUID`` values for series-level
            downloads. Not required in full-study mode.
        download_full_study
            If True, download all series in each study using WADO-RS study retrieval.
        skip_existing
            If True, skip rows whose expected DICOM or NIfTI outputs already exist.
        write_manifest
            Write full-study manifests when ``download_full_study=True``.
        study_layout
            Full-study layout: ``"hierarchical"`` for per-series folders or
            ``"flat"`` for all series directly under the study folder.
        study_folder_name_col
            Optional DataFrame column used as a readable prefix before the study hash.
        save_study_manifest
            Optional override for ``write_manifest`` in full-study downloads.
        results_csv
            Optional CSV path where the returned result table is also saved.
        save_reference_dicom
            One-call override for the constructor setting. When True and
            ``output_format="nifti"``, retain one source DICOM slice beside each
            NIfTI output.
        reference_dicom_name
            One-call override for the retained metadata DICOM file name.
        keep_reference_dicom
            Deprecated alias for ``save_reference_dicom`` kept for older scripts.

        Returns
        -------
        pandas.DataFrame
            One row per result with study UID, series UID, deterministic
            ``download_id``, output path, output format, and error text.
        """
        resolved_save_reference, resolved_reference_name = self._resolve_reference_dicom_options(
            save_reference_dicom=save_reference_dicom,
            reference_dicom_name=reference_dicom_name,
            keep_reference_dicom=keep_reference_dicom,
        )
        if self.log_downloads:
            event(logger, "dicom", "activity", level=logging.DEBUG)
        output_dir = pathlib.Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if study_uid_col not in df.columns:
            raise ValueError(f"Missing study column '{study_uid_col}'.")
        if not download_full_study and series_uid_col not in df.columns:
            raise ValueError(f"Missing series column '{series_uid_col}'.")
        if study_folder_name_col is not None and study_folder_name_col not in df.columns:
            raise ValueError(f"Missing study folder name column '{study_folder_name_col}'.")

        tasks = _build_tasks(
            df=df,
            study_uid_col=study_uid_col,
            series_uid_col=series_uid_col,
            download_full_study=download_full_study,
            study_folder_name_col=study_folder_name_col,
        )
        results: List[DicomResult] = []
        if self.num_processes > 1 and not (
            self.dicom_user or self.dicom_password
            or isinstance(self.session.auth, (_DeviceAuth, TokenAuth, _ClientCredentialsAuth))
        ):
            if self.log_downloads:
                event(logger, "dicom", "activity", level=logging.DEBUG)
            self.num_processes = 1

        if self.num_processes > 1:
            coordinated_auth = self.session.auth if isinstance(self.session.auth, (_DeviceAuth, TokenAuth, _ClientCredentialsAuth)) else None
            with managed_pool(coordinated_auth, self.num_processes, self.worker_auth_timeout) as (pool, _):
                for result in tqdm(
                    pool.imap_unordered(
                        _worker_download_task,
                        [
                            (
                                task,
                                self.dicom_web_url,
                                self.output_format,
                                self.use_compression,
                                skip_existing,
                                write_manifest,
                                output_dir,
                                self.dicom_user,
                                self.dicom_password,
                                study_layout,
                                save_study_manifest,
                                resolved_save_reference,
                                resolved_reference_name,
                            )
                            for task in tasks
                        ],
                    ),
                    total=len(tasks),
                    desc="Downloading DICOM",
                ):
                    results.extend(result)
                    completed_task(result)
        else:
            for task in tqdm(tasks, total=len(tasks), desc="Downloading DICOM"):
                task_results = self._run_task(
                        task=task,
                        output_dir=output_dir,
                        skip_existing=skip_existing,
                        write_manifest=write_manifest,
                        study_layout=study_layout,
                        save_study_manifest=save_study_manifest,
                        save_reference_dicom=resolved_save_reference,
                        reference_dicom_name=resolved_reference_name,
                    )
                results.extend(task_results)
                completed_task(task_results)
        df_out = pd.DataFrame([r.__dict__ for r in results])
        if results_csv:
            pathlib.Path(results_csv).parent.mkdir(parents=True, exist_ok=True)
            df_out.to_csv(results_csv, index=False)
        return df_out

    def download_from_df(
        self,
        df: pd.DataFrame,
        output_dir: Union[str, pathlib.Path],
        study_uid_col: str = "study_instance_uid",
        series_uid_col: str = "series_instance_uid",
        download_full_study: bool = False,
        skip_existing: bool = True,
        write_manifest: bool = True,
        study_layout: Literal["hierarchical", "flat"] = "hierarchical",
        study_folder_name_col: Optional[str] = None,
        save_study_manifest: Optional[bool] = None,
        results_csv: Optional[Union[str, pathlib.Path]] = None,
        save_reference_dicom: Optional[bool] = None,
        reference_dicom_name: Optional[str] = None,
        keep_reference_dicom: Optional[bool] = None,
    ) -> pd.DataFrame:
        """Short alias for :meth:`download_from_dataframe`.

        Parameters
        ----------
        df
            Input manifest with study and optionally series UID columns.
        output_dir
            Root directory for downloaded outputs.
        study_uid_col
            Column containing DICOM ``StudyInstanceUID`` values.
        series_uid_col
            Column containing DICOM ``SeriesInstanceUID`` values.
        download_full_study
            If True, download all series for each study row.
        skip_existing
            If True, skip outputs that already exist.
        write_manifest
            Write full-study manifests when applicable.
        study_layout
            Full-study output layout.
        study_folder_name_col
            Optional DataFrame column for human-readable study folder names.
        save_study_manifest
            Optional full-study manifest override.
        results_csv
            Optional path for saving the returned result table.
        save_reference_dicom
            One-call override for retaining a source DICOM beside NIfTI outputs.
        reference_dicom_name
            One-call override for the retained metadata DICOM file name.
        keep_reference_dicom
            Deprecated alias for ``save_reference_dicom``.

        Returns
        -------
        pandas.DataFrame
            Same result table returned by ``download_from_dataframe``.
        """
        return self.download_from_dataframe(
            df=df,
            output_dir=output_dir,
            study_uid_col=study_uid_col,
            series_uid_col=series_uid_col,
            download_full_study=download_full_study,
            skip_existing=skip_existing,
            write_manifest=write_manifest,
            study_layout=study_layout,
            study_folder_name_col=study_folder_name_col,
            save_study_manifest=save_study_manifest,
            results_csv=results_csv,
            save_reference_dicom=save_reference_dicom,
            reference_dicom_name=reference_dicom_name,
            keep_reference_dicom=keep_reference_dicom,
        )

    def _download_series_to_dir(
        self,
        study_uid: str,
        series_uid: str,
        target_dir: pathlib.Path,
        skip_existing: bool = True,
    ) -> DicomResult:
        """Download a series into a target directory."""
        target_dir.mkdir(parents=True, exist_ok=True)
        download_id = self.download_id(study_uid, series_uid)
        if skip_existing and _series_exists(target_dir, self.output_format, series_uid,
                self.reference_dicom_name if self.save_reference_dicom and self.output_format == "nifti" else None):
            if self.log_downloads:
                event(logger, "dicom", "activity", level=logging.DEBUG)
            return DicomResult(
                study_uid=study_uid,
                series_uid=series_uid,
                download_id=download_id,
                path=str(target_dir),
                format=self.output_format,
                error=None,
                skipped=True,
            )
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = pathlib.Path(tmpdir)
                saved: List[pathlib.Path] = []
                seen_sop: set[str] = set()
                for instance in self.client.iter_series(
                    study_instance_uid=study_uid,
                    series_instance_uid=series_uid,
                ):
                    saved.append(_save_unique_instance(instance, tmp_path, seen_sop))
                if not saved:
                    return DicomResult(
                        study_uid=study_uid,
                        series_uid=series_uid,
                        download_id=download_id,
                        path=str(target_dir),
                        format=self.output_format,
                        error="No DICOM instances retrieved for series.",
                    )
                return self._store_series_files(study_uid, series_uid, saved, target_dir, overwrite=not skip_existing)
        except Exception as exc:
            error_event(logger, "dicom", exc)
            return DicomResult(
                study_uid=study_uid,
                series_uid=series_uid,
                download_id=download_id,
                path=str(target_dir),
                format=self.output_format,
                error=self._format_exception(exc),
            )

    @staticmethod
    def _normalize_format(output_format: str) -> str:
        """Normalize output format to 'dicom' or 'nifti'."""
        fmt = output_format.strip().lower()
        if fmt in {"dicom", "dcm", ".dcm"}:
            return "dicom"
        if fmt in {"nifti", "nii", "nii.gz", ".nii", ".nii.gz"}:
            return "nifti"
        raise ValueError("output_format must be 'dicom' or 'nifti'.")

    @staticmethod
    def _normalize_study_layout(study_layout: str) -> Literal["hierarchical", "flat"]:
        """Normalize study folder layout for full-study downloads."""
        s = study_layout.strip().lower()
        if s in {"flat", "one_folder", "single_folder"}:
            return "flat"
        if s in {"hierarchical", "hierarchy", "nested", "per_series"}:
            return "hierarchical"
        raise ValueError("study_layout must be 'hierarchical' or 'flat'.")

    @staticmethod
    def _normalize_reference_dicom_name(name: str) -> str:
        """Validate the retained metadata DICOM file name."""
        value = str(name).strip()
        if not value:
            raise ValueError("reference_dicom_name must not be empty.")
        if pathlib.Path(value).name != value:
            raise ValueError("reference_dicom_name must be a file name, not a path.")
        if not value.lower().endswith(".dcm"):
            value += ".dcm"
        return value

    def _resolve_reference_dicom_options(
        self,
        *,
        save_reference_dicom: Optional[bool],
        reference_dicom_name: Optional[str],
        keep_reference_dicom: Optional[bool],
    ) -> Tuple[bool, str]:
        """Resolve constructor and one-call reference-DICOM settings."""
        if keep_reference_dicom is not None:
            warnings.warn(
                "keep_reference_dicom is deprecated; use save_reference_dicom instead.",
                DeprecationWarning,
                stacklevel=3,
            )
            if save_reference_dicom is not None and bool(save_reference_dicom) != bool(keep_reference_dicom):
                raise ValueError(
                    "save_reference_dicom and deprecated keep_reference_dicom disagree."
                )
            save_reference_dicom = bool(keep_reference_dicom)
        resolved_save = self.save_reference_dicom if save_reference_dicom is None else bool(save_reference_dicom)
        resolved_name = (
            self.reference_dicom_name
            if reference_dicom_name is None
            else self._normalize_reference_dicom_name(reference_dicom_name)
        )
        return resolved_save, resolved_name

    @staticmethod
    def _study_output_dir_name(study_uid: str, study_folder_name: Optional[object]) -> str:
        """Resolve a study-specific directory, optionally with a readable prefix."""
        if study_folder_name is None:
            return DICOMDownloader.download_id(study_uid)
        try:
            if bool(pd.isna(study_folder_name)):
                return DICOMDownloader.download_id(study_uid)
        except (TypeError, ValueError):
            pass
        raw = str(study_folder_name).strip()
        if not raw:
            return DICOMDownloader.download_id(study_uid)
        forbidden = '<>:"/\\|?*\n\r\t'
        safe = "".join(ch if ch not in forbidden and ord(ch) >= 32 else "_" for ch in raw)
        safe = safe.strip(" .")
        if not safe:
            return DICOMDownloader.download_id(study_uid)
        study_id = DICOMDownloader.download_id(study_uid)
        # Bound bytes rather than characters for multibyte patient labels.
        prefix = safe.encode("utf-8")[:240 - len(study_id) - 2].decode("utf-8", errors="ignore")
        return f"{prefix}__{study_id}"


def _series_exists(target_dir: pathlib.Path, output_format: str, series_uid: Optional[str] = None,
                   reference_name: Optional[str] = None) -> bool:
    """Skip only outputs verified against a completion record."""
    paths = verified_files(target_dir, f"{output_format}:{series_uid}") if series_uid else []
    return bool(paths) and (reference_name is None or reference_name in {p.name for p in paths})


def _flat_series_output_complete(
    study_dir: pathlib.Path,
    series_uid: str,
    series_files: Sequence[pathlib.Path],
    output_format: str,
    reference_name: Optional[str] = None,
) -> bool:
    paths = verified_files(study_dir, f"{output_format}:{series_uid}")
    if output_format == "dicom":
        return bool(paths) and {p.name for p in paths} == {p.name for p in series_files}
    return bool(paths) and (reference_name is None or reference_name in {p.name for p in paths})


def _write_study_manifest(
    study_dir: pathlib.Path,
    results: Sequence[DicomResult],
    study_layout: Optional[str] = None,
) -> None:
    """Write a study manifest JSON file with series results."""
    study_dir.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, object] = {
        "series": [
            {
                "study_uid": r.study_uid,
                "series_uid": r.series_uid,
                "download_id": r.download_id,
                "path": r.path,
                "format": r.format,
                "error": r.error,
            }
            for r in results
        ],
    }
    if study_layout is not None:
        manifest["study_layout"] = study_layout
    with (study_dir / "study_manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2)


def _build_tasks(
    df: pd.DataFrame,
    study_uid_col: str,
    series_uid_col: str,
    download_full_study: bool,
    study_folder_name_col: Optional[str] = None,
) -> List[Tuple[str, Optional[str], bool, Optional[str]]]:
    """Build download tasks from a DataFrame."""
    tasks: List[Tuple[str, Optional[str], bool, Optional[str]]] = []
    seen = set()
    for row in df.itertuples(index=False):
        study_uid = getattr(row, study_uid_col)
        series_uid = getattr(row, series_uid_col, None) if not download_full_study else None
        folder_label: Optional[str] = None
        if download_full_study and study_folder_name_col:
            v = getattr(row, study_folder_name_col)
            if v is not None:
                try:
                    if bool(pd.isna(v)):
                        v = None
                except (TypeError, ValueError):
                    pass
            if v is not None:
                folder_label = str(v).strip() or None
        folder = DICOMDownloader._study_output_dir_name(study_uid, folder_label) if download_full_study else None
        key = (study_uid, series_uid, folder)
        if key not in seen:
            tasks.append((study_uid, series_uid, download_full_study, folder_label))
            seen.add(key)
    return tasks


def _worker_download_task(
    args: Tuple[
        Tuple[str, Optional[str], bool, Optional[str]],
        str,
        str,
        bool,
        bool,
        bool,
        Union[str, pathlib.Path],
        Optional[str],
        Optional[str],
        str,
        Optional[bool],
        bool,
        str,
        Optional[_WorkerAuth],
    ],
) -> List[DicomResult]:
    """Worker helper for parallel DICOM downloads."""
    worker_auth = current_worker_auth() or (args[13] if len(args) > 13 else None)
    (
        task,
        dicom_web_url,
        output_format,
        use_compression,
        skip_existing,
        write_manifest,
        output_dir,
        user,
        password,
        study_layout,
        save_study_manifest,
        save_reference_dicom,
        reference_dicom_name,
    ) = args[:13]
    session = requests.Session() if worker_auth is not None else None
    if session is not None:
        session.auth = worker_auth
    downloader = DICOMDownloader(
        auth=session,
        dicom_web_url=dicom_web_url,
        dicom_user=user,
        dicom_password=password,
        output_format=output_format,
        use_compression=use_compression,
        save_reference_dicom=save_reference_dicom,
        reference_dicom_name=reference_dicom_name,
    )
    try:
        return downloader._run_task(
            task=task,
            output_dir=output_dir,
            skip_existing=skip_existing,
            write_manifest=write_manifest,
            study_layout=study_layout,
            save_study_manifest=save_study_manifest,
        )
    finally:
        downloader.close()
        if session is not None:
            session.close()


def main() -> int:
    """CLI entrypoint for DICOM downloads."""
    parser = argparse.ArgumentParser(description="Fyron DICOM downloader")
    parser.add_argument("--dicom-web-url", default=os.environ.get("DICOM_WEB_URL"))
    parser.add_argument("--dicom-user", default=os.environ.get("DICOM_USER"))
    parser.add_argument("--dicom-password", default=os.environ.get("DICOM_PASSWORD"))
    parser.add_argument("--study-uid")
    parser.add_argument("--series-uid", default=None)
    parser.add_argument("--csv", help="Path to CSV with study/series columns")
    parser.add_argument("--study-col", default="study_instance_uid")
    parser.add_argument("--series-col", default="series_instance_uid")
    parser.add_argument("--full-study", action="store_true")
    parser.add_argument("--output-dir", default="dicom_out")
    parser.add_argument("--output-format", default="nifti")
    parser.add_argument("--compression", action="store_true")
    parser.add_argument(
        "--save-reference-dicom",
        action="store_true",
        help="When writing NIfTI output, keep one source DICOM slice as metadata",
    )
    parser.add_argument(
        "--reference-dicom-name",
        default="reference.dcm",
        help="File name for --save-reference-dicom",
    )
    parser.add_argument("--processes", type=int, default=1)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument(
        "--study-layout",
        choices=("hierarchical", "flat"),
        default="hierarchical",
        help="Full-study folder layout: per-series subfolders or single study folder",
    )
    parser.add_argument(
        "--study-folder-name",
        default=None,
        help="For single full-study download: subdirectory name under output-dir (default: hashed id)",
    )
    parser.add_argument(
        "--study-folder-col",
        default=None,
        help="CSV column whose value names each study folder when using --full-study",
    )
    parser.add_argument(
        "--no-study-manifest",
        action="store_true",
        help="Do not write study_manifest.json for full-study downloads",
    )
    parser.add_argument("--results-csv", default=None)
    args = parser.parse_args()

    if not args.dicom_web_url:
        raise SystemExit("DICOM_WEB_URL is required (or pass --dicom-web-url).")

    downloader = DICOMDownloader(
        dicom_web_url=args.dicom_web_url,
        dicom_user=args.dicom_user,
        dicom_password=args.dicom_password,
        output_format=args.output_format,
        use_compression=args.compression,
        num_processes=args.processes,
        save_reference_dicom=args.save_reference_dicom,
        reference_dicom_name=args.reference_dicom_name,
    )

    if args.csv:
        df = pd.read_csv(args.csv)
        results = downloader.download_from_dataframe(
            df=df,
            output_dir=args.output_dir,
            study_uid_col=args.study_col,
            series_uid_col=args.series_col,
            download_full_study=args.full_study,
            skip_existing=args.skip_existing,
            write_manifest=args.manifest,
            study_layout=args.study_layout,
            study_folder_name_col=args.study_folder_col,
            save_study_manifest=False if args.no_study_manifest else None,
            results_csv=args.results_csv,
        )
        info(f"Download results: {len(results)}; failed: {int(results['error'].notna().sum()) if 'error' in results else 0}")
        return 0

    if not args.study_uid:
        raise SystemExit("Provide --study-uid or --csv.")

    if args.series_uid:
        result = downloader.download_series(
            study_uid=args.study_uid,
            series_uid=args.series_uid,
            output_dir=args.output_dir,
            skip_existing=args.skip_existing,
        )
        info("Download failed" if result.error else ("Download skipped" if result.skipped else "Download succeeded"))
    else:
        results = downloader.download_study(
            study_uid=args.study_uid,
            output_dir=args.output_dir,
            skip_existing=args.skip_existing,
            write_manifest=args.manifest,
            study_layout=args.study_layout,
            study_folder_name=args.study_folder_name,
            save_study_manifest=False if args.no_study_manifest else None,
        )
        for result in results:
            info("Download failed" if result.error else ("Download skipped" if result.skipped else "Download succeeded"))
    return 0
