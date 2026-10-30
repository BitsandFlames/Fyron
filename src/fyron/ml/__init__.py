"""Tabular machine learning utilities for healthcare datasets.

Install optional dependencies with::

    uv add "fyron[ml]"

For Boruta feature selection::

    uv add "fyron[ml,boruta]"

"""

from __future__ import annotations

try:
    import numpy  # noqa: F401
    import sklearn  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The fyron.ml module requires numpy and scikit-learn. "
        'Install them with: uv add "fyron[ml]"'
    ) from exc

from fyron.ml.boruta_selection import run_boruta_feature_selection
from fyron.ml.class_weights import (
    compute_class_weights,
    compute_scale_pos_weight,
    sample_weights_for_sklearn,
)
from fyron.ml.cv import cross_validate_model
from fyron.ml.defaults import get_default_param_grid
from fyron.ml.evaluation import (
    apply_probability_calibrator,
    evaluate_external_validation,
    evaluate_locked_threshold,
    fit_probability_calibrator,
    model_card_summary,
    nested_cross_validate_model,
)
from fyron.ml.importance import get_feature_importance, plot_feature_importance
from fyron.ml.metrics import calculate_classification_metrics
from fyron.ml.persistence import load_estimator, save_estimator
from fyron.ml.pipeline import run_classification_pipeline
from fyron.ml.plots import (
    add_stat_annotations,
    format_p_value_annotation,
    plot_alluvial_flow,
    plot_binned_marker_heatmap,
    plot_calibration_curve,
    plot_bland_altman,
    plot_confusion_matrix,
    plot_correlation_heatmap,
    plot_cohort_flow,
    plot_cross_validated_roc,
    plot_density,
    plot_decision_curve,
    plot_dice_by_label,
    plot_directional_ratio_rows,
    plot_external_validation_metrics,
    plot_feature_selection_summary,
    plot_filled_kde,
    plot_forest_estimates,
    plot_grouped_bar_with_significance,
    plot_grouped_correlation_heatmaps,
    plot_grouped_boxplot,
    plot_hazard_ratios,
    plot_histogram,
    plot_kaplan_meier,
    plot_likert_scale,
    plot_metric_bars,
    plot_missingness_bar,
    plot_patterned_bar,
    plot_precision_recall_curve,
    plot_qq,
    plot_raincloud,
    plot_reference_band_grid,
    plot_risk_score_distribution,
    plot_roc_curve,
    plot_signed_feature_weights,
    plot_significance_bars,
    plot_stability_selection,
    plot_swarmplot,
    plot_swimmer,
    plot_survival_calibration,
    plot_table_one_summary,
    plot_time_dependent_auc,
    plot_segmentation_overlay_grid,
    plot_waffle,
    plot_volcano,
    plot_waterfall,
    stat_test_pairs,
)
from fyron.plotting_palettes import (
    get_colormap,
    get_palette,
    list_palettes,
    palette_grayscale_contrast,
    palette_luminance_table,
    preview_palette,
    set_plot_style,
)
from fyron.ml.search import grid_search_model
from fyron.ml.splitting import train_test_split_data
from fyron.ml.training import train_random_forest, train_xgboost

__all__ = [
    "calculate_classification_metrics",
    "add_stat_annotations",
    "apply_probability_calibrator",
    "compute_class_weights",
    "compute_scale_pos_weight",
    "cross_validate_model",
    "evaluate_external_validation",
    "evaluate_locked_threshold",
    "fit_probability_calibrator",
    "format_p_value_annotation",
    "get_colormap",
    "get_default_param_grid",
    "get_feature_importance",
    "get_palette",
    "grid_search_model",
    "load_estimator",
    "list_palettes",
    "model_card_summary",
    "nested_cross_validate_model",
    "plot_alluvial_flow",
    "plot_binned_marker_heatmap",
    "plot_calibration_curve",
    "plot_bland_altman",
    "plot_confusion_matrix",
    "plot_correlation_heatmap",
    "plot_cohort_flow",
    "plot_cross_validated_roc",
    "plot_density",
    "plot_decision_curve",
    "plot_dice_by_label",
    "plot_directional_ratio_rows",
    "plot_external_validation_metrics",
    "plot_feature_selection_summary",
    "plot_feature_importance",
    "plot_filled_kde",
    "plot_forest_estimates",
    "plot_grouped_bar_with_significance",
    "plot_grouped_correlation_heatmaps",
    "plot_grouped_boxplot",
    "plot_hazard_ratios",
    "plot_histogram",
    "plot_kaplan_meier",
    "plot_likert_scale",
    "plot_metric_bars",
    "plot_missingness_bar",
    "plot_patterned_bar",
    "plot_precision_recall_curve",
    "plot_qq",
    "plot_raincloud",
    "plot_reference_band_grid",
    "plot_risk_score_distribution",
    "plot_roc_curve",
    "plot_signed_feature_weights",
    "plot_significance_bars",
    "plot_stability_selection",
    "plot_swarmplot",
    "plot_swimmer",
    "plot_survival_calibration",
    "plot_table_one_summary",
    "plot_time_dependent_auc",
    "plot_segmentation_overlay_grid",
    "plot_waffle",
    "plot_volcano",
    "plot_waterfall",
    "palette_grayscale_contrast",
    "palette_luminance_table",
    "preview_palette",
    "run_boruta_feature_selection",
    "run_classification_pipeline",
    "sample_weights_for_sklearn",
    "save_estimator",
    "set_plot_style",
    "train_random_forest",
    "train_test_split_data",
    "train_xgboost",
    "stat_test_pairs",
]
