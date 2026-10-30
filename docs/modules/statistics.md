# Statistics

## Inference Corrections

Paired t-tests and Wilcoxon tests filter missing/non-finite observations jointly,
preserving patient pairs. Selecting a paired method implies paired metadata and
sample counts. Original lengths must agree; conflicting paired/independent
options are rejected. Recompute older paired analyses with asymmetric missingness.

Regression inference requires a finite, full-column-rank design. Redundant
predictors raise `ValueError` instead of receiving misleading coefficient tests.
Logistic outcomes must be exactly `0` and `1`, with both classes present; fractional
outcomes are rejected. Complete separation and non-identifiable information
matrices cannot produce ordinary Wald inference. Confidence levels require
`0 < alpha < 1`. OLS uses a stable design pseudoinverse for covariance after
checking full rank.

Zero-denominator Cohen's d and SMD values are `NaN`, not evidence of balance.
Statistical test result objects represent undefined effect sizes as `None`;
descriptive tables preserve undefined SMDs. Reassess earlier constant-group
effect sizes and regression tables with redundant predictors or invalid outcomes.

`fyron.statistics` provides small, explicit statistical helpers for clinical data science. It includes common hypothesis tests, multiple-testing correction, manuscript regression tables, correlation and missingness QC, paired model-comparison tests, and bootstrap confidence intervals for scores and model metrics.

The goal is not to hide analysis choices. Fyron makes the test name, statistic, p-value, sample size, and bootstrap settings visible so results can be inspected and reported clearly.

## Install

```bash
uv add "fyron[statistics]"
```

## Imports

```python
from fyron import statistics as fst
```

## API Contract

Numeric samples and correlation inputs must be one-dimensional; multidimensional inputs are not flattened into additional observations. Contingency tables require finite, nonnegative integer counts. Fractional counts are rejected before Fisher or chi-square testing.

| Topic | Contract |
| --- | --- |
| Input shape | Arrays for simple tests; DataFrames for manuscript regression, correction, missingness, correlation, and QC tables. |
| Required columns | Outcome, covariate, p-value, group, or metric columns named in the call must exist. |
| Return shape | `StatisticalTestResult`, `BootstrapResult`, or `pandas.DataFrame` with estimates, p-values, CIs, and correction metadata. |
| Saved artifacts | Export test tables, adjusted p-value tables, regression tables, bootstrap summaries, and QC tables. |
| Failure modes | Missing optional `statsmodels`/SciPy support, invalid p-values, nonnumeric inputs, singular models, empty groups, or incompatible paired arrays. |

## Function Summary

| Function | Use When | Returns |
| --- | --- | --- |
| `normality_test` | Checking whether a numeric vector is compatible with normality | `StatisticalTestResult` |
| `compare_two_groups` | Comparing two numeric groups | `StatisticalTestResult` |
| `compare_multiple_groups` | Comparing three or more numeric groups | `StatisticalTestResult` |
| `categorical_test` | Testing a contingency table | `StatisticalTestResult` |
| `correlation_test` | Testing association between two variables | `StatisticalTestResult` |
| `adjust_p_values` | Correcting a vector of p-values | DataFrame |
| `p_value_correction_table` | Adding adjusted p-values to a result table | DataFrame |
| `fit_logistic_regression_table` | Paper-ready odds-ratio table for binary endpoints | DataFrame |
| `fit_linear_regression_table` | Paper-ready beta/CI table for continuous endpoints | DataFrame |
| `vif_table` | Multicollinearity checks for regression covariates | DataFrame |
| `mcnemar_test` | Paired comparison of two classifiers | DataFrame |
| `bootstrap_auc_difference` | Paired bootstrap CI for AUC difference | DataFrame |
| `normality_table` | Normality tests over many variables | DataFrame |
| `correlation_pvalue_table` | Pairwise correlation and p-value table | DataFrame |
| `missingness_by_group_table` | Missingness by cohort/group | DataFrame |
| `outlier_table` | IQR-based outlier summary | DataFrame |
| `bootstrap_summary` | Bootstrapping mean, median, or a custom one-sample statistic | `BootstrapResult` |
| `bootstrap_metric` | Bootstrapping an arbitrary metric over aligned arrays | `BootstrapResult` |
| `bootstrap_binary_classification_metrics` | Bootstrapping sensitivity, specificity, AUC, and related metrics | `pandas.DataFrame` |

## Parameter Reference

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `normality_test(values, ...)` | `values` | `method="shapiro"` or `"normaltest"` | result dataclass |
| `compare_two_groups(group_a, group_b, ...)` | `group_a`, `group_b` | `paired`, `method`, `alternative`, `equal_var` | result dataclass |
| `compare_multiple_groups(groups, ...)` | `groups` | `method="auto"`, `"anova"`, or `"kruskal"` | result dataclass |
| `categorical_test(table, ...)` | `table` | `method="auto"`, `"chi2"`, or `"fisher"` | result dataclass |
| `correlation_test(x, y, ...)` | `x`, `y` | `method="spearman"`, `alternative` | result dataclass |
| `adjust_p_values(p_values, ...)` | p-value vector | method, alpha | correction DataFrame |
| `p_value_correction_table(df, ...)` | DataFrame with p-value column | p column, method, alpha | DataFrame |
| `fit_logistic_regression_table(df, ...)` | DataFrame, outcome, covariates | intercept, alpha, FDR method | OR table |
| `fit_linear_regression_table(df, ...)` | DataFrame, outcome, covariates | intercept, alpha, FDR method | beta table |
| `vif_table(df, covariates)` | DataFrame and covariates | none | VIF table |
| `mcnemar_test(y_true, pred_a, pred_b, ...)` | paired labels/predictions | exact mode | test table |
| `bootstrap_auc_difference(y_true, prob_a, prob_b, ...)` | labels and two probability vectors | rounds, alpha, seed | CI table |
| `normality_table(df, columns, ...)` | DataFrame and columns | method | QC table |
| `correlation_pvalue_table(df, columns, ...)` | DataFrame and columns | method, correction | pairwise table |
| `missingness_by_group_table(df, ...)` | DataFrame and group column | columns | missingness table |
| `outlier_table(df, columns, ...)` | DataFrame and numeric columns | IQR multiplier | outlier table |
| `bootstrap_summary(values, ...)` | `values` | `statistic`, `n_rounds`, `alpha`, `random_state` | result dataclass |
| `bootstrap_metric(*arrays, metric_func=...)` | aligned arrays, `metric_func` | `metric_name`, `n_rounds`, `alpha`, `random_state`, `drop_invalid` | result dataclass |
| `bootstrap_binary_classification_metrics(y_true, y_pred, ...)` | `y_true`, `y_pred` | `y_prob`, `metrics`, `pos_label`, `n_rounds`, `alpha`, `random_state` | summary DataFrame |

## Result Objects

Statistical tests return `StatisticalTestResult`.

```python
result = fst.compare_two_groups(
    group_a=[1.2, 1.4, 1.1, 1.3],
    group_b=[1.8, 2.0, 1.7, 2.1],
)

result.test
result.statistic
result.p_value
result.effect_size
result.to_dict()
```

Bootstrap functions return either `BootstrapResult` or a DataFrame. The dataclass contains the original estimate, percentile confidence interval, number of completed rounds, and the bootstrap distribution.

```python
boot = fst.bootstrap_summary(
    values=[1.2, 1.4, 1.1, 1.3, 1.5],
    statistic="mean",
    n_rounds=2000,
    random_state=42,
)

boot.estimate
boot.ci_low
boot.ci_high
boot.to_dict()
```

## Choosing Tests

| Question | Suggested Function |
| --- | --- |
| Is this numeric variable approximately normal? | `normality_test` |
| Do two independent numeric groups differ? | `compare_two_groups(method="ttest")` or `method="mannwhitney"` |
| Do paired measurements differ before and after treatment? | `compare_two_groups(paired=True)` or `method="wilcoxon"` |
| Do three or more groups differ? | `compare_multiple_groups(method="anova")` or `method="kruskal"` |
| Are two categorical variables associated? | `categorical_test` |
| Are two numeric or ordinal variables associated? | `correlation_test(method="spearman")` |
| What is the confidence interval around a model metric? | `bootstrap_binary_classification_metrics` |
| Which p-values remain significant after multiple tests? | `p_value_correction_table(method="fdr_bh")` |
| What are adjusted odds ratios for a binary endpoint? | `fit_logistic_regression_table` |
| Do two classifiers make significantly different paired errors? | `mcnemar_test` |
| Does model A have higher AUC than model B with uncertainty? | `bootstrap_auc_difference` |

## Multiple Testing And FDR

Use Benjamini-Hochberg false discovery rate correction when screening many features, correlations, or univariate models.

```python
adjusted = fst.p_value_correction_table(
    univariate_results,
    p_col="p_value",
    method="fdr_bh",
    alpha=0.05,
)
```

Supported methods are `fdr_bh`, `bonferroni`, `holm`, and `none`. The output includes `p_adjusted`, `p_rank`, `rejected`, `p_adjust_method`, and `alpha`.

## Manuscript Regression Tables

Use regression tables for classical inference alongside ML results.

```python
logistic = fst.fit_logistic_regression_table(
    cohort,
    outcome_col="response",
    covariates=["age", "stage", "l3_sma_cm2"],
    p_adjust="fdr_bh",
)

linear = fst.fit_linear_regression_table(
    cohort,
    outcome_col="risk_score",
    covariates=["age", "stage", "vat_ml"],
)

vif = fst.vif_table(cohort, ["age", "stage", "vat_ml"])
```

Logistic regression returns odds ratios and confidence intervals. Linear regression returns beta estimates and confidence intervals. Categorical variables are dummy encoded with the first level as reference.

## Model Comparison For Papers

Use McNemar's test for paired classification errors and bootstrap AUC difference for discrimination comparisons.

```python
mcnemar = fst.mcnemar_test(y_true, pred_model_a, pred_model_b)

auc_diff = fst.bootstrap_auc_difference(
    y_true,
    prob_model_a,
    prob_model_b,
    n_rounds=2000,
    random_state=42,
)
```

Fyron uses the bootstrap AUC difference as the default robust comparison in this pass. DeLong testing is intentionally not exposed until a small, well-tested internal implementation is added.

## Statistical QC Tables

```python
normality = fst.normality_table(cohort, ["age", "l3_sma_cm2", "vat_ml"])
correlations = fst.correlation_pvalue_table(
    cohort,
    ["age", "l3_sma_cm2", "vat_ml", "risk_score"],
    method="spearman",
    p_adjust="fdr_bh",
)
missingness = fst.missingness_by_group_table(cohort, group_col="stage")
outliers = fst.outlier_table(cohort, ["age", "l3_sma_cm2", "vat_ml"])
```

These tables are intended for supplements, methods checks, and reviewer-facing data QC. They do not replace a pre-specified statistical analysis plan.

## Two-Group Comparisons

`compare_two_groups` supports Welch t-test, Student t-test, Mann-Whitney U, paired t-test, and Wilcoxon signed-rank tests.

```python
from fyron import statistics as fst

result = fst.compare_two_groups(
    group_a=[42, 47, 51, 49, 45],
    group_b=[55, 58, 53, 60, 57],
    method="mannwhitney",
    alternative="two-sided",
)

result.to_dict()
```

Clinical guidance:

- Use `method="ttest"` when the analysis plan assumes approximately normal group distributions.
- Use `equal_var=False` for Welch's t-test, which is the default.
- Use `method="mannwhitney"` for a rank-based comparison of independent groups.
- Use `paired=True` for paired numeric measurements.
- Use `method="wilcoxon"` for paired rank-based testing.

## Categorical Tests

`categorical_test` accepts a contingency table. With `method="auto"`, Fyron uses Fisher's exact test for sparse 2x2 tables and chi-square otherwise.

```python
result = fst.categorical_test(
    table=[
        [12, 8],
        [4, 16],
    ],
    method="auto",
)

result.test
result.p_value
```

For larger tables, use chi-square explicitly:

```python
result = fst.categorical_test(
    table=[
        [12, 8, 5],
        [4, 16, 10],
    ],
    method="chi2",
)
```

## Correlation Tests

Spearman is the default because clinical variables are often skewed or ordinal.

```python
result = fst.correlation_test(
    x=[1, 2, 3, 4, 5],
    y=[2.1, 2.9, 3.2, 4.4, 5.1],
    method="spearman",
)
```

Use `method="pearson"` when a linear relationship is the planned assumption. Use `method="kendall"` for small samples or ordinal associations where Kendall's tau is preferred.

## Bootstrap A Summary Score

Use `bootstrap_summary` for uncertainty around a score, biomarker, measurement, or model output distribution.

```python
boot = fst.bootstrap_summary(
    values=cohort["risk_score"],
    statistic="median",
    n_rounds=5000,
    alpha=0.05,
    random_state=42,
)

print(boot.estimate, boot.ci_low, boot.ci_high)
```

You can also pass a custom one-sample function.

```python
def p90(values):
    import numpy as np

    return float(np.percentile(values, 90))

boot = fst.bootstrap_summary(
    values=cohort["risk_score"],
    statistic=p90,
    n_rounds=2000,
    random_state=42,
)
```

## Bootstrap A Custom Metric

Use `bootstrap_metric` when the statistic depends on one or more aligned arrays.

```python
import numpy as np
from fyron import statistics as fst

def mean_difference(group, value):
    group = np.asarray(group)
    value = np.asarray(value, dtype=float)
    return float(value[group == 1].mean() - value[group == 0].mean())

boot = fst.bootstrap_metric(
    cohort["treatment_group"],
    cohort["risk_score"],
    metric_func=mean_difference,
    metric_name="risk_score_mean_difference",
    n_rounds=3000,
    random_state=42,
)
```

The arrays must have the same length. Each bootstrap round samples row indices and passes the resampled arrays to your metric function.

## Bootstrap Binary Classification Metrics

Use this for confidence intervals around clinical model metrics.

```python
table = fst.bootstrap_binary_classification_metrics(
    y_true=y_test,
    y_pred=y_pred,
    y_prob=y_prob,
    metrics=[
        "auc",
        "sensitivity",
        "specificity",
        "balanced_accuracy",
        "f1",
    ],
    pos_label=1,
    n_rounds=2000,
    alpha=0.05,
    random_state=42,
)

table
```

Available metrics:

| Metric | Meaning |
| --- | --- |
| `accuracy` | `(TP + TN) / N` |
| `sensitivity` | recall for the positive class |
| `specificity` | recall for the negative class |
| `balanced_accuracy` | mean of sensitivity and specificity |
| `precision` | positive predictive value |
| `npv` | negative predictive value |
| `f1` | harmonic mean of precision and sensitivity |
| `auc` | ROC AUC, available when `y_prob` is provided |
| `tp`, `tn`, `fp`, `fn` | confusion counts |

The result is a DataFrame with `metric`, `estimate`, `ci_low`, `ci_high`, `n_rounds`, `requested_rounds`, `dropped_rounds`, and `alpha`.

## Effect Sizes And Ratios

Use effect-size helpers when a paper table needs magnitude, not only p-values.

| Function | Required | Returns |
| --- | --- | --- |
| `cohens_d(group_a, group_b)` | two numeric groups | standardized mean difference |
| `cliffs_delta(group_a, group_b)` | two ordinal/numeric groups | non-parametric dominance effect |
| `cramers_v(table)` | contingency table | categorical association strength |
| `odds_ratio_ci(table)` | 2x2 table | odds ratio and CI dict |
| `risk_ratio_ci(table)` | 2x2 table | risk ratio and CI dict |
| `standardized_mean_difference(group_a, group_b, categorical=False)` | two groups | numeric or binary categorical SMD |

```python
d = fst.cohens_d(group_a, group_b)
v = fst.cramers_v([[10, 5], [3, 12]])
odds = fst.odds_ratio_ci([[10, 5], [3, 12]])
```

## Practical Guidance

- Define the statistical test before looking at the p-value.
- Use `random_state` for reproducible bootstrap intervals.
- Increase `n_rounds` for final reports; `1000` is a reasonable development default, while `2000` to `10000` is more common for final tables.
- Keep `drop_invalid=True` for bootstrap metrics that may be undefined in rare resamples, such as AUC with only one class.
- Report the test name and sample size together with p-values.
- Prefer effect sizes and confidence intervals over p-values alone.
