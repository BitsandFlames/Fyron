# Quickstart: Curate Image Review

Use this when you need a local review workspace for accepting and rejecting image samples before analysis.

## Install And Start

```bash
uv add "fyron[curate]"
fyron curate --open
```

Docker Desktop or another Docker Compose runtime must be running.

## Review A Cohort

1. Open `http://localhost:5174/`.
2. Create a cohort and drop in an image or DICOM folder.
3. Add a **Selection context** note so reviewers know what to look for.
4. Use gallery view for overview review or **Zen mode** for one-image-at-a-time review.
5. Accept with `A`, reject with `D`, move with left/right arrows, and close preview or Zen mode with `Esc`.
6. Export CSV after the full cohort is reviewed.

The CSV export contains `filename,status`, where status is `accepted` or `rejected`.

## Data Lifecycle

Curate keeps source uploads immutable. Review state is stored in PostgreSQL, clean folders copy accepted files into the export volume, and Docker volumes persist until you remove them.

## Next Steps

- [Start the app](../applications/curate/start.md) for installation, restart, and storage.
- [Prepare your data](../applications/curate/prepare-data.md) for supported formats, folder layouts, and Bash/Python preview examples.
- [Review & export](../applications/curate/review-export.md) for explicit review decisions and the different export requirements.
