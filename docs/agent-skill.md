# Skills

Fyron can be used as an agent skill for Codex, Claude, Cursor, or any assistant that benefits from compact project knowledge. The skill teaches an assistant which Fyron module to use, how to install extras, how to start Curate, and where the safety boundaries are for clinical research data.

Use this when the assistant should help you create scripts, notebooks, figures, CLI recipes, Curate preview folders, or provenance manifests without guessing where Fyron functions live.

## Download

The docs build publishes a ready-to-copy skill package:

- [Download the Fyron skill zip](assets/fyron-skill.zip)
- [Read SKILL.md](ai/fyron-skill/SKILL.md) in the documentation; the same file is included at `fyron-skill/SKILL.md` in the download.
- Browse compact references such as `fyron-skill/references/module-map.md`

The package contains:

```text
fyron-skill/
  SKILL.md
  install.py
  references/
    module-map.md
    install-extras.md
    cli-recipes.md
    fhir-rest.md
    dicom-imaging.md
    curate.md
    plotting.md
    safety.md
```

## Recommended: Use `uv`

For projects that already use Fyron, prefer `uv` for reproducible installs and commands:

```bash
uv add "fyron[all]"
uv run python fyron-skill/install.py --target codex
uv run python fyron-skill/install.py --target claude --project-dir .
uv run python fyron-skill/install.py --target cursor --project-dir .
```

If you downloaded the skill zip outside a Python project, plain Python is also fine because the installer has no external dependencies:

```bash
python install.py --target codex
```

## Choose Your Assistant

After downloading and unpacking the skill zip, use the included installer:

```bash
python install.py --target codex
python install.py --target claude --project-dir /path/to/project
python install.py --target cursor --project-dir /path/to/project
python install.py --target all --project-dir /path/to/project
```

The targets write different local files:

| Target | What gets created |
| --- | --- |
| `codex` | Native reusable skill at `~/.codex/skills/fyron/` with `SKILL.md` and references |
| `claude` | Project instructions in `CLAUDE.md`, a `.claude/fyron-skill/` copy, and `fyron-claude-project-knowledge.md` for Claude Project knowledge |
| `cursor` | Cursor project rules in `.cursor/rules/fyron.mdc` plus `.cursor/rules/fyron-references/` |
| `all` | all of the above |

Use `codex` when you want Fyron available across Codex tasks. Use `claude` or `cursor` inside the research project folder so the guidance travels with that project.

<div class="bf-docs-grid bf-docs-grid--featured">
  <a class="bf-docs-card" href="#manual-codex-install"><strong>Codex</strong><span>Install once as a native skill and call it with “Use the Fyron skill”.</span></a>
  <a class="bf-docs-card" href="#manual-claude-setup"><strong>Claude</strong><span>Create project knowledge and a CLAUDE.md instruction file for study-specific work.</span></a>
  <a class="bf-docs-card" href="#manual-cursor-setup"><strong>Cursor</strong><span>Add Fyron as project rules with compact references for code generation.</span></a>
</div>

## Manual Codex Install

Copy the skill into your local Codex skills folder:

```bash
mkdir -p ~/.codex/skills/fyron
cp -R fyron-skill/* ~/.codex/skills/fyron/
```

If you are working from the Fyron repository, you can install the source copy directly:

```bash
mkdir -p ~/.codex/skills/fyron
cp -R docs/ai/fyron-skill/* ~/.codex/skills/fyron/
```

Then ask Codex:

```text
Use the Fyron skill to create a survival analysis workflow from my cohort CSV.
```

or:

```text
Use the Fyron skill to prepare a nested CT/MRI folder for Curate review.
```

## Manual Claude Setup

Claude can use the same files as project knowledge:

1. Create a Claude Project for the study or package.
2. Upload `fyron-claude-project-knowledge.md`, or upload `SKILL.md` and the `references/` folder.
3. Add the public documentation URL: `https://fyron.bitsandflames.ai`.
4. Tell Claude to prefer public Fyron APIs and to keep clinical assumptions explicit.

A compact Claude project instruction:

```text
Use Fyron for clinical data science workflows. Prefer public APIs from fyron.fhir,
fyron.dicom, fyron.imaging, fyron.cohort, fyron.statistics, fyron.survival,
fyron.ml, fyron.validation, fyron.plotting, fyron.visualization, and fyron.audit.
Keep examples synthetic or de-identified. Do not send PHI to external LLMs.
Use https://fyron.bitsandflames.ai as the source of truth.
```

## Manual Cursor Setup

For Cursor, put the guidance into project rules:

```bash
mkdir -p .cursor/rules
cp fyron-skill/references .cursor/rules/fyron-references -R
cp fyron-skill/SKILL.md .cursor/rules/fyron.mdc
```

The installer creates a richer `.cursor/rules/fyron.mdc` file with Cursor frontmatter, so prefer the installer when possible:

```bash
python fyron-skill/install.py --target cursor --project-dir .
```

## How The Skill Should Behave

The skill is intentionally practical. A good assistant using it should:

- map the task to the right Fyron module before writing code,
- choose a targeted install extra instead of always requiring `fyron[all]`,
- validate column names, event coding, dates, array shapes, image geometry, and mask alignment early,
- write inspectable outputs such as CSV, JSON, PNG/SVG, Markdown, notebooks, and provenance manifests,
- use Curate for local image selection workflows,
- keep private endpoints, credentials, accessions, MRNs, and patient-linked dates out of prompts and generated examples,
- ask for human review when clinical or statistical assumptions would change the result.

## Example Prompt

```text
Use the Fyron skill. I have a cohort CSV with patient_id, diagnosis_date,
last_followup_date, death_event, age, sex, stage, and CT feature columns.
Create a reproducible workflow that validates columns, builds survival time/event,
creates a Table 1, draws Kaplan-Meier curves, fits a Cox model, writes figures,
and saves a provenance manifest. Use only public Fyron APIs.
```

## Related Pages

- [LLM Python API](modules/llm.md)
- [SKILL.md](ai/fyron-skill/SKILL.md)
- [AI Assistant Guide](agents.md)
- [Modules Overview](modules/index.md)
- [Fyron Curate](applications/curate.md)
- [Unified CLI](modules/cli.md)
- [Function Reference](function-reference.md)
- [Using Fyron In Research](repository-trust.md)
