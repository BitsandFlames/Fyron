# API Reference

This reference lists the main public APIs by workflow. It is not a generated docstring dump; it is a practical index for choosing the right entry point. See each module page for detailed examples.

Use this page as a map of stable entry points. The detailed module pages explain context, expected data shapes, and interpretation; this page helps you find the import and function name quickly.

## Top-Level Imports

Most common clients and helpers are available from `fyron`.

```python
from fyron import (
    Auth,
    DICOMDownloader,
    DocumentDownloader,
    FHIRRestClient,
    FHIRSQLClient,
    LLMAgent,
    configure_logging,
    console_message,
    get_logger,
    get_run_footer,
    get_run_header,
    load_env,
    read_json,
    read_table,
    read_csv,
    write_csv,
    write_json,
    write_table,
    read_excel,
    write_excel,
)
```

| Symbol | Module | Purpose |
| --- | --- | --- |
| `Auth` | `fyron.fhir.auth` | Basic/session/token authentication helper |
| `FHIRRestClient` | `fyron.fhir.rest` | Query FHIR REST APIs and return DataFrames |
| `FHIRSQLClient` | `fyron.fhir.sql` | Query SQL-backed FHIR stores |
| `DICOMDownloader` | `fyron.dicom.client` | Download DICOMweb studies/series |
| `DocumentDownloader` | `fyron.documents.client` | Download document URLs or DataFrame URL columns |
| `LLMAgent` | `fyron.llm.agent` | Prompt over text, files, images, and DataFrames |
| `get_run_header` / `get_run_footer` | `fyron.banner` | Render reproducible run markers for scripts and logs |
| `configure_logging` / `get_logger` | `fyron.console` | Configure Fyron logging and retrieve package loggers |
| `console_message` | `fyron.console` | Emit one BF-style terminal message |
| `load_env` | `fyron.core.env` | Load `.env` files |
| `read_table` / `write_table` | `fyron.core.io` | Unified CSV/TSV/Excel/JSON/JSONL table I/O |
| `read_json` / `write_json` | `fyron.core.io` | JSON sidecar I/O |
| `read_csv` / `write_csv` | `fyron.core.io` | CSV helpers |
| `read_excel` / `write_excel` | `fyron.core.io` | Excel helpers, requires `fyron[excel]` |

## API Design Contract

Fyron keeps one primary public path per workflow:

- REST/live FHIR extraction returns DataFrames through `FHIRRestClient.search_df(...)` and row-wise searches through `search_df_from(...)`.
- SQL-backed FHIR extraction returns DataFrames through `FHIRSQLClient.query_df(...)`.
- FHIR builders return plain dictionaries that can be inspected, validated, written, or posted.
- FHIR mapping helpers return dictionaries with `bundle`, `resources`, `summary`, and `validation`.
- Plotting functions return Matplotlib objects, usually `(fig, ax)`.
- CLI commands write inspectable CSV, JSON, DICOM, NIfTI, or manifest files.

Compatibility names such as `query_df`, `query_df_from`, `query_to_dataframe`, and `query_from_dataframe` remain supported.

## Unified CLI

```bash
fyron --help
```

Global flags:

| Flag | Purpose |
| --- | --- |
| `--verbose` | Enable debug logging |
| `--quiet` | Suppress nonessential user-facing messages |
| `--no-color` | Disable ANSI colors |
| `--json-log` | Emit structured JSON log records |
| `--no-progress` | Disable progress bars where supported |

| Command | Purpose |
| --- | --- |
| `fyron banner` | Print the Fyron terminal banner |
| `fyron spark` | Print the Fyron banner easter egg |
| `fyron docs-build` | Build the custom BF documentation site |
| `fyron fhir-rest` | Query FHIR REST resources into CSV/JSON |
| `fyron fhir-build-bundle` | Build FHIR bundles from reviewed CSV tables |
| `fyron dicom-download` | Download DICOMweb series/studies |
| `fyron synthetic-dicom` | Export generated NIfTI volumes as synthetic DICOM |
| `fyron dicom-seg` | Write DICOM SEG objects |
| `fyron boa-extract` | Extract BOA measurement features |
| `fyron boa-radiomics` | Extract BOA radiomics features |
| `fyron imaging-qc` | Write imaging QC summaries |
| `fyron audit-manifest` | Write provenance manifests |

## Core I/O

```python
from fyron.core import DataIO, TeableClient, load_env, read_table, write_table
from fyron.core.s3 import S3Storage
```

| API | Purpose |
| --- | --- |
| `load_env(path=".env", override=False, warn_if_missing=True)` | Load environment variables |
| `read_table(path, ...)` / `write_table(df, path, ...)` | Unified table I/O for CSV, TSV, Excel, JSON, and JSONL |
| `read_json(path)` / `write_json(payload, path)` | JSON sidecar I/O |
| `summarize_table(df)` / `describe_file(path)` | Lightweight table and file metadata |
| `read_csv(path, **kwargs)` | Read a CSV into a DataFrame |
| `write_csv(df, path, **kwargs)` | Write a DataFrame to CSV |
| `read_excel(path, **kwargs)` | Read an Excel workbook |
| `write_excel(df, path, **kwargs)` | Write an Excel workbook |
| `DataIO` | Object/static wrapper around Core I/O helpers |
| `TeableClient.read_cohort(...)` | Read and validate Teable review/cohort tables |
| `TeableClient.write_research_cohort(...)` | Write finished research cohorts to Teable |
| `S3Storage` | Optional S3/S3-compatible table, JSON, and file I/O with `fyron[s3]` |

## FHIR

```python
from fyron.fhir import Auth, FHIRObj, FHIRRestClient
from fyron import FHIRSQLClient
from fyron.fhir.builder import build_bundle, build_observation, write_fhir_json
```

| API | Purpose |
| --- | --- |
| `FHIRRestClient.search_df(resource_type, params=None, max_pages=None)` | Search a FHIR resource and return a DataFrame |
| `FHIRRestClient.search_df_from(df, ...)` | Row-wise FHIR searches from an input DataFrame |
| `FHIRRestClient.query_df(...)` / `query_df_from(...)` | Compatibility names for FHIR REST searches |
| `FHIRRestClient.create_resource(resource, ...)` | POST a resource to a FHIR server |
| `FHIRRestClient.update_resource(resource, ...)` | PUT a resource to a FHIR server |
| `FHIRRestClient.submit_bundle(bundle)` | POST a transaction Bundle to the FHIR base URL |
| `FHIRSQLClient.query_df(sql, ...)` | SQL query to DataFrame |
| `FHIRSQLClient.query_df_from(df, ...)` | Row-wise SQL queries from an input DataFrame |
| `Auth.token_env(...)` | Build token auth from environment variables |
| `FHIRObj` | Object-style wrapper around raw FHIR JSON |
| `safe_get` and `extract_*` helpers | Defensive resource field extraction |
| `build_observation(...)`, `build_condition(...)` | Build FHIR clinical resources as dictionaries |
| `build_document_reference(...)`, `build_diagnostic_report(...)` | Build report/source-document resources |
| `build_llm_extraction_bundle(...)` | Package LLM-extracted report evidence |
| `build_imaging_measurement_bundle(...)` | Package imaging-derived measurements |
| `build_bundle(resources, bundle_type=...)` | Build collection or transaction Bundles with POST/PUT request metadata |
| `build_observation_component(...)` | Build multi-part Observation components |
| `build_encounter(...)`, `build_procedure(...)`, `build_medication_statement(...)` | Build additional clinical resources |
| `build_service_request(...)`, `build_specimen(...)` | Build request/specimen resources |
| `loinc(...)`, `snomed(...)`, `icd10(...)`, `dicom_code(...)` | Common clinical coding helpers |
| `summarize_fhir_resource(...)`, `summarize_fhir_bundle(...)` | Inspect resources and bundles before writing/posting |
| `write_fhir_json(...)`, `read_fhir_json(...)` | Local FHIR JSON file I/O |
| `validate_fhir_resource(...)`, `validate_fhir_bundle(...)`, `validate_fhir_references(...)` | Lightweight structural and reference validation |
| `build_observations_from_dataframe(...)`, `build_conditions_from_dataframe(...)` | Map reviewed DataFrames to FHIR bundles |
| `build_document_references_from_dataframe(...)`, `build_imaging_measurements_from_dataframe(...)` | Map document/imaging tables to FHIR bundles |
| `validate_fhir_mapping(...)`, `validate_fhir_payload(...)`, `fhir_validation_report(...)` | Structured validation reports |

## DICOM And Imaging

```python
from fyron import DICOMDownloader
from fyron.dicom.seg import (
    label_map_to_segments,
    load_source_dicom_series,
    read_segment_descriptions,
    summarize_dicom_seg,
    validate_dicom_seg,
    validate_segment_descriptions,
    write_dicom_seg,
)
from fyron.dicom.synthetic import write_synthetic_dicom_series, write_synthetic_nifti
from fyron import imaging as fim
from fyron.imaging import qc as fiq
```

| API | Purpose |
| --- | --- |
| `DICOMDownloader.download_series(...)` | Download one DICOM series |
| `DICOMDownloader.download_study(...)` | Download a full study |
| `DICOMDownloader.download_from_df(...)` | Batch downloads from a DataFrame |
| `write_synthetic_nifti(volume, output_path, ...)` | Write generated volume to NIfTI with reference geometry |
| `write_synthetic_dicom_series(volume, output_dir, ...)` | Write generated volume as synthetic DICOM slices and return a manifest |
| `write_dicom_seg(mask, source_images, output_path, segment_descriptions, ...)` | Write segmentation masks as DICOM SEG, requires `fyron[dicom-seg]` |
| `label_map_to_segments(label_map, labels)` | Convert integer labels to binary segment stack |
| `load_source_dicom_series(source_dicom_dir, sort_by="geometry")` | Load source DICOM slices in geometry-safe order for SEG export |
| `read_segment_descriptions(path)` | Read CLI-style segment JSON |
| `validate_segment_descriptions(segment_descriptions)` | Check segment labels, duplicates, and coded concepts |
| `validate_dicom_seg(path, source_images=None)` | Inspect core DICOM SEG metadata |
| `summarize_dicom_seg(path, source_images=None)` | Return DICOM SEG metadata summary for CLI/reporting |
| `fim.read_dicom_header(path)` | Read selected or full DICOM metadata |
| `fim.get_dicom_series_ids(path)` | Discover series IDs under a study folder |
| `fim.read_dicom_series(path, series_id=None)` | Load DICOM series as SimpleITK image/array |
| `fim.read_nifti(path, return_array=True)` | Load NIfTI |
| `fim.write_nifti(array_or_image, path, reference_image=None)` | Save NIfTI |
| `fim.normalize_ct(...)` | Clip/scale CT intensities |
| `fim.normalize_mr(...)` | Normalize MR intensities |
| `fiq.summarize_dicom_series_geometry(dicom_dir, ...)` | DICOM spacing/orientation/slice geometry table |
| `fiq.summarize_nifti_geometry(paths)` | NIfTI size/spacing/origin/direction table |
| `fiq.check_image_mask_alignment(image, mask)` | Geometry alignment checks for image and mask |
| `fiq.summarize_mask_volume(mask, ...)` | Label volume table in voxels and ml |
| `fiq.summarize_intensity_range(image, ...)` | Intensity range and percentile summary |
| `fim.dice_score(...)`, `fim.segmentation_metric_table(...)` | Segmentation overlap, surface, and volume metrics |

## Phenotyping

```python
from fyron import phenotyping as fph
```

| API | Purpose |
| --- | --- |
| `fph.define_code_phenotype(...)` | Patient-level phenotype flags from diagnosis/procedure/code rows |
| `fph.define_lab_threshold_phenotype(...)` | Patient-level flags from numeric thresholds |
| `fph.define_medication_exposure(...)` | Patient-level medication exposure flags |
| `fph.combine_phenotypes(...)` | Combine phenotype flags with any/all logic |
| `fph.phenotype_summary(...)` | Prevalence summary overall or by group |

## Datasets

```python
from fyron.datasets import (
    make_boa_like_folder,
    make_classification_cohort,
    make_clinical_cohort,
    make_dicom_series,
    make_nifti_pair,
    make_survival_cohort,
    prepare_nnunetv2_dataset,
    prepare_yolo_classification_dataset,
    prepare_yolo_detection_dataset,
    validate_nnunetv2_dataset,
    validate_yolo_dataset,
)
```

| API | Purpose |
| --- | --- |
| `make_clinical_cohort(n=40, random_state=42)` | Tiny deterministic clinical table |
| `make_survival_cohort(n=40, random_state=42)` | Survival-ready synthetic cohort |
| `make_classification_cohort(n=80, random_state=42)` | Classification features and target |
| `make_nifti_pair(output_dir, ...)` | Tiny image/mask NIfTI pair |
| `make_dicom_series(output_dir, ...)` | Tiny synthetic CT DICOM series |
| `make_boa_like_folder(output_dir)` | Minimal BOA-like folder for examples/tests |
| `prepare_nnunetv2_dataset(manifest, output_dir, ...)` | Build nnU-Net v2 dataset folders and `dataset.json` |
| `prepare_yolo_classification_dataset(manifest, output_dir, ...)` | Build YOLO split/class image folders |
| `prepare_yolo_detection_dataset(manifest, output_dir, ...)` | Build YOLO images, labels, and `data.yaml` |
| `validate_nnunetv2_dataset(dataset_dir)` | Check nnU-Net v2 folder structure and names |
| `validate_yolo_dataset(dataset_dir, task=...)` | Check YOLO classification or detection folders |

## BOA Extraction And Visualization

```python
from fyron.boa_extraction import (
    discover_boa_cases,
    extract_body_region_features,
    extract_total_segmentation_features,
    extract_cohort_body_region_features,
    extract_cohort_total_features,
    extract_experimental_aortic_calcification_features,
    extract_experimental_cohort_aortic_calcification_features,
    extract_boa_features,
)
from fyron.boa_radiomics import (
    discover_boa_radiomics_cases,
    extract_case_radiomics_features,
    extract_boa_radiomics_features,
)
from fyron.visualization import (
    SegmentationLayer,
    create_boa_segmentation_collage,
    plot_volume_difference_heatmap,
)
```

| API | Purpose |
| --- | --- |
| `discover_boa_cases(cohort_folder, measurement_filename="bca-measurements.json")` | Find completed BOA patient folders |
| `extract_body_region_features(case_folder_or_measurements, ...)` | Extract tissue volumes, derived body-region ratios, and L3 SMA/IMATI/VATI markers |
| `extract_total_segmentation_features(case_folder, ...)` | Extract organ CNR, volume, HU, and ratios for one patient |
| `extract_cohort_body_region_features(cohort_folder_or_cases, ...)` | Batch body-region extraction to a DataFrame |
| `extract_cohort_total_features(cohort_folder_or_cases, ...)` | Batch total-segmentation extraction to a DataFrame |
| `extract_experimental_aortic_calcification_features(case_folder_or_masks_dir, ...)` | Experimental aortic calcification burden from BOA-style CT and vascular masks |
| `extract_experimental_cohort_aortic_calcification_features(cohort_folder_or_cases, ...)` | Batch experimental aortic calcification extraction |
| `extract_boa_features(cohort_folder_or_cases, ...)` | Extract and merge BOA feature families by `download_id` |
| `discover_boa_radiomics_cases(cohort_folder, ...)` | Find patient folders with a target segmentation file |
| `extract_case_radiomics_features(case_folder, ...)` | Extract PyRadiomics features for one BOA patient folder |
| `extract_boa_radiomics_features(cohort_folder_or_cases, ...)` | Batch radiomics extraction from `total.nii.gz` or `body-regions.nii.gz` |
| `create_boa_segmentation_collage(...)` | Render BOA segmentation review collages |
| `plot_volume_difference_heatmap(...)` | Compare aligned CT/MR volumes with slice panels and a zero-centered difference map |

## Preprocessing, Reporting, Validation, Explainability, Audit

```python
from fyron import preprocessing as fp
from fyron import descriptive as fd
from fyron import feature_selection as fs
from fyron import plotting as fplot
from fyron import reporting as fr
from fyron import statistics as fst
from fyron import validation as fv
from fyron import explainability as fe
from fyron import FlowTracker, track_filter
from fyron import audit as fa
```

| API | Purpose |
| --- | --- |
| `fp.summarize_missingness(df, ...)` | missing-value table, optionally by group |
| `fp.find_duplicate_ids(df, id_col="patient_id")` | duplicate patient identifier rows |
| `fp.compare_train_test_balance(train, test, ...)` | split balance summary |
| `fp.detect_potential_leakage(columns, ...)` | suspicious outcome/time-like column names |
| `fp.fit_imputer(...)`, `fp.apply_imputer(...)` | train/apply imputation for feature tables |
| `fp.fit_categorical_encoder(...)`, `fp.apply_categorical_encoder(...)` | stable one-hot encoding across cohorts |
| `fd.describe_numeric(df, ...)` | numeric descriptive summary table |
| `fd.describe_categorical(df, ...)` | categorical count/percent summary table |
| `fd.create_table_one(df, ...)` | table-one style descriptive table |
| `fd.summarize_endpoint(df, ...)` | event rate and follow-up summary |
| `fs.univariate_feature_screening(X, y, ...)` | statistical feature screening with FDR correction |
| `fs.correlation_filter(X, ...)` | redundant-feature filtering |
| `fs.model_importance_selection(estimator, X, y, ...)` | estimator importance/coefficient selection |
| `fs.permutation_importance_selection(estimator, X, y, ...)` | model-agnostic permutation selection |
| `fs.stability_selection(estimator, X, y, ...)` | repeated subsampling selection frequencies |
| `fs.combine_feature_selection_results(results, ...)` | consensus feature-selection table |
| `fr.summarize_baseline_table(df, ...)` | baseline characteristics table |
| `fr.cohort_flow_table(steps)` | CONSORT/STROBE-style flow table data |
| `fr.metrics_table(metrics, ...)` | normalize metric dictionaries/DataFrames for reporting |
| `fst.p_value_correction_table(df, ...)` | Benjamini-Hochberg, Bonferroni, Holm, or no correction |
| `fst.fit_logistic_regression_table(df, ...)` | manuscript odds-ratio table for binary endpoints |
| `fst.fit_linear_regression_table(df, ...)` | manuscript beta/CI table for continuous endpoints |
| `fst.mcnemar_test(...)`, `fst.bootstrap_auc_difference(...)` | paired model-comparison statistics |
| `fst.normality_table(...)`, `fst.correlation_pvalue_table(...)` | statistical QC tables for supplements |
| `FlowTracker(title).add_step(...)` | record cohort/filter steps as explainable flow artifacts |
| `track_filter(flow, label=...)` | decorate DataFrame filters and record their outputs |
| `fv.find_best_threshold(y_true, y_prob, ...)` | threshold selection table |
| `fv.calibration_summary(y_true, y_prob, ...)` | calibration summary and bin table |
| `fv.subgroup_metric_table(df, ...)` | model metrics by subgroup |
| `fv.decision_curve_table(y_true, y_prob, ...)` | decision-curve net benefit table |
| `fv.bootstrap_concordance_index(...)` | bootstrap C-index for survival risk scores |
| `fv.survival_calibration_at_time(...)` | fixed-horizon survival calibration table |
| `fv.brier_score_at_time(...)` | fixed-horizon Brier score |
| `fv.external_survival_validation(...)` | external survival score validation |
| `fe.permutation_importance_table(estimator, X, y, ...)` | sklearn permutation importance table |
| `fe.partial_dependence_table(estimator, X, ...)` | one-way partial-dependence table |
| `fe.shap_summary_table(estimator, X, ...)` | ranked mean absolute SHAP summary table |
| `fe.shap_values_table(estimator, X, ...)` | long row-feature SHAP value table |
| `fe.explain_model_summary(...)` | merge importance, SHAP, metrics, notes, and feature QC |
| `fe.explain_patient_prediction(...)` | top signed drivers for one patient or row |
| `fa.create_provenance_manifest(...)` | JSON-serializable analysis provenance |
| `fa.write_manifest(manifest, path)` | write provenance JSON |

## Plotting Facade

```python
from fyron import plotting as fplot
```

| API | Purpose |
| --- | --- |
| `fplot.plot_kaplan_meier(...)` | Time-to-event curves with survival summaries |
| `fplot.plot_roc_curve(...)`, `fplot.plot_precision_recall_curve(...)` | Discrimination plots |
| `fplot.plot_calibration_curve(...)`, `fplot.plot_confusion_matrix(...)` | Probability/threshold diagnostics |
| `fplot.plot_grouped_boxplot(...)`, `fplot.plot_density(...)`, `fplot.plot_qq(...)`, `fplot.plot_reference_band_grid(...)` | Clinical distributions, Q-Q diagnostics, and reference bands by group/hue |
| `fplot.plot_correlation_heatmap(...)`, `fplot.plot_missingness_bar(...)` | Exploratory data checks |
| `fplot.plot_patterned_bar(...)`, `fplot.plot_forest_estimates(...)`, `fplot.plot_directional_ratio_rows(...)` | Publication-style summary figures |
| `fplot.plot_feature_selection_summary(...)`, `fplot.plot_stability_selection(...)` | Feature-selection summaries |
| `fplot.plot_survival_calibration(...)`, `fplot.plot_decision_curve(...)` | Validation curves |
| `fplot.plot_cohort_flow(...)`, `fplot.plot_segmentation_overlay_grid(...)` | Cohort and imaging QC figures |

## Documents And LLM

```python
from fyron import DocumentDownloader, LLMAgent
```

| API | Purpose |
| --- | --- |
| `DocumentDownloader.download_urls(urls)` | Download a list of URLs |
| `DocumentDownloader.download_from_df(df, url_col=...)` | Download documents referenced in a DataFrame |
| `LLMAgent.prompt(...)` | Single prompt |
| `LLMAgent.prompt_documents(...)` | Prompt over text snippets or file paths |
| `LLMAgent.prompt_dataframe(...)` | Prompt row-wise over a DataFrame column |
| `LLMAgent.describe_python_file(...)` | Generate methods-style text from code |

## Cohort

```python
from fyron.cohort import (
    build_survival_columns,
    join_cohort_tables,
    validate_cohort_table,
)
```

| API | Purpose |
| --- | --- |
| `join_cohort_tables(features, outcomes, on="patient_id", how="inner")` | Merge feature and outcome tables |
| `validate_cohort_table(df, required_columns=..., id_column=None)` | Fail fast on schema/key problems |
| `build_survival_columns(df, start_col, end_col, event_col, ...)` | Add duration and event columns |

## Survival

```python
from fyron.survival import (
    calculate_rmst,
    check_ph_assumptions,
    compare_rmst,
    create_survival_groups,
    fit_multivariate_cox,
    fit_univariate_cox,
    fit_weibull_aft,
    plot_aft_survival_curves,
    plot_kaplan_meier,
    train_gradient_survival_boosting,
)
```

| API | Purpose | Requires |
| --- | --- | --- |
| `plot_kaplan_meier` | KM curves, log-rank, risk counts, RMST annotation | `fyron[survival]` |
| `create_survival_groups` | median/tertile/quartile/custom groups | `fyron[survival]` |
| `calculate_rmst` | RMST by group | `fyron[survival]` |
| `compare_rmst` | pairwise RMST differences | `fyron[survival]` |
| `fit_univariate_cox` | one Cox model per covariate | `fyron[survival]` |
| `fit_multivariate_cox` | adjusted Cox PH model | `fyron[survival]` |
| `check_ph_assumptions` | PH diagnostics | `fyron[survival]` |
| `fit_weibull_aft` | Weibull AFT model | `fyron[survival]` |
| `plot_aft_survival_curves` | AFT profile curves | `fyron[survival]` |
| `train_gradient_survival_boosting` | non-linear censored risk model | `fyron[survival-ml]` |

## Statistics

```python
from fyron import statistics as fst
```

| API | Purpose | Requires |
| --- | --- | --- |
| `fst.normality_test` | Shapiro or D'Agostino-Pearson normality test | `fyron[statistics]` |
| `fst.compare_two_groups` | t-test, Mann-Whitney, paired t-test, or Wilcoxon | `fyron[statistics]` |
| `fst.compare_multiple_groups` | ANOVA or Kruskal-Wallis | `fyron[statistics]` |
| `fst.categorical_test` | chi-square or Fisher exact test | `fyron[statistics]` |
| `fst.correlation_test` | Pearson, Spearman, or Kendall association test | `fyron[statistics]` |
| `fst.bootstrap_summary` | bootstrap CI for mean, median, or custom score | `fyron[statistics]` |
| `fst.bootstrap_metric` | bootstrap CI for custom metrics over aligned arrays | `fyron[statistics]` |
| `fst.bootstrap_binary_classification_metrics` | bootstrap CIs for AUC, sensitivity, specificity, F1, and confusion counts | `fyron[statistics]` |

## Machine Learning

```python
from fyron import ml
```

| API | Purpose |
| --- | --- |
| `ml.train_test_split_data` | stratified train/test split |
| `ml.compute_class_weights` | sklearn class weight dictionary |
| `ml.compute_scale_pos_weight` | XGBoost imbalance ratio |
| `ml.train_random_forest` | fit/evaluate RF classifier |
| `ml.train_xgboost` | fit/evaluate XGBoost classifier |
| `ml.calculate_classification_metrics` | clinical binary/multiclass metrics |
| `ml.cross_validate_model` | stratified CV with fold summaries |
| `ml.grid_search_model` | GridSearchCV wrapper |
| `ml.get_default_param_grid` | default grids for RF/XGB/survival boosting |
| `ml.get_feature_importance` | feature importance DataFrame |
| `ml.plot_feature_importance` | importance plot |
| `ml.run_boruta_feature_selection` | optional Boruta all-relevant selection |
| `ml.run_classification_pipeline` | convenience end-to-end classifier pipeline |
| `ml.save_estimator` / `ml.load_estimator` | joblib persistence |

## Clinical Plots

```python
from fyron import ml
```

| API | Purpose |
| --- | --- |
| `ml.plot_kaplan_meier` | Kaplan-Meier curves, log-rank comparison, risk counts, RMST annotation |
| `ml.plot_roc_curve` | ROC curve and AUC |
| `ml.plot_precision_recall_curve` | precision-recall curve and average precision |
| `ml.plot_calibration_curve` | observed vs predicted probability |
| `ml.plot_confusion_matrix` | count heatmap |
| `ml.plot_grouped_boxplot` | grouped clinical boxplots with optional hue and patient-level jitter |
| `ml.plot_grouped_bar_with_significance` | grouped/hue summary bars with statistical notation |
| `ml.plot_density` | smoothed clinical density curves by optional hue |
| `ml.plot_qq` | normal-theory Q-Q diagnostics for residuals, biomarkers, and scores |
| `ml.plot_missingness_bar` | missingness summary bar plot |
| `ml.plot_feature_selection_summary` | feature selection selected/rejected summary |
| `ml.plot_stability_selection` | stability selection frequency plot |
| `ml.plot_bland_altman` | measurement agreement plot |
| `ml.plot_waterfall` | ordered patient-level response/change plot |
| `ml.plot_table_one_summary` | Table 1 p-value overview |
| `ml.plot_correlation_heatmap` | numeric correlation matrix, returns `corr_df` |
| `ml.plot_patterned_bar` | grouped bar plot with hatches and optional errors |
| `ml.plot_metric_bars` | model metric comparison bars |
| `ml.plot_risk_score_distribution` | BOARISK-style event/censoring risk score distribution |
| `ml.plot_signed_feature_weights` | signed coefficient bars with risk direction hatches |
| `ml.plot_significance_bars` | p-values shown as `-log10(p)` bars |
| `ml.plot_volcano` | feature screening by effect size and p-value |
| `ml.plot_swimmer` | patient treatment timeline with event markers |
| `ml.plot_raincloud` | half-violin, box, and patient-point distributions |
| `ml.plot_alluvial_flow` | categorical paths across ordered stages |
| `ml.plot_binned_marker_heatmap` | discrete patient-feature marker grid |
| `ml.plot_reference_band_grid` | precomputed reference bands across age, biological age, or another continuous axis, with optional presets |
| `ml.plot_directional_ratio_rows` | odds or hazard ratios with protective/hazardous direction bands |
| `ml.plot_forest_estimates` | estimates with confidence intervals in forest layout |

## BOA Visualization

```python
from fyron.visualization import (
    SegmentationLayer,
    create_boa_segmentation_collage,
    plot_volume_difference_heatmap,
)
```

| API | Purpose |
| --- | --- |
| `SegmentationLayer(kind, display_mode=..., opacity=...)` | Configure one BOA mask panel |
| `create_boa_segmentation_collage(...)` | Render multi-patient CT/segmentation collage |
| `plot_volume_difference_heatmap(...)` | Render aligned CT/MR slice comparison panels and return a difference summary table |

## Return-Type Conventions

| Pattern | Used by |
| --- | --- |
| `DataFrame` | FHIR, SQL, cohort, metrics tables, RMST results |
| dictionary | training helpers, search helpers, survival boosting |
| dataclass | Kaplan-Meier plot result |
| `(fig, ax)` | most plotting helpers |
| `(fig, ax, table)` | correlation heatmap |
| fitted estimator/fitter | RF, XGBoost, Cox, AFT, survival boosting |
