"""Exercise an installed wheel in a disposable environment outside the checkout."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(command, *, cwd):
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        env.pop(name, None)
    for name in list(env):
        if name.startswith(("FHIR_", "DICOM_", "OAUTH_", "OIDC_", "AWS_", "S3_", "OPENAI_")):
            env.pop(name)
    env.update(MPLBACKEND="Agg", MPLCONFIGDIR=str(cwd / "mpl"))
    subprocess.run(command, cwd=cwd, env=env, check=True)


def check(wheel, extra="base", platform_tests=False, radiomics_build_workaround=False):
    wheel = Path(wheel).resolve()
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise ValueError("Provide one existing wheel file.")
    with tempfile.TemporaryDirectory(prefix="fyron-wheel-") as directory:
        work = Path(directory)
        environment = work / "venv"
        run(["uv", "venv", "--python", sys.executable, str(environment)], cwd=work)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        requirement = str(wheel) + (f"[{extra}]" if extra != "base" else "")
        command = ["uv", "pip", "install", "--python", str(python), requirement]
        if radiomics_build_workaround:
            if extra not in {"radiomics", "all"} or sys.version_info >= (3, 12):
                raise ValueError("The radiomics build workaround is only for radiomics/all on Python <3.12.")
            config = work / "radiomics-uv.toml"
            config.write_text('[extra-build-dependencies]\npyradiomics = ["numpy<2"]\n')
            command.extend(["--config-file", str(config)])
            print("Explicit PyRadiomics build-only NumPy workaround enabled; not a bare-install check.", flush=True)
        if platform_tests:
            command.append("pytest>=9.1.1,<10")
        run(command, cwd=work)
        probe = work / "wheel_probe.py"
        shutil.copy2(ROOT / "scripts/wheel_probe.py", probe)
        run([str(python), "-I", str(probe), extra], cwd=work)
        for name in ["ingestion_workflow", "research_contracts"] + (["survival_workflow"] if extra in {"survival-ml", "all"} else []):
            script = work / f"{name}.py"
            shutil.copy2(ROOT / "examples" / f"{name}.py", script)
            run([str(python), "-I", str(script), "--output-dir", str(work / name)], cwd=work)
        if platform_tests:
            tests = work / "tests"
            tests.mkdir()
            # Do not copy the repository conftest: base environments lack Matplotlib.
            for name in ("test_worker_coordination.py", "test_storage_recovery.py", "test_platform_contracts.py"):
                shutil.copy2(ROOT / "tests" / name, tests / name)
            # S3 has its own isolated extra probe; it is not part of base coverage.
            run([str(python), "-I", "-m", "pytest", str(tests), "-q", "-k", "not s3"], cwd=work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--extra", default="base")
    parser.add_argument("--platform-tests", action="store_true")
    parser.add_argument("--radiomics-build-workaround", action="store_true")
    args = parser.parse_args()
    check(args.wheel, args.extra, args.platform_tests, args.radiomics_build_workaround)


if __name__ == "__main__":
    main()
