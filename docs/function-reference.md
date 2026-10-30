# Function Reference

This page is a practical function-level reference. It lists each major public function, required inputs, optional arguments, and return values. Module pages explain workflows and examples in more depth.

Use this page when you already know which module you need and want to check a call quickly. For conceptual guidance, start with the module pages; this reference is intentionally dense and optimized for lookup while coding.

For exhaustive per-function documentation generated from source signatures and docstrings, use the [Complete Function Reference](reference/index.md). It includes public functions, classes, methods, parameters, defaults, return notes, and import paths.

## Reading Function Signatures

Fyron APIs are built around explicit clinical data science inputs. The same parameter names appear across modules:

| Parameter pattern | Meaning |
| --- | --- |
| `df`, `data`, `cohort` | A `pandas.DataFrame`, usually one row per patient, resource, feature, or result. |
| `duration_col`, `time_col` | Follow-up duration column for survival analysis. Values should be positive. |
| `event_col` | Endpoint/event indicator. Survival workflows use `1` for event and `0` for censored. |
| `group_col`, `hue`, `strata` | Clinical grouping variable used for summaries, plots, or model stratification. |
| `id_col`, `patient_col`, `subject_col` | Stable identifier used for joins, validation, or FHIR subject references. |
| `X`, `y` | Feature matrix and target labels for machine learning. |
| `y_true`, `y_pred`, `y_prob` | Observed labels, hard predictions, and positive-class probabilities. |
| `save_path`, `output`, `write` | File destination for generated artifacts. |
| `random_state` | Reproducibility seed; record it in manifests for final analyses. |

## Where To Learn The Workflow

| Topic | Detailed page |
| --- | --- |
| FHIR REST extraction and pagination | [FHIR REST](modules/fhir/rest.md) |
| DICOMweb downloads and `download_id` | [DICOMDownloader](modules/dicom/downloader.md) |
| BOA feature extraction | [BOA Extraction](modules/boa-extraction.md) |
| Cohort construction | [Cohort Tables](modules/cohort.md) |
| Descriptive tables | [Descriptive Analysis](modules/descriptive.md) |
| Survival analysis | [Survival Analysis](modules/survival.md) |
| Machine learning | [Machine Learning](modules/ml.md) |
| Validation | [Model Validation](modules/validation.md) |
| Publication figures | [Clinical Plotting](modules/plotting.md) |
| Provenance | [Audit & Provenance](modules/audit.md) |

## CLI Commands

Global flags: `--verbose`, `--quiet`, `--no-color`, `--json-log`, and `--no-progress`.

| Command | Required | Common optional arguments | Output |
| --- | --- | --- | --- |
| `fyron banner` | none | `--no-color`, `--no-version`, `--theme bf/plain/mono` | terminal banner |
| `fyron spark` | none | `--no-color`, `--no-version`, `--theme bf/plain/mono` | terminal easter egg banner |
| `fyron docs-build` | none | none | static site in `site/` |
| `fyron fhir-rest` | `--resource`, `--output` | `--base-url`, `--param`, `--params-json`, `--input`, `--column-map`, `--fhir-paths`, `--format` | CSV/JSON |
| `fyron fhir-build-bundle` | `--input`, `--mapping`, `--resource`, `--subject-col`, `--output` | IDs, imaging UIDs, bundle type, summary/validation JSON, submit | FHIR JSON bundle |
| `fyron dicom-download` | output target plus study/CSV IDs | endpoint/auth, `--output-format`, `--full-study`, `--manifest`, `--results-csv` | DICOM/NIfTI and manifests |
| `fyron synthetic-dicom` | `--volume`, `--output-dir` | `--reference-dicom`, `--patient-id`, `--manifest` | DICOM slices |
| `fyron dicom-seg` | `--mask`, `--source-dicom`, `--segments`, `--output` | `--series-description`, `--algorithm-name`, `--algorithm-type`, `--manufacturer`, `--validate`, `--summary-json` | DICOM SEG |
| `fyron boa-extract` | `--cohort-folder`, `--output` | feature-family flags, `--num-workers` | CSV |
| `fyron boa-radiomics` | `--cohort-folder`, `--output` | `--segmentation`, `--num-workers` | CSV |
| `fyron imaging-qc` | at least one imaging input and `--output` | `--dicom-dir`, `--nifti`, `--mask`, `--format` | CSV/JSON |
| `fyron audit-manifest` | `--write` | `--title`, `--input`, `--output`, `--param`, `--note` | provenance JSON |

## Console And Banner

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `configure_logging(level="INFO", ...)` | none | color, JSON mode, stream | configured `fyron` logger |
| `get_logger(name=None)` | none | logger name | logger under `fyron` |
| `console_message(message, ...)` | message | level, color, prefix, quiet, stream | rendered text |
| `success(...)`, `warning(...)`, `error(...)`, `info(...)` | message | color, prefix, quiet, stream | rendered text |
| `format_path(path)` | path | none | compact display path |
| `format_count(label, value)` | label and count | none | formatted count string |
| `format_duration(seconds)` | seconds | none | human duration string |
| `supports_color(stream=None)` | none | stream | boolean ANSI support |
| `get_banner(...)` / `print_banner(...)` | none | color, version, theme | compatibility helpers for the opt-in banner easter egg |
| `get_run_header(...)` / `get_run_footer(...)` | none | command, version, timestamp, status, duration, outputs | run summary text |

## Core I/O

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `load_env(path=None, ...)` | none | override, missing warning | loaded path or `None` |
| `ensure_parent_dir(path)` | path | none | `Path` |
| `read_json(path, ...)` | path | JSON load kwargs | Python object |
| `write_json(payload, path, ...)` | payload, path | indent, parent creation | output `Path` |
| `read_table(path, ...)` | path | file format, pandas kwargs | DataFrame |
| `write_table(df, path, ...)` | DataFrame, path | file format, parent creation, index, pandas kwargs | output `Path` |
| `summarize_table(df, ...)` | DataFrame | name | summary dict |
| `describe_file(path)` | path | none | file metadata dict |
| `TeableClient.read_cohort(...)` | table ID | ID column, required columns, view, max records | validated DataFrame |
| `TeableClient.write_research_cohort(...)` | table ID, DataFrame | mode, metadata, ID column, typecast | audit dict |
| `TeableClient.create_research_cohort_table(...)` | base ID, name | DataFrame, fields, metadata | table dict |
| `TeableClient.summarize_teable_table(...)` | table ID | view, projection, max records | summary dict |
| `S3Storage.read_table(...)` / `S3Storage.write_table(...)` | S3 key | format, pandas kwargs | DataFrame / S3 URI |
| `read_s3_table(uri)` / `write_s3_table(df, uri)` | S3 URI | table kwargs | DataFrame / S3 URI |

## FHIR REST And SQL

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `FHIRRestClient.search_df(resource_type, ...)` | resource type | params, page limit, FHIR paths, processing mode | DataFrame or dict of DataFrames |
| `FHIRRestClient.search_df_from(df, ...)` | input table, resource type, column map | params, page limit, FHIR paths, metadata columns | DataFrame or dict of DataFrames |
| `FHIRRestClient.query_df(...)` / `query_df_from(...)` | same as search aliases | compatibility names | DataFrame or dict of DataFrames |
| `FHIRRestClient.create_resource(resource, ...)` | resource dict | resource type override | `FHIRWriteResult` |
| `FHIRRestClient.update_resource(resource, ...)` | resource dict | resource ID/type override | `FHIRWriteResult` |
| `FHIRRestClient.submit_bundle(bundle)` | transaction bundle | none | `FHIRWriteResult` |
| `FHIRSQLClient.query_df(sql, ...)` | SQL string | params, rename | DataFrame |
| `FHIRSQLClient.query_df_stream(sql, ...)` | SQL string | params, rename, chunk size | iterator of DataFrames |
| `FHIRSQLClient.query_df_parallel(jobs, ...)` | query jobs | worker count, merge options | DataFrame |
| `FHIRSQLClient.query_df_from(df, ...)` | input table, SQL template, column map | chunking and parallel options | DataFrame |

## Imaging

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `read_dicom_header(dicom_path, ...)` | `dicom_path` | `stop_before_pixels=True`, `force=False`, `as_dict=False`, `selected_tags=None` | `pydicom.Dataset` or `dict` |
| `get_dicom_series_ids(dicom_dir, ...)` | `dicom_dir` | `include_metadata=False`, `recursive=False` | `list[str]` or DataFrame |
| `read_dicom_series(study_path, series_id, ...)` | `study_path`, `series_id` | `return_array=False` | `SimpleITK.Image` or `(image, array)` |
| `read_nifti(nifti_path, ...)` | `nifti_path` | `return_array=False` | `SimpleITK.Image` or `(image, array)` |
| `write_nifti(image, output_path, ...)` | `image`, `output_path` | `reference_image=None`, `compress=True` | resolved `Path` |
| `normalize_ct(image, ...)` | `image` | `hu_min=-1000.0`, `hu_max=3000.0` | same type as input |
| `normalize_mr(image, ...)` | `image` | `mode="percentile"`, `percentile=99.0`, `value=None`, `ignore_zeros=True`, `clip=True` | same type as input |
| `summarize_dicom_series_geometry(dicom_dir, ...)` | `dicom_dir` | `recursive=False` | geometry DataFrame |
| `summarize_nifti_geometry(paths)` | `paths` | none | geometry DataFrame |
| `check_image_mask_alignment(image, mask)` | `image`, `mask` | none | alignment dict |
| `summarize_mask_volume(mask, ...)` | `mask` | `labels=None`, `spacing=None` | volume DataFrame |
| `summarize_intensity_range(image, ...)` | `image` | `mask=None`, `percentiles=(0.5, 99.5)` | summary dict |
| `dice_score(mask_true, mask_pred, ...)` | two masks | `label` | float |
| `hausdorff_distance(mask_true, mask_pred, ...)` | two masks | `label`, `spacing`, `percentile` | float |
| `surface_dice(mask_true, mask_pred, ...)` | two masks | `label`, `tolerance`, `spacing` | float |
| `volume_difference(mask_true, mask_pred, ...)` | two masks | `label`, `spacing` | dict |
| `segmentation_metric_table(mask_true, mask_pred, ...)` | two masks | labels, spacing, tolerance | DataFrame |

See [Imaging](modules/imaging.md) for full parameter explanations.

## FHIR Builder

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `build_observation(...)` | `subject`, `code` | value, components, data_absent_reason, performer, encounter, derived_from, method, body_site, version | Observation dict |
| `build_observation_component(...)` | `code` | value, unit, value_type, data_absent_reason, interpretation | Observation component dict |
| `build_encounter(...)`, `build_procedure(...)` | patient subject and code/context | ids, period/performed, profile metadata | Encounter/Procedure dict |
| `build_medication_statement(...)`, `build_service_request(...)`, `build_specimen(...)` | patient subject and resource-specific code/type | ids, status, profile metadata | resource dict |
| `build_condition(...)` | `subject`, `code` | clinical/verification status, onset, evidence, version | Condition dict |
| `build_document_reference(...)` | `subject` plus URL/data attachment values | title, content type, date, description, version | DocumentReference dict |
| `build_diagnostic_report(...)` | `subject`, `code` | results, imaging study refs, conclusion, presented form | DiagnosticReport dict |
| `build_imaging_study_reference(...)` | `subject`, `study_instance_uid` | series UID/description, modality, started, version | ImagingStudy dict |
| `build_model_device(...)` / `build_endpoint(...)` | model/endpoint identity | version, model endpoint, manufacturer | Device/Endpoint dict |
| `build_provenance(...)` | `targets` | agent, entity, recorded, activity, prompt version | Provenance dict |
| `build_llm_extraction_bundle(...)` | subject, source report, model name, bundle type | observations, conditions, summary, endpoint, versions, id_prefix | Bundle dict |
| `build_imaging_measurement_bundle(...)` | subject, study UID, measurements, bundle type | series UID, model info, id_prefix, version | Bundle dict |
| `build_bundle(resources, bundle_type=...)` | resources, explicit bundle type | bundle id, transaction method, conditional create, version | Bundle dict |
| `loinc(...)`, `snomed(...)`, `icd10(...)`, `dicom_code(...)` | code | display | Coding dict |
| `ucum_quantity(...)` | value, unit | code | Quantity dict |
| `write_fhir_json(payload, path)` | payload, path | none | resolved path |
| `read_fhir_json(path)` | path | none | payload dict |
| `summarize_fhir_resource(...)` / `summarize_fhir_bundle(...)` | resource/bundle | none | summary dict |
| `validate_fhir_resource(...)` / `validate_fhir_bundle(...)` | resource/bundle | version | validated dict or raises |
| `validate_fhir_references(...)` | bundle | none | reference report dict |
| `build_observations_from_dataframe(...)` | DataFrame, mapping, subject column | id, bundle type, transaction method | mapping result dict |
| `build_conditions_from_dataframe(...)` | DataFrame, mapping, subject column | id/evidence/status mappings | mapping result dict |
| `build_document_references_from_dataframe(...)` | DataFrame, mapping, subject column | URL/title/content mappings | mapping result dict |
| `build_imaging_measurements_from_dataframe(...)` | DataFrame, mapping, subject and study UID columns | series UID, id, model metadata | mapping result dict |
| `build_bundle_from_dataframe(...)` | DataFrame, resource type, mapping, subject column | dispatch and transaction options | mapping result dict |
| `validate_fhir_mapping(...)`, `validate_fhir_payload(...)` | mapping or FHIR payload | DataFrame, strict mode | validation report dict |

See [FHIR Builder](modules/fhir/builder.md) for LLM extraction and imaging measurement examples.

## DICOM Export

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `write_synthetic_nifti(volume, output_path, ...)` | `volume`, `output_path` | `reference_image`, `spacing`, `origin`, `direction`, `dtype`, `compress`, `metadata` | resolved `Path` |
| `write_synthetic_dicom_series(volume, output_dir, ...)` | `volume`, `output_dir` | `reference_dicom_dir`, `reference_datasets`, `patient_id`, UIDs, modality, description, intensity mode, rescale tags, patient-copy flag | manifest DataFrame |
| `write_dicom_seg(mask, source_images, output_path, segment_descriptions, ...)` | `mask`, `source_images`, `output_path`, `segment_descriptions` | `series_description`, `manufacturer`, algorithm metadata | resolved `Path` |
| `label_map_to_segments(label_map, labels)` | `label_map`, `labels` | none | binary stack `(segment, z, y, x)` |
| `validate_dicom_seg(path, ...)` | `path` | `source_images=None` | metadata dict |
| `summarize_dicom_seg(path, ...)` | `path` | `source_images=None` | metadata dict |
| `load_source_dicom_series(source_dicom_dir, ...)` | `source_dicom_dir` | `sort_by="geometry"` | sorted source DICOM datasets |
| `read_segment_descriptions(path)` | `path` | none | validated segment description list |
| `validate_segment_descriptions(segment_descriptions)` | segment list | none | normalized segment description list |

See [Synthetic Export](modules/dicom/synthetic.md) and [DICOM SEG](modules/dicom/seg.md) for scientific context and examples.

## Datasets

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `make_clinical_cohort(n=40, ...)` | none | `n`, `random_state=42` | clinical DataFrame |
| `make_survival_cohort(n=40, ...)` | none | `n`, `random_state=42` | survival DataFrame |
| `make_classification_cohort(n=80, ...)` | none | `n`, `random_state=42` | `(X, y)` |
| `make_nifti_pair(output_dir, ...)` | `output_dir` | `shape=(4, 8, 8)` | dict of image/mask paths |
| `make_dicom_series(output_dir, ...)` | `output_dir` | `shape`, `patient_id` | list of DICOM paths |
| `make_boa_like_folder(output_dir)` | `output_dir` | none | BOA-like root path |
| `prepare_nnunetv2_dataset(manifest, output_dir, ...)` | manifest, output dir, dataset ID/name | columns, labels, copy mode, validation | written-file manifest |
| `prepare_yolo_classification_dataset(manifest, output_dir, ...)` | manifest, output dir | class/split columns, slice behavior, copy mode | written-image manifest |
| `prepare_yolo_detection_dataset(manifest, output_dir, ...)` | manifest, output dir | class/box columns, slice behavior, copy mode | image/label manifest |
| `validate_nnunetv2_dataset(dataset_dir)` | dataset dir | none | QC DataFrame |
| `validate_yolo_dataset(dataset_dir, ...)` | dataset dir | `task="detect"` or `"classify"` | QC DataFrame |

## Cohort

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `join_cohort_tables(features, outcomes, ...)` | `features`, `outcomes` | `on="patient_id"`, `how="inner"`, suffix options | merged DataFrame |
| `validate_cohort_table(df, ...)` | `df` | `required_columns=None`, `id_column=None` | validated DataFrame / raises on problems |
| `build_survival_columns(df, start_col, end_col, event_col, ...)` | `df`, `start_col`, `end_col`, `event_col` | `time_col="time"`, date parsing/output options | DataFrame with `time` and `event` |

## Phenotyping

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `define_code_phenotype(df, code_col, codes, ...)` | table, code column, codes | patient/date/code-system columns | phenotype table |
| `define_lab_threshold_phenotype(df, value_col, threshold, ...)` | table, value column, threshold | direction, patient/date columns | phenotype table |
| `define_medication_exposure(df, medication_col, medications, ...)` | table, medication column, medication list | patient/start/end columns | exposure table |
| `combine_phenotypes(tables, ...)` | phenotype tables | patient column, strategy, name | combined phenotype table |
| `phenotype_summary(df, phenotype_col, ...)` | table and phenotype column | patient/group columns | prevalence table |

## Survival

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `ml.plot_kaplan_meier(df, duration_col, event_col, ...)` | `df`, `duration_col`, `event_col` | `group_col`, `split_column`, CI/risk count/style/save/RMST options | `KaplanMeierPlotResult` |
| `create_survival_groups(df, column, method, out_col, ...)` | `df`, `column`, `method`, `out_col` | `bins`, `labels`, method-specific options | DataFrame copy |
| `calculate_rmst(df, duration_col, event_col, ...)` | `df`, `duration_col`, `event_col` | `group_col=None`, `tau=None` | RMST DataFrame |
| `compare_rmst(df, duration_col, event_col, group_col, ...)` | `df`, `duration_col`, `event_col`, `group_col` | `reference=None`, `tau=None` | pairwise comparison DataFrame |
| `fit_univariate_cox(df, duration_col, event_col, covariates, ...)` | `df`, `duration_col`, `event_col`, `covariates` | `strata=None`, `robust=False` | result table and fitters |
| `fit_multivariate_cox(df, duration_col, event_col, ...)` | `df`, `duration_col`, `event_col`, one of `covariates`/`formula` | `strata=None`, `robust=False` | result table and fitter |
| `check_ph_assumptions(df, fitter, ...)` | `df`, fitted Cox model | `show_plots=False`, diagnostic options | summary and violations |
| `fit_weibull_aft(df, duration_col, event_col, ...)` | `df`, `duration_col`, `event_col`, one of `covariates`/`formula` | `robust=False` | result table and fitter |
| `plot_aft_survival_curves(fitter, covariates, profiles, ...)` | `fitter`, `covariates`, `profiles` | `plot_baseline=True`, `figsize`, `ax`, `plot_kwargs` | figure/axes/fitter dict |
| `train_gradient_survival_boosting(X_train, duration_train, event_train, ...)` | `X_train`, `duration_train`, `event_train` | test data, `random_state=42`, model params | model, risk scores, concordance |

## Statistics

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `normality_test(values, ...)` | `values` | `method="shapiro"` | `StatisticalTestResult` |
| `compare_two_groups(group_a, group_b, ...)` | `group_a`, `group_b` | `paired`, `method`, `alternative`, `equal_var` | `StatisticalTestResult` |
| `compare_multiple_groups(groups, ...)` | `groups` | `method="auto"` | `StatisticalTestResult` |
| `categorical_test(table, ...)` | contingency `table` | `method="auto"` | `StatisticalTestResult` |
| `correlation_test(x, y, ...)` | `x`, `y` | `method="spearman"`, `alternative` | `StatisticalTestResult` |
| `bootstrap_summary(values, ...)` | `values` | `statistic`, `n_rounds`, `alpha`, `random_state` | `BootstrapResult` |
| `bootstrap_metric(*arrays, metric_func=...)` | aligned arrays, `metric_func` | `metric_name`, `n_rounds`, `alpha`, `random_state` | `BootstrapResult` |
| `bootstrap_binary_classification_metrics(y_true, y_pred, ...)` | `y_true`, `y_pred` | `y_prob`, metric list, `pos_label`, `n_rounds`, `alpha` | DataFrame |
| `cohens_d(group_a, group_b)` | two groups | none | float |
| `cliffs_delta(group_a, group_b)` | two groups | none | float |
| `cramers_v(table)` | contingency table | none | float |
| `odds_ratio_ci(table)` | 2x2 table | alpha, correction | dict |
| `risk_ratio_ci(table)` | 2x2 table | alpha, correction | dict |
| `standardized_mean_difference(group_a, group_b, ...)` | two groups | categorical flag | float |

## Machine Learning

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `train_test_split_data(X, y, ...)` | `X`, `y` | `test_size=0.2`, `stratify=True`, `random_state=42` | `X_train`, `X_test`, `y_train`, `y_test` |
| `compute_class_weights(y, ...)` | `y` | class-weight options | class-to-weight dict |
| `compute_scale_pos_weight(y, ...)` | `y` | positive label options | float ratio for XGBoost |
| `sample_weights_for_sklearn(y, ...)` | `y` | class-weight options | sample-weight array |
| `train_random_forest(X_train, y_train, ...)` | `X_train`, `y_train` | test data, `class_weight`, `random_state`, `plot`, RF params | model/predictions/metrics/figures dict |
| `train_xgboost(X_train, y_train, ...)` | `X_train`, `y_train` | test data, `scale_pos_weight`, `random_state`, `plot`, XGB params | model/predictions/metrics/figures dict |
| `calculate_classification_metrics(y_true, y_pred, ...)` | `y_true`, `y_pred` | `y_prob=None`, `pos_label=None` | metrics dict |
| `cross_validate_model(estimator, X, y, ...)` | `estimator`, `X`, `y` | `cv=5`, `return_models`, `return_oof_predictions`, `pos_label` | CV result dict |
| `nested_cross_validate_model(estimator, param_grid, X, y, ...)` | estimator, grid, X, y | outer/inner CV, scoring | nested CV result dict |
| `evaluate_external_validation(estimator, X_external, y_external, ...)` | fitted estimator and external data | locked threshold, pos label | validation dict |
| `evaluate_locked_threshold(y_true, y_prob, ...)` | labels, probabilities, threshold | labels | metrics dict |
| `fit_probability_calibrator(estimator, X_calibration, y_calibration, ...)` | fitted estimator and calibration data | method | calibrator |
| `apply_probability_calibrator(calibrator, X)` | calibrator and features | positive class index | probabilities |
| `model_card_summary(estimator, ...)` | estimator | X, y, metrics, intended use | dict |
| `grid_search_model(estimator, param_grid, X_train, y_train, ...)` | `estimator`, `param_grid`, `X_train`, `y_train` | validation data, scoring/CV/jobs/refit/random state | search result dict |
| `get_default_param_grid(model_name)` | `model_name` | none | parameter grid dict |
| `get_feature_importance(model, ...)` | `model` | `feature_names=None` | importance DataFrame |
| `plot_feature_importance(model_or_df, ...)` | model or importance table | `feature_names`, `top_n`, `save_path` | `(fig, ax)` |
| `run_boruta_feature_selection(X, y, ...)` | `X`, `y` | Boruta/model params | selected features, ranking, transform |
| `run_classification_pipeline(X, y, ...)` | `X`, `y` | model/split/imbalance/Boruta/search/plot/model params | full pipeline result dict |
| `save_estimator(model, path)` | `model`, `path` | none | writes joblib file |
| `load_estimator(path)` | `path` | none | loaded estimator |

## Clinical Plots

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `plot_kaplan_meier(df, duration_col, event_col, ...)` | `df`, `duration_col`, `event_col` | `group_col`, `split_column`, CI/risk count/style/save/RMST options | `KaplanMeierPlotResult` |
| `plot_roc_curve(y_true, y_prob, ...)` | `y_true`, `y_prob` | `title`, `ax`, `save_path`, `fmt`, `pos_label` | `(fig, ax)` |
| `plot_precision_recall_curve(y_true, y_prob, ...)` | `y_true`, `y_prob` | `title`, `ax`, `save_path`, `fmt`, `pos_label` | `(fig, ax)` |
| `plot_calibration_curve(y_true, y_prob, ...)` | `y_true`, `y_prob` | `n_bins=10`, `strategy`, `title`, `ax`, `save_path`, `fmt`, `pos_label` | `(fig, ax)` |
| `plot_confusion_matrix(y_true, y_pred, ...)` | `y_true`, `y_pred` | `title`, `ax`, `save_path`, `fmt`, `pos_label` | `(fig, ax)` |
| `plot_grouped_boxplot(data, x, y, ...)` | `data`, `x`, `y` | `hue`, `order`, `hue_order`, labels, palette, jitter/save options | `(fig, ax)` |
| `plot_grouped_bar_with_significance(data, x, y, ...)` | `data`, `x`, `y` | `hue`, estimator/error/test/comparison settings, notation thresholds, save | `(fig, ax, table)` |
| `plot_density(data, x, ...)` | `data`, `x` | `hue`, `hue_order`, labels, palette, fill, bandwidth, gridsize, save | `(fig, ax)` |
| `plot_qq(data, ...)` | vector data, `value_col`, or `columns` | `group_col`, line mode, facets, palette, labels, save | `(fig, axes, table)` |
| `plot_missingness_bar(data, ...)` | missingness summary table | column/group/value names, save options | `(fig, ax)` |
| `plot_feature_selection_summary(data, ...)` | feature-selection summary table | feature/selected/score columns, top N, save | `(fig, ax)` |
| `plot_stability_selection(data, ...)` | stability-selection table | feature/frequency columns, threshold, top N, save | `(fig, ax)` |
| `plot_bland_altman(method_a, method_b, ...)` | two aligned measurements | title/save options | `(fig, ax)` |
| `plot_waterfall(values, ...)` | ordered numeric values | labels, threshold, title/save options | `(fig, ax)` |
| `plot_table_one_summary(data, ...)` | Table 1 long table with p-values | variable/p-value columns, save | `(fig, ax)` |
| `plot_survival_calibration(data, ...)` | calibration table | observed/predicted columns, save | `(fig, ax)` |
| `plot_decision_curve(data, ...)` | decision-curve table | threshold/net-benefit columns, save | `(fig, ax)` |
| `plot_time_dependent_auc(data, ...)` | time/AUC table | column names, save | `(fig, ax)` |
| `plot_cohort_flow(data, ...)` | flow table | step/count columns, save | `(fig, ax)` |
| `plot_segmentation_overlay_grid(image, mask, ...)` | image and mask arrays | slice indices, label, alpha, save | `(fig, axes)` |
| `plot_dice_by_label(data, ...)` | segmentation metric table | label/Dice columns, save | `(fig, ax)` |
| `plot_external_validation_metrics(data, ...)` | metric dict/table | metric/value columns, save | `(fig, ax)` |
| `plot_correlation_heatmap(data, ...)` | `data` | `columns`, `method`, `title`, `annotate`, `mask_upper`, `cmap`, range, `ax`, `save_path` | `(fig, ax, corr_df)` |
| `plot_patterned_bar(data, x, y, ...)` | `data`, `x`, `y` | `group`, `error`, labels, orientation, palette, hatches, annotate, save | `(fig, ax)` |
| `plot_metric_bars(metrics, ...)` | `metrics` | `metrics_to_plot`, `model_col`, `title`, `ax`, `save_path` | `(fig, ax)` |
| `plot_risk_score_distribution(data, ...)` | `data` with risk score column | `risk_col`, `event_col`, labels, jitter/violin, palette, save | `(fig, ax)` |
| `plot_signed_feature_weights(data, ...)` | `data` with feature and weight columns | `feature_col`, `weight_col`, `top_n`, labels, save | `(fig, ax)` |
| `plot_significance_bars(data, ...)` | `data` with label and p-value columns | `label_col`, `p_col`, `threshold`, `annotate`, save | `(fig, ax, table)` |
| `plot_volcano(data, ...)` | feature, effect, and p-value columns | group column, thresholds, labels, palette, save | `(fig, ax)` |
| `plot_swimmer(data, ...)` | patient, start, and end columns | group and event columns, palette, save | `(fig, ax)` |
| `plot_raincloud(data, ...)` | group and numeric value columns | order, palette, random state, save | `(fig, ax)` |
| `plot_alluvial_flow(data, ...)` | path, stage, category, and value columns | stage order, palette, save | `(fig, ax)` |
| `plot_binned_marker_heatmap(data, ...)` | row, column, and bin columns | row/column order, colormap, missing color, save | `(fig, ax)` |
| `plot_qq(data, ...)` | vector data, `value_col`, or `columns` | grouped overlays/facets, reference line mode, labels, save | `(fig, axes, table)` |
| `plot_reference_band_grid(data, ...)` | precomputed reference-band intervals | x/lower/upper/band/facet columns, optional line overlay, presets, order, colors, save | `(fig, axes)` |
| `plot_directional_ratio_rows(data, ...)` | `data` with feature and ratio columns | optional CI, p-value, group, n columns, OR/HR table headers, reference, log scale, save | `(fig, ax)` |
| `plot_forest_estimates(data, ...)` | `data` with estimate and CI columns | label/estimate/CI column names, `p_col`, `n_col`, `reference`, `log_scale`, save | `(fig, ax)` |

## Preprocessing, Reporting, Validation, Explainability, Audit

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `summarize_missingness(df, ...)` | `df` | columns, `group_col` | missingness DataFrame |
| `find_duplicate_ids(df, ...)` | `df` | `id_col` | duplicate rows |
| `compare_train_test_balance(train, test, ...)` | train/test DataFrames | columns | balance DataFrame |
| `detect_potential_leakage(columns, ...)` | DataFrame or column list | keyword lists | leakage flag table |
| `fit_imputer(df, ...)` | DataFrame | numeric/categorical strategies | imputer dict |
| `apply_imputer(df, imputer)` | DataFrame and imputer | none | imputed DataFrame |
| `fit_categorical_encoder(df, ...)` | DataFrame | rare handling, drop-first | encoder dict |
| `apply_categorical_encoder(df, encoder)` | DataFrame and encoder | none | encoded DataFrame |
| `describe_numeric(df, ...)` | DataFrame | columns, group column, digits | numeric summary DataFrame |
| `describe_categorical(df, ...)` | DataFrame | columns, group column, missing handling | categorical summary DataFrame |
| `compare_descriptive_groups(df, group_col, ...)` | DataFrame and group column | numeric/categorical columns | p-value summary table |
| `create_table_one(df, ...)` | DataFrame | group, numeric/categorical columns | long Table 1 table |
| `summarize_endpoint(df, event_col, ...)` | DataFrame and event column | time/group columns | endpoint summary table |
| `univariate_feature_screening(X, y, ...)` | features, target | task, alpha, correction | selection result dict |
| `variance_filter(X, ...)` | features | threshold | selection result dict |
| `correlation_filter(X, ...)` | features | threshold, method | selection result dict |
| `model_importance_selection(estimator, X, y, ...)` | estimator, features, target | threshold/top N | selection result dict |
| `permutation_importance_selection(estimator, X, y, ...)` | estimator, features, target | repeats, scoring, threshold/top N | selection result dict |
| `stability_selection(estimator, X, y, ...)` | estimator, features, target | rounds, fraction, threshold | selection result dict |
| `combine_feature_selection_results(results, ...)` | selection results | strategy, minimum methods | consensus result dict |
| `summarize_baseline_table(df, ...)` | `df` | group, continuous/categorical columns, digits | baseline table |
| `cohort_flow_table(steps)` | step dictionaries | none | flow table |
| `metrics_table(metrics, ...)` | metrics mapping/DataFrame | model column, digits | report metric table |
| `p_value_correction_table(df, ...)` | DataFrame with p-values | method, alpha | adjusted p-value table |
| `fit_logistic_regression_table(df, ...)` | DataFrame, outcome, covariates | intercept, alpha, p adjustment | OR table |
| `fit_linear_regression_table(df, ...)` | DataFrame, outcome, covariates | intercept, alpha, p adjustment | beta table |
| `vif_table(df, covariates)` | DataFrame and covariates | none | multicollinearity table |
| `mcnemar_test(y_true, pred_a, pred_b, ...)` | paired labels/predictions | exact mode | McNemar table |
| `bootstrap_auc_difference(y_true, prob_a, prob_b, ...)` | labels and two probability vectors | rounds, alpha, seed | AUC difference table |
| `FlowTracker(title).add_step(label, df, ...)` | step label and DataFrame | reason, metadata | DataFrame unchanged and recorded flow step |
| `track_filter(flow, label=...)` | `FlowTracker`, label | reason, metadata | decorated DataFrame filter |
| `find_best_threshold(y_true, y_prob, ...)` | labels, probabilities | metric, thresholds, positive label | threshold dict/table |
| `calibration_summary(y_true, y_prob, ...)` | labels, probabilities | bins, positive label | summary dict and bin table |
| `subgroup_metric_table(df, ...)` | DataFrame and group/label/pred columns | probability column, positive label | subgroup metric table |
| `decision_curve_table(y_true, y_prob, ...)` | labels, probabilities | thresholds, positive label | net-benefit table |
| `bootstrap_concordance_index(df, ...)` | survival table and duration/event/risk columns | rounds, random state | C-index summary dict |
| `survival_calibration_at_time(df, ...)` | survival table and prediction column | time horizon, bins | summary dict and bin table |
| `brier_score_at_time(df, ...)` | survival table and prediction column | time horizon | Brier score dict |
| `external_survival_validation(...)` | external table and risk column | prediction column, horizon | validation dict |
| `permutation_importance_table(estimator, X, y, ...)` | fitted estimator, features, labels | names, repeats, scoring, random state | importance DataFrame |
| `partial_dependence_table(estimator, X, ...)` | fitted estimator and features | selected features, names, grid resolution | PDP DataFrame |
| `shap_summary_table(estimator, X, ...)` | fitted estimator and feature table | feature names, custom explainer, background data, max rows | SHAP summary DataFrame |
| `shap_values_table(estimator, X, ...)` | fitted estimator and feature table | feature names, custom explainer, background data, max rows | long SHAP DataFrame |
| `explain_model_summary(...)` | importance, SHAP, or feature QC table | metrics, notes, feature column | merged explanation summary |
| `explain_patient_prediction(contributions, ...)` | long contribution table | row/patient selector, top N | top signed drivers |
| `create_provenance_manifest(...)` | none | title, inputs, outputs, parameters, notes | manifest dict |
| `write_manifest(manifest, path)` | manifest and output path | none | written path |

## BOA Extraction, Radiomics And Visualization

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `discover_boa_cases(cohort_folder, ...)` | `cohort_folder` | `measurement_filename` | list of case folders |
| `extract_body_region_features(case_folder_or_measurements, ...)` | patient folder or measurement JSON | body regions, tissues, SMA labels, derived markers, height, missing value | feature dict or `None` |
| `extract_total_segmentation_features(case_folder, ...)` | `case_folder` | labels, ratios, measurement filename, rounding, missing value | feature dict or `None` |
| `extract_experimental_aortic_calcification_features(case_folder_or_masks_dir, ...)` | patient or mask folder | CT path, mask folder, HU threshold, aorta/total/body-region/iliac mask settings | feature dict or `None` |
| `extract_experimental_cohort_aortic_calcification_features(cohort_folder_or_cases, ...)` | cohort root or case folders | workers, progress, single-case extraction options | aortic calcification DataFrame |
| `discover_boa_radiomics_cases(cohort_folder, ...)` | `cohort_folder` | `segmentation_filename` | list of case folders |
| `extract_case_radiomics_features(case_folder, ...)` | `case_folder` | image/segmentation filenames, labels, extractor settings, paths, `on_error` | feature dict or `None` |
| `extract_boa_radiomics_features(cohort_folder_or_cases, ...)` | cohort root or case folders | segmentation kind, labels, extractor settings, workers | radiomics DataFrame |
| `SegmentationLayer(kind, ...)` | `kind` | `display_mode`, `title`, `filename`, `opacity` | layer configuration |
| `create_boa_segmentation_collage(boa_folders, output_path, ...)` | `boa_folders`, `output_path` | orientation, layers, labels, slices, CT window, opacity, panel width, body-region crop options | metadata dict and output image |
| `plot_volume_difference_heatmap(volume_a, volume_b, ...)` | two aligned CT/MR volumes | data type, orientation, slices, labels, CT/MR scaling, difference colormap, save path | `(fig, axes, table)` |

## Documents, DICOM, FHIR, LLM

Client classes have broader method surfaces; see their module pages for workflow detail:

- [FHIR](modules/fhir.md)
- [DICOM](modules/dicom.md)
- [Documents](modules/documents.md)
- [LLM](modules/llm.md)
