"""Internal OAuth device authorization and worker coordination for Fyron."""

from __future__ import annotations

import ipaddress
import json
import math
import os
import stat
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

import requests
from requests.auth import AuthBase
from requests.utils import rewind_body

from fyron.console import info


class DeviceAuthError(RuntimeError):
    """Device authentication failed; messages intentionally exclude responses."""


def _url(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("OAuth endpoint must be a URL string.")
    parsed = urlsplit(value)
    try:
        loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        loopback = False
    if (
        (parsed.scheme != "https" and not (parsed.scheme == "http" and loopback))
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ValueError(
            "OAuth endpoints require HTTPS (HTTP literal loopback is allowed)."
        )
    return value


def _endpoint(value: str) -> tuple:
    p = urlsplit(value)
    return p.scheme, p.hostname, p.port or (443 if p.scheme == "https" else 80), p.path


def _positive(value) -> float:
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise DeviceAuthError("Invalid OAuth lifetime or interval.") from None
    if not math.isfinite(number) or number <= 0:
        raise DeviceAuthError("Invalid OAuth lifetime or interval.")
    return number


class _BearerAuth(AuthBase):
    """Request-local challenge handling, shared by local and worker auth."""

    def __call__(self, request):
        token = self.get_token()
        request.headers["Authorization"] = f"Bearer {token}"
        request.register_hook("response", self._challenge)
        return request

    def _challenge(self, response, **kwargs):
        request = response.request
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return response
        redirect = (
            response.is_redirect
            and self.authorization_endpoint
            and _endpoint(urljoin(response.url, response.headers["Location"]))
            == _endpoint(self.authorization_endpoint)
        )
        if response.status_code != 401 and not redirect:
            return response
        retry = request.copy()
        retry.hooks = {key: list(value) for key, value in request.hooks.items()}
        if retry.body is not None and not isinstance(retry.body, (str, bytes)):
            try:
                rewind_body(retry)
            except (requests.exceptions.UnrewindableBodyError, OSError, ValueError):
                return response
        try:
            token = self.get_token(rejected=header[7:])
        finally:
            response.close()
        retry.headers["Authorization"] = f"Bearer {token}"
        retry.deregister_hook("response", self._challenge)
        result = response.connection.send(retry, **kwargs)
        result.history = [*response.history, response]
        result.request = retry
        return result


class _DeviceAuth(_BearerAuth):
    def __init__(
        self,
        issuer,
        client_id,
        *,
        client_secret=None,
        scope="openid",
        token_cache=None,
        allow_reauthentication=True,
        device_authorization_endpoint=None,
        token_endpoint=None,
        authorization_endpoint=None,
        device_code_callback=None,
    ):
        if not client_id or not issuer:
            raise ValueError(
                "Device authentication requires auth_url (issuer) and client_id."
            )
        self.issuer = _url(issuer)
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = " ".join(sorted(set(scope.split())))
        self.allow_reauthentication = allow_reauthentication
        self.callback = device_code_callback
        self.cache = Path(token_cache).expanduser() if token_cache else None
        self.state = {}
        self._session = requests.Session()
        self._lock = threading.RLock()
        self._cancel = threading.Event()
        if bool(device_authorization_endpoint) != bool(token_endpoint):
            raise ValueError(
                "Supply both device_authorization_endpoint and token_endpoint."
            )
        methods = ["client_secret_basic"]
        if not token_endpoint:
            metadata = self._request(
                "GET", issuer.rstrip("/") + "/.well-known/openid-configuration"
            )
            if metadata.get("issuer") != issuer:
                raise DeviceAuthError("OIDC discovery issuer does not match auth_url.")
            device_authorization_endpoint = metadata.get(
                "device_authorization_endpoint"
            )
            token_endpoint = metadata.get("token_endpoint")
            authorization_endpoint = authorization_endpoint or metadata.get(
                "authorization_endpoint"
            )
            methods = metadata.get("token_endpoint_auth_methods_supported", methods)
        if not device_authorization_endpoint or not token_endpoint:
            raise DeviceAuthError(
                "Provider does not advertise device authorization endpoints."
            )
        self.device_endpoint = _url(device_authorization_endpoint)
        self.token_endpoint = _url(token_endpoint)
        self.authorization_endpoint = (
            _url(authorization_endpoint) if authorization_endpoint else None
        )
        self.client_method = "none"
        if client_secret:
            self.client_method = next(
                (
                    m
                    for m in ("client_secret_basic", "client_secret_post")
                    if m in methods
                ),
                None,
            )
            if self.client_method is None:
                raise DeviceAuthError("Unsupported OAuth client authentication method.")
        try:
            self.get_token()
        except BaseException:
            self.close()
            raise

    def _request(self, method, url, *, data=None, timeout=30, polling=False):
        worker_deadline = getattr(self, "_worker_deadline", None)
        if worker_deadline is not None:
            remaining = worker_deadline - time.monotonic()
            if remaining <= 0:
                raise DeviceAuthError("Worker authentication deadline exceeded.")
            timeout = min(timeout, remaining)
        kwargs = {}
        if data is not None:
            data = dict(data, client_id=self.client_id)
            if self.client_method == "client_secret_basic":
                kwargs["auth"] = (
                    quote(self.client_id, safe=""),
                    quote(self.client_secret, safe=""),
                )
            elif self.client_method == "client_secret_post":
                data["client_secret"] = self.client_secret
        try:
            with self._session.request(
                method, url, data=data, timeout=timeout, allow_redirects=False, **kwargs
            ) as response:
                if response.is_redirect or response.status_code >= 500:
                    raise DeviceAuthError("OAuth endpoint failed or redirected.")
                payload = response.json()
                if not isinstance(payload, dict):
                    raise DeviceAuthError(
                        "OAuth endpoint returned a non-object response."
                    )
                if "error" in payload and not isinstance(payload["error"], str):
                    raise DeviceAuthError(
                        "OAuth endpoint returned an invalid error code."
                    )
                if response.status_code >= 400 and "error" not in payload:
                    raise DeviceAuthError("OAuth endpoint rejected the request.")
                return payload
        except requests.exceptions.Timeout:
            if polling:
                return {"error": "_timeout"}
            raise DeviceAuthError("OAuth endpoint timed out.") from None
        except (requests.RequestException, ValueError):
            raise DeviceAuthError(
                "OAuth endpoint returned an invalid response or could not be reached."
            ) from None

    def _accept(self, payload):
        token = payload.get("access_token")
        if (
            not isinstance(token, str)
            or not token
            or not isinstance(payload.get("token_type"), str)
            or payload.get("token_type", "").lower() != "bearer"
        ):
            raise DeviceAuthError("Provider did not return a Bearer access token.")
        lifetime = _positive(payload["expires_in"]) if "expires_in" in payload else None
        refresh = payload.get("refresh_token", self.state.get("refresh_token"))
        if refresh is not None and (not isinstance(refresh, str) or not refresh):
            raise DeviceAuthError("Provider returned an invalid refresh token.")
        self.state = {
            "access_token": token,
            "refresh_token": refresh,
            "issued_at": time.time(),
            "lifetime": lifetime,
        }

    def _login(self):
        if not self.allow_reauthentication:
            raise DeviceAuthError(
                "Browser approval required; allow_reauthentication is disabled."
            )
        payload = self._request(
            "POST", self.device_endpoint, data={"scope": self.scope}
        )
        if "error" in payload or not all(
            payload.get(k)
            for k in ("device_code", "user_code", "verification_uri", "expires_in")
        ):
            raise DeviceAuthError(
                "Provider rejected device authorization or returned incomplete instructions."
            )
        lifetime = _positive(payload["expires_in"])
        interval = _positive(payload.get("interval", 5))
        deadline = time.monotonic() + lifetime
        worker_deadline = getattr(self, "_worker_deadline", None)
        if worker_deadline is not None:
            deadline = min(deadline, worker_deadline)
        instructions = {
            k: payload[k] for k in ("verification_uri", "user_code", "expires_in")
        }
        _url(instructions["verification_uri"])
        if payload.get("verification_uri_complete"):
            instructions["verification_uri_complete"] = _url(
                payload["verification_uri_complete"]
            )
        if self.callback:
            self.callback(instructions)
        else:
            info(
                f"Sign in at {instructions['verification_uri']} with code {instructions['user_code']}"
            )
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= interval:
                raise DeviceAuthError("Device authorization expired.")
            if self._cancel.wait(interval):
                raise DeviceAuthError("Device authorization cancelled.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DeviceAuthError("Device authorization expired.")
            result = self._request(
                "POST",
                self.token_endpoint,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": payload["device_code"],
                },
                timeout=min(30, remaining),
                polling=True,
            )
            if time.monotonic() >= deadline:
                raise DeviceAuthError("Device authorization expired.")
            error = result.get("error")
            if not error:
                self.state = {}
                self._accept(result)
                return
            if error == "slow_down":
                interval += 5
            elif error == "_timeout":
                interval *= 2
            elif error != "authorization_pending":
                message = {
                    "access_denied": "Device authorization denied.",
                    "expired_token": "Device authorization expired.",
                }
                raise DeviceAuthError(
                    message.get(error, "Device authorization failed.")
                )

    def _identity(self):
        return [
            self.issuer,
            self.client_id,
            self.device_endpoint,
            self.token_endpoint,
            self.scope,
        ]

    @contextmanager
    def _cache_lock(self):
        if self.cache is None:
            yield
            return
        if os.name != "posix":
            raise DeviceAuthError(
                "Token caching requires POSIX owner-only file protection; omit token_cache on this platform."
            )
        import fcntl

        self.cache.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(
            str(self.cache) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
        )
        try:
            self._check_file(fd)
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    @staticmethod
    def _check_file(fd):
        status = os.fstat(fd)
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_uid != os.getuid()
            or status.st_mode & 0o077
            or status.st_nlink != 1
        ):
            raise DeviceAuthError("Unsafe token cache permissions or ownership.")

    def _load(self):
        if self.cache is None:
            return
        try:
            fd = os.open(self.cache, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return
        with os.fdopen(fd) as stream:
            self._check_file(stream.fileno())
            try:
                record = json.load(stream)
                if record.get("identity") != self._identity():
                    return
                state = record["state"]
                if (
                    not isinstance(state["access_token"], str)
                    or not state["access_token"]
                ):
                    raise ValueError()
                _positive(state["issued_at"])
                if state["lifetime"] is not None:
                    _positive(state["lifetime"])
                if state.get("refresh_token") is not None and not isinstance(
                    state["refresh_token"], str
                ):
                    raise ValueError()
                self.state = state
            except (ValueError, KeyError, TypeError, AttributeError):
                raise DeviceAuthError(
                    "Invalid token cache; remove it and sign in again."
                ) from None

    def _save(self):
        if self.cache is None:
            return
        fd, name = tempfile.mkstemp(prefix=".fyron-token-", dir=self.cache.parent)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump({"identity": self._identity(), "state": self.state}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.cache)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def get_token(self, rejected=None):
        with self._lock, self._cache_lock():
            self._load()
            token = self.state.get("access_token")
            lifetime = self.state.get("lifetime")
            due = (
                lifetime is not None
                and time.time() >= self.state["issued_at"] + 0.75 * lifetime
            )
            if token and not due and token != rejected:
                return token
            if self.state.get("refresh_token"):
                result = self._request(
                    "POST",
                    self.token_endpoint,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.state["refresh_token"],
                    },
                )
                if not result.get("error"):
                    self._accept(result)
                elif result["error"] == "invalid_grant":
                    self._login()
                else:
                    raise DeviceAuthError("OAuth token refresh failed.")
            else:
                self._login()
            self._save()
            return self.state["access_token"]

    def close(self):
        self._session.close()

    def __getstate__(self):
        return {
            k: v
            for k, v in self.__dict__.items()
            if k not in {"_session", "_lock", "_cancel"}
        }

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._session = requests.Session()
        self._lock = threading.RLock()
        self._cancel = threading.Event()
