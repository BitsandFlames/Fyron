"""Private HTTP retries, redirect checks and controlled transport logging."""

import contextvars
import functools
import inspect
import logging
import time
import warnings
from contextlib import contextmanager
from urllib3.util.retry import Retry

from urllib.parse import urljoin, urlsplit

import requests


def _redirect_boundary(response, **kwargs):
    if not response.is_redirect:
        return response
    try:
        source = urlsplit(response.url)
        target = urlsplit(urljoin(response.url, response.headers["Location"]))

        def origin(url):
            port = url.port if url.port is not None else (443 if url.scheme == "https" else 80)
            return url.scheme.lower(), url.hostname, port

        allowed = (target.scheme in {"http", "https"} and target.hostname
                   and target.username is None and target.password is None
                   and origin(source) == origin(target))
    except (TypeError, ValueError):
        allowed = False
    if not allowed:
        response.close()
        raise requests.exceptions.InvalidURL(
            "Unsafe cross-origin or credential-bearing redirect blocked.", response=response,
        )
    return response


def guard_redirects(session):
    """Preserve existing hooks while checking redirects before Requests follows them."""
    hooks = getattr(session, "hooks", None)
    if isinstance(hooks, dict):
        current = hooks.get("response", [])
        current = [current] if callable(current) else list(current or [])
        if _redirect_boundary not in current:
            hooks["response"] = [_redirect_boundary, *current]
    return session


# Upstream transports may log full request URLs, headers and remote warnings.
# Filters apply only inside Fyron operations, leaving unrelated application logs alone.
_private = contextvars.ContextVar("fyron_private_transport", default=False)


class _PrivateFilter(logging.Filter):
    def filter(self, record):
        return not _private.get()


_filter = _PrivateFilter()


def _guard_upstream_warnings():
    """Redact upstream parsing warnings only in the current client context."""
    previous = warnings.showwarning
    if getattr(previous, "_fyron_boundary", False):
        return
    @functools.wraps(previous)
    def show(message, category, filename, lineno, file=None, line=None):
        source = str(filename).replace("\\", "/")
        if _private.get() and any(part in source for part in (
                "/pydicom/", "/dicomweb_client/", "/urllib3/")):
            from ._diagnostics import event
            event(logging.getLogger("fyron.transport"), "network", "warning",
                  level=logging.WARNING)
            return
        return previous(message, category, filename, lineno, file=file, line=line)
    show._fyron_boundary = True
    warnings.showwarning = show


@contextmanager
def transport_boundary():
    _guard_upstream_warnings()
    for name in ("urllib3.connectionpool", "urllib3.connection", "urllib3.poolmanager",
                 "urllib3.util.retry", "dicomweb_client.web",
                 "dicomweb_client.api", "pydicom", "requests.packages.urllib3.connectionpool"):
        logger = logging.getLogger(name)
        if _filter not in logger.filters:
            logger.addFilter(_filter)
    token = _private.set(True)
    try:
        yield
    finally:
        _private.reset(token)


def private_transport(function):
    """Keep upstream transport text out of logs, including generator execution."""
    if inspect.isgeneratorfunction(function):
        @functools.wraps(function)
        def generate(*args, **kwargs):
            with transport_boundary():
                yield from function(*args, **kwargs)
        return generate
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        with transport_boundary():
            return function(*args, **kwargs)
    return wrapped


def default_retries():
    return Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 502, 503, 504],
                 allowed_methods=["GET"], respect_retry_after_header=True, raise_on_status=False)


def guarded_hooks(session):
    """Add a per-request boundary without changing a borrowed session's hooks."""
    existing = getattr(session, "hooks", {}).get("response", [])
    existing = [existing] if callable(existing) else list(existing or [])
    return {"response": [_redirect_boundary, *[hook for hook in existing if hook is not _redirect_boundary]]}


class ClientCancelledError(requests.RequestException):
    _fyron_cancelled = True


def check_cancelled(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise ClientCancelledError("Client operation cancelled.")


def _retry_wait(seconds, cancel_event):
    if cancel_event is None:
        time.sleep(seconds)
    elif cancel_event.wait(seconds):
        check_cancelled(cancel_event)


@private_transport
def get_with_retry(session, url, *, retries=None, cancel_event=None, **kwargs):
    """Retry transient GET failures without replacing session adapters or auth."""
    policy = retries if retries is not None else default_retries()
    kwargs.setdefault("hooks", guarded_hooks(session))
    # Adapter retry policies remain caller-owned. Do not multiply their retries.
    adapter = session.get_adapter(url) if hasattr(session, "get_adapter") else None
    adapter_policy = getattr(adapter, "max_retries", None)
    if adapter_policy is not None and getattr(adapter_policy, "total", 0) not in (0, False):
        check_cancelled(cancel_event)
        return session.get(url, **kwargs)
    while True:
        check_cancelled(cancel_event)
        try:
            response = session.get(url, **kwargs)
        except requests.exceptions.SSLError:
            raise
        except (requests.ConnectionError, requests.Timeout) as exc:
            if policy.total in (0, False) or (policy.allowed_methods and "GET" not in policy.allowed_methods):
                raise
            try:
                policy = policy.increment(method="GET", error=exc)
            except Exception:
                raise requests.ConnectionError("HTTP GET retry budget exhausted.") from None
            _retry_wait(policy.get_backoff_time(), cancel_event)
            continue
        if not policy.is_retry("GET", response.status_code, "Retry-After" in response.headers):
            return response
        if policy.total in (0, False):
            return response
        try:
            # Retry only needs status/redirect metadata, not a transport-specific raw object.
            class RetryResponse:
                status = response.status_code
                def get_redirect_location(self):
                    return None
            updated = policy.increment(method="GET", response=RetryResponse())
        except Exception:
            return response
        try:
            wait = policy.get_retry_after(response) or updated.get_backoff_time()
        except Exception:
            wait = updated.get_backoff_time()
        response.close()
        _retry_wait(wait, cancel_event)
        policy = updated


class DICOMSession:
    """Private request facade; retain authentication and ownership on the caller session."""
    def __init__(self, session, timeout=None, retries=None):
        self.session = session
        self.timeout = timeout
        self.retries = retries

    def get(self, *args, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return get_with_retry(self.session, *args, retries=self.retries, **kwargs)

    def __getattr__(self, name):
        return getattr(self.session, name)
