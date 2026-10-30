"""Authentication helpers for Fyron."""

from __future__ import annotations

from .._diagnostics import safe_network_errors

import getpass
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import requests
import jwt
from requests.auth import AuthBase, HTTPBasicAuth


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def _as_timedelta(value: Optional[Union[int, timedelta]]) -> Optional[timedelta]:
    """Normalize a minutes int or timedelta into a timedelta (or None)."""
    if value is None:
        return None
    if isinstance(value, timedelta):
        return value
    return timedelta(minutes=int(value))


def _response_text(response: requests.Response) -> str:
    """Return a compact response body preview for auth classification."""
    try:
        return response.text[:2000]
    except Exception:
        return ""


def _looks_like_auth_failure(response: requests.Response) -> bool:
    """Return True when a non-401 response likely represents token failure."""
    if response.status_code == requests.codes.unauthorized:
        return True
    if response.status_code not in {requests.codes.bad_request, requests.codes.forbidden}:
        return False
    header_text = " ".join(
        str(value) for key, value in response.headers.items() if key.lower() == "www-authenticate"
    )
    body_text = _response_text(response)
    combined = f"{header_text}\n{body_text}".lower()
    auth_terms = (
        "access token",
        "auth",
        "bearer",
        "expired",
        "invalid_token",
        "jwt",
        "login",
        "session",
        "token",
        "unauthorized",
    )
    return any(term in combined for term in auth_terms)


class TokenAuth(AuthBase):
    """Very small token auth helper.

    Expects token endpoints that return JSON with `access_token` or `token`.
    """

    def __init__(
        self,
        username: str,
        password: str,
        auth_url: str,
        refresh_url: Optional[str] = None,
        token: Optional[str] = None,
        token_refresh_delta: Optional[Union[int, timedelta]] = None,
        max_login_attempts: int = 3,
        session: Optional[requests.Session] = None,
        token_field: str = "access_token",
        auth_method: str = "basic",
    ) -> None:
        """Create a token-based auth handler."""
        self._username = username
        self._lock = threading.RLock()
        self._password = password
        self._auth_url = auth_url
        self._refresh_url = refresh_url
        self._token_field = token_field
        self._session = session or requests.Session()
        self._token_session = requests.Session()
        self._session.hooks["response"].append(self._refresh_hook)
        self._max_login_attempts = max_login_attempts
        self._refresh_delta = _as_timedelta(token_refresh_delta)
        self._token: Optional[str] = None
        self._issued_at: Optional[datetime] = None
        self._auth_method = auth_method.lower()
        if token is None:
            self._authenticate()
        else:
            self._set_token(token)
        self.auth_time = now_utc()

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:  # type: ignore[override]
        """Attach a Bearer token to the request."""
        r.headers["Authorization"] = f"Bearer {self._get_token()}"
        return r

    def _get_token(self, rejected: Optional[str] = None) -> str:
        """Return a live token, serializing renewal for parent-owned workers."""
        with self._lock:
            if rejected is not None and self._token == rejected:
                self._refresh()
            else:
                self._ensure_token()
            if self._token is None:
                raise RuntimeError("TokenAuth could not obtain a token.")
            self.token = self._token
            return self._token

    def _ensure_token(self) -> None:
        """Ensure a valid token is present, refreshing or logging in if needed."""
        if self._token is None:
            self._authenticate()
            return
        if self.is_refresh_required():
            self._refresh()

    @safe_network_errors
    def _refresh(self) -> None:
        """Refresh the token using refresh_url or fall back to login."""
        if self._refresh_url is None:
            self._authenticate()
            return
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        response = self._token_session.get(
            self._refresh_url, headers=headers, timeout=self._request_timeout(), allow_redirects=False
        )
        if response.is_redirect:
            response.close()
            raise RuntimeError("Token refresh endpoint redirected; check refresh_url.")
        if response.status_code == requests.codes.unauthorized:
            self._authenticate()
        else:
            response.raise_for_status()
            token = self._extract_token(response)
            self._set_token(token)
        self.auth_time = now_utc()

    @safe_network_errors
    def _authenticate(self) -> None:
        """Login to obtain a fresh token."""
        last_error: Optional[Exception] = None
        for _ in range(self._max_login_attempts):
            try:
                if self._auth_method == "basic":
                    response = self._token_session.get(
                        self._auth_url,
                        auth=(self._username, self._password),
                        timeout=self._request_timeout(),
                    )
                else:
                    response = self._token_session.post(
                        self._auth_url,
                        json={"username": self._username, "password": self._password},
                        timeout=self._request_timeout(),
                    )
                response.raise_for_status()
                token = self._extract_token(response)
                self._set_token(token)
                self.auth_time = now_utc()
                return
            except Exception as exc:  # pragma: no cover - last-resort fallthrough
                last_error = exc
        if last_error is not None:
            raise last_error

    def _request_timeout(self) -> float:
        deadline = getattr(self, "_worker_deadline", None)
        remaining = 30 if deadline is None else min(30, deadline - time.monotonic())
        if remaining <= 0:
            raise RuntimeError("Worker authentication deadline exceeded.")
        return remaining

    def _extract_token(self, response: requests.Response) -> str:
        """Extract the token from a JSON response payload."""
        try:
            data = response.json()
            token = data.get(self._token_field) or data.get("token")
        except ValueError:
            token = response.text.strip()
        if not token:
            raise ValueError("Token response did not include an access token.")
        return token

    def _set_token(self, token: str) -> None:
        """Store the token and record issue time if refresh is enabled."""
        self._token = token
        self.token = token
        self._issued_at = datetime.now(timezone.utc)

    def is_refresh_required(self) -> bool:
        """Return True if token should be refreshed."""
        if self._token is None:
            return True
        try:
            decoded = jwt.decode(self._token, options={"verify_signature": False})
            if "exp" in decoded and "iat" in decoded:
                refresh_interval = (decoded["exp"] - decoded["iat"]) / 4
                return datetime.now(timezone.utc).timestamp() > (decoded["exp"] - refresh_interval)
            return False
        except jwt.exceptions.PyJWTError:
            return (
                self._refresh_delta is not None
                and (now_utc() - self.auth_time) > self._refresh_delta
            )

    def _refresh_hook(
        self, response: requests.Response, *args: Any, **kwargs: Any
    ) -> Optional[requests.Response]:
        """Refresh token on unauthorized or expiry."""
        if _looks_like_auth_failure(response) or self.is_refresh_required():
            attempts = getattr(response.request, "login_reattempted_times", 0)
            attempts += 1
            if attempts >= self._max_login_attempts:
                return response
            setattr(response.request, "login_reattempted_times", attempts)
            header = response.request.headers.get("Authorization", "")
            rejected = header[7:] if header.startswith("Bearer ") else self._token
            self._get_token(rejected=rejected)
            return self._session.send(self(response.request), **kwargs)
        return response


class Auth:
    """Simplified authentication wrapper for Fyron sessions.

    Supports password-to-token, HTTP Basic, OAuth device and client credentials.

    Use ``Auth.client_credentials`` for service accounts with an OIDC issuer or
    explicit token endpoint. This obtains access tokens, not user ID tokens.

    For ``auth_type="device_code"``, ``auth_url`` is the OIDC issuer and
    ``client_id`` is required. User credentials are not read. Optional
    ``client_secret`` enables confidential-client authentication; ``scope``
    defaults to ``openid``. ``token_cache`` opts into sensitive plaintext token
    storage protected by owner-only POSIX permissions and file locks.

    ``allow_reauthentication=False`` prohibits interactive approval, including
    at startup without usable cached credentials. ``device_code_callback``
    receives verification instructions instead of displaying them. Both
    ``device_authorization_endpoint`` and ``token_endpoint`` must be supplied
    to bypass discovery; ``authorization_endpoint`` optionally identifies login
    redirects. Device options are keyword-only and do not alter other modes.
    """

    def __init__(
        self,
        auth_url: Optional[str] = None,
        auth_type: str = "token",
        refresh_url: Optional[str] = None,
        username: Optional[str] = None,
        auth_method: str = "env",
        token_auth_method: Optional[str] = None,
        token: Optional[str] = None,
        max_login_attempts: int = 3,
        token_refresh_delta: Optional[Union[int, timedelta]] = None,
        session: Optional[requests.Session] = None,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: Optional[str] = None,
        token_cache: Optional[str] = None,
        allow_reauthentication: bool = True,
        device_authorization_endpoint: Optional[str] = None,
        token_endpoint: Optional[str] = None,
        authorization_endpoint: Optional[str] = None,
        device_code_callback=None,
        client_auth_method: Optional[str] = None,
    ) -> None:
        """Initialize an authenticated requests session."""
        self.auth_type = auth_type
        self.auth_method = auth_method
        self.auth_url = auth_url or os.environ.get("FHIR_AUTH_URL")
        self.refresh_url = refresh_url or os.environ.get("FHIR_REFRESH_URL")
        self.username = username
        self.token = token
        self.token_auth_method = (token_auth_method or "basic").lower()
        self.max_login_attempts = max_login_attempts
        self.token_refresh_delta = token_refresh_delta
        self._user_env_name = "FHIR_USER"
        self._pass_env_name = "FHIR_PASSWORD"
        self.session = session or requests.Session()
        if auth_type is not None and auth_type.lower() == "client_credentials":
            from ._client_credentials import _ClientCredentialsAuth

            self.session.auth = _ClientCredentialsAuth(
                auth_url, client_id, client_secret, token_endpoint=token_endpoint,
                scope="" if scope is None else scope,
                client_auth_method=client_auth_method,
            )
            return
        if auth_type is not None and auth_type.lower() == "device_code":
            from ._device_auth import _DeviceAuth

            self.session.auth = _DeviceAuth(
                self.auth_url, client_id, client_secret=client_secret, scope="openid" if scope is None else scope,
                token_cache=token_cache, allow_reauthentication=allow_reauthentication,
                device_authorization_endpoint=device_authorization_endpoint,
                token_endpoint=token_endpoint, authorization_endpoint=authorization_endpoint,
                device_code_callback=device_code_callback,
            )
            return
        self._authenticate()

    @classmethod
    def client_credentials(
        cls, *, client_id: str, client_secret: str, auth_url: Optional[str] = None,
        token_endpoint: Optional[str] = None, scope: str = "",
        client_auth_method: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> "Auth":
        """Create service-account OAuth auth, optionally using OIDC discovery.

        Supply an issuer in ``auth_url`` or an explicit ``token_endpoint``.
        Scopes must be approved by the provider. Tokens are renewed automatically
        using the client credentials, without a browser or user password.
        ``client_auth_method`` supports ``client_secret_basic`` (preferred) and
        ``client_secret_post``. Parallel FHIR/DICOM workers share token renewal.
        """
        return cls(
            auth_type="client_credentials", auth_url=auth_url,
            client_id=client_id, client_secret=client_secret, scope=scope,
            token_endpoint=token_endpoint, client_auth_method=client_auth_method,
            session=session,
        )

    @classmethod
    def token_env(
        cls,
        *,
        auth_url: str,
        refresh_url: Optional[str] = None,
        token_auth_method: str = "basic",
        token: Optional[str] = None,
        max_login_attempts: int = 3,
        token_refresh_delta: Optional[Union[int, timedelta]] = None,
        session: Optional[requests.Session] = None,
    ) -> "Auth":
        """Create token-based auth using credentials from environment variables."""
        return cls(
            auth_url=auth_url,
            auth_type="token",
            refresh_url=refresh_url,
            auth_method="env",
            token_auth_method=token_auth_method,
            token=token,
            max_login_attempts=max_login_attempts,
            token_refresh_delta=token_refresh_delta,
            session=session,
        )

    def __enter__(self) -> "Auth":
        """Return self for context manager usage."""
        return self

    def close(self) -> None:
        """Close the underlying session."""
        from ._device_auth import _DeviceAuth
        from ._client_credentials import _ClientCredentialsAuth

        if isinstance(self.session.auth, (_DeviceAuth, _ClientCredentialsAuth)):
            self.session.auth.close()
        self.session.close()

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        """Close the session on context manager exit."""
        self.close()

    def _authenticate(self) -> None:
        """Authenticate the session using the configured method."""
        if self.auth_type is None:
            return
        auth_type = self.auth_type.lower()
        if auth_type not in {"token", "basic"}:
            raise ValueError(f"Unsupported auth_type: {self.auth_type}")
        if auth_type == "basic":
            username, password = self._resolve_credentials()
            self.session.auth = HTTPBasicAuth(username, password)
            return
        if self.auth_url is None and self.token is None:
            raise ValueError("auth_url is required for token auth unless token is provided.")
        username, password = self._resolve_credentials() if self.token is None else ("", "")
        self.session.auth = TokenAuth(
            username=username,
            password=password,
            auth_url=self.auth_url or "",
            refresh_url=self.refresh_url,
            token=self.token,
            token_refresh_delta=self.token_refresh_delta,
            max_login_attempts=self.max_login_attempts,
            session=self.session,
            auth_method=self.token_auth_method,
        )

    def _resolve_credentials(self) -> tuple[str, str]:
        """Resolve credentials via password prompt or environment."""
        method = self.auth_method.lower()
        if method == "password":
            if not self.username:
                raise ValueError("username is required for password auth.")
            return self.username, getpass.getpass()
        if method == "env":
            return os.environ[self._user_env_name], os.environ[self._pass_env_name]
        raise ValueError(f"Unsupported auth_method: {self.auth_method}")
