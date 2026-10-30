"""Clinical statistics helpers for Fyron.

Install optional dependencies with::

    uv add "fyron[statistics]"

The functions are intentionally small and explicit. They are meant for
inspectable clinical data science workflows, not as a replacement for a full
statistical analysis plan.
"""

from __future__ import annotations

from .bootstrap import (
    BootstrapResult,
    bootstrap_binary_classification_metrics,
    bootstrap_metric,
    bootstrap_summary,
)
from .comparison import bootstrap_auc_difference, mcnemar_test
from .correction import adjust_p_values, p_value_correction_table
from .tests import (
    StatisticalTestResult,
    categorical_test,
    compare_multiple_groups,
    compare_two_groups,
    correlation_test,
    normality_test,
)
from .qc import correlation_pvalue_table, missingness_by_group_table, normality_table, outlier_table
from .regression import fit_linear_regression_table, fit_logistic_regression_table, vif_table
from .effects import (
    cliffs_delta,
    cohens_d,
    cramers_v,
    odds_ratio_ci,
    risk_ratio_ci,
    standardized_mean_difference,
)

__all__ = [
    "BootstrapResult",
    "StatisticalTestResult",
    "adjust_p_values",
    "bootstrap_binary_classification_metrics",
    "bootstrap_auc_difference",
    "bootstrap_metric",
    "bootstrap_summary",
    "categorical_test",
    "cliffs_delta",
    "cohens_d",
    "compare_multiple_groups",
    "compare_two_groups",
    "correlation_test",
    "correlation_pvalue_table",
    "cramers_v",
    "normality_test",
    "normality_table",
    "fit_linear_regression_table",
    "fit_logistic_regression_table",
    "mcnemar_test",
    "missingness_by_group_table",
    "odds_ratio_ci",
    "outlier_table",
    "p_value_correction_table",
    "risk_ratio_ci",
    "standardized_mean_difference",
    "vif_table",
]
