"""Regression checks for installation isolation and documentation gates."""

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_wheel_rejected(tmp_path):
    with pytest.raises(ValueError, match="existing wheel"):
        load("check_wheel").check(tmp_path / "absent.whl")


def test_subprocess_failure_and_environment_isolation(tmp_path, monkeypatch):
    module = load("check_wheel")
    monkeypatch.setenv("PYTHONPATH", str(ROOT / "src"))
    monkeypatch.setenv("VIRTUAL_ENV", "unrelated")
    monkeypatch.setenv("FHIR_AUTH_URL", "https://example.invalid/do-not-call")

    def fail(command, **kwargs):
        assert kwargs["check"] is True
        assert "PYTHONPATH" not in kwargs["env"] and "VIRTUAL_ENV" not in kwargs["env"]
        assert "FHIR_AUTH_URL" not in kwargs["env"]
        raise subprocess.CalledProcessError(19, command)

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError) as error:
        module.run(["false"], cwd=tmp_path)
    assert error.value.returncode == 19


def test_install_failure_cleans_temporary_environment(tmp_path, monkeypatch):
    module = load("check_wheel")
    wheel = tmp_path / "synthetic.whl"
    wheel.touch()
    directories = []

    def fail(command, *, cwd):
        directories.append(cwd)
        raise subprocess.CalledProcessError(2, command)

    monkeypatch.setattr(module, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        module.check(wheel)
    assert directories and not directories[0].exists()


def test_docstring_gate_ratchets(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = load("check_docstrings")
    assert module.compare({"old": "gap"}, {"old": "gap"}) == ({}, [])
    assert module.compare({"new": "gap"}, {}) == ({"new": "gap"}, [])
    assert module.compare({}, {"fixed": "gap"}) == ({}, ["fixed"])
    assert module.compare({"part": "missing parameter descriptions: x"},
                          {"part": "missing parameter descriptions: x, y"}) == ({}, ["part"])


def test_probe_rejects_checkout_import(tmp_path):
    result = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/wheel_probe.py"), "base"],
                            cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode != 0
    assert "Not an installed wheel" in result.stderr


def test_every_extra_has_an_operation():
    try:
        import tomllib
    except ImportError:  # pytest supplies tomli on Python 3.10.
        import tomli as tomllib
    extras = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["optional-dependencies"]
    tree = ast.parse((ROOT / "scripts/wheel_probe.py").read_text())
    cases = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "CASES" for target in node.targets))
    keys = {key.value for key in cases.keys}
    assert set(extras) - {"all"} <= keys


@pytest.mark.parametrize("values", [{"age": [20, 30]}, {"group": ["a", "b"]}, {}])
def test_table_one_handles_single_variable_kind(values):
    import pandas as pd
    from fyron.descriptive import create_table_one
    result = create_table_one(pd.DataFrame(values))
    assert list(result.columns) == ["variable", "level", "group", "summary"]
    assert result.empty == (not values)
