"""Shared redirect boundary for requests-based research clients."""

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
