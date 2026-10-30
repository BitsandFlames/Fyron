"""Encounter type feature helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

ENCOUNTER_TYPE_MAPPING = {
    "AMB": "elective",
    "IMP": "elective",
    "EMER": "non_elective",
}


def classify_elective_status(encounter_type: Any) -> str:
    """Classify elective status from an encounter type code.

    Parameters
    ----------
    encounter_type
        Encounter type such as ``"AMB"``, ``"IMP"``, or ``"EMER"``.

    Returns
    -------
    str
        ``"elective"``, ``"non_elective"``, or ``"unknown"``.
    """

    if encounter_type is None or pd.isna(encounter_type):
        return "unknown"
    normalized_type = str(encounter_type).strip().upper()
    if not normalized_type:
        return "unknown"
    return ENCOUNTER_TYPE_MAPPING.get(normalized_type, "unknown")


def add_encounter_type_features(
    df: pd.DataFrame,
    encounter_type_column: str = "pni_encounter_type",
) -> pd.DataFrame:
    """Add normalized encounter type and elective-status columns.

    Parameters
    ----------
    df
        DataFrame with an encounter type column.
    encounter_type_column
        Source column containing encounter type codes.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with ``pni_encounter_type_normalized`` and
        ``pni_encounter_elective_status``.
    """

    out = df.copy()
    if encounter_type_column not in out.columns:
        out["pni_encounter_type_normalized"] = pd.NA
        out["pni_encounter_elective_status"] = "unknown"
        return out
    normalized = out[encounter_type_column].astype("string").str.strip().str.upper()
    normalized = normalized.mask(normalized.isin(["", "NAN", "NONE", "<NA>"]))
    out["pni_encounter_type_normalized"] = normalized
    out["pni_encounter_elective_status"] = normalized.map(classify_elective_status).fillna("unknown")
    return out
