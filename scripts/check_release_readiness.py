#!/usr/bin/env python3
"""Audit Fyron release hygiene before a public beta or stable release."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PACKAGE_PARTS = {
    "output",
    "node_modules",
    "dist",
    "dist-electron",
    "release",
    "out",
    ".vite",
    "uploads",
    "exports",
    "projects",
    "postgres_data",
    "__pycache__",
}
BLOCKED_PACKAGE_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pyc", ".pyo"}
BLOCKED_WORKBENCH_PATTERNS = (
    re.compile(r"workbench", re.IGNORECASE),
    re.compile(r"research-workbench", re.IGNORECASE),
    re.compile(r"fyron-workbench", re.IGNORECASE),
)
PUBLIC_SAFETY_PATTERNS = [
    ("private_user_path", re.compile(r"/(?:Users|home)/[^/\s]+/(?:Downloads|Desktop|Documents)|/local/work/[^/\s]+")),
    ("temporary_capture_path", re.compile(r"/var/folders/|/private/tmp/|TemporaryItems")),
    ("secret_assignment", re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]")),
    ("placeholder_private_token", re.compile(r"(?i)(YOUR_PYPI_TOKEN|YOUR_TESTPYPI_TOKEN)")),
    ("patient_like_identifier", re.compile(r"(?i)\b(patient[\s_-]+(name|dob|birth|address)|mrn|social security)\b")),
    (
        "private_institution_url",
        re.compile(r"(?i)https?://[^`\"')\s<>{}]*\b(?:medico|intranet|his[-.]|hospital-internal|\.corp|\.local)\b"),
    ),
]
TEXT_SUFFIXES = {
    ".cff",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}
SAFETY_EXCLUDE_PARTS = {
    "output",
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "site",
    "dist",
    "__pycache__",
}
WORKBENCH_ABSENCE_EXCLUDE_PARTS = SAFETY_EXCLUDE_PARTS | {
    "apps",
    "tests",
}
SAFETY_ALLOWLIST = {
    ("placeholder_private_token", "release.MD"),
    ("placeholder_private_token", "release.md"),
    ("patient_like_identifier", "SECURITY.md"),
    ("patient_like_identifier", "CONTRIBUTING.md"),
    ("patient_like_identifier", ".github/PULL_REQUEST_TEMPLATE.md"),
    ("patient_like_identifier", ".github/ISSUE_TEMPLATE/bug_report.md"),
}
SAFETY_ALLOWLIST_PREFIXES = (
    "tests/",
    "scripts/check_release_readiness.py",
)


class LinkParser(HTMLParser):
    """Collect href/src references from generated HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.refs.append((name, value))


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_release_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & SAFETY_EXCLUDE_PARTS:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def check_worktree_clean() -> CheckResult:
    status = run_git(["status", "--short"])
    if status.returncode != 0:
        return CheckResult("git_status", False, status.stderr.strip() or "git status failed")
    lines = [line for line in status.stdout.splitlines() if line.strip()]
    if not lines:
        return CheckResult("git_status", True, "working tree is clean")
    return CheckResult("git_status", False, f"{len(lines)} pending path(s); commit or intentionally ignore before tagging")


def check_ignored_artifacts() -> CheckResult:
    probes = [
        ".env",
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
    ]
    bad: list[str] = []
    for probe in probes:
        proc = run_git(["check-ignore", "-q", probe])
        if proc.returncode != 0:
            bad.append(probe)
    if bad:
        return CheckResult("ignored_artifacts", False, "not ignored: " + ", ".join(bad))
    return CheckResult("ignored_artifacts", True, "local build, env, and Curate artifacts are ignored")


def check_workbench_absent() -> CheckResult:
    """Ensure the postponed Workbench app is not part of the current release tree."""
    forbidden_paths = [
        ROOT / "apps" / "research-workbench",
        ROOT / "src" / "fyron" / "workbench.py",
        ROOT / "tests" / "test_workbench.py",
        ROOT / "docs" / "research-workbench.md",
    ]
    present = [relative(path) for path in forbidden_paths if path.exists()]
    findings: list[str] = present.copy()
    for path in iter_release_text_files():
        rel = relative(path)
        if rel.startswith("site/"):
            continue
        if rel == "scripts/check_release_readiness.py":
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & WORKBENCH_ABSENCE_EXCLUDE_PARTS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in BLOCKED_WORKBENCH_PATTERNS:
            if pattern.search(text):
                findings.append(rel)
                break
    if findings:
        return CheckResult("workbench_absent", False, "Workbench release references found: " + ", ".join(findings[:12]))
    return CheckResult("workbench_absent", True, "Workbench is absent from release-facing source and docs")


def check_package_archives(dist_dir: Path) -> CheckResult:
    archives = sorted(dist_dir.glob("fyron-*"))
    if not archives:
        return CheckResult("package_archives", False, f"no fyron archives found in {relative(dist_dir)}")

    blocked: list[str] = []
    required = {
        "fyron/apps/image-curator/docker-compose.yml": False,
        "fyron/apps/image-curator/backend/package.json": False,
        "fyron/apps/image-curator/frontend/package.json": False,
        "fyron/apps/image-curator/backend/prisma/schema.prisma": False,
    }
    for archive in archives:
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive) as package:
                names = package.namelist()
        elif archive.name.endswith(".tar.gz"):
            import tarfile

            with tarfile.open(archive) as package:
                names = package.getnames()
        else:
            continue
        for name in names:
            parts = set(Path(name).parts)
            suffix = Path(name).suffix.lower()
            if parts & BLOCKED_PACKAGE_PARTS or suffix in BLOCKED_PACKAGE_SUFFIXES:
                blocked.append(f"{archive.name}:{name}")
            if any(pattern.search(name) for pattern in BLOCKED_WORKBENCH_PATTERNS):
                blocked.append(f"{archive.name}:{name}")
            for required_name in required:
                if name.endswith(required_name) or name == required_name:
                    required[required_name] = True
    missing = [name for name, present in required.items() if not present]
    if blocked or missing:
        details = []
        if blocked:
            details.append("blocked package paths: " + ", ".join(blocked[:8]))
        if missing:
            details.append("missing Curate paths: " + ", ".join(missing))
        return CheckResult("package_archives", False, "; ".join(details))
    return CheckResult("package_archives", True, f"checked {len(archives)} archive(s)")


def check_pages_workflow() -> CheckResult:
    """Confirm GitHub Pages deployment is absent or correctly configured."""
    docs_workflow = ROOT / ".github" / "workflows" / "pages.yml"
    if not docs_workflow.exists():
        return CheckResult("pages_workflow", True, "GitHub Pages deployment workflow is disabled")
    text = docs_workflow.read_text(encoding="utf-8")
    required = [
        "pages: write",
        "id-token: write",
        "scripts/build_docs.py",
        "actions/configure-pages",
        "actions/upload-pages-artifact",
        "path: site",
        "actions/deploy-pages",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        return CheckResult("pages_workflow", False, "missing Pages workflow pieces: " + ", ".join(missing))
    return CheckResult("pages_workflow", True, "GitHub Pages workflow builds and deploys site/")


def _is_external_ref(ref: str) -> bool:
    return ref.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:"))


def _target_path(html_file: Path, ref: str) -> Path:
    clean = ref.split("#", 1)[0].split("?", 1)[0]
    if clean.startswith("/"):
        return ROOT / "site" / clean.lstrip("/")
    return (html_file.parent / clean).resolve()


def check_built_site_links() -> CheckResult:
    """Check generated site links for raw Markdown URLs and missing local assets."""
    site = ROOT / "site"
    if not site.exists():
        return CheckResult("built_site_links", False, "site/ is missing; run scripts/build_docs.py before release")
    problems: list[str] = []
    for html_file in site.rglob("*.html"):
        parser = LinkParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        rel_html = relative(html_file)
        for attr, ref in parser.refs:
            if _is_external_ref(ref):
                continue
            clean = ref.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            if clean.endswith(".md"):
                problems.append(f"{rel_html}:{attr} points to raw markdown {ref}")
                continue
            target = _target_path(html_file, ref)
            if clean.endswith("/"):
                target = target / "index.html"
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                problems.append(f"{rel_html}:{attr} missing target {ref}")
    if problems:
        return CheckResult("built_site_links", False, "; ".join(problems[:12]))
    return CheckResult("built_site_links", True, "generated site has no raw Markdown links or missing local targets")


def check_public_safety() -> CheckResult:
    findings: list[str] = []
    for path in iter_release_text_files():
        rel = relative(path)
        if rel in SAFETY_ALLOWLIST_PREFIXES or rel.startswith(SAFETY_ALLOWLIST_PREFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in PUBLIC_SAFETY_PATTERNS:
            if (name, rel) in SAFETY_ALLOWLIST:
                continue
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{rel}:{line}:{name}")
                break
    if findings:
        return CheckResult("public_safety_scan", False, "; ".join(findings[:12]))
    return CheckResult("public_safety_scan", True, "no blocking public-safety patterns found")


def check_version_alignment() -> CheckResult:
    pyproject = ROOT / "pyproject.toml"
    citation = ROOT / "CITATION.cff"
    init_file = ROOT / "src/fyron/__init__.py"
    banner_file = ROOT / "src/fyron/banner.py"
    version_match = re.search(r'^version = "([^"]+)"', pyproject.read_text(), re.MULTILINE)
    citation_match = re.search(r'^version: "([^"]+)"', citation.read_text(), re.MULTILINE)
    if not version_match or not citation_match:
        return CheckResult("version_alignment", False, "could not read pyproject/CITATION version")
    version = version_match.group(1)
    mismatches = []
    if citation_match.group(1) != version:
        mismatches.append("CITATION.cff")
    for file in [init_file, banner_file]:
        if f'return "{version}"' not in file.read_text():
            mismatches.append(relative(file))
    if mismatches:
        return CheckResult("version_alignment", False, f"{version} not aligned in: {', '.join(mismatches)}")
    return CheckResult("version_alignment", True, f"version {version} aligned")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", default="dist", help="Directory containing built wheel/sdist archives.")
    parser.add_argument("--skip-git-clean", action="store_true", help="Do not fail on a dirty working tree.")
    parser.add_argument("--skip-package", action="store_true", help="Do not inspect built package archives.")
    args = parser.parse_args(argv)

    checks = [
        check_ignored_artifacts(),
        check_workbench_absent(),
        check_public_safety(),
        check_version_alignment(),
        check_pages_workflow(),
        check_built_site_links(),
    ]
    if not args.skip_git_clean:
        checks.insert(0, check_worktree_clean())
    if not args.skip_package:
        checks.append(check_package_archives(ROOT / args.dist_dir))

    failed = False
    for result in checks:
        icon = "OK" if result.ok else "FAIL"
        print(f"[{icon}] {result.name}: {result.detail}")
        failed = failed or not result.ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
