"""Charlson Comorbidity Index helpers from ICD-10 diagnosis codes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from .utils import split_code_string

CHARLSON_CATEGORY_ORDER = ["0", "1-2", "3-4", ">=5"]

CHARLSON_WEIGHTS = {
    "myocardial_infarction": 1,
    "congestive_heart_failure": 1,
    "peripheral_vascular_disease": 1,
    "cerebrovascular_disease": 1,
    "dementia": 1,
    "chronic_pulmonary_disease": 1,
    "rheumatic_disease": 1,
    "peptic_ulcer_disease": 1,
    "mild_liver_disease": 1,
    "diabetes_without_complication": 1,
    "diabetes_with_complication": 2,
    "paraplegia_or_hemiplegia": 2,
    "renal_disease": 2,
    "any_malignancy": 2,
    "moderate_or_severe_liver_disease": 3,
    "metastatic_solid_tumor": 6,
    "aids_hiv": 6,
}


def derive_charlson_category(score: pd.Series) -> pd.Categorical:
    """Bin Charlson scores into ordered clinical categories.

    Parameters
    ----------
    score
        Numeric Charlson Comorbidity Index values.

    Returns
    -------
    pandas.Categorical
        Ordered categories ``"0"``, ``"1-2"``, ``"3-4"``, and ``">=5"``.
    """

    numeric = pd.to_numeric(score, errors="coerce")
    values = pd.Series(pd.NA, index=score.index, dtype="object")
    values[numeric.eq(0)] = "0"
    values[numeric.between(1, 2, inclusive="both")] = "1-2"
    values[numeric.between(3, 4, inclusive="both")] = "3-4"
    values[numeric.ge(5)] = ">=5"
    return pd.Categorical(values, categories=CHARLSON_CATEGORY_ORDER, ordered=True)


def classify_charlson_comorbidities(icd_codes: Any) -> dict[str, int]:
    """Classify ICD-10 codes into Charlson comorbidity indicators.

    Parameters
    ----------
    icd_codes
        Missing value, semicolon-separated ICD-10 string, or iterable of ICD-10
        codes.

    Returns
    -------
    dict[str, int]
        Binary Charlson comorbidity indicators using explicit ICD-10 ranges.
    """

    codes = _split_icd_codes(icd_codes)
    indicators = {name: 0 for name in CHARLSON_WEIGHTS}
    for code in codes:
        for name in _charlson_conditions_for_code(code):
            indicators[name] = 1

    # Apply common Charlson hierarchies so severe forms do not double-count
    # their milder parent categories.
    if indicators["diabetes_with_complication"]:
        indicators["diabetes_without_complication"] = 0
    if indicators["moderate_or_severe_liver_disease"]:
        indicators["mild_liver_disease"] = 0
    if indicators["metastatic_solid_tumor"]:
        indicators["any_malignancy"] = 0
    return indicators


def charlson_comorbidity_index(icd_codes: Any) -> int | None:
    """Calculate a Charlson Comorbidity Index score from ICD-10 codes.

    Parameters
    ----------
    icd_codes
        Missing value, semicolon-separated ICD-10 string, or iterable of ICD-10
        codes.

    Returns
    -------
    int or None
        Charlson score, or None when no parsable ICD-10 codes are present.
    """

    codes = _split_icd_codes(icd_codes)
    if not codes:
        return None
    indicators = classify_charlson_comorbidities(codes)
    return int(sum(CHARLSON_WEIGHTS[name] * value for name, value in indicators.items()))


def add_charlson_comorbidity_columns(
    df: pd.DataFrame,
    icd_column: str = "pni_icd",
    id_column: str | None = None,
) -> tuple[pd.DataFrame, str | None]:
    """Add Charlson Comorbidity Index columns from ICD-10 code strings.

    Parameters
    ----------
    df
        DataFrame containing ICD-10 code strings.
    icd_column
        Column containing one or more semicolon-separated ICD-10 codes.
    id_column
        Optional encounter or patient identifier column. Repeated IDs are
        scored across all ICD-10 codes observed for that ID.

    Returns
    -------
    tuple[pandas.DataFrame, str or None]
        DataFrame copy with ``charlson_comorbidity_index``,
        ``charlson_comorbidity_category``, and binary ``charlson_*``
        comorbidity indicators. ``skipped_reason`` is None when scoring
        succeeds.
    """

    result = df.copy()
    if icd_column not in result.columns:
        _add_empty_charlson_columns(result)
        return result, f"missing {icd_column}"

    if id_column is not None and id_column not in result.columns:
        _add_empty_charlson_columns(result)
        return result, f"missing {id_column}"

    parsed = result[icd_column].map(_split_icd_codes)
    if not parsed.map(bool).any():
        _add_empty_charlson_columns(result)
        return result, f"no parsable ICD codes in {icd_column}"

    if id_column is None:
        indicators = parsed.map(classify_charlson_comorbidities)
        for name in CHARLSON_WEIGHTS:
            result[f"charlson_{name}"] = indicators.map(lambda values, name=name: values[name]).astype(int)
        result["charlson_comorbidity_index"] = indicators.map(_score_indicators).astype(int)
    else:
        grouped_codes = (
            pd.DataFrame({id_column: result[id_column], "__charlson_codes": parsed})
            .groupby(id_column, dropna=False)["__charlson_codes"]
            .agg(_flatten_codes)
        )
        grouped_indicators = grouped_codes.map(classify_charlson_comorbidities)
        grouped_scores = grouped_indicators.map(_score_indicators)
        result["charlson_comorbidity_index"] = result[id_column].map(grouped_scores).astype(int)
        for name in CHARLSON_WEIGHTS:
            values = grouped_indicators.map(lambda item, name=name: item[name])
            result[f"charlson_{name}"] = result[id_column].map(values).astype(int)

    result["charlson_comorbidity_category"] = derive_charlson_category(result["charlson_comorbidity_index"])
    return result, None


def _charlson_conditions_for_code(code: str) -> set[str]:
    conditions: set[str] = set()
    if _matches(code, ["I21", "I22", "I252"]):
        conditions.add("myocardial_infarction")
    if _matches(code, ["I099", "I110", "I130", "I132", "I255", "I420", ("I425", "I429"), "I43", "I50", "P290"]):
        conditions.add("congestive_heart_failure")
    if _matches(code, ["I70", "I71", "I731", "I738", "I739", "I771", "I790", "I792", "K551", "K558", "K559", "Z958", "Z959"]):
        conditions.add("peripheral_vascular_disease")
    if _matches(code, ["G45", "G46", "H340", ("I60", "I69")]):
        conditions.add("cerebrovascular_disease")
    if _matches(code, ["F00", "F01", "F02", "F03", "F051", "G30", "G311"]):
        conditions.add("dementia")
    if _matches(code, [("I278", "I279"), ("J40", "J47"), ("J60", "J67"), "J684", "J701", "J703"]):
        conditions.add("chronic_pulmonary_disease")
    if _matches(code, ["M05", "M06", "M315", ("M32", "M34"), "M351", "M353", "M360"]):
        conditions.add("rheumatic_disease")
    if _matches(code, [("K25", "K28")]):
        conditions.add("peptic_ulcer_disease")
    if _matches(code, ["B18", ("K700", "K703"), "K709", ("K713", "K715"), "K717", "K73", "K74", "K760", ("K762", "K764"), "K768", "K769", "Z944"]):
        conditions.add("mild_liver_disease")
    if _matches_diabetes_complication(code, {"0", "1", "6", "8", "9"}):
        conditions.add("diabetes_without_complication")
    if _matches_diabetes_complication(code, {"2", "3", "4", "5", "7"}):
        conditions.add("diabetes_with_complication")
    if _matches(code, ["G041", "G114", ("G801", "G802"), "G81", "G82", ("G830", "G834"), "G839"]):
        conditions.add("paraplegia_or_hemiplegia")
    if _matches(code, ["I120", "I131", "N18", "N19", ("N032", "N037"), ("N052", "N057"), "N25", "N26", "Z490", "Z491", "Z492", "Z940", "Z992"]):
        conditions.add("renal_disease")
    if _matches(code, [("C00", "C26"), ("C30", "C34"), ("C37", "C41"), "C43", ("C45", "C58"), ("C60", "C76"), ("C81", "C85"), "C88", ("C90", "C97")]):
        conditions.add("any_malignancy")
    if _matches(code, ["I850", "I859", "I864", "I982", "K704", "K711", "K721", "K729", ("K765", "K767")]):
        conditions.add("moderate_or_severe_liver_disease")
    if _matches(code, [("C77", "C80")]):
        conditions.add("metastatic_solid_tumor")
    if _matches(code, [("B20", "B22"), "B24"]):
        conditions.add("aids_hiv")
    return conditions


def _matches(code: str, patterns: Iterable[str | tuple[str, str]]) -> bool:
    return any(_matches_one(code, pattern) for pattern in patterns)


def _matches_one(code: str, pattern: str | tuple[str, str]) -> bool:
    if isinstance(pattern, tuple):
        start, end = pattern
        width = min(len(start), len(end))
        prefix = code[:width]
        return start <= prefix <= end
    return code.startswith(pattern)


def _matches_diabetes_complication(code: str, complication_digits: set[str]) -> bool:
    return len(code) >= 4 and code[:3] in {"E10", "E11", "E12", "E13", "E14"} and code[3] in complication_digits


def _split_icd_codes(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        raw_codes = [str(code) for code in value if code is not None]
    else:
        raw_codes = split_code_string(value, sep=";")
    return [_normalize_icd_for_charlson(code) for code in raw_codes if _normalize_icd_for_charlson(code)]


def _normalize_icd_for_charlson(code: Any) -> str:
    return str(code).upper().strip().replace(" ", "").replace(".", "")


def _flatten_codes(values: Iterable[list[str]]) -> list[str]:
    codes: list[str] = []
    for row_codes in values:
        codes.extend(row_codes)
    return codes


def _score_indicators(indicators: dict[str, int]) -> int:
    return int(sum(CHARLSON_WEIGHTS[name] * value for name, value in indicators.items()))


def _add_empty_charlson_columns(df: pd.DataFrame) -> None:
    df["charlson_comorbidity_index"] = pd.NA
    df["charlson_comorbidity_category"] = pd.Categorical(
        pd.Series(pd.NA, index=df.index, dtype="object"),
        categories=CHARLSON_CATEGORY_ORDER,
        ordered=True,
    )
