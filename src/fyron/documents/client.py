"""Document downloader utilities for URL lists and DataFrames."""

from __future__ import annotations

from .._diagnostics import event, safe_error, batch_report, error_event, completed_task

import hashlib
import logging
import math
import mimetypes
import numbers
import re
import os
import pathlib
import threading
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, fields
from typing import Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlsplit

from ..fhir.auth import Auth
from .._completion import verified_files, publish_files

logger = logging.getLogger(__name__)


class DocumentDownloadError(RuntimeError):
    """Raised when a document download fails."""


@dataclass
class DocumentResult:
    url: str
    download_id: str
    path: str
    status_code: Optional[int]
    content_type: Optional[str] = None
    sha256: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False
    document_id: Optional[str] = None


class DocumentDownloader:
    """Download documents from URLs into a deterministic folder structure.

    Parameters
    ----------
    auth:
        Optional Auth or requests.Session to reuse.
    basic_auth:
        Optional (user, password) tuple for basic auth (standalone).
    base_url:
        Optional base URL to prefix relative paths.
    output_dir:
        Parent folder where documents are stored.
    timeout:
        Request timeout in seconds.
    skip_existing:
        Skip downloads if the target file already exists.
    log_downloads:
        If True, logs each download.
    require_pdf:
        Require HTTP 200, application/pdf content type, and a PDF header.
    allow_redirects:
        Follow only same-origin redirects when True; reject redirects when False.
    write_completion_record:
        Write a hidden JSON record for verified restarts. If False, newly saved
        files cannot be skipped on subsequent runs without an existing valid record.
    flat_output:
        Save documents directly in output_dir using URL-hash filenames. Results
        contain absolute paths. Explicit output_path takes precedence.
    """

    def __init__(
        self,
        auth: Optional[Union[Auth, requests.Session]] = None,
        base_url: Optional[str] = None,
        output_dir: Union[str, pathlib.Path] = "documents_out",
        timeout: int = 30,
        skip_existing: bool = True,
        log_downloads: bool = False,
        max_workers: int = 4,
        retries: Optional[Retry] = None,
        save_mode: str = "auto",
        force_extension: Optional[str] = None,
        basic_auth: Optional[Tuple[str, str]] = None,
        *,
        require_pdf: bool = False,
        allow_redirects: bool = True,
        write_completion_record: bool = True,
        flat_output: bool = False,
    ) -> None:
        """Initialize the document downloader."""
        if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number.")
        self.base_url = base_url or os.environ.get("FHIR_BASE_URL")
        self.output_dir = pathlib.Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.skip_existing = skip_existing
        self.log_downloads = log_downloads
        self.max_workers = max(1, max_workers)
        self.save_mode = save_mode
        self.force_extension = force_extension
        self.require_pdf = require_pdf
        self.allow_redirects = allow_redirects
        self.write_completion_record = write_completion_record
        self.flat_output = flat_output
        self._owned_auth = None
        self._download_lock = threading.Lock()
        self._batch_state = threading.local()

        if basic_auth and auth is not None:
            raise ValueError("Provide either basic_auth or auth, not both.")

        if isinstance(auth, Auth):
            self.session = auth.session
            self._close_session_on_exit = False
        elif isinstance(auth, requests.Session):
            self.session = auth
            self._close_session_on_exit = False
        elif basic_auth:
            session = requests.Session()
            session.auth = HTTPBasicAuth(basic_auth[0], basic_auth[1])
            self.session = session
            self._close_session_on_exit = True
        else:
            if os.environ.get("FHIR_AUTH_URL") or os.environ.get("FHIR_REFRESH_URL"):
                self._owned_auth = Auth(
                    auth_method="env",
                    auth_url=os.environ.get("FHIR_AUTH_URL"),
                    refresh_url=os.environ.get("FHIR_REFRESH_URL"),
                )
                self.session = self._owned_auth.session
                self._close_session_on_exit = False
            else:
                self.session = requests.Session()
                self._close_session_on_exit = True

        from .._http import guard_redirects
        guard_redirects(self.session)
        if retries is None:
            retries = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[502, 503, 504],
                allowed_methods=["GET"],
                raise_on_status=False,
            )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def __enter__(self) -> "DocumentDownloader":
        """Return self for context manager usage."""
        return self

    def close(self) -> None:
        """Close the underlying session if owned."""
        if self._owned_auth is not None:
            self._owned_auth.close()
        elif self._close_session_on_exit:
            self.session.close()

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        """Close the session on context manager exit."""
        self.close()

    @staticmethod
    def download_id(url: str) -> str:
        """Return a deterministic download ID for a URL."""
        return hashlib.sha256(url.encode()).hexdigest()

    def download_url(
        self, url: str, *, output_path: Optional[Union[str, pathlib.Path]] = None,
        document_id: Optional[Union[str, int]] = None,
    ) -> DocumentResult:
        """Download a document with staged publication and verified restarts.

        Parameters
        ----------
        url:
            Absolute document URL or a path relative to base_url.
        output_path:
            Exact destination file, bypassing automatic naming. When omitted,
            use automatic naming below output_dir.
        document_id:
            Optional filename-safe string or integer ID used for automatic naming.
            Defaults to the URL hash; output_path overrides automatic naming.

        Returns
        -------
        DocumentResult
            Sensitive source/path metadata, HTTP status, hash, and a controlled
            error on failure. Existing files require explicit replacement via
            skip_existing=False. PDF validation checks type and signature, not
            complete PDF syntax or clinical correctness.
        """
        full_url = self._resolve_url(url)
        download_id = self.download_id(full_url)
        chosen_id = download_id if document_id is None else _validate_document_id(document_id)
        filename = _filename_from_url(full_url) if document_id is None else chosen_id
        destination_dir = self.output_dir / chosen_id
        if self.flat_output and output_path is None:
            destination_dir = self.output_dir.resolve()
            filename = chosen_id
        target_path = (pathlib.Path(output_path) if output_path is not None
                       else destination_dir / filename)
        target_dir = target_path.parent

        completion_key = f"document:{self.save_mode}:{self.force_extension or ''}"
        if document_id is not None or output_path is not None or self.flat_output or self.require_pdf or not self.allow_redirects:
            # Legacy keys remain valid only for the unchanged default policy.
            completion_key += (f":{download_id}:{target_path.name}"
                               f":pdf={self.require_pdf}:redirects={self.allow_redirects}")
        if document_id is not None:
            completion_key += f":id={chosen_id}"
        existing = verified_files(target_dir, completion_key) if self.skip_existing else []
        if existing:
            if self.log_downloads:
                event(logger, "documents", "activity", level=logging.DEBUG)
            return DocumentResult(full_url, download_id, str(existing[0]), None, None, skipped=True, document_id=chosen_id)

        status = None
        content_type = None
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            if self.log_downloads:
                event(logger, "documents", "activity", level=logging.DEBUG)
            headers = {"Accept": "application/pdf"} if self.require_pdf else {}
            with self.session.get(full_url, stream=True, timeout=self.timeout,
                                  headers=headers, allow_redirects=self.allow_redirects) as resp:
                status = resp.status_code
                resp.raise_for_status()
                if not 200 <= status < 300:
                    raise ValueError("Document response did not succeed.")
                content_type = resp.headers.get("Content-Type")
                if self.require_pdf and (status != 200 or
                        (content_type or "").split(";", 1)[0].strip().lower() != "application/pdf"):
                    raise ValueError("Document response is not an HTTP 200 PDF.")
                ext = _extension_from_content_type(content_type)
                if output_path is None:
                    target_path = _resolve_target_path(
                        target_dir=target_dir,
                        filename=filename,
                        ext=ext,
                        save_mode=self.save_mode,
                        force_extension=self.force_extension,
                    )
                if target_path.parent != target_dir or target_path.name in {"", ".", ".."}:
                    raise ValueError("Document filename must stay within its destination.")
                hasher = hashlib.sha256()
                with tempfile.TemporaryDirectory(prefix=".fyron-stage-", dir=target_dir) as staging:
                    size = 0
                    prefix = b""
                    with open(pathlib.Path(staging) / target_path.name, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                if self.require_pdf and len(prefix) < 5:
                                    prefix += chunk[:5 - len(prefix)]
                                    if len(prefix) == 5 and prefix != b"%PDF-":
                                        raise ValueError("Document has no PDF header.")
                                f.write(chunk)
                                hasher.update(chunk)
                                size += len(chunk)
                        f.flush()
                        os.fsync(f.fileno())
                    if self.require_pdf and prefix != b"%PDF-":
                        raise ValueError("Document has no PDF header.")
                    length = resp.headers.get("Content-Length")
                    if length is not None and not resp.headers.get("Content-Encoding") and size != int(length):
                        raise ValueError("Document response length mismatch.")
                    # Serialize publication within this client, including duplicate
                    # URLs submitted concurrently. Downloads themselves stay parallel.
                    with self._download_lock:
                        # Different IDs can still resolve to the same filename,
                        # e.g. "report" and "report.pdf" for PDF responses.
                        destinations = getattr(self._batch_state, "destinations", None)
                        if destinations is not None:
                            destination = str(target_path.resolve()).casefold()
                            owner = (download_id, chosen_id)
                            if destination in destinations and destinations[destination] != owner:
                                raise ValueError("Document destinations collide within this batch.")
                            destinations[destination] = owner
                        if self.skip_existing:
                            existing = verified_files(target_dir, completion_key)
                            if existing:
                                return DocumentResult(full_url, download_id, str(existing[0]),
                                                      status, content_type, skipped=True, document_id=chosen_id)
                        publish_files(staging, target_dir, completion_key,
                                      overwrite=not self.skip_existing,
                                      write_record=self.write_completion_record)
            return DocumentResult(
                full_url,
                download_id,
                str(target_path),
                status,
                content_type=content_type,
                sha256=hasher.hexdigest(),
                error=None,
                document_id=chosen_id,
            )
        except Exception as exc:
            response = getattr(exc, "response", None)
            if status is None and response is not None:
                status = getattr(response, "status_code", None)
            error_event(logger, "documents", exc)
            message = ("Existing output is unverified; review it before using skip_existing=False."
                       if isinstance(exc, FileExistsError) else safe_error(exc))
            return DocumentResult(full_url, download_id, str(target_path), status, content_type, None, message, document_id=chosen_id)

    def download_urls(
        self,
        urls: Iterable[str],
        results_csv: Optional[Union[str, pathlib.Path]] = None,
    ) -> pd.DataFrame:
        """Download a list of URLs and return results as a DataFrame."""
        url_list = list(urls)
        df = pd.DataFrame({"document_url": url_list})
        return self.download_from_dataframe(
            df=df,
            url_col="document_url",
            results_csv=results_csv,
        )

    @batch_report("documents")
    def download_from_dataframe(
        self,
        df: pd.DataFrame,
        url_col: str = "document_url",
        results_csv: Optional[Union[str, pathlib.Path]] = None,
        *,
        id_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """Download all URLs from a DataFrame column.

        Parameters
        ----------
        df:
            Input table with unique column names.
        url_col:
            Column containing document URLs.
        results_csv:
            Optional results CSV destination, separate from document paths.
        id_col:
            Optional column of unique filename-safe string or integer IDs.
            Omit to retain URL-hash naming. IDs are validated before requests.

        Returns
        -------
        pd.DataFrame
            Download outcomes with URL-hash download_id, effective document_id,
            actual path, status, hash, and controlled errors. Parallel results
            may arrive in completion order.
        """
        if url_col not in df.columns:
            raise ValueError(f"Column '{url_col}' not found in DataFrame.")
        if not df.columns.is_unique:
            raise ValueError("Document table columns must be unique.")
        urls = [self._resolve_url(url) for url in df[url_col].tolist()]
        ids = _document_ids(df, id_col)
        destinations = {}
        results: List[DocumentResult] = []
        if self.log_downloads:
            event(logger, "documents", "activity", level=logging.DEBUG)
        if self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futures = [ex.submit(self._download_batch_url, url, identifier, destinations)
                           for url, identifier in zip(urls, ids)]
                for fut in as_completed(futures):
                    result = fut.result()
                    results.append(result)
                    completed_task([result])
        else:
            for url, identifier in zip(urls, ids):
                result = self._download_batch_url(url, identifier, destinations)
                results.append(result)
                completed_task([result])
        out = pd.DataFrame([r.__dict__ for r in results], columns=[f.name for f in fields(DocumentResult)])
        if results_csv:
            report = pathlib.Path(results_csv).resolve()
            if any(report == pathlib.Path(path).resolve() for path in out["path"]):
                raise ValueError("Result report would overwrite a document.")
            pathlib.Path(results_csv).parent.mkdir(parents=True, exist_ok=True)
            out.to_csv(results_csv, index=False)
        return out

    def _download_batch_url(self, url, identifier, destinations):
        self._batch_state.destinations = destinations
        try:
            return self.download_url(url, document_id=identifier)
        finally:
            del self._batch_state.destinations

    def download_from_df(
        self,
        df: pd.DataFrame,
        url_col: str = "document_url",
        results_csv: Optional[Union[str, pathlib.Path]] = None,
        *,
        id_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """Short alias for download_from_dataframe.

        Parameters
        ----------
        df:
            Input table with unique column names.
        url_col:
            Column containing document URLs.
        results_csv:
            Optional results CSV destination, separate from document paths.
        id_col:
            Optional column of unique filename-safe string or integer IDs.
            Omit to retain URL-hash naming. IDs are validated before requests.

        Returns
        -------
        pd.DataFrame
            Download outcomes with URL-hash download_id, effective document_id,
            actual path, status, hash, and controlled errors. Parallel results
            may arrive in completion order.
        """
        return self.download_from_dataframe(df=df, url_col=url_col, results_csv=results_csv, id_col=id_col)

    def _resolve_url(self, url: str) -> str:
        """Resolve relative URLs against base_url."""
        return _resolve_document_url(url, self.base_url)


def _validate_document_id(value) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, numbers.Integral)):
        raise ValueError("Document IDs must be strings or integers.")
    value = str(value)
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value)
            or value.endswith(".")
            or value.split(".", 1)[0].upper() in {
                "CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
                *[f"LPT{i}" for i in range(1, 10)],
            }):
        raise ValueError("Document ID must be a portable filename component of 1–128 ASCII characters.")
    return value


def _document_ids(df: pd.DataFrame, id_col: Optional[str]) -> list:
    if id_col is None:
        return [None] * len(df)
    if not df.columns.is_unique or id_col not in df.columns:
        raise ValueError("Document table requires a unique configured ID column.")
    ids = [_validate_document_id(value) for value in df[id_col].tolist()]
    if len({value.casefold() for value in ids}) != len(ids):
        raise ValueError("Document IDs must be unique, including case-insensitive comparisons.")
    return ids


def _resolve_document_url(url: str, base_url: Optional[str] = None) -> str:
    if not isinstance(url, str) or not url.strip() or any(c.isspace() for c in url):
        raise ValueError("Document URL must be a nonempty string without whitespace.")
    try:
        if not urlsplit(url).scheme:
            if not base_url:
                raise ValueError
            url = base_url.rstrip("/") + "/" + url.lstrip("/")
        parsed = urlsplit(url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username is not None or parsed.password is not None):
            raise ValueError
        parsed.port  # Validate the port without including the URL in errors.
    except ValueError:
        raise ValueError("Document URL requires HTTP(S), a host, and no embedded credentials.") from None
    return url


def _filename_from_url(url: str) -> str:
    """Derive a filename from a URL path."""
    name = pathlib.Path(urlsplit(url).path).name
    return name if name not in {"", ".", ".."} else "document"


def _extension_from_content_type(content_type: Optional[str]) -> Optional[str]:
    """Map content-type to a file extension, if known."""
    if not content_type:
        return None
    ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
    return ext


def _resolve_target_path(
    target_dir: pathlib.Path,
    filename: str,
    ext: Optional[str],
    save_mode: str,
    force_extension: Optional[str],
) -> pathlib.Path:
    """Determine the final target path based on save mode and extension."""
    # If user forces an extension, always use that.
    if force_extension:
        ext = force_extension if force_extension.startswith(".") else f".{force_extension}"
        return target_dir / (filename + ext)

    # Auto mode: prefer content-type extension if present.
    if save_mode == "auto":
        if ext and not filename.endswith(ext):
            return target_dir / (filename + ext)
        return target_dir / filename

    # Force to a given type.
    if save_mode in {"txt", "pdf"}:
        forced = f".{save_mode}"
        return target_dir / (filename + forced)

    # Default fallback
    return target_dir / filename
