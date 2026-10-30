"""Survival analysis utilities (Kaplan–Meier, RMST, Cox PH, Weibull AFT).

This subpackage requires optional dependencies. Install with::

    uv add "fyron[survival]"

"""

from __future__ import annotations

try:
    import lifelines  # noqa: F401
except ImportError as exc:  # pragma: no cover - exercised when extras missing
    raise ImportError(
        "The fyron.survival module requires lifelines and matplotlib. "
        'Install them with: uv add "fyron[survival]"'
    ) from exc

from fyron.survival.boosting import train_gradient_survival_boosting
from fyron.survival.cox import fit_multivariate_cox, fit_univariate_cox
from fyron.survival.groups import SplitMethod, create_survival_groups, default_tau_from_observed_times
from fyron.survival.kaplan_meier import KaplanMeierPlotResult, plot_kaplan_meier
from fyron.survival.outputs import cox_forest_table, survival_prediction_table
from fyron.survival.ph_diagnostics import (
    check_ph_assumptions,
    plot_schoenfeld_residuals,
    schoenfeld_residuals_table,
    schoenfeld_test_table,
)
from fyron.survival.rmst import calculate_rmst, compare_rmst
from fyron.survival.time_varying import (
    expand_time_interaction_dataframe,
    fit_cox_time_interactions,
    fit_time_varying_cox,
    run_survival_sensitivity_analysis,
)
from fyron.survival.weibull_aft import fit_weibull_aft, plot_aft_survival_curves

__all__ = [
    "SplitMethod",
    "KaplanMeierPlotResult",
    "calculate_rmst",
    "check_ph_assumptions",
    "compare_rmst",
    "cox_forest_table",
    "create_survival_groups",
    "default_tau_from_observed_times",
    "fit_multivariate_cox",
    "fit_cox_time_interactions",
    "fit_time_varying_cox",
    "fit_univariate_cox",
    "fit_weibull_aft",
    "expand_time_interaction_dataframe",
    "plot_aft_survival_curves",
    "plot_kaplan_meier",
    "plot_schoenfeld_residuals",
    "schoenfeld_residuals_table",
    "schoenfeld_test_table",
    "run_survival_sensitivity_analysis",
    "survival_prediction_table",
    "train_gradient_survival_boosting",
]
