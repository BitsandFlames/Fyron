# Survival Reference

Kaplan-Meier curves, RMST, Cox models, proportional hazards diagnostics, AFT models, and survival boosting.

For workflow context, see [Survival module guide](../modules/survival.md).

## Functions And Classes

- [`fyron.survival.boosting.train_gradient_survival_boosting`](#fyronsurvivalboostingtraingradientsurvivalboosting)
- [`fyron.survival.cox.fit_multivariate_cox`](#fyronsurvivalcoxfitmultivariatecox)
- [`fyron.survival.cox.fit_univariate_cox`](#fyronsurvivalcoxfitunivariatecox)
- [`fyron.survival.groups.create_survival_groups`](#fyronsurvivalgroupscreatesurvivalgroups)
- [`fyron.survival.groups.default_tau_from_observed_times`](#fyronsurvivalgroupsdefaulttaufromobservedtimes)
- [`fyron.survival.kaplan_meier.KaplanMeierPlotResult`](#fyronsurvivalkaplanmeierkaplanmeierplotresult)
- [`fyron.survival.kaplan_meier.plot_kaplan_meier`](#fyronsurvivalkaplanmeierplotkaplanmeier)
- [`fyron.survival.outputs.cox_forest_table`](#fyronsurvivaloutputscoxforesttable)
- [`fyron.survival.outputs.survival_prediction_table`](#fyronsurvivaloutputssurvivalpredictiontable)
- [`fyron.survival.ph_diagnostics.check_ph_assumptions`](#fyronsurvivalphdiagnosticscheckphassumptions)
- [`fyron.survival.ph_diagnostics.plot_schoenfeld_residuals`](#fyronsurvivalphdiagnosticsplotschoenfeldresiduals)
- [`fyron.survival.ph_diagnostics.schoenfeld_residuals_table`](#fyronsurvivalphdiagnosticsschoenfeldresidualstable)
- [`fyron.survival.ph_diagnostics.schoenfeld_test_table`](#fyronsurvivalphdiagnosticsschoenfeldtesttable)
- [`fyron.survival.rmst.calculate_rmst`](#fyronsurvivalrmstcalculatermst)
- [`fyron.survival.rmst.compare_rmst`](#fyronsurvivalrmstcomparermst)
- [`fyron.survival.time_varying.expand_time_interaction_dataframe`](#fyronsurvivaltimevaryingexpandtimeinteractiondataframe)
- [`fyron.survival.time_varying.fit_cox_time_interactions`](#fyronsurvivaltimevaryingfitcoxtimeinteractions)
- [`fyron.survival.time_varying.fit_time_varying_cox`](#fyronsurvivaltimevaryingfittimevaryingcox)
- [`fyron.survival.time_varying.run_survival_sensitivity_analysis`](#fyronsurvivaltimevaryingrunsurvivalsensitivityanalysis)
- [`fyron.survival.weibull_aft.fit_weibull_aft`](#fyronsurvivalweibullaftfitweibullaft)
- [`fyron.survival.weibull_aft.plot_aft_survival_curves`](#fyronsurvivalweibullaftplotaftsurvivalcurves)

## `fyron.survival.boosting.train_gradient_survival_boosting`

Train a gradient boosting survival model.

**Import path:** `fyron.survival.boosting.train_gradient_survival_boosting`

```python
train_gradient_survival_boosting(X_train: ArrayLikeInput, duration_train: ArrayLike, event_train: ArrayLike, X_test: ArrayLikeInput | None = None, duration_test: ArrayLike | None = None, event_test: ArrayLike | None = None, *, random_state: int = 42, **model_params: Any) -> SurvivalBoostingResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `X_train` | yes | `ArrayLikeInput` |  | Feature matrix. |
| `duration_train` | yes | `ArrayLike` |  | See signature. |
| `event_train` | yes | `ArrayLike` |  | Survival time and event indicator for the training set. |
| `X_test` | no | `ArrayLikeInput  or  None` | `None` | See signature. |
| `duration_test` | no | `ArrayLike  or  None` | `None` | See signature. |
| `event_test` | no | `ArrayLike  or  None` | `None` | Optional held-out data. When supplied, the returned risk scores and concordance index are computed on this set; otherwise in-sample scores are returned. |
| `random_state` | no | `int` | `42` | Random seed passed to the estimator. **model_params Additional parameters passed to ``GradientBoostingSurvivalAnalysis``. |
| `model_params` | yes | `Any` |  | See signature. |

### Returns

`dict` - ``model``, ``risk_score``, ``concordance_index``, ``train_concordance_index``, and the structured survival arrays used for fitting/evaluation.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.cox.fit_multivariate_cox`

Fit a multivariate Cox model.

**Import path:** `fyron.survival.cox.fit_multivariate_cox`

```python
fit_multivariate_cox(df: pd.DataFrame, duration_col: str, event_col: str, *, covariates: Sequence[str] | None = None, formula: str | None = None, strata: str | Sequence[str] | None = None, robust: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `covariates` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `formula` | no | `str  or  None` | `None` | See signature. |
| `strata` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `robust` | no | `bool` | `False` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.cox.fit_univariate_cox`

Fit separate univariate Cox models for one or more covariates.

**Import path:** `fyron.survival.cox.fit_univariate_cox`

```python
fit_univariate_cox(df: pd.DataFrame, duration_col: str, event_col: str, covariates: str | Sequence[str], *, strata: str | Sequence[str] | None = None, robust: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Survival dataset. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | Follow-up time and event indicator (1 = event). |
| `covariates` | yes | `str  or  Sequence[str]` |  | Column name(s) modeled one at a time (each produces its own fit). |
| `strata` | no | `str  or  Sequence[str]  or  None` | `None` | Passed through to ``lifelines.CoxPHFitter.fit``. |
| `robust` | no | `bool` | `False` | If True, use robust sandwich errors (cluster-robust when combined with ``cluster_col`` in lifelines). |

### Returns

`dict` - ``results`` — stacked summary table with ``model`` identifying the covariate used; ``fitters`` — list of fitted ``CoxPHFitter`` objects in the same order; ``n_excluded`` / ``n_used`` per fit (included as columns ``n_excluded``, ``n_used`` on each slice).

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.groups.create_survival_groups`

Add a survival/stratification group column to a copy of ``df``.

**Import path:** `fyron.survival.groups.create_survival_groups`

```python
create_survival_groups(df: pd.DataFrame, column: str, method: SplitMethod, group_col: str, *, bins: int | Sequence[float] | None = None, labels: Sequence[str] | bool | None = None, duplicates: Literal['raise', 'drop'] = 'drop') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input table. |
| `column` | yes | `str` |  | Column used to derive groups (categorical levels or numeric for splits). |
| `method` | yes | `SplitMethod` |  | ``"categorical"`` copies stringified levels from ``column``. ``"median"``, ``"tertile"``, and ``"quartile"`` use ``pandas.qcut``. ``"custom"`` uses ``pandas.cut`` with ``bins`` (required). |
| `group_col` | yes | `str` |  | Name of the new column to create. |
| `bins` | no | `int  or  Sequence[float]  or  None` | `None` | For ``method="custom"``: edges passed to ``pandas.cut`` (sequence of bin edges or an integer number of equal-width bins). Ignored for quantile methods unless you rely on ``pandas`` defaults for integer ``bins`` with ``cut`` (not used here). |
| `labels` | no | `Sequence[str]  or  bool  or  None` | `None` | Optional labels for ``qcut``/``cut`` groups. Must match the number of resulting bins. |
| `duplicates` | no | `Literal['raise', 'drop']` | `'drop'` | Quantile method duplicate policy. ``"drop"`` matches ``pandas.qcut``; ``"raise"`` surfaces ``ValueError`` when quantiles are not distinct. |

### Returns

`pandas.DataFrame` - A **copy** of ``df`` including ``group_col``.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.groups.default_tau_from_observed_times`

Default RMST truncation: minimum of per-group maximum observed times.

**Import path:** `fyron.survival.groups.default_tau_from_observed_times`

```python
default_tau_from_observed_times(df: pd.DataFrame, duration_col: str, group_col: str | None = None) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |

### Returns

`float`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.kaplan_meier.KaplanMeierPlotResult`

Outputs from :func:`plot_kaplan_meier`.

**Import path:** `fyron.survival.kaplan_meier.KaplanMeierPlotResult`

```python
KaplanMeierPlotResult()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.kaplan_meier.plot_kaplan_meier`

Fit Kaplan–Meier curves, optionally compare groups, and plot.

**Import path:** `fyron.survival.kaplan_meier.plot_kaplan_meier`

```python
plot_kaplan_meier(df: pd.DataFrame, duration_col: str, event_col: str, group_col: str | None = None, *, split_column: str | None = None, split_method: SplitMethod | None = None, split_bins: int | Sequence[float] | None = None, split_labels: Sequence[str] | bool | None = None, confidence_interval: bool = True, ci_alpha: float = 0.05, at_risk_counts: bool = False, at_risk_rows: Literal['all', 'at_risk', 'censored', 'events'] | Sequence[str] = 'all', show_censors: bool = False, censor_styles: Mapping[str, Any] | None = None, xlim: tuple[float, float] | None = None, reference_bands: Any | None = None, reference_band_time_col: str = 'time', reference_band_lower_col: str = 'lower', reference_band_upper_col: str = 'upper', reference_band_label_col: str = 'band', reference_band_preset: Literal['survival', 'risk', 'percentile'] | None = None, reference_band_order: Sequence[str] | None = None, reference_band_colors: Mapping[str, str] | Sequence[str] | None = None, reference_band_alpha: float = 0.22, reference_band_legend: bool = True, annotate_logrank: bool = False, palette: str | Sequence[str] | None = None, colors: Mapping[str, str] | Sequence[str] | None = None, linestyles: str | Sequence[str] | None = None, title: str | None = None, xlabel: str | None = None, ylabel: str = 'Survival probability', legend_title: str | None = None, legend_kwargs: MutableMapping[str, Any] | None = None, figsize: tuple[float, float] | None = None, save_path: str | Path | None = None, save_format: Literal['png', 'pdf', 'svg'] | None = None, dpi: int | None = None, annotate_rmst: bool = False, rmst_tau: float | None = None, rmst_group_col: str | None = None) -> KaplanMeierPlotResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Survival dataset. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | Follow-up time and event indicator (1 = event, 0 = censored). |
| `group_col` | no | `str  or  None` | `None` | Optional categorical column defining cohorts. |
| `split_column` | no | `str  or  None` | `None` | See signature. |
| `split_method` | no | `SplitMethod  or  None` | `None` | See signature. |
| `split_bins` | no | `int  or  Sequence[float]  or  None` | `None` | See signature. |
| `split_labels` | no | `Sequence[str]  or  bool  or  None` | `None` | When ``split_column`` is set, groups are created with :func:`fyron.survival.create_survival_groups` into a temporary column (``split_method`` must be ``"median"``, ``"tertile"``, ``"quartile"``, or ``"custom"`` with ``split_bins`` for custom edges). |
| `confidence_interval` | no | `bool` | `True` | If True, shaded pointwise intervals are drawn. |
| `ci_alpha` | no | `float` | `0.05` | See signature. |
| `at_risk_counts` | no | `bool` | `False` | If True, lifelines' at-risk table is drawn under the x-axis. |
| `at_risk_rows` | no | `Literal['all', 'at_risk', 'censored', 'events']  or  Sequence[str]` | `'all'` | Rows to show when ``at_risk_counts=True``. Use ``"all"`` for lifelines' default rows (at risk, censored, events) or ``"at_risk"`` to show only the at-risk row. A custom sequence can contain ``"at_risk"``, ``"censored"``, and ``"events"`` aliases, or lifelines row labels such as ``"At risk"``, ``"Censored"``, and ``"Events"``. Sequence order is preserved in the rendered table. |
| `show_censors` | no | `bool` | `False` | If True, censor marks are drawn on the survival curves. |
| `censor_styles` | no | `Mapping[str, Any]  or  None` | `None` | See signature. |
| `xlim` | no | `tuple[float, float]  or  None` | `None` | Optional x-axis limits. |
| `reference_bands` | no | `Any  or  None` | `None` | Optional long-form table with precomputed survival reference intervals. |
| `reference_band_time_col` | no | `str` | `'time'` | Time column in ``reference_bands``. |
| `reference_band_lower_col` | no | `str` | `'lower'` | Lower survival probability bound in ``reference_bands``. |
| `reference_band_upper_col` | no | `str` | `'upper'` | Upper survival probability bound in ``reference_bands``. |
| `reference_band_label_col` | no | `str` | `'band'` | Band label column in ``reference_bands``. |
| `reference_band_preset` | no | `Literal['survival', 'risk', 'percentile']  or  None` | `None` | Optional named preset for common survival band labels and colors: ``"survival"``, ``"risk"``, or ``"percentile"``. |
| `reference_band_order` | no | `Sequence[str]  or  None` | `None` | Optional explicit order for drawing reference bands and legend entries. |
| `reference_band_colors` | no | `Mapping[str, str]  or  Sequence[str]  or  None` | `None` | Optional mapping from band label to color, or a color sequence matching ``reference_band_order``. |
| `reference_band_alpha` | no | `float` | `0.22` | Transparency used for reference bands. |
| `reference_band_legend` | no | `bool` | `True` | If True, include reference-band entries in the KM legend. |
| `annotate_logrank` | no | `bool` | `False` | If True, annotate the plot with the log-rank p-value when groups are present. |
| `palette` | no | `str  or  Sequence[str]  or  None` | `None` | Named Fyron palette or explicit colors used when ``colors`` is not supplied. |
| `colors` | no | `Mapping[str, str]  or  Sequence[str]  or  None` | `None` | Per-group colors as a dict ``{label: color}`` or a list applied in sorted label order. |
| `linestyles` | no | `str  or  Sequence[str]  or  None` | `None` | Matplotlib linestyle or one linestyle per sorted group label. |
| `title` | no | `str  or  None` | `None` | See signature. |
| `xlabel` | no | `str  or  None` | `None` | See signature. |
| `ylabel` | no | `str` | `'Survival probability'` | See signature. |
| `legend_title` | no | `str  or  None` | `None` | See signature. |
| `legend_kwargs` | no | `MutableMapping[str, Any]  or  None` | `None` | See signature. |
| `figsize` | no | `tuple[float, float]  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `save_format` | no | `Literal['png', 'pdf', 'svg']  or  None` | `None` | See signature. |
| `dpi` | no | `int  or  None` | `None` | See signature. |
| `annotate_rmst` | no | `bool` | `False` | If True, draw a vertical line at ``rmst_tau`` (default from data) and annotate RMST. |
| `rmst_tau` | no | `float  or  None` | `None` | Truncation time for RMST text; defaults to :func:`fyron.survival.default_tau_from_observed_times`. |
| `rmst_group_col` | no | `str  or  None` | `None` | Group column passed to RMST helper when annotating (defaults to effective group column). |

### Returns

`KaplanMeierPlotResult`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.outputs.cox_forest_table`

Extract hazard ratios and confidence intervals for forest plots.

**Import path:** `fyron.survival.outputs.cox_forest_table`

```python
cox_forest_table(cox_result: Any, *, covariate_col: str = 'covariate') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cox_result` | yes | `Any` |  | Output from ``fit_multivariate_cox`` / ``fit_univariate_cox``, a lifelines ``CoxPHFitter``, or a DataFrame with Cox summary columns. |
| `covariate_col` | no | `str` | `'covariate'` | Name for the covariate column in the returned table. |

### Returns

`pandas.DataFrame` - Columns include covariate, hazard ratio, confidence interval, p-value, and a formatted label.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.outputs.survival_prediction_table`

Create fixed-time survival/risk predictions for supported survival models.

**Import path:** `fyron.survival.outputs.survival_prediction_table`

```python
survival_prediction_table(model: Any, df: pd.DataFrame, times: Sequence[float], *, id_col: str | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `model` | yes | `Any` |  | Fitted model with ``predict_survival_function`` support. |
| `df` | yes | `pd.DataFrame` |  | Feature rows to score. |
| `times` | yes | `Sequence[float]` |  | Positive time horizons. |
| `id_col` | no | `str  or  None` | `None` | Optional identifier column copied into the output. |

### Returns

`pandas.DataFrame` - Long table with one row per input row and time horizon.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.ph_diagnostics.check_ph_assumptions`

Schoenfeld-based proportional hazards diagnostics.

**Import path:** `fyron.survival.ph_diagnostics.check_ph_assumptions`

```python
check_ph_assumptions(training_df: pd.DataFrame, fitter: CoxPHFitter, *, p_value_threshold: float = 0.05, show_plots: bool = False, columns: Sequence[str] | None = None, advice: bool = False, p_adjust: str | None = 'fdr_bh', include_residuals: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `training_df` | yes | `pd.DataFrame` |  | The same (or row-aligned) dataframe used in ``fitter.fit``. |
| `fitter` | yes | `CoxPHFitter` |  | A fitted ``CoxPHFitter``. |
| `p_value_threshold` | no | `float` | `0.05` | Flag covariates whose minimum adjusted p-value across time transforms falls below this level (raw p-values when adjustment is disabled). |
| `show_plots` | no | `bool` | `False` | If True, scaled Schoenfeld residual plots are produced (can be slow). |
| `columns` | no | `Sequence[str]  or  None` | `None` | Optional subset of covariates to summarize. |
| `advice` | no | `bool` | `False` | Forwarded to lifelines ``check_assumptions`` when ``show_plots`` is True (verbose console advice). |
| `p_adjust` | no | `str  or  None` | `'fdr_bh'` | Multiple-testing correction for the test table and violation flags. Lifelines' optional diagnostic plots/advice use its raw-test convention. |
| `include_residuals` | no | `bool` | `False` | See signature. |

### Returns

`dict` - ``summary`` — long-form test table; ``violations`` — covariates failing the threshold; ``warnings`` / ``suggestions`` — narrative guidance.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.ph_diagnostics.plot_schoenfeld_residuals`

Plot Schoenfeld residuals for selected covariates.

**Import path:** `fyron.survival.ph_diagnostics.plot_schoenfeld_residuals`

```python
plot_schoenfeld_residuals(residuals: pd.DataFrame, *, covariates: Sequence[str] | None = None, time_col: str = 'time', residual_col: str = 'residual', covariate_col: str = 'covariate', title: str = 'Schoenfeld residuals', ax: Any | None = None, save_path: str | Path | None = None, fmt: str = 'png') -> PlotReturn
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `residuals` | yes | `pd.DataFrame` |  | See signature. |
| `covariates` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `time_col` | no | `str` | `'time'` | See signature. |
| `residual_col` | no | `str` | `'residual'` | See signature. |
| `covariate_col` | no | `str` | `'covariate'` | See signature. |
| `title` | no | `str` | `'Schoenfeld residuals'` | See signature. |
| `ax` | no | `Any  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |
| `fmt` | no | `str` | `'png'` | See signature. |

### Returns

`PlotReturn`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.ph_diagnostics.schoenfeld_residuals_table`

Return Schoenfeld residuals in long tabular form.

**Import path:** `fyron.survival.ph_diagnostics.schoenfeld_residuals_table`

```python
schoenfeld_residuals_table(fitter: CoxPHFitter, training_df: pd.DataFrame, *, scaled: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `fitter` | yes | `CoxPHFitter` |  | Fitted lifelines ``CoxPHFitter``. |
| `training_df` | yes | `pd.DataFrame` |  | Row-aligned DataFrame used for fitting. |
| `scaled` | no | `bool` | `True` | If True, use scaled Schoenfeld residuals; otherwise raw residuals. |

### Returns

`pandas.DataFrame` - Long table with event row index, covariate, residual, and event time.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.ph_diagnostics.schoenfeld_test_table`

Run Schoenfeld proportional-hazards tests and return a clean table.

**Import path:** `fyron.survival.ph_diagnostics.schoenfeld_test_table`

```python
schoenfeld_test_table(fitter: CoxPHFitter, training_df: pd.DataFrame, *, method: str | Sequence[str] = 'rank', p_adjust: str | None = 'fdr_bh', alpha: float = 0.05) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `fitter` | yes | `CoxPHFitter` |  | See signature. |
| `training_df` | yes | `pd.DataFrame` |  | See signature. |
| `method` | no | `str  or  Sequence[str]` | `'rank'` | See signature. |
| `p_adjust` | no | `str  or  None` | `'fdr_bh'` | See signature. |
| `alpha` | no | `float` | `0.05` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.rmst.calculate_rmst`

Compute RMST at truncation ``tau`` using Kaplan–Meier integration.

**Import path:** `fyron.survival.rmst.calculate_rmst`

```python
calculate_rmst(df: pd.DataFrame, duration_col: str, event_col: str, *, group_col: str | None = None, tau: float | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Survival data. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | Time and event columns (1 = event, 0 = censored). |
| `group_col` | no | `str  or  None` | `None` | Optional categorical column; one RMST row per level plus ``n`` counts. |
| `tau` | no | `float  or  None` | `None` | Upper integration limit. Must be finite and positive. Beyond observed follow-up, the final KM survival level is continued unchanged. |

### Returns

`pandas.DataFrame` - Columns: ``group``, ``n``, ``rmst``, ``rmst_se``, ``rmst_lower``, ``rmst_upper``, ``tau``. Standard errors use the Greenwood-based variance of the RMST estimator. Normal-based 95% intervals use the 0.975 standard normal quantile.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.rmst.compare_rmst`

Pairwise RMST differences versus a reference group.

**Import path:** `fyron.survival.rmst.compare_rmst`

```python
compare_rmst(df: pd.DataFrame, duration_col: str, event_col: str, group_col: str, reference: str, *, tau: float | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `group_col` | yes | `str` |  | Same conventions as :func:`calculate_rmst`. |
| `reference` | yes | `str` |  | Reference level of ``group_col`` (string-coerced). |
| `tau` | no | `float  or  None` | `None` | Truncation time; defaults like :func:`calculate_rmst`. |

### Returns

`pandas.DataFrame` - Columns include ``group``, ``reference``, ``rmst_group``, ``rmst_reference``, ``difference``, ``diff_lower``, ``diff_upper``, ``p_value``, ``tau``.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.time_varying.expand_time_interaction_dataframe`

Expand data with piecewise-constant interactions at common interval ends.

**Import path:** `fyron.survival.time_varying.expand_time_interaction_dataframe`

```python
expand_time_interaction_dataframe(df: pd.DataFrame, duration_col: str, event_col: str, *, covariates: Sequence[str], time_interaction_covariates: Sequence[str], time_transform: TimeTransform = 'log', n_intervals: int = 8, breakpoints: Sequence[float] | None = None, id_col: str | None = None, start_col: str = 'start', stop_col: str = 'stop') -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `covariates` | yes | `Sequence[str]` |  | See signature. |
| `time_interaction_covariates` | yes | `Sequence[str]` |  | See signature. |
| `time_transform` | no | `TimeTransform` | `'log'` | See signature. |
| `n_intervals` | no | `int` | `8` | See signature. |
| `breakpoints` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `start_col` | no | `str` | `'start'` | See signature. |
| `stop_col` | no | `str` | `'stop'` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.time_varying.fit_cox_time_interactions`

Fit a Cox model with generated covariate-by-time interaction terms.

**Import path:** `fyron.survival.time_varying.fit_cox_time_interactions`

```python
fit_cox_time_interactions(df: pd.DataFrame, duration_col: str, event_col: str, *, covariates: Sequence[str], time_interaction_covariates: Sequence[str] | None = None, time_transform: TimeTransform = 'log', n_intervals: int = 8, breakpoints: Sequence[float] | None = None, id_col: str | None = None, strata: str | Sequence[str] | None = None, robust: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `covariates` | yes | `Sequence[str]` |  | See signature. |
| `time_interaction_covariates` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `time_transform` | no | `TimeTransform` | `'log'` | See signature. |
| `n_intervals` | no | `int` | `8` | See signature. |
| `breakpoints` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `strata` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `robust` | no | `bool` | `False` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.time_varying.fit_time_varying_cox`

Fit a Cox model for long-format start-stop survival data.

**Import path:** `fyron.survival.time_varying.fit_time_varying_cox`

```python
fit_time_varying_cox(df: pd.DataFrame, event_col: str, *, start_col: str = 'start', stop_col: str = 'stop', id_col: str | None = None, covariates: Sequence[str] | None = None, formula: str | None = None, strata: str | Sequence[str] | None = None, robust: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Long-format survival data with one row per time interval. |
| `event_col` | yes | `str` |  | Event indicator column, where 1 means the event occurred at interval end. |
| `start_col` | no | `str` | `'start'` | See signature. |
| `stop_col` | no | `str` | `'stop'` | Interval start and stop time columns. Every row must satisfy start < stop. |
| `id_col` | no | `str  or  None` | `None` | Optional subject identifier column used by lifelines. |
| `covariates` | no | `Sequence[str]  or  None` | `None` | Covariate column names joined into a formula. |
| `formula` | no | `str  or  None` | `None` | Lifelines formula string. Pass either this or ``covariates``. |
| `strata` | no | `str  or  Sequence[str]  or  None` | `None` | Optional strata passed to ``CoxTimeVaryingFitter.fit``. |
| `robust` | no | `bool` | `False` | Whether to request robust variance estimates from lifelines. |

### Returns

`dict` - ``results`` table, fitted ``fitter``, ``n_used``, ``formula_used``, and ``concordance_index`` when lifelines exposes it.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.time_varying.run_survival_sensitivity_analysis`

Run Cox PH diagnostics and sensitivity models for PH concerns.

**Import path:** `fyron.survival.time_varying.run_survival_sensitivity_analysis`

```python
run_survival_sensitivity_analysis(df: pd.DataFrame, duration_col: str, event_col: str, *, covariates: Sequence[str] | None = None, formula: str | None = None, group_col: str | None = None, rmst_tau: float | None = None, ph_p_value_threshold: float = 0.05, time_interaction_covariates: Sequence[str] | None = None, time_transform: TimeTransform = 'log', n_intervals: int = 8, breakpoints: Sequence[float] | None = None, fit_time_interactions: bool = True, fit_aft: bool = True, fit_rmst: bool = True) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | See signature. |
| `covariates` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `formula` | no | `str  or  None` | `None` | See signature. |
| `group_col` | no | `str  or  None` | `None` | See signature. |
| `rmst_tau` | no | `float  or  None` | `None` | See signature. |
| `ph_p_value_threshold` | no | `float` | `0.05` | See signature. |
| `time_interaction_covariates` | no | `Sequence[str]  or  None` | `None` | See signature. |
| `time_transform` | no | `TimeTransform` | `'log'` | See signature. |
| `n_intervals` | no | `int` | `8` | See signature. |
| `breakpoints` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `fit_time_interactions` | no | `bool` | `True` | See signature. |
| `fit_aft` | no | `bool` | `True` | See signature. |
| `fit_rmst` | no | `bool` | `True` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.weibull_aft.fit_weibull_aft`

Fit a Weibull AFT model with ``lifelines.WeibullAFTFitter``.

**Import path:** `fyron.survival.weibull_aft.fit_weibull_aft`

```python
fit_weibull_aft(df: pd.DataFrame, duration_col: str, event_col: str, *, covariates: Sequence[str] | None = None, formula: str | None = None, robust: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `duration_col` | yes | `str` |  | See signature. |
| `event_col` | yes | `str` |  | Survival data. |
| `covariates` | no | `Sequence[str]  or  None` | `None` | List of column names joined into a formula. |
| `formula` | no | `str  or  None` | `None` | Patsy-like lifelines formula string. |
| `robust` | no | `bool` | `False` | Passed through to ``fit`` when supported. |

### Returns

`dict` - ``results`` — coefficient table; ``fitter``; ``AIC``; ``concordance_index`` (if available); ``n_excluded`` / ``n_used`` and ``training_df`` with the exact fitting rows and original index. Formula-specific missing predictors are excluded; unrelated missing columns do not affect the fitting cohort.

**See also:** [Survival module guide](../modules/survival.md).

## `fyron.survival.weibull_aft.plot_aft_survival_curves`

Plot predicted survival curves for covariate profiles (partial effects).

**Import path:** `fyron.survival.weibull_aft.plot_aft_survival_curves`

```python
plot_aft_survival_curves(fitter: WeibullAFTFitter, covariates: str | Sequence[str], profiles: Sequence[Mapping[str, float]], *, plot_baseline: bool = True, figsize: tuple[float, float] | None = None, ax: plt.Axes | None = None, plot_kwargs: MutableMapping[str, Any] | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `fitter` | yes | `WeibullAFTFitter` |  | Fitted ``WeibullAFTFitter``. |
| `covariates` | yes | `str  or  Sequence[str]` |  | Names to vary (order must match each profile mapping). |
| `profiles` | yes | `Sequence[Mapping[str, float]]` |  | Iterable of dicts mapping covariate name to numeric level. |
| `plot_baseline` | no | `bool` | `True` | Include the baseline curve at central values. |
| `figsize` | no | `tuple[float, float]  or  None` | `None` | Used when ``ax`` is not provided. |
| `ax` | no | `plt.Axes  or  None` | `None` | Optional matplotlib axes. |
| `plot_kwargs` | no | `MutableMapping[str, Any]  or  None` | `None` | Extra kwargs forwarded to ``plot_partial_effects_on_outcome``. |

### Returns

`dict` - ``figure``, ``axes``, ``fitter``.

**See also:** [Survival module guide](../modules/survival.md).
