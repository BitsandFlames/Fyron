"""Prepare URL-backed evidence for text prompt workflows."""

from contextlib import ExitStack
from email.message import Message
from hashlib import sha256
from pathlib import Path
from ..documents._text import extract_text, TextFailure
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

import requests

from ..documents import DocumentDownloader
from ..fhir.auth import Auth


def _origin(url):
    if not isinstance(url, str) or not url or "\\" in url or any(c.isspace() or ord(c) < 32 for c in url):
        raise ValueError("Expected an absolute HTTP(S) document URL.")
    parsed = urlsplit(url)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("Expected an absolute HTTP(S) document URL without credentials.")
    return parsed.scheme, parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)


def _read(result, limit):
    if result.error or result.status_code != 200:
        raise TextFailure(getattr(result, "reason", None) or "download_failed")
    header = Message()
    header["Content-Type"] = result.content_type or "application/octet-stream"
    return extract_text(result.path, header.get_content_type(), limit=limit,
                        charset=header.get_content_charset() or "utf-8-sig")


def _prepare(df, url_col, *, auth, origin, selected, max_download_bytes, max_extracted_chars):
    if auth is not None and not isinstance(auth, (Auth, requests.Session)):
        raise TypeError("document_auth requires Auth or a requests.Session.")
    allowed = _origin(origin) if origin is not None else None
    if auth is not None and (allowed is None or allowed[0] != "https"):
        raise ValueError("Authenticated document requests require an explicit HTTPS document_origin.")
    urls = df[url_col].tolist()
    for url in urls:
        actual = _origin(url)
        if allowed and actual != allowed:
            raise ValueError("Document URL outside configured document_origin.")
    cache = {}
    with ExitStack() as stack:
        directory = stack.enter_context(TemporaryDirectory(prefix="fyron-llm-"))
        if auth is None:
            auth = stack.enter_context(requests.Session())
            auth.trust_env = False
        loader = stack.enter_context(DocumentDownloader(
            auth=auth, output_dir=directory, allow_redirects=False,
            max_download_bytes=max_download_bytes, write_completion_record=False, expected_content_types=["text/plain", "application/pdf"],
        ))
        for url in dict.fromkeys(df.loc[selected, url_col]):
            try:
                result = loader.download_url(url, output_path=Path(directory) / sha256(url.encode()).hexdigest())
                cache[url] = _read(result, max_extracted_chars)
            except TextFailure as exc:
                cache[url] = TextFailure(str(exc))
            except (OSError, ValueError, requests.RequestException):
                cache[url] = TextFailure("download_failed")
    return [cache.get(url) for url in urls]
