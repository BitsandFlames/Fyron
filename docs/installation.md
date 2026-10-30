# Installation & Extras

Fyron keeps heavy scientific dependencies optional. Start small, then install extras as your workflow grows.

The base installation is enough for many integration workflows. Add extras only when you need the corresponding analysis surface: survival modeling, tabular ML, Excel files, or BOA visualization. This keeps deployment environments smaller and makes optional dependency errors easier to diagnose.

## Which Extra Do I Install?

| If your task is... | Install |
| --- | --- |
| FHIR, DICOMweb client setup, table I/O, documents, or cohort shaping | `uv add fyron` |
| A local research notebook that should have every feature available | `uv add "fyron[all]"` |
| Kaplan-Meier, Cox, RMST, Weibull AFT, or survival diagnostics | `uv add "fyron[survival]"` |
| Random forest, XGBoost, ROC/PR, calibration, feature importance, or plotting | `uv add "fyron[ml]"` |
| Model validation helpers such as thresholds, calibration, decision curves, or subgroup metrics | `uv add "fyron[validation]"` |
| BOA collages, image review previews, or visual volume comparisons | `uv add "fyron[visualization]"` |
| DICOM SEG export | `uv add "fyron[dicom-seg]"` |
| Local image cohort review with Curate | `uv add "fyron[curate]"` |
| Excel files or S3/object storage | `uv add "fyron[excel]"` or `uv add "fyron[s3]"` |

## Base Package

```bash
uv add fyron
```

The base package covers FHIR REST, FHIR JSON builders/write-back helpers, SQL helpers, DICOM client wrappers, documents, environment loading, and DataFrame utilities.

## All Features

For local workstations, tutorials, full documentation examples, and exploratory clinical research notebooks, install every optional Fyron feature with:

```bash
uv add "fyron[all]"
```

This includes the heavier scientific extras such as survival ML, DICOM SEG, BOA visualization, radiomics, explainability, feature selection, Excel, and S3 support. For servers, CI jobs, and smaller deployments, prefer the targeted extras below.

## Extras

| Extra | Install | Adds |
| --- | --- | --- |
| All features | `uv add "fyron[all]"` | Full local research environment with every optional dependency |
| Excel | `uv add "fyron[excel]"` | `openpyxl` for `.xlsx` I/O |
| S3 | `uv add "fyron[s3]"` | `boto3` for AWS S3 and S3-compatible object storage |
| Survival | `uv add "fyron[survival]"` | `lifelines`, `matplotlib`, `scipy` |
| Survival ML | `uv add "fyron[survival-ml]"` | `scikit-survival` for gradient survival boosting |
| Statistics | `uv add "fyron[statistics]"` | `numpy`, `scipy` for tests and bootstrap intervals |
| Descriptive | `uv add "fyron[descriptive]"` | NumPy/SciPy descriptive analysis helpers |
| DICOM SEG | `uv add "fyron[dicom-seg]"` | `highdicom` for standards-compliant DICOM SEG export |
| ML | `uv add "fyron[ml]"` | `numpy`, `scikit-learn`, `xgboost`, `matplotlib`, `joblib` |
| Feature Selection | `uv add "fyron[feature-selection]"` | statistical/model feature selection, including Boruta |
| Validation | `uv add "fyron[validation]"` | NumPy/scikit-learn validation helpers |
| Explainability | `uv add "fyron[explainability]"` | sklearn model inspection and SHAP tables |
| Reporting | `uv add "fyron[reporting]"` | reporting helper alias; no extra dependency |
| Audit | `uv add "fyron[audit]"` | provenance helper alias; no extra dependency |
| Boruta | `uv add "fyron[ml,boruta]"` | Boruta feature selection |
| Visualization | `uv add "fyron[visualization]"` | OpenCV for BOA collages |
| Radiomics | `uv add "fyron[radiomics]"` | PyRadiomics for BOA mask feature extraction; currently Python 3.11 because PyRadiomics 3.0.1 does not build on Python 3.12 |

## Compatibility Matrix

| Surface | Supported / expected environment |
| --- | --- |
| Base package | Python 3.11, 3.12 |
| CI | Ubuntu latest across Python 3.11-3.12 |
| `fyron[ml]` | NumPy, scikit-learn, XGBoost, Matplotlib, Joblib |
| `fyron[survival]` | lifelines, SciPy, Matplotlib |
| `fyron[survival-ml]` | scikit-survival plus survival dependencies |
| `fyron[dicom-seg]` | highdicom for DICOM SEG export |
| `fyron[radiomics]` | PyRadiomics; intended for Python 3.11 |
| `fyron[curate]` | Docker Compose runtime plus local browser |
| Docs | Custom static docs builder in `scripts/build_docs.py` |

Fyron is in public beta. The base package and main workflow modules are tested in CI, while heavyweight optional extras depend on upstream scientific package compatibility.

## Recommended Analysis Install

```bash
uv add "fyron[all]"
```

## Working From A Clone

```bash
git clone https://github.com/bitsandflames/fyron.git
cd fyron
uv sync --all-extras --dev
uv run pytest
```

This is mainly useful if you want to contribute, run the test suite, or inspect examples from the source tree.

## Preview Documentation Locally

Fyron's docs are built from the Markdown files in `docs/`. If you are editing the docs, preview them locally with:

```bash
uv run python scripts/build_docs.py
uv run python -m http.server 8001 --directory site
```
