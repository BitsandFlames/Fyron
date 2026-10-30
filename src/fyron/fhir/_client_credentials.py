"""Internal OAuth client-credentials support for service accounts."""

import threading
import time
from urllib.parse import quote_plus

import requests

from ._device_auth import _BearerAuth, _positive, _url


class _ClientCredentialsAuth(_BearerAuth):
    def __init__(
        self,
        issuer,
        client_id,
        client_secret,
        *,
        token_endpoint=None,
        scope="",
        client_auth_method=None,
    ):
        if (
            not isinstance(client_id, str)
            or not client_id
            or not isinstance(client_secret, str)
            or not client_secret
        ):
            raise ValueError("Client credentials require client_id and client_secret.")
        if not isinstance(scope, str):
            raise TypeError("scope must be a space-separated string.")
        self.client_id, self.client_secret = client_id, client_secret
        self.scope = scope
        self.authorization_endpoint = None
        self._session = requests.Session()
        self._lock = threading.RLock()
        self._token = None
        self._renew_at = None
        try:
            methods = ["client_secret_basic", "client_secret_post"]
            if token_endpoint is None:
                if not issuer:
                    raise ValueError("Supply auth_url (OIDC issuer) or token_endpoint.")
                metadata = self._request(
                    "GET",
                    _url(issuer).rstrip("/") + "/.well-known/openid-configuration",
                )
                if metadata.get("issuer") != issuer:
                    raise RuntimeError("OIDC discovery issuer does not match auth_url.")
                token_endpoint = metadata.get("token_endpoint")
                methods = metadata.get(
                    "token_endpoint_auth_methods_supported", ["client_secret_basic"]
                )
            if not isinstance(methods, list):
                raise TypeError("Invalid OIDC client authentication metadata.")
            self.client_method = client_auth_method or next(
                (
                    m
                    for m in ("client_secret_basic", "client_secret_post")
                    if m in methods
                ),
                None,
            )
            if (
                self.client_method not in {"client_secret_basic", "client_secret_post"}
                or self.client_method not in methods
            ):
                raise ValueError("Unsupported client authentication method.")
            self.token_endpoint = _url(token_endpoint)
            self.get_token()
        except BaseException:
            self.close()
            raise

    def _request(self, method, url, **kwargs):
        deadline = getattr(self, "_worker_deadline", None)
        timeout = 30 if deadline is None else min(30, deadline - time.monotonic())
        if timeout <= 0:
            raise RuntimeError("Worker authentication deadline exceeded.")
        try:
            with self._session.request(
                method, url, timeout=timeout, allow_redirects=False, **kwargs
            ) as response:
                if not 200 <= response.status_code < 300:
                    raise RuntimeError(
                        "OAuth endpoint rejected the request or redirected."
                    )
                payload = response.json()
                if not isinstance(payload, dict) or "error" in payload:
                    raise RuntimeError("OAuth endpoint returned an invalid response.")
                return payload
        except (requests.RequestException, ValueError):
            raise RuntimeError(
                "OAuth endpoint unavailable or returned invalid JSON."
            ) from None

    def get_token(self, rejected=None):
        with self._lock:
            if (
                self._token
                and self._token != rejected
                and (self._renew_at is None or time.monotonic() < self._renew_at)
            ):
                return self._token
            data = {"grant_type": "client_credentials"}
            if self.scope:
                data["scope"] = self.scope
            kwargs = {}
            if self.client_method == "client_secret_basic":
                kwargs["auth"] = (
                    quote_plus(self.client_id),
                    quote_plus(self.client_secret),
                )
            else:
                data.update(client_id=self.client_id, client_secret=self.client_secret)
            started = time.monotonic()
            payload = self._request("POST", self.token_endpoint, data=data, **kwargs)
            token = payload.get("access_token")
            if (
                not isinstance(token, str)
                or not token
                or any(c.isspace() for c in token)
                or str(payload.get("token_type", "")).lower() != "bearer"
            ):
                raise RuntimeError("Provider did not return a Bearer access token.")
            lifetime = (
                _positive(payload["expires_in"]) if "expires_in" in payload else None
            )
            self._renew_at = started + 0.75 * lifetime if lifetime else None
            self._token = token
            return token

    def close(self):
        self._session.close()

    def __getstate__(self):
        return {
            k: v for k, v in self.__dict__.items() if k not in {"_session", "_lock"}
        }

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._session = requests.Session()
        self._lock = threading.RLock()
