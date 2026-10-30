"""Clinical DataFrame operations for transparent feature derivation."""

from __future__ import annotations

import re
import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal

import pandas as pd
from ._dates import date_difference as _date_difference, time_unit_factor

from .clinical_codes import (
    CHARLSON_CATEGORY_ORDER,
    CHARLSON_WEIGHTS,
    ENCOUNTER_TYPE_MAPPING,
    add_charlson_comorbidity_columns,
    add_encounter_type_features,
    add_mdc_partition,
    aggregate_code_rows,
    aggregate_ops_by_encounter,
    charlson_comorbidity_index,
    classify_charlson_comorbidities,
    classify_elective_status,
    classify_mdc_partition,
    derive_charlson_category,
    get_ops_chapter,
    normalize_ops_codes,
)

TimeUnit = Literal["days", "weeks", "months", "years"]

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


def normalize_code(
    value: Any,
    *,
    uppercase: bool = True,
    remove_spaces: bool = True,
    remove_dots: bool = False,
) -> str | None:
    """Normalize one clinical code value for matching.

    Parameters
    ----------
    value
        Raw code value such as an ICD-10, OPS, medication, or local registry code.
    uppercase
        If True, convert the returned code to uppercase.
    remove_spaces
        If True, remove whitespace within the code.
    remove_dots
        If True, remove dots from the code.

    Returns
    -------
    str or None
        Normalized code string, or None for missing/empty values.
    """

    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    if remove_spaces:
        text = re.sub(r"\s+", "", text)
    if remove_dots:
        text = text.replace(".", "")
    if uppercase:
        text = text.upper()
    return text or None


def split_code_string(value: Any, *, sep: str = ";", normalize: bool = True) -> list[str]:
    """Split one cell containing one or more clinical codes.

    Parameters
    ----------
    value
        Scalar value containing one or more codes, usually separated by semicolons.
    sep
        Delimiter used between codes.
    normalize
        If True, normalize each code with :func:`normalize_code`.

    Returns
    -------
    list[str]
        Ordered list of non-empty codes.
    """

    if pd.isna(value):
        return []
    codes: list[str] = []
    for part in str(value).split(sep):
        code = normalize_code(part) if normalize else str(part).strip()
        if code:
            codes.append(code)
    return codes


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


def explode_code_column(
    df: pd.DataFrame,
    code_col: str,
    *,
    sep: str = ";",
    output_col: str = "code",
    keep_empty: bool = False,
) -> pd.DataFrame:
    """Explode a delimited clinical code column into one row per code.

    Parameters
    ----------
    df
        DataFrame containing a delimited code column.
    code_col
        Column with one or more codes per row.
    sep
        Delimiter between codes.
    output_col
        Name of the exploded output code column.
    keep_empty
        If True, keep rows without codes and set ``output_col`` to missing.

    Returns
    -------
    pandas.DataFrame
        Exploded DataFrame with one row per parsed code.
    """

    _require_columns(df, [code_col])
    rows: list[pd.Series] = []
    for _, row in df.iterrows():
        codes = split_code_string(row[code_col], sep=sep)
        if not codes and keep_empty:
            new_row = row.copy()
            new_row[output_col] = pd.NA
            rows.append(new_row)
        for code in codes:
            new_row = row.copy()
            new_row[output_col] = code
            rows.append(new_row)
    if not rows:
        columns = list(df.columns)
        if output_col not in columns:
            columns.append(output_col)
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).reset_index(drop=True)


def add_code_indicators(
    df: pd.DataFrame,
    code_col: str,
    codes: Sequence[Any] | Mapping[str, Sequence[Any]],
    *,
    sep: str = ";",
    prefix: str = "code_",
    normalize: bool = True,
) -> pd.DataFrame:
    """Add binary indicator columns for selected clinical codes.

    Parameters
    ----------
    df
        DataFrame containing a code column.
    code_col
        Column with one or more codes per row.
    codes
        Either a sequence of codes or a mapping from output names to code lists.
    sep
        Delimiter between multiple codes in one cell.
    prefix
        Prefix used for generated indicator columns.
    normalize
        If True, normalize both input and target codes before matching.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with binary indicator columns.
    """

    _require_columns(df, [code_col])
    out = df.copy()
    targets = _indicator_targets(codes, normalize=normalize)
    parsed = out[code_col].apply(lambda value: set(split_code_string(value, sep=sep, normalize=normalize)))
    for name, target_codes in targets.items():
        out[f"{prefix}{_slug(name)}"] = parsed.apply(lambda values, target_codes=target_codes: int(bool(values & target_codes)))
    return out


def date_difference(
    start: Any,
    end: Any,
    *,
    unit: TimeUnit = "days",
    absolute: bool = False,
    errors: str = "coerce",
) -> pd.Series:
    """Calculate a date difference in days, weeks, months, or years.

    Parameters
    ----------
    start
        Start date scalar or array-like value.
    end
        End date scalar or array-like value.
    unit
        Output unit: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``.
    absolute
        If True, return absolute differences.
    errors
        ``"coerce"`` makes malformed dates missing; ``"raise"`` rejects them.
        Aware timestamps use UTC elapsed time; naive/aware mixtures raise.
        Scalars broadcast to vectors; Series indices must agree exactly.

    Returns
    -------
    pandas.Series
        Numeric difference in the requested unit.
    """

    diff = _date_difference(start, end, unit=unit, errors=errors)
    if absolute:
        diff = diff.abs()
    return diff.astype(float)


def add_date_difference(
    df: pd.DataFrame,
    start_col: str,
    end_col: str,
    output_col: str,
    *,
    unit: TimeUnit = "days",
    absolute: bool = False,
    allow_negative: bool = True,
    errors: str = "coerce",
) -> pd.DataFrame:
    """Add a date-difference feature from two DataFrame columns.

    Parameters
    ----------
    df
        DataFrame containing start and end date columns.
    start_col
        Start date column.
    end_col
        End date column.
    output_col
        Name of the created numeric difference column.
    unit
        Output unit: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``.
    absolute
        If True, store absolute differences.
    allow_negative
        If False, raise when a non-missing negative interval is computed.
    errors
        Date parsing policy: ``"coerce"`` (default) or ``"raise"``.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with the created difference column.
    """

    _require_columns(df, [start_col, end_col])
    out = df.copy()
    diff = date_difference(out[start_col], out[end_col], unit=unit, absolute=absolute, errors=errors)
    if not allow_negative and (diff.dropna() < 0).any():
        raise ValueError("Negative date differences computed; check start/end columns.")
    out[output_col] = diff
    return out


def age_at_date(
    df: pd.DataFrame,
    birth_date_col: str,
    reference_date_col: str,
    *,
    output_col: str = "age_years",
    errors: str = "coerce",
) -> pd.DataFrame:
    """Add age in years at a reference date.

    Parameters
    ----------
    df
        DataFrame containing birth and reference dates.
    birth_date_col
        Date-of-birth column.
    reference_date_col
        Date column where age should be calculated, such as diagnosis or index date.
    output_col
        Name of the created age column.
    errors
        Date parsing policy: ``"coerce"`` (default) or ``"raise"``. Age is
        elapsed days divided by 365.25, not completed calendar birthdays.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with age in years.
    """

    return add_date_difference(
        df,
        birth_date_col,
        reference_date_col,
        output_col,
        unit="years",
        allow_negative=False,
        errors=errors,
    )


def add_time_window_flag(
    df: pd.DataFrame,
    date_col: str,
    index_date_col: str,
    output_col: str,
    *,
    before: float | None = None,
    after: float | None = None,
    unit: TimeUnit = "days",
    errors: str = "coerce",
) -> pd.DataFrame:
    """Flag rows where a date falls within a window around an index date.

    Parameters
    ----------
    df
        DataFrame containing event and index date columns.
    date_col
        Date to test against the index date.
    index_date_col
        Index/reference date column.
    output_col
        Name of the created binary flag column.
    before
        Maximum time before the index date allowed in the window.
    after
        Maximum time after the index date allowed in the window.
    unit
        Window unit: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``.
    errors
        Date parsing policy: ``"coerce"`` (default) or ``"raise"``. Missing dates
        produce zero flags. Bounds must be finite and nonnegative.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with an integer 0/1 window flag column.
    """

    if before is None and after is None:
        raise ValueError("At least one of before or after must be provided.")
    for bound in (before, after):
        if bound is not None and (not math.isfinite(float(bound)) or float(bound) < 0):
            raise ValueError("Time-window bounds must be finite and nonnegative.")
    _require_columns(df, [date_col, index_date_col])
    out = df.copy()
    diff = date_difference(out[index_date_col], out[date_col], unit=unit, errors=errors)
    mask = diff.notna()
    if before is not None:
        mask &= diff >= -float(before)
    if after is not None:
        mask &= diff <= float(after)
    out[output_col] = mask.astype(int)
    return out


def _indicator_prevalence(
    df: pd.DataFrame,
    *,
    group_cols: Sequence[str] | None,
    prefix: str,
    label_col: str,
) -> pd.DataFrame:
    cols = list(group_cols or [col for col in df.columns if col.startswith(prefix)])
    if not cols:
        raise ValueError(f"No indicator columns found with prefix {prefix!r}.")
    _require_columns(df, cols)
    denom = len(df)
    rows = []
    for col in cols:
        n = int(pd.to_numeric(df[col], errors="coerce").fillna(0).astype(bool).sum())
        rows.append(
            {
                label_col: col.removeprefix(prefix),
                "column": col,
                "n_patients": n,
                "percent": round(100 * n / denom, 1) if denom else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("n_patients", ascending=False).reset_index(drop=True)


def _indicator_targets(
    codes: Sequence[Any] | Mapping[str, Sequence[Any]],
    *,
    normalize: bool,
) -> dict[str, set[str]]:
    if isinstance(codes, Mapping):
        items = codes.items()
    else:
        items = [(str(code), [code]) for code in codes]
    targets: dict[str, set[str]] = {}
    for name, values in items:
        normalized = {
            normalize_code(value) if normalize else str(value).strip()
            for value in values
            if not pd.isna(value)
        }
        targets[str(name)] = {value for value in normalized if value}
    if not targets:
        raise ValueError("codes must contain at least one target code.")
    return targets


def _time_unit_factor(unit: TimeUnit) -> float:
    return time_unit_factor(unit)


def _slug(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def _require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


__all__ = [
    "ICD10_DISEASE_GROUPS",
    "CHARLSON_CATEGORY_ORDER",
    "CHARLSON_WEIGHTS",
    "ENCOUNTER_TYPE_MAPPING",
    "OPS_CATEGORIES",
    "add_charlson_comorbidity_columns",
    "add_code_indicators",
    "add_date_difference",
    "add_encounter_type_features",
    "add_icd10_disease_groups",
    "add_mdc_partition",
    "add_ops_categories",
    "add_time_window_flag",
    "aggregate_code_rows",
    "aggregate_ops_by_encounter",
    "age_at_date",
    "charlson_comorbidity_index",
    "classify_elective_status",
    "classify_charlson_comorbidities",
    "classify_icd10",
    "classify_icd10_string",
    "classify_mdc_partition",
    "classify_ops",
    "classify_ops_string",
    "date_difference",
    "derive_charlson_category",
    "explode_code_column",
    "get_ops_chapter",
    "icd10_group_prevalence",
    "normalize_code",
    "normalize_ops_codes",
    "ops_category_prevalence",
    "split_code_string",
]
