"""FHIR REST client with simple multiprocessing helpers."""

from __future__ import annotations

from .._diagnostics import event, safe_error, batch_report, error_event, completed_task
from .._http import guard_redirects

import logging
import multiprocessing as mp
import os
import re
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth, _basic_auth_str
from requests.adapters import HTTPAdapter
from urllib.parse import quote, urlparse, urljoin, urldefrag
from urllib3.util.retry import Retry
from tqdm import tqdm

from .auth import Auth, TokenAuth
from ._client_credentials import _ClientCredentialsAuth
from ._device_auth import _DeviceAuth
from ._workers import PipeAuth as _WorkerAuth
from .types import FHIRObj
from ._workers import managed_pool, monitored_results, positive_timeout, stage, worker_auth as current_worker_auth

ProcessFunc = Callable[[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]
logger = logging.getLogger(__name__)
_FHIRPATH_COMPILED: Optional[List[Tuple[str, Any]]] = None
_WORKER_SESSION = None


class FHIRRequestError(RuntimeError):
    """Raised when a FHIR request fails or returns invalid JSON."""


@dataclass
class QueryJob:
    resource_type: str
    params: Dict[str, Any]
    max_pages: int
    ordinal: int = 0


@dataclass(frozen=True)
class RepeatedParam:
    """Represent repeated FHIR search parameters with the same key."""

    values: Tuple[Any, ...]


@dataclass
class FHIRWriteResult:
    """Summary of a FHIR write request."""

    status_code: int
    location: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    response_json: Optional[Dict[str, Any]]


def _join_url(base: str, path: str) -> str:
    """Join a base URL and a resource path with a single slash."""
    if base.endswith("/"):
        base = base[:-1]
    if path.startswith("/"):
        path = path[1:]
    return f"{base}/{path}"


def _resolve_next_url(base_url: str, next_link: str) -> str:
    """Resolve pagination relative to the response, without crossing origins."""
    resolved = urldefrag(urljoin(base_url, next_link))[0]
    try:
        source, target = urlparse(base_url), urlparse(resolved)
        def origin(value):
            return (value.scheme.lower(), value.hostname,
                    value.port or (443 if value.scheme == "https" else 80))
        valid = (target.scheme in {"http", "https"}
                 and not target.username and not target.password
                 and origin(source) == origin(target))
    except ValueError:
        valid = False
    if not valid:
        raise FHIRRequestError("Unsafe pagination destination (unexpected_response).")
    return resolved


def _validate_max_pages(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < -1:
        raise ValueError("max_pages must be -1 or a nonnegative integer.")


def _flatten_record(resource: Any, out: Dict[str, Any], prefix: str, sep: str) -> None:
    """Recursively flatten a resource into a flat dictionary."""
    if isinstance(resource, dict):
        for key, value in resource.items():
            _flatten_record(value, out, f"{prefix}{sep}{key}", sep)
    elif isinstance(resource, list):
        for idx, value in enumerate(resource):
            _flatten_record(value, out, f"{prefix}{sep}{idx}", sep)
    else:
        out[prefix.lstrip(sep)] = resource


def _freeze_params(params: Dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    """Freeze params into a hashable, stable structure."""
    frozen: List[Tuple[str, Any]] = []
    for key, value in sorted(params.items()):
        if isinstance(value, dict):
            frozen.append((key, tuple(sorted(value.items()))))
        elif isinstance(value, RepeatedParam):
            frozen.append((key, tuple(value.values)))
        elif isinstance(value, (list, tuple, set)):
            frozen.append((key, tuple(value)))
        else:
            frozen.append((key, value))
    return tuple(frozen)


def _params_to_query_sequence(params: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """Convert params dict to a list of (key, value) for requests.

    List/tuple values are joined comma-separated for the same param so that
    e.g. {"code": ["a", "b"]} becomes [("code", "a,b")],
    producing query strings like ?code=a,b.
    """
    out: List[Tuple[str, Any]] = []
    for key, value in params.items():
        if isinstance(value, RepeatedParam):
            for item in value.values:
                out.append((key, item))
        elif isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            out.append((key, ",".join(str(v) for v in value)))
        else:
            out.append((key, value))
    return out


def _quote_query_value(s: str) -> str:
    """Encode a string for use in a query parameter.

    If the value looks like a URL (starts with http:// or https://), it is
    left as-is (no encoding). Otherwise, the string is encoded while
    preserving any existing %XX sequences. Leading/trailing quote characters
    are stripped so the request URL never contains quotes.
    """
    s = str(s).strip().strip("'\"").strip()
    if s.lower().startswith(("http://", "https://")):
        return s
    parts = re.split(r"(%[0-9A-Fa-f]{2})", s)
    return "".join(
        part if len(part) == 3 and part.startswith("%") else quote(part, safe="")
        for part in parts
    )


def _build_query_string(query_params: List[Tuple[str, Any]]) -> str:
    """Build a query string from (key, value) pairs with single encoding."""
    return "&".join(
        f"{_quote_query_value(str(k))}={_quote_query_value(str(v))}"
        for k, v in query_params
    )


def _format_fhir_boundary(value: pd.Timestamp) -> str:
    """Format a pandas timestamp as a FHIR date/dateTime search boundary."""
    if value.time() == pd.Timestamp(value.date()).time():
        return value.date().isoformat()
    return value.isoformat()


def build_partition_params(
    params: Optional[Dict[str, Any]],
    partition_param: str,
    start: Union[str, pd.Timestamp],
    end: Union[str, pd.Timestamp],
    *,
    frequency: str = "YS",
    window_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Build FHIR search parameter sets split by a date/dateTime range.

    The partition parameter is represented as repeated FHIR search params,
    e.g. ``recorded-date=ge2020-01-01&recorded-date=lt2021-01-01``. Ordinary
    list values in other parameters keep Fyron's existing comma-separated
    behavior for code searches such as ``code=a,b``.
    """
    if not partition_param:
        raise ValueError("partition_param is required.")
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if pd.isna(start_ts) or pd.isna(end_ts):
        raise ValueError("start and end must be valid dates.")
    if start_ts >= end_ts:
        raise ValueError("start must be earlier than end.")
    if window_days is not None:
        if window_days <= 0:
            raise ValueError("window_days must be positive.")
        boundaries = list(pd.date_range(start=start_ts, end=end_ts, freq=f"{int(window_days)}D"))
    else:
        if not frequency:
            raise ValueError("frequency is required when window_days is not set.")
        boundaries = list(pd.date_range(start=start_ts, end=end_ts, freq=frequency))
    if not boundaries or boundaries[0] != start_ts:
        boundaries.insert(0, start_ts)
    if boundaries[-1] != end_ts:
        boundaries.append(end_ts)

    base_params = dict(params or {})
    if partition_param in base_params:
        raise ValueError(
            f"params already contains '{partition_param}'. Use start/end partition arguments instead."
        )

    partitions: List[Dict[str, Any]] = []
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        partition = dict(base_params)
        partition[partition_param] = RepeatedParam(
            (f"ge{_format_fhir_boundary(left)}", f"lt{_format_fhir_boundary(right)}")
        )
        partitions.append(partition)
    return partitions


def _partition_metadata(
    param_list: Sequence[Dict[str, Any]],
    partition_param: str,
) -> List[Dict[str, Any]]:
    """Build per-partition metadata columns for DataFrame traceability."""
    metadata: List[Dict[str, Any]] = []
    for params in param_list:
        value = params.get(partition_param)
        if isinstance(value, RepeatedParam) and len(value.values) >= 2:
            start_value = str(value.values[0]).removeprefix("ge")
            end_value = str(value.values[1]).removeprefix("lt")
        else:
            start_value = None
            end_value = None
        metadata.append(
            {
                "_fyron_partition_param": partition_param,
                "_fyron_partition_start": start_value,
                "_fyron_partition_end": end_value,
            }
        )
    return metadata


def _deduplicate_result(
    result: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
    deduplicate_by: Optional[Union[str, Sequence[str]]],
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Drop duplicate rows from DataFrame outputs when requested."""
    if deduplicate_by is None:
        return result
    subset = [deduplicate_by] if isinstance(deduplicate_by, str) else list(deduplicate_by)
    if isinstance(result, pd.DataFrame):
        available = [col for col in subset if col in result.columns]
        return result.drop_duplicates(subset=available) if available else result
    deduped: Dict[str, pd.DataFrame] = {}
    for key, frame in result.items():
        available = [col for col in subset if col in frame.columns]
        deduped[key] = frame.drop_duplicates(subset=available) if available else frame
    return deduped


class ResponseCache:
    """Small in-memory TTL cache for GET responses."""

    def __init__(self, ttl_seconds: int = 300, max_entries: int = 1000) -> None:
        self.ttl_seconds = max(0, int(ttl_seconds))
        self.max_entries = max(0, int(max_entries))
        self._store: "OrderedDict[Tuple[Any, ...], Tuple[float, Tuple[Dict[str, Any], str, int, float]]]" = (
            OrderedDict()
        )

    def _prune(self) -> None:
        while self.max_entries and len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def get(self, key: Tuple[Any, ...], now: float) -> Optional[Tuple[Dict[str, Any], str, int, float]]:
        if self.ttl_seconds <= 0 or self.max_entries <= 0:
            return None
        entry = self._store.get(key)
        if entry is None:
            return None
        inserted_at, payload = entry
        if (now - inserted_at) > self.ttl_seconds:
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return payload

    def set(self, key: Tuple[Any, ...], payload: Tuple[Dict[str, Any], str, int, float], now: float) -> None:
        if self.ttl_seconds <= 0 or self.max_entries <= 0:
            return
        self._store[key] = (now, payload)
        self._store.move_to_end(key)
        self._prune()


def flatten_data(
    bundle: Dict[str, Any] | FHIRObj, col_sep: str = "_"
) -> Dict[str, List[Dict[str, Any]]]:
    """Flatten bundle entries into row dictionaries by resourceType."""
    if isinstance(bundle, FHIRObj):
        bundle = bundle.to_dict()
    records: Dict[str, List[Dict[str, Any]]] = {}
    for entry in bundle.get("entry", []) or []:
        resource = entry.get("resource") or {}
        resource_type = resource.get("resourceType", "Resource")
        records.setdefault(resource_type, [])
        base: Dict[str, Any] = {}
        _flatten_record(resource, base, "", col_sep)
        records[resource_type].append({k: v for k, v in base.items() if v is not None})
    return records


def _bundle_entry_count(bundle: Dict[str, Any] | FHIRObj) -> int:
    entries = bundle.entry if isinstance(bundle, FHIRObj) else bundle.get("entry", [])
    return len(entries or [])


def _processed_row_count(processed: Iterable[Dict[str, List[Dict[str, Any]]]]) -> int:
    total = 0
    for bundle_output in processed:
        for rows in bundle_output.values():
            total += len(rows)
    return total


def _format_fancy_summary(
    bundles: int, entries: int, rows: int, mode: str, color: bool = True
) -> str:
    label = "FHIR Summary"
    if color:
        label = "\033[1;36mFHIR Summary\033[0m"
    line = "—" * 58
    if color:
        line = f"\033[2m{line}\033[0m"
    return (
        f"\n{line}\n"
        f"  {label}\n"
        f"  bundles: {bundles:<8}  entries: {entries:<8}  rows: {rows:<8}\n"
        f"  mode: {mode}\n"
        f"{line}"
    )


def _compile_fhir_paths(fhir_paths: Sequence[Union[str, Tuple[str, str]]]) -> List[Tuple[str, Any]]:
    """Compile FHIRPath expressions into callable functions."""
    try:
        import fhirpathpy  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency should be installed with Fyron
        raise ImportError(
            "FHIRPath support requires `fhirpathpy`, which is a Fyron package dependency. "
            "Reinstall or update Fyron to restore fhir_paths support."
        ) from None
    compiled: List[Tuple[str, Any]] = []
    for path in fhir_paths:
        name, expr = (path, path) if isinstance(path, str) else path
        compiled.append((name, fhirpathpy.compile(path=expr)))
    return compiled


def _parse_fhir_path_worker(bundle: Dict[str, Any] | FHIRObj) -> Dict[str, List[Dict[str, Any]]]:
    """Worker-friendly wrapper for parsing FHIRPath using global compiled paths."""
    if _FHIRPATH_COMPILED is None:
        raise RuntimeError("FHIRPath worker not initialized.")
    return parse_fhir_path(bundle, _FHIRPATH_COMPILED)


def _init_fhirpath_worker(compiled: List[Tuple[str, Any]]) -> None:
    """Initializer to set compiled FHIRPath expressions in worker processes."""
    global _FHIRPATH_COMPILED
    _FHIRPATH_COMPILED = compiled


def parse_fhir_path(
    bundle: Dict[str, Any] | FHIRObj,
    compiled_fhir_paths: List[Tuple[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Extract fields from bundle entries using compiled FHIRPath expressions."""
    if isinstance(bundle, FHIRObj):
        bundle = bundle.to_dict()
    records: Dict[str, List[Dict[str, Any]]] = {}
    for entry in bundle.get("entry", []) or []:
        resource = entry.get("resource") or {}
        resource_type = resource.get("resourceType", "Resource")
        records.setdefault(resource_type, [])
        base: Dict[str, Any] = {}
        for name, compiled in compiled_fhir_paths:
            result = compiled(resource=resource)
            if isinstance(result, list):
                if len(result) == 0:
                    value = None
                elif len(result) == 1:
                    value = result[0]
                else:
                    value = result
            else:
                value = result
            if name not in base or base[name] is None:
                base[name] = value
        records[resource_type].append({k: v for k, v in base.items() if v is not None})
    return records


def _request_json(
    session: requests.Session,
    url: str,
    params: Dict[str, Any],
    timeout: int,
    log: Optional[logging.Logger],
    cache: Optional[ResponseCache] = None,
    log_request_url: bool = False,
) -> Tuple[Dict[str, Any], str, int, float]:
    """GET a URL, validate response, parse JSON, and return payload plus metadata."""
    start = time.perf_counter()
    query_params = _params_to_query_sequence(params)
    qs = _build_query_string(query_params) if query_params else ""
    full_url = url + ("?" + qs if qs else "")
    if log_request_url:
        event(log or logging.getLogger("fyron.fhir.rest"), "fhir", "activity", level=logging.DEBUG)
    if cache is not None:
        cache_key = (
            url,
            _freeze_params(params),
            id(session.auth) if hasattr(session, "auth") else None,
            session.headers.get("Authorization"),
            session.headers.get("Accept"),
        )
        cached = cache.get(cache_key, start)
        if cached is not None:
            if log is not None:
                event(log, "fhir", "activity", level=logging.DEBUG)
            data, response_url, status_code, _ = cached
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return data, response_url, status_code, elapsed_ms
    try:
        guard_redirects(session)
        response = session.get(full_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        if log is not None:
            error_event(log, "fhir", exc)
        raise FHIRRequestError(safe_error(exc)) from None

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    if log is not None:
        event(log, "fhir", "activity", level=logging.DEBUG)
    try:
        data = response.json()
    except ValueError as exc:
        if log is not None:
            error_event(log, "fhir", exc)
        raise FHIRRequestError("Invalid JSON response (unexpected_response).") from None
    if cache is not None:
        cache.set(cache_key, (data, response.url, response.status_code, elapsed_ms), time.perf_counter())
    return data, response.url, response.status_code, elapsed_ms


def _write_json_request(
    session: requests.Session,
    method: str,
    url: str,
    payload: Dict[str, Any],
    timeout: int,
    log: Optional[logging.Logger],
) -> FHIRWriteResult:
    """Send a FHIR write request and return compact metadata."""
    try:
        guard_redirects(session)
        response = session.request(method, url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        if log is not None:
            error_event(log, "fhir", exc)
        raise FHIRRequestError(safe_error(exc)) from None

    parsed: Optional[Dict[str, Any]]
    try:
        parsed = response.json()
    except ValueError:
        parsed = None
    response_resource_type = parsed.get("resourceType") if isinstance(parsed, dict) else payload.get("resourceType")
    response_resource_id = parsed.get("id") if isinstance(parsed, dict) else payload.get("id")
    return FHIRWriteResult(
        status_code=response.status_code,
        location=response.headers.get("Location") or response.headers.get("Content-Location"),
        resource_type=response_resource_type,
        resource_id=response_resource_id,
        response_json=parsed,
    )


def _ensure_bundle_payload(payload: Any, response_url: str) -> Dict[str, Any]:
    """Return a plain FHIR Bundle dict for search pagination.

    FHIR servers normally return Bundle resources for search endpoints, but
    some endpoints may return a single resource or an empty/non-dict payload.
    Keep pagination internals on plain dictionaries so optional ``FHIRObj``
    wrapping cannot break link handling.
    """
    if isinstance(payload, FHIRObj):
        payload = payload.to_dict()
    if not isinstance(payload, dict):
        raise FHIRRequestError(
            "FHIR search response must be a JSON object (unexpected_response)."
        )
    resource_type = payload.get("resourceType")
    if not isinstance(resource_type, str) or not resource_type or resource_type == "OperationOutcome":
        raise FHIRRequestError("FHIR response is not a resource result (unexpected_response).")
    if resource_type != "Bundle":
        return {
            "resourceType": "Bundle",
            "type": "read",
            "total": 1,
            "entry": [{"fullUrl": response_url, "resource": payload}],
        }
    return payload


def _bundle_next_link(bundle: Dict[str, Any] | FHIRObj) -> Optional[str]:
    """Extract the pagination next link without assuming dict-only bundles."""
    if isinstance(bundle, FHIRObj):
        links = bundle.link or []
    else:
        links = bundle.get("link", []) or []
    for link in links:
        if isinstance(link, FHIRObj):
            relation = link.relation
            url = link.url
        elif isinstance(link, dict):
            relation = link.get("relation")
            url = link.get("url")
        else:
            continue
        if relation == "next" and url:
            return str(url)
    return None


def _resource_type_and_id(resource: Dict[str, Any], resource_type: Optional[str], resource_id: Optional[str] = None) -> Tuple[str, Optional[str]]:
    resolved_type = resource_type or resource.get("resourceType")
    if not resolved_type:
        raise ValueError("resource_type is required or resource must contain resourceType")
    return str(resolved_type), resource_id or resource.get("id")


def _close_worker_session():
    global _WORKER_SESSION
    if _WORKER_SESSION is not None:
        _WORKER_SESSION.close()
        _WORKER_SESSION = None


def _worker_fetch_job(args):
    return args[1].ordinal, _worker_fetch_bundles(args)


def _worker_fetch_bundles(
    args: Tuple[
        str,
        QueryJob,
        Dict[str, str],
        int,
        Dict[str, Any],
        bool,
        bool,
        str,
        Optional[str],
        Optional[str],
        Optional[str],
        int,
        int,
        Optional[_WorkerAuth],
        Retry,
    ]
) -> List[Dict[str, Any]]:
    """Worker helper for parallel bundle fetching."""
    worker_auth = current_worker_auth() or (args[13] if len(args) > 13 else None)
    (
        base_url,
        job,
        headers,
        timeout,
        request_params,
        log_requests,
        log_request_urls,
        auth_mode,
        auth_url,
        refresh_url,
        token_auth_method,
        cache_ttl_seconds,
        cache_max_entries,
    ) = args[:13]
    log = logger if log_requests else None
    global _WORKER_SESSION
    reuse = mp.current_process().name != "MainProcess"
    fresh = not reuse or _WORKER_SESSION is None
    session = requests.Session() if fresh else _WORKER_SESSION
    if reuse:
        _WORKER_SESSION = session
    if fresh and len(args) > 14:
        adapter = HTTPAdapter(max_retries=args[14])
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    cache = ResponseCache(ttl_seconds=cache_ttl_seconds, max_entries=cache_max_entries)
    if headers:
        session.headers.update(headers)
    if worker_auth is not None:
        session.auth = worker_auth
    elif auth_mode == "basic":
        username = os.environ.get("FHIR_USER")
        password = os.environ.get("FHIR_PASSWORD")
        if username and password:
            session.auth = HTTPBasicAuth(username, password)
    elif auth_mode == "token_env" and fresh:
        username = os.environ.get("FHIR_USER")
        password = os.environ.get("FHIR_PASSWORD")
        if username and password and auth_url:
            session.auth = TokenAuth(
                username=username,
                password=password,
                auth_url=auth_url,
                refresh_url=refresh_url,
                session=session,
                auth_method=token_auth_method or "basic",
            )
    bundles: List[Dict[str, Any]] = []
    request_url = _join_url(base_url, job.resource_type)
    params = {**request_params, **job.params}
    pages = 0
    seen_pages = set()
    try:
        _validate_max_pages(job.max_pages)
        if job.max_pages == 0:
            return []
        while True:
            stage("http")
            bundle, response_url, _, _ = _request_json(
                session=session,
                url=request_url,
                params=params,
                timeout=timeout,
                log=log,
                cache=cache,
                log_request_url=log_request_urls,
            )
            if response_url in seen_pages:
                raise FHIRRequestError("Repeated pagination page (unexpected_response).")
            seen_pages.add(response_url)
            bundle = _ensure_bundle_payload(bundle, response_url)
            bundles.append(bundle)
            pages += 1
            if 0 < job.max_pages <= pages:
                break
            next_link = _bundle_next_link(bundle)
            if not next_link:
                break
            request_url = _resolve_next_url(response_url, next_link)
            if request_url in seen_pages:
                raise FHIRRequestError("Repeated pagination page (unexpected_response).")
            params = {}
        return bundles
    finally:
        if not reuse:
            session.close()


def _can_worker_use_token_env(auth_url: Optional[str]) -> bool:
    """Return whether worker processes can create refreshable token auth."""
    return bool(auth_url and os.environ.get("FHIR_USER") and os.environ.get("FHIR_PASSWORD"))


class FHIRRestClient:
    """Simple FHIR REST client focused on bundle retrieval and DataFrame conversion.

    Parameters
    ----------
    base_url:
        Base FHIR server URL (e.g., https://example.org/fhir).
    auth_url:
        Token endpoint for password-based auth. If omitted, uses FHIR_AUTH_URL env.
    auth:
        Optional Auth or requests.Session instance to use.
    num_processes:
        Process count for multiprocessing (>=1).
    request_timeout:
        Per-request timeout in seconds.
    worker_auth_timeout:
        Positive worker token-wait timeout in seconds (default 120).
    parallel_job_timeout:
        Positive execution deadline per parallel query in seconds (default 300).
        Excludes queue time; None disables the overall job deadline.
    request_params:
        Default query params merged into every request.
    bearer_token:
        Token used for parallel requests (or set FHIR_TOKEN env).
    log_requests:
        If True, logs request timing and summaries.
    log_request_urls:
        If True, prints each request URL (with query string) to the console.
    token_auth_method:
        Token auth method for password-based token endpoints ("basic" or "post").
    cache_ttl_seconds:
        In-memory cache TTL for GET responses.
    cache_max_entries:
        Maximum number of cached GET responses.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        auth: Optional[Union[Auth, requests.Session]] = None,
        num_processes: int = 4,
        request_timeout: int = 30,
        request_params: Optional[Dict[str, Any]] = None,
        bearer_token: Optional[str] = None,
        log_requests: bool = False,
        log_request_urls: bool = False,
        extra_headers: Optional[Dict[str, str]] = None,
        retries: Optional[Retry] = None,
        return_fhir_obj: bool = False,
        token_auth_method: Optional[str] = None,
        cache_ttl_seconds: int = 300,
        cache_max_entries: int = 1000,
        *,
        worker_auth_timeout: float = 120,
        parallel_job_timeout: Optional[float] = 300,
    ) -> None:
        """Initialize a FHIR REST client."""
        self.base_url = base_url or os.environ.get("FHIR_BASE_URL")
        if not self.base_url:
            raise ValueError("base_url is required (or set FHIR_BASE_URL).")
        if "://" not in self.base_url:
            # Default to https when scheme is missing (common config mistake).
            self.base_url = f"https://{self.base_url}"
        self.auth_url = auth_url or os.environ.get("FHIR_AUTH_URL")
        self.request_timeout = positive_timeout(request_timeout, "request_timeout")
        self.worker_auth_timeout = positive_timeout(worker_auth_timeout, "worker_auth_timeout")
        self.parallel_job_timeout = None if parallel_job_timeout is None else positive_timeout(parallel_job_timeout, "parallel_job_timeout")
        self.request_params = request_params or {}
        self.num_processes = max(1, num_processes)
        self._close_session_on_exit = False
        self.log_requests = log_requests
        self.log_request_urls = log_request_urls
        self.extra_headers = extra_headers or {}
        self.return_fhir_obj = return_fhir_obj
        self._token_auth_method = (token_auth_method or "basic").lower()
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache_max_entries = cache_max_entries
        self._response_cache = ResponseCache(
            ttl_seconds=self._cache_ttl_seconds,
            max_entries=self._cache_max_entries,
        )

        if isinstance(auth, Auth):
            self.session = auth.session
        elif isinstance(auth, requests.Session):
            self.session = auth
        else:
            self._close_session_on_exit = True
            if self.auth_url:
                self.session = Auth(
                    auth_url=self.auth_url,
                    refresh_url=os.environ.get("FHIR_REFRESH_URL"),
                    auth_method="env",
                    token_auth_method=self._token_auth_method,
                ).session
            else:
                self.session = requests.Session()

        if self.extra_headers:
            self.session.headers.update(self.extra_headers)

        if retries is None:
            retries = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[502, 503, 504],
                allowed_methods=["GET"],
                raise_on_status=False,
            )
        adapter = HTTPAdapter(max_retries=retries)
        self._retries = retries
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self._bearer_token = bearer_token or os.environ.get("FHIR_TOKEN")
        if self._bearer_token and self.session.auth is None:
            self.session.headers["Authorization"] = f"Bearer {self._bearer_token}"
        event(logger, "fhir", "activity", level=logging.DEBUG)

    def __enter__(self) -> "FHIRRestClient":
        """Return self for context manager usage."""
        return self

    def close(self) -> None:
        """Close the underlying session if owned."""
        if self._close_session_on_exit:
            self.session.close()

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        """Close the session on context manager exit."""
        self.close()

    def fetch_bundles(
        self,
        resource_type: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = -1,
        show_progress: bool = True,
    ) -> Generator[Dict[str, Any], None, int]:
        """Fetch bundles for a resource with pagination.

        Parameters
        ----------
        resource_type:
            FHIR resource type (e.g., Patient, Observation).
        params:
            Query parameters for the search.
        max_pages:
            Maximum number of pages to fetch (-1 for all).
        show_progress:
            Whether to show a tqdm progress bar.

        Yields
        ------
        dict
            FHIR Bundle JSON objects.
        """
        _validate_max_pages(max_pages)
        if max_pages == 0:
            return 0
        request_url = _join_url(self.base_url, resource_type)
        merged_params = {**self.request_params, **(params or {})}
        pages = 0
        total_requests = 0
        seen_pages = set()
        progress = tqdm(
            desc=f"Query ({resource_type})",
            disable=not show_progress,
            total=None if max_pages == -1 else max_pages,
        )
        try:
            while True:
                bundle, response_url, _, _ = _request_json(
                    session=self.session,
                    url=request_url,
                    params=merged_params,
                    timeout=self.request_timeout,
                    log=logger if self.log_requests else None,
                    cache=self._response_cache,
                    log_request_url=self.log_request_urls,
                )
                total_requests += 1
                if response_url in seen_pages:
                    raise FHIRRequestError("Repeated pagination page (unexpected_response).")
                seen_pages.add(response_url)
                bundle = _ensure_bundle_payload(bundle, response_url)
                next_link = _bundle_next_link(bundle)
                if self.return_fhir_obj:
                    bundle = FHIRObj(**bundle)
                yield bundle
                pages += 1
                progress.update(1)
                if max_pages != -1 and pages >= max_pages:
                    break
                if not next_link:
                    break
                request_url = _resolve_next_url(response_url, next_link)
                if request_url in seen_pages:
                    raise FHIRRequestError("Repeated pagination page (unexpected_response).")
                merged_params = {}
        finally:
            progress.close()
        if self.log_requests:
            event(logger, "fhir", "activity", level=logging.DEBUG)
        return pages

    def fetch_bundles_parallel(
        self,
        resource_type: str,
        param_list: Sequence[Dict[str, Any]],
        max_pages: int = -1,
        show_progress: bool = True,
    ) -> Generator[Dict[str, Any], None, int]:
        """Fetch bundles for independent searches in completion order.

        Parameters
        ----------
        resource_type:
            FHIR resource type.
        param_list:
            One parameter dictionary per query.
        max_pages:
            Per-query page limit, or -1 for all pages.
        show_progress:
            Show completed query progress.

        Yields
        ------
        dict
            Bundles; results already yielded are incomplete if iteration fails.
        """
        count = 0
        for _, bundles in self._fetch_parallel_jobs(resource_type, param_list, max_pages, show_progress):
            for bundle in bundles:
                yield bundle
                count += 1
        return count

    def _fetch_parallel_jobs(
        self,
        resource_type: str,
        param_list: Sequence[Dict[str, Any]],
        max_pages: int = -1,
        show_progress: bool = True,
    ) -> Generator[Dict[str, Any], None, int]:
        """Fetch bundles in parallel for multiple parameter sets.

        Parameters
        ----------
        resource_type:
            FHIR resource type.
        param_list:
            List of query param dicts; each runs as a separate job.
        max_pages:
            Maximum pages per job (-1 for all).
        show_progress:
            Whether to show a tqdm progress bar.
        """
        _validate_max_pages(max_pages)
        if max_pages == 0:
            return 0
        headers: Dict[str, str] = dict(self.session.headers)
        auth_mode = "none"
        token: Optional[str] = None
        if hasattr(self.session, "auth"):
            auth = self.session.auth
            if isinstance(auth, HTTPBasicAuth):
                auth_mode = "explicit_basic"
                headers["Authorization"] = _basic_auth_str(auth.username, auth.password)
            elif isinstance(auth, (_DeviceAuth, _ClientCredentialsAuth)):
                auth_mode = "device_code"
                headers.pop("Authorization", None)
            elif isinstance(auth, TokenAuth):
                if _can_worker_use_token_env(self.auth_url):
                    # Let each worker create TokenAuth so long-running parallel
                    # jobs can refresh or re-authenticate instead of freezing a
                    # parent bearer token into process-local request headers.
                    auth_mode = "token_env"
                    headers.pop("Authorization", None)
                else:
                    # Fall back to the live token when worker credentials are
                    # not available. This supports explicit static-token use,
                    # but cannot refresh after expiry.
                    token = getattr(auth, "token", None)
                    if token:
                        auth_mode = "bearer"
                        headers["Authorization"] = f"Bearer {token}"
                    else:
                        auth_mode = "token_env"
            elif auth is not None:
                # Use token auth in worker (re-auth from env) instead of reusing parent token.
                auth_mode = "token_env"
        # Fall back to explicit bearer token (param/env) only if we didn't use auth.
        if auth_mode == "none":
            token = self._bearer_token
            if token and not _can_worker_use_token_env(self.auth_url):
                auth_mode = "bearer"
                headers["Authorization"] = f"Bearer {token}"
            elif _can_worker_use_token_env(self.auth_url):
                auth_mode = "token_env"
                headers.pop("Authorization", None)
        if auth_mode == "none" and not headers:
            raise ValueError(
                "Parallel fetch requires token or basic auth. "
                "Configure Auth(auth_type='basic'|'token') or pass bearer_token."
            )
        jobs = [QueryJob(resource_type, params, max_pages, i) for i, params in enumerate(param_list)]
        if self.log_requests:
            event(logger, "fhir", "activity", level=logging.DEBUG)
        progress = tqdm(
            total=len(jobs),
            desc=f"Query Parallel ({resource_type})",
            disable=not show_progress,
        )
        bundles_count = 0
        coordinated_auth = self.session.auth if isinstance(self.session.auth, (_DeviceAuth, _ClientCredentialsAuth)) else None
        with progress, managed_pool(coordinated_auth, self.num_processes, self.worker_auth_timeout) as (pool, events):
            for ordinal, bundles in monitored_results(
                pool, events,
                _worker_fetch_job,
                [
                    (
                        self.base_url,
                        job,
                        headers,
                        self.request_timeout,
                        self.request_params,
                        self.log_requests,
                        self.log_request_urls,
                        auth_mode,
                        self.auth_url,
                        os.environ.get("FHIR_REFRESH_URL"),
                        self._token_auth_method,
                        self._cache_ttl_seconds,
                        self._cache_max_entries,
                        None,
                        self._retries,
                    )
                    for job in jobs
                ],
                self.parallel_job_timeout,
            ):
                yield ordinal, bundles
                bundles_count += len(bundles)
                progress.update(1)
                completed_task([])
        progress.close()
        if self.log_requests:
            event(logger, "fhir", "activity", level=logging.DEBUG)
        return bundles_count

    def _query_jobs(self, resource_type, param_list, max_pages, parallel, show_progress):
        """Collect ordered jobs without exposing query values in diagnostics."""
        _validate_max_pages(max_pages)
        jobs = [[] for _ in param_list]
        if parallel and self.num_processes > 1 and max_pages != 0:
            received = set()
            for ordinal, bundles in self._fetch_parallel_jobs(
                resource_type=resource_type, param_list=param_list,
                max_pages=max_pages, show_progress=show_progress
            ):
                if ordinal in received or not 0 <= ordinal < len(jobs):
                    raise FHIRRequestError("Invalid worker result association.")
                received.add(ordinal)
                jobs[ordinal] = bundles
            if len(received) != len(jobs):
                raise FHIRRequestError("Parallel results are incomplete.")
        else:
            progress = tqdm(total=len(param_list), desc=f"Query Sequential ({resource_type})",
                            unit="query", disable=not show_progress)
            try:
                for ordinal, params in enumerate(param_list):
                    jobs[ordinal] = list(self.fetch_bundles(
                        resource_type=resource_type, params=params, max_pages=max_pages, show_progress=False))
                    progress.update(1)
                    completed_task([])
            finally:
                progress.close()
        rows = []
        for ordinal, bundles in enumerate(jobs):
            limited = bool(bundles and _bundle_next_link(bundles[-1]))
            exhausted = max_pages != 0 and not limited
            count = sum(_bundle_entry_count(bundle) for bundle in bundles)
            rows.append({"job": ordinal, "status": "not_requested" if max_pages == 0 else (
                "page_limit" if limited else ("no_match" if count == 0 else "success")),
                "pages": len(bundles), "resource_entries": count,
                "exhausted": exhausted, "page_limited": limited})
        table = pd.DataFrame(rows, columns=[
            "job", "status", "pages", "resource_entries", "exhausted", "page_limited"])
        summary = pd.DataFrame([{
            "queries": len(jobs), "execution_complete": True,
            "retrieval_exhaustive": bool(rows) and all(row["exhausted"] for row in rows),
            "no_match": sum(row["status"] == "no_match" for row in rows),
            "page_limited": sum(row["page_limited"] for row in rows),
            "pages": sum(row["pages"] for row in rows),
            "resource_entries": sum(row["resource_entries"] for row in rows),
        }])
        return jobs, {"rows": table, "summary": summary}

    def fetch_bundles_partitioned(
        self,
        resource_type: str,
        partition_param: str,
        start: Union[str, pd.Timestamp],
        end: Union[str, pd.Timestamp],
        params: Optional[Dict[str, Any]] = None,
        frequency: str = "YS",
        window_days: Optional[int] = None,
        max_pages_per_partition: int = -1,
        show_progress: bool = True,
        parallel_fetch: bool = False,
        auto_sort: bool = True,
        sort: str = "_id",
    ) -> Generator[Dict[str, Any], None, int]:
        """Fetch bundles by splitting a broad search into date/time partitions.

        This is useful for FHIR servers that enforce hard search caps such as
        10,000 resources. Each partition uses repeated FHIR date search
        parameters, e.g. ``recorded-date=ge2020-01-01`` and
        ``recorded-date=lt2021-01-01``.

        Parameters
        ----------
        resource_type:
            FHIR resource type to search.
        partition_param:
            Date or dateTime search parameter used for partition windows.
        start:
            Inclusive start date for the first partition.
        end:
            Exclusive end date for the final partition.
        params:
            Base search parameters merged into every partition.
        frequency:
            Pandas-style partition frequency, for example ``YS`` or ``MS``.
        window_days:
            Optional fixed window size in days; overrides ``frequency``.
        max_pages_per_partition:
            Maximum pages fetched inside each partition.
        show_progress:
            Whether to show progress bars.
        parallel_fetch:
            Whether to fetch partitions in parallel when supported.
        auto_sort:
            Whether to add a stable ``_sort`` parameter when one is missing.
        sort:
            Sort field used when ``auto_sort`` is enabled.
        """
        base_params = dict(params or {})
        if auto_sort and "_sort" not in base_params:
            base_params["_sort"] = sort
        param_list = build_partition_params(
            base_params,
            partition_param=partition_param,
            start=start,
            end=end,
            frequency=frequency,
            window_days=window_days,
        )
        if parallel_fetch and self.num_processes > 1:
            count = 0
            for bundle in self.fetch_bundles_parallel(
                resource_type=resource_type,
                param_list=param_list,
                max_pages=max_pages_per_partition,
                show_progress=show_progress,
            ):
                count += 1
                yield bundle
            return count

        progress = tqdm(
            total=len(param_list),
            desc=f"Query Partitions ({resource_type})",
            disable=not show_progress,
        )
        bundle_count = 0
        try:
            for partition_params in param_list:
                for bundle in self.fetch_bundles(
                    resource_type=resource_type,
                    params=partition_params,
                    max_pages=max_pages_per_partition,
                    show_progress=False,
                ):
                    bundle_count += 1
                    yield bundle
                progress.update(1)
        finally:
            progress.close()
        return bundle_count

    def bundles_to_dataframe(
        self,
        bundles: Iterable[Dict[str, Any] | FHIRObj],
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        per_bundle_metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Convert bundles to DataFrame(s).

        Parameters
        ----------
        bundles:
            Iterable of FHIR Bundle JSON objects.
        process_function:
            Custom processing function. Required when mode="custom".
        fhir_paths:
            FHIRPath expressions to extract fields (requires fhirpathpy).
        mode:
            "flatten" (default) or "custom".
        use_multiprocessing:
            Whether to process bundles with multiprocessing.
        per_bundle_metadata:
            Optional list of dicts, one per bundle; each dict is merged into
            every row from that bundle (e.g. to attach column_map values).
        """
        bundles_list = list(bundles)
        if self.log_requests:
            event(logger, "fhir", "activity", level=logging.DEBUG)
        if fhir_paths is not None:
            compiled = _compile_fhir_paths(fhir_paths)
            # Store compiled paths globally for multiprocessing worker access.
            global _FHIRPATH_COMPILED
            _FHIRPATH_COMPILED = compiled
            process_function = _parse_fhir_path_worker
            mode = "custom"
        if mode == "flatten":
            process_function = flatten_data
        elif mode == "custom":
            if process_function is None:
                raise ValueError("custom mode requires a process_function.")
        else:
            raise ValueError("mode must be 'flatten' or 'custom'.")
        if use_multiprocessing and self.num_processes > 1:
            if process_function is _parse_fhir_path_worker and fhir_paths is not None:
                with mp.Pool(
                    processes=self.num_processes,
                    initializer=_init_fhirpath_worker,
                    initargs=(compiled,),
                ) as pool:
                    processed = list(pool.imap(process_function, bundles_list))
            else:
                with mp.Pool(processes=self.num_processes) as pool:
                    processed = list(pool.imap(process_function, bundles_list))
        else:
            processed = [process_function(bundle) for bundle in bundles_list]

        if per_bundle_metadata is not None:
            if len(per_bundle_metadata) != len(processed):
                raise ValueError("Bundle metadata must align with processed bundles.")
            for i, bundle_output in enumerate(processed):
                if i < len(per_bundle_metadata) and per_bundle_metadata[i]:
                    meta = per_bundle_metadata[i]
                    for rows in bundle_output.values():
                        for row in rows:
                            if set(row).intersection(meta):
                                raise ValueError("Input metadata conflicts with resource output columns.")
                            row.update(meta)

        bundle_count = len(bundles_list)
        entry_count = sum(_bundle_entry_count(bundle) for bundle in bundles_list)
        row_count = _processed_row_count(processed)
        event(logger, "fhir", "activity", level=logging.DEBUG)

        return _records_to_dataframe(processed)

    def query_to_dataframe_partitioned(
        self,
        resource_type: str,
        partition_param: str,
        start: Union[str, pd.Timestamp],
        end: Union[str, pd.Timestamp],
        params: Optional[Dict[str, Any]] = None,
        frequency: str = "YS",
        window_days: Optional[int] = None,
        max_pages_per_partition: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_fetch: bool = False,
        include_partition_columns: bool = True,
        deduplicate_by: Optional[Union[str, Sequence[str]]] = None,
        auto_sort: bool = True,
        sort: str = "_id",
        show_progress: bool = True,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Run a partitioned FHIR search and return DataFrame output.

        Partitioned search splits a broad date/dateTime range into smaller
        search requests to work around server-side result caps. Use a real FHIR
        search parameter for ``partition_param`` such as ``recorded-date``,
        ``date``, ``authored``, or ``_lastUpdated`` depending on the resource
        and server.

        Parameters
        ----------
        resource_type:
            FHIR resource type to search.
        partition_param:
            Date or dateTime search parameter used for partition windows.
        start:
            Inclusive start date for the first partition.
        end:
            Exclusive end date for the final partition.
        params:
            Base search parameters merged into every partition.
        frequency:
            Pandas-style partition frequency, for example ``YS`` or ``MS``.
        window_days:
            Optional fixed window size in days; overrides ``frequency``.
        max_pages_per_partition:
            Maximum pages fetched inside each partition.
        process_function:
            Custom bundle processing function used in ``custom`` mode.
        fhir_paths:
            FHIRPath expressions to extract columns from each resource.
        mode:
            DataFrame conversion mode, usually ``flatten`` or ``custom``.
        use_multiprocessing:
            Whether bundle-to-table conversion can use multiprocessing.
        parallel_fetch:
            Whether partitions may be fetched in parallel.
        include_partition_columns:
            Whether partition metadata columns are added to result rows.
        deduplicate_by:
            Optional column or columns used to drop duplicate rows.
        auto_sort:
            Whether to add a stable ``_sort`` parameter when one is missing.
        sort:
            Sort field used when ``auto_sort`` is enabled.
        show_progress:
            Whether to show progress bars.
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        base_params = dict(params or {})
        if auto_sort and "_sort" not in base_params:
            base_params["_sort"] = sort
        param_list = build_partition_params(
            base_params,
            partition_param=partition_param,
            start=start,
            end=end,
            frequency=frequency,
            window_days=window_days,
        )

        jobs, report = self._query_jobs(resource_type, param_list, max_pages_per_partition,
                                       parallel_fetch, show_progress)
        bundles = [bundle for job in jobs for bundle in job]
        metadata = _partition_metadata(param_list, partition_param)
        per_bundle_metadata = [metadata[i] for i, job in enumerate(jobs) for _ in job] if include_partition_columns else None

        result = self.bundles_to_dataframe(
            bundles=bundles,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            per_bundle_metadata=per_bundle_metadata,
        )
        result = _deduplicate_result(result, deduplicate_by)
        return {"data": result, "report": report} if return_report else result

    def query_to_dataframe(
        self,
        resource_type: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_params: Optional[Sequence[Dict[str, Any]]] = None,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Run a query and return DataFrame(s).

        Parameters
        ----------
        resource_type:
            FHIR resource type.
        params:
            Query parameters for a single request flow.
        max_pages:
            Maximum pages to fetch (-1 for all).
        process_function:
            Custom processing function.
        fhir_paths:
            FHIRPath expressions to extract fields.
        mode:
            "flatten" (default) or "custom".
        use_multiprocessing:
            Whether to process bundles with multiprocessing.
        parallel_params:
            If provided, runs parallel jobs for each param dict.
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        if self.log_requests:
            event(logger, "fhir", "activity", level=logging.DEBUG)
        jobs, report = self._query_jobs(resource_type,
            list(parallel_params) if parallel_params is not None else [params or {}],
            max_pages, parallel_params is not None, True)
        bundles = [bundle for job in jobs for bundle in job]
        result = self.bundles_to_dataframe(
            bundles=bundles,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
        )
        return {"data": result, "report": report} if return_report else result

    @batch_report("fhir")
    def query_from_dataframe(
        self,
        df: pd.DataFrame,
        resource_type: str,
        column_map: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_fetch: bool = False,
        param_prefix: Optional[Dict[str, str]] = None,
        include_column_map_columns: bool = False,
        show_progress: bool = True,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Run one query per DataFrame row and return DataFrame(s).

        Parameters
        ----------
        df:
            Input DataFrame containing query values.
        resource_type:
            FHIR resource type.
        column_map:
            Mapping of FHIR param -> DataFrame column. Column values can be
            scalars or list-like; lists are sent comma-separated for the
            same param (e.g. code=a,b).
        params:
            Base query parameters added to each request. Values may be
            list-like; multiple values are sent comma-separated (e.g. code=a,b).
        max_pages:
            Maximum pages per row (-1 for all).
        process_function:
            Custom processing function.
        fhir_paths:
            FHIRPath expressions to extract fields.
        mode:
            "flatten" (default) or "custom".
        use_multiprocessing:
            Whether to process bundles with multiprocessing.
        parallel_fetch:
            Whether to fetch bundles in parallel (uses active Auth token or basic auth).
        param_prefix:
            Optional mapping of FHIR param -> prefix to prepend to each value
            (e.g., {"subject": "Patient/"}).
        include_column_map_columns:
            If True, the DataFrame column values used as query params (from
            column_map) are added as columns to the result so each row can be
            traced back to the input row. Works with sequential or parallel
            fetching; original values and input order are preserved.
        show_progress:
            Show completed input-query progress (not resource or page counts).
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        if self.log_requests:
            event(logger, "fhir", "activity", level=logging.DEBUG)
        if df.empty:
            raise ValueError("Input DataFrame is empty.")
        if not df.columns.is_unique:
            raise ValueError("Input column names must be unique.")
        for _, col in column_map.items():
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
            if df[col].isnull().any():
                raise ValueError(f"Column '{col}' contains null values.")

        base_params = params or {}
        prefixes = param_prefix or {}
        param_list = []
        for row in df.itertuples(index=False):
            row_params: Dict[str, Any] = {}
            for fhir_param, col in column_map.items():
                value = row[df.columns.get_loc(col)]
                prefix = prefixes.get(fhir_param, "")
                if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
                    row_params[fhir_param] = [
                        f"{prefix}{v}" if prefix else v for v in value
                    ]
                else:
                    row_params[fhir_param] = f"{prefix}{value}" if prefix else value
            param_list.append({**base_params, **row_params})

        jobs, report = self._query_jobs(resource_type, param_list, max_pages,
                                       parallel_fetch, show_progress)
        bundles = [bundle for job in jobs for bundle in job]
        per_bundle_metadata = [
            {col: df[col].iloc[i] for col in column_map.values()}
            for i, job in enumerate(jobs) for _ in job
        ] if include_column_map_columns else None

        result = self.bundles_to_dataframe(
            bundles=bundles,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            per_bundle_metadata=per_bundle_metadata,
        )
        return {"data": result, "report": report} if return_report else result

    def query_df(
        self,
        resource_type: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_params: Optional[Sequence[Dict[str, Any]]] = None,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Short alias for query_to_dataframe.

        Parameters
        ----------
        resource_type:
            FHIR resource type.
        params:
            Search parameters for one request flow.
        max_pages:
            Maximum pages to fetch.
        process_function:
            Custom bundle processing function used in ``custom`` mode.
        fhir_paths:
            FHIRPath expressions to extract columns from each resource.
        mode:
            DataFrame conversion mode, usually ``flatten`` or ``custom``.
        use_multiprocessing:
            Whether bundle-to-table conversion can use multiprocessing.
        parallel_params:
            Optional sequence of parameter dictionaries fetched in parallel.
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        return self.query_to_dataframe(
            resource_type=resource_type,
            params=params,
            max_pages=max_pages,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            parallel_params=parallel_params,
            return_report=return_report,
        )

    def search_df(
        self,
        resource_type: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_params: Optional[Sequence[Dict[str, Any]]] = None,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Friendly FHIR search alias returning DataFrame output.

        This is the preferred REST-facing name for new code. ``query_df`` and
        ``query_to_dataframe`` remain supported compatibility names.

        Parameters
        ----------
        resource_type:
            FHIR resource type.
        params:
            Search parameters for one request flow.
        max_pages:
            Maximum pages to fetch.
        process_function:
            Custom bundle processing function used in ``custom`` mode.
        fhir_paths:
            FHIRPath expressions to extract columns from each resource.
        mode:
            DataFrame conversion mode, usually ``flatten`` or ``custom``.
        use_multiprocessing:
            Whether bundle-to-table conversion can use multiprocessing.
        parallel_params:
            Optional sequence of parameter dictionaries fetched in parallel.
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        return self.query_to_dataframe(
            resource_type=resource_type,
            params=params,
            max_pages=max_pages,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            parallel_params=parallel_params,
            return_report=return_report,
        )

    def query_df_partitioned(
        self,
        resource_type: str,
        partition_param: str,
        start: Union[str, pd.Timestamp],
        end: Union[str, pd.Timestamp],
        params: Optional[Dict[str, Any]] = None,
        frequency: str = "YS",
        window_days: Optional[int] = None,
        max_pages_per_partition: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_fetch: bool = False,
        include_partition_columns: bool = True,
        deduplicate_by: Optional[Union[str, Sequence[str]]] = None,
        auto_sort: bool = True,
        sort: str = "_id",
        show_progress: bool = True,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Short alias for query_to_dataframe_partitioned.

        Parameters
        ----------
        resource_type:
            FHIR resource type to search.
        partition_param:
            Date or dateTime search parameter used for partition windows.
        start:
            Inclusive start date for the first partition.
        end:
            Exclusive end date for the final partition.
        params:
            Base search parameters merged into every partition.
        frequency:
            Pandas-style partition frequency.
        window_days:
            Optional fixed window size in days.
        max_pages_per_partition:
            Maximum pages fetched inside each partition.
        process_function:
            Custom bundle processing function used in ``custom`` mode.
        fhir_paths:
            FHIRPath expressions to extract columns from each resource.
        mode:
            DataFrame conversion mode, usually ``flatten`` or ``custom``.
        use_multiprocessing:
            Whether bundle-to-table conversion can use multiprocessing.
        parallel_fetch:
            Whether partitions may be fetched in parallel.
        include_partition_columns:
            Whether partition metadata columns are added to result rows.
        deduplicate_by:
            Optional column or columns used to drop duplicate rows.
        auto_sort:
            Whether to add a stable ``_sort`` parameter when one is missing.
        sort:
            Sort field used when ``auto_sort`` is enabled.
        show_progress:
            Whether to show progress bars.
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        return self.query_to_dataframe_partitioned(
            resource_type=resource_type,
            partition_param=partition_param,
            start=start,
            end=end,
            params=params,
            frequency=frequency,
            window_days=window_days,
            max_pages_per_partition=max_pages_per_partition,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            parallel_fetch=parallel_fetch,
            include_partition_columns=include_partition_columns,
            deduplicate_by=deduplicate_by,
            auto_sort=auto_sort,
            sort=sort,
            show_progress=show_progress,
            return_report=return_report,
        )

    def search_df_partitioned(
        self,
        resource_type: str,
        partition_param: str,
        start: Union[str, pd.Timestamp],
        end: Union[str, pd.Timestamp],
        params: Optional[Dict[str, Any]] = None,
        frequency: str = "YS",
        window_days: Optional[int] = None,
        max_pages_per_partition: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_fetch: bool = False,
        include_partition_columns: bool = True,
        deduplicate_by: Optional[Union[str, Sequence[str]]] = None,
        auto_sort: bool = True,
        sort: str = "_id",
        show_progress: bool = True,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Friendly alias for partitioned FHIR search returning DataFrames.

        Parameters
        ----------
        resource_type:
            FHIR resource type to search.
        partition_param:
            Date or dateTime search parameter used for partition windows.
        start:
            Inclusive start date for the first partition.
        end:
            Exclusive end date for the final partition.
        params:
            Base search parameters merged into every partition.
        frequency:
            Pandas-style partition frequency.
        window_days:
            Optional fixed window size in days.
        max_pages_per_partition:
            Maximum pages fetched inside each partition.
        process_function:
            Custom bundle processing function used in ``custom`` mode.
        fhir_paths:
            FHIRPath expressions to extract columns from each resource.
        mode:
            DataFrame conversion mode, usually ``flatten`` or ``custom``.
        use_multiprocessing:
            Whether bundle-to-table conversion can use multiprocessing.
        parallel_fetch:
            Whether partitions may be fetched in parallel.
        include_partition_columns:
            Whether partition metadata columns are added to result rows.
        deduplicate_by:
            Optional column or columns used to drop duplicate rows.
        auto_sort:
            Whether to add a stable ``_sort`` parameter when one is missing.
        sort:
            Sort field used when ``auto_sort`` is enabled.
        show_progress:
            Whether to show progress bars.
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        return self.query_to_dataframe_partitioned(
            resource_type=resource_type,
            partition_param=partition_param,
            start=start,
            end=end,
            params=params,
            frequency=frequency,
            window_days=window_days,
            max_pages_per_partition=max_pages_per_partition,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            parallel_fetch=parallel_fetch,
            include_partition_columns=include_partition_columns,
            deduplicate_by=deduplicate_by,
            auto_sort=auto_sort,
            sort=sort,
            show_progress=show_progress,
            return_report=return_report,
        )

    def query_df_from(
        self,
        df: pd.DataFrame,
        resource_type: str,
        column_map: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_fetch: bool = False,
        param_prefix: Optional[Dict[str, str]] = None,
        include_column_map_columns: bool = False,
        show_progress: bool = True,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Short alias for query_from_dataframe.

        Parameters
        ----------
        df:
            Input DataFrame containing query values.
        resource_type:
            FHIR resource type.
        column_map:
            Mapping from FHIR search parameter to DataFrame column.
        params:
            Base query parameters added to every row-wise request.
        max_pages:
            Maximum pages per row.
        process_function:
            Custom bundle processing function used in ``custom`` mode.
        fhir_paths:
            FHIRPath expressions to extract columns from each resource.
        mode:
            DataFrame conversion mode, usually ``flatten`` or ``custom``.
        use_multiprocessing:
            Whether bundle-to-table conversion can use multiprocessing.
        parallel_fetch:
            Whether row-wise requests may be fetched in parallel.
        param_prefix:
            Optional prefixes prepended to row values by FHIR parameter.
        include_column_map_columns:
            Whether input query values are copied into result rows.
        show_progress:
            Show completed input-query progress (not resource or page counts).
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        return self.query_from_dataframe(
            df=df,
            resource_type=resource_type,
            column_map=column_map,
            params=params,
            max_pages=max_pages,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            parallel_fetch=parallel_fetch,
            param_prefix=param_prefix,
            include_column_map_columns=include_column_map_columns,
            show_progress=show_progress,
            return_report=return_report,
        )

    def search_df_from(
        self,
        df: pd.DataFrame,
        resource_type: str,
        column_map: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = -1,
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
        parallel_fetch: bool = False,
        param_prefix: Optional[Dict[str, str]] = None,
        include_column_map_columns: bool = False,
        show_progress: bool = True,
        *,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Friendly row-wise FHIR search alias returning DataFrame output.

        This is the preferred REST-facing name for new code. ``query_df_from``
        and ``query_from_dataframe`` remain supported compatibility names.

        Parameters
        ----------
        df:
            Input DataFrame containing query values.
        resource_type:
            FHIR resource type.
        column_map:
            Mapping from FHIR search parameter to DataFrame column.
        params:
            Base query parameters added to every row-wise request.
        max_pages:
            Maximum pages per row.
        process_function:
            Custom bundle processing function used in ``custom`` mode.
        fhir_paths:
            FHIRPath expressions to extract columns from each resource.
        mode:
            DataFrame conversion mode, usually ``flatten`` or ``custom``.
        use_multiprocessing:
            Whether bundle-to-table conversion can use multiprocessing.
        parallel_fetch:
            Whether row-wise requests may be fetched in parallel.
        param_prefix:
            Optional prefixes prepended to row values by FHIR parameter.
        include_column_map_columns:
            Whether input query values are copied into result rows.
        show_progress:
            Show completed input-query progress (not resource or page counts).
        return_report:
            Return data and per-query completeness tables when True; defaults to False.
        """
        return self.query_from_dataframe(
            df=df,
            resource_type=resource_type,
            column_map=column_map,
            params=params,
            max_pages=max_pages,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
            parallel_fetch=parallel_fetch,
            param_prefix=param_prefix,
            include_column_map_columns=include_column_map_columns,
            show_progress=show_progress,
            return_report=return_report,
        )

    def bundles_to_df(
        self,
        bundles: Iterable[Dict[str, Any] | FHIRObj],
        process_function: Optional[ProcessFunc] = None,
        fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
        mode: str = "flatten",
        use_multiprocessing: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Short alias for bundles_to_dataframe."""
        return self.bundles_to_dataframe(
            bundles=bundles,
            process_function=process_function,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=use_multiprocessing,
        )

    def create_resource(
        self,
        resource: Dict[str, Any],
        resource_type: Optional[str] = None,
    ) -> FHIRWriteResult:
        """POST a FHIR resource to ``/{resourceType}``."""
        from .builder import validate_fhir_resource

        validate_fhir_resource(resource)
        resolved_type, _ = _resource_type_and_id(resource, resource_type)
        return _write_json_request(
            session=self.session,
            method="POST",
            url=_join_url(self.base_url, resolved_type),
            payload=resource,
            timeout=self.request_timeout,
            log=logger if self.log_requests else None,
        )

    def update_resource(
        self,
        resource: Dict[str, Any],
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> FHIRWriteResult:
        """PUT a FHIR resource to ``/{resourceType}/{id}``."""
        from .builder import validate_fhir_resource

        validate_fhir_resource(resource)
        resolved_type, resolved_id = _resource_type_and_id(resource, resource_type, resource_id)
        if not resolved_id:
            raise ValueError("resource_id is required or resource must contain id")
        return _write_json_request(
            session=self.session,
            method="PUT",
            url=_join_url(self.base_url, f"{resolved_type}/{resolved_id}"),
            payload=resource,
            timeout=self.request_timeout,
            log=logger if self.log_requests else None,
        )

    def submit_bundle(self, bundle: Dict[str, Any]) -> FHIRWriteResult:
        """POST a transaction FHIR bundle to the server base URL."""
        from .builder import validate_fhir_bundle

        validate_fhir_bundle(bundle)
        if bundle.get("type") != "transaction":
            raise ValueError("submit_bundle requires a transaction Bundle")
        return _write_json_request(
            session=self.session,
            method="POST",
            url=self.base_url.rstrip("/"),
            payload=bundle,
            timeout=self.request_timeout,
            log=logger if self.log_requests else None,
        )


def _records_to_dataframe(
    processed: Iterable[Dict[str, List[Dict[str, Any]]]]
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Convert processed bundle records into DataFrame(s)."""
    records: Dict[str, List[Dict[str, Any]]] = {}
    for bundle_output in processed:
        for resource_type, rows in bundle_output.items():
            records.setdefault(resource_type, [])
            records[resource_type].extend(rows)
    if not records:
        return pd.DataFrame()
    dfs = {
        resource_type: pd.DataFrame(rows).dropna(axis=1, how="all")
        for resource_type, rows in records.items()
    }
    return next(iter(dfs.values())) if len(dfs) == 1 else dfs
