"""Model explainability helpers with explicit tabular outputs."""

from __future__ import annotations

from .inspection import (
    explain_model_summary,
    explain_patient_prediction,
    partial_dependence_table,
    permutation_importance_table,
    shap_summary_table,
    shap_values_table,
)

__all__ = [
    "explain_model_summary",
    "explain_patient_prediction",
    "partial_dependence_table",
    "permutation_importance_table",
    "shap_summary_table",
    "shap_values_table",
]
