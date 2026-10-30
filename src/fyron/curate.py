"""Launcher for the Fyron image curation web app."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import webbrowser
from pathlib import Path

from fyron.console import console_message

DEFAULT_URL = "http://localhost:5174/"


def default_app_dir() -> Path:
    """Return the best available path for the bundled image curator app."""
    package_dir = Path(__file__).resolve().parent / "apps" / "image-curator"
    if (package_dir / "docker-compose.yml").exists():
        return package_dir

    source_dir = Path(__file__).resolve().parents[2] / "apps" / "image-curator"
    if (source_dir / "docker-compose.yml").exists():
        return source_dir

    return package_dir


def build_compose_command(*, build: bool = True, detached: bool = True) -> list[str]:
    """Build the Docker Compose command used to run the curator stack.

    Parameters
    ----------
    build
        Whether to include ``--build`` so Docker rebuilds the Curate images.
    detached
        Whether to include ``-d`` so the stack runs in the background.

    Returns
    -------
    list[str]
        Command tokens suitable for :func:`subprocess.run`.
    """
    command = ["docker", "compose", "up"]
    if detached:
        command.append("-d")
    if build:
        command.append("--build")
    return command


def start_curator(
    *,
    app_dir: str | Path | None = None,
    build: bool = True,
    detached: bool = True,
    open_browser: bool = False,
    color: bool = True,
    quiet: bool = False,
) -> int:
    """Start the local Fyron image curator Docker Compose app.

    Parameters
    ----------
    app_dir
        Optional path to an ``apps/image-curator`` directory. When omitted,
        Fyron uses the bundled app from the installed package or source tree.
    build
        Whether Docker Compose should rebuild service images.
    detached
        Whether Docker Compose should run the stack in the background.
    open_browser
        Whether to open the local Curate URL in the default browser.
    color
        Whether status messages may use ANSI color.
    quiet
        Whether to suppress nonessential status messages.

    Returns
    -------
    int
        Process-style exit code, where ``0`` means Curate started.
    """
    root = Path(app_dir).expanduser().resolve() if app_dir else default_app_dir()
    compose_file = root / "docker-compose.yml"
    if not compose_file.exists():
        raise SystemExit(
            f"Could not find the Fyron curator app at {root}. "
            'Install with `fyron[curate]`, run from a Fyron source checkout, or pass --app-dir.'
        )
    if shutil.which("docker") is None:
        if not quiet:
            console_message(
                "Docker Desktop / Docker Compose is required to start Fyron Curate.",
                level="error",
                color=color,
            )
        return 127

    command = build_compose_command(build=build, detached=detached)
    if not quiet:
        console_message(
            f"Starting Fyron Curate from {root}",
            level="info",
            color=color,
        )
    try:
        completed = subprocess.run(command, cwd=root, check=False)
    except FileNotFoundError:
        if not quiet:
            console_message(
                "Docker Desktop / Docker Compose is required to start Fyron Curate.",
                level="error",
                color=color,
            )
        return 127
    if completed.returncode != 0:
        return int(completed.returncode)

    if open_browser:
        webbrowser.open(DEFAULT_URL)
    if not quiet:
        console_message(
            f"Fyron Curate is available at {DEFAULT_URL}",
            level="success",
            color=color,
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Console entry point for the standalone ``curate`` command."""
    parser = argparse.ArgumentParser(prog="curate", description="Start the Fyron image curation web app")
    parser.add_argument("--app-dir", help="Path to apps/image-curator when running outside a Fyron source checkout")
    parser.add_argument("--no-build", action="store_true", help="Start without rebuilding Docker images")
    parser.add_argument("--foreground", action="store_true", help="Run Docker Compose in the foreground")
    parser.add_argument("--open", action="store_true", help="Open the app URL in the default browser")
    parser.add_argument("--quiet", action="store_true", help="Suppress Fyron status messages")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    args = parser.parse_args(argv)
    return start_curator(
        app_dir=args.app_dir,
        build=not args.no_build,
        detached=not args.foreground,
        open_browser=args.open,
        color=not args.no_color,
        quiet=args.quiet,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
