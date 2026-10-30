"""Terminal banner utilities for Fyron."""

from __future__ import annotations

import sys
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import TextIO


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
FG_PURPLE = "\033[38;2;61;50;103m"
FG_ORANGE = "\033[38;2;255;106;26m"
FG_YELLOW = "\033[38;2;255;190;25m"
BG_PURPLE = "\033[48;2;61;50;103m"
BG_ORANGE = "\033[48;2;255;106;26m"
BG_DEEP_ORANGE = "\033[48;2;255;82;34m"
BG_YELLOW = "\033[48;2;255;190;25m"

_BF_WORDMARK = (
    "██████╗ ███████╗",
    "██╔══██╗██╔════╝",
    "██████╔╝█████╗  ",
    "██╔══██╗██╔══╝  ",
    "██████╔╝██║     ",
    "╚═════╝ ╚═╝     ",
)

_BF_WORDMARK_PLAIN = (
    "BBBBBB  FFFFFFF",
    "B    B  F",
    "BBBBBB  FFFFF",
    "B    B  F",
    "BBBBBB  F",
)

_GRADIENT = (
    "\033[38;2;255;214;64m",
    "\033[38;2;255;188;44m",
    "\033[38;2;255;158;31m",
    "\033[38;2;255;128;26m",
    "\033[38;2;255;96;22m",
)
_SHADOW = "\033[38;2;92;61;44m"


def _gradient_line(line: str, row_index: int) -> str:
    colored = []
    visible_index = 0

    for character in line:
        if character == " ":
            colored.append(character)
            continue
        color = _GRADIENT[min((visible_index + row_index) // 5, len(_GRADIENT) - 1)]
        colored.append(f"{color}{character}{RESET}")
        visible_index += 1

    return "".join(colored)


def _render_wordmark(*, color: bool, theme: str = "bf") -> str:
    if theme not in {"bf", "plain", "mono"}:
        raise ValueError("theme must be one of: bf, plain, mono")
    if not color or theme in {"plain", "mono"}:
        title = "Bits & Flames - Fyron" if theme != "mono" else "FYRON"
        return "\n".join(
            [
                *_BF_WORDMARK_PLAIN,
                "",
                title,
                "Built by bits. Shaped by flames." if theme != "mono" else "Interoperable clinical data science.",
            ]
        )

    lines = []
    for row_index, line in enumerate(_BF_WORDMARK):
        foreground = _gradient_line(line, row_index)
        shadow = f"{_SHADOW}  {line}{RESET}"
        lines.append(f"{foreground}{shadow}")

    lines.extend(
        [
            "",
            f"{BOLD}{FG_ORANGE}Bits & Flames{RESET}  {FG_YELLOW}|{RESET}  {BOLD}{FG_YELLOW}Fyron{RESET}",
            f"{DIM}{FG_PURPLE}Built by bits. Shaped by flames.{RESET}",
        ]
    )
    return "\n".join(lines)


BF_FYRON_ASCII = _render_wordmark(color=False)


def _installed_version() -> str:
    try:
        return package_version("fyron")
    except PackageNotFoundError:
        return "0.3.20b4"


def get_banner(
    version: str | None = None,
    *,
    include_version: bool = True,
    color: bool = True,
    theme: str = "bf",
) -> str:
    """Return the Bits & Flames Fyron terminal banner.

    Parameters
    ----------
    version:
        Optional version label. If omitted, the installed package version is used.
    include_version:
        Append a version line below the banner when ``True``.
    color:
        Render the pixel logo with ANSI colors when ``True``.
    theme:
        Terminal theme: ``"bf"`` for the colored Bits & Flames wordmark,
        ``"plain"`` for ASCII logs, or ``"mono"`` for minimal monochrome output.
    """

    banner = _render_wordmark(color=color, theme=theme)
    if not include_version:
        return banner

    resolved_version = version or _installed_version()
    version_prefix = f"{DIM}{FG_PURPLE}" if color else ""
    version_suffix = RESET if color else ""
    return f"{banner}\n{version_prefix}version {resolved_version}{version_suffix}"


def print_banner(
    version: str | None = None,
    *,
    include_version: bool = True,
    color: bool = True,
    theme: str = "bf",
    file: TextIO | None = None,
) -> None:
    """Print the Bits & Flames Fyron terminal banner to a text stream."""

    print(
        get_banner(version=version, include_version=include_version, color=color, theme=theme),
        file=file or sys.stdout,
    )


def get_run_header(
    command: str | None = None,
    *,
    version: bool = True,
    timestamp: bool = True,
    color: bool = True,
) -> str:
    """Return a compact Fyron run header for scripts and CLI jobs."""
    parts = [f"{BOLD}{FG_ORANGE}Fyron{RESET}" if color else "Fyron"]
    if command:
        parts.append(str(command))
    if version:
        parts.append(f"version {_installed_version()}")
    if timestamp:
        parts.append(datetime.now().isoformat(timespec="seconds"))
    return " | ".join(parts)


def get_run_footer(
    status: str = "success",
    *,
    duration: float | None = None,
    outputs: list[str | Path] | tuple[str | Path, ...] | None = None,
    color: bool = True,
) -> str:
    """Return a compact Fyron run footer."""
    status_text = status.upper()
    if color:
        status_text = f"{FG_YELLOW}{status_text}{RESET}" if status == "success" else f"{FG_ORANGE}{status_text}{RESET}"
    parts = [f"Fyron {status_text}"]
    if duration is not None:
        parts.append(f"duration {duration:.2f}s")
    if outputs:
        parts.append("outputs " + ", ".join(str(path) for path in outputs))
    return " | ".join(parts)


def main() -> None:
    """CLI entry point for ``python -m fyron.banner``."""

    print_banner()


if __name__ == "__main__":
    main()
