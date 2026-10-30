"""Broad ICD-10 disease group helpers."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

import pandas as pd

from .utils import _indicator_prevalence, _require_columns, _slug, normalize_code, split_code_string

ICD10_DISEASE_GROUPS = [
    "Cancer",
    "Benign / In Situ Neoplasm",
    "Hematologic / Immune",
    "Infectious",
    "Endocrine / Metabolic",
    "Mental Health",
    "Neurological",
    "Cardiovascular",
    "Respiratory",
    "Gastrointestinal",
    "Dermatologic",
    "Musculoskeletal / Autoimmune",
    "Renal / Urologic",
    "Obstetric / Perinatal",
    "Congenital",
    "Symptoms / Findings",
    "Trauma",
    "Healthcare Encounter",
    "External Cause",
    "Other",
]


def classify_icd10(code: Any) -> str | None:
    """Classify one ICD-10 code into a broad disease group.

    Parameters
    ----------
    code
        ICD-10 code such as ``"C34"``, ``"I50.1"``, or ``"Z51"``.

    Returns
    -------
    str or None
        Broad disease group name, ``"Other"`` for malformed non-empty codes,
        or None for missing values.
    """

    icd = normalize_code(code, remove_spaces=True, remove_dots=False)
    if icd is None:
        return None
    match = re.match(r"^([A-Z])\.?(\d{2})", icd)
    if match is None:
        return "Other"
    letter = match.group(1)
    number = int(match.group(2))
    if letter in {"A", "B"}:
        return "Infectious"
    if letter == "C":
        return "Cancer"
    if letter == "D":
        if number <= 48:
            return "Benign / In Situ Neoplasm"
        if number <= 89:
            return "Hematologic / Immune"
        return "Other"
    mapping = {
        "E": "Endocrine / Metabolic",
        "F": "Mental Health",
        "G": "Neurological",
        "I": "Cardiovascular",
        "J": "Respiratory",
        "K": "Gastrointestinal",
        "L": "Dermatologic",
        "M": "Musculoskeletal / Autoimmune",
        "N": "Renal / Urologic",
        "Q": "Congenital",
        "R": "Symptoms / Findings",
        "Z": "Healthcare Encounter",
    }
    if letter in mapping:
        return mapping[letter]
    if letter in {"O", "P"}:
        return "Obstetric / Perinatal"
    if letter in {"S", "T"}:
        return "Trauma"
    if letter in {"V", "W", "X", "Y"}:
        return "External Cause"
    return "Other"


def classify_icd10_string(value: Any, *, sep: str = ";") -> set[str]:
    """Classify a delimited ICD-10 code string into disease groups.

    Parameters
    ----------
    value
        Scalar cell containing one or more ICD-10 codes.
    sep
        Delimiter between codes.

    Returns
    -------
    set[str]
        Disease groups present in the code string.
    """

    groups: set[str] = set()
    for code in split_code_string(value, sep=sep):
        group = classify_icd10(code)
        if group is not None:
            groups.add(group)
    return groups


def add_icd10_disease_groups(
    df: pd.DataFrame,
    icd_col: str,
    *,
    sep: str = ";",
    prefix: str = "icd10_group_",
    summary_col: str = "icd10_groups",
    count_col: str = "n_icd10_groups",
    groups: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Add broad ICD-10 disease-group indicator columns.

    Parameters
    ----------
    df
        DataFrame containing an ICD-10 code column.
    icd_col
        Column with one or more ICD-10 codes per row.
    sep
        Delimiter between multiple codes in one cell.
    prefix
        Prefix for generated binary indicator columns.
    summary_col
        Output column containing human-readable disease groups.
    count_col
        Output column containing the number of disease groups per row.
    groups
        Optional explicit disease-group order. Defaults to Fyron's built-in
        broad ICD-10 groups.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with binary disease-group indicators and summary columns.
    """

    _require_columns(df, [icd_col])
    selected_groups = list(groups or ICD10_DISEASE_GROUPS)
    out = df.copy()
    row_groups = out[icd_col].apply(lambda value: classify_icd10_string(value, sep=sep))
    for group in selected_groups:
        out[f"{prefix}{_slug(group)}"] = row_groups.apply(lambda values, group=group: int(group in values))
    out[summary_col] = row_groups.apply(lambda values: "; ".join(sorted(values)) if values else "Unknown")
    out[count_col] = row_groups.apply(len).astype(int)
    return out


def icd10_group_prevalence(
    df: pd.DataFrame,
    *,
    group_cols: Sequence[str] | None = None,
    prefix: str = "icd10_group_",
) -> pd.DataFrame:
    """Summarize ICD-10 disease-group indicator prevalence.

    Parameters
    ----------
    df
        DataFrame with ICD-10 group indicator columns.
    group_cols
        Optional explicit indicator columns. If omitted, columns with ``prefix``
        are used.
    prefix
        Prefix used to discover indicator columns.

    Returns
    -------
    pandas.DataFrame
        Prevalence table with group, column, patient count, and percent.
    """

    return _indicator_prevalence(df, group_cols=group_cols, prefix=prefix, label_col="group")
