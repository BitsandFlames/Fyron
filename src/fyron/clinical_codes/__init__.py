"""Clinical coding helpers for ICD-10, OPS, MDC partitions, and comorbidity."""

from __future__ import annotations

from .charlson import (
    CHARLSON_CATEGORY_ORDER,
    CHARLSON_WEIGHTS,
    add_charlson_comorbidity_columns,
    charlson_comorbidity_index,
    classify_charlson_comorbidities,
    derive_charlson_category,
)
from .encounter import ENCOUNTER_TYPE_MAPPING, add_encounter_type_features, classify_elective_status
from .icd10 import (
    ICD10_DISEASE_GROUPS,
    add_icd10_disease_groups,
    classify_icd10,
    classify_icd10_string,
    icd10_group_prevalence,
)
from .ops import (
    OPS_CATEGORIES,
    add_mdc_partition,
    add_ops_categories,
    aggregate_ops_by_encounter,
    classify_mdc_partition,
    classify_ops,
    classify_ops_string,
    get_ops_chapter,
    normalize_ops_codes,
    ops_category_prevalence,
)
from .utils import aggregate_code_rows, explode_code_column, normalize_code, split_code_string

__all__ = [
    "CHARLSON_CATEGORY_ORDER",
    "CHARLSON_WEIGHTS",
    "ENCOUNTER_TYPE_MAPPING",
    "ICD10_DISEASE_GROUPS",
    "OPS_CATEGORIES",
    "add_charlson_comorbidity_columns",
    "add_encounter_type_features",
    "add_icd10_disease_groups",
    "add_mdc_partition",
    "add_ops_categories",
    "aggregate_code_rows",
    "aggregate_ops_by_encounter",
    "charlson_comorbidity_index",
    "classify_charlson_comorbidities",
    "classify_elective_status",
    "classify_icd10",
    "classify_icd10_string",
    "classify_mdc_partition",
    "classify_ops",
    "classify_ops_string",
    "derive_charlson_category",
    "explode_code_column",
    "get_ops_chapter",
    "icd10_group_prevalence",
    "normalize_code",
    "normalize_ops_codes",
    "ops_category_prevalence",
    "split_code_string",
]
