#!/usr/bin/env python3
"""Install the Fyron agent skill for Codex, Claude, or Cursor.

The installer is intentionally local and dependency-free. It copies the shared
Fyron skill files into the shape expected by the selected assistant surface:

- Codex: a skill folder under ``~/.codex/skills/fyron``.
- Claude: project-local ``CLAUDE.md`` guidance, a ``.claude/fyron-skill`` copy,
  and a single Markdown bundle suitable for Claude Project knowledge.
- Cursor: project-local ``.cursor/rules`` files.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SKILL = ROOT / "SKILL.md"
REFERENCES = ROOT / "references"

CLAUDE_BLOCK_START = "<!-- FYRON_SKILL_START -->"
CLAUDE_BLOCK_END = "<!-- FYRON_SKILL_END -->"


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"),
    )


def _read_references() -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    for path in sorted(REFERENCES.glob("*.md")):
        references.append((path.name, path.read_text(encoding="utf-8")))
    return references


def _skill_body_without_frontmatter() -> str:
    text = SKILL.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()


def install_codex(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    _copy_tree(ROOT, destination)
    return destination


def _claude_block() -> str:
    return f"""{CLAUDE_BLOCK_START}
# Fyron Skill

Use Fyron for clinical data science workflows. Prefer public APIs from
`fyron.fhir`, `fyron.dicom`, `fyron.imaging`, `fyron.cohort`,
`fyron.statistics`, `fyron.survival`, `fyron.ml`, `fyron.validation`,
`fyron.plotting`, `fyron.visualization`, and `fyron.audit`.

Keep examples synthetic or de-identified. Do not send PHI, private endpoint
responses, credentials, accessions, MRNs, or patient-linked dates to external
LLMs. Use the local `.claude/fyron-skill/` folder and
`fyron-claude-project-knowledge.md` as the project knowledge source.

Public docs: https://fyron.bitsandflames.ai
{CLAUDE_BLOCK_END}
"""


def install_claude(project_dir: Path) -> tuple[Path, Path, Path]:
    project_dir.mkdir(parents=True, exist_ok=True)
    skill_dest = project_dir / ".claude" / "fyron-skill"
    _copy_tree(ROOT, skill_dest)

    bundle = project_dir / "fyron-claude-project-knowledge.md"
    parts = [
        "# Fyron Claude Project Knowledge",
        "",
        "Use this file as Claude Project knowledge when a project cannot read a skill folder directly.",
        "",
        "## Main Skill",
        "",
        _skill_body_without_frontmatter(),
    ]
    for name, content in _read_references():
        parts.extend(["", f"## Reference: {name}", "", content.strip()])
    bundle.write_text("\n".join(parts).strip() + "\n", encoding="utf-8")

    claude_md = project_dir / "CLAUDE.md"
    block = _claude_block()
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        if CLAUDE_BLOCK_START in text and CLAUDE_BLOCK_END in text:
            before, rest = text.split(CLAUDE_BLOCK_START, 1)
            _, after = rest.split(CLAUDE_BLOCK_END, 1)
            text = before.rstrip() + "\n\n" + block + after.lstrip()
        else:
            text = text.rstrip() + "\n\n" + block
    else:
        text = block
    claude_md.write_text(text, encoding="utf-8")
    return claude_md, skill_dest, bundle


def _cursor_rule() -> str:
    body = _skill_body_without_frontmatter()
    return f"""---
description: Fyron clinical data science workflows
globs:
  - "**/*.py"
  - "**/*.ipynb"
  - "**/*.md"
alwaysApply: false
---

{body}

## Cursor References

The compact Fyron references are copied to `.cursor/rules/fyron-references/`.
Use them before writing code for FHIR REST, DICOM/imaging, Curate, plotting,
CLI recipes, install extras, and safety-sensitive clinical workflows.
"""


def install_cursor(project_dir: Path) -> tuple[Path, Path]:
    rules_dir = project_dir / ".cursor" / "rules"
    references_dest = rules_dir / "fyron-references"
    rules_dir.mkdir(parents=True, exist_ok=True)
    _copy_tree(REFERENCES, references_dest)

    rule = rules_dir / "fyron.mdc"
    rule.write_text(_cursor_rule(), encoding="utf-8")
    return rule, references_dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the Fyron skill for Codex, Claude, or Cursor.")
    parser.add_argument(
        "--target",
        choices=("codex", "claude", "cursor", "all"),
        default="codex",
        help="Assistant surface to configure.",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project folder for Claude/Cursor files. Defaults to the current directory.",
    )
    parser.add_argument(
        "--codex-dir",
        type=Path,
        default=Path.home() / ".codex" / "skills" / "fyron",
        help="Codex skill destination. Defaults to ~/.codex/skills/fyron.",
    )
    args = parser.parse_args()

    installed: list[str] = []
    if args.target in {"codex", "all"}:
        installed.append(f"Codex: {install_codex(args.codex_dir)}")
    if args.target in {"claude", "all"}:
        claude_md, skill_dest, bundle = install_claude(args.project_dir)
        installed.append(f"Claude: {claude_md}, {skill_dest}, {bundle}")
    if args.target in {"cursor", "all"}:
        rule, references = install_cursor(args.project_dir)
        installed.append(f"Cursor: {rule}, {references}")

    for item in installed:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

