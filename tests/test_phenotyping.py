"""Tests for rule-based phenotyping helpers."""

from __future__ import annotations

import pandas as pd

from fyron.phenotyping import (
    combine_phenotypes,
    define_code_phenotype,
    define_lab_threshold_phenotype,
    define_medication_exposure,
    phenotype_summary,
)


def test_code_lab_medication_phenotypes_and_summary() -> None:
    codes = pd.DataFrame(
        {
            "patient_id": ["p1", "p1", "p2"],
            "code": ["A", "B", "C"],
            "date": ["2020-01-01", "2020-02-01", "2020-03-01"],
            "system": ["ICD", "ICD", "ICD"],
        }
    )
    code_pheno = define_code_phenotype(codes, "code", ["A"], date_col="date", code_system_col="system", code_systems=["ICD"])
    assert bool(code_pheno.loc[0, "phenotype"]) is True
    assert code_pheno.loc[0, "evidence_count"] == 1

    labs = pd.DataFrame({"patient_id": ["p1", "p2"], "value": [9.0, 4.0], "date": ["2020-01-01", "2020-01-02"]})
    lab_pheno = define_lab_threshold_phenotype(labs, "value", 5.0, direction=">", date_col="date", phenotype_name="high_lab")
    assert lab_pheno["patient_id"].tolist() == ["p1"]

    meds = pd.DataFrame({"patient_id": ["p1", "p2"], "med": ["drug-a", "drug-b"], "start": ["2020-01-01", "2020-02-01"]})
    med_pheno = define_medication_exposure(meds, "med", ["drug-b"], start_col="start")
    assert med_pheno["patient_id"].tolist() == ["p2"]

    combined = combine_phenotypes([code_pheno, lab_pheno.rename(columns={"high_lab": "phenotype"})])
    assert set(combined["patient_id"]) == {"p1"}

    source = pd.DataFrame({"patient_id": ["p1", "p2"], "has_it": [True, False], "sex": ["F", "M"]})
    summary = phenotype_summary(source, "has_it", group_col="sex")
    assert set(summary["group"]) == {"F", "M"}
