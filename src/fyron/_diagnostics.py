"""Controlled diagnostics for network operations; never serialize remote text."""

from contextlib import contextmanager
from functools import wraps
import copy
import logging
import time
import uuid
from contextvars import ContextVar

import requests


CATEGORIES = {
    "authentication", "permission", "timeout", "network", "unexpected_response",
    "conversion", "filesystem", "empty_download", "unknown",
}
_batch_state = ContextVar("fyron_batch_state", default=None)


def classify_error(error, default="unknown"):
    """Return a controlled category and optional numeric HTTP status."""
    for _ in range(5):
        attempt = getattr(error, "last_attempt", None)
        value = getattr(attempt, "value", None)
        if isinstance(value, tuple) and len(value) > 1 and isinstance(value[1], BaseException):
            error = value[1]
        else:
            break
    response = getattr(error, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(response, dict):
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    status = status if type(status) is int and 100 <= status <= 599 else None
    if status == 401:
        category = "authentication"
    elif status == 403 or isinstance(error, PermissionError):
        category = "permission"
    elif isinstance(error, (requests.Timeout, TimeoutError)):
        category = "timeout"
    elif isinstance(error, requests.ConnectionError):
        category = "network"
    elif isinstance(error, requests.RequestException):
        category = "unexpected_response" if status else "network"
    elif isinstance(error, OSError):
        category = "filesystem"
    elif isinstance(error, ValueError):
        category = "conversion" if default == "conversion" else "unexpected_response"
    else:
        category = default if default in CATEGORIES else "unknown"
    return category, status


def safe_error(error, default="unknown"):
    category, status = classify_error(error, default)
    return f"Operation failed ({category})" + (f"; HTTP {status}." if status else ".")


def error_event(logger, operation, error):
    category, status = classify_error(error)
    event(logger, operation, "failed", level=logging.ERROR,
          error_category=category, http_status=status)


def safe_network_errors(function):
    """Retain exception types while removing remote diagnostics at the boundary."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as error:
            message = safe_error(error)
            if isinstance(error, ImportError) and function.__module__ == "fyron.core.s3":
                message = 'S3 support requires boto3. Install with `uv add "fyron[s3]"`.'
            category, status = classify_error(error)
            event(logging.getLogger(function.__module__), "network", "failed",
                  level=logging.ERROR, error_category=category, http_status=status)
            sanitized = copy.copy(error)
            sanitized.args = (message,)
            if isinstance(sanitized, OSError):
                sanitized.strerror = message
            if hasattr(sanitized, "kwargs"):
                sanitized.kwargs = {key: "redacted" for key in sanitized.kwargs}
            for name in ("request", "response", "filename", "filename2"):
                if hasattr(sanitized, name):
                    setattr(sanitized, name, None)
            raise sanitized.with_traceback(None) from None
    return wrapped


def completed_task(results):
    """Record one completed task and its independently counted result outcomes."""
    state = _batch_state.get()
    if state is None:
        return
    state["completed"] += 1
    for result in results:
        error = getattr(result, "error", None)
        outcome = "failed" if error is not None else ("skipped" if getattr(result, "skipped", False) else "succeeded")
        state[outcome] = state.get(outcome, 0) + 1


def task_outcome(failed=False, skipped=False):
    state = _batch_state.get()
    if state is not None:
        state["completed"] += 1
        key = "failed" if failed else ("skipped" if skipped else "succeeded")
        state[key] = state.get(key, 0) + 1


def event(logger, operation, stage, *, level=logging.INFO, **fields):
    """Emit only internal labels and explicitly allowed numeric metadata."""
    operation = operation if operation in {"fhir", "dicom", "documents", "llm", "sql", "network", "s3", "radiomics", "boa"} else "network"
    stage = stage if stage in {"started", "finished", "incomplete", "failed", "warning", "activity", "http", "authentication", "delivery"} else "activity"
    payload = {"operation": operation, "stage": stage}
    for name in ("job", "elapsed_s", "total", "completed", "succeeded", "failed", "skipped", "http_status", "unfinished"):
        value = fields.get(name)
        if type(value) in (int, float):
            payload[name] = value
    run_id = fields.get("run_id", (_batch_state.get() or {}).get("run_id"))
    if isinstance(run_id, str) and len(run_id) == 32 and all(c in "0123456789abcdef" for c in run_id):
        payload["run_id"] = run_id
    if fields.get("error_category") in CATEGORIES:
        payload["error_category"] = fields["error_category"]
    message = " ".join(f"{key}={value}" for key, value in payload.items())
    logger.log(level, message, extra={"fyron_event": payload})


@contextmanager
def batch(logger, operation):
    state = {"run_id": uuid.uuid4().hex, "completed": 0}
    start = time.monotonic()
    event(logger, operation, "started", **state)
    try:
        yield state
    except BaseException:
        event(logger, operation, "incomplete", level=logging.WARNING,
              elapsed_s=time.monotonic() - start, **state)
        raise
    else:
        event(logger, operation, "finished", elapsed_s=time.monotonic() - start, **state)


def batch_report(operation):
    """Summarize materialized batch outputs without inspecting clinical values."""
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with batch(logging.getLogger(function.__module__), operation) as counts:
                token = _batch_state.set(counts)
                try:
                    return function(*args, **kwargs)
                finally:
                    _batch_state.reset(token)
        return wrapped
    return decorate
