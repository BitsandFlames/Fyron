"""Preprocessing and cohort quality-control helpers."""

from __future__ import annotations

from .qc import (
    compare_train_test_balance,
    detect_potential_leakage,
    feature_matrix_report,
    find_duplicate_ids,
    summarize_categorical_levels,
    summarize_missingness,
)
from .encoding import (
    apply_categorical_encoder,
    encode_categorical,
    fit_categorical_encoder,
    summarize_encoding_plan,
)
from .imputation import (
    apply_imputer,
    fit_imputer,
    impute_dataframe,
    summarize_imputation_plan,
)

__all__ = [
    "apply_categorical_encoder",
    "apply_imputer",
    "compare_train_test_balance",
    "detect_potential_leakage",
    "encode_categorical",
    "feature_matrix_report",
    "find_duplicate_ids",
    "fit_categorical_encoder",
    "fit_imputer",
    "impute_dataframe",
    "summarize_categorical_levels",
    "summarize_encoding_plan",
    "summarize_imputation_plan",
    "summarize_missingness",
]
