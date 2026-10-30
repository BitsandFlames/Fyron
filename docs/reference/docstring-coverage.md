# Docstring Coverage Report

This generated report lists public APIs whose generated reference entries are incomplete. It is a quality-control artifact for maintainers; the module guides remain the main workflow documentation.

Priority public-beta APIs with incomplete docstring coverage: **141**.

Full generated backlog: **358** incomplete API entries.

## How To Use This Report

- `fyron`, `core`, `fhir`, `dicom`, `imaging`, `survival`, `ml`, `plotting`, and `curate` are the first public-beta documentation surfaces. Treat the priority backlog as the milestone for first external users; the full backlog below remains useful for long-tail polishing.
- Add a short first docstring paragraph, parameter descriptions, and return notes.
- Public APIs are documented package exports and top-level workflow helpers; underscore-prefixed modules and helpers are internal and may change without compatibility guarantees.
- Regenerate the docs with `uv run python scripts/build_docs.py`.

## Priority Public-Beta Backlog

## `fyron.core.io`

| API | Issues |
| --- | --- |
| `fyron.core.io.DataIO.describe_file` | missing description; missing parameter descriptions: path |
| `fyron.core.io.DataIO.read_csv` | missing description; missing parameter descriptions: path, kwargs |
| `fyron.core.io.DataIO.read_excel` | missing description; missing parameter descriptions: path, kwargs |
| `fyron.core.io.DataIO.read_json` | missing description; missing parameter descriptions: path, kwargs |
| `fyron.core.io.DataIO.read_table` | missing description; missing parameter descriptions: path, file_format, kwargs |
| `fyron.core.io.DataIO.summarize_table` | missing description; missing parameter descriptions: df, name |
| `fyron.core.io.DataIO.write_csv` | missing description; missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.DataIO.write_excel` | missing description; missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.DataIO.write_json` | missing description; missing parameter descriptions: payload, path, indent, create_parent, kwargs |
| `fyron.core.io.DataIO.write_table` | missing description; missing parameter descriptions: df, path, file_format, create_parent, index, kwargs |
| `fyron.core.io.TeableClient` | missing parameter descriptions: base_url, token, timeout |
| `fyron.core.io.TeableClient.clear_table` | missing parameter descriptions: table_id, batch_size, take |
| `fyron.core.io.TeableClient.create_base` | missing parameter descriptions: space_id, name, icon |
| `fyron.core.io.TeableClient.create_records` | missing description; missing parameter descriptions: table_id, records, field_key_type, typecast, order |
| `fyron.core.io.TeableClient.create_research_cohort_table` | missing parameter descriptions: base_id, name, df, description, fields, metadata |
| `fyron.core.io.TeableClient.create_table` | missing parameter descriptions: base_id, name, db_table_name, description, icon, fields, views, records, order, field_key_type |
| `fyron.core.io.TeableClient.delete_records` | missing parameter descriptions: table_id, record_ids |
| `fyron.core.io.TeableClient.get_or_create_base` | missing parameter descriptions: name, space_id, space_name, icon |
| `fyron.core.io.TeableClient.get_or_create_table` | missing parameter descriptions: base_id, name, db_table_name, description, icon, fields, views, records, order, field_key_type |
| `fyron.core.io.TeableClient.list_bases` | missing parameter descriptions: space_id |
| `fyron.core.io.TeableClient.list_records` | missing description; missing parameter descriptions: table_id, view_id, take, skip, field_key_type, cell_format, projection, params |
| `fyron.core.io.TeableClient.list_tables` | missing parameter descriptions: base_id |
| `fyron.core.io.TeableClient.overwrite_table` | missing parameter descriptions: table_id, df, delete_batch_size, create_chunk_size, field_key_type, typecast |
| `fyron.core.io.TeableClient.read_cohort` | missing parameter descriptions: table_id, id_col, required_columns, view_id, max_records |
| `fyron.core.io.TeableClient.read_table` | missing description; missing parameter descriptions: table_id, view_id, field_key_type, cell_format, projection, take, max_records |
| `fyron.core.io.TeableClient.summarize_teable_table` | missing parameter descriptions: table_id, view_id, projection, max_records |
| `fyron.core.io.TeableClient.write_dataframe` | missing description; missing parameter descriptions: table_id, df, field_key_type, typecast, chunk_size |
| `fyron.core.io.TeableClient.write_research_cohort` | missing parameter descriptions: table_id, df, mode, cohort_name, version, metadata, id_col, field_key_type, typecast, chunk_size |
| `fyron.core.io.TeableConfig` | missing description |
| `fyron.core.io.describe_file` | missing parameter descriptions: path |
| `fyron.core.io.ensure_parent_dir` | missing parameter descriptions: path |
| `fyron.core.io.read_csv` | missing parameter descriptions: path, kwargs |
| `fyron.core.io.read_excel` | missing parameter descriptions: path, kwargs |
| `fyron.core.io.read_json` | missing parameter descriptions: path, kwargs |
| `fyron.core.io.read_table` | missing parameter descriptions: path, file_format, kwargs |
| `fyron.core.io.summarize_table` | missing parameter descriptions: df, name |
| `fyron.core.io.write_csv` | missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.write_excel` | missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.write_json` | missing parameter descriptions: payload, path, indent, create_parent, kwargs |
| `fyron.core.io.write_table` | missing parameter descriptions: df, path, file_format, create_parent, index, kwargs |

## `fyron.fhir.rest`

| API | Issues |
| --- | --- |
| `fyron.fhir.rest.FHIRRestClient` | missing parameter descriptions: extra_headers, retries, return_fhir_obj |
| `fyron.fhir.rest.FHIRRestClient.bundles_to_df` | missing parameter descriptions: bundles, process_function, fhir_paths, mode, use_multiprocessing |
| `fyron.fhir.rest.FHIRRestClient.create_resource` | missing parameter descriptions: resource, resource_type |
| `fyron.fhir.rest.FHIRRestClient.submit_bundle` | missing parameter descriptions: bundle |
| `fyron.fhir.rest.FHIRRestClient.update_resource` | missing parameter descriptions: resource, resource_id, resource_type |
| `fyron.fhir.rest.QueryJob` | missing description |
| `fyron.fhir.rest.ResponseCache` | missing parameter descriptions: ttl_seconds, max_entries |
| `fyron.fhir.rest.ResponseCache.get` | missing description; missing parameter descriptions: key, now |
| `fyron.fhir.rest.ResponseCache.set` | missing description; missing parameter descriptions: key, payload, now |
| `fyron.fhir.rest.build_partition_params` | missing parameter descriptions: params, partition_param, start, end, frequency, window_days |
| `fyron.fhir.rest.flatten_data` | missing parameter descriptions: bundle, col_sep |
| `fyron.fhir.rest.parse_fhir_path` | missing parameter descriptions: bundle, compiled_fhir_paths |

## `fyron.imaging.normalize`

| API | Issues |
| --- | --- |
| `fyron.imaging.normalize.normalize_ct` | missing parameter descriptions: hu_min |

## `fyron.imaging.qc`

| API | Issues |
| --- | --- |
| `fyron.imaging.qc.check_image_mask_alignment` | missing parameter descriptions: image, mask |
| `fyron.imaging.qc.summarize_dicom_series_geometry` | missing parameter descriptions: dicom_dir, recursive |
| `fyron.imaging.qc.summarize_intensity_range` | missing parameter descriptions: image, mask, percentiles |
| `fyron.imaging.qc.summarize_mask_volume` | missing parameter descriptions: mask, labels, spacing |
| `fyron.imaging.qc.summarize_nifti_geometry` | missing parameter descriptions: paths |

## `fyron.imaging.segmentation`

| API | Issues |
| --- | --- |
| `fyron.imaging.segmentation.dice_score` | missing parameter descriptions: mask_true, mask_pred, label |
| `fyron.imaging.segmentation.hausdorff_distance` | missing parameter descriptions: mask_true, mask_pred, label, spacing, percentile |
| `fyron.imaging.segmentation.label_overlap_table` | missing parameter descriptions: mask_true, mask_pred, labels, spacing |
| `fyron.imaging.segmentation.segmentation_metric_table` | missing parameter descriptions: mask_true, mask_pred, labels, spacing, surface_tolerance |
| `fyron.imaging.segmentation.surface_dice` | missing parameter descriptions: mask_true, mask_pred, label, tolerance, spacing |
| `fyron.imaging.segmentation.volume_difference` | missing parameter descriptions: mask_true, mask_pred, label, spacing |

## `fyron.ml.evaluation`

| API | Issues |
| --- | --- |
| `fyron.ml.evaluation.apply_probability_calibrator` | missing parameter descriptions: calibrator, X, positive_class_index |
| `fyron.ml.evaluation.evaluate_external_validation` | missing parameter descriptions: estimator, X_external, y_external, threshold, pos_label |
| `fyron.ml.evaluation.evaluate_locked_threshold` | missing parameter descriptions: y_true, y_prob, threshold, pos_label, neg_label |
| `fyron.ml.evaluation.fit_probability_calibrator` | missing parameter descriptions: estimator, X_calibration, y_calibration, method |
| `fyron.ml.evaluation.model_card_summary` | missing parameter descriptions: estimator, X, y, metrics, intended_use, limitations, random_state |
| `fyron.ml.evaluation.nested_cross_validate_model` | missing parameter descriptions: estimator, param_grid, X, y, outer_cv, inner_cv, scoring, random_state, n_jobs, pos_label |

## `fyron.ml.pipeline`

| API | Issues |
| --- | --- |
| `fyron.ml.pipeline.run_classification_pipeline` | missing parameter descriptions: X, y, model, test_size, stratify, random_state, handle_imbalance, use_boruta, boruta_kwargs, use_grid_search, param_grid, plot, pos_label, model_params |

## `fyron.ml.plots`

| API | Issues |
| --- | --- |
| `fyron.ml.plots.add_stat_annotations` | missing parameter descriptions: ax, stats_table, positions, heights, annotation_col, line_color, text_color, fontsize, loc |
| `fyron.ml.plots.plot_alluvial_flow` | missing parameter descriptions: data, path_col, stage_col, category_col, value_col, stage_order, title, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_binned_marker_heatmap` | missing parameter descriptions: data, row_col, col_col, value_col, row_order, col_order, title, cmap, missing_color, ax, save_path, fmt |
| `fyron.ml.plots.plot_bland_altman` | missing parameter descriptions: method_a, method_b, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_calibration_curve` | missing parameter descriptions: y_true, y_prob, n_bins, strategy, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_cohort_flow` | missing parameter descriptions: data, step_col, n_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_confusion_matrix` | missing parameter descriptions: y_true, y_pred, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_correlation_heatmap` | missing parameter descriptions: data, columns, method, group_col, title, annotate, annotate_significance, p_adjust, mask_upper, cmap, vmin, vmax, ax, save_path, fmt |
| `fyron.ml.plots.plot_cross_validated_roc` | missing parameter descriptions: y_true_col, y_prob_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_decision_curve` | missing parameter descriptions: data, threshold_col, model_col, treat_all_col, treat_none_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_density` | missing parameter descriptions: title, xlabel, ylabel, hue_order, palette, fill, alpha, rug, gridsize, ax, save_path, fmt |
| `fyron.ml.plots.plot_dice_by_label` | missing parameter descriptions: data, label_col, dice_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_directional_ratio_rows` | missing parameter descriptions: data, feature_col, ratio_col, lower_col, upper_col, p_col, group_col, n_col, ratio_label, title, protective_label, hazardous_label, reference, log_scale, xlim, annotate, estimate_label, ci_label, p_label, ax, save_path, fmt |
| `fyron.ml.plots.plot_external_validation_metrics` | missing parameter descriptions: data, metric_col, value_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_feature_importance` | missing parameter descriptions: importance_df, top_n, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_feature_selection_summary` | missing parameter descriptions: data, feature_col, selected_col, score_col, title, top_n, ax, save_path, fmt |
| `fyron.ml.plots.plot_forest_estimates` | missing parameter descriptions: data, label_col, estimate_col, lower_col, upper_col, p_col, p_adjust_col, n_col, group_col, table_columns, reference, log_scale, title, xlabel, ax, save_path, fmt |
| `fyron.ml.plots.plot_grouped_bar_with_significance` | missing parameter descriptions: data, x, y, hue, order, hue_order, estimator, error, ci, test, comparisons, p_thresholds, title, ylabel, xlabel, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_grouped_boxplot` | missing parameter descriptions: x, title, xlabel, ylabel, order, palette, show_points, point_alpha, random_state, comparisons, stat_test, p_adjust, annotation_format, hide_ns, return_stats, ax, save_path, fmt |
| `fyron.ml.plots.plot_grouped_correlation_heatmaps` | missing parameter descriptions: data, group_col, columns, method, title, annotate, annotate_significance, p_adjust, mask_upper, cmap, vmin, vmax, save_path, fmt |
| `fyron.ml.plots.plot_hazard_ratios` | missing parameter descriptions: cox_result, label_col, title, xlabel, table_columns, ax, save_path, fmt |
| `fyron.ml.plots.plot_histogram` | missing parameter descriptions: data, x, hue, group, bins, stat, multiple, title, xlabel, ylabel, hue_order, palette, alpha, ax, save_path, fmt |
| `fyron.ml.plots.plot_kaplan_meier` | missing return documentation; missing parameter descriptions: args, kwargs |
| `fyron.ml.plots.plot_likert_scale` | missing parameter descriptions: item_col, order, palette, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_metric_bars` | missing parameter descriptions: metrics, metrics_to_plot, model_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_missingness_bar` | missing parameter descriptions: data, column_col, missing_col, group_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_patterned_bar` | missing parameter descriptions: x, title, xlabel, ylabel, orientation, palette, hatches, annotate, ax, save_path, fmt |
| `fyron.ml.plots.plot_precision_recall_curve` | missing parameter descriptions: y_true, y_prob, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_raincloud` | missing parameter descriptions: data, x, y, order, title, ylabel, palette, random_state, ax, save_path, fmt |
| `fyron.ml.plots.plot_risk_score_distribution` | missing parameter descriptions: data, risk_col, event_col, event_labels, title, ylabel, jitter, violin, palette, random_state, ax, save_path, fmt |
| `fyron.ml.plots.plot_roc_curve` | missing parameter descriptions: y_true, y_prob, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_segmentation_overlay_grid` | missing parameter descriptions: image, mask, slice_indices, label, alpha, title, save_path, fmt |
| `fyron.ml.plots.plot_signed_feature_weights` | missing parameter descriptions: data, feature_col, weight_col, top_n, title, xlabel, positive_label, negative_label, ax, save_path, fmt |
| `fyron.ml.plots.plot_significance_bars` | missing parameter descriptions: data, label_col, p_col, threshold, title, xlabel, annotate, ax, save_path, fmt |
| `fyron.ml.plots.plot_stability_selection` | missing parameter descriptions: data, feature_col, frequency_col, threshold, title, top_n, ax, save_path, fmt |
| `fyron.ml.plots.plot_survival_calibration` | missing parameter descriptions: calibration_table, observed_col, predicted_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_swarmplot` | missing parameter descriptions: data, x, y, hue, order, hue_order, dodge, title, xlabel, ylabel, palette, point_size, point_alpha, random_state, comparisons, stat_test, p_adjust, annotation_format, hide_ns, return_stats, ax, save_path, fmt |
| `fyron.ml.plots.plot_swimmer` | missing parameter descriptions: data, patient_col, start_col, end_col, group_col, event_time_col, event_col, title, xlabel, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_table_one_summary` | missing parameter descriptions: data, variable_col, p_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_time_dependent_auc` | missing parameter descriptions: data, time_col, auc_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_volcano` | missing parameter descriptions: data, feature_col, effect_col, p_col, group_col, p_threshold, effect_threshold, top_n_labels, title, xlabel, ylabel, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_waffle` | missing parameter descriptions: category_col, palette, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_waterfall` | missing parameter descriptions: values, labels, title, ylabel, threshold, ax, save_path, fmt |
| `fyron.ml.plots.stat_test_pairs` | missing parameter descriptions: x, alpha, label_col, p_col |

## `fyron.ml.training`

| API | Issues |
| --- | --- |
| `fyron.ml.training.train_random_forest` | missing parameter descriptions: X_train, y_train, X_test, y_test, class_weight, random_state, plot, pos_label, model_params |
| `fyron.ml.training.train_xgboost` | missing parameter descriptions: X_train, y_train, X_test, y_test, scale_pos_weight, random_state, plot, pos_label, model_params |

## `fyron.plotting_palettes`

| API | Issues |
| --- | --- |
| `fyron.plotting_palettes.get_colormap` | missing parameter descriptions: name, reverse |
| `fyron.plotting_palettes.get_palette` | missing parameter descriptions: name, n, reverse |
| `fyron.plotting_palettes.list_palettes` | missing parameter descriptions: kind |
| `fyron.plotting_palettes.palette_grayscale_contrast` | missing parameter descriptions: name_or_colors |
| `fyron.plotting_palettes.palette_luminance_table` | missing parameter descriptions: name_or_colors |
| `fyron.plotting_palettes.preview_palette` | missing parameter descriptions: name, n, save_path |
| `fyron.plotting_palettes.resolve_colormap` | missing parameter descriptions: cmap |
| `fyron.plotting_palettes.resolve_palette` | missing parameter descriptions: palette, n, default |
| `fyron.plotting_palettes.set_plot_style` | missing parameter descriptions: style, palette |

## `fyron.survival.boosting`

| API | Issues |
| --- | --- |
| `fyron.survival.boosting.train_gradient_survival_boosting` | missing parameter descriptions: duration_train, X_test, duration_test, model_params |

## `fyron.survival.cox`

| API | Issues |
| --- | --- |
| `fyron.survival.cox.fit_multivariate_cox` | missing parameter descriptions: df, duration_col, event_col, covariates, formula, strata, robust |
| `fyron.survival.cox.fit_univariate_cox` | missing parameter descriptions: duration_col |

## `fyron.survival.groups`

| API | Issues |
| --- | --- |
| `fyron.survival.groups.default_tau_from_observed_times` | missing parameter descriptions: df, duration_col, group_col |

## `fyron.survival.kaplan_meier`

| API | Issues |
| --- | --- |
| `fyron.survival.kaplan_meier.plot_kaplan_meier` | missing parameter descriptions: duration_col, split_column, split_method, split_bins, ci_alpha, censor_styles, title, xlabel, ylabel, legend_title, legend_kwargs, figsize, save_path, save_format, dpi |

## `fyron.survival.ph_diagnostics`

| API | Issues |
| --- | --- |
| `fyron.survival.ph_diagnostics.check_ph_assumptions` | missing parameter descriptions: include_residuals |
| `fyron.survival.ph_diagnostics.plot_schoenfeld_residuals` | missing parameter descriptions: residuals, covariates, time_col, residual_col, covariate_col, title, ax, save_path, fmt |
| `fyron.survival.ph_diagnostics.schoenfeld_test_table` | missing parameter descriptions: fitter, training_df, method, p_adjust, alpha |

## `fyron.survival.rmst`

| API | Issues |
| --- | --- |
| `fyron.survival.rmst.calculate_rmst` | missing parameter descriptions: duration_col |
| `fyron.survival.rmst.compare_rmst` | missing parameter descriptions: df, duration_col, event_col |

## `fyron.survival.time_varying`

| API | Issues |
| --- | --- |
| `fyron.survival.time_varying.expand_time_interaction_dataframe` | missing parameter descriptions: df, duration_col, event_col, covariates, time_interaction_covariates, time_transform, n_intervals, breakpoints, id_col, start_col, stop_col |
| `fyron.survival.time_varying.fit_cox_time_interactions` | missing parameter descriptions: df, duration_col, event_col, covariates, time_interaction_covariates, time_transform, n_intervals, breakpoints, id_col, strata, robust |
| `fyron.survival.time_varying.fit_time_varying_cox` | missing parameter descriptions: start_col |
| `fyron.survival.time_varying.run_survival_sensitivity_analysis` | missing parameter descriptions: df, duration_col, event_col, covariates, formula, group_col, rmst_tau, ph_p_value_threshold, time_interaction_covariates, time_transform, n_intervals, breakpoints, fit_time_interactions, fit_aft, fit_rmst |

## `fyron.survival.weibull_aft`

| API | Issues |
| --- | --- |
| `fyron.survival.weibull_aft.fit_weibull_aft` | missing parameter descriptions: df, duration_col |

## Full Generated Backlog

## `fyron.audit.manifest`

| API | Issues |
| --- | --- |
| `fyron.audit.manifest.analysis_run_manifest` | missing parameter descriptions: inputs |
| `fyron.audit.manifest.create_provenance_manifest` | missing parameter descriptions: title, inputs, outputs, parameters, notes |
| `fyron.audit.manifest.hash_file` | missing parameter descriptions: path, algorithm, chunk_size |
| `fyron.audit.manifest.write_manifest` | missing parameter descriptions: manifest, path |

## `fyron.banner`

| API | Issues |
| --- | --- |
| `fyron.banner.get_run_footer` | missing parameter descriptions: status, duration, outputs, color |
| `fyron.banner.get_run_header` | missing parameter descriptions: command, version, timestamp, color |
| `fyron.banner.print_banner` | missing parameter descriptions: version, include_version, color, theme, file |

## `fyron.boa_extraction.experimental_aortic_calcification`

| API | Issues |
| --- | --- |
| `fyron.boa_extraction.experimental_aortic_calcification.extract_experimental_aortic_calcification_features` | missing parameter descriptions: thoracic_mask_filename |

## `fyron.boa_radiomics.features`

| API | Issues |
| --- | --- |
| `fyron.boa_radiomics.features.discover_boa_radiomics_cases` | missing parameter descriptions: cohort_folder, segmentation_filename |
| `fyron.boa_radiomics.features.extract_case_radiomics_features` | missing parameter descriptions: case_folder, image_filename, segmentation_kind, segmentation_filename, labels, extractor, extractor_settings, feature_prefix, download_id, include_paths, exclude_diagnostics, minimum_voxels, resample_mask, on_error |

## `fyron.cohort.tables`

| API | Issues |
| --- | --- |
| `fyron.cohort.tables.audit_cohort_join` | missing parameter descriptions: features |
| `fyron.cohort.tables.audit_time_to_event_endpoint` | missing parameter descriptions: index_date_col, event_date_col |

## `fyron.console`

| API | Issues |
| --- | --- |
| `fyron.console.configure_logging` | missing parameter descriptions: level, color, json, stream |
| `fyron.console.console_message` | missing parameter descriptions: message, level, color, prefix, stream, quiet |
| `fyron.console.error` | missing description; missing parameter descriptions: message, kwargs |
| `fyron.console.format_count` | missing description; missing parameter descriptions: label, value |
| `fyron.console.format_duration` | missing description; missing parameter descriptions: seconds |
| `fyron.console.format_path` | missing description; missing parameter descriptions: path |
| `fyron.console.get_logger` | missing parameter descriptions: name |
| `fyron.console.get_timer` | missing description |
| `fyron.console.info` | missing description; missing parameter descriptions: message, kwargs |
| `fyron.console.success` | missing description; missing parameter descriptions: message, kwargs |
| `fyron.console.supports_color` | missing parameter descriptions: stream |
| `fyron.console.warning` | missing description; missing parameter descriptions: message, kwargs |

## `fyron.core.io`

| API | Issues |
| --- | --- |
| `fyron.core.io.DataIO.describe_file` | missing description; missing parameter descriptions: path |
| `fyron.core.io.DataIO.read_csv` | missing description; missing parameter descriptions: path, kwargs |
| `fyron.core.io.DataIO.read_excel` | missing description; missing parameter descriptions: path, kwargs |
| `fyron.core.io.DataIO.read_json` | missing description; missing parameter descriptions: path, kwargs |
| `fyron.core.io.DataIO.read_table` | missing description; missing parameter descriptions: path, file_format, kwargs |
| `fyron.core.io.DataIO.summarize_table` | missing description; missing parameter descriptions: df, name |
| `fyron.core.io.DataIO.write_csv` | missing description; missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.DataIO.write_excel` | missing description; missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.DataIO.write_json` | missing description; missing parameter descriptions: payload, path, indent, create_parent, kwargs |
| `fyron.core.io.DataIO.write_table` | missing description; missing parameter descriptions: df, path, file_format, create_parent, index, kwargs |
| `fyron.core.io.TeableClient` | missing parameter descriptions: base_url, token, timeout |
| `fyron.core.io.TeableClient.clear_table` | missing parameter descriptions: table_id, batch_size, take |
| `fyron.core.io.TeableClient.create_base` | missing parameter descriptions: space_id, name, icon |
| `fyron.core.io.TeableClient.create_records` | missing description; missing parameter descriptions: table_id, records, field_key_type, typecast, order |
| `fyron.core.io.TeableClient.create_research_cohort_table` | missing parameter descriptions: base_id, name, df, description, fields, metadata |
| `fyron.core.io.TeableClient.create_table` | missing parameter descriptions: base_id, name, db_table_name, description, icon, fields, views, records, order, field_key_type |
| `fyron.core.io.TeableClient.delete_records` | missing parameter descriptions: table_id, record_ids |
| `fyron.core.io.TeableClient.get_or_create_base` | missing parameter descriptions: name, space_id, space_name, icon |
| `fyron.core.io.TeableClient.get_or_create_table` | missing parameter descriptions: base_id, name, db_table_name, description, icon, fields, views, records, order, field_key_type |
| `fyron.core.io.TeableClient.list_bases` | missing parameter descriptions: space_id |
| `fyron.core.io.TeableClient.list_records` | missing description; missing parameter descriptions: table_id, view_id, take, skip, field_key_type, cell_format, projection, params |
| `fyron.core.io.TeableClient.list_tables` | missing parameter descriptions: base_id |
| `fyron.core.io.TeableClient.overwrite_table` | missing parameter descriptions: table_id, df, delete_batch_size, create_chunk_size, field_key_type, typecast |
| `fyron.core.io.TeableClient.read_cohort` | missing parameter descriptions: table_id, id_col, required_columns, view_id, max_records |
| `fyron.core.io.TeableClient.read_table` | missing description; missing parameter descriptions: table_id, view_id, field_key_type, cell_format, projection, take, max_records |
| `fyron.core.io.TeableClient.summarize_teable_table` | missing parameter descriptions: table_id, view_id, projection, max_records |
| `fyron.core.io.TeableClient.write_dataframe` | missing description; missing parameter descriptions: table_id, df, field_key_type, typecast, chunk_size |
| `fyron.core.io.TeableClient.write_research_cohort` | missing parameter descriptions: table_id, df, mode, cohort_name, version, metadata, id_col, field_key_type, typecast, chunk_size |
| `fyron.core.io.TeableConfig` | missing description |
| `fyron.core.io.describe_file` | missing parameter descriptions: path |
| `fyron.core.io.ensure_parent_dir` | missing parameter descriptions: path |
| `fyron.core.io.read_csv` | missing parameter descriptions: path, kwargs |
| `fyron.core.io.read_excel` | missing parameter descriptions: path, kwargs |
| `fyron.core.io.read_json` | missing parameter descriptions: path, kwargs |
| `fyron.core.io.read_table` | missing parameter descriptions: path, file_format, kwargs |
| `fyron.core.io.summarize_table` | missing parameter descriptions: df, name |
| `fyron.core.io.write_csv` | missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.write_excel` | missing parameter descriptions: df, path, kwargs |
| `fyron.core.io.write_json` | missing parameter descriptions: payload, path, indent, create_parent, kwargs |
| `fyron.core.io.write_table` | missing parameter descriptions: df, path, file_format, create_parent, index, kwargs |

## `fyron.core.s3`

| API | Issues |
| --- | --- |
| `fyron.core.s3.S3Storage.download_file` | missing parameter descriptions: key, local_path, create_parent |
| `fyron.core.s3.S3Storage.exists` | missing parameter descriptions: key |
| `fyron.core.s3.S3Storage.key` | missing parameter descriptions: key |
| `fyron.core.s3.S3Storage.list` | missing parameter descriptions: prefix, suffix, max_keys |
| `fyron.core.s3.S3Storage.read_bytes` | missing parameter descriptions: key |
| `fyron.core.s3.S3Storage.read_json` | missing parameter descriptions: key |
| `fyron.core.s3.S3Storage.read_table` | missing parameter descriptions: key, file_format, kwargs |
| `fyron.core.s3.S3Storage.upload_file` | missing parameter descriptions: local_path, key, content_type |
| `fyron.core.s3.S3Storage.write_bytes` | missing parameter descriptions: key, data, content_type |
| `fyron.core.s3.S3Storage.write_json` | missing parameter descriptions: key, payload, indent |
| `fyron.core.s3.S3Storage.write_table` | missing parameter descriptions: key, df, file_format, index, kwargs |
| `fyron.core.s3.parse_s3_uri` | missing parameter descriptions: uri |
| `fyron.core.s3.read_s3_table` | missing parameter descriptions: uri, kwargs |
| `fyron.core.s3.write_s3_table` | missing parameter descriptions: df, uri, kwargs |

## `fyron.datasets`

| API | Issues |
| --- | --- |
| `fyron.datasets.make_boa_like_folder` | missing parameter descriptions: output_dir |
| `fyron.datasets.make_classification_cohort` | missing parameter descriptions: n, random_state |
| `fyron.datasets.make_clinical_cohort` | missing parameter descriptions: n, random_state |
| `fyron.datasets.make_dicom_series` | missing parameter descriptions: output_dir, shape, patient_id |
| `fyron.datasets.make_nifti_pair` | missing parameter descriptions: output_dir, shape |
| `fyron.datasets.make_survival_cohort` | missing parameter descriptions: n, random_state |

## `fyron.datasets.preparation`

| API | Issues |
| --- | --- |
| `fyron.datasets.preparation.prepare_nnunetv2_dataset` | missing parameter descriptions: manifest, output_dir, dataset_id, dataset_name, image_col, label_col, case_id_col, split_col, channel_names, labels, copy_mode, overwrite, validate |
| `fyron.datasets.preparation.prepare_yolo_classification_dataset` | missing parameter descriptions: manifest, output_dir, image_col, class_col, split_col, sample_id_col, image_format, copy_mode, dicom_window, nifti_slice, overwrite, validate |
| `fyron.datasets.preparation.prepare_yolo_detection_dataset` | missing parameter descriptions: manifest, output_dir, image_col, split_col, class_col, bbox_cols, image_width_col, image_height_col, coord_format, sample_id_col, image_format, copy_mode, dicom_window, nifti_slice, overwrite, validate |
| `fyron.datasets.preparation.validate_nnunetv2_dataset` | missing parameter descriptions: dataset_dir |
| `fyron.datasets.preparation.validate_yolo_dataset` | missing parameter descriptions: dataset_dir, task |
| `fyron.datasets.preparation.write_dataset_manifest` | missing parameter descriptions: df, output_path |

## `fyron.dicom.seg`

| API | Issues |
| --- | --- |
| `fyron.dicom.seg.read_segment_descriptions` | missing parameter descriptions: path |
| `fyron.dicom.seg.summarize_dicom_seg` | missing parameter descriptions: path, source_images |
| `fyron.dicom.seg.validate_dicom_seg` | missing parameter descriptions: path, source_images |
| `fyron.dicom.seg.validate_segment_descriptions` | missing parameter descriptions: segment_descriptions |
| `fyron.dicom.seg.write_dicom_seg` | missing parameter descriptions: mask, source_images, output_path, segment_descriptions, series_description, manufacturer, algorithm_type, algorithm_name |

## `fyron.dicom.synthetic`

| API | Issues |
| --- | --- |
| `fyron.dicom.synthetic.write_synthetic_dicom_series` | missing parameter descriptions: volume, output_dir, reference_dicom_dir, reference_datasets, patient_id, study_instance_uid, series_instance_uid, modality, series_description, intensity_mode, rescale_intercept, rescale_slope, copy_patient_tags |
| `fyron.dicom.synthetic.write_synthetic_nifti` | missing parameter descriptions: volume, output_path, reference_image, spacing, origin, direction, dtype, compress, metadata |

## `fyron.documents.client`

| API | Issues |
| --- | --- |
| `fyron.documents.client.DocumentDownloader` | missing parameter descriptions: max_workers, retries, save_mode, force_extension |
| `fyron.documents.client.DocumentDownloader.download_id` | missing parameter descriptions: url |
| `fyron.documents.client.DocumentDownloader.download_urls` | missing parameter descriptions: urls, results_csv |
| `fyron.documents.client.DocumentResult` | missing description |

## `fyron.explainability.inspection`

| API | Issues |
| --- | --- |
| `fyron.explainability.inspection.explain_patient_prediction` | missing parameter descriptions: row_col, patient_col, feature_col, contribution_col |
| `fyron.explainability.inspection.partial_dependence_table` | missing parameter descriptions: estimator, X, features, feature_names, grid_resolution |
| `fyron.explainability.inspection.permutation_importance_table` | missing parameter descriptions: estimator, X, y, feature_names, n_repeats, scoring, random_state |
| `fyron.explainability.inspection.shap_summary_table` | missing parameter descriptions: estimator, X, feature_names, explainer, background_data, max_rows |
| `fyron.explainability.inspection.shap_values_table` | missing parameter descriptions: estimator, X, feature_names, explainer, background_data, max_rows |

## `fyron.feature_selection.selection`

| API | Issues |
| --- | --- |
| `fyron.feature_selection.selection.boruta_feature_selection` | missing parameter descriptions: X, y, kwargs |
| `fyron.feature_selection.selection.combine_feature_selection_results` | missing parameter descriptions: results, strategy, min_methods |
| `fyron.feature_selection.selection.correlation_filter` | missing parameter descriptions: X, threshold, method |
| `fyron.feature_selection.selection.model_importance_selection` | missing parameter descriptions: estimator, X, y, threshold, top_n |
| `fyron.feature_selection.selection.permutation_importance_selection` | missing parameter descriptions: estimator, X, y, n_repeats, scoring, random_state, threshold, top_n |
| `fyron.feature_selection.selection.stability_selection` | missing parameter descriptions: estimator, X, y, n_rounds, sample_fraction, selection_threshold, random_state |
| `fyron.feature_selection.selection.univariate_feature_screening` | missing parameter descriptions: X, y, task, alpha, correction |
| `fyron.feature_selection.selection.variance_filter` | missing parameter descriptions: X, threshold |

## `fyron.fhir.auth`

| API | Issues |
| --- | --- |
| `fyron.fhir.auth.Auth` | missing parameter descriptions: auth_url, auth_type, refresh_url, username, auth_method, token_auth_method, token, max_login_attempts, token_refresh_delta, session, client_id, client_secret, scope, token_cache, allow_reauthentication, device_authorization_endpoint, token_endpoint, authorization_endpoint, device_code_callback, client_auth_method |
| `fyron.fhir.auth.Auth.client_credentials` | missing parameter descriptions: client_id, client_secret, auth_url, token_endpoint, scope, client_auth_method, session |
| `fyron.fhir.auth.Auth.token_env` | missing parameter descriptions: auth_url, refresh_url, token_auth_method, token, max_login_attempts, token_refresh_delta, session |
| `fyron.fhir.auth.TokenAuth` | missing parameter descriptions: username, password, auth_url, refresh_url, token, token_refresh_delta, max_login_attempts, session, token_field, auth_method |

## `fyron.fhir.builder`

| API | Issues |
| --- | --- |
| `fyron.fhir.builder.attachment` | missing parameter descriptions: url, content_type, title, data, creation |
| `fyron.fhir.builder.build_bundle` | missing parameter descriptions: resources, bundle_type, bundle_id, transaction_method, if_none_exist, version |
| `fyron.fhir.builder.build_condition` | missing parameter descriptions: subject, code, condition_id, clinical_status, verification_status, onset, recorded_date, evidence, profile, identifier, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_diagnostic_report` | missing parameter descriptions: subject, code, results, report_id, status, effective, issued, imaging_study, conclusion, presented_form, profile, identifier, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_document_reference` | missing parameter descriptions: subject, url, title, content_type, document_id, status, doc_status, type_code, date, description, profile, identifier, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_encounter` | missing parameter descriptions: subject, status, encounter_class, encounter_id, period_start, period_end, reason_code, profile, identifier, version |
| `fyron.fhir.builder.build_endpoint` | missing parameter descriptions: address, endpoint_id, name, status, connection_type_code, profile, identifier, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_imaging_measurement_bundle` | missing parameter descriptions: subject, study_instance_uid, measurements, series_instance_uid, series_description, model_name, model_endpoint_url, id_prefix, bundle_type, version |
| `fyron.fhir.builder.build_imaging_study_reference` | missing parameter descriptions: subject, study_instance_uid, imaging_study_id, series_instance_uid, series_description, modality_code, started, profile, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_llm_extraction_bundle` | missing parameter descriptions: subject, source_report_url, observations, conditions, summary_text, model_name, model_endpoint_url, model_version, prompt_version, id_prefix, bundle_type, version |
| `fyron.fhir.builder.build_medication_statement` | missing parameter descriptions: subject, medication, medication_statement_id, status, effective, date_asserted, reason_code, profile, identifier, version |
| `fyron.fhir.builder.build_model_device` | missing parameter descriptions: model_name, model_version, device_id, manufacturer, endpoint, profile, identifier, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_observation` | missing parameter descriptions: subject, code, value, status, observation_id, effective, issued, category, unit, value_type, derived_from, method, body_site, imaging_series_uid, components, data_absent_reason, performer, encounter, interpretation, note, profile, identifier, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_observation_component` | missing parameter descriptions: code, value, unit, value_type, data_absent_reason, interpretation |
| `fyron.fhir.builder.build_procedure` | missing parameter descriptions: subject, code, procedure_id, status, performed, encounter, reason_code, body_site, profile, identifier, version |
| `fyron.fhir.builder.build_provenance` | missing parameter descriptions: targets, agent, entity, provenance_id, recorded, activity, prompt_version, profile, meta_source, tag, security, extension, version |
| `fyron.fhir.builder.build_service_request` | missing parameter descriptions: subject, code, service_request_id, status, intent, authored_on, requester, reason_code, profile, identifier, version |
| `fyron.fhir.builder.build_specimen` | missing parameter descriptions: subject, specimen_type, specimen_id, status, received_time, collection_time, profile, identifier, version |
| `fyron.fhir.builder.codeable_concept` | missing parameter descriptions: code, system, display, text, codings |
| `fyron.fhir.builder.coding` | missing parameter descriptions: code, system, display |
| `fyron.fhir.builder.dicom_code` | missing parameter descriptions: code, display |
| `fyron.fhir.builder.icd10` | missing parameter descriptions: code, display |
| `fyron.fhir.builder.identifier` | missing parameter descriptions: value, system, use |
| `fyron.fhir.builder.loinc` | missing parameter descriptions: code, display |
| `fyron.fhir.builder.quantity` | missing parameter descriptions: value, unit, system, code |
| `fyron.fhir.builder.read_fhir_json` | missing parameter descriptions: path |
| `fyron.fhir.builder.reference` | missing parameter descriptions: target, display |
| `fyron.fhir.builder.snomed` | missing parameter descriptions: code, display |
| `fyron.fhir.builder.summarize_fhir_bundle` | missing parameter descriptions: bundle |
| `fyron.fhir.builder.summarize_fhir_resource` | missing parameter descriptions: resource |
| `fyron.fhir.builder.ucum_quantity` | missing parameter descriptions: value, unit, code |
| `fyron.fhir.builder.validate_fhir_bundle` | missing parameter descriptions: bundle, version |
| `fyron.fhir.builder.validate_fhir_references` | missing parameter descriptions: bundle |
| `fyron.fhir.builder.validate_fhir_resource` | missing parameter descriptions: resource, version |
| `fyron.fhir.builder.write_fhir_json` | missing parameter descriptions: payload, path |

## `fyron.fhir.mapping`

| API | Issues |
| --- | --- |
| `fyron.fhir.mapping.build_bundle_from_dataframe` | missing parameter descriptions: df, resource_type, mapping, subject_col, id_col, study_uid_col, series_uid_col, bundle_type, transaction_method, if_none_exist, version |
| `fyron.fhir.mapping.build_conditions_from_dataframe` | missing parameter descriptions: df, mapping, subject_col, id_col, bundle_type, transaction_method, if_none_exist, version |
| `fyron.fhir.mapping.build_document_references_from_dataframe` | missing parameter descriptions: df, mapping, subject_col, id_col, bundle_type, transaction_method, if_none_exist, version |
| `fyron.fhir.mapping.build_imaging_measurements_from_dataframe` | missing parameter descriptions: df, mapping, subject_col, study_uid_col, series_uid_col, id_col, bundle_type, transaction_method, if_none_exist, version |
| `fyron.fhir.mapping.build_observations_from_dataframe` | missing parameter descriptions: df, mapping, subject_col, id_col, bundle_type, transaction_method, if_none_exist, version |
| `fyron.fhir.mapping.extract_coding_summary` | missing parameter descriptions: payload |
| `fyron.fhir.mapping.fhir_validation_report` | missing parameter descriptions: bundle |
| `fyron.fhir.mapping.read_fhir_mapping` | missing parameter descriptions: path |
| `fyron.fhir.mapping.validate_coding_systems` | missing parameter descriptions: payload, allowed_systems |
| `fyron.fhir.mapping.validate_fhir_mapping` | missing parameter descriptions: mapping, df, required_columns |
| `fyron.fhir.mapping.validate_fhir_mapping_result` | missing parameter descriptions: result |
| `fyron.fhir.mapping.validate_fhir_payload` | missing parameter descriptions: payload, version, strict |
| `fyron.fhir.mapping.write_fhir_mapping` | missing parameter descriptions: mapping, path |

## `fyron.fhir.rest`

| API | Issues |
| --- | --- |
| `fyron.fhir.rest.FHIRRestClient` | missing parameter descriptions: extra_headers, retries, return_fhir_obj |
| `fyron.fhir.rest.FHIRRestClient.bundles_to_df` | missing parameter descriptions: bundles, process_function, fhir_paths, mode, use_multiprocessing |
| `fyron.fhir.rest.FHIRRestClient.create_resource` | missing parameter descriptions: resource, resource_type |
| `fyron.fhir.rest.FHIRRestClient.submit_bundle` | missing parameter descriptions: bundle |
| `fyron.fhir.rest.FHIRRestClient.update_resource` | missing parameter descriptions: resource, resource_id, resource_type |
| `fyron.fhir.rest.QueryJob` | missing description |
| `fyron.fhir.rest.ResponseCache` | missing parameter descriptions: ttl_seconds, max_entries |
| `fyron.fhir.rest.ResponseCache.get` | missing description; missing parameter descriptions: key, now |
| `fyron.fhir.rest.ResponseCache.set` | missing description; missing parameter descriptions: key, payload, now |
| `fyron.fhir.rest.build_partition_params` | missing parameter descriptions: params, partition_param, start, end, frequency, window_days |
| `fyron.fhir.rest.flatten_data` | missing parameter descriptions: bundle, col_sep |
| `fyron.fhir.rest.parse_fhir_path` | missing parameter descriptions: bundle, compiled_fhir_paths |

## `fyron.fhir.sql`

| API | Issues |
| --- | --- |
| `fyron.fhir.sql.FHIRSQLClient` | missing parameter descriptions: dsn, host, port, dbname, user, password, sslmode, connect_timeout, log_queries |
| `fyron.fhir.sql.FHIRSQLClient.query` | missing parameter descriptions: sql, params |
| `fyron.fhir.sql.FHIRSQLClient.query_df` | missing parameter descriptions: sql, params, rename |
| `fyron.fhir.sql.FHIRSQLClient.query_df_from` | missing parameter descriptions: df, sql, column_map, rename, param_limit, chunk_size, parallel, max_workers, merge, unique_on, param_style, param_safety_factor |
| `fyron.fhir.sql.FHIRSQLClient.query_df_parallel` | missing parameter descriptions: merge, unique_on |
| `fyron.fhir.sql.FHIRSQLClient.query_df_stream` | missing parameter descriptions: sql, params, rename, chunksize |
| `fyron.fhir.sql.SQLConfig` | missing description |

## `fyron.fhir.types`

| API | Issues |
| --- | --- |
| `fyron.fhir.types.FHIRObj` | missing parameter descriptions: kwargs |

## `fyron.fhir.utils`

| API | Issues |
| --- | --- |
| `fyron.fhir.utils.extract_condition` | missing description; missing parameter descriptions: resource |
| `fyron.fhir.utils.extract_diagnostic_report` | missing description; missing parameter descriptions: resource |
| `fyron.fhir.utils.extract_encounter` | missing description; missing parameter descriptions: resource |
| `fyron.fhir.utils.extract_imaging_study` | missing description; missing parameter descriptions: resource, series |
| `fyron.fhir.utils.extract_observation` | missing description; missing parameter descriptions: resource |
| `fyron.fhir.utils.extract_patient` | missing description; missing parameter descriptions: resource |
| `fyron.fhir.utils.extract_procedure` | missing description; missing parameter descriptions: resource |
| `fyron.fhir.utils.process_condition_bundle` | missing description; missing parameter descriptions: bundle |
| `fyron.fhir.utils.process_diagnostic_report_bundle` | missing description; missing parameter descriptions: bundle |
| `fyron.fhir.utils.process_encounter_bundle` | missing description; missing parameter descriptions: bundle |
| `fyron.fhir.utils.process_imaging_study_bundle` | missing description; missing parameter descriptions: bundle |
| `fyron.fhir.utils.process_observation_bundle` | missing description; missing parameter descriptions: bundle |
| `fyron.fhir.utils.process_patient_bundle` | missing description; missing parameter descriptions: bundle |
| `fyron.fhir.utils.process_procedure_bundle` | missing description; missing parameter descriptions: bundle |
| `fyron.fhir.utils.safe_get` | missing parameter descriptions: resource, path, default |

## `fyron.flow.tracking`

| API | Issues |
| --- | --- |
| `fyron.flow.tracking.FlowTracker.print` | missing parameter descriptions: stream, color, quiet |
| `fyron.flow.tracking.FlowTracker.to_markdown` | missing parameter descriptions: digits |
| `fyron.flow.tracking.FlowTracker.to_text_flowchart` | missing parameter descriptions: digits |

## `fyron.imaging.normalize`

| API | Issues |
| --- | --- |
| `fyron.imaging.normalize.normalize_ct` | missing parameter descriptions: hu_min |

## `fyron.imaging.qc`

| API | Issues |
| --- | --- |
| `fyron.imaging.qc.check_image_mask_alignment` | missing parameter descriptions: image, mask |
| `fyron.imaging.qc.summarize_dicom_series_geometry` | missing parameter descriptions: dicom_dir, recursive |
| `fyron.imaging.qc.summarize_intensity_range` | missing parameter descriptions: image, mask, percentiles |
| `fyron.imaging.qc.summarize_mask_volume` | missing parameter descriptions: mask, labels, spacing |
| `fyron.imaging.qc.summarize_nifti_geometry` | missing parameter descriptions: paths |

## `fyron.imaging.segmentation`

| API | Issues |
| --- | --- |
| `fyron.imaging.segmentation.dice_score` | missing parameter descriptions: mask_true, mask_pred, label |
| `fyron.imaging.segmentation.hausdorff_distance` | missing parameter descriptions: mask_true, mask_pred, label, spacing, percentile |
| `fyron.imaging.segmentation.label_overlap_table` | missing parameter descriptions: mask_true, mask_pred, labels, spacing |
| `fyron.imaging.segmentation.segmentation_metric_table` | missing parameter descriptions: mask_true, mask_pred, labels, spacing, surface_tolerance |
| `fyron.imaging.segmentation.surface_dice` | missing parameter descriptions: mask_true, mask_pred, label, tolerance, spacing |
| `fyron.imaging.segmentation.volume_difference` | missing parameter descriptions: mask_true, mask_pred, label, spacing |

## `fyron.llm.agent`

| API | Issues |
| --- | --- |
| `fyron.llm.agent.LLMAgent.chat` | missing parameter descriptions: user_prompt, image_path, file_path, mode |
| `fyron.llm.agent.LLMAgent.prompt` | missing parameter descriptions: user_prompt, image_path, file_path, mode |
| `fyron.llm.agent.LLMAgent.prompt_dataframe` | missing parameter descriptions: df, text_col, prompt, output_col, output_csv, format_func, image_col, file_col, mode |
| `fyron.llm.agent.LLMAgent.prompt_df` | missing parameter descriptions: df, text_col, prompt, output_col, output_csv, format_func, image_col, file_col, mode |
| `fyron.llm.agent.LLMAgent.prompt_directory` | missing parameter descriptions: input_dir, prompt, glob, mode |
| `fyron.llm.agent.LLMAgent.prompt_documents` | missing parameter descriptions: documents, prompt, output_csv, mode |
| `fyron.llm.agent.LLMAgent.run_on_directory` | missing parameter descriptions: input_dir, prompt, glob, mode |
| `fyron.llm.agent.LLMAgent.run_prompt_on_dataframe` | missing parameter descriptions: df, text_col, prompt, output_col, output_csv, format_func, image_col, file_col, mode |
| `fyron.llm.agent.LLMConfig` | missing description |

## `fyron.ml.boruta_selection`

| API | Issues |
| --- | --- |
| `fyron.ml.boruta_selection.run_boruta_feature_selection` | missing parameter descriptions: X, y, estimator, class_weight, max_iter, random_state |

## `fyron.ml.class_weights`

| API | Issues |
| --- | --- |
| `fyron.ml.class_weights.sample_weights_for_sklearn` | missing parameter descriptions: y, class_weight |

## `fyron.ml.cv`

| API | Issues |
| --- | --- |
| `fyron.ml.cv.cross_validate_model` | missing parameter descriptions: X, random_state, pos_label |

## `fyron.ml.evaluation`

| API | Issues |
| --- | --- |
| `fyron.ml.evaluation.apply_probability_calibrator` | missing parameter descriptions: calibrator, X, positive_class_index |
| `fyron.ml.evaluation.evaluate_external_validation` | missing parameter descriptions: estimator, X_external, y_external, threshold, pos_label |
| `fyron.ml.evaluation.evaluate_locked_threshold` | missing parameter descriptions: y_true, y_prob, threshold, pos_label, neg_label |
| `fyron.ml.evaluation.fit_probability_calibrator` | missing parameter descriptions: estimator, X_calibration, y_calibration, method |
| `fyron.ml.evaluation.model_card_summary` | missing parameter descriptions: estimator, X, y, metrics, intended_use, limitations, random_state |
| `fyron.ml.evaluation.nested_cross_validate_model` | missing parameter descriptions: estimator, param_grid, X, y, outer_cv, inner_cv, scoring, random_state, n_jobs, pos_label |

## `fyron.ml.importance`

| API | Issues |
| --- | --- |
| `fyron.ml.importance.get_feature_importance` | missing parameter descriptions: model, feature_names |
| `fyron.ml.importance.plot_feature_importance` | missing parameter descriptions: model, feature_names, top_n, title, save_path, fmt |

## `fyron.ml.persistence`

| API | Issues |
| --- | --- |
| `fyron.ml.persistence.load_estimator` | missing parameter descriptions: path |
| `fyron.ml.persistence.save_estimator` | missing parameter descriptions: model, path |

## `fyron.ml.pipeline`

| API | Issues |
| --- | --- |
| `fyron.ml.pipeline.run_classification_pipeline` | missing parameter descriptions: X, y, model, test_size, stratify, random_state, handle_imbalance, use_boruta, boruta_kwargs, use_grid_search, param_grid, plot, pos_label, model_params |

## `fyron.ml.plots`

| API | Issues |
| --- | --- |
| `fyron.ml.plots.add_stat_annotations` | missing parameter descriptions: ax, stats_table, positions, heights, annotation_col, line_color, text_color, fontsize, loc |
| `fyron.ml.plots.plot_alluvial_flow` | missing parameter descriptions: data, path_col, stage_col, category_col, value_col, stage_order, title, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_binned_marker_heatmap` | missing parameter descriptions: data, row_col, col_col, value_col, row_order, col_order, title, cmap, missing_color, ax, save_path, fmt |
| `fyron.ml.plots.plot_bland_altman` | missing parameter descriptions: method_a, method_b, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_calibration_curve` | missing parameter descriptions: y_true, y_prob, n_bins, strategy, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_cohort_flow` | missing parameter descriptions: data, step_col, n_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_confusion_matrix` | missing parameter descriptions: y_true, y_pred, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_correlation_heatmap` | missing parameter descriptions: data, columns, method, group_col, title, annotate, annotate_significance, p_adjust, mask_upper, cmap, vmin, vmax, ax, save_path, fmt |
| `fyron.ml.plots.plot_cross_validated_roc` | missing parameter descriptions: y_true_col, y_prob_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_decision_curve` | missing parameter descriptions: data, threshold_col, model_col, treat_all_col, treat_none_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_density` | missing parameter descriptions: title, xlabel, ylabel, hue_order, palette, fill, alpha, rug, gridsize, ax, save_path, fmt |
| `fyron.ml.plots.plot_dice_by_label` | missing parameter descriptions: data, label_col, dice_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_directional_ratio_rows` | missing parameter descriptions: data, feature_col, ratio_col, lower_col, upper_col, p_col, group_col, n_col, ratio_label, title, protective_label, hazardous_label, reference, log_scale, xlim, annotate, estimate_label, ci_label, p_label, ax, save_path, fmt |
| `fyron.ml.plots.plot_external_validation_metrics` | missing parameter descriptions: data, metric_col, value_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_feature_importance` | missing parameter descriptions: importance_df, top_n, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_feature_selection_summary` | missing parameter descriptions: data, feature_col, selected_col, score_col, title, top_n, ax, save_path, fmt |
| `fyron.ml.plots.plot_forest_estimates` | missing parameter descriptions: data, label_col, estimate_col, lower_col, upper_col, p_col, p_adjust_col, n_col, group_col, table_columns, reference, log_scale, title, xlabel, ax, save_path, fmt |
| `fyron.ml.plots.plot_grouped_bar_with_significance` | missing parameter descriptions: data, x, y, hue, order, hue_order, estimator, error, ci, test, comparisons, p_thresholds, title, ylabel, xlabel, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_grouped_boxplot` | missing parameter descriptions: x, title, xlabel, ylabel, order, palette, show_points, point_alpha, random_state, comparisons, stat_test, p_adjust, annotation_format, hide_ns, return_stats, ax, save_path, fmt |
| `fyron.ml.plots.plot_grouped_correlation_heatmaps` | missing parameter descriptions: data, group_col, columns, method, title, annotate, annotate_significance, p_adjust, mask_upper, cmap, vmin, vmax, save_path, fmt |
| `fyron.ml.plots.plot_hazard_ratios` | missing parameter descriptions: cox_result, label_col, title, xlabel, table_columns, ax, save_path, fmt |
| `fyron.ml.plots.plot_histogram` | missing parameter descriptions: data, x, hue, group, bins, stat, multiple, title, xlabel, ylabel, hue_order, palette, alpha, ax, save_path, fmt |
| `fyron.ml.plots.plot_kaplan_meier` | missing return documentation; missing parameter descriptions: args, kwargs |
| `fyron.ml.plots.plot_likert_scale` | missing parameter descriptions: item_col, order, palette, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_metric_bars` | missing parameter descriptions: metrics, metrics_to_plot, model_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_missingness_bar` | missing parameter descriptions: data, column_col, missing_col, group_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_patterned_bar` | missing parameter descriptions: x, title, xlabel, ylabel, orientation, palette, hatches, annotate, ax, save_path, fmt |
| `fyron.ml.plots.plot_precision_recall_curve` | missing parameter descriptions: y_true, y_prob, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_raincloud` | missing parameter descriptions: data, x, y, order, title, ylabel, palette, random_state, ax, save_path, fmt |
| `fyron.ml.plots.plot_risk_score_distribution` | missing parameter descriptions: data, risk_col, event_col, event_labels, title, ylabel, jitter, violin, palette, random_state, ax, save_path, fmt |
| `fyron.ml.plots.plot_roc_curve` | missing parameter descriptions: y_true, y_prob, title, ax, save_path, fmt, pos_label |
| `fyron.ml.plots.plot_segmentation_overlay_grid` | missing parameter descriptions: image, mask, slice_indices, label, alpha, title, save_path, fmt |
| `fyron.ml.plots.plot_signed_feature_weights` | missing parameter descriptions: data, feature_col, weight_col, top_n, title, xlabel, positive_label, negative_label, ax, save_path, fmt |
| `fyron.ml.plots.plot_significance_bars` | missing parameter descriptions: data, label_col, p_col, threshold, title, xlabel, annotate, ax, save_path, fmt |
| `fyron.ml.plots.plot_stability_selection` | missing parameter descriptions: data, feature_col, frequency_col, threshold, title, top_n, ax, save_path, fmt |
| `fyron.ml.plots.plot_survival_calibration` | missing parameter descriptions: calibration_table, observed_col, predicted_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_swarmplot` | missing parameter descriptions: data, x, y, hue, order, hue_order, dodge, title, xlabel, ylabel, palette, point_size, point_alpha, random_state, comparisons, stat_test, p_adjust, annotation_format, hide_ns, return_stats, ax, save_path, fmt |
| `fyron.ml.plots.plot_swimmer` | missing parameter descriptions: data, patient_col, start_col, end_col, group_col, event_time_col, event_col, title, xlabel, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_table_one_summary` | missing parameter descriptions: data, variable_col, p_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_time_dependent_auc` | missing parameter descriptions: data, time_col, auc_col, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_volcano` | missing parameter descriptions: data, feature_col, effect_col, p_col, group_col, p_threshold, effect_threshold, top_n_labels, title, xlabel, ylabel, palette, ax, save_path, fmt |
| `fyron.ml.plots.plot_waffle` | missing parameter descriptions: category_col, palette, title, ax, save_path, fmt |
| `fyron.ml.plots.plot_waterfall` | missing parameter descriptions: values, labels, title, ylabel, threshold, ax, save_path, fmt |
| `fyron.ml.plots.stat_test_pairs` | missing parameter descriptions: x, alpha, label_col, p_col |

## `fyron.ml.search`

| API | Issues |
| --- | --- |
| `fyron.ml.search.grid_search_model` | missing parameter descriptions: estimator, param_grid, X_train, y_train, X_val, y_val, scoring, cv, n_jobs, refit, random_state, pos_label |

## `fyron.ml.training`

| API | Issues |
| --- | --- |
| `fyron.ml.training.train_random_forest` | missing parameter descriptions: X_train, y_train, X_test, y_test, class_weight, random_state, plot, pos_label, model_params |
| `fyron.ml.training.train_xgboost` | missing parameter descriptions: X_train, y_train, X_test, y_test, scale_pos_weight, random_state, plot, pos_label, model_params |

## `fyron.phenotyping.rules`

| API | Issues |
| --- | --- |
| `fyron.phenotyping.rules.combine_phenotypes` | missing parameter descriptions: tables, patient_col, strategy, phenotype_name |
| `fyron.phenotyping.rules.define_code_phenotype` | missing parameter descriptions: df, code_col, codes, patient_col, date_col, phenotype_name, code_system_col, code_systems |
| `fyron.phenotyping.rules.define_lab_threshold_phenotype` | missing parameter descriptions: df, value_col, threshold, direction, patient_col, date_col, phenotype_name |
| `fyron.phenotyping.rules.define_medication_exposure` | missing parameter descriptions: df, medication_col, medications, patient_col, start_col, end_col, phenotype_name |
| `fyron.phenotyping.rules.phenotype_summary` | missing parameter descriptions: df, phenotype_col, patient_col, group_col |

## `fyron.plotting_palettes`

| API | Issues |
| --- | --- |
| `fyron.plotting_palettes.get_colormap` | missing parameter descriptions: name, reverse |
| `fyron.plotting_palettes.get_palette` | missing parameter descriptions: name, n, reverse |
| `fyron.plotting_palettes.list_palettes` | missing parameter descriptions: kind |
| `fyron.plotting_palettes.palette_grayscale_contrast` | missing parameter descriptions: name_or_colors |
| `fyron.plotting_palettes.palette_luminance_table` | missing parameter descriptions: name_or_colors |
| `fyron.plotting_palettes.preview_palette` | missing parameter descriptions: name, n, save_path |
| `fyron.plotting_palettes.resolve_colormap` | missing parameter descriptions: cmap |
| `fyron.plotting_palettes.resolve_palette` | missing parameter descriptions: palette, n, default |
| `fyron.plotting_palettes.set_plot_style` | missing parameter descriptions: style, palette |

## `fyron.preprocessing.encoding`

| API | Issues |
| --- | --- |
| `fyron.preprocessing.encoding.apply_categorical_encoder` | missing parameter descriptions: df, encoder |
| `fyron.preprocessing.encoding.encode_categorical` | missing parameter descriptions: df, kwargs |
| `fyron.preprocessing.encoding.fit_categorical_encoder` | missing parameter descriptions: df, columns, drop_first, rare_min_count, rare_label |
| `fyron.preprocessing.encoding.summarize_encoding_plan` | missing parameter descriptions: df, columns, max_levels |

## `fyron.preprocessing.imputation`

| API | Issues |
| --- | --- |
| `fyron.preprocessing.imputation.apply_imputer` | missing parameter descriptions: df, imputer |
| `fyron.preprocessing.imputation.fit_imputer` | missing parameter descriptions: df, numeric, categorical, strategy_numeric, strategy_categorical, fill_value_numeric, fill_value_categorical, add_missing_indicators |
| `fyron.preprocessing.imputation.impute_dataframe` | missing parameter descriptions: df, kwargs |
| `fyron.preprocessing.imputation.summarize_imputation_plan` | missing parameter descriptions: df, numeric, categorical, strategy_numeric, strategy_categorical |

## `fyron.preprocessing.qc`

| API | Issues |
| --- | --- |
| `fyron.preprocessing.qc.compare_train_test_balance` | missing parameter descriptions: train, test, columns |
| `fyron.preprocessing.qc.detect_potential_leakage` | missing parameter descriptions: columns, outcome_keywords, time_keywords |
| `fyron.preprocessing.qc.find_duplicate_ids` | missing parameter descriptions: df, id_col |
| `fyron.preprocessing.qc.summarize_categorical_levels` | missing parameter descriptions: df, columns, max_levels, include_missing |
| `fyron.preprocessing.qc.summarize_missingness` | missing parameter descriptions: df, columns, group_col |

## `fyron.statistics.bootstrap`

| API | Issues |
| --- | --- |
| `fyron.statistics.bootstrap.BootstrapResult.to_dict` | missing description; missing parameter descriptions: include_distribution |
| `fyron.statistics.bootstrap.bootstrap_binary_classification_metrics` | missing parameter descriptions: y_true, y_pred, y_prob, metrics, pos_label, n_rounds, alpha, random_state, drop_invalid |
| `fyron.statistics.bootstrap.bootstrap_metric` | missing parameter descriptions: arrays, metric_func, metric_name, n_rounds, alpha, random_state, drop_invalid, metric_kwargs |
| `fyron.statistics.bootstrap.bootstrap_summary` | missing parameter descriptions: values, statistic, n_rounds, alpha, random_state |

## `fyron.statistics.effects`

| API | Issues |
| --- | --- |
| `fyron.statistics.effects.cliffs_delta` | missing parameter descriptions: group_a, group_b |
| `fyron.statistics.effects.cohens_d` | missing parameter descriptions: group_a, group_b |
| `fyron.statistics.effects.cramers_v` | missing parameter descriptions: table |
| `fyron.statistics.effects.odds_ratio_ci` | missing parameter descriptions: table, alpha, correction |
| `fyron.statistics.effects.risk_ratio_ci` | missing parameter descriptions: table, alpha, correction |
| `fyron.statistics.effects.standardized_mean_difference` | missing parameter descriptions: group_a, group_b, categorical |

## `fyron.statistics.tests`

| API | Issues |
| --- | --- |
| `fyron.statistics.tests.StatisticalTestResult.to_dict` | missing description |
| `fyron.statistics.tests.categorical_test` | missing parameter descriptions: table, method |
| `fyron.statistics.tests.compare_multiple_groups` | missing parameter descriptions: groups, method |
| `fyron.statistics.tests.compare_two_groups` | missing parameter descriptions: group_a, group_b, paired, method, alternative, equal_var |
| `fyron.statistics.tests.correlation_test` | missing parameter descriptions: x, y, method, alternative |
| `fyron.statistics.tests.normality_test` | missing parameter descriptions: values, method |

## `fyron.survival.boosting`

| API | Issues |
| --- | --- |
| `fyron.survival.boosting.train_gradient_survival_boosting` | missing parameter descriptions: duration_train, X_test, duration_test, model_params |

## `fyron.survival.cox`

| API | Issues |
| --- | --- |
| `fyron.survival.cox.fit_multivariate_cox` | missing parameter descriptions: df, duration_col, event_col, covariates, formula, strata, robust |
| `fyron.survival.cox.fit_univariate_cox` | missing parameter descriptions: duration_col |

## `fyron.survival.groups`

| API | Issues |
| --- | --- |
| `fyron.survival.groups.default_tau_from_observed_times` | missing parameter descriptions: df, duration_col, group_col |

## `fyron.survival.kaplan_meier`

| API | Issues |
| --- | --- |
| `fyron.survival.kaplan_meier.plot_kaplan_meier` | missing parameter descriptions: duration_col, split_column, split_method, split_bins, ci_alpha, censor_styles, title, xlabel, ylabel, legend_title, legend_kwargs, figsize, save_path, save_format, dpi |

## `fyron.survival.ph_diagnostics`

| API | Issues |
| --- | --- |
| `fyron.survival.ph_diagnostics.check_ph_assumptions` | missing parameter descriptions: include_residuals |
| `fyron.survival.ph_diagnostics.plot_schoenfeld_residuals` | missing parameter descriptions: residuals, covariates, time_col, residual_col, covariate_col, title, ax, save_path, fmt |
| `fyron.survival.ph_diagnostics.schoenfeld_test_table` | missing parameter descriptions: fitter, training_df, method, p_adjust, alpha |

## `fyron.survival.rmst`

| API | Issues |
| --- | --- |
| `fyron.survival.rmst.calculate_rmst` | missing parameter descriptions: duration_col |
| `fyron.survival.rmst.compare_rmst` | missing parameter descriptions: df, duration_col, event_col |

## `fyron.survival.time_varying`

| API | Issues |
| --- | --- |
| `fyron.survival.time_varying.expand_time_interaction_dataframe` | missing parameter descriptions: df, duration_col, event_col, covariates, time_interaction_covariates, time_transform, n_intervals, breakpoints, id_col, start_col, stop_col |
| `fyron.survival.time_varying.fit_cox_time_interactions` | missing parameter descriptions: df, duration_col, event_col, covariates, time_interaction_covariates, time_transform, n_intervals, breakpoints, id_col, strata, robust |
| `fyron.survival.time_varying.fit_time_varying_cox` | missing parameter descriptions: start_col |
| `fyron.survival.time_varying.run_survival_sensitivity_analysis` | missing parameter descriptions: df, duration_col, event_col, covariates, formula, group_col, rmst_tau, ph_p_value_threshold, time_interaction_covariates, time_transform, n_intervals, breakpoints, fit_time_interactions, fit_aft, fit_rmst |

## `fyron.survival.weibull_aft`

| API | Issues |
| --- | --- |
| `fyron.survival.weibull_aft.fit_weibull_aft` | missing parameter descriptions: df, duration_col |

## `fyron.validation.classification`

| API | Issues |
| --- | --- |
| `fyron.validation.classification.bootstrap_classification_metrics` | missing parameter descriptions: y_true |
| `fyron.validation.classification.calibration_summary` | missing parameter descriptions: y_true, y_prob, n_bins, pos_label |
| `fyron.validation.classification.decision_curve_table` | missing parameter descriptions: y_true, y_prob, thresholds, pos_label |
| `fyron.validation.classification.find_best_threshold` | missing parameter descriptions: y_true, y_prob, metric, pos_label, thresholds |
| `fyron.validation.classification.subgroup_metric_table` | missing parameter descriptions: df, group_col, y_true_col, y_pred_col, y_prob_col, pos_label |

## `fyron.validation.survival`

| API | Issues |
| --- | --- |
| `fyron.validation.survival.bootstrap_concordance_index` | missing parameter descriptions: df, duration_col, event_col, risk_col, n_rounds, random_state |
| `fyron.validation.survival.brier_score_at_time` | missing parameter descriptions: df, duration_col, event_col, prediction_col, time_horizon, censoring_df |
| `fyron.validation.survival.external_survival_validation` | missing parameter descriptions: train_summary_or_model, external_df, duration_col, event_col, risk_col, prediction_col, time_horizon, censoring_df |
| `fyron.validation.survival.survival_calibration_at_time` | missing parameter descriptions: df, duration_col, event_col, prediction_col, time_horizon, n_bins, censoring_df |
| `fyron.validation.survival.time_dependent_auc_table` | missing parameter descriptions: duration_col |

## `fyron.visualization.boa`

| API | Issues |
| --- | --- |
| `fyron.visualization.boa.create_boa_segmentation_collage` | missing parameter descriptions: window_center, row_label_prefix |

## `fyron.visualization.curate_previews`

| API | Issues |
| --- | --- |
| `fyron.visualization.curate_previews.discover_preview_sources` | missing parameter descriptions: input_dir, recursive, include_dicom, include_image_files |
| `fyron.visualization.curate_previews.prepare_curate_image_previews` | missing parameter descriptions: window_center |

## `fyron.visualization.volume_difference`

| API | Issues |
| --- | --- |
| `fyron.visualization.volume_difference.plot_volume_difference_heatmap` | missing parameter descriptions: volume_a, slice_index, slice_indices, label_a, window_center, rescale_slope, mr_normalization |
