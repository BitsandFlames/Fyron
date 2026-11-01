from __future__ import annotations

import subprocess
import sys
import zipfile
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_release_readiness",
    ROOT / "scripts/check_release_readiness.py",
)
assert SPEC and SPEC.loader
readiness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = readiness
SPEC.loader.exec_module(readiness)


def test_curate_local_artifact_paths_are_git_ignored() -> None:
    for path in [
        ".env",
        "output/release-audit/findings.json",
        ".venv/pyvenv.cfg",
        "site/index.html",
        "dist/fyron-0.0.0-py3-none-any.whl",
        "apps/image-curator/backend/node_modules/.release-check",
        "apps/image-curator/frontend/node_modules/.release-check",
        "apps/image-curator/frontend/dist/.release-check",
        "apps/image-curator/backend/data/.release-check",
        "apps/image-curator/frontend/.vite/.release-check",
        "apps/image-curator/backend/.env",
        "apps/image-curator/frontend/.env.local",
        "apps/image-curator/backend/uploads/image.png",
        "apps/image-curator/backend/exports/clean/image.png",
        "apps/image-curator/postgres_data/.release-check",
        "apps/image-curator/backend/local.sqlite",
    ]:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0, path


def test_release_readiness_detects_blocked_package_paths(tmp_path: Path, monkeypatch) -> None:
    archive = tmp_path / "fyron-0.0.0-py3-none-any.whl"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("fyron/apps/image-curator/docker-compose.yml", "services: {}\n")
        package.writestr("fyron/apps/image-curator/backend/package.json", "{}\n")
        package.writestr("fyron/apps/image-curator/frontend/package.json", "{}\n")
        package.writestr("fyron/apps/image-curator/backend/prisma/schema.prisma", "// schema\n")
        package.writestr("fyron/apps/image-curator/frontend/node_modules/pkg/index.js", "")
        package.writestr("fyron/output/local-audit.txt", "synthetic")

    monkeypatch.setattr(readiness, "ROOT", tmp_path)
    result = readiness.check_package_archives(tmp_path)

    assert not result.ok
    assert "node_modules" in result.detail
    assert "output" in result.detail


def test_release_readiness_detects_workbench_package_paths(tmp_path: Path, monkeypatch) -> None:
    archive = tmp_path / "fyron-0.0.0-py3-none-any.whl"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("fyron/apps/image-curator/docker-compose.yml", "services: {}\n")
        package.writestr("fyron/apps/image-curator/backend/package.json", "{}\n")
        package.writestr("fyron/apps/image-curator/frontend/package.json", "{}\n")
        package.writestr("fyron/apps/image-curator/backend/prisma/schema.prisma", "// schema\n")
        package.writestr("fyron/apps/research-workbench/package.json", "{}\n")

    monkeypatch.setattr(readiness, "ROOT", tmp_path)
    result = readiness.check_package_archives(tmp_path)

    assert not result.ok
    assert "research-workbench" in result.detail


def test_release_readiness_pages_workflow_gate(tmp_path: Path, monkeypatch) -> None:
    workflow = tmp_path / ".github" / "workflows" / "pages.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        """
permissions:
  pages: write
  id-token: write
jobs:
  build:
    steps:
      - run: uv run python scripts/build_docs.py
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
  deploy:
    steps:
      - uses: actions/deploy-pages@v4
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(readiness, "ROOT", tmp_path)
    result = readiness.check_pages_workflow()

    assert result.ok


def test_release_readiness_pages_workflow_can_be_disabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(readiness, "ROOT", tmp_path)

    result = readiness.check_pages_workflow()

    assert result.ok
    assert "disabled" in result.detail


def test_release_readiness_built_site_link_gate(tmp_path: Path, monkeypatch) -> None:
    site = tmp_path / "site"
    (site / "assets").mkdir(parents=True)
    (site / "assets" / "style.css").write_text("body{}\n", encoding="utf-8")
    (site / "index.html").write_text(
        '<link rel="stylesheet" href="assets/style.css"><a href="guide.md">bad</a>',
        encoding="utf-8",
    )

    monkeypatch.setattr(readiness, "ROOT", tmp_path)
    result = readiness.check_built_site_links()

    assert not result.ok
    assert "raw markdown" in result.detail


def test_release_readiness_detects_private_institution_urls(tmp_path: Path, monkeypatch) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "bad.md").write_text(
        "Do not publish https://hospital-internal.example.org/HIS in public docs.\n",
        encoding="utf-8",
    )
    (docs / "ok.md").write_text(
        "Synthetic endpoints such as https://example.org/fhir are fine.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(readiness, "ROOT", tmp_path)
    result = readiness.check_public_safety()

    assert not result.ok
    assert "private_institution_url" in result.detail
    assert "bad.md" in result.detail


def test_release_readiness_skip_modes_run_without_dist() -> None:
    script = ROOT / "scripts/check_release_readiness.py"
    result = subprocess.run(
        [sys.executable, str(script), "--skip-git-clean", "--skip-package"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "public_safety_scan" in result.stdout
