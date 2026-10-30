"""Console and logging helpers for Fyron."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
FG_PURPLE = "\033[38;2;61;50;103m"
FG_EMBER = "\033[38;2;255;106;26m"
FG_ORANGE = "\033[38;2;255;128;26m"
FG_YELLOW = "\033[38;2;255;190;25m"
FG_RED = "\033[38;2;220;38;38m"

LEVEL_STYLES = {
    "debug": DIM,
    "info": FG_PURPLE,
    "success": FG_YELLOW,
    "warning": FG_ORANGE,
    "error": FG_RED,
}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "fyron_event"):
            payload.update(record.fyron_event)
        return json.dumps(payload, default=str)


class _ColorFormatter(logging.Formatter):
    def __init__(self, *, color: bool) -> None:
        super().__init__("%(asctime)s %(levelname)s %(name)s: %(message)s")
        self.color = color

    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created, timezone.utc).isoformat()

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        if not self.color:
            return text
        level = record.levelname.lower()
        style = LEVEL_STYLES.get("error" if level == "critical" else level, "")
        return f"{style}{text}{RESET}" if style else text


def supports_color(stream: TextIO | None = None) -> bool:
    """Return whether ANSI colors should be emitted for a stream."""
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def configure_logging(
    level: str | int = "INFO",
    *,
    color: bool = True,
    json: bool = False,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Configure root Fyron logging and return the ``fyron`` logger."""
    target = stream or sys.stderr
    logger = logging.getLogger("fyron")
    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False
    handler = logging.StreamHandler(target)
    handler.setFormatter(_JsonFormatter() if json else _ColorFormatter(color=color and supports_color(target)))
    handler.setLevel(level)
    logger.addHandler(handler)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger below the Fyron namespace."""
    if not name:
        return logging.getLogger("fyron")
    return logging.getLogger(name if name.startswith("fyron") else f"fyron.{name}")


def console_message(
    message: str,
    *,
    level: str = "info",
    color: bool = True,
    prefix: str = "fyron",
    stream: TextIO | None = None,
    quiet: bool = False,
) -> str:
    """Print and return a styled terminal message."""
    style = LEVEL_STYLES.get(level, LEVEL_STYLES["info"])
    target = stream or sys.stdout
    label = level.upper() if level != "success" else "OK"
    plain = f"{prefix} {label}: {message}"
    text = f"{style}{prefix}{RESET} {style}{label}:{RESET} {message}" if color and supports_color(target) else plain
    if not quiet:
        print(text, file=target)
    return text


def success(message: str, **kwargs: Any) -> str:
    return console_message(message, level="success", **kwargs)


def warning(message: str, **kwargs: Any) -> str:
    return console_message(message, level="warning", **kwargs)


def error(message: str, **kwargs: Any) -> str:
    return console_message(message, level="error", **kwargs)


def info(message: str, **kwargs: Any) -> str:
    return console_message(message, level="info", **kwargs)


def format_path(path: str | Path) -> str:
    return str(Path(path))


def format_count(label: str, value: int | float) -> str:
    return f"{value:,} {label}"


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)} min {rest:.0f} s"


def get_timer() -> float:
    return time.perf_counter()


__all__ = [
    "configure_logging",
    "console_message",
    "error",
    "format_count",
    "format_duration",
    "format_path",
    "get_logger",
    "get_timer",
    "info",
    "success",
    "supports_color",
    "warning",
]
