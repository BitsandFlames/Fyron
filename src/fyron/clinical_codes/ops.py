"""German OPS procedure and MDC partition helpers."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

import pandas as pd

from .utils import (
    _indicator_prevalence,
    _require_columns,
    _slug,
    _split_code_values,
    aggregate_code_rows,
    normalize_code,
    split_code_string,
)

OPS_CATEGORIES = [
    "Diagnostic Procedures",
    "Imaging",
    "Surgery",
    "Medication / Therapy",
    "Radiation / Nuclear Medicine",
    "Intensive Care",
    "Rehabilitation",
    "Other",
]

OPS_CHAPTER_PARTITION_MAPPING = {
    "1": "medical",
    "3": "medical",
    "5": "surgical",
    "6": "medical",
    "8": "medical",
    "9": "medical",
}


def classify_ops(code: Any) -> str | None:
    """Classify one German OPS code into a broad procedure category.

    Parameters
    ----------
    code
        OPS code such as ``"1-620"``, ``"3-20"``, ``"5-541"``, or ``"8-980"``.

    Returns
    -------
    str or None
        Broad OPS category, ``"Other"`` for malformed non-empty codes, or None
        for missing values.
    """

    ops = normalize_code(code, remove_spaces=True, remove_dots=False)
    if ops is None:
        return None
    match = re.match(r"^([0-9])", ops)
    if match is None:
        return "Other"
    chapter = match.group(1)
    if chapter == "1":
        return "Diagnostic Procedures"
    if chapter == "3":
        return "Imaging"
    if chapter == "5":
        return "Surgery"
    if chapter == "6":
        return "Medication / Therapy"
    if chapter == "8":
        if ops.startswith(("8-98", "898")):
            return "Intensive Care"
        return "Medication / Therapy"
    if chapter == "9":
        return "Rehabilitation"
    if chapter == "2":
        return "Diagnostic Procedures"
    if chapter == "7":
        return "Radiation / Nuclear Medicine"
    return "Other"


def classify_ops_string(value: Any, *, sep: str = ";") -> set[str]:
    """Classify a delimited OPS code string into broad procedure categories.

    Parameters
    ----------
    value
        Scalar cell containing one or more OPS codes.
    sep
        Delimiter between codes.

    Returns
    -------
    set[str]
        OPS categories present in the code string.
    """

    categories: set[str] = set()
    for code in split_code_string(value, sep=sep):
        category = classify_ops(code)
        if category is not None:
            categories.add(category)
    return categories


def normalize_ops_codes(ops_codes: Any) -> list[str]:
    """Convert different OPS column formats into a clean list of OPS codes.

    Parameters
    ----------
    ops_codes
        Missing value, scalar code, delimited string, Python-style list string,
        or iterable of OPS codes.

    Returns
    -------
    list[str]
        Normalized OPS code strings.
    """

    return _split_code_values(ops_codes, separators=r"[,;|\s]+", normalize=True)


def get_ops_chapter(ops_code: Any) -> str | None:
    """Extract the one-digit OPS chapter from an OPS code.

    Parameters
    ----------
    ops_code
        OPS code such as ``"5-470.0"``, ``"8-930"``, or ``"1-632"``.

    Returns
    -------
    str or None
        One-digit chapter, or None for missing/malformed values.
    """

    ops = normalize_code(ops_code, remove_spaces=True, remove_dots=False)
    if ops is None:
        return None
    match = re.match(r"^(\d+)-", ops)
    return match.group(1) if match else None


def classify_mdc_partition(ops_codes: Any) -> str:
    """Classify a stay into a broad MDC partition from OPS codes.

    Parameters
    ----------
    ops_codes
        Missing value, scalar code, delimited string, Python-style list string,
        or iterable of OPS codes.

    Returns
    -------
    str
        ``"surgical"`` when any chapter-5 OPS code is present, ``"medical"``
        when any other valid OPS chapter is present, otherwise ``"other"``.
    """

    codes = normalize_ops_codes(ops_codes)
    if not codes:
        return "other"
    chapters = {chapter for code in codes if (chapter := get_ops_chapter(code)) is not None}
    if "5" in chapters:
        return "surgical"
    if chapters:
        return "medical"
    return "other"


def add_mdc_partition(df: pd.DataFrame, ops_column: str | None = None) -> pd.DataFrame:
    """Add MDC partition labels from an OPS code column.

    Parameters
    ----------
    df
        DataFrame containing OPS code values.
    ops_column
        Explicit source column. If omitted, common OPS column names are tried.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with ``mdc_partition`` and ``mdc_partition_source``.
    """

    out = df.copy()
    candidates = [ops_column] if ops_column else ["ops_code_list", "pni_ops", "ops", "ops_codes", "pni_ops_codes"]
    source = next((column for column in candidates if column and column in out.columns), None)
    if source is None:
        out["mdc_partition"] = "other"
        out["mdc_partition_source"] = pd.NA
        return out
    out["mdc_partition"] = out[source].apply(classify_mdc_partition)
    out["mdc_partition_source"] = source
    return out


def aggregate_ops_by_encounter(
    procedures: pd.DataFrame,
    *,
    patient_col: str = "patient_id",
    encounter_col: str = "encounter_id",
    date_col: str = "performed_date",
    ops_code_col: str = "ops_code",
    ops_display_col: str | None = "ops_display",
    complete_encounters: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Aggregate one-OPS-procedure-per-row data to encounter-level lists.

    Parameters
    ----------
    procedures
        Long procedure DataFrame with one OPS code per row.
    patient_col
        Patient identifier column.
    encounter_col
        Encounter identifier column.
    date_col
        Procedure date column used for first/last performed dates.
    ops_code_col
        OPS code column.
    ops_display_col
        Optional OPS display text column.
    complete_encounters
        Optional patient/encounter table used to retain encounters without OPS
        codes.

    Returns
    -------
    pandas.DataFrame
        One row per patient encounter with ``ops_code_list``,
        ``ops_display_list``, first/last performed dates, and ``n_ops_codes``.
    """

    return aggregate_code_rows(
        procedures,
        [patient_col, encounter_col],
        ops_code_col,
        display_col=ops_display_col,
        date_col=date_col,
        code_list_col="ops_code_list",
        display_list_col="ops_display_list" if ops_display_col is not None else None,
        first_date_col="ops_first_performed_date",
        last_date_col="ops_last_performed_date",
        count_col="n_ops_codes",
        complete_groups=complete_encounters,
    )


def add_ops_categories(
    df: pd.DataFrame,
    ops_col: str,
    *,
    sep: str = ";",
    prefix: str = "ops_category_",
    summary_col: str = "ops_categories",
    count_col: str = "n_ops_categories",
    categories: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Add broad German OPS procedure-category indicator columns.

    Parameters
    ----------
    df
        DataFrame containing an OPS code column.
    ops_col
        Column with one or more OPS codes per row.
    sep
        Delimiter between multiple codes in one cell.
    prefix
        Prefix for generated binary indicator columns.
    summary_col
        Output column containing human-readable OPS categories.
    count_col
        Output column containing the number of OPS categories per row.
    categories
        Optional explicit category order. Defaults to Fyron's broad OPS groups.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with binary OPS category indicators and summary columns.
    """

    _require_columns(df, [ops_col])
    selected_categories = list(categories or OPS_CATEGORIES)
    out = df.copy()
    row_categories = out[ops_col].apply(lambda value: classify_ops_string(value, sep=sep))
    for category in selected_categories:
        out[f"{prefix}{_slug(category)}"] = row_categories.apply(lambda values, category=category: int(category in values))
    out[summary_col] = row_categories.apply(lambda values: "; ".join(sorted(values)) if values else "Unknown")
    out[count_col] = row_categories.apply(len).astype(int)
    return out


def ops_category_prevalence(
    df: pd.DataFrame,
    *,
    category_cols: Sequence[str] | None = None,
    prefix: str = "ops_category_",
) -> pd.DataFrame:
    """Summarize OPS procedure-category indicator prevalence.

    Parameters
    ----------
    df
        DataFrame with OPS category indicator columns.
    category_cols
        Optional explicit indicator columns. If omitted, columns with ``prefix``
        are used.
    prefix
        Prefix used to discover indicator columns.

    Returns
    -------
    pandas.DataFrame
        Prevalence table with category, column, patient count, and percent.
    """

    return _indicator_prevalence(df, group_cols=category_cols, prefix=prefix, label_col="category")
