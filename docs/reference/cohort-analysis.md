# Cohort And Analysis Reference

Cohort construction, preprocessing, descriptive tables, statistical tests, effects, bootstrap intervals, and phenotype rules.

For workflow context, see [Cohort And Analysis module guide](../modules/cohort.md).

## Functions And Classes

- [`fyron.cohort.tables.audit_cohort_join`](#fyroncohorttablesauditcohortjoin)
- [`fyron.cohort.tables.audit_time_to_event_endpoint`](#fyroncohorttablesaudittimetoeventendpoint)
- [`fyron.cohort.tables.build_survival_columns`](#fyroncohorttablesbuildsurvivalcolumns)
- [`fyron.cohort.tables.build_time_to_event_endpoint`](#fyroncohorttablesbuildtimetoeventendpoint)
- [`fyron.cohort.tables.cohort_profile`](#fyroncohorttablescohortprofile)
- [`fyron.cohort.tables.join_cohort_tables`](#fyroncohorttablesjoincohorttables)
- [`fyron.cohort.tables.validate_cohort_table`](#fyroncohorttablesvalidatecohorttable)
- [`fyron.dataframe.add_code_indicators`](#fyrondataframeaddcodeindicators)
- [`fyron.dataframe.add_date_difference`](#fyrondataframeadddatedifference)
- [`fyron.dataframe.add_icd10_disease_groups`](#fyrondataframeaddicd10diseasegroups)
- [`fyron.dataframe.add_ops_categories`](#fyrondataframeaddopscategories)
- [`fyron.dataframe.add_time_window_flag`](#fyrondataframeaddtimewindowflag)
- [`fyron.dataframe.age_at_date`](#fyrondataframeageatdate)
- [`fyron.dataframe.classify_icd10`](#fyrondataframeclassifyicd10)
- [`fyron.dataframe.classify_icd10_string`](#fyrondataframeclassifyicd10string)
- [`fyron.dataframe.classify_ops`](#fyrondataframeclassifyops)
- [`fyron.dataframe.classify_ops_string`](#fyrondataframeclassifyopsstring)
- [`fyron.dataframe.date_difference`](#fyrondataframedatedifference)
- [`fyron.dataframe.explode_code_column`](#fyrondataframeexplodecodecolumn)
- [`fyron.dataframe.icd10_group_prevalence`](#fyrondataframeicd10groupprevalence)
- [`fyron.dataframe.normalize_code`](#fyrondataframenormalizecode)
- [`fyron.dataframe.ops_category_prevalence`](#fyrondataframeopscategoryprevalence)
- [`fyron.dataframe.split_code_string`](#fyrondataframesplitcodestring)
- [`fyron.descriptive.analysis.compare_descriptive_groups`](#fyrondescriptiveanalysiscomparedescriptivegroups)
- [`fyron.descriptive.analysis.create_table_one`](#fyrondescriptiveanalysiscreatetableone)
- [`fyron.descriptive.analysis.describe_categorical`](#fyrondescriptiveanalysisdescribecategorical)
- [`fyron.descriptive.analysis.describe_numeric`](#fyrondescriptiveanalysisdescribenumeric)
- [`fyron.descriptive.analysis.summarize_endpoint`](#fyrondescriptiveanalysissummarizeendpoint)
- [`fyron.phenotyping.rules.combine_phenotypes`](#fyronphenotypingrulescombinephenotypes)
- [`fyron.phenotyping.rules.define_code_phenotype`](#fyronphenotypingrulesdefinecodephenotype)
- [`fyron.phenotyping.rules.define_lab_threshold_phenotype`](#fyronphenotypingrulesdefinelabthresholdphenotype)
- [`fyron.phenotyping.rules.define_medication_exposure`](#fyronphenotypingrulesdefinemedicationexposure)
- [`fyron.phenotyping.rules.phenotype_summary`](#fyronphenotypingrulesphenotypesummary)
- [`fyron.preprocessing.encoding.apply_categorical_encoder`](#fyronpreprocessingencodingapplycategoricalencoder)
- [`fyron.preprocessing.encoding.encode_categorical`](#fyronpreprocessingencodingencodecategorical)
- [`fyron.preprocessing.encoding.fit_categorical_encoder`](#fyronpreprocessingencodingfitcategoricalencoder)
- [`fyron.preprocessing.encoding.summarize_encoding_plan`](#fyronpreprocessingencodingsummarizeencodingplan)
- [`fyron.preprocessing.imputation.apply_imputer`](#fyronpreprocessingimputationapplyimputer)
- [`fyron.preprocessing.imputation.fit_imputer`](#fyronpreprocessingimputationfitimputer)
- [`fyron.preprocessing.imputation.impute_dataframe`](#fyronpreprocessingimputationimputedataframe)
- [`fyron.preprocessing.imputation.summarize_imputation_plan`](#fyronpreprocessingimputationsummarizeimputationplan)
- [`fyron.preprocessing.qc.compare_train_test_balance`](#fyronpreprocessingqccomparetraintestbalance)
- [`fyron.preprocessing.qc.detect_potential_leakage`](#fyronpreprocessingqcdetectpotentialleakage)
- [`fyron.preprocessing.qc.feature_matrix_report`](#fyronpreprocessingqcfeaturematrixreport)
- [`fyron.preprocessing.qc.find_duplicate_ids`](#fyronpreprocessingqcfindduplicateids)
- [`fyron.preprocessing.qc.summarize_categorical_levels`](#fyronpreprocessingqcsummarizecategoricallevels)
- [`fyron.preprocessing.qc.summarize_missingness`](#fyronpreprocessingqcsummarizemissingness)
- [`fyron.statistics.bootstrap.BootstrapResult`](#fyronstatisticsbootstrapbootstrapresult)
- [`fyron.statistics.bootstrap.BootstrapResult.to_dict`](#fyronstatisticsbootstrapbootstrapresulttodict)
- [`fyron.statistics.bootstrap.bootstrap_binary_classification_metrics`](#fyronstatisticsbootstrapbootstrapbinaryclassificationmetrics)
- [`fyron.statistics.bootstrap.bootstrap_metric`](#fyronstatisticsbootstrapbootstrapmetric)
- [`fyron.statistics.bootstrap.bootstrap_summary`](#fyronstatisticsbootstrapbootstrapsummary)
- [`fyron.statistics.comparison.bootstrap_auc_difference`](#fyronstatisticscomparisonbootstrapaucdifference)
- [`fyron.statistics.comparison.mcnemar_test`](#fyronstatisticscomparisonmcnemartest)
- [`fyron.statistics.correction.adjust_p_values`](#fyronstatisticscorrectionadjustpvalues)
- [`fyron.statistics.correction.p_value_correction_table`](#fyronstatisticscorrectionpvaluecorrectiontable)
- [`fyron.statistics.effects.cliffs_delta`](#fyronstatisticseffectscliffsdelta)
- [`fyron.statistics.effects.cohens_d`](#fyronstatisticseffectscohensd)
- [`fyron.statistics.effects.cramers_v`](#fyronstatisticseffectscramersv)
- [`fyron.statistics.effects.odds_ratio_ci`](#fyronstatisticseffectsoddsratioci)
- [`fyron.statistics.effects.risk_ratio_ci`](#fyronstatisticseffectsriskratioci)
- [`fyron.statistics.effects.standardized_mean_difference`](#fyronstatisticseffectsstandardizedmeandifference)
- [`fyron.statistics.qc.correlation_pvalue_table`](#fyronstatisticsqccorrelationpvaluetable)
- [`fyron.statistics.qc.missingness_by_group_table`](#fyronstatisticsqcmissingnessbygrouptable)
- [`fyron.statistics.qc.normality_table`](#fyronstatisticsqcnormalitytable)
- [`fyron.statistics.qc.outlier_table`](#fyronstatisticsqcoutliertable)
- [`fyron.statistics.regression.fit_linear_regression_table`](#fyronstatisticsregressionfitlinearregressiontable)
- [`fyron.statistics.regression.fit_logistic_regression_table`](#fyronstatisticsregressionfitlogisticregressiontable)
- [`fyron.statistics.regression.vif_table`](#fyronstatisticsregressionviftable)
- [`fyron.statistics.tests.StatisticalTestResult`](#fyronstatisticstestsstatisticaltestresult)
- [`fyron.statistics.tests.StatisticalTestResult.to_dict`](#fyronstatisticstestsstatisticaltestresulttodict)
- [`fyron.statistics.tests.categorical_test`](#fyronstatisticstestscategoricaltest)
- [`fyron.statistics.tests.compare_multiple_groups`](#fyronstatisticstestscomparemultiplegroups)
- [`fyron.statistics.tests.compare_two_groups`](#fyronstatisticstestscomparetwogroups)
- [`fyron.statistics.tests.correlation_test`](#fyronstatisticstestscorrelationtest)
- [`fyron.statistics.tests.normality_test`](#fyronstatisticstestsnormalitytest)

## `fyron.cohort.tables.audit_cohort_join`

Report key coverage and hypothetical pandas merge sizes without joining rows.

**Import path:** `fyron.cohort.tables.audit_cohort_join`

```python
audit_cohort_join(features: pd.DataFrame, outcomes: pd.DataFrame, *, on: str = 'patient_id') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `features` | yes | `pd.DataFrame` |  | See signature. |
| `outcomes` | yes | `pd.DataFrame` |  | Research tables to inspect. Neither table is modified. |
| `on` | no | `str` | `'patient_id'` | Shared identifier column, as in ``join_cohort_tables``. |

### Returns

`pandas.DataFrame` - ``metric`` and integer ``count`` columns. Key and duplicate counts refer to nonmissing keys; missing rows are reported separately. Expected join sizes include pandas' null-to-null matching, but ``join_cohort_tables`` deliberately rejects missing keys. No identifiers are returned or logged.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.cohort.tables.audit_time_to_event_endpoint`

Inspect endpoint decisions without dropping or repairing any rows.

**Import path:** `fyron.cohort.tables.audit_time_to_event_endpoint`

```python
audit_time_to_event_endpoint(df: pd.DataFrame, *, index_date_col: str, event_date_col: str, censor_date_col: str, time_unit: TimeUnit = 'days', administrative_censor_date = None) -> dict[str, pd.DataFrame]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | One row per analysis unit. Original indices and ordering are retained. |
| `index_date_col` | yes | `str` |  | See signature. |
| `event_date_col` | yes | `str` |  | See signature. |
| `censor_date_col` | yes | `str` |  | Baseline, event, and last-follow-up date columns. |
| `time_unit` | no | `TimeUnit` | `'days'` | Elapsed days, weeks, months (30.4375 days), or years (365.25 days). |
| `administrative_censor_date` | no |  | `None` | Optional scalar cutoff; cannot create otherwise missing follow-up. |

### Returns

`dict` - ``rows`` contains tentative time/event/endpoint decisions and boolean quality flags. Use ``valid_endpoint`` or ``positive_duration_eligible`` before interpreting outcomes. ``summary`` contains metric, count, and severity columns. Flags may overlap; counts are not additive exclusions.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.cohort.tables.build_survival_columns`

Build standard survival ``time`` and ``event`` columns from date fields.

**Import path:** `fyron.cohort.tables.build_survival_columns`

```python
build_survival_columns(df: pd.DataFrame, *, start_col: str, end_col: str, event_col: str, time_col: str = 'time', event_out_col: str = 'event') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort table containing start, end, and event columns. |
| `start_col` | yes | `str` |  | Baseline or index-date column where follow-up begins. |
| `end_col` | yes | `str` |  | Endpoint or censoring column where follow-up ends. |
| `event_col` | yes | `str` |  | Existing column indicating whether the event occurred. |
| `time_col` | no | `str` | `'time'` | Name of the output duration column. |
| `event_out_col` | no | `str` | `'event'` | Name of the output event-indicator column. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with duration and event columns appended. Negative durations raise a ``ValueError``.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.cohort.tables.build_time_to_event_endpoint`

Build time-to-event columns from index, event, and censor dates.

**Import path:** `fyron.cohort.tables.build_time_to_event_endpoint`

```python
build_time_to_event_endpoint(df: pd.DataFrame, *, index_date_col: str, event_date_col: str, censor_date_col: str, time_col: str = 'time', event_col: str = 'event', endpoint_date_col: str = 'endpoint_date', endpoint_source_col: str = 'endpoint_source', time_unit: TimeUnit = 'days', require_endpoint: bool = True, administrative_censor_date = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort table with one row per patient or analysis unit. |
| `index_date_col` | yes | `str` |  | Start date for follow-up, such as diagnosis, baseline CT, or treatment start. |
| `event_date_col` | yes | `str` |  | Date of the event of interest. Missing values are treated as censored. |
| `censor_date_col` | yes | `str` |  | Last known follow-up or administrative censoring date. |
| `time_col` | no | `str` | `'time'` | Name of the output follow-up duration column. |
| `event_col` | no | `str` | `'event'` | Name of the output binary event-indicator column. |
| `endpoint_date_col` | no | `str` | `'endpoint_date'` | Name of the output column storing the selected event or censoring date. |
| `endpoint_source_col` | no | `str` | `'endpoint_source'` | Name of the output column storing ``"event"``, ``"censor"``, or ``"missing"``. |
| `time_unit` | no | `TimeUnit` | `'days'` | Unit for the computed follow-up time: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``. |
| `require_endpoint` | no | `bool` | `True` | If True, rows with neither an event nor a censor date raise an error. If False, unresolved rows retain missing time, event=0, and source ``missing``; they are not valid observed censoring. |
| `administrative_censor_date` | no |  | `None` | Optional scalar date limiting an otherwise available endpoint. Cannot manufacture missing follow-up. Events exactly on the cutoff count as events. Timezone-aware dates are normalized to UTC; mixing aware and naive nonmissing dates raises. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with time, event, endpoint date, and endpoint source columns.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.cohort.tables.cohort_profile`

Create a compact audit table for a patient-level cohort.

**Import path:** `fyron.cohort.tables.cohort_profile`

```python
cohort_profile(df: pd.DataFrame, *, id_col: str = 'patient_id', endpoint_cols: Sequence[str] | None = None, group_col: str | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort table to profile. |
| `id_col` | no | `str` | `'patient_id'` | Patient or analysis-unit identifier. |
| `endpoint_cols` | no | `Sequence[str]  or  None` | `None` | Optional binary or numeric endpoint columns to summarize. |
| `group_col` | no | `str  or  None` | `None` | Optional subgroup column for distribution checks. |

### Returns

`pandas.DataFrame` - Rows named by ``metric`` with values useful for cohort review.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.cohort.tables.join_cohort_tables`

Join feature and outcome tables on a patient identifier.

**Import path:** `fyron.cohort.tables.join_cohort_tables`

```python
join_cohort_tables(features: pd.DataFrame, outcomes: pd.DataFrame, *, on: str = 'patient_id', how: str = 'inner', validate: str = 'one_to_one') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `features` | yes | `pd.DataFrame` |  | Patient-level predictors (must include ``on``). |
| `outcomes` | yes | `pd.DataFrame` |  | Patient-level outcomes (must include ``on``). |
| `on` | no | `str` | `'patient_id'` | Join key column name. |
| `how` | no | `str` | `'inner'` | Merge strategy passed to :meth:`pandas.DataFrame.merge`. |
| `validate` | no | `str` | `'one_to_one'` | Merge validation (e.g. ``one_to_one``) to catch duplicate keys. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.cohort.tables.validate_cohort_table`

Validate a cohort DataFrame for analysis-ready use.

**Import path:** `fyron.cohort.tables.validate_cohort_table`

```python
validate_cohort_table(df: pd.DataFrame, *, required_columns: Sequence[str], id_column: str | None = 'patient_id', allow_duplicate_ids: bool = False) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort table with one row per patient, lesion, study, or other declared analysis unit. |
| `required_columns` | yes | `Sequence[str]` |  | Column names that must be present before the cohort can be used downstream. |
| `id_column` | no | `str  or  None` | `'patient_id'` | Optional identifier column used to detect missing or duplicate analysis units. Pass ``None`` to skip identifier checks. |
| `allow_duplicate_ids` | no | `bool` | `False` | If False, duplicate values in ``id_column`` raise a ``ValueError``. |

### Returns

`pandas.DataFrame` - The original input DataFrame, unchanged, when all validation checks pass.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.add_code_indicators`

Add binary indicator columns for selected clinical codes.

**Import path:** `fyron.dataframe.add_code_indicators`

```python
add_code_indicators(df: pd.DataFrame, code_col: str, codes: Sequence[Any] | Mapping[str, Sequence[Any]], *, sep: str = ';', prefix: str = 'code_', normalize: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing a code column. |
| `code_col` | yes | `str` |  | Column with one or more codes per row. |
| `codes` | yes | `Sequence[Any]  or  Mapping[str, Sequence[Any]]` |  | Either a sequence of codes or a mapping from output names to code lists. |
| `sep` | no | `str` | `';'` | Delimiter between multiple codes in one cell. |
| `prefix` | no | `str` | `'code_'` | Prefix used for generated indicator columns. |
| `normalize` | no | `bool` | `True` | If True, normalize both input and target codes before matching. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with binary indicator columns.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.add_date_difference`

Add a date-difference feature from two DataFrame columns.

**Import path:** `fyron.dataframe.add_date_difference`

```python
add_date_difference(df: pd.DataFrame, start_col: str, end_col: str, output_col: str, *, unit: TimeUnit = 'days', absolute: bool = False, allow_negative: bool = True, errors: str = 'coerce') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing start and end date columns. |
| `start_col` | yes | `str` |  | Start date column. |
| `end_col` | yes | `str` |  | End date column. |
| `output_col` | yes | `str` |  | Name of the created numeric difference column. |
| `unit` | no | `TimeUnit` | `'days'` | Output unit: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``. |
| `absolute` | no | `bool` | `False` | If True, store absolute differences. |
| `allow_negative` | no | `bool` | `True` | If False, raise when a non-missing negative interval is computed. |
| `errors` | no | `str` | `'coerce'` | Date parsing policy: ``"coerce"`` (default) or ``"raise"``. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with the created difference column.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.add_icd10_disease_groups`

Add broad ICD-10 disease-group indicator columns.

**Import path:** `fyron.dataframe.add_icd10_disease_groups`

```python
add_icd10_disease_groups(df: pd.DataFrame, icd_col: str, *, sep: str = ';', prefix: str = 'icd10_group_', summary_col: str = 'icd10_groups', count_col: str = 'n_icd10_groups', groups: Sequence[str] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing an ICD-10 code column. |
| `icd_col` | yes | `str` |  | Column with one or more ICD-10 codes per row. |
| `sep` | no | `str` | `';'` | Delimiter between multiple codes in one cell. |
| `prefix` | no | `str` | `'icd10_group_'` | Prefix for generated binary indicator columns. |
| `summary_col` | no | `str` | `'icd10_groups'` | Output column containing human-readable disease groups. |
| `count_col` | no | `str` | `'n_icd10_groups'` | Output column containing the number of disease groups per row. |
| `groups` | no | `Sequence[str]  or  None` | `None` | Optional explicit disease-group order. Defaults to Fyron's built-in broad ICD-10 groups. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with binary disease-group indicators and summary columns.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.add_ops_categories`

Add broad German OPS procedure-category indicator columns.

**Import path:** `fyron.dataframe.add_ops_categories`

```python
add_ops_categories(df: pd.DataFrame, ops_col: str, *, sep: str = ';', prefix: str = 'ops_category_', summary_col: str = 'ops_categories', count_col: str = 'n_ops_categories', categories: Sequence[str] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing an OPS code column. |
| `ops_col` | yes | `str` |  | Column with one or more OPS codes per row. |
| `sep` | no | `str` | `';'` | Delimiter between multiple codes in one cell. |
| `prefix` | no | `str` | `'ops_category_'` | Prefix for generated binary indicator columns. |
| `summary_col` | no | `str` | `'ops_categories'` | Output column containing human-readable OPS categories. |
| `count_col` | no | `str` | `'n_ops_categories'` | Output column containing the number of OPS categories per row. |
| `categories` | no | `Sequence[str]  or  None` | `None` | Optional explicit category order. Defaults to Fyron's broad OPS groups. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with binary OPS category indicators and summary columns.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.add_time_window_flag`

Flag rows where a date falls within a window around an index date.

**Import path:** `fyron.dataframe.add_time_window_flag`

```python
add_time_window_flag(df: pd.DataFrame, date_col: str, index_date_col: str, output_col: str, *, before: float | None = None, after: float | None = None, unit: TimeUnit = 'days', errors: str = 'coerce') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing event and index date columns. |
| `date_col` | yes | `str` |  | Date to test against the index date. |
| `index_date_col` | yes | `str` |  | Index/reference date column. |
| `output_col` | yes | `str` |  | Name of the created binary flag column. |
| `before` | no | `float  or  None` | `None` | Maximum time before the index date allowed in the window. |
| `after` | no | `float  or  None` | `None` | Maximum time after the index date allowed in the window. |
| `unit` | no | `TimeUnit` | `'days'` | Window unit: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``. |
| `errors` | no | `str` | `'coerce'` | Date parsing policy: ``"coerce"`` (default) or ``"raise"``. Missing dates produce zero flags. Bounds must be finite and nonnegative. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with an integer 0/1 window flag column.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.age_at_date`

Add age in years at a reference date.

**Import path:** `fyron.dataframe.age_at_date`

```python
age_at_date(df: pd.DataFrame, birth_date_col: str, reference_date_col: str, *, output_col: str = 'age_years', errors: str = 'coerce') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing birth and reference dates. |
| `birth_date_col` | yes | `str` |  | Date-of-birth column. |
| `reference_date_col` | yes | `str` |  | Date column where age should be calculated, such as diagnosis or index date. |
| `output_col` | no | `str` | `'age_years'` | Name of the created age column. |
| `errors` | no | `str` | `'coerce'` | Date parsing policy: ``"coerce"`` (default) or ``"raise"``. Age is elapsed days divided by 365.25, not completed calendar birthdays. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with age in years.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.classify_icd10`

Classify one ICD-10 code into a broad disease group.

**Import path:** `fyron.dataframe.classify_icd10`

```python
classify_icd10(code: Any) -> str | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `Any` |  | ICD-10 code such as ``"C34"``, ``"I50.1"``, or ``"Z51"``. |

### Returns

`str or None` - Broad disease group name, ``"Other"`` for malformed non-empty codes, or None for missing values.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.classify_icd10_string`

Classify a delimited ICD-10 code string into disease groups.

**Import path:** `fyron.dataframe.classify_icd10_string`

```python
classify_icd10_string(value: Any, *, sep: str = ';') -> set[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Scalar cell containing one or more ICD-10 codes. |
| `sep` | no | `str` | `';'` | Delimiter between codes. |

### Returns

`set[str]` - Disease groups present in the code string.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.classify_ops`

Classify one German OPS code into a broad procedure category.

**Import path:** `fyron.dataframe.classify_ops`

```python
classify_ops(code: Any) -> str | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `Any` |  | OPS code such as ``"1-620"``, ``"3-20"``, ``"5-541"``, or ``"8-980"``. |

### Returns

`str or None` - Broad OPS category, ``"Other"`` for malformed non-empty codes, or None for missing values.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.classify_ops_string`

Classify a delimited OPS code string into broad procedure categories.

**Import path:** `fyron.dataframe.classify_ops_string`

```python
classify_ops_string(value: Any, *, sep: str = ';') -> set[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Scalar cell containing one or more OPS codes. |
| `sep` | no | `str` | `';'` | Delimiter between codes. |

### Returns

`set[str]` - OPS categories present in the code string.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.date_difference`

Calculate a date difference in days, weeks, months, or years.

**Import path:** `fyron.dataframe.date_difference`

```python
date_difference(start: Any, end: Any, *, unit: TimeUnit = 'days', absolute: bool = False, errors: str = 'coerce') -> pd.Series
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `start` | yes | `Any` |  | Start date scalar or array-like value. |
| `end` | yes | `Any` |  | End date scalar or array-like value. |
| `unit` | no | `TimeUnit` | `'days'` | Output unit: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``. |
| `absolute` | no | `bool` | `False` | If True, return absolute differences. |
| `errors` | no | `str` | `'coerce'` | ``"coerce"`` makes malformed dates missing; ``"raise"`` rejects them. Aware timestamps use UTC elapsed time; naive/aware mixtures raise. Scalars broadcast to vectors; Series indices must agree exactly. |

### Returns

`pandas.Series` - Numeric difference in the requested unit.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.explode_code_column`

Explode a delimited clinical code column into one row per code.

**Import path:** `fyron.dataframe.explode_code_column`

```python
explode_code_column(df: pd.DataFrame, code_col: str, *, sep: str = ';', output_col: str = 'code', keep_empty: bool = False) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing a delimited code column. |
| `code_col` | yes | `str` |  | Column with one or more codes per row. |
| `sep` | no | `str` | `';'` | Delimiter between codes. |
| `output_col` | no | `str` | `'code'` | Name of the exploded output code column. |
| `keep_empty` | no | `bool` | `False` | If True, keep rows without codes and set ``output_col`` to missing. |

### Returns

`pandas.DataFrame` - Exploded DataFrame with one row per parsed code.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.icd10_group_prevalence`

Summarize ICD-10 disease-group indicator prevalence.

**Import path:** `fyron.dataframe.icd10_group_prevalence`

```python
icd10_group_prevalence(df: pd.DataFrame, *, group_cols: Sequence[str] | None = None, prefix: str = 'icd10_group_') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame with ICD-10 group indicator columns. |
| `group_cols` | no | `Sequence[str]  or  None` | `None` | Optional explicit indicator columns. If omitted, columns with ``prefix`` are used. |
| `prefix` | no | `str` | `'icd10_group_'` | Prefix used to discover indicator columns. |

### Returns

`pandas.DataFrame` - Prevalence table with group, column, patient count, and percent.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.normalize_code`

Normalize one clinical code value for matching.

**Import path:** `fyron.dataframe.normalize_code`

```python
normalize_code(value: Any, *, uppercase: bool = True, remove_spaces: bool = True, remove_dots: bool = False) -> str | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Raw code value such as an ICD-10, OPS, medication, or local registry code. |
| `uppercase` | no | `bool` | `True` | If True, convert the returned code to uppercase. |
| `remove_spaces` | no | `bool` | `True` | If True, remove whitespace within the code. |
| `remove_dots` | no | `bool` | `False` | If True, remove dots from the code. |

### Returns

`str or None` - Normalized code string, or None for missing/empty values.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.ops_category_prevalence`

Summarize OPS procedure-category indicator prevalence.

**Import path:** `fyron.dataframe.ops_category_prevalence`

```python
ops_category_prevalence(df: pd.DataFrame, *, category_cols: Sequence[str] | None = None, prefix: str = 'ops_category_') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame with OPS category indicator columns. |
| `category_cols` | no | `Sequence[str]  or  None` | `None` | Optional explicit indicator columns. If omitted, columns with ``prefix`` are used. |
| `prefix` | no | `str` | `'ops_category_'` | Prefix used to discover indicator columns. |

### Returns

`pandas.DataFrame` - Prevalence table with category, column, patient count, and percent.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.dataframe.split_code_string`

Split one cell containing one or more clinical codes.

**Import path:** `fyron.dataframe.split_code_string`

```python
split_code_string(value: Any, *, sep: str = ';', normalize: bool = True) -> list[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Scalar value containing one or more codes, usually separated by semicolons. |
| `sep` | no | `str` | `';'` | Delimiter used between codes. |
| `normalize` | no | `bool` | `True` | If True, normalize each code with :func:`normalize_code`. |

### Returns

`list[str]` - Ordered list of non-empty codes.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.descriptive.analysis.compare_descriptive_groups`

Compare descriptive variables across groups with explicit statistical tests.

**Import path:** `fyron.descriptive.analysis.compare_descriptive_groups`

```python
compare_descriptive_groups(df: pd.DataFrame, *, group_col: str, numeric: Sequence[str] | None = None, categorical: Sequence[str] | None = None, include_smd: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort or analysis table. |
| `group_col` | yes | `str` |  | Column defining comparison groups. |
| `numeric` | no | `Sequence[str]  or  None` | `None` | Numeric variables to compare. If omitted, numeric columns are selected automatically. |
| `categorical` | no | `Sequence[str]  or  None` | `None` | Categorical variables to compare. If omitted, remaining non-numeric columns are selected automatically. |
| `include_smd` | no | `bool` | `True` | If True, include standardized mean difference summaries. |

### Returns

`pandas.DataFrame` - One row per variable with variable type, test result fields, p-value, optional SMD, and error text when a comparison cannot be computed.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.descriptive.analysis.create_table_one`

Create a table-one style long table with optional p-values.

**Import path:** `fyron.descriptive.analysis.create_table_one`

```python
create_table_one(df: pd.DataFrame, *, group_col: str | None = None, numeric: Sequence[str] | None = None, categorical: Sequence[str] | None = None, include_smd: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort table to describe. |
| `group_col` | no | `str  or  None` | `None` | Optional group column such as treatment arm, cohort, split, or outcome. |
| `numeric` | no | `Sequence[str]  or  None` | `None` | Numeric variables to include. If omitted, numeric columns are selected automatically. |
| `categorical` | no | `Sequence[str]  or  None` | `None` | Categorical variables to include. If omitted, non-numeric columns are selected automatically. |
| `include_smd` | no | `bool` | `True` | If True and ``group_col`` is provided, include standardized mean difference values. |

### Returns

`pandas.DataFrame` - Long Table 1 style output with variable, level, group, formatted summary, and optional p-value, SMD, and test columns.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.descriptive.analysis.describe_categorical`

Describe categorical variables with counts and percentages.

**Import path:** `fyron.descriptive.analysis.describe_categorical`

```python
describe_categorical(df: pd.DataFrame, *, columns: Sequence[str] | None = None, group_col: str | None = None, include_missing: bool = True, digits: int = 1) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort or analysis table. |
| `columns` | no | `Sequence[str]  or  None` | `None` | Categorical columns to summarize. If omitted, non-numeric columns are selected automatically. |
| `group_col` | no | `str  or  None` | `None` | Optional grouping column for stratified summaries. |
| `include_missing` | no | `bool` | `True` | Include missing values as an explicit ``"<missing>"`` level. |
| `digits` | no | `int` | `1` | Decimal places used for percentages. |

### Returns

`pandas.DataFrame` - Long table with group, variable, level, count, and percent columns.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.descriptive.analysis.describe_numeric`

Describe numeric variables with n, missing, mean, SD, median, IQR, and range.

**Import path:** `fyron.descriptive.analysis.describe_numeric`

```python
describe_numeric(df: pd.DataFrame, *, columns: Sequence[str] | None = None, group_col: str | None = None, digits: int = 2) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort or analysis table. |
| `columns` | no | `Sequence[str]  or  None` | `None` | Numeric columns to summarize. If omitted, numeric columns are selected automatically. |
| `group_col` | no | `str  or  None` | `None` | Optional grouping column for stratified summaries. |
| `digits` | no | `int` | `2` | Decimal places used for rounded numeric summaries. |

### Returns

`pandas.DataFrame` - Long table with one row per variable and group containing count, missingness, mean, standard deviation, median, quartiles, and range.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.descriptive.analysis.summarize_endpoint`

Summarize endpoint counts, event rates, and optional follow-up time.

**Import path:** `fyron.descriptive.analysis.summarize_endpoint`

```python
summarize_endpoint(df: pd.DataFrame, *, event_col: str, time_col: str | None = None, group_col: str | None = None, digits: int = 2) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort table containing endpoint and optional follow-up columns. |
| `event_col` | yes | `str` |  | Binary or numeric event-indicator column where nonzero values count as events. |
| `time_col` | no | `str  or  None` | `None` | Optional duration/follow-up column to summarize. |
| `group_col` | no | `str  or  None` | `None` | Optional grouping column for stratified endpoint summaries. |
| `digits` | no | `int` | `2` | Decimal places used for percentages and follow-up summaries. |

### Returns

`pandas.DataFrame` - One row per group with sample size, event count, event rate, and optional median/min/max follow-up.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.phenotyping.rules.combine_phenotypes`

Combine patient-level phenotype tables with an any/all rule.

**Import path:** `fyron.phenotyping.rules.combine_phenotypes`

```python
combine_phenotypes(tables: Sequence[pd.DataFrame], *, patient_col: str = 'patient_id', strategy: CombineStrategy = 'any', phenotype_name: str = 'combined') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `tables` | yes | `Sequence[pd.DataFrame]` |  | See signature. |
| `patient_col` | no | `str` | `'patient_id'` | See signature. |
| `strategy` | no | `CombineStrategy` | `'any'` | See signature. |
| `phenotype_name` | no | `str` | `'combined'` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.phenotyping.rules.define_code_phenotype`

Define a phenotype from diagnosis/procedure/code rows.

**Import path:** `fyron.phenotyping.rules.define_code_phenotype`

```python
define_code_phenotype(df: pd.DataFrame, code_col: str, codes: Sequence[Any], *, patient_col: str = 'patient_id', date_col: str | None = None, phenotype_name: str = 'phenotype', code_system_col: str | None = None, code_systems: Sequence[Any] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `code_col` | yes | `str` |  | See signature. |
| `codes` | yes | `Sequence[Any]` |  | See signature. |
| `patient_col` | no | `str` | `'patient_id'` | See signature. |
| `date_col` | no | `str  or  None` | `None` | See signature. |
| `phenotype_name` | no | `str` | `'phenotype'` | See signature. |
| `code_system_col` | no | `str  or  None` | `None` | See signature. |
| `code_systems` | no | `Sequence[Any]  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.phenotyping.rules.define_lab_threshold_phenotype`

Define a phenotype from numeric lab/measurement thresholds.

**Import path:** `fyron.phenotyping.rules.define_lab_threshold_phenotype`

```python
define_lab_threshold_phenotype(df: pd.DataFrame, value_col: str, threshold: float, *, direction: ThresholdDirection = '>=', patient_col: str = 'patient_id', date_col: str | None = None, phenotype_name: str = 'phenotype') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `value_col` | yes | `str` |  | See signature. |
| `threshold` | yes | `float` |  | See signature. |
| `direction` | no | `ThresholdDirection` | `'>='` | See signature. |
| `patient_col` | no | `str` | `'patient_id'` | See signature. |
| `date_col` | no | `str  or  None` | `None` | See signature. |
| `phenotype_name` | no | `str` | `'phenotype'` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.phenotyping.rules.define_medication_exposure`

Define medication exposure from medication name/code rows.

**Import path:** `fyron.phenotyping.rules.define_medication_exposure`

```python
define_medication_exposure(df: pd.DataFrame, medication_col: str, medications: Sequence[Any], *, patient_col: str = 'patient_id', start_col: str | None = None, end_col: str | None = None, phenotype_name: str = 'exposure') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `medication_col` | yes | `str` |  | See signature. |
| `medications` | yes | `Sequence[Any]` |  | See signature. |
| `patient_col` | no | `str` | `'patient_id'` | See signature. |
| `start_col` | no | `str  or  None` | `None` | See signature. |
| `end_col` | no | `str  or  None` | `None` | See signature. |
| `phenotype_name` | no | `str` | `'exposure'` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.phenotyping.rules.phenotype_summary`

Summarize phenotype prevalence overall or by group.

**Import path:** `fyron.phenotyping.rules.phenotype_summary`

```python
phenotype_summary(df: pd.DataFrame, phenotype_col: str, *, patient_col: str = 'patient_id', group_col: str | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `phenotype_col` | yes | `str` |  | See signature. |
| `patient_col` | no | `str` | `'patient_id'` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.encoding.apply_categorical_encoder`

Apply a fitted Fyron categorical encoder.

**Import path:** `fyron.preprocessing.encoding.apply_categorical_encoder`

```python
apply_categorical_encoder(df: pd.DataFrame, encoder: dict[str, Any]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `encoder` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.encoding.encode_categorical`

Fit and apply a categorical encoder to one DataFrame.

**Import path:** `fyron.preprocessing.encoding.encode_categorical`

```python
encode_categorical(df: pd.DataFrame, **kwargs: Any) -> tuple[pd.DataFrame, dict[str, Any]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`tuple[pd.DataFrame, dict[str, Any]]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.encoding.fit_categorical_encoder`

Fit a deterministic one-hot encoder specification.

**Import path:** `fyron.preprocessing.encoding.fit_categorical_encoder`

```python
fit_categorical_encoder(df: pd.DataFrame, *, columns: Sequence[str] | None = None, drop_first: bool = False, rare_min_count: int | None = None, rare_label: str = '__rare__') -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `columns` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `drop_first` | no | `bool` | `False` | See signature. |
| `rare_min_count` | no | `int  or  None` | `None` | See signature. |
| `rare_label` | no | `str` | `'__rare__'` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.encoding.summarize_encoding_plan`

Summarize categorical levels before one-hot encoding.

**Import path:** `fyron.preprocessing.encoding.summarize_encoding_plan`

```python
summarize_encoding_plan(df: pd.DataFrame, *, columns: Sequence[str] | None = None, max_levels: int = 20) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `columns` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `max_levels` | no | `int` | `20` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.imputation.apply_imputer`

Apply a fitted Fyron imputer to a DataFrame.

**Import path:** `fyron.preprocessing.imputation.apply_imputer`

```python
apply_imputer(df: pd.DataFrame, imputer: dict[str, Any]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `imputer` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.imputation.fit_imputer`

Fit a lightweight imputation specification on a training DataFrame.

**Import path:** `fyron.preprocessing.imputation.fit_imputer`

```python
fit_imputer(df: pd.DataFrame, *, numeric: Sequence[str] | None = None, categorical: Sequence[str] | None = None, strategy_numeric: NumericStrategy = 'median', strategy_categorical: CategoricalStrategy = 'most_frequent', fill_value_numeric: float = 0.0, fill_value_categorical: str = '__missing__', add_missing_indicators: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `numeric` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `categorical` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `strategy_numeric` | no | `NumericStrategy` | `'median'` | See signature. |
| `strategy_categorical` | no | `CategoricalStrategy` | `'most_frequent'` | See signature. |
| `fill_value_numeric` | no | `float` | `0.0` | See signature. |
| `fill_value_categorical` | no | `str` | `'__missing__'` | See signature. |
| `add_missing_indicators` | no | `bool` | `False` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.imputation.impute_dataframe`

Fit and apply an imputer to one DataFrame.

**Import path:** `fyron.preprocessing.imputation.impute_dataframe`

```python
impute_dataframe(df: pd.DataFrame, **kwargs: Any) -> tuple[pd.DataFrame, dict[str, Any]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`tuple[pd.DataFrame, dict[str, Any]]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.imputation.summarize_imputation_plan`

Summarize columns and strategies before fitting an imputer.

**Import path:** `fyron.preprocessing.imputation.summarize_imputation_plan`

```python
summarize_imputation_plan(df: pd.DataFrame, *, numeric: Sequence[str] | None = None, categorical: Sequence[str] | None = None, strategy_numeric: NumericStrategy = 'median', strategy_categorical: CategoricalStrategy = 'most_frequent') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `numeric` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `categorical` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `strategy_numeric` | no | `NumericStrategy` | `'median'` | See signature. |
| `strategy_categorical` | no | `CategoricalStrategy` | `'most_frequent'` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.qc.compare_train_test_balance`

Compare simple train/test distributions for leakage and split sanity checks.

**Import path:** `fyron.preprocessing.qc.compare_train_test_balance`

```python
compare_train_test_balance(train: pd.DataFrame, test: pd.DataFrame, *, columns: Sequence[str] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `train` | yes | `pd.DataFrame` |  | See signature. |
| `test` | yes | `pd.DataFrame` |  | See signature. |
| `columns` | no | `Sequence[str]  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.qc.detect_potential_leakage`

Flag column names that may encode outcomes, labels, or post-index information.

**Import path:** `fyron.preprocessing.qc.detect_potential_leakage`

```python
detect_potential_leakage(columns: Sequence[str] | pd.DataFrame, *, outcome_keywords: Sequence[str] = ('event', 'death', 'survival', 'outcome', 'label', 'target'), time_keywords: Sequence[str] = ('followup', 'follow_up', 'last', 'end_date', 'post', 'af...) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `columns` | yes | `Sequence[str]  or  pd.DataFrame` |  | See signature. |
| `outcome_keywords` | no | `Sequence[str]` | `('event', 'death', 'survival', 'outcome', 'label', 'target')` | See signature. |
| `time_keywords` | no | `Sequence[str]` | `('followup', 'follow_up', 'last', 'end_date', 'post', 'af...` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.qc.feature_matrix_report`

Summarize feature-matrix quality before modeling.

**Import path:** `fyron.preprocessing.qc.feature_matrix_report`

```python
feature_matrix_report(X: pd.DataFrame, y: Sequence[Any] | pd.Series | None = None, *, rare_threshold: float = 0.01, leakage_keywords: Sequence[str] = ('event', 'death', 'survival', 'outcome', 'label', 'target')) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X` | yes | `pd.DataFrame` |  | Feature matrix with one column per candidate predictor. |
| `y` | no | `Sequence[Any]  or  pd.Series  or  None` | `None` | Optional labels used only for target count metadata. |
| `rare_threshold` | no | `float` | `0.01` | Binary features with a minority-class frequency below this value are flagged. |
| `leakage_keywords` | no | `Sequence[str]` | `('event', 'death', 'survival', 'outcome', 'label', 'target')` | Column-name fragments that suggest outcome or post-index leakage. |

### Returns

`pandas.DataFrame` - One row per feature with dtype, missingness, uniqueness, constant, rare-binary, and leakage-name flags.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.qc.find_duplicate_ids`

Return rows whose patient identifier appears more than once.

**Import path:** `fyron.preprocessing.qc.find_duplicate_ids`

```python
find_duplicate_ids(df: pd.DataFrame, *, id_col: str = 'patient_id') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `id_col` | no | `str` | `'patient_id'` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.qc.summarize_categorical_levels`

Summarize counts and percentages for categorical columns.

**Import path:** `fyron.preprocessing.qc.summarize_categorical_levels`

```python
summarize_categorical_levels(df: pd.DataFrame, *, columns: Sequence[str] | None = None, max_levels: int = 20, include_missing: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `columns` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `max_levels` | no | `int` | `20` | See signature. |
| `include_missing` | no | `bool` | `True` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.preprocessing.qc.summarize_missingness`

Summarize missing values by column, optionally within groups.

**Import path:** `fyron.preprocessing.qc.summarize_missingness`

```python
summarize_missingness(df: pd.DataFrame, *, columns: Sequence[str] | None = None, group_col: str | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `columns` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.bootstrap.BootstrapResult`

Result for one bootstrapped statistic.

**Import path:** `fyron.statistics.bootstrap.BootstrapResult`

```python
BootstrapResult()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

### Public Methods

#### `fyron.statistics.bootstrap.BootstrapResult.to_dict`

See the signature and linked module guide for context.

**Import path:** `fyron.statistics.bootstrap.BootstrapResult.to_dict`

```python
BootstrapResult.to_dict(self, *, include_distribution: bool = False) -> dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `include_distribution` | no | `bool` | `False` | See signature. |

#### Returns

`dict[str, Any]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.bootstrap.bootstrap_binary_classification_metrics`

Bootstrap common binary classification metrics.

**Import path:** `fyron.statistics.bootstrap.bootstrap_binary_classification_metrics`

```python
bootstrap_binary_classification_metrics(y_true: Sequence[Any], y_pred: Sequence[Any], y_prob: Sequence[Any] | None = None, *, metrics: Sequence[str] | None = None, pos_label: Any = 1, n_rounds: int = 1000, alpha: float = 0.05, random_state: int | None = None, drop_invalid: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `Sequence[Any]` |  | See signature. |
| `y_pred` | yes | `Sequence[Any]` |  | See signature. |
| `y_prob` | no | `Sequence[Any]  or  None` | `None` | See signature. |
| `metrics` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `pos_label` | no | `Any` | `1` | See signature. |
| `n_rounds` | no | `int` | `1000` | See signature. |
| `alpha` | no | `float` | `0.05` | See signature. |
| `random_state` | no | `int  or  None` | `None` | See signature. |
| `drop_invalid` | no | `bool` | `True` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.bootstrap.bootstrap_metric`

Bootstrap an arbitrary metric over one or more aligned arrays.

**Import path:** `fyron.statistics.bootstrap.bootstrap_metric`

```python
bootstrap_metric(*arrays: Sequence[Any], metric_func: MetricFunc, metric_name: str | None = None, n_rounds: int = 1000, alpha: float = 0.05, random_state: int | None = None, drop_invalid: bool = True, **metric_kwargs: Any) -> BootstrapResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `arrays` | yes | `Sequence[Any]` |  | See signature. |
| `metric_func` | yes | `MetricFunc` |  | See signature. |
| `metric_name` | no | `str  or  None` | `None` | See signature. |
| `n_rounds` | no | `int` | `1000` | See signature. |
| `alpha` | no | `float` | `0.05` | See signature. |
| `random_state` | no | `int  or  None` | `None` | See signature. |
| `drop_invalid` | no | `bool` | `True` | See signature. |
| `metric_kwargs` | yes | `Any` |  | See signature. |

### Returns

`BootstrapResult`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.bootstrap.bootstrap_summary`

Bootstrap a one-sample summary statistic such as mean or median.

**Import path:** `fyron.statistics.bootstrap.bootstrap_summary`

```python
bootstrap_summary(values: Sequence[Any], *, statistic: SummaryStatistic | Callable[[Any], float] = 'mean', n_rounds: int = 1000, alpha: float = 0.05, random_state: int | None = None) -> BootstrapResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `values` | yes | `Sequence[Any]` |  | See signature. |
| `statistic` | no | `SummaryStatistic  or  Callable[[Any], float]` | `'mean'` | See signature. |
| `n_rounds` | no | `int` | `1000` | See signature. |
| `alpha` | no | `float` | `0.05` | See signature. |
| `random_state` | no | `int  or  None` | `None` | See signature. |

### Returns

`BootstrapResult`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.comparison.bootstrap_auc_difference`

Bootstrap the paired AUC difference between two models.

**Import path:** `fyron.statistics.comparison.bootstrap_auc_difference`

```python
bootstrap_auc_difference(y_true: Sequence[Any], prob_a: Sequence[Any], prob_b: Sequence[Any], *, pos_label: Any = 1, n_rounds: int = 1000, alpha: float = 0.05, random_state: int | None = None, drop_invalid: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `Sequence[Any]` |  | Ground-truth binary labels. |
| `prob_a` | yes | `Sequence[Any]` |  | Predicted probabilities or scores from model A. |
| `prob_b` | yes | `Sequence[Any]` |  | Predicted probabilities or scores from model B on the same samples. |
| `pos_label` | no | `Any` | `1` | Label treated as the positive class. |
| `n_rounds` | no | `int` | `1000` | Number of bootstrap resamples. |
| `alpha` | no | `float` | `0.05` | Two-sided confidence interval width, where ``0.05`` gives 95% intervals. |
| `random_state` | no | `int  or  None` | `None` | Optional random seed for reproducible resampling. |
| `drop_invalid` | no | `bool` | `True` | If True, skip bootstrap rounds that contain only one class. |

### Returns

`pandas.DataFrame` - One-row table with AUC for both models, paired AUC difference, bootstrap confidence interval, requested rounds, valid rounds, dropped rounds, and alpha.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.comparison.mcnemar_test`

Run McNemar's paired test for two classifiers.

**Import path:** `fyron.statistics.comparison.mcnemar_test`

```python
mcnemar_test(y_true: Sequence[Any], pred_a: Sequence[Any], pred_b: Sequence[Any], *, exact: bool = False) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `y_true` | yes | `Sequence[Any]` |  | Ground-truth class labels. |
| `pred_a` | yes | `Sequence[Any]` |  | Predicted class labels from model A. |
| `pred_b` | yes | `Sequence[Any]` |  | Predicted class labels from model B on the same samples. |
| `exact` | no | `bool` | `False` | If True, use the exact binomial version; otherwise use the continuity corrected chi-square approximation. |

### Returns

`pandas.DataFrame` - One-row table with the test name, statistic, p-value, total sample size, discordant-pair counts, and exact-test flag.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.correction.adjust_p_values`

Adjust p-values for multiple testing and return a review table.

**Import path:** `fyron.statistics.correction.adjust_p_values`

```python
adjust_p_values(p_values: Sequence[Any], *, method: PValueCorrectionMethod = 'fdr_bh', alpha: float = 0.05) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `p_values` | yes | `Sequence[Any]` |  | Sequence of raw p-values. Missing values are preserved. |
| `method` | no | `PValueCorrectionMethod` | `'fdr_bh'` | Correction method: ``"fdr_bh"``/Benjamini-Hochberg, ``"bonferroni"``, ``"holm"``, or ``"none"``. |
| `alpha` | no | `float` | `0.05` | Significance level used to compute the rejected flag. |

### Returns

`pandas.DataFrame` - One row per p-value with raw p-value, adjusted p-value, rank, rejected flag, correction method, and alpha.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.correction.p_value_correction_table`

Append adjusted p-values and rejection flags to a result DataFrame.

**Import path:** `fyron.statistics.correction.p_value_correction_table`

```python
p_value_correction_table(df: pd.DataFrame, *, p_col: str = 'p_value', method: PValueCorrectionMethod = 'fdr_bh', alpha: float = 0.05) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Result table containing one raw p-value column, for example a regression, correlation, or feature-screening table. |
| `p_col` | no | `str` | `'p_value'` | Name of the column containing raw p-values. |
| `method` | no | `PValueCorrectionMethod` | `'fdr_bh'` | Multiple-testing correction method. Use ``"fdr_bh"`` for Benjamini-Hochberg FDR, ``"bonferroni"``, ``"holm"``, or ``"none"``. |
| `alpha` | no | `float` | `0.05` | Significance threshold used to compute the ``rejected`` flag. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with ``p_adjusted``, ``p_rank``, ``rejected``, ``p_adjust_method``, and ``alpha`` columns appended.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.effects.cliffs_delta`

Return Cliff's delta for ordinal/non-parametric two-group comparisons.

**Import path:** `fyron.statistics.effects.cliffs_delta`

```python
cliffs_delta(group_a: Sequence[Any], group_b: Sequence[Any]) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `group_a` | yes | `Sequence[Any]` |  | See signature. |
| `group_b` | yes | `Sequence[Any]` |  | See signature. |

### Returns

`float`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.effects.cohens_d`

Return Cohen's d; zero pooled variance produces NaN, not zero effect.

**Import path:** `fyron.statistics.effects.cohens_d`

```python
cohens_d(group_a: Sequence[Any], group_b: Sequence[Any]) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `group_a` | yes | `Sequence[Any]` |  | See signature. |
| `group_b` | yes | `Sequence[Any]` |  | See signature. |

### Returns

`float`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.effects.cramers_v`

Return Cramer's V for a contingency table.

**Import path:** `fyron.statistics.effects.cramers_v`

```python
cramers_v(table: Sequence[Sequence[Any]]) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table` | yes | `Sequence[Sequence[Any]]` |  | See signature. |

### Returns

`float`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.effects.odds_ratio_ci`

Return odds ratio and Wald confidence interval for a 2x2 table.

**Import path:** `fyron.statistics.effects.odds_ratio_ci`

```python
odds_ratio_ci(table: Sequence[Sequence[Any]], *, alpha: float = 0.05, correction: float = 0.5) -> dict[str, float]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table` | yes | `Sequence[Sequence[Any]]` |  | See signature. |
| `alpha` | no | `float` | `0.05` | See signature. |
| `correction` | no | `float` | `0.5` | See signature. |

### Returns

`dict[str, float]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.effects.risk_ratio_ci`

Return risk ratio and Wald confidence interval for a 2x2 table.

**Import path:** `fyron.statistics.effects.risk_ratio_ci`

```python
risk_ratio_ci(table: Sequence[Sequence[Any]], *, alpha: float = 0.05, correction: float = 0.5) -> dict[str, float]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table` | yes | `Sequence[Sequence[Any]]` |  | See signature. |
| `alpha` | no | `float` | `0.05` | See signature. |
| `correction` | no | `float` | `0.5` | See signature. |

### Returns

`dict[str, float]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.effects.standardized_mean_difference`

Return numeric/binary SMD, or NaN when its denominator is zero.

**Import path:** `fyron.statistics.effects.standardized_mean_difference`

```python
standardized_mean_difference(group_a: Sequence[Any], group_b: Sequence[Any], *, categorical: bool = False) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `group_a` | yes | `Sequence[Any]` |  | See signature. |
| `group_b` | yes | `Sequence[Any]` |  | See signature. |
| `categorical` | no | `bool` | `False` | See signature. |

### Returns

`float`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.qc.correlation_pvalue_table`

Return pairwise correlations, p-values, and optional adjusted p-values.

**Import path:** `fyron.statistics.qc.correlation_pvalue_table`

```python
correlation_pvalue_table(df: pd.DataFrame, columns: Sequence[str], *, method: str = 'spearman', p_adjust: str | None = 'fdr_bh') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Analysis table containing numeric variables. |
| `columns` | yes | `Sequence[str]` |  | Variables for pairwise correlation testing. |
| `method` | no | `str` | `'spearman'` | Correlation method, typically ``"spearman"`` or ``"pearson"``. |
| `p_adjust` | no | `str  or  None` | `'fdr_bh'` | Optional multiple-testing correction method. Pass ``None`` to keep only raw p-values. |

### Returns

`pandas.DataFrame` - Pairwise table with variable names, method, correlation coefficient, p-value, sample size, and optional adjusted p-value columns.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.qc.missingness_by_group_table`

Summarize missingness overall and by group for manuscript supplements.

**Import path:** `fyron.statistics.qc.missingness_by_group_table`

```python
missingness_by_group_table(df: pd.DataFrame, *, group_col: str, columns: Sequence[str] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort or feature table to audit. |
| `group_col` | yes | `str` |  | Column defining groups such as cohort, center, split, or endpoint status. |
| `columns` | no | `Sequence[str]  or  None` | `None` | Columns to summarize. If omitted, all columns except ``group_col`` are included. |

### Returns

`pandas.DataFrame` - Long table with variable, group, row count, missing count, and missing percent.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.qc.normality_table`

Run normality tests for multiple columns and return one table.

**Import path:** `fyron.statistics.qc.normality_table`

```python
normality_table(df: pd.DataFrame, columns: Sequence[str], *, method: str = 'shapiro') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Analysis table containing numeric columns to test. |
| `columns` | yes | `Sequence[str]` |  | Column names to test. |
| `method` | no | `str` | `'shapiro'` | Normality test passed to ``normality_test``. The default is ``"shapiro"``. |

### Returns

`pandas.DataFrame` - One row per variable with test name, statistic, p-value, non-missing sample size, and an error column when a test could not be computed.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.qc.outlier_table`

Flag numeric outliers by IQR fences and return one summary row per column.

**Import path:** `fyron.statistics.qc.outlier_table`

```python
outlier_table(df: pd.DataFrame, columns: Sequence[str], *, method: str = 'iqr', iqr_multiplier: float = 1.5) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Analysis table containing numeric variables. |
| `columns` | yes | `Sequence[str]` |  | Numeric columns to inspect. |
| `method` | no | `str` | `'iqr'` | Outlier method. Currently only ``"iqr"`` is supported. |
| `iqr_multiplier` | no | `float` | `1.5` | Multiplier for the IQR fence, commonly ``1.5``. |

### Returns

`pandas.DataFrame` - One row per variable with non-missing count, outlier count, outlier percent, lower fence, and upper fence.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.regression.fit_linear_regression_table`

Fit an ordinary least-squares model and return a manuscript table.

**Import path:** `fyron.statistics.regression.fit_linear_regression_table`

```python
fit_linear_regression_table(df: pd.DataFrame, *, outcome_col: str, covariates: Sequence[str], add_intercept: bool = True, alpha: float = 0.05, p_adjust: str | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Analysis table containing the outcome and covariate columns. |
| `outcome_col` | yes | `str` |  | Numeric continuous outcome column. |
| `covariates` | yes | `Sequence[str]` |  | Predictor columns. Categorical columns are dummy encoded with the first level dropped. |
| `add_intercept` | no | `bool` | `True` | If True, include an intercept row in the model and output table. |
| `alpha` | no | `float` | `0.05` | Two-sided confidence interval width, where ``0.05`` gives 95% intervals. |
| `p_adjust` | no | `str  or  None` | `None` | Optional multiple-testing correction method applied to non-intercept p-values, such as ``"fdr_bh"``, ``"bonferroni"``, or ``"holm"``. |

### Returns

`pandas.DataFrame` - One row per model term with beta estimate, standard error, confidence interval, test statistic, p-value, sample size, model name, outcome, and formula.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.regression.fit_logistic_regression_table`

Fit a binary logistic regression model and return OR/CI/p-value rows.

**Import path:** `fyron.statistics.regression.fit_logistic_regression_table`

```python
fit_logistic_regression_table(df: pd.DataFrame, *, outcome_col: str, covariates: Sequence[str], add_intercept: bool = True, alpha: float = 0.05, p_adjust: str | None = None, max_iter: int = 1000) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Analysis table containing a binary outcome and covariate columns. |
| `outcome_col` | yes | `str` |  | Binary outcome column coded as ``0`` and ``1``. |
| `covariates` | yes | `Sequence[str]` |  | Predictor columns. Categorical columns are dummy encoded with the first level dropped. |
| `add_intercept` | no | `bool` | `True` | If True, include an intercept row in the model and output table. |
| `alpha` | no | `float` | `0.05` | Two-sided confidence interval width, where ``0.05`` gives 95% intervals. |
| `p_adjust` | no | `str  or  None` | `None` | Optional multiple-testing correction method applied to non-intercept p-values. |
| `max_iter` | no | `int` | `1000` | Maximum optimizer iterations for the logistic likelihood fit. |

### Returns

`pandas.DataFrame` - One row per model term with odds ratio, log-odds estimate, standard error, confidence interval, z statistic, p-value, sample size, model name, outcome, and formula.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.regression.vif_table`

Return variance inflation factors for covariates after dummy encoding.

**Import path:** `fyron.statistics.regression.vif_table`

```python
vif_table(df: pd.DataFrame, covariates: Sequence[str]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Analysis table containing the covariate columns. |
| `covariates` | yes | `Sequence[str]` |  | Predictor columns to inspect for multicollinearity. Categorical columns are dummy encoded before VIF calculation. |

### Returns

`pandas.DataFrame` - Table with one row per encoded term and columns ``term``, ``vif``, and ``n``.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.tests.StatisticalTestResult`

Named result returned by Fyron statistical tests.

**Import path:** `fyron.statistics.tests.StatisticalTestResult`

```python
StatisticalTestResult()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

### Public Methods

#### `fyron.statistics.tests.StatisticalTestResult.to_dict`

See the signature and linked module guide for context.

**Import path:** `fyron.statistics.tests.StatisticalTestResult.to_dict`

```python
StatisticalTestResult.to_dict(self) -> dict[str, Any]
```

#### Parameters

No parameters documented.

#### Returns

`dict[str, Any]`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.tests.categorical_test`

Run a chi-square or Fisher exact test on a contingency table.

**Import path:** `fyron.statistics.tests.categorical_test`

```python
categorical_test(table: Sequence[Sequence[Any]], *, method: CategoricalMethod = 'auto') -> StatisticalTestResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table` | yes | `Sequence[Sequence[Any]]` |  | See signature. |
| `method` | no | `CategoricalMethod` | `'auto'` | See signature. |

### Returns

`StatisticalTestResult`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.tests.compare_multiple_groups`

Compare three or more numeric groups with ANOVA or Kruskal-Wallis.

**Import path:** `fyron.statistics.tests.compare_multiple_groups`

```python
compare_multiple_groups(groups: Sequence[Sequence[Any]], *, method: MultiGroupMethod = 'auto') -> StatisticalTestResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `groups` | yes | `Sequence[Sequence[Any]]` |  | See signature. |
| `method` | no | `MultiGroupMethod` | `'auto'` | See signature. |

### Returns

`StatisticalTestResult`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.tests.compare_two_groups`

Compare two numeric groups.

**Import path:** `fyron.statistics.tests.compare_two_groups`

```python
compare_two_groups(group_a: Sequence[Any], group_b: Sequence[Any], *, paired: bool = False, method: TwoGroupMethod = 'auto', alternative: Alternative = 'two-sided', equal_var: bool = False) -> StatisticalTestResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `group_a` | yes | `Sequence[Any]` |  | See signature. |
| `group_b` | yes | `Sequence[Any]` |  | See signature. |
| `paired` | no | `bool` | `False` | See signature. |
| `method` | no | `TwoGroupMethod` | `'auto'` | See signature. |
| `alternative` | no | `Alternative` | `'two-sided'` | See signature. |
| `equal_var` | no | `bool` | `False` | See signature. |

### Returns

`StatisticalTestResult`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.tests.correlation_test`

Test association between two numeric variables.

**Import path:** `fyron.statistics.tests.correlation_test`

```python
correlation_test(x: Sequence[Any], y: Sequence[Any], *, method: CorrelationMethod = 'spearman', alternative: Alternative = 'two-sided') -> StatisticalTestResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `x` | yes | `Sequence[Any]` |  | See signature. |
| `y` | yes | `Sequence[Any]` |  | See signature. |
| `method` | no | `CorrelationMethod` | `'spearman'` | See signature. |
| `alternative` | no | `Alternative` | `'two-sided'` | See signature. |

### Returns

`StatisticalTestResult`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).

## `fyron.statistics.tests.normality_test`

Test whether a numeric vector is compatible with a normal distribution.

**Import path:** `fyron.statistics.tests.normality_test`

```python
normality_test(values: Sequence[Any], *, method: Literal['shapiro', 'normaltest'] = 'shapiro') -> StatisticalTestResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `values` | yes | `Sequence[Any]` |  | See signature. |
| `method` | no | `Literal['shapiro', 'normaltest']` | `'shapiro'` | See signature. |

### Returns

`StatisticalTestResult`

**See also:** [Cohort And Analysis module guide](../modules/cohort.md).
