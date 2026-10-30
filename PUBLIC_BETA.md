# Fyron Public Beta

Fyron is open for public-beta use by healthcare data scientists, imaging AI teams, and clinical research engineers who need inspectable research workflows.

## What Public Beta Means

- Core workflows are tested, documented, and intended to be useful.
- APIs may still evolve before a stable `1.0` release.
- We prefer additive changes, migration notes, and compatibility aliases where practical.
- Public examples should use synthetic or de-identified data only.

## Intended Use

Fyron supports research workflows such as FHIR and DICOM extraction, cohort construction, descriptive analysis, survival analysis, tabular ML, validation, plotting, curation, and provenance capture.

Fyron is not a medical device, treatment recommendation system, compliance platform, or replacement for local governance, clinical validation, privacy review, or institutional approval.

## Public Repository Safety

Before sharing issues, examples, screenshots, or pull requests, remove:

- credentials, tokens, and private endpoint URLs,
- patient names, MRNs, birth dates, accession numbers, and free text,
- patient-identifying DICOM tags and real FHIR payloads,
- local paths that reveal private projects, users, institutions, or unreleased studies.

Use small synthetic fixtures whenever possible.

## Current Readiness Snapshot

The maintained pre-release checks are:

```bash
uv run pytest
uv run python scripts/build_docs.py
uv build
uv run python scripts/check_release_readiness.py --skip-git-clean
```

Known public-beta polish work remains, especially improving generated docstring coverage for all public APIs.
