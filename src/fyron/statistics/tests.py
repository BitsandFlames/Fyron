"""Statistical tests for clinical tabular data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

from ._deps import require_numpy, require_scipy_stats


Alternative = Literal["two-sided", "less", "greater"]
TwoGroupMethod = Literal["auto", "ttest", "mannwhitney", "paired_ttest", "wilcoxon"]
MultiGroupMethod = Literal["auto", "anova", "kruskal"]
CategoricalMethod = Literal["auto", "chi2", "fisher"]
CorrelationMethod = Literal["pearson", "spearman", "kendall"]


@dataclass(frozen=True)
class StatisticalTestResult:
    """Named result returned by Fyron statistical tests."""

    test: str
    statistic: float
    p_value: float
    n: int
    effect_size: float | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "test": self.test,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "n": self.n,
            "effect_size": self.effect_size,
            **self.details,
        }


def _numeric_array(values: Sequence[Any], *, name: str):
    np = require_numpy()
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional.")
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError(f"{name} must contain at least one finite numeric value.")
    return arr


def _cohens_d(a, b) -> float:
    np = require_numpy()
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    pooled = ((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2)
    if pooled <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pooled))


def _paired_cohens_d(diff) -> float:
    np = require_numpy()
    if len(diff) < 2:
        return float("nan")
    sd = np.std(diff, ddof=1)
    if sd == 0:
        return float("nan")
    return float(np.mean(diff) / sd)


def normality_test(
    values: Sequence[Any],
    *,
    method: Literal["shapiro", "normaltest"] = "shapiro",
) -> StatisticalTestResult:
    """Test whether a numeric vector is compatible with a normal distribution."""
    stats = require_scipy_stats()
    arr = _numeric_array(values, name="values")
    if method == "shapiro":
        if len(arr) < 3:
            raise ValueError("Shapiro-Wilk test requires at least 3 observations.")
        result = stats.shapiro(arr)
        test_name = "shapiro"
    elif method == "normaltest":
        if len(arr) < 8:
            raise ValueError("D'Agostino-Pearson normality test requires at least 8 observations.")
        result = stats.normaltest(arr)
        test_name = "normaltest"
    else:
        raise ValueError("method must be 'shapiro' or 'normaltest'.")
    return StatisticalTestResult(
        test=test_name,
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        n=int(len(arr)),
    )


def compare_two_groups(
    group_a: Sequence[Any],
    group_b: Sequence[Any],
    *,
    paired: bool = False,
    method: TwoGroupMethod = "auto",
    alternative: Alternative = "two-sided",
    equal_var: bool = False,
) -> StatisticalTestResult:
    """Compare two numeric groups.

    ``method="auto"`` uses Welch's t-test for independent groups and paired
    t-test for paired groups. Choose Mann-Whitney or Wilcoxon explicitly when
    the analysis plan calls for a non-parametric test.
    Paired methods retain only jointly finite pairs and report pair counts.
    Zero-scale standardized effects are undefined and returned as ``None``.
    """
    np = require_numpy()
    stats = require_scipy_stats()
    selected = method
    if method == "auto":
        selected = "paired_ttest" if paired else "ttest"
    if paired and selected in ("ttest", "mannwhitney"):
        raise ValueError("paired=True conflicts with an independent-group test.")
    paired = selected in ("paired_ttest", "wilcoxon")
    if paired:
        a = np.asarray(group_a, dtype=float)
        b = np.asarray(group_b, dtype=float)
        if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape:
            raise ValueError("paired comparisons require one-dimensional groups with equal length.")
        keep = np.isfinite(a) & np.isfinite(b)
        a, b = a[keep], b[keep]
        if len(a) < 2:
            raise ValueError("paired comparisons require at least two complete pairs.")
    else:
        a = _numeric_array(group_a, name="group_a")
        b = _numeric_array(group_b, name="group_b")

    if selected == "ttest":
        result = stats.ttest_ind(a, b, equal_var=equal_var, alternative=alternative)
        effect = _cohens_d(a, b)
        test_name = "welch_ttest" if not equal_var else "student_ttest"
    elif selected == "paired_ttest":
        result = stats.ttest_rel(a, b, alternative=alternative)
        effect = _paired_cohens_d(a - b)
        test_name = "paired_ttest"
    elif selected == "mannwhitney":
        result = stats.mannwhitneyu(a, b, alternative=alternative)
        effect = float(result.statistic / (len(a) * len(b)))
        test_name = "mannwhitney_u"
    elif selected == "wilcoxon":
        if len(a) != len(b):
            raise ValueError("Wilcoxon signed-rank test requires equal length groups.")
        result = stats.wilcoxon(a, b, alternative=alternative)
        effect = None
        test_name = "wilcoxon"
    else:
        raise ValueError(
            "method must be 'auto', 'ttest', 'mannwhitney', 'paired_ttest', or 'wilcoxon'."
        )

    return StatisticalTestResult(
        test=test_name,
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        n=int(len(a) + len(b) if not paired else len(a)),
        effect_size=None if effect is None or not np.isfinite(effect) else float(effect),
        details={
            "n_a": int(len(a)),
            "n_b": int(len(b)),
            "paired": paired,
            "alternative": alternative,
        },
    )


def compare_multiple_groups(
    groups: Sequence[Sequence[Any]],
    *,
    method: MultiGroupMethod = "auto",
) -> StatisticalTestResult:
    """Compare three or more numeric groups with ANOVA or Kruskal-Wallis."""
    stats = require_scipy_stats()
    arrays = [_numeric_array(group, name=f"group_{index}") for index, group in enumerate(groups)]
    if len(arrays) < 2:
        raise ValueError("at least two groups are required.")
    selected = "anova" if method == "auto" else method
    if selected == "anova":
        result = stats.f_oneway(*arrays)
        test_name = "one_way_anova"
    elif selected == "kruskal":
        result = stats.kruskal(*arrays)
        test_name = "kruskal_wallis"
    else:
        raise ValueError("method must be 'auto', 'anova', or 'kruskal'.")
    return StatisticalTestResult(
        test=test_name,
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        n=int(sum(len(arr) for arr in arrays)),
        details={"group_sizes": [int(len(arr)) for arr in arrays]},
    )


def categorical_test(
    table: Sequence[Sequence[Any]],
    *,
    method: CategoricalMethod = "auto",
) -> StatisticalTestResult:
    """Run a chi-square or Fisher exact test on a contingency table."""
    np = require_numpy()
    stats = require_scipy_stats()
    observed = np.asarray(table, dtype=float)
    if observed.ndim != 2:
        raise ValueError("table must be a two-dimensional contingency table.")
    if observed.shape[0] < 2 or observed.shape[1] < 2:
        raise ValueError("table must have at least two rows and two columns.")
    if not np.isfinite(observed).all() or (observed < 0).any() or (observed != np.floor(observed)).any():
        raise ValueError("Contingency table counts must be finite non-negative integers.")

    selected = method
    if method == "auto":
        selected = "fisher" if observed.shape == (2, 2) and observed.min() < 5 else "chi2"
    if selected == "fisher":
        if observed.shape != (2, 2):
            raise ValueError("Fisher exact test currently requires a 2x2 table.")
        odds_ratio, p_value = stats.fisher_exact(observed)
        return StatisticalTestResult(
            test="fisher_exact",
            statistic=float(odds_ratio),
            p_value=float(p_value),
            n=int(observed.sum()),
            effect_size=float(odds_ratio),
            details={"shape": tuple(observed.shape)},
        )
    if selected == "chi2":
        statistic, p_value, dof, expected = stats.chi2_contingency(observed)
        return StatisticalTestResult(
            test="chi_square",
            statistic=float(statistic),
            p_value=float(p_value),
            n=int(observed.sum()),
            details={
                "dof": int(dof),
                "shape": tuple(observed.shape),
                "expected": expected.tolist(),
            },
        )
    raise ValueError("method must be 'auto', 'chi2', or 'fisher'.")


def correlation_test(
    x: Sequence[Any],
    y: Sequence[Any],
    *,
    method: CorrelationMethod = "spearman",
    alternative: Alternative = "two-sided",
) -> StatisticalTestResult:
    """Test association between two numeric variables."""
    np = require_numpy()
    stats = require_scipy_stats()
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    if x_arr.ndim != 1 or y_arr.ndim != 1:
        raise ValueError("x and y must be one-dimensional.")
    if x_arr.shape[0] != y_arr.shape[0]:
        raise ValueError("x and y must have the same length.")
    mask = np.isfinite(x_arr) & np.isfinite(y_arr)
    x_arr = x_arr[mask]
    y_arr = y_arr[mask]
    if len(x_arr) < 3:
        raise ValueError("correlation tests require at least 3 paired observations.")
    if method == "pearson":
        result = stats.pearsonr(x_arr, y_arr, alternative=alternative)
    elif method == "spearman":
        result = stats.spearmanr(x_arr, y_arr, alternative=alternative)
    elif method == "kendall":
        result = stats.kendalltau(x_arr, y_arr, alternative=alternative)
    else:
        raise ValueError("method must be 'pearson', 'spearman', or 'kendall'.")
    return StatisticalTestResult(
        test=f"{method}_correlation",
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        n=int(len(x_arr)),
        effect_size=float(result.statistic),
        details={"alternative": alternative},
    )
