"""Paper-ready tables and lightweight report helpers."""

from __future__ import annotations

from .tables import (
    cohort_flow_table,
    compare_models_table,
    dataframe_to_markdown,
    format_estimate_ci,
    metrics_table,
    summarize_baseline_table,
)

__all__ = [
    "cohort_flow_table",
    "compare_models_table",
    "dataframe_to_markdown",
    "format_estimate_ci",
    "metrics_table",
    "summarize_baseline_table",
]
