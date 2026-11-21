"""Bounded text extraction shared by document workflows."""

import subprocess
import threading
from pathlib import Path


class TextFailure(ValueError):
    """A controlled reason for an unusable document."""


def _pdf_text(path, limit, timeout):
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise TextFailure("decoding_failed")
    try:
        process = subprocess.Popen(
            ["pdftotext", "-enc", "UTF-8", str(path.resolve()), "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            text=True, encoding="utf-8",
        )
    except FileNotFoundError:
        raise TextFailure("pdf_converter_unavailable") from None

    expired = threading.Event()

    def expire():
        expired.set()
        process.kill()

    with process:
        timer = threading.Timer(timeout, expire)
        timer.start()
        try:
            text = process.stdout.read(limit + 1)
            if len(text) > limit:
                raise TextFailure("extracted_text_too_large")
            status = process.wait()
            if expired.is_set():
                raise TextFailure("pdf_conversion_timeout")
            if status:
                raise TextFailure("decoding_failed")
            return text
        finally:
            timer.cancel()
            timer.join()
            if process.poll() is None:
                process.kill()


def extract_text(path, media_type, *, charset="utf-8-sig", limit, timeout=60):
    path = Path(path)
    try:
        if media_type == "text/plain":
            with path.open(encoding=charset) as stream:
                text = stream.read(limit + 1)
        elif media_type == "application/pdf":
            text = _pdf_text(path, limit, timeout)
        else:
            raise TextFailure("unsupported_media_type")
    except (OSError, UnicodeError, LookupError):
        raise TextFailure("decoding_failed") from None
    if len(text) > limit:
        raise TextFailure("extracted_text_too_large")
    if not text.strip():
        raise TextFailure("empty_text")
    return text
