"""Transparent rule-based phenotyping for clinical tables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import reduce
from typing import Any, Literal

import numpy as np
import pandas as pd

CombineStrategy = Literal["any", "all"]
ThresholdDirection = Literal[">=", ">", "<=", "<", "==", "!="]


def define_code_phenotype(
    df: pd.DataFrame,
    code_col: str,
    codes: Sequence[Any],
    *,
    patient_col: str = "patient_id",
    date_col: str | None = None,
    phenotype_name: str = "phenotype",
    code_system_col: str | None = None,
    code_systems: Sequence[Any] | None = None,
) -> pd.DataFrame:
    """Define a phenotype from diagnosis/procedure/code rows."""

    required = [patient_col, code_col] + ([date_col] if date_col else []) + ([code_system_col] if code_system_col else [])
    _require_columns(df, required)
    if not codes:
        raise ValueError("codes must contain at least one value.")
    work = df.copy()
    mask = work[code_col].astype(str).isin({str(code) for code in codes})
    if code_system_col and code_systems is not None:
        mask &= work[code_system_col].astype(str).isin({str(system) for system in code_systems})
    return _aggregate_evidence(
        work.loc[mask],
        patient_col=patient_col,
        flag_col=phenotype_name,
        date_col=date_col,
        evidence_col=code_col,
        extra={"rule_type": "code", "codes": ",".join(map(str, codes))},
    )


def define_lab_threshold_phenotype(
    df: pd.DataFrame,
    value_col: str,
    threshold: float,
    *,
    direction: ThresholdDirection = ">=",
    patient_col: str = "patient_id",
    date_col: str | None = None,
    phenotype_name: str = "phenotype",
) -> pd.DataFrame:
    """Define a phenotype from numeric lab/measurement thresholds."""

    _require_columns(df, [patient_col, value_col] + ([date_col] if date_col else []))
    values = pd.to_numeric(df[value_col], errors="coerce")
    if not np.isfinite(threshold):
        raise ValueError("threshold must be finite.")
    mask = np.isfinite(values) & _threshold_mask(values, threshold, direction)
    return _aggregate_evidence(
        df.loc[mask],
        patient_col=patient_col,
        flag_col=phenotype_name,
        date_col=date_col,
        evidence_col=value_col,
        extra={"rule_type": "lab_threshold", "direction": direction, "threshold": threshold},
    )


def define_medication_exposure(
    df: pd.DataFrame,
    medication_col: str,
    medications: Sequence[Any],
    *,
    patient_col: str = "patient_id",
    start_col: str | None = None,
    end_col: str | None = None,
    phenotype_name: str = "exposure",
) -> pd.DataFrame:
    """Define medication exposure from medication name/code rows."""

    required = [patient_col, medication_col] + ([start_col] if start_col else []) + ([end_col] if end_col else [])
    _require_columns(df, required)
    if not medications:
        raise ValueError("medications must contain at least one value.")
    needle = {str(med).lower() for med in medications}
    mask = df[medication_col].astype(str).str.lower().isin(needle)
    out = _aggregate_evidence(
        df.loc[mask],
        patient_col=patient_col,
        flag_col=phenotype_name,
        date_col=start_col,
        evidence_col=medication_col,
        extra={"rule_type": "medication", "medications": ",".join(map(str, medications))},
    )
    if end_col and not out.empty:
        end_dates = pd.to_datetime(df.loc[mask, [patient_col, end_col]][end_col], errors="coerce")
        latest = df.loc[mask].assign(_end=end_dates).groupby(patient_col, dropna=False)["_end"].max()
        out["last_exposure_end"] = out[patient_col].map(latest)
    return out


def combine_phenotypes(
    tables: Sequence[pd.DataFrame],
    *,
    patient_col: str = "patient_id",
    strategy: CombineStrategy = "any",
    phenotype_name: str = "combined",
) -> pd.DataFrame:
    """Combine patient-level phenotype tables with an any/all rule."""

    if not tables:
        raise ValueError("tables must contain at least one phenotype table.")
    if strategy not in {"any", "all"}:
        raise ValueError("strategy must be 'any' or 'all'.")
    prepared = []
    flag_cols = []
    for index, table in enumerate(tables):
        _require_columns(table, [patient_col])
        flag_col = _first_non_metadata_flag(table, patient_col)
        _validate_patient_flags(table, patient_col, flag_col)
        if table[patient_col].duplicated().any():
            raise ValueError("Combination inputs must have unique patient keys.")
        name = f"phenotype_{index + 1}"
        flag_cols.append(name)
        prepared.append(table[[patient_col, flag_col]].rename(columns={flag_col: name}))
    if phenotype_name in {patient_col, "evidence_count", *flag_cols}:
        raise ValueError("phenotype_name conflicts with an output column.")
    merged = reduce(lambda left, right: pd.merge(left, right, on=patient_col, how="outer", validate="one_to_one"), prepared)
    bools = merged[flag_cols].fillna(False).astype(bool)
    merged[flag_cols] = bools
    merged[phenotype_name] = bools.any(axis=1) if strategy == "any" else bools.all(axis=1)
    merged["evidence_count"] = bools.sum(axis=1).astype(int)
    return merged[[patient_col, phenotype_name, "evidence_count", *flag_cols]]


def phenotype_summary(
    df: pd.DataFrame,
    phenotype_col: str,
    *,
    patient_col: str = "patient_id",
    group_col: str | None = None,
) -> pd.DataFrame:
    """Summarize phenotype prevalence overall or by group."""

    _require_columns(df, [patient_col, phenotype_col] + ([group_col] if group_col else []))
    _validate_patient_flags(df, patient_col, phenotype_col)
    for col in [phenotype_col] + ([group_col] if group_col else []):
        if df.groupby(patient_col)[col].nunique(dropna=False).gt(1).any():
            raise ValueError("Conflicting patient-level flags or groups.")
    groups = [(None, df)] if group_col is None else list(df.groupby(group_col, dropna=False))
    rows = []
    for group, group_df in groups:
        patient_level = group_df[[patient_col, phenotype_col]].drop_duplicates(patient_col)
        flags = patient_level[phenotype_col].astype(bool)
        row = {
            "group": "overall" if group_col is None else group,
            "n_patients": int(len(patient_level)),
            "n_phenotype": int(flags.sum()),
            "prevalence_percent": float(flags.mean() * 100) if len(flags) else 0.0,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def _aggregate_evidence(
    evidence: pd.DataFrame,
    *,
    patient_col: str,
    flag_col: str,
    date_col: str | None,
    evidence_col: str,
    extra: Mapping[str, Any],
) -> pd.DataFrame:
    columns = [patient_col, flag_col, "evidence_count", "evidence_values", *extra.keys()]
    if date_col:
        columns.extend(["first_date", "last_date"])
    if evidence.empty:
        return pd.DataFrame(columns=columns)
    grouped = evidence.groupby(patient_col, dropna=False)
    out = grouped.size().rename("evidence_count").reset_index()
    out[flag_col] = True
    values = grouped[evidence_col].apply(lambda s: "|".join(sorted({str(v) for v in s.dropna()})))
    out["evidence_values"] = out[patient_col].map(values)
    if date_col:
        dates = pd.to_datetime(evidence[date_col], errors="coerce")
        dated = evidence.assign(_date=dates).groupby(patient_col, dropna=False)["_date"]
        out["first_date"] = out[patient_col].map(dated.min())
        out["last_date"] = out[patient_col].map(dated.max())
    for key, value in extra.items():
        out[key] = value
    return out


def _threshold_mask(values: pd.Series, threshold: float, direction: ThresholdDirection) -> pd.Series:
    if direction == ">=":
        return values >= threshold
    if direction == ">":
        return values > threshold
    if direction == "<=":
        return values <= threshold
    if direction == "<":
        return values < threshold
    if direction == "==":
        return values == threshold
    if direction == "!=":
        return values != threshold
    raise ValueError("direction must be one of >=, >, <=, <, ==, !=")


def _first_non_metadata_flag(table: pd.DataFrame, patient_col: str) -> str:
    excluded = {patient_col, "evidence_count", "evidence_values", "first_date", "last_date", "rule_type",
                "codes", "direction", "threshold", "medications", "last_exposure_end"}
    candidates = [col for col in table.columns if col not in excluded]
    if len(candidates) != 1:
        raise ValueError("Could not infer phenotype flag column.")
    return candidates[0]


def _validate_patient_flags(table: pd.DataFrame, patient_col: str, flag_col: str) -> None:
    if table[patient_col].isna().any():
        raise ValueError("Patient keys must not be missing.")
    flags = table[flag_col]
    if flags.isna().any() or not flags.isin([True, False, 0, 1]).all():
        raise ValueError("Phenotype flags must be nonmissing binary values.")


def _require_columns(df: pd.DataFrame, columns: Sequence[str | None]) -> None:
    missing = [col for col in columns if col and col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
