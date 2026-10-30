# ML, Validation, And Explainability Reference

Classification pipelines, metrics, plotting wrappers, feature selection, validation, model interpretation, and filter-flow explainability.

For workflow context, see [ML, Validation, And Explainability module guide](../modules/ml.md).

## Functions And Classes

- [`fyron.explainability.inspection.explain_model_summary`](#fyronexplainabilityinspectionexplainmodelsummary)
- [`fyron.explainability.inspection.explain_patient_prediction`](#fyronexplainabilityinspectionexplainpatientprediction)
- [`fyron.explainability.inspection.partial_dependence_table`](#fyronexplainabilityinspectionpartialdependencetable)
- [`fyron.explainability.inspection.permutation_importance_table`](#fyronexplainabilityinspectionpermutationimportancetable)
- [`fyron.explainability.inspection.shap_summary_table`](#fyronexplainabilityinspectionshapsummarytable)
- [`fyron.explainability.inspection.shap_values_table`](#fyronexplainabilityinspectionshapvaluestable)
- [`fyron.feature_selection.selection.boruta_feature_selection`](#fyronfeatureselectionselectionborutafeatureselection)
- [`fyron.feature_selection.selection.combine_feature_selection_results`](#fyronfeatureselectionselectioncombinefeatureselectionresults)
- [`fyron.feature_selection.selection.correlation_filter`](#fyronfeatureselectionselectioncorrelationfilter)
- [`fyron.feature_selection.selection.model_importance_selection`](#fyronfeatureselectionselectionmodelimportanceselection)
- [`fyron.feature_selection.selection.permutation_importance_selection`](#fyronfeatureselectionselectionpermutationimportanceselection)
- [`fyron.feature_selection.selection.stability_selection`](#fyronfeatureselectionselectionstabilityselection)
- [`fyron.feature_selection.selection.univariate_feature_screening`](#fyronfeatureselectionselectionunivariatefeaturescreening)
- [`fyron.feature_selection.selection.variance_filter`](#fyronfeatureselectionselectionvariancefilter)
- [`fyron.flow.tracking.FlowStep`](#fyronflowtrackingflowstep)
- [`fyron.flow.tracking.FlowTracker`](#fyronflowtrackingflowtracker)
- [`fyron.flow.tracking.FlowTracker.add`](#fyronflowtrackingflowtrackeradd)
- [`fyron.flow.tracking.FlowTracker.step`](#fyronflowtrackingflowtrackerstep)
- [`fyron.flow.tracking.FlowTracker.cohort_table`](#fyronflowtrackingflowtrackercohorttable)
- [`fyron.flow.tracking.FlowTracker.plot`](#fyronflowtrackingflowtrackerplot)
- [`fyron.flow.tracking.FlowTracker.add_step`](#fyronflowtrackingflowtrackeraddstep)
- [`fyron.flow.tracking.FlowTracker.to_dataframe`](#fyronflowtrackingflowtrackertodataframe)
- [`fyron.flow.tracking.FlowTracker.to_markdown`](#fyronflowtrackingflowtrackertomarkdown)
- [`fyron.flow.tracking.FlowTracker.to_text_flowchart`](#fyronflowtrackingflowtrackertotextflowchart)
- [`fyron.flow.tracking.FlowTracker.print`](#fyronflowtrackingflowtrackerprint)
- [`fyron.flow.tracking.track_filter`](#fyronflowtrackingtrackfilter)
- [`fyron.ml.boruta_selection.run_boruta_feature_selection`](#fyronmlborutaselectionrunborutafeatureselection)
- [`fyron.ml.class_weights.compute_class_weights`](#fyronmlclassweightscomputeclassweights)
- [`fyron.ml.class_weights.compute_scale_pos_weight`](#fyronmlclassweightscomputescaleposweight)
- [`fyron.ml.class_weights.sample_weights_for_sklearn`](#fyronmlclassweightssampleweightsforsklearn)
- [`fyron.ml.cv.cross_validate_model`](#fyronmlcvcrossvalidatemodel)
- [`fyron.ml.defaults.get_default_param_grid`](#fyronmldefaultsgetdefaultparamgrid)
- [`fyron.ml.evaluation.apply_probability_calibrator`](#fyronmlevaluationapplyprobabilitycalibrator)
- [`fyron.ml.evaluation.evaluate_external_validation`](#fyronmlevaluationevaluateexternalvalidation)
- [`fyron.ml.evaluation.evaluate_locked_threshold`](#fyronmlevaluationevaluatelockedthreshold)
- [`fyron.ml.evaluation.fit_probability_calibrator`](#fyronmlevaluationfitprobabilitycalibrator)
- [`fyron.ml.evaluation.model_card_summary`](#fyronmlevaluationmodelcardsummary)
- [`fyron.ml.evaluation.nested_cross_validate_model`](#fyronmlevaluationnestedcrossvalidatemodel)
- [`fyron.ml.importance.get_feature_importance`](#fyronmlimportancegetfeatureimportance)
- [`fyron.ml.importance.plot_feature_importance`](#fyronmlimportanceplotfeatureimportance)
- [`fyron.ml.metrics.calculate_classification_metrics`](#fyronmlmetricscalculateclassificationmetrics)
- [`fyron.ml.persistence.load_estimator`](#fyronmlpersistenceloadestimator)
- [`fyron.ml.persistence.save_estimator`](#fyronmlpersistencesaveestimator)
- [`fyron.ml.pipeline.run_classification_pipeline`](#fyronmlpipelinerunclassificationpipeline)
- [`fyron.ml.plots.add_stat_annotations`](#fyronmlplotsaddstatannotations)
- [`fyron.ml.plots.format_p_value_annotation`](#fyronmlplotsformatpvalueannotation)
- [`fyron.ml.plots.plot_alluvial_flow`](#fyronmlplotsplotalluvialflow)
- [`fyron.ml.plots.plot_binned_marker_heatmap`](#fyronmlplotsplotbinnedmarkerheatmap)
- [`fyron.ml.plots.plot_bland_altman`](#fyronmlplotsplotblandaltman)
- [`fyron.ml.plots.plot_calibration_curve`](#fyronmlplotsplotcalibrationcurve)
- [`fyron.ml.plots.plot_cohort_flow`](#fyronmlplotsplotcohortflow)
- [`fyron.ml.plots.plot_confusion_matrix`](#fyronmlplotsplotconfusionmatrix)
- [`fyron.ml.plots.plot_correlation_heatmap`](#fyronmlplotsplotcorrelationheatmap)
- [`fyron.ml.plots.plot_cross_validated_roc`](#fyronmlplotsplotcrossvalidatedroc)
- [`fyron.ml.plots.plot_decision_curve`](#fyronmlplotsplotdecisioncurve)
- [`fyron.ml.plots.plot_density`](#fyronmlplotsplotdensity)
- [`fyron.ml.plots.plot_dice_by_label`](#fyronmlplotsplotdicebylabel)
- [`fyron.ml.plots.plot_directional_ratio_rows`](#fyronmlplotsplotdirectionalratiorows)
- [`fyron.ml.plots.plot_external_validation_metrics`](#fyronmlplotsplotexternalvalidationmetrics)
- [`fyron.ml.plots.plot_feature_importance`](#fyronmlplotsplotfeatureimportance)
- [`fyron.ml.plots.plot_feature_selection_summary`](#fyronmlplotsplotfeatureselectionsummary)
- [`fyron.ml.plots.plot_filled_kde`](#fyronmlplotsplotfilledkde)
- [`fyron.ml.plots.plot_forest_estimates`](#fyronmlplotsplotforestestimates)
- [`fyron.ml.plots.plot_grouped_bar_with_significance`](#fyronmlplotsplotgroupedbarwithsignificance)
- [`fyron.ml.plots.plot_grouped_boxplot`](#fyronmlplotsplotgroupedboxplot)
- [`fyron.ml.plots.plot_grouped_correlation_heatmaps`](#fyronmlplotsplotgroupedcorrelationheatmaps)
- [`fyron.ml.plots.plot_hazard_ratios`](#fyronmlplotsplothazardratios)
- [`fyron.ml.plots.plot_histogram`](#fyronmlplotsplothistogram)
- [`fyron.ml.plots.plot_kaplan_meier`](#fyronmlplotsplotkaplanmeier)
- [`fyron.ml.plots.plot_likert_scale`](#fyronmlplotsplotlikertscale)
- [`fyron.ml.plots.plot_metric_bars`](#fyronmlplotsplotmetricbars)
- [`fyron.ml.plots.plot_missingness_bar`](#fyronmlplotsplotmissingnessbar)
- [`fyron.ml.plots.plot_patterned_bar`](#fyronmlplotsplotpatternedbar)
- [`fyron.ml.plots.plot_precision_recall_curve`](#fyronmlplotsplotprecisionrecallcurve)
- [`fyron.ml.plots.plot_qq`](#fyronmlplotsplotqq)
- [`fyron.ml.plots.plot_raincloud`](#fyronmlplotsplotraincloud)
- [`fyron.ml.plots.plot_reference_band_grid`](#fyronmlplotsplotreferencebandgrid)
- [`fyron.ml.plots.plot_risk_score_distribution`](#fyronmlplotsplotriskscoredistribution)
- [`fyron.ml.plots.plot_roc_curve`](#fyronmlplotsplotroccurve)
- [`fyron.ml.plots.plot_segmentation_overlay_grid`](#fyronmlplotsplotsegmentationoverlaygrid)
- [`fyron.ml.plots.plot_signed_feature_weights`](#fyronmlplotsplotsignedfeatureweights)
- [`fyron.ml.plots.plot_significance_bars`](#fyronmlplotsplotsignificancebars)
- [`fyron.ml.plots.plot_stability_selection`](#fyronmlplotsplotstabilityselection)
- [`fyron.ml.plots.plot_survival_calibration`](#fyronmlplotsplotsurvivalcalibration)
- [`fyron.ml.plots.plot_swarmplot`](#fyronmlplotsplotswarmplot)
- [`fyron.ml.plots.plot_swimmer`](#fyronmlplotsplotswimmer)
- [`fyron.ml.plots.plot_table_one_summary`](#fyronmlplotsplottableonesummary)
- [`fyron.ml.plots.plot_time_dependent_auc`](#fyronmlplotsplottimedependentauc)
- [`fyron.ml.plots.plot_volcano`](#fyronmlplotsplotvolcano)
- [`fyron.ml.plots.plot_waffle`](#fyronmlplotsplotwaffle)
- [`fyron.ml.plots.plot_waterfall`](#fyronmlplotsplotwaterfall)
- [`fyron.ml.plots.stat_test_pairs`](#fyronmlplotsstattestpairs)
- [`fyron.ml.search.grid_search_model`](#fyronmlsearchgridsearchmodel)
- [`fyron.ml.splitting.train_test_split_data`](#fyronmlsplittingtraintestsplitdata)
- [`fyron.ml.training.train_random_forest`](#fyronmltrainingtrainrandomforest)
- [`fyron.ml.training.train_xgboost`](#fyronmltrainingtrainxgboost)
- [`fyron.validation.classification.bootstrap_classification_metrics`](#fyronvalidationclassificationbootstrapclassificationmetrics)
- [`fyron.validation.classification.calibration_summary`](#fyronvalidationclassificationcalibrationsummary)
- [`fyron.validation.classification.decision_curve_table`](#fyronvalidationclassificationdecisioncurvetable)
- [`fyron.validation.classification.find_best_threshold`](#fyronvalidationclassificationfindbestthreshold)
- [`fyron.validation.classification.subgroup_metric_table`](#fyronvalidationclassificationsubgroupmetrictable)
- [`fyron.validation.survival.bootstrap_concordance_index`](#fyronvalidationsurvivalbootstrapconcordanceindex)
- [`fyron.validation.survival.brier_score_at_time`](#fyronvalidationsurvivalbrierscoreattime)
- [`fyron.validation.survival.external_survival_validation`](#fyronvalidationsurvivalexternalsurvivalvalidation)
- [`fyron.validation.survival.survival_calibration_at_time`](#fyronvalidationsurvivalsurvivalcalibrationattime)
- [`fyron.validation.survival.time_dependent_auc_table`](#fyronvalidationsurvivaltimedependentauctable)

## `fyron.explainability.inspection.explain_model_summary`

Create a reviewer-facing model explanation summary table.

**Import path:** `fyron.explainability.inspection.explain_model_summary`

```python
explain_model_summary(*, importance: pd.DataFrame | None = None, shap_summary: pd.DataFrame | None = None, metrics: Mapping[str, Any] | pd.DataFrame | None = None, feature_qc: pd.DataFrame | None = None, notes: Mapping[str, str] | pd.DataFrame | None = None, feature_col: str = 'feature') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `importance` | no | `pd.DataFrame  or  None` | `None` | Feature importance table, for example from ``permutation_importance_table``. |
| `shap_summary` | no | `pd.DataFrame  or  None` | `None` | Feature-level SHAP summary table, for example from ``shap_summary_table``. |
| `metrics` | no | `Mapping[str, Any]  or  pd.DataFrame  or  None` | `None` | Optional model metrics as a dictionary or one-row DataFrame. Metrics are repeated on each feature row for convenient review/export. |
| `feature_qc` | no | `pd.DataFrame  or  None` | `None` | Optional feature quality-control table, for example from ``fyron.preprocessing.feature_matrix_report``. |
| `notes` | no | `Mapping[str, str]  or  pd.DataFrame  or  None` | `None` | Optional mapping or DataFrame with feature-specific reviewer notes. |
| `feature_col` | no | `str` | `'feature'` | Column name containing feature names in feature-level inputs. |

### Returns

`pandas.DataFrame` - One row per feature with available importance, SHAP, QC, metric, and note columns merged by feature name.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.explainability.inspection.explain_patient_prediction`

Return the strongest positive and negative drivers for one prediction.

**Import path:** `fyron.explainability.inspection.explain_patient_prediction`

```python
explain_patient_prediction(contributions: pd.DataFrame, *, row_index: Any | None = None, patient_id: Any | None = None, row_col: str = 'row_index', patient_col: str = 'patient_id', feature_col: str = 'feature', contribution_col: str = 'shap_value', feature_value_col: str = 'feature_value', top_n: int = 5) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `contributions` | yes | `pd.DataFrame` |  | Long contribution table with feature names and signed contributions, such as output from ``shap_values_table``. |
| `row_index` | no | `Any  or  None` | `None` | Optional row identifier to select when ``row_col`` exists. |
| `patient_id` | no | `Any  or  None` | `None` | Optional patient identifier to select when ``patient_col`` exists. |
| `row_col` | no | `str` | `'row_index'` | See signature. |
| `patient_col` | no | `str` | `'patient_id'` | See signature. |
| `feature_col` | no | `str` | `'feature'` | See signature. |
| `contribution_col` | no | `str` | `'shap_value'` | See signature. |
| `feature_value_col` | no | `str` | `'feature_value'` | Column names used to identify rows, features, contributions, and values. |
| `top_n` | no | `int` | `5` | Number of positive and negative drivers to return. |

### Returns

`pandas.DataFrame` - Feature-level contribution rows sorted by direction and absolute impact.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.explainability.inspection.partial_dependence_table`

Return one-way partial dependence values in long tabular form.

**Import path:** `fyron.explainability.inspection.partial_dependence_table`

```python
partial_dependence_table(estimator: Any, X: Any, *, features: Sequence[int | str], feature_names: Sequence[str] | None = None, grid_resolution: int = 50) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | yes | `Any` |  | See signature. |
| `features` | yes | `Sequence[int  or  str]` |  | See signature. |
| `feature_names` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `grid_resolution` | no | `int` | `50` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.explainability.inspection.permutation_importance_table`

Return sklearn permutation importance as a sorted DataFrame.

**Import path:** `fyron.explainability.inspection.permutation_importance_table`

```python
permutation_importance_table(estimator: Any, X: Any, y: Any, *, feature_names: Sequence[str] | None = None, n_repeats: int = 10, scoring: str | None = None, random_state: int = 42) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | yes | `Any` |  | See signature. |
| `y` | yes | `Any` |  | See signature. |
| `feature_names` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `n_repeats` | no | `int` | `10` | See signature. |
| `scoring` | no | `str  or  None` | `None` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.explainability.inspection.shap_summary_table`

Return mean absolute SHAP importance by feature.

**Import path:** `fyron.explainability.inspection.shap_summary_table`

```python
shap_summary_table(estimator: Any, X: Any, *, feature_names: Sequence[str] | None = None, explainer: Any | None = None, background_data: Any | None = None, max_rows: int | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | yes | `Any` |  | See signature. |
| `feature_names` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `explainer` | no | `Any  or  None` | `None` | See signature. |
| `background_data` | no | `Any  or  None` | `None` | See signature. |
| `max_rows` | no | `int  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.explainability.inspection.shap_values_table`

Return SHAP values in long patient-feature form.

**Import path:** `fyron.explainability.inspection.shap_values_table`

```python
shap_values_table(estimator: Any, X: Any, *, feature_names: Sequence[str] | None = None, explainer: Any | None = None, background_data: Any | None = None, max_rows: int | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | yes | `Any` |  | See signature. |
| `feature_names` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `explainer` | no | `Any  or  None` | `None` | See signature. |
| `background_data` | no | `Any  or  None` | `None` | See signature. |
| `max_rows` | no | `int  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.boruta_feature_selection`

Run Boruta through the scientific feature-selection namespace.

**Import path:** `fyron.feature_selection.selection.boruta_feature_selection`

```python
boruta_feature_selection(X: Any, y: Any, **kwargs: Any) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `Any` |  | See signature. |
| `y` | yes | `Any` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.combine_feature_selection_results`

Combine several feature-selection result dictionaries.

**Import path:** `fyron.feature_selection.selection.combine_feature_selection_results`

```python
combine_feature_selection_results(results: Mapping[str, Mapping[str, Any]] | Sequence[Mapping[str, Any]], *, strategy: Literal['consensus', 'union', 'intersection'] = 'consensus', min_methods: int = 2) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `results` | yes | `Mapping[str, Mapping[str, Any]]  or  Sequence[Mapping[str, Any]]` |  | See signature. |
| `strategy` | no | `Literal['consensus', 'union', 'intersection']` | `'consensus'` | See signature. |
| `min_methods` | no | `int` | `2` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.correlation_filter`

Find redundant numeric features and drop later correlated features.

**Import path:** `fyron.feature_selection.selection.correlation_filter`

```python
correlation_filter(X: Any, *, threshold: float = 0.85, method: Literal['pearson', 'spearman', 'kendall'] = 'spearman') -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `Any` |  | See signature. |
| `threshold` | no | `float` | `0.85` | See signature. |
| `method` | no | `Literal['pearson', 'spearman', 'kendall']` | `'spearman'` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.model_importance_selection`

Fit an estimator and select features by importance or coefficient magnitude.

**Import path:** `fyron.feature_selection.selection.model_importance_selection`

```python
model_importance_selection(estimator: Any, X: Any, y: Any, *, threshold: float | None = None, top_n: int | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | yes | `Any` |  | See signature. |
| `y` | yes | `Any` |  | See signature. |
| `threshold` | no | `float  or  None` | `None` | See signature. |
| `top_n` | no | `int  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.permutation_importance_selection`

Select features using sklearn permutation importance.

**Import path:** `fyron.feature_selection.selection.permutation_importance_selection`

```python
permutation_importance_selection(estimator: Any, X: Any, y: Any, *, n_repeats: int = 10, scoring: str | None = None, random_state: int = 42, threshold: float | None = None, top_n: int | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | yes | `Any` |  | See signature. |
| `y` | yes | `Any` |  | See signature. |
| `n_repeats` | no | `int` | `10` | See signature. |
| `scoring` | no | `str  or  None` | `None` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `threshold` | no | `float  or  None` | `None` | See signature. |
| `top_n` | no | `int  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.stability_selection`

Repeated subsampling feature selection by model importance.

**Import path:** `fyron.feature_selection.selection.stability_selection`

```python
stability_selection(estimator: Any, X: Any, y: Any, *, n_rounds: int = 100, sample_fraction: float = 0.75, selection_threshold: float = 0.6, random_state: int = 42) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | yes | `Any` |  | See signature. |
| `y` | yes | `Any` |  | See signature. |
| `n_rounds` | no | `int` | `100` | See signature. |
| `sample_fraction` | no | `float` | `0.75` | See signature. |
| `selection_threshold` | no | `float` | `0.6` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.univariate_feature_screening`

Screen features with transparent univariate tests and FDR correction.

**Import path:** `fyron.feature_selection.selection.univariate_feature_screening`

```python
univariate_feature_screening(X: Any, y: Any, *, task: Task = 'classification', alpha: float = 0.05, correction: Literal['fdr_bh', 'none'] = 'fdr_bh') -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `Any` |  | See signature. |
| `y` | yes | `Any` |  | See signature. |
| `task` | no | `Task` | `'classification'` | See signature. |
| `alpha` | no | `float` | `0.05` | See signature. |
| `correction` | no | `Literal['fdr_bh', 'none']` | `'fdr_bh'` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.feature_selection.selection.variance_filter`

Filter constant or near-constant numeric features.

**Import path:** `fyron.feature_selection.selection.variance_filter`

```python
variance_filter(X: Any, *, threshold: float = 0.0) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `Any` |  | See signature. |
| `threshold` | no | `float` | `0.0` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.flow.tracking.FlowStep`

One recorded cohort/filter-flow step.

**Import path:** `fyron.flow.tracking.FlowStep`

```python
FlowStep()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.flow.tracking.FlowTracker`

Record ordered cohort filter steps and render flow summaries.

**Import path:** `fyron.flow.tracking.FlowTracker`

```python
FlowTracker(self, title: str = 'Cohort flow', *, id_col: str | None = None, progress: bool = False)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | no | `str` | `'Cohort flow'` | Human-readable name for the cohort or workflow. |
| `id_col` | no | `str  or  None` | `None` | Optional analysis-unit column. Count distinct nonmissing IDs instead of rows and track membership changes between cohort steps. |
| `progress` | no | `bool` | `False` | Display nonidentifying step labels and counts on the interactive console. |

### Returns

Class constructor.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

### Public Methods

#### `fyron.flow.tracking.FlowTracker.add`

Record a result unchanged, counting unique IDs when configured.

**Import path:** `fyron.flow.tracking.FlowTracker.add`

```python
FlowTracker.add(self, label: str, result: Any, *, reason: str | None = None, kind: str = 'cohort') -> Any
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `label` | yes | `str` |  | Nonidentifying step name. |
| `result` | yes | `Any` |  | DataFrame or Fyron DataFrame/report dictionary. |
| `reason` | no | `str  or  None` | `None` | Optional selection reason. |
| `kind` | no | `str` | `'cohort'` | ``cohort`` for a selection, ``query`` for retrieval activity. |

#### Returns

`object` - The original result, unchanged.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.step`

Announce an operation and record its result on successful context exit.

**Import path:** `fyron.flow.tracking.FlowTracker.step`

```python
FlowTracker.step(self, label: str, *, kind: str = 'cohort', reason: str | None = None)
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `label` | yes | `str` |  | Nonidentifying operation name. |
| `kind` | no | `str` | `'cohort'` | ``cohort`` or ``query``. |
| `reason` | no | `str  or  None` | `None` | Optional selection reason. |

#### Returns

`context manager` - A step with a ``result(value)`` method.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.cohort_table`

Return only completed cohort selections, excluding query activities.

**Import path:** `fyron.flow.tracking.FlowTracker.cohort_table`

```python
FlowTracker.cohort_table(self) -> pd.DataFrame
```

#### Parameters

No parameters documented.

#### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.plot`

Plot completed cohort selections using Fyron's plotting facade.

**Import path:** `fyron.flow.tracking.FlowTracker.plot`

```python
FlowTracker.plot(self, **kwargs: Any)
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `kwargs` | yes | `Any` |  | Options forwarded to ``fyron.plotting.plot_cohort_flow``. |

#### Returns

`tuple` - Figure and axes from the existing plotting function.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.add_step`

Record a DataFrame step and return ``df`` unchanged.

**Import path:** `fyron.flow.tracking.FlowTracker.add_step`

```python
FlowTracker.add_step(self, label: str, df: pd.DataFrame, *, reason: str | None = None, metadata: Mapping[str, Any] | None = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `label` | yes | `str` |  | Short reviewer-facing step label. |
| `df` | yes | `pd.DataFrame` |  | DataFrame after the filter or workflow step. |
| `reason` | no | `str  or  None` | `None` | Optional exclusion reason, usually describing why rows were removed from the previous step. |
| `metadata` | no | `Mapping[str, Any]  or  None` | `None` | Optional JSON-like metadata such as filter parameters or notes. |

#### Returns

`pandas.DataFrame` - The same DataFrame object passed to ``df`` for pipeline-friendly use.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.to_dataframe`

Return the recorded flow as a structured DataFrame.

**Import path:** `fyron.flow.tracking.FlowTracker.to_dataframe`

```python
FlowTracker.to_dataframe(self) -> pd.DataFrame
```

#### Parameters

No parameters documented.

#### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.to_markdown`

Render the flow as a Markdown table.

**Import path:** `fyron.flow.tracking.FlowTracker.to_markdown`

```python
FlowTracker.to_markdown(self, *, digits: int = 1) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `digits` | no | `int` | `1` | See signature. |

#### Returns

`str`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.to_text_flowchart`

Render an arrow-style text flow chart.

**Import path:** `fyron.flow.tracking.FlowTracker.to_text_flowchart`

```python
FlowTracker.to_text_flowchart(self, *, digits: int = 1) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `digits` | no | `int` | `1` | See signature. |

#### Returns

`str`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

#### `fyron.flow.tracking.FlowTracker.print`

Print and return a Bits & Flames-style console flow summary.

**Import path:** `fyron.flow.tracking.FlowTracker.print`

```python
FlowTracker.print(self, *, stream: TextIO | None = None, color: bool = True, quiet: bool = False) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `stream` | no | `TextIO  or  None` | `None` | See signature. |
| `color` | no | `bool` | `True` | See signature. |
| `quiet` | no | `bool` | `False` | See signature. |

#### Returns

`str`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.flow.tracking.track_filter`

Decorate a DataFrame filter function and record its output.

**Import path:** `fyron.flow.tracking.track_filter`

```python
track_filter(tracker: FlowTracker, *, label: str, reason: str | None = None, metadata: Mapping[str, Any] | None = None) -> Callable[[F], F]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `tracker` | yes | `FlowTracker` |  | FlowTracker instance that receives the recorded step. |
| `label` | yes | `str` |  | Reviewer-facing label for the filter. |
| `reason` | no | `str  or  None` | `None` | Optional exclusion reason. |
| `metadata` | no | `Mapping[str, Any]  or  None` | `None` | Optional JSON-like metadata saved with the step. |

### Returns

`callable` - Wrapped function that returns the original DataFrame result after recording it in ``tracker``.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.boruta_selection.run_boruta_feature_selection`

Run Boruta all-relevant feature selection.

**Import path:** `fyron.ml.boruta_selection.run_boruta_feature_selection`

```python
run_boruta_feature_selection(X: ArrayLikeInput, y: ArrayLikeInput, estimator: Any | None = None, *, class_weight: str | dict[Any, float] | None = 'balanced', max_iter: int = 100, random_state: int = 42) -> BorutaResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `ArrayLikeInput` |  | See signature. |
| `y` | yes | `ArrayLikeInput` |  | See signature. |
| `estimator` | no | `Any  or  None` | `None` | See signature. |
| `class_weight` | no | `str  or  dict[Any, float]  or  None` | `'balanced'` | See signature. |
| `max_iter` | no | `int` | `100` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |

### Returns

`BorutaResult`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.class_weights.compute_class_weights`

Compute class weights as a label-to-weight mapping.

**Import path:** `fyron.ml.class_weights.compute_class_weights`

```python
compute_class_weights(y: ArrayLikeInput, *, class_weight: str = 'balanced') -> dict[Any, float]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y` | yes | `ArrayLikeInput` |  | Target vector. |
| `class_weight` | no | `str` | `'balanced'` | Strategy passed to :func:`sklearn.utils.class_weight.compute_class_weight`. |

### Returns

`dict` - Mapping from class label to weight. Pass directly to :class:`sklearn.ensemble.RandomForestClassifier(class_weight=...)`.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.class_weights.compute_scale_pos_weight`

Compute XGBoost ``scale_pos_weight`` for binary classification.

**Import path:** `fyron.ml.class_weights.compute_scale_pos_weight`

```python
compute_scale_pos_weight(y: ArrayLikeInput, *, pos_label: Any | None = None) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y` | yes | `ArrayLikeInput` |  | Binary target vector. |
| `pos_label` | no | `Any  or  None` | `None` | Positive class label. Defaults to the larger of the two unique labels. |

### Returns

`float` - Value suitable for :class:`xgboost.XGBClassifier(scale_pos_weight=...)`.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.class_weights.sample_weights_for_sklearn`

Per-sample weights for sklearn estimators that accept ``sample_weight``.

**Import path:** `fyron.ml.class_weights.sample_weights_for_sklearn`

```python
sample_weights_for_sklearn(y: ArrayLikeInput, *, class_weight: str | dict[Any, float] = 'balanced') -> np.ndarray
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y` | yes | `ArrayLikeInput` |  | See signature. |
| `class_weight` | no | `str  or  dict[Any, float]` | `'balanced'` | See signature. |

### Returns

`np.ndarray`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.cv.cross_validate_model`

Stratified k-fold cross-validation with healthcare-oriented metrics.

**Import path:** `fyron.ml.cv.cross_validate_model`

```python
cross_validate_model(estimator: Any, X: ArrayLikeInput, y: ArrayLikeInput, *, cv: int = 5, random_state: int = 42, return_models: bool = False, return_oof_predictions: bool = False, pos_label: Any | None = None) -> CVResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | Any sklearn-compatible classifier (must support ``fit`` / ``predict``). |
| `X` | yes | `ArrayLikeInput` |  | See signature. |
| `y` | yes | `ArrayLikeInput` |  | Full dataset. |
| `cv` | no | `int` | `5` | Number of folds. |
| `random_state` | no | `int` | `42` | See signature. |
| `return_models` | no | `bool` | `False` | If True, include a list of fitted models (one per fold). |
| `return_oof_predictions` | no | `bool` | `False` | If True, include out-of-fold predictions and positive-class probabilities. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`dict` - Keys: ``fold_metrics`` (DataFrame), ``mean_metrics``, ``std_metrics``, and optionally ``models``, ``oof_pred``, ``oof_prob``.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.defaults.get_default_param_grid`

Return a sensible default parameter grid for grid search.

**Import path:** `fyron.ml.defaults.get_default_param_grid`

```python
get_default_param_grid(model_name: str) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `model_name` | yes | `str` |  | ``"random_forest"``, ``"xgboost"``, or ``"survival_gradient_boosting"``. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.evaluation.apply_probability_calibrator`

Return calibrated positive-class probabilities.

**Import path:** `fyron.ml.evaluation.apply_probability_calibrator`

```python
apply_probability_calibrator(calibrator: Any, X: ArrayLikeInput, *, positive_class_index: int = 1) -> np.ndarray
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `calibrator` | yes | `Any` |  | See signature. |
| `X` | yes | `ArrayLikeInput` |  | See signature. |
| `positive_class_index` | no | `int` | `1` | See signature. |

### Returns

`np.ndarray`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.evaluation.evaluate_external_validation`

Evaluate a fitted sklearn-style estimator on an external cohort.

**Import path:** `fyron.ml.evaluation.evaluate_external_validation`

```python
evaluate_external_validation(estimator: Any, X_external: ArrayLikeInput, y_external: ArrayLikeInput, *, threshold: float | None = None, pos_label: Any | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X_external` | yes | `ArrayLikeInput` |  | See signature. |
| `y_external` | yes | `ArrayLikeInput` |  | See signature. |
| `threshold` | no | `float  or  None` | `None` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.evaluation.evaluate_locked_threshold`

Evaluate probabilities with a pre-specified decision threshold.

**Import path:** `fyron.ml.evaluation.evaluate_locked_threshold`

```python
evaluate_locked_threshold(y_true: ArrayLikeInput, y_prob: ArrayLikeInput, *, threshold: float, pos_label: Any = 1, neg_label: Any = 0) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `ArrayLikeInput` |  | See signature. |
| `y_prob` | yes | `ArrayLikeInput` |  | See signature. |
| `threshold` | yes | `float` |  | See signature. |
| `pos_label` | no | `Any` | `1` | See signature. |
| `neg_label` | no | `Any` | `0` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.evaluation.fit_probability_calibrator`

Fit a probability calibrator for an already fitted classifier.

**Import path:** `fyron.ml.evaluation.fit_probability_calibrator`

```python
fit_probability_calibrator(estimator: Any, X_calibration: ArrayLikeInput, y_calibration: ArrayLikeInput, *, method: str = 'sigmoid') -> CalibratedClassifierCV
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X_calibration` | yes | `ArrayLikeInput` |  | See signature. |
| `y_calibration` | yes | `ArrayLikeInput` |  | See signature. |
| `method` | no | `str` | `'sigmoid'` | See signature. |

### Returns

`CalibratedClassifierCV`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.evaluation.model_card_summary`

Create a small inspectable model-card summary dictionary.

**Import path:** `fyron.ml.evaluation.model_card_summary`

```python
model_card_summary(estimator: Any, *, X: ArrayLikeInput | None = None, y: ArrayLikeInput | None = None, metrics: Mapping[str, Any] | None = None, intended_use: str | None = None, limitations: str | None = None, random_state: int | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `X` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `y` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `metrics` | no | `Mapping[str, Any]  or  None` | `None` | See signature. |
| `intended_use` | no | `str  or  None` | `None` | See signature. |
| `limitations` | no | `str  or  None` | `None` | See signature. |
| `random_state` | no | `int  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.evaluation.nested_cross_validate_model`

Run nested stratified CV with an inner grid search.

**Import path:** `fyron.ml.evaluation.nested_cross_validate_model`

```python
nested_cross_validate_model(estimator: Any, param_grid: Mapping[str, Sequence[Any]], X: ArrayLikeInput, y: ArrayLikeInput, *, outer_cv: int = 5, inner_cv: int = 3, scoring: str = 'roc_auc', random_state: int = 42, n_jobs: int = -1, pos_label: Any | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `param_grid` | yes | `Mapping[str, Sequence[Any]]` |  | See signature. |
| `X` | yes | `ArrayLikeInput` |  | See signature. |
| `y` | yes | `ArrayLikeInput` |  | See signature. |
| `outer_cv` | no | `int` | `5` | See signature. |
| `inner_cv` | no | `int` | `3` | See signature. |
| `scoring` | no | `str` | `'roc_auc'` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `n_jobs` | no | `int` | `-1` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.importance.get_feature_importance`

Extract sorted feature importances from a tree-based model.

**Import path:** `fyron.ml.importance.get_feature_importance`

```python
get_feature_importance(model: Any, feature_names: list[str] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `model` | yes | `Any` |  | See signature. |
| `feature_names` | no | `list[str]  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.importance.plot_feature_importance`

Plot feature importances for a fitted model.

**Import path:** `fyron.ml.importance.plot_feature_importance`

```python
plot_feature_importance(model: Any, feature_names: list[str] | None = None, *, top_n: int = 20, title: str = 'Feature importance', save_path: str | None = None, fmt: str = 'png') -> tuple[Any, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `model` | yes | `Any` |  | See signature. |
| `feature_names` | no | `list[str]  or  None` | `None` | See signature. |
| `top_n` | no | `int` | `20` | See signature. |
| `title` | no | `str` | `'Feature importance'` | See signature. |
| `save_path` | no | `str  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`tuple[Any, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.metrics.calculate_classification_metrics`

Compute binary classification metrics and confusion-matrix counts.

**Import path:** `fyron.ml.metrics.calculate_classification_metrics`

```python
calculate_classification_metrics(y_true: ArrayLikeInput, y_pred: ArrayLikeInput, y_prob: ArrayLike | None = None, *, pos_label: Any | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `ArrayLikeInput` |  | Ground-truth labels. |
| `y_pred` | yes | `ArrayLikeInput` |  | Predicted labels. |
| `y_prob` | no | `ArrayLike  or  None` | `None` | Predicted probability of the positive class (binary only). |
| `pos_label` | no | `Any  or  None` | `None` | Positive class label for binary metrics. |

### Returns

`dict` - Keys include ``accuracy``, ``f1``, ``precision``, ``recall``, ``sensitivity``, ``specificity``, ``balanced_accuracy``, ``auc``, and ``tn``, ``fp``, ``fn``, ``tp``.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.persistence.load_estimator`

Load an estimator saved with :func:`save_estimator`.

**Import path:** `fyron.ml.persistence.load_estimator`

```python
load_estimator(path: str | Path) -> Any
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |

### Returns

`Any`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.persistence.save_estimator`

Serialize a fitted estimator with joblib.

**Import path:** `fyron.ml.persistence.save_estimator`

```python
save_estimator(model: Any, path: str | Path) -> None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `model` | yes | `Any` |  | See signature. |
| `path` | yes | `str  or  Path` |  | See signature. |

### Returns

`None`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.pipeline.run_classification_pipeline`

Split, optionally select features within training folds, then evaluate.

**Import path:** `fyron.ml.pipeline.run_classification_pipeline`

```python
run_classification_pipeline(X: Any, y: Any, *, model: Literal['random_forest', 'xgboost'] = 'random_forest', test_size: float = 0.2, stratify: bool = True, random_state: int = 42, handle_imbalance: bool = True, use_boruta: bool = False, boruta_kwargs: dict[str, Any] | None = None, use_grid_search: bool = False, param_grid: dict[str, Any] | None = None, plot: bool = False, pos_label: Any | None = None, **model_params: Any) -> PipelineResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `Any` |  | See signature. |
| `y` | yes | `Any` |  | See signature. |
| `model` | no | `Literal['random_forest', 'xgboost']` | `'random_forest'` | See signature. |
| `test_size` | no | `float` | `0.2` | See signature. |
| `stratify` | no | `bool` | `True` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `handle_imbalance` | no | `bool` | `True` | See signature. |
| `use_boruta` | no | `bool` | `False` | See signature. |
| `boruta_kwargs` | no | `dict[str, Any]  or  None` | `None` | See signature. |
| `use_grid_search` | no | `bool` | `False` | See signature. |
| `param_grid` | no | `dict[str, Any]  or  None` | `None` | See signature. |
| `plot` | no | `bool` | `False` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |
| `model_params` | yes | `Any` |  | See signature. |

### Returns

`PipelineResult`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.add_stat_annotations`

Add bracket-style statistical annotations to an existing categorical plot.

**Import path:** `fyron.ml.plots.add_stat_annotations`

```python
add_stat_annotations(ax: Axes, stats_table: pd.DataFrame, *, positions: Mapping[tuple[str, str], float] | None = None, heights: Mapping[tuple[str, str], float] | None = None, annotation_col: str = 'annotation', line_color: str = BOARISK_PALETTE['ink'], text_color: str = BOARISK_PALETTE['ink'], fontsize: float = 9, loc: Literal['outside', 'inside'] = 'outside') -> Axes
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `ax` | yes | `Axes` |  | See signature. |
| `stats_table` | yes | `pd.DataFrame` |  | See signature. |
| `positions` | no | `Mapping[tuple[str, str], float]  or  None` | `None` | See signature. |
| `heights` | no | `Mapping[tuple[str, str], float]  or  None` | `None` | See signature. |
| `annotation_col` | no | `str` | `'annotation'` | See signature. |
| `line_color` | no | `str` | `BOARISK_PALETTE['ink']` | See signature. |
| `text_color` | no | `str` | `BOARISK_PALETTE['ink']` | See signature. |
| `fontsize` | no | `float` | `9` | See signature. |
| `loc` | no | `Literal['outside', 'inside']` | `'outside'` | See signature. |

### Returns

`Axes`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.format_p_value_annotation`

Format a p-value for manuscript-style plot annotations.

**Import path:** `fyron.ml.plots.format_p_value_annotation`

```python
format_p_value_annotation(p_value: Any, *, text_format: AnnotationFormat = 'star', thresholds: Sequence[tuple[float, str]] = ((0.001, '***'), (0.01, '**'), (0.05, '*')), ns_label: str = 'ns') -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `p_value` | yes | `Any` |  | Raw or adjusted p-value. |
| `text_format` | no | `AnnotationFormat` | `'star'` | ``"star"`` for significance stars, ``"pvalue"`` for explicit p-values, or ``"simple"`` for compact values such as ``p<0.001``. |
| `thresholds` | no | `Sequence[tuple[float, str]]` | `((0.001, '***'), (0.01, '**'), (0.05, '*'))` | P-value thresholds used for star labels. |
| `ns_label` | no | `str` | `'ns'` | Label for non-significant comparisons in ``"star"`` mode. |

### Returns

`str` - Text label suitable for plot brackets.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_alluvial_flow`

Plot categorical flows across ordered stages.

**Import path:** `fyron.ml.plots.plot_alluvial_flow`

```python
plot_alluvial_flow(data: Any, *, path_col: str = 'path', stage_col: str = 'stage', category_col: str = 'category', value_col: str | None = 'value', stage_order: Sequence[Any] | None = None, title: str = 'Alluvial flow', palette: str | Sequence[str] | None = 'bf_vibrant_muted', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `path_col` | no | `str` | `'path'` | See signature. |
| `stage_col` | no | `str` | `'stage'` | See signature. |
| `category_col` | no | `str` | `'category'` | See signature. |
| `value_col` | no | `str  or  None` | `'value'` | See signature. |
| `stage_order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Alluvial flow'` | See signature. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'bf_vibrant_muted'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_binned_marker_heatmap`

Plot a discrete patient-feature marker heatmap.

**Import path:** `fyron.ml.plots.plot_binned_marker_heatmap`

```python
plot_binned_marker_heatmap(data: Any, *, row_col: str = 'feature', col_col: str = 'sample', value_col: str = 'bin', row_order: Sequence[Any] | None = None, col_order: Sequence[Any] | None = None, title: str = 'Binned marker heatmap', cmap: str = 'fyron_diverging_teal_orange', missing_color: str = '#F7F8FA', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `row_col` | no | `str` | `'feature'` | See signature. |
| `col_col` | no | `str` | `'sample'` | See signature. |
| `value_col` | no | `str` | `'bin'` | See signature. |
| `row_order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `col_order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Binned marker heatmap'` | See signature. |
| `cmap` | no | `str` | `'fyron_diverging_teal_orange'` | See signature. |
| `missing_color` | no | `str` | `'#F7F8FA'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_bland_altman`

Plot agreement between two measurements.

**Import path:** `fyron.ml.plots.plot_bland_altman`

```python
plot_bland_altman(method_a: ArrayLike, method_b: ArrayLike, *, title: str = 'Bland-Altman plot', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `method_a` | yes | `ArrayLike` |  | See signature. |
| `method_b` | yes | `ArrayLike` |  | See signature. |
| `title` | no | `str` | `'Bland-Altman plot'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_calibration_curve`

Plot observed event frequency against predicted probability.

**Import path:** `fyron.ml.plots.plot_calibration_curve`

```python
plot_calibration_curve(y_true: ArrayLikeInput, y_prob: ArrayLike, *, n_bins: int = 10, strategy: Literal['uniform', 'quantile'] = 'uniform', title: str = 'Calibration curve', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png', pos_label: Any | None = None) -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `ArrayLikeInput` |  | See signature. |
| `y_prob` | yes | `ArrayLike` |  | See signature. |
| `n_bins` | no | `int` | `10` | See signature. |
| `strategy` | no | `Literal['uniform', 'quantile']` | `'uniform'` | See signature. |
| `title` | no | `str` | `'Calibration curve'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_cohort_flow`

Plot cohort counts across inclusion/exclusion steps.

**Import path:** `fyron.ml.plots.plot_cohort_flow`

```python
plot_cohort_flow(data: Any, *, step_col: str = 'step', n_col: str = 'n', title: str = 'Cohort flow', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `step_col` | no | `str` | `'step'` | See signature. |
| `n_col` | no | `str` | `'n'` | See signature. |
| `title` | no | `str` | `'Cohort flow'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_confusion_matrix`

Plot a confusion matrix heatmap.

**Import path:** `fyron.ml.plots.plot_confusion_matrix`

```python
plot_confusion_matrix(y_true: ArrayLikeInput, y_pred: ArrayLikeInput, *, title: str = 'Confusion matrix', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png', pos_label: Any | None = None) -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `ArrayLikeInput` |  | See signature. |
| `y_pred` | yes | `ArrayLikeInput` |  | See signature. |
| `title` | no | `str` | `'Confusion matrix'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_correlation_heatmap`

Plot a numeric correlation heatmap and return the correlation table.

**Import path:** `fyron.ml.plots.plot_correlation_heatmap`

```python
plot_correlation_heatmap(data: Any, *, columns: Sequence[str] | None = None, method: Literal['pearson', 'spearman', 'kendall'] = 'spearman', group_col: str | None = None, title: str = 'Correlation heatmap', annotate: bool = True, annotate_significance: bool = False, p_adjust: str | None = 'fdr_bh', mask_upper: bool = False, cmap: str = 'fyron_diverging_blue_red', vmin: float = -1.0, vmax: float = 1.0, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> tuple[Figure, Axes, pd.DataFrame]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `columns` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `method` | no | `Literal['pearson', 'spearman', 'kendall']` | `'spearman'` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Correlation heatmap'` | See signature. |
| `annotate` | no | `bool` | `True` | See signature. |
| `annotate_significance` | no | `bool` | `False` | See signature. |
| `p_adjust` | no | `str  or  None` | `'fdr_bh'` | See signature. |
| `mask_upper` | no | `bool` | `False` | See signature. |
| `cmap` | no | `str` | `'fyron_diverging_blue_red'` | See signature. |
| `vmin` | no | `float` | `-1.0` | See signature. |
| `vmax` | no | `float` | `1.0` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`tuple[Figure, Axes, pd.DataFrame]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_cross_validated_roc`

Plot ROC curves from cross-validation fold predictions.

**Import path:** `fyron.ml.plots.plot_cross_validated_roc`

```python
plot_cross_validated_roc(data: Any, *, y_true_col: str = 'y_true', y_prob_col: str = 'y_prob', fold_col: str = 'fold', mean_grid_points: int = 101, palette: str | Sequence[str] | None = 'okabe_ito', title: str | None = None, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> TablePlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | DataFrame-like table with one row per out-of-fold prediction. |
| `y_true_col` | no | `str` | `'y_true'` | See signature. |
| `y_prob_col` | no | `str` | `'y_prob'` | See signature. |
| `fold_col` | no | `str` | `'fold'` | Columns containing the binary label, predicted probability, and fold ID. |
| `mean_grid_points` | no | `int` | `101` | Number of false-positive-rate grid points used for the mean ROC curve. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'okabe_ito'` | Named Fyron palette or explicit color sequence for fold curves. |
| `title` | no | `str  or  None` | `None` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`tuple` - ``(fig, ax, table)`` where ``table`` contains per-fold AUC values and mean/std summary rows.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_decision_curve`

Plot net benefit over decision thresholds.

**Import path:** `fyron.ml.plots.plot_decision_curve`

```python
plot_decision_curve(data: Any, *, threshold_col: str = 'threshold', model_col: str = 'net_benefit_model', treat_all_col: str = 'net_benefit_treat_all', treat_none_col: str = 'net_benefit_treat_none', title: str = 'Decision curve', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `threshold_col` | no | `str` | `'threshold'` | See signature. |
| `model_col` | no | `str` | `'net_benefit_model'` | See signature. |
| `treat_all_col` | no | `str` | `'net_benefit_treat_all'` | See signature. |
| `treat_none_col` | no | `str` | `'net_benefit_treat_none'` | See signature. |
| `title` | no | `str` | `'Decision curve'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_density`

Plot one or more smoothed clinical density curves.

**Import path:** `fyron.ml.plots.plot_density`

```python
plot_density(data: Any, *, x: str, hue: str | None = None, title: str = 'Density plot', xlabel: str | None = None, ylabel: str = 'Density', hue_order: Sequence[Any] | None = None, palette: Sequence[str] | None = None, fill: bool = True, alpha: float = 0.22, rug: bool = False, bandwidth: float | None = None, gridsize: int = 256, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Tabular data coercible to a DataFrame. |
| `x` | yes | `str` |  | Numeric variable to plot. |
| `hue` | no | `str  or  None` | `None` | Optional grouping column for separate density curves. |
| `title` | no | `str` | `'Density plot'` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `ylabel` | no | `str` | `'Density'` | See signature. |
| `hue_order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `palette` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `fill` | no | `bool` | `True` | See signature. |
| `alpha` | no | `float` | `0.22` | See signature. |
| `rug` | no | `bool` | `False` | See signature. |
| `bandwidth` | no | `float  or  None` | `None` | Optional Gaussian kernel bandwidth. When omitted, Silverman's rule is used. |
| `gridsize` | no | `int` | `256` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_dice_by_label`

Plot Dice scores by segmentation label.

**Import path:** `fyron.ml.plots.plot_dice_by_label`

```python
plot_dice_by_label(data: Any, *, label_col: str = 'label_name', dice_col: str = 'dice', title: str = 'Dice by label', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `label_col` | no | `str` | `'label_name'` | See signature. |
| `dice_col` | no | `str` | `'dice'` | See signature. |
| `title` | no | `str` | `'Dice by label'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_directional_ratio_rows`

Plot odds or hazard ratios with protective and hazardous direction bands.

**Import path:** `fyron.ml.plots.plot_directional_ratio_rows`

```python
plot_directional_ratio_rows(data: Any, *, feature_col: str = 'feature', ratio_col: str = 'ratio', lower_col: str | None = 'ci_lower', upper_col: str | None = 'ci_upper', p_col: str | None = None, group_col: str | None = None, n_col: str | None = None, ratio_label: str = 'Hazard / odds ratio', title: str = 'Directional ratio rows', protective_label: str = 'Protective', hazardous_label: str = 'Hazardous', reference: float = 1.0, log_scale: bool = True, xlim: tuple[float, float] | None = None, annotate: bool = True, estimate_label: str | None = None, ci_label: str = '95% CI', p_label: str = 'p value', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `feature_col` | no | `str` | `'feature'` | See signature. |
| `ratio_col` | no | `str` | `'ratio'` | See signature. |
| `lower_col` | no | `str  or  None` | `'ci_lower'` | See signature. |
| `upper_col` | no | `str  or  None` | `'ci_upper'` | See signature. |
| `p_col` | no | `str  or  None` | `None` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |
| `n_col` | no | `str  or  None` | `None` | See signature. |
| `ratio_label` | no | `str` | `'Hazard / odds ratio'` | See signature. |
| `title` | no | `str` | `'Directional ratio rows'` | See signature. |
| `protective_label` | no | `str` | `'Protective'` | See signature. |
| `hazardous_label` | no | `str` | `'Hazardous'` | See signature. |
| `reference` | no | `float` | `1.0` | See signature. |
| `log_scale` | no | `bool` | `True` | See signature. |
| `xlim` | no | `tuple[float, float]  or  None` | `None` | See signature. |
| `annotate` | no | `bool` | `True` | See signature. |
| `estimate_label` | no | `str  or  None` | `None` | See signature. |
| `ci_label` | no | `str` | `'95% CI'` | See signature. |
| `p_label` | no | `str` | `'p value'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_external_validation_metrics`

Plot external validation metrics from a dict or long table.

**Import path:** `fyron.ml.plots.plot_external_validation_metrics`

```python
plot_external_validation_metrics(data: Any, *, metric_col: str = 'metric', value_col: str = 'value', title: str = 'External validation', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `metric_col` | no | `str` | `'metric'` | See signature. |
| `value_col` | no | `str` | `'value'` | See signature. |
| `title` | no | `str` | `'External validation'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_feature_importance`

Plot top-N features from a feature-importance DataFrame.

**Import path:** `fyron.ml.plots.plot_feature_importance`

```python
plot_feature_importance(importance_df: Any, *, top_n: int = 20, title: str = 'Feature importance', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `importance_df` | yes | `Any` |  | See signature. |
| `top_n` | no | `int` | `20` | See signature. |
| `title` | no | `str` | `'Feature importance'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_feature_selection_summary`

Plot selected versus rejected features from a selection summary table.

**Import path:** `fyron.ml.plots.plot_feature_selection_summary`

```python
plot_feature_selection_summary(data: Any, *, feature_col: str = 'feature', selected_col: str = 'selected', score_col: str | None = None, title: str = 'Feature selection summary', top_n: int = 25, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `feature_col` | no | `str` | `'feature'` | See signature. |
| `selected_col` | no | `str` | `'selected'` | See signature. |
| `score_col` | no | `str  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Feature selection summary'` | See signature. |
| `top_n` | no | `int` | `25` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_filled_kde`

Plot filled two-dimensional Gaussian KDE contours.

**Import path:** `fyron.ml.plots.plot_filled_kde`

```python
plot_filled_kde(data: Any, *, x: str, y: str, hue: str | None = None, title: str = 'Filled KDE plot', xlabel: str | None = None, ylabel: str | None = None, hue_order: Sequence[Any] | None = None, palette: str | Sequence[str] | None = None, fill: bool = True, alpha: float = 0.36, levels: int = 8, thresh: float = 0.05, bandwidth: float | tuple[float, float] | None = None, gridsize: int = 96, show_points: bool = False, point_size: float = 10, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Tabular data coercible to a DataFrame. |
| `x` | yes | `str` |  | Numeric column plotted on the horizontal axis. |
| `y` | yes | `str` |  | Numeric column plotted on the vertical axis. |
| `hue` | no | `str  or  None` | `None` | Optional categorical column for separate filled KDE contours. |
| `title` | no | `str` | `'Filled KDE plot'` | Plot title. |
| `xlabel` | no | `str  or  None` | `None` | Optional x-axis label. Defaults to a title-cased version of ``x``. |
| `ylabel` | no | `str  or  None` | `None` | Optional y-axis label. Defaults to a title-cased version of ``y``. |
| `hue_order` | no | `Sequence[Any]  or  None` | `None` | Optional explicit order for hue groups. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `None` | Named Fyron palette or explicit color sequence. |
| `fill` | no | `bool` | `True` | If True, draw filled contours. If False, draw contour lines only. |
| `alpha` | no | `float` | `0.36` | Fill transparency. |
| `levels` | no | `int` | `8` | Number of contour levels to draw. |
| `thresh` | no | `float` | `0.05` | Relative density threshold between 0 and 1 for the first contour. |
| `bandwidth` | no | `float  or  tuple[float, float]  or  None` | `None` | Optional shared bandwidth or ``(x_bandwidth, y_bandwidth)`` tuple. When omitted, a Scott-style rule is used for each axis. |
| `gridsize` | no | `int` | `96` | Number of grid points per axis used to evaluate the density. |
| `show_points` | no | `bool` | `False` | If True, overlay source points. |
| `point_size` | no | `float` | `10` | Marker size used when ``show_points`` is True. |
| `ax` | no | `Axes  or  None` | `None` | Optional Matplotlib axes to draw into. |
| `save_path` | no | `str  or  Path  or  None` | `None` | Optional path for saving the figure. |
| `fmt` | no | `str` | `'png'` | Output format used when ``save_path`` is provided. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_forest_estimates`

Plot estimates with confidence intervals in a compact forest layout.

**Import path:** `fyron.ml.plots.plot_forest_estimates`

```python
plot_forest_estimates(data: Any, *, label_col: str = 'label', estimate_col: str = 'estimate', lower_col: str = 'ci_lower', upper_col: str = 'ci_upper', p_col: str | None = None, p_adjust_col: str | None = None, n_col: str | None = None, group_col: str | None = None, table_columns: bool = False, reference: float = 1.0, log_scale: bool = True, title: str = 'Forest plot', xlabel: str = 'Hazard ratio', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `label_col` | no | `str` | `'label'` | See signature. |
| `estimate_col` | no | `str` | `'estimate'` | See signature. |
| `lower_col` | no | `str` | `'ci_lower'` | See signature. |
| `upper_col` | no | `str` | `'ci_upper'` | See signature. |
| `p_col` | no | `str  or  None` | `None` | See signature. |
| `p_adjust_col` | no | `str  or  None` | `None` | See signature. |
| `n_col` | no | `str  or  None` | `None` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |
| `table_columns` | no | `bool` | `False` | See signature. |
| `reference` | no | `float` | `1.0` | See signature. |
| `log_scale` | no | `bool` | `True` | See signature. |
| `title` | no | `str` | `'Forest plot'` | See signature. |
| `xlabel` | no | `str` | `'Hazard ratio'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_grouped_bar_with_significance`

Plot grouped bars with statistical significance brackets.

**Import path:** `fyron.ml.plots.plot_grouped_bar_with_significance`

```python
plot_grouped_bar_with_significance(data: Any, *, x: str, y: str, hue: str | None = None, order: Sequence[Any] | None = None, hue_order: Sequence[Any] | None = None, estimator: Literal['mean', 'median'] = 'mean', error: Literal['sem', 'sd', 'ci', 'none'] = 'sem', ci: float = 0.95, test: Literal['auto', 'mannwhitney', 'ttest', 'kruskal'] = 'auto', comparisons: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]] | None = None, p_thresholds: Sequence[tuple[float, str]] = ((0.001, '***'), (0.01, '**'), (0.05, '*')), title: str = 'Grouped outcome summary', ylabel: str | None = None, xlabel: str | None = None, palette: Sequence[str] | None = None, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> TablePlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `x` | yes | `str` |  | See signature. |
| `y` | yes | `str` |  | See signature. |
| `hue` | no | `str  or  None` | `None` | See signature. |
| `order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `hue_order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `estimator` | no | `Literal['mean', 'median']` | `'mean'` | See signature. |
| `error` | no | `Literal['sem', 'sd', 'ci', 'none']` | `'sem'` | See signature. |
| `ci` | no | `float` | `0.95` | See signature. |
| `test` | no | `Literal['auto', 'mannwhitney', 'ttest', 'kruskal']` | `'auto'` | See signature. |
| `comparisons` | no | `Sequence[tuple[Any, Any]  or  tuple[tuple[Any, Any], tuple[Any, Any]]]  or  None` | `None` | See signature. |
| `p_thresholds` | no | `Sequence[tuple[float, str]]` | `((0.001, '***'), (0.01, '**'), (0.05, '*'))` | See signature. |
| `title` | no | `str` | `'Grouped outcome summary'` | See signature. |
| `ylabel` | no | `str  or  None` | `None` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `palette` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`TablePlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_grouped_boxplot`

Plot a clinical grouped boxplot with optional hue and jittered patients.

**Import path:** `fyron.ml.plots.plot_grouped_boxplot`

```python
plot_grouped_boxplot(data: Any, *, x: str, y: str, hue: str | None = None, title: str = 'Grouped boxplot', xlabel: str | None = None, ylabel: str | None = None, order: Sequence[Any] | None = None, hue_order: Sequence[Any] | None = None, palette: Sequence[str] | None = None, show_points: bool = True, point_alpha: float = 0.55, random_state: int = 42, comparisons: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]] | None = None, stat_test: StatTestName = 'mannwhitney', p_adjust: str = 'none', annotation_format: AnnotationFormat = 'star', hide_ns: bool = False, return_stats: bool = False, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn | TablePlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Tabular data coercible to a DataFrame. |
| `x` | yes | `str` |  | See signature. |
| `y` | yes | `str` |  | Categorical grouping column and numeric value column. |
| `hue` | no | `str  or  None` | `None` | Optional second grouping column, for example sex, treatment, cohort, or event status. |
| `title` | no | `str` | `'Grouped boxplot'` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `ylabel` | no | `str  or  None` | `None` | See signature. |
| `order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `hue_order` | no | `Sequence[Any]  or  None` | `None` | Optional display order for the x groups and hue groups. |
| `palette` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `show_points` | no | `bool` | `True` | See signature. |
| `point_alpha` | no | `float` | `0.55` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `comparisons` | no | `Sequence[tuple[Any, Any]  or  tuple[tuple[Any, Any], tuple[Any, Any]]]  or  None` | `None` | See signature. |
| `stat_test` | no | `StatTestName` | `'mannwhitney'` | See signature. |
| `p_adjust` | no | `str` | `'none'` | See signature. |
| `annotation_format` | no | `AnnotationFormat` | `'star'` | See signature. |
| `hide_ns` | no | `bool` | `False` | See signature. |
| `return_stats` | no | `bool` | `False` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn | TablePlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_grouped_correlation_heatmaps`

Plot one correlation heatmap per group and return a long correlation table.

**Import path:** `fyron.ml.plots.plot_grouped_correlation_heatmaps`

```python
plot_grouped_correlation_heatmaps(data: Any, *, group_col: str, columns: Sequence[str] | None = None, method: Literal['pearson', 'spearman', 'kendall'] = 'spearman', title: str = 'Grouped correlation heatmaps', annotate: bool = True, annotate_significance: bool = False, p_adjust: str | None = 'fdr_bh', mask_upper: bool = False, cmap: str = 'fyron_diverging_blue_red', vmin: float = -1.0, vmax: float = 1.0, save_path: str | Path | None = None, fmt: str = 'png') -> tuple[Figure, np.ndarray, pd.DataFrame]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `group_col` | yes | `str` |  | See signature. |
| `columns` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `method` | no | `Literal['pearson', 'spearman', 'kendall']` | `'spearman'` | See signature. |
| `title` | no | `str` | `'Grouped correlation heatmaps'` | See signature. |
| `annotate` | no | `bool` | `True` | See signature. |
| `annotate_significance` | no | `bool` | `False` | See signature. |
| `p_adjust` | no | `str  or  None` | `'fdr_bh'` | See signature. |
| `mask_upper` | no | `bool` | `False` | See signature. |
| `cmap` | no | `str` | `'fyron_diverging_blue_red'` | See signature. |
| `vmin` | no | `float` | `-1.0` | See signature. |
| `vmax` | no | `float` | `1.0` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`tuple[Figure, np.ndarray, pd.DataFrame]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_hazard_ratios`

Plot Cox hazard ratios from a Fyron Cox result or lifelines fitter.

**Import path:** `fyron.ml.plots.plot_hazard_ratios`

```python
plot_hazard_ratios(cox_result: Any, *, label_col: str = 'label', title: str = 'Hazard ratios', xlabel: str = 'Hazard ratio', table_columns: bool = True, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cox_result` | yes | `Any` |  | See signature. |
| `label_col` | no | `str` | `'label'` | See signature. |
| `title` | no | `str` | `'Hazard ratios'` | See signature. |
| `xlabel` | no | `str` | `'Hazard ratio'` | See signature. |
| `table_columns` | no | `bool` | `True` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_histogram`

Plot manuscript-friendly histograms with optional hue/group strata.

**Import path:** `fyron.ml.plots.plot_histogram`

```python
plot_histogram(data: Any, *, x: str, hue: str | None = None, group: str | None = None, bins: int | str | Sequence[float] = 'auto', stat: Literal['count', 'density', 'percent'] = 'count', multiple: Literal['layer', 'stack', 'dodge'] = 'layer', title: str = 'Histogram', xlabel: str | None = None, ylabel: str | None = None, hue_order: Sequence[Any] | None = None, palette: Sequence[str] | None = None, alpha: float = 0.55, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `x` | yes | `str` |  | See signature. |
| `hue` | no | `str  or  None` | `None` | See signature. |
| `group` | no | `str  or  None` | `None` | See signature. |
| `bins` | no | `int  or  str  or  Sequence[float]` | `'auto'` | See signature. |
| `stat` | no | `Literal['count', 'density', 'percent']` | `'count'` | See signature. |
| `multiple` | no | `Literal['layer', 'stack', 'dodge']` | `'layer'` | See signature. |
| `title` | no | `str` | `'Histogram'` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `ylabel` | no | `str  or  None` | `None` | See signature. |
| `hue_order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `palette` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `alpha` | no | `float` | `0.55` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_kaplan_meier`

Clinical plotting alias for Kaplan-Meier curves.

**Import path:** `fyron.ml.plots.plot_kaplan_meier`

```python
plot_kaplan_meier(*args: Any, **kwargs: Any)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `args` | yes | `Any` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

See the function signature and module guide.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_likert_scale`

Plot a diverging Likert scale summary.

**Import path:** `fyron.ml.plots.plot_likert_scale`

```python
plot_likert_scale(data: Any, *, item_col: str = 'item', response_col: str = 'response', count_col: str | None = None, order: Sequence[Any] | None = None, response_order: Sequence[Any] | None = None, neutral_values: Sequence[Any] | None = None, normalize: bool = True, palette: str | Sequence[str] | None = 'okabe_ito', title: str | None = None, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> TablePlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Long table with one row per response or one row per response count. |
| `item_col` | no | `str` | `'item'` | See signature. |
| `response_col` | no | `str` | `'response'` | Columns containing survey item names and ordered Likert responses. |
| `count_col` | no | `str  or  None` | `None` | Optional count column. If omitted, rows are counted. |
| `order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `response_order` | no | `Sequence[Any]  or  None` | `None` | Explicit item and response order for stable manuscript figures. |
| `neutral_values` | no | `Sequence[Any]  or  None` | `None` | Responses that should be centered around zero. If omitted and the response order has odd length, the middle response is treated as neutral. |
| `normalize` | no | `bool` | `True` | If True, show percentages per item. If False, show counts. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'okabe_ito'` | See signature. |
| `title` | no | `str  or  None` | `None` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`tuple` - ``(fig, ax, table)`` where ``table`` contains counts, percentages, and the assigned negative/neutral/positive side for each response.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_metric_bars`

Plot model metrics with grouped patterned bars.

**Import path:** `fyron.ml.plots.plot_metric_bars`

```python
plot_metric_bars(metrics: Mapping[str, Mapping[str, float]] | pd.DataFrame, *, metrics_to_plot: Sequence[str] | None = None, model_col: str = 'model', title: str = 'Model metrics', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `metrics` | yes | `Mapping[str, Mapping[str, float]]  or  pd.DataFrame` |  | See signature. |
| `metrics_to_plot` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `model_col` | no | `str` | `'model'` | See signature. |
| `title` | no | `str` | `'Model metrics'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_missingness_bar`

Plot missingness percentages from a preprocessing summary table.

**Import path:** `fyron.ml.plots.plot_missingness_bar`

```python
plot_missingness_bar(data: Any, *, column_col: str = 'column', missing_col: str = 'missing_percent', group_col: str | None = None, title: str = 'Missingness', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `column_col` | no | `str` | `'column'` | See signature. |
| `missing_col` | no | `str` | `'missing_percent'` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Missingness'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_patterned_bar`

Plot grouped bars with hatch patterns for grayscale-safe figures.

**Import path:** `fyron.ml.plots.plot_patterned_bar`

```python
plot_patterned_bar(data: Any, *, x: str, y: str, group: str | None = None, error: str | None = None, title: str = 'Bar plot', xlabel: str | None = None, ylabel: str | None = None, orientation: Orientation = 'vertical', palette: Sequence[str] | None = None, hatches: Sequence[str] | None = None, annotate: bool = False, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Tabular data coercible to a DataFrame. |
| `x` | yes | `str` |  | See signature. |
| `y` | yes | `str` |  | Category and value columns. |
| `group` | no | `str  or  None` | `None` | Optional grouping column. Each group receives a distinct color/hatch. |
| `error` | no | `str  or  None` | `None` | Optional symmetric error-bar column. |
| `title` | no | `str` | `'Bar plot'` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `ylabel` | no | `str  or  None` | `None` | See signature. |
| `orientation` | no | `Orientation` | `'vertical'` | See signature. |
| `palette` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `hatches` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `annotate` | no | `bool` | `False` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_precision_recall_curve`

Plot a precision-recall curve for binary classification.

**Import path:** `fyron.ml.plots.plot_precision_recall_curve`

```python
plot_precision_recall_curve(y_true: ArrayLikeInput, y_prob: ArrayLike, *, title: str = 'Precision-recall curve', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png', pos_label: Any | None = None) -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `ArrayLikeInput` |  | See signature. |
| `y_prob` | yes | `ArrayLike` |  | See signature. |
| `title` | no | `str` | `'Precision-recall curve'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_qq`

Plot configurable normal Q-Q diagnostics.

**Import path:** `fyron.ml.plots.plot_qq`

```python
plot_qq(data: Any, *, value_col: str | None = None, columns: Sequence[str] | None = None, group_col: str | None = None, theoretical: Literal['normal'] = 'normal', line: Literal['quartile', 'fit', 'identity'] | None = 'quartile', facet: bool = False, title: str = 'Q-Q plot', xlabel: str = 'Theoretical quantiles', ylabel: str = 'Observed quantiles', palette: str | Sequence[str] | None = 'okabe_ito', point_size: float = 24.0, alpha: float = 0.82, marker: str = 'o', line_color: str = '#1F2933', line_width: float = 1.35, sharex: bool = True, sharey: bool = True, figsize: tuple[float, float] | None = None, legend: bool = True, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> tuple[Figure, np.ndarray, pd.DataFrame]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Vector-like values or a table containing numeric columns. |
| `value_col` | no | `str  or  None` | `None` | Single numeric DataFrame column to plot. |
| `columns` | no | `Sequence[str]  or  None` | `None` | Optional list of numeric DataFrame columns to plot. |
| `group_col` | no | `str  or  None` | `None` | Optional grouping column. Groups are overlaid by default or faceted when ``facet=True``. |
| `theoretical` | no | `Literal['normal']` | `'normal'` | Theoretical distribution. Version 1 supports ``"normal"``. |
| `line` | no | `Literal['quartile', 'fit', 'identity']  or  None` | `'quartile'` | Reference line mode: ``"quartile"``, ``"fit"``, ``"identity"``, or ``None``. |
| `facet` | no | `bool` | `False` | Draw one panel per variable/group series instead of overlaying series. |
| `title` | no | `str` | `'Q-Q plot'` | Figure title. |
| `xlabel` | no | `str` | `'Theoretical quantiles'` | X-axis label. |
| `ylabel` | no | `str` | `'Observed quantiles'` | Y-axis label. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'okabe_ito'` | Fyron palette name or explicit color sequence. |
| `point_size` | no | `float` | `24.0` | Scatter point size. |
| `alpha` | no | `float` | `0.82` | Scatter point transparency. |
| `marker` | no | `str` | `'o'` | Matplotlib marker used for points. |
| `line_color` | no | `str` | `'#1F2933'` | Reference line color. |
| `line_width` | no | `float` | `1.35` | Reference line width. |
| `sharex` | no | `bool` | `True` | Whether faceted panels share the x-axis. |
| `sharey` | no | `bool` | `True` | Whether faceted panels share the y-axis. |
| `figsize` | no | `tuple[float, float]  or  None` | `None` | Optional figure size. |
| `legend` | no | `bool` | `True` | Whether to show a legend for overlaid series. |
| `ax` | no | `Axes  or  None` | `None` | Optional axis for a single overlaid panel. |
| `save_path` | no | `str  or  Path  or  None` | `None` | Optional path for saving the figure. |
| `fmt` | no | `str` | `'png'` | Output format used with ``save_path``. |

### Returns

`tuple[Figure, np.ndarray, pandas.DataFrame]` - Matplotlib figure, two-dimensional axes array, and long-form Q-Q table.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_raincloud`

Plot half-violin distributions with box summaries and patient-level points.

**Import path:** `fyron.ml.plots.plot_raincloud`

```python
plot_raincloud(data: Any, *, x: str = 'group', y: str = 'value', order: Sequence[Any] | None = None, title: str = 'Raincloud plot', ylabel: str | None = None, palette: str | Sequence[str] | None = 'bf_vibrant_muted', random_state: int = 7, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `x` | no | `str` | `'group'` | See signature. |
| `y` | no | `str` | `'value'` | See signature. |
| `order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Raincloud plot'` | See signature. |
| `ylabel` | no | `str  or  None` | `None` | See signature. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'bf_vibrant_muted'` | See signature. |
| `random_state` | no | `int` | `7` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_reference_band_grid`

Plot faceted clinical reference bands with an optional trend line.

**Import path:** `fyron.ml.plots.plot_reference_band_grid`

```python
plot_reference_band_grid(data: Any, *, x: str, lower_col: str = 'lower', upper_col: str = 'upper', band_col: str = 'band', col: str = 'feature', row: str | None = None, line_df: Any | None = None, line_y: str | None = None, feature_order: Sequence[Any] | None = None, row_order: Sequence[Any] | None = None, band_preset: Literal['sd', 'survival', 'risk', 'percentile'] | None = None, band_order: Sequence[Any] | None = None, band_colors: Mapping[Any, str] | Sequence[str] | None = None, title: str = 'Reference band grid', xlabel: str | None = None, ylabel: str | None = None, sharex: bool = True, sharey: bool | Literal['row', 'col'] = False, legend: bool = True, figsize: tuple[float, float] | None = None, line_color: str = '#1F2933', line_width: float = 1.35, save_path: str | Path | None = None, fmt: str = 'png') -> tuple[Figure, np.ndarray]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Long-form table with one row per x value, reference band, and facet. |
| `x` | yes | `str` |  | Numeric x-axis column, such as age, biological age, follow-up month, or dose. |
| `lower_col` | no | `str` | `'lower'` | Numeric lower bound for each reference band interval. |
| `upper_col` | no | `str` | `'upper'` | Numeric upper bound for each reference band interval. |
| `band_col` | no | `str` | `'band'` | Column containing the reference band label. |
| `col` | no | `str` | `'feature'` | Facet column shown across plot columns, usually a feature or measurement name. |
| `row` | no | `str  or  None` | `None` | Optional facet column shown across plot rows, such as sex, cohort, scanner, or modality. |
| `line_df` | no | `Any  or  None` | `None` | Optional long-form table with the same x and facet columns for an overlaid trend line. |
| `line_y` | no | `str  or  None` | `None` | Numeric y column in ``line_df``. Required when ``line_df`` is provided. |
| `feature_order` | no | `Sequence[Any]  or  None` | `None` | Optional explicit order for column facets. |
| `row_order` | no | `Sequence[Any]  or  None` | `None` | Optional explicit order for row facets. |
| `band_preset` | no | `Literal['sd', 'survival', 'risk', 'percentile']  or  None` | `None` | Optional named preset for common band labels and colors: ``"sd"``, ``"survival"``, ``"risk"``, or ``"percentile"``. |
| `band_order` | no | `Sequence[Any]  or  None` | `None` | Optional explicit order for drawing bands and the legend. |
| `band_colors` | no | `Mapping[Any, str]  or  Sequence[str]  or  None` | `None` | Optional mapping from band label to color, or a color sequence matching ``band_order``. |
| `title` | no | `str` | `'Reference band grid'` | Figure title. |
| `xlabel` | no | `str  or  None` | `None` | X-axis label. |
| `ylabel` | no | `str  or  None` | `None` | Y-axis label. When ``row`` is provided, the row label is combined with the y-axis label. |
| `sharex` | no | `bool` | `True` | Whether column facets share the x-axis. |
| `sharey` | no | `bool  or  Literal['row', 'col']` | `False` | Matplotlib y-axis sharing control for facets. |
| `legend` | no | `bool` | `True` | Whether to draw a shared band legend below the grid. |
| `figsize` | no | `tuple[float, float]  or  None` | `None` | Optional figure size in inches. |
| `line_color` | no | `str` | `'#1F2933'` | Color used for the optional trend line. |
| `line_width` | no | `float` | `1.35` | Width used for the optional trend line. |
| `save_path` | no | `str  or  Path  or  None` | `None` | Optional path for saving the figure. |
| `fmt` | no | `str` | `'png'` | Output format used with ``save_path``. |

### Returns

`tuple[Figure, np.ndarray]` - Matplotlib figure and two-dimensional array of axes.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_risk_score_distribution`

Plot risk scores as a BOARISK-style violin/jitter distribution.

**Import path:** `fyron.ml.plots.plot_risk_score_distribution`

```python
plot_risk_score_distribution(data: Any, *, risk_col: str = 'risk_score', event_col: str | None = None, event_labels: Mapping[Any, str] | Sequence[str] | None = None, title: str = 'Risk score distribution', ylabel: str | None = None, jitter: bool = True, violin: bool = True, palette: Sequence[str] | None = None, random_state: int = 42, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `risk_col` | no | `str` | `'risk_score'` | See signature. |
| `event_col` | no | `str  or  None` | `None` | See signature. |
| `event_labels` | no | `Mapping[Any, str]  or  Sequence[str]  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Risk score distribution'` | See signature. |
| `ylabel` | no | `str  or  None` | `None` | See signature. |
| `jitter` | no | `bool` | `True` | See signature. |
| `violin` | no | `bool` | `True` | See signature. |
| `palette` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_roc_curve`

Plot an ROC curve and return the figure and axis.

**Import path:** `fyron.ml.plots.plot_roc_curve`

```python
plot_roc_curve(y_true: ArrayLikeInput, y_prob: ArrayLike, *, title: str = 'ROC curve', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png', pos_label: Any | None = None) -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `ArrayLikeInput` |  | See signature. |
| `y_prob` | yes | `ArrayLike` |  | See signature. |
| `title` | no | `str` | `'ROC curve'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_segmentation_overlay_grid`

Plot CT/image slices with a mask overlay.

**Import path:** `fyron.ml.plots.plot_segmentation_overlay_grid`

```python
plot_segmentation_overlay_grid(image: Any, mask: Any, *, slice_indices: Sequence[int] | None = None, label: int | None = None, alpha: float = 0.35, title: str = 'Segmentation overlay', save_path: str | Path | None = None, fmt: str = 'png') -> tuple[Figure, np.ndarray]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `image` | yes | `Any` |  | See signature. |
| `mask` | yes | `Any` |  | See signature. |
| `slice_indices` | no | `Sequence[int]  or  None` | `None` | See signature. |
| `label` | no | `int  or  None` | `None` | See signature. |
| `alpha` | no | `float` | `0.35` | See signature. |
| `title` | no | `str` | `'Segmentation overlay'` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`tuple[Figure, np.ndarray]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_signed_feature_weights`

Plot signed coefficients or feature weights with BOARISK hatches.

**Import path:** `fyron.ml.plots.plot_signed_feature_weights`

```python
plot_signed_feature_weights(data: Any, *, feature_col: str = 'feature', weight_col: str = 'coef', top_n: int = 20, title: str = 'Signed feature weights', xlabel: str = 'Model coefficient', positive_label: str = 'Higher risk', negative_label: str = 'Lower risk', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `feature_col` | no | `str` | `'feature'` | See signature. |
| `weight_col` | no | `str` | `'coef'` | See signature. |
| `top_n` | no | `int` | `20` | See signature. |
| `title` | no | `str` | `'Signed feature weights'` | See signature. |
| `xlabel` | no | `str` | `'Model coefficient'` | See signature. |
| `positive_label` | no | `str` | `'Higher risk'` | See signature. |
| `negative_label` | no | `str` | `'Lower risk'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_significance_bars`

Plot p-values as ``-log10(p)`` bars and return the computed table.

**Import path:** `fyron.ml.plots.plot_significance_bars`

```python
plot_significance_bars(data: Any, *, label_col: str = 'label', p_col: str = 'p_value', threshold: float = 0.05, title: str = 'Statistical significance', xlabel: str = '-log10(p)', annotate: bool = True, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> TablePlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `label_col` | no | `str` | `'label'` | See signature. |
| `p_col` | no | `str` | `'p_value'` | See signature. |
| `threshold` | no | `float` | `0.05` | See signature. |
| `title` | no | `str` | `'Statistical significance'` | See signature. |
| `xlabel` | no | `str` | `'-log10(p)'` | See signature. |
| `annotate` | no | `bool` | `True` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`TablePlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_stability_selection`

Plot feature-selection frequencies from stability selection.

**Import path:** `fyron.ml.plots.plot_stability_selection`

```python
plot_stability_selection(data: Any, *, feature_col: str = 'feature', frequency_col: str = 'selection_frequency', threshold: float = 0.6, title: str = 'Stability selection', top_n: int = 25, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `feature_col` | no | `str` | `'feature'` | See signature. |
| `frequency_col` | no | `str` | `'selection_frequency'` | See signature. |
| `threshold` | no | `float` | `0.6` | See signature. |
| `title` | no | `str` | `'Stability selection'` | See signature. |
| `top_n` | no | `int` | `25` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_survival_calibration`

Plot fixed-horizon observed versus predicted survival/event risk.

**Import path:** `fyron.ml.plots.plot_survival_calibration`

```python
plot_survival_calibration(calibration_table: Any, *, observed_col: str = 'observed', predicted_col: str = 'predicted', title: str = 'Survival calibration', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `calibration_table` | yes | `Any` |  | See signature. |
| `observed_col` | no | `str` | `'observed'` | See signature. |
| `predicted_col` | no | `str` | `'predicted'` | See signature. |
| `title` | no | `str` | `'Survival calibration'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_swarmplot`

Plot patient-level values with jitter/dodge and optional statistics.

**Import path:** `fyron.ml.plots.plot_swarmplot`

```python
plot_swarmplot(data: Any, *, x: str, y: str, hue: str | None = None, order: Sequence[Any] | None = None, hue_order: Sequence[Any] | None = None, dodge: bool = True, title: str = 'Swarm plot', xlabel: str | None = None, ylabel: str | None = None, palette: Sequence[str] | None = None, point_size: float = 24, point_alpha: float = 0.72, random_state: int = 42, comparisons: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]] | None = None, stat_test: StatTestName = 'mannwhitney', p_adjust: str = 'none', annotation_format: AnnotationFormat = 'star', hide_ns: bool = False, return_stats: bool = False, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn | TablePlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `x` | yes | `str` |  | See signature. |
| `y` | yes | `str` |  | See signature. |
| `hue` | no | `str  or  None` | `None` | See signature. |
| `order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `hue_order` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `dodge` | no | `bool` | `True` | See signature. |
| `title` | no | `str` | `'Swarm plot'` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `ylabel` | no | `str  or  None` | `None` | See signature. |
| `palette` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `point_size` | no | `float` | `24` | See signature. |
| `point_alpha` | no | `float` | `0.72` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `comparisons` | no | `Sequence[tuple[Any, Any]  or  tuple[tuple[Any, Any], tuple[Any, Any]]]  or  None` | `None` | See signature. |
| `stat_test` | no | `StatTestName` | `'mannwhitney'` | See signature. |
| `p_adjust` | no | `str` | `'none'` | See signature. |
| `annotation_format` | no | `AnnotationFormat` | `'star'` | See signature. |
| `hide_ns` | no | `bool` | `False` | See signature. |
| `return_stats` | no | `bool` | `False` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn | TablePlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_swimmer`

Plot patient-level duration bars with optional event markers.

**Import path:** `fyron.ml.plots.plot_swimmer`

```python
plot_swimmer(data: Any, *, patient_col: str = 'patient', start_col: str = 'start', end_col: str = 'end', group_col: str | None = None, event_time_col: str | None = 'event_time', event_col: str | None = 'event', title: str = 'Swimmer plot', xlabel: str = 'Time', palette: str | Sequence[str] | None = 'bf_vibrant_muted', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `patient_col` | no | `str` | `'patient'` | See signature. |
| `start_col` | no | `str` | `'start'` | See signature. |
| `end_col` | no | `str` | `'end'` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |
| `event_time_col` | no | `str  or  None` | `'event_time'` | See signature. |
| `event_col` | no | `str  or  None` | `'event'` | See signature. |
| `title` | no | `str` | `'Swimmer plot'` | See signature. |
| `xlabel` | no | `str` | `'Time'` | See signature. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'bf_vibrant_muted'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_table_one_summary`

Plot Table 1 p-values as a compact overview.

**Import path:** `fyron.ml.plots.plot_table_one_summary`

```python
plot_table_one_summary(data: Any, *, variable_col: str = 'variable', p_col: str = 'p_value', title: str = 'Table 1 summary', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `variable_col` | no | `str` | `'variable'` | See signature. |
| `p_col` | no | `str` | `'p_value'` | See signature. |
| `title` | no | `str` | `'Table 1 summary'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_time_dependent_auc`

Plot time-dependent AUC values from a precomputed table.

**Import path:** `fyron.ml.plots.plot_time_dependent_auc`

```python
plot_time_dependent_auc(data: Any, *, time_col: str = 'time', auc_col: str = 'auc', title: str = 'Time-dependent AUC', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `time_col` | no | `str` | `'time'` | See signature. |
| `auc_col` | no | `str` | `'auc'` | See signature. |
| `title` | no | `str` | `'Time-dependent AUC'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_volcano`

Plot feature effects against statistical significance.

**Import path:** `fyron.ml.plots.plot_volcano`

```python
plot_volcano(data: Any, *, feature_col: str = 'feature', effect_col: str = 'log2_fold_change', p_col: str = 'p_value', group_col: str | None = None, p_threshold: float = 0.05, effect_threshold: float = 1.0, top_n_labels: int = 8, title: str = 'Volcano plot', xlabel: str | None = None, ylabel: str = '-log10(p)', palette: str | Sequence[str] | None = 'bf_vibrant_muted', ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | See signature. |
| `feature_col` | no | `str` | `'feature'` | See signature. |
| `effect_col` | no | `str` | `'log2_fold_change'` | See signature. |
| `p_col` | no | `str` | `'p_value'` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |
| `p_threshold` | no | `float` | `0.05` | See signature. |
| `effect_threshold` | no | `float` | `1.0` | See signature. |
| `top_n_labels` | no | `int` | `8` | See signature. |
| `title` | no | `str` | `'Volcano plot'` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `ylabel` | no | `str` | `'-log10(p)'` | See signature. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'bf_vibrant_muted'` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_waffle`

Plot a waffle chart for cohort composition or endpoint mix.

**Import path:** `fyron.ml.plots.plot_waffle`

```python
plot_waffle(data: Any, *, category_col: str = 'category', value_col: str = 'value', total: int = 100, rows: int = 10, palette: str | Sequence[str] | None = 'bf_vibrant_muted', title: str | None = None, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> TablePlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Table with category labels and non-negative values. |
| `category_col` | no | `str` | `'category'` | See signature. |
| `value_col` | no | `str` | `'value'` | Columns containing categories and values to allocate into waffle cells. |
| `total` | no | `int` | `100` | Number of cells in the waffle chart. |
| `rows` | no | `int` | `10` | Number of waffle rows. Columns are derived from ``total`` and ``rows``. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `'bf_vibrant_muted'` | See signature. |
| `title` | no | `str  or  None` | `None` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`tuple` - ``(fig, ax, table)`` where ``table`` contains category proportions, allocated cell counts, and source values.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.plot_waterfall`

Plot ordered patient-level changes or response scores.

**Import path:** `fyron.ml.plots.plot_waterfall`

```python
plot_waterfall(values: ArrayLike, *, labels: Sequence[Any] | None = None, title: str = 'Waterfall plot', ylabel: str = 'Change', threshold: float | None = None, ax: Axes | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `values` | yes | `ArrayLike` |  | See signature. |
| `labels` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `title` | no | `str` | `'Waterfall plot'` | See signature. |
| `ylabel` | no | `str` | `'Change'` | See signature. |
| `threshold` | no | `float  or  None` | `None` | See signature. |
| `ax` | no | `Axes  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.plots.stat_test_pairs`

Run pairwise statistical tests for plot annotations.

**Import path:** `fyron.ml.plots.stat_test_pairs`

```python
stat_test_pairs(data: Any, *, x: str, y: str, pairs: Sequence[tuple[Any, Any] | tuple[tuple[Any, Any], tuple[Any, Any]]], hue: str | None = None, test: StatTestName = 'mannwhitney', p_adjust: str = 'none', alpha: float = 0.05, p_values: Sequence[float] | Mapping[tuple[Any, Any], float] | pd.DataFrame | None = None, label_col: str = 'label', p_col: str = 'p_value', text_format: AnnotationFormat = 'star', hide_ns: bool = False) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `data` | yes | `Any` |  | Tabular data coercible to a DataFrame. |
| `x` | yes | `str` |  | See signature. |
| `y` | yes | `str` |  | Categorical grouping column and numeric value column. |
| `pairs` | yes | `Sequence[tuple[Any, Any]  or  tuple[tuple[Any, Any], tuple[Any, Any]]]` |  | Comparisons. Without ``hue`` use ``("A", "B")``. With ``hue`` use ``(("A", "F"), ("A", "M"))`` keys. |
| `hue` | no | `str  or  None` | `None` | Optional second grouping column. |
| `test` | no | `StatTestName` | `'mannwhitney'` | Statistical test name. |
| `p_adjust` | no | `str` | `'none'` | Multiple-testing correction method accepted by :func:`fyron.statistics.p_value_correction_table`. |
| `alpha` | no | `float` | `0.05` | See signature. |
| `p_values` | no | `Sequence[float]  or  Mapping[tuple[Any, Any], float]  or  pd.DataFrame  or  None` | `None` | Optional custom p-values. When provided, no statistical test is run. |
| `label_col` | no | `str` | `'label'` | See signature. |
| `p_col` | no | `str` | `'p_value'` | See signature. |
| `text_format` | no | `AnnotationFormat` | `'star'` | Annotation label style: ``"star"``, ``"pvalue"``, or ``"simple"``. |
| `hide_ns` | no | `bool` | `False` | If True, non-significant comparisons receive an empty annotation. |

### Returns

`pandas.DataFrame` - One row per comparison with test, statistic, raw/adjusted p-values, reject flag, annotation, and group sizes.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.search.grid_search_model`

Run :class:`~sklearn.model_selection.GridSearchCV` with stratified folds.

**Import path:** `fyron.ml.search.grid_search_model`

```python
grid_search_model(estimator: Any, param_grid: dict[str, Any], X_train: ArrayLikeInput, y_train: ArrayLikeInput, X_val: ArrayLikeInput | None = None, y_val: ArrayLikeInput | None = None, *, scoring: str = 'roc_auc', cv: int = 5, n_jobs: int = -1, refit: bool = True, random_state: int = 42, pos_label: Any | None = None) -> SearchResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimator` | yes | `Any` |  | See signature. |
| `param_grid` | yes | `dict[str, Any]` |  | See signature. |
| `X_train` | yes | `ArrayLikeInput` |  | See signature. |
| `y_train` | yes | `ArrayLikeInput` |  | See signature. |
| `X_val` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `y_val` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `scoring` | no | `str` | `'roc_auc'` | See signature. |
| `cv` | no | `int` | `5` | See signature. |
| `n_jobs` | no | `int` | `-1` | See signature. |
| `refit` | no | `bool` | `True` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |

### Returns

`SearchResult`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.splitting.train_test_split_data`

Split features and target into train and test sets.

**Import path:** `fyron.ml.splitting.train_test_split_data`

```python
train_test_split_data(X: ArrayLikeInput, y: ArrayLikeInput, *, test_size: float = 0.2, stratify: bool = True, random_state: int = 42) -> SplitReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `ArrayLikeInput` |  | Feature matrix. |
| `y` | yes | `ArrayLikeInput` |  | Target vector. |
| `test_size` | no | `float` | `0.2` | Fraction of samples held out for testing. |
| `stratify` | no | `bool` | `True` | If True, stratify on ``y``. |
| `random_state` | no | `int` | `42` | Random seed passed to scikit-learn. |

### Returns

X_train, X_test, y_train, y_test

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.training.train_random_forest`

Train a :class:`~sklearn.ensemble.RandomForestClassifier`.

**Import path:** `fyron.ml.training.train_random_forest`

```python
train_random_forest(X_train: ArrayLikeInput, y_train: ArrayLikeInput, X_test: ArrayLikeInput | None = None, y_test: ArrayLikeInput | None = None, *, class_weight: str | dict[Any, float] | None = None, random_state: int = 42, plot: bool = False, pos_label: Any | None = None, **model_params: Any) -> TrainingResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X_train` | yes | `ArrayLikeInput` |  | See signature. |
| `y_train` | yes | `ArrayLikeInput` |  | See signature. |
| `X_test` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `y_test` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `class_weight` | no | `str  or  dict[Any, float]  or  None` | `None` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `plot` | no | `bool` | `False` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |
| `model_params` | yes | `Any` |  | See signature. |

### Returns

`TrainingResult`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.ml.training.train_xgboost`

Train an :class:`xgboost.XGBClassifier`.

**Import path:** `fyron.ml.training.train_xgboost`

```python
train_xgboost(X_train: ArrayLikeInput, y_train: ArrayLikeInput, X_test: ArrayLikeInput | None = None, y_test: ArrayLikeInput | None = None, *, scale_pos_weight: float | None = None, random_state: int = 42, plot: bool = False, pos_label: Any | None = None, **model_params: Any) -> TrainingResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X_train` | yes | `ArrayLikeInput` |  | See signature. |
| `y_train` | yes | `ArrayLikeInput` |  | See signature. |
| `X_test` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `y_test` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `scale_pos_weight` | no | `float  or  None` | `None` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |
| `plot` | no | `bool` | `False` | See signature. |
| `pos_label` | no | `Any  or  None` | `None` | See signature. |
| `model_params` | yes | `Any` |  | See signature. |

### Returns

`TrainingResult`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.classification.bootstrap_classification_metrics`

Bootstrap binary classification metrics with percentile intervals.

**Import path:** `fyron.validation.classification.bootstrap_classification_metrics`

```python
bootstrap_classification_metrics(y_true: Sequence[Any], y_pred: Sequence[Any], y_prob: Sequence[float] | None = None, *, n_rounds: int = 1000, random_state: int = 42, pos_label: Any = 1, ci: float = 0.95) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `Sequence[Any]` |  | See signature. |
| `y_pred` | yes | `Sequence[Any]` |  | Ground-truth and predicted labels. |
| `y_prob` | no | `Sequence[float]  or  None` | `None` | Optional positive-class probabilities for AUC intervals. |
| `n_rounds` | no | `int` | `1000` | Number of bootstrap resamples. |
| `random_state` | no | `int` | `42` | Random seed for deterministic intervals. |
| `pos_label` | no | `Any` | `1` | Positive class label. |
| `ci` | no | `float` | `0.95` | Confidence interval width, for example ``0.95``. |

### Returns

`pandas.DataFrame` - One row per numeric metric with estimate, bootstrap mean, lower and upper CI.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.classification.calibration_summary`

Return calibration-in-the-large, calibration slope proxy, and bin table.

**Import path:** `fyron.validation.classification.calibration_summary`

```python
calibration_summary(y_true: Sequence[Any], y_prob: Sequence[float], *, n_bins: int = 10, pos_label: Any = 1) -> tuple[dict[str, float], pd.DataFrame]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `Sequence[Any]` |  | See signature. |
| `y_prob` | yes | `Sequence[float]` |  | See signature. |
| `n_bins` | no | `int` | `10` | See signature. |
| `pos_label` | no | `Any` | `1` | See signature. |

### Returns

`tuple[dict[str, float], pd.DataFrame]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.classification.decision_curve_table`

Compute binary decision-curve net benefit over thresholds.

**Import path:** `fyron.validation.classification.decision_curve_table`

```python
decision_curve_table(y_true: Sequence[Any], y_prob: Sequence[float], *, thresholds: Sequence[float] | None = None, pos_label: Any = 1) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `Sequence[Any]` |  | See signature. |
| `y_prob` | yes | `Sequence[float]` |  | See signature. |
| `thresholds` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `pos_label` | no | `Any` | `1` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.classification.find_best_threshold`

Find a binary decision threshold by an explicit metric.

**Import path:** `fyron.validation.classification.find_best_threshold`

```python
find_best_threshold(y_true: Sequence[Any], y_prob: Sequence[float], *, metric: ThresholdMetric = 'youden', pos_label: Any = 1, thresholds: Sequence[float] | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `Sequence[Any]` |  | See signature. |
| `y_prob` | yes | `Sequence[float]` |  | See signature. |
| `metric` | no | `ThresholdMetric` | `'youden'` | See signature. |
| `pos_label` | no | `Any` | `1` | See signature. |
| `thresholds` | no | `Sequence[float]  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.classification.subgroup_metric_table`

Calculate classification metrics separately for each subgroup.

**Import path:** `fyron.validation.classification.subgroup_metric_table`

```python
subgroup_metric_table(df: pd.DataFrame, *, group_col: str, y_true_col: str, y_pred_col: str, y_prob_col: str | None = None, pos_label: Any = 1) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `group_col` | yes | `str` |  | See signature. |
| `y_true_col` | yes | `str` |  | See signature. |
| `y_pred_col` | yes | `str` |  | See signature. |
| `y_prob_col` | no | `str  or  None` | `None` | See signature. |
| `pos_label` | no | `Any` | `1` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.survival.bootstrap_concordance_index`

Bootstrap Harrell-style concordance index for risk scores.

**Import path:** `fyron.validation.survival.bootstrap_concordance_index`

```python
bootstrap_concordance_index(df: pd.DataFrame, duration_col: str, event_col: str, risk_col: str, *, n_rounds: int = 1000, random_state: int = 42) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `risk_col` | yes | `str` |  | See signature. |
| `n_rounds` | no | `int` | `1000` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.survival.brier_score_at_time`

Return IPCW Brier score; censoring defaults to the evaluation cohort.

**Import path:** `fyron.validation.survival.brier_score_at_time`

```python
brier_score_at_time(df: pd.DataFrame, duration_col: str, event_col: str, prediction_col: str, time_horizon: float, *, censoring_df: pd.DataFrame | None = None) -> dict[str, float]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `prediction_col` | yes | `str` |  | See signature. |
| `time_horizon` | yes | `float` |  | See signature. |
| `censoring_df` | no | `pd.DataFrame  or  None` | `None` | See signature. |

### Returns

`dict[str, float]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.survival.external_survival_validation`

Evaluate a locked survival score or prediction column in an external cohort.

**Import path:** `fyron.validation.survival.external_survival_validation`

```python
external_survival_validation(train_summary_or_model: Any, external_df: pd.DataFrame, *, duration_col: str, event_col: str, risk_col: str, prediction_col: str | None = None, time_horizon: float | None = None, censoring_df: pd.DataFrame | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `train_summary_or_model` | yes | `Any` |  | See signature. |
| `external_df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `risk_col` | yes | `str` |  | See signature. |
| `prediction_col` | no | `str  or  None` | `None` | See signature. |
| `time_horizon` | no | `float  or  None` | `None` | See signature. |
| `censoring_df` | no | `pd.DataFrame  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.survival.survival_calibration_at_time`

Compare event risks with KM estimates and an IPCW Brier score.

**Import path:** `fyron.validation.survival.survival_calibration_at_time`

```python
survival_calibration_at_time(df: pd.DataFrame, duration_col: str, event_col: str, prediction_col: str, time_horizon: float, *, n_bins: int = 5, censoring_df: pd.DataFrame | None = None) -> tuple[dict[str, float], pd.DataFrame]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `prediction_col` | yes | `str` |  | See signature. |
| `time_horizon` | yes | `float` |  | See signature. |
| `n_bins` | no | `int` | `5` | See signature. |
| `censoring_df` | no | `pd.DataFrame  or  None` | `None` | See signature. |

### Returns

`tuple[dict[str, float], pd.DataFrame]`

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).

## `fyron.validation.survival.time_dependent_auc_table`

Compute cumulative/dynamic AUC at fixed time horizons.

**Import path:** `fyron.validation.survival.time_dependent_auc_table`

```python
time_dependent_auc_table(train_df: pd.DataFrame, test_df: pd.DataFrame, *, duration_col: str, event_col: str, risk_col: str, times: Sequence[float]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `train_df` | yes | `pd.DataFrame` |  | Training cohort used to estimate the censoring distribution. |
| `test_df` | yes | `pd.DataFrame` |  | Validation cohort with risk scores. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | Survival time and event indicator columns. |
| `risk_col` | yes | `str` |  | Higher values should indicate higher event risk. |
| `times` | yes | `Sequence[float]` |  | Positive time horizons for dynamic AUC. |

### Returns

`pandas.DataFrame` - AUC by time plus the mean AUC returned by scikit-survival.

**See also:** [ML, Validation, And Explainability module guide](../modules/ml.md).
