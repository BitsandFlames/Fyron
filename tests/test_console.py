"""Tests for Fyron console helpers."""

from __future__ import annotations

import json
from io import StringIO

from fyron.console import (
    configure_logging,
    console_message,
    format_count,
    format_duration,
    supports_color,
)


class TtyStringIO(StringIO):
    def isatty(self) -> bool:
        return True


def test_console_message_uses_and_disables_ansi(monkeypatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")

    stream = TtyStringIO()
    text = console_message("done", level="success", color=True, stream=stream)

    assert "\033[" in text
    assert "\033[" in stream.getvalue()

    plain_stream = TtyStringIO()
    plain = console_message("done", level="success", color=False, stream=plain_stream)
    assert "\033[" not in plain

    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    no_color_stream = TtyStringIO()
    no_color = console_message("done", level="success", color=True, stream=no_color_stream)
    assert "\033[" not in no_color
    assert supports_color(no_color_stream) is False


def test_configure_logging_json_outputs_parseable_records() -> None:
    stream = StringIO()
    logger = configure_logging("INFO", json=True, stream=stream)

    logger.info("hello %s", "fyron")

    payload = json.loads(stream.getvalue())
    assert payload["level"] == "INFO"
    assert payload["logger"] == "fyron"
    assert payload["message"] == "hello fyron"


def test_console_format_helpers() -> None:
    assert format_count("rows", 1200) == "1,200 rows"
    assert format_duration(0.2) == "200 ms"
    assert format_duration(2.25) == "2.2 s"
