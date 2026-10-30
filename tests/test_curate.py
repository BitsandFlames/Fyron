"""Tests for the Fyron Curate app launcher."""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest
from fyron import curate
from fyron.cli import main as fyron_main


def test_curate_launcher_runs_docker_compose(tmp_path, monkeypatch) -> None:
    app_dir = tmp_path / "image-curator"
    app_dir.mkdir()
    (app_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    calls = {}

    def fake_run(command: list[str], *, cwd, check: bool) -> subprocess.CompletedProcess:
        calls["command"] = command
        calls["cwd"] = cwd
        calls["check"] = check
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(curate.subprocess, "run", fake_run)
    monkeypatch.setattr(curate.shutil, "which", lambda command: "/usr/bin/docker" if command == "docker" else None)

    assert curate.start_curator(app_dir=app_dir, build=False, detached=False, quiet=True) == 0
    assert calls == {
        "command": ["docker", "compose", "up"],
        "cwd": app_dir.resolve(),
        "check": False,
    }


def test_curate_cli_command_uses_launcher_options(tmp_path, monkeypatch) -> None:
    app_dir = tmp_path / "image-curator"
    app_dir.mkdir()
    (app_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    calls = {}

    def fake_run(command: list[str], *, cwd, check: bool) -> subprocess.CompletedProcess:
        calls["command"] = command
        calls["cwd"] = cwd
        calls["check"] = check
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(curate.subprocess, "run", fake_run)
    monkeypatch.setattr(curate.shutil, "which", lambda command: "/usr/bin/docker" if command == "docker" else None)

    assert fyron_main(["--quiet", "curate", "--app-dir", str(app_dir), "--no-build", "--foreground"]) == 0
    assert calls["command"] == ["docker", "compose", "up"]
    assert calls["cwd"] == app_dir.resolve()


def test_curate_default_command_builds_detached() -> None:
    assert curate.build_compose_command() == ["docker", "compose", "up", "-d", "--build"]


def test_curate_missing_app_mentions_extra(tmp_path) -> None:
    with pytest.raises(SystemExit) as exc:
        curate.start_curator(app_dir=tmp_path / "missing", quiet=True)
    assert "fyron[curate]" in str(exc.value)
    assert "--app-dir" in str(exc.value)


def test_curate_missing_docker_returns_clear_error(tmp_path, monkeypatch, capsys) -> None:
    app_dir = tmp_path / "image-curator"
    app_dir.mkdir()
    (app_dir / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")

    monkeypatch.setattr(curate.shutil, "which", lambda command: None)

    assert curate.start_curator(app_dir=app_dir, color=False) == 127
    assert "Docker Desktop / Docker Compose is required" in capsys.readouterr().out


def test_curate_extra_and_packaged_app_files_are_in_wheel(tmp_path) -> None:
    artifact = os.environ.get("FYRON_TEST_WHEEL")
    if artifact:
        wheels = [Path(artifact)]
        assert wheels[0].is_file(), "Configured CI wheel artifact is missing"
    else:
        if shutil.which("uv") is None:
            pytest.skip("uv is required for the packaging smoke test")
        repo = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["UV_CACHE_DIR"] = str(tmp_path / "uv-cache")
        result = subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(tmp_path / "dist")],
            cwd=repo, env=env, text=True, capture_output=True, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        wheels = sorted((tmp_path / "dist").glob("fyron-*.whl"))
    assert wheels, "Expected uv build to create a Fyron wheel"
    with zipfile.ZipFile(wheels[-1]) as wheel:
        names = set(wheel.namelist())

    assert "fyron/apps/image-curator/docker-compose.yml" in names
    assert "fyron/apps/image-curator/backend/package.json" in names
    assert "fyron/apps/image-curator/backend/prisma/schema.prisma" in names
    assert "fyron/apps/image-curator/frontend/package.json" in names
    assert "fyron/apps/image-curator/frontend/src/main.jsx" in names
    assert "fyron/apps/image-curator/frontend/public/brand/logo-modern-light.png" in names
    assert any(name.endswith(".dist-info/METADATA") for name in names)
    assert not any("node_modules/" in name for name in names)
    assert not any(name.startswith("fyron/apps/image-curator/frontend/dist/") for name in names)

    metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
    with zipfile.ZipFile(wheels[-1]) as wheel:
        metadata = wheel.read(metadata_name).decode("utf-8")
    assert "Provides-Extra: curate" in metadata
