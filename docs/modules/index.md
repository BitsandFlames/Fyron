# Module Overview

Fyron is a set of small healthcare workflow modules. You do not need the whole package for every project. A FHIR integration can use only `fyron.fhir`; an imaging QC script can use only `fyron.imaging`; a clinical modeling project can use `fyron.cohort`, `fyron.descriptive`, `fyron.survival`, and `fyron.ml`.

Use this page to choose the right module from your task, input type, and expected output.

For a study-oriented path through cohort definition, validation, reporting, and provenance, start with the [Clinical AI Study Workflow](../clinical-ai-study-workflow.md).

For runnable synthetic tutorials, see the [Example Gallery](../example-gallery.md). For citation, privacy, and research-use guidance, see [Using Fyron In Research](../repository-trust.md). For terminal workflows, see [Unified CLI](cli.md).

## How To Think About Fyron

Most Fyron functions follow the same pattern:

| Concept | Meaning |
| --- | --- |
| Input | DataFrame, array, file path, FHIR JSON, DICOM/NIfTI file, or explicit parameter dictionary. |
| Parameters | Named clinical or technical assumptions such as `duration_col`, `event_col`, `group_col`, `save_path`, or `max_pages`. |
| Output | Inspectable DataFrame, dict/dataclass, fitted model, Matplotlib figure, file path, or JSON manifest. |
| Responsibility | Fyron computes structured artifacts; the researcher still reviews clinical meaning. |

Prefer explicit column names even when defaults match your table. A call with `duration_col="time"` and `event_col="event"` is easier to review than one that relies on hidden conventions.

## Public And Internal APIs

For public beta, the supported API surface is the documented package exports, top-level helpers, CLI commands, and functions/classes described in the module guides. Underscore-prefixed modules and helpers are implementation details and may change without a compatibility window. The generated reference intentionally includes many functions for lookup, but the module guides define the workflows external users should depend on.

## Choose By Workflow Stage

| Stage | Typical input | Use | Typical output |
| --- | --- | --- | --- |
| Acquire FHIR resources | FHIR REST endpoint | `fyron.fhir.FHIRRestClient` | resource DataFrame |
| Query FHIR warehouse | SQL-backed FHIR tables | `fyron.fhir.FHIRSQLClient` | query DataFrame |
| Build FHIR JSON | reviewed DataFrame or measurements | `fyron.fhir.builder`, `fyron.fhir.mapping` | FHIR resources/bundles |
| Download imaging | Study/Series Instance UIDs | `fyron.dicom.DICOMDownloader` | DICOM/NIfTI files and result table |
| Read local imaging | DICOM/NIfTI paths | `fyron.imaging` | SimpleITK images, arrays, QC tables |
| Visualize aligned image differences | CT/MR volumes | `fyron.visualization` | slice figure and difference summary table |
| Prepare training datasets | NIfTI, DICOM, PNG/JPG, box tables | `fyron.datasets` | nnU-Net v2 and YOLO folders |
| Extract BOA features | BOA case folders | `fyron.boa_extraction`, `fyron.boa_radiomics` | patient-level feature DataFrame |
| Download reports | URLs or file table | `fyron.documents.DocumentDownloader` | downloaded files and metadata |
| Store tabular data | CSV/Excel/JSON/S3/Teable | `fyron.core` | DataFrames and storage metadata |
| Derive clinical code features | ICD-10/OPS/MDC/Charlson columns | `fyron.clinical_codes` | indicators, partitions, comorbidity score columns |
| Derive general table features | code/date columns | `fyron.dataframe` | indicators, prevalence tables, interval columns |
| Build cohorts | feature and outcome tables | `fyron.cohort`, `fyron.phenotyping` | patient-level cohort |
| Prepare features | cohort table | `fyron.preprocessing` | missingness, imputation, encoding, leakage tables |
| Summarize cohort | cohort table | `fyron.descriptive`, `fyron.reporting` | Table 1, endpoint summary, flow table |
| Explain cohort filters | sequential cohort DataFrames | `fyron.flow` | console summary, Markdown flow, flow table |
| Analyze endpoints | survival cohort | `fyron.survival`, `fyron.statistics` | survival curves, model tables, tests |
| Train classifiers | feature matrix and labels | `fyron.ml` | model, predictions, metrics, figures |
| Select features | `X`, `y` | `fyron.feature_selection` | selected features and consensus tables |
| Validate models | labels, probabilities, predictions | `fyron.validation` | calibration, thresholds, subgroup, DCA tables |
| Explain models | fitted sklearn-style model | `fyron.explainability` | importance, PDP, SHAP-style tables |
| Publish artifacts | tables, metrics, images | `fyron.plotting`, `fyron.reporting`, `fyron.audit` | figures, tables, manifests |
| Run repeatable jobs | terminal parameters | `fyron` CLI | CSV, JSON, DICOM, NIfTI, manifests |

## Choose By Question

| If you need to... | Start with | Then consider |
| --- | --- | --- |
| Pull Observations or Conditions from a live server | [FHIR REST](fhir/rest.md) | [FHIR Paths example](../examples/fhir-paths-custom-extraction.md) |
| Avoid FHIR server result caps | `search_df_partitioned` in [FHIR REST](fhir/rest.md) | smaller date windows and `deduplicate_by` |
| Download CT series from a cohort CSV | [DICOMDownloader](dicom/downloader.md) | [Imaging](imaging.md) for QC |
| Download text reports or PDFs with OIDC authentication | [DocumentDownloader](documents/downloader.md) | [Documents overview](documents.md) and [document CLI](cli.md#document-downloads) |
| Compare two aligned CT/MR volumes visually | [BOA Visualization](visualization.md#volume-difference-heatmaps) | [Imaging](imaging.md) for explicit alignment and normalization |
| Prepare 3D segmentation datasets | [nnU-Net v2 preparation](datasets.md#nnu-net-v2-preparation) | [Synthetic nnU-Net example](../examples/dataset-preparation.md#nnu-net-v2-dataset) |
| Prepare image classification datasets | [YOLO classification](datasets.md#yolo-classification-preparation) | [Synthetic classification example](../examples/dataset-preparation.md#yolo-classification-dataset) |
| Prepare object detection datasets | [YOLO detection](datasets.md#yolo-object-detection-preparation) | [Synthetic detection example](../examples/dataset-preparation.md#yolo-detection-dataset) |
| Find the upstream BOA segmentation tools | [BOA CT and BOA MR repositories](boa.md#upstream-tools-and-repositories) | [Fyron's BOA workflows](boa.md#choose-a-fyron-workflow) |
| Turn BOA outputs into a feature table | [BOA Extraction](boa-extraction.md) | [BOA Radiomics](boa-radiomics.md), [BOA Visualization](visualization.md) |
| Join baseline features and outcomes | [Cohort Tables](cohort.md) | [Preprocessing QC](preprocessing.md) |
| Turn ICD, OPS, MDC, or Charlson columns into features | [Clinical Codes](clinical-codes.md) | [DataFrame Operations](dataframe.md), [Phenotyping](phenotyping.md) |
| Turn local code or date columns into features | [DataFrame Operations](dataframe.md) | [Phenotyping](phenotyping.md), [Cohort Tables](cohort.md) |
| Create a manuscript Table 1 | [Descriptive Analysis](descriptive.md) | [Reporting](reporting.md), [Clinical Plotting](plotting.md) |
| Explain inclusion/exclusion filters | [Flow Explainability](flow.md) | [Reporting](reporting.md), [Clinical Plotting](plotting.md) |
| Plot survival by treatment or risk group | [Survival Analysis](survival.md) | [Clinical Plotting](plotting.md) |
| Train a random forest or XGBoost model | [Machine Learning](ml.md) | [Validation](validation.md), [Explainability](explainability.md) |
| Record reproducibility metadata | [Audit & Provenance](audit.md) | `fyron audit-manifest` CLI |
| Run the same step from terminal or scheduler | [Unified CLI](cli.md) | JSON logs and `--no-progress` for batch systems |
| Choose colorblind-safe scientific figure palettes | [Colors And Styles](../colors.md) | [Clinical Plotting](plotting.md) |

## Common Data Shapes

| Shape | Modules | Notes |
| --- | --- | --- |
| Long resource table | `fhir`, `documents` | One row per resource, document, or extracted result. |
| Feature table | `boa_extraction`, `imaging`, `phenotyping` | One row per patient or analysis unit, feature columns wide. |
| Derived clinical feature table | `clinical_codes`, `dataframe`, `phenotyping` | Raw code/date columns plus explicit indicators, summaries, partitions, scores, and intervals. |
| Cohort table | `cohort`, `preprocessing`, `descriptive`, `survival`, `ml` | One row per patient/analysis unit with endpoint and covariates. |
| Flow table | `flow`, `reporting`, `plotting` | Ordered inclusion/exclusion steps with counts and reasons. |
| Feature matrix and labels | `ml`, `feature_selection`, `validation` | `X` is features; `y` is endpoint labels. |
| Figure artifact | `plotting`, `survival`, `ml` | Matplotlib figure/axes, often with optional `save_path`. |
| Image review figure | `visualization` | Slice panels, overlays, difference heatmaps, and image metadata. |
| Manifest | `audit` | JSON-serializable provenance metadata. |

## Clinical Defaults To Remember

- Survival functions expect positive duration values and event indicators where `1` means event and `0` means censored.
- Classification metrics should be interpreted with sensitivity, specificity, balanced accuracy, AUC when probabilities exist, and confusion counts.
- Imbalanced binary classification can use sklearn `class_weight` or XGBoost `scale_pos_weight`.
- Correlation heatmaps default to Spearman for clinical exploratory work.
- BOA body-region tissue volumes are read from `measurements_no_extremities`.
- FHIR pagination should be bounded during exploration; partition broad searches by date when server caps appear.
- Flow tracking should start from the source cohort so retention percentages have a real denominator.

## Extras By Module

| Extra | Modules unlocked or enhanced |
| --- | --- |
| none | `fyron.fhir`, `fyron.dicom`, `fyron.imaging`, `fyron.documents`, `fyron.llm`, `fyron.core`, `fyron.clinical_codes`, `fyron.dataframe`, `fyron.cohort`, `fyron.flow` |
| `fyron[all]` | all optional Fyron dependencies for a full local research environment |
| `fyron[excel]` | Excel I/O via `read_excel` and `write_excel` |
| `fyron[s3]` | S3 and S3-compatible object storage helpers |
| `fyron[survival]` | lifelines-based survival analysis |
| `fyron[survival-ml]` | gradient survival boosting with `scikit-survival` |
| `fyron[statistics]` | statistical tests and bootstrap confidence intervals |
| `fyron[descriptive]` | descriptive tables backed by NumPy/SciPy |
| `fyron[dicom-seg]` | standards-compliant DICOM SEG writing with highdicom |
| `fyron[ml]` | classification ML and clinical model plots |
| `fyron[feature-selection]` | univariate, correlation, model, permutation, Boruta, and stability selection |
| `fyron[validation]` | model validation helpers |
| `fyron[explainability]` | permutation importance, PDP, and optional SHAP tables |
| `fyron[visualization]` | BOA/OpenCV collage rendering |
| `fyron[radiomics]` | BOA/PyRadiomics texture and shape features |

## End-To-End Composition

```python
from fyron.cohort import build_survival_columns, join_cohort_tables
from fyron.survival import fit_multivariate_cox
from fyron import descriptive as fd
from fyron import ml

cohort = join_cohort_tables(features_df, outcomes_df, on="patient_id")
cohort = build_survival_columns(cohort, "index_date", "last_followup", "event")

table_one = fd.create_table_one(
    cohort,
    group_col="risk_group",
    numeric=["age", "risk_score"],
    categorical=["sex", "stage"],
)

cox = fit_multivariate_cox(
    cohort,
    duration_col="time",
    event_col="event",
    covariates=["age", "stage", "risk_score"],
)

clf = ml.run_classification_pipeline(
    cohort[["age", "stage_encoded", "risk_score"]],
    cohort["binary_endpoint"],
    model="xgboost",
    plot=True,
)
```

## Design Principles

- Keep protocol-specific details visible. FHIR remains FHIR; DICOM remains DICOM.
- Prefer explicit clinical column names over hidden conventions.
- Return both computed tables and fitted model objects where useful.
- Make optional dependencies opt-in.
- Keep plots manuscript-friendly and reproducible from code.
