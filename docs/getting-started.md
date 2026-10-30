# Getting Started

For site-specific access setup, see [Authentication](authentication/index.md). Choose the method and permissions approved by your administrator.

This page walks through the smallest useful Fyron workflow: install the package, choose the right interface, query a FHIR server, shape a patient-level cohort, create a descriptive table or plot, and write a provenance record. Treat it as a smoke test before connecting to private systems or larger datasets.

Fyron is intentionally explicit. Most functions accept ordinary Python objects, file paths, arrays, or `pandas.DataFrame` inputs. They return inspectable DataFrames, dictionaries, fitted estimators, Matplotlib figures, or JSON manifests instead of hiding clinical assumptions behind a large framework.

## Install

```bash
uv add fyron
```

Install extras only when your workflow needs them:

| Workflow | Install |
| --- | --- |
| Full local research environment | `uv add "fyron[all]"` |
| Excel files | `uv add "fyron[excel]"` |
| Descriptive statistics and Table 1 | `uv add "fyron[descriptive]"` |
| Survival analysis | `uv add "fyron[survival]"` |
| Tabular machine learning | `uv add "fyron[ml]"` |
| Validation helpers | `uv add "fyron[validation]"` |
| BOA collages | `uv add "fyron[visualization]"` |

For a broad local clinical data science environment:

```bash
uv add "fyron[all]"
```

## Choose Your Interface

| Interface | Best for | Example |
| --- | --- | --- |
| Python API | notebooks, scripts, reusable analysis functions | `FHIRRestClient(...).search_df(...)` |
| CLI | repeatable extraction jobs and batch outputs | `fyron fhir-rest --resource Patient ...` |
| Docs examples | learning workflows before adapting them | [Workflow Guide](workflow.md) |
| Example gallery | runnable synthetic workflows by artifact | [Example Gallery](example-gallery.md) |

Use the Python API while designing an analysis. Use the CLI when a step should be rerun by another person, a scheduler, or CI.

## Configure Credentials

Public examples can run without credentials. Private FHIR, DICOMweb, S3, or Teable systems usually need environment variables. Fyron provides a small `.env` loader:

```python
from fyron import load_env

load_env()
```

Common project-specific variables include `FHIR_BASE_URL`, `FHIR_BEARER_TOKEN`, `DICOM_WEB_URL`, `DICOM_USER`, and `DICOM_PASSWORD`.

## Query A Public FHIR Server

Start every new FHIR workflow with bounded queries. `max_pages=1` keeps exploration safe and makes the returned shape easy to inspect.

```python
from fyron import FHIRRestClient

client = FHIRRestClient("https://hapi.fhir.org/baseR4")

patients = client.search_df(
    "Patient",
    params={"_count": 10, "_sort": "_id"},
    max_pages=1,
)

patients.head()
```

The same extraction can run from the CLI:

```bash
fyron fhir-rest \
  --base-url https://hapi.fhir.org/baseR4 \
  --resource Patient \
  --param _count=10 \
  --max-pages 1 \
  --output patients.csv
```

## Build A Cohort Table

A Fyron cohort table is usually one row per patient or analysis unit. It should have stable identifiers, endpoint information, and features that are available at the intended analysis time.

```python
import pandas as pd
from fyron.cohort import build_survival_columns, validate_cohort_table

cohort = pd.DataFrame(
    {
        "patient_id": ["p1", "p2", "p3"],
        "diagnosis_date": ["2022-01-01", "2022-02-15", "2022-03-20"],
        "last_followup_or_event_date": ["2023-01-01", "2022-10-01", "2023-03-01"],
        "death_event": [1, 0, 1],
        "age": [67, 72, 59],
        "risk_group": ["high", "low", "high"],
    }
)

cohort = build_survival_columns(
    cohort,
    start_col="diagnosis_date",
    end_col="last_followup_or_event_date",
    event_col="death_event",
    time_col="time",
    event_out_col="event",
)

validate_cohort_table(
    cohort,
    required_columns=["patient_id", "time", "event", "age", "risk_group"],
    id_column="patient_id",
)
```

Survival workflows expect positive durations and event coding where `1` means event and `0` means censored.

## Create A Table And A Plot

```python
from fyron import descriptive as fd
from fyron.survival import plot_kaplan_meier

table_one = fd.create_table_one(
    cohort,
    group_col="risk_group",
    numeric=["age", "time"],
    categorical=["event"],
    include_smd=True,
)

km = plot_kaplan_meier(
    cohort,
    duration_col="time",
    event_col="event",
    group_col="risk_group",
    at_risk_counts=True,
)
```

Typical return shapes:

| Function family | Common return |
| --- | --- |
| Descriptive/reporting functions | `pandas.DataFrame` |
| Survival/model functions | dict-like result objects with tables, fitters, metrics, and figures |
| Plotting functions | Matplotlib `(fig, ax)` or a named result object |
| Audit functions | JSON-serializable dictionaries |

## Export Results And Provenance

```python
from fyron import audit as fa
from fyron import reporting as fr

table_one.to_csv("results/table_one.csv", index=False)
fr.dataframe_to_markdown(table_one)

manifest = fa.create_provenance_manifest(
    title="Getting started cohort analysis",
    inputs=["data/cohort.csv"],
    outputs=["results/table_one.csv"],
    parameters={
        "duration_col": "time",
        "event_col": "event",
        "group_col": "risk_group",
    },
)

fa.write_manifest(manifest, "results/provenance.json")
```

The manifest records inputs, outputs, parameters, package metadata, and file hashes when paths exist.

## What To Read Next

- [Workflow Guide](workflow.md) for the full clinical data science pipeline.
- [Modules Overview](modules/index.md) to choose the right module.
- [Example Gallery](example-gallery.md) for runnable synthetic workflows.
- [Using Fyron In Research](repository-trust.md) for citation, privacy, and reproducibility guidance.
- [Function Reference](function-reference.md) for quick lookup while coding.
- [Colors And Styles](colors.md) for scientific palettes and figure style choices.
- [FHIR REST](modules/fhir/rest.md) for live FHIR extraction.
- [DICOMDownloader](modules/dicom/downloader.md) for imaging downloads.
- [BOA Extraction](modules/boa-extraction.md) for body-composition feature tables.
- [Function Reference](function-reference.md) for quick lookup while coding.
