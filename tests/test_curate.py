"""Curate is standalone; Fyron retains preview preparation."""
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
import pytest
from fyron.cli import main


def test_removed_curate_command():
    with pytest.raises(SystemExit) as exc:
        main(["curate"])
    assert exc.value.code == 2


def test_curate_is_separate_and_previews_remain_in_wheel(tmp_path) -> None:
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

    assert not any("image-curator/" in name for name in names)
    assert "fyron/curate.py" not in names
    assert "fyron/visualization/curate_previews.py" in names
    assert any(name.endswith(".dist-info/METADATA") for name in names)
    assert not any("node_modules/" in name for name in names)
    assert not any(name.startswith("fyron/apps/image-curator/frontend/dist/") for name in names)

    metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
    with zipfile.ZipFile(wheels[-1]) as wheel:
        metadata = wheel.read(metadata_name).decode("utf-8")
    assert "Provides-Extra: curate" not in metadata
    with zipfile.ZipFile(wheels[-1]) as wheel:
        entrypoints = wheel.read(next(n for n in names if n.endswith(".dist-info/entry_points.txt"))).decode()
    assert "\ncurate =" not in entrypoints
