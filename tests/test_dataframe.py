from __future__ import annotations

import math

import pandas as pd
import pytest

from fyron import dataframe as fdf


def test_icd10_classification_and_group_columns() -> None:
    assert fdf.classify_icd10("C34") == "Cancer"
    assert fdf.classify_icd10("d05") == "Benign / In Situ Neoplasm"
    assert fdf.classify_icd10("D70") == "Hematologic / Immune"
    assert fdf.classify_icd10("I50.1") == "Cardiovascular"
    assert fdf.classify_icd10("Z51") == "Healthcare Encounter"
    assert fdf.classify_icd10("not-a-code") == "Other"
    assert fdf.classify_icd10(None) is None

    assert fdf.classify_icd10_string("c34; I50 ; z51") == {
        "Cancer",
        "Cardiovascular",
        "Healthcare Encounter",
    }
    assert fdf.classify_icd10_string(None) == set()

    source = pd.DataFrame({"patient_id": ["p1", "p2", "p3"], "icd": ["C34; I50", "D70", None]})
    out = fdf.add_icd10_disease_groups(source, "icd")
    assert "icd10_group_cancer" in out.columns
    assert "icd10_group_cardiovascular" in out.columns
    assert out.loc[0, "icd10_group_cancer"] == 1
    assert out.loc[0, "icd10_group_cardiovascular"] == 1
    assert out.loc[1, "icd10_group_hematologic_immune"] == 1
    assert out.loc[2, "icd10_groups"] == "Unknown"
    assert "icd10_group_cancer" not in source.columns

    prevalence = fdf.icd10_group_prevalence(out)
    cancer = prevalence.set_index("column").loc["icd10_group_cancer"]
    assert cancer["n_patients"] == 1
    assert cancer["percent"] == 33.3


def test_ops_classification_and_category_columns() -> None:
    assert fdf.classify_ops("1-620") == "Diagnostic Procedures"
    assert fdf.classify_ops("3-20") == "Imaging"
    assert fdf.classify_ops("5-541") == "Surgery"
    assert fdf.classify_ops("6-001") == "Medication / Therapy"
    assert fdf.classify_ops("8-980") == "Intensive Care"
    assert fdf.classify_ops("9-200") == "Rehabilitation"
    assert fdf.classify_ops("x") == "Other"
    assert fdf.classify_ops(None) is None

    source = pd.DataFrame({"ops": ["5-541; 8-980", "3-20", ""]})
    out = fdf.add_ops_categories(source, "ops")
    assert out.loc[0, "ops_category_surgery"] == 1
    assert out.loc[0, "ops_category_intensive_care"] == 1
    assert out.loc[1, "ops_category_imaging"] == 1
    assert out.loc[2, "ops_categories"] == "Unknown"

    prevalence = fdf.ops_category_prevalence(out)
    assert {"category", "column", "n_patients", "percent"}.issubset(prevalence.columns)


def test_general_code_utilities() -> None:
    assert fdf.normalize_code(" c34.1 ") == "C34.1"
    assert fdf.normalize_code(" c34.1 ", remove_dots=True) == "C341"
    assert fdf.normalize_code("") is None
    assert fdf.split_code_string(" a ; b ; ; c ") == ["A", "B", "C"]

    df = pd.DataFrame({"patient_id": ["p1", "p2"], "codes": ["A; B", None]})
    exploded = fdf.explode_code_column(df, "codes")
    assert exploded["code"].tolist() == ["A", "B"]

    exploded_keep = fdf.explode_code_column(df, "codes", keep_empty=True)
    assert len(exploded_keep) == 3
    assert pd.isna(exploded_keep.loc[2, "code"])

    indicators = fdf.add_code_indicators(
        df,
        "codes",
        {"has_a": ["A"], "has_c": ["C"]},
        prefix="local_",
    )
    assert indicators["local_has_a"].tolist() == [1, 0]
    assert indicators["local_has_c"].tolist() == [0, 0]


def test_date_difference_helpers() -> None:
    diff = fdf.date_difference(
        pd.Series(["2020-01-01", "2020-01-10"]),
        pd.Series(["2020-01-11", "2020-01-01"]),
    )
    assert diff.tolist() == [10.0, -9.0]
    assert fdf.date_difference(["2020-01-01"], ["2020-01-08"], unit="weeks").iloc[0] == 1.0
    assert math.isclose(fdf.date_difference(["2020-01-01"], ["2021-01-01"], unit="years").iloc[0], 366 / 365.25)
    assert fdf.date_difference(["2020-01-10"], ["2020-01-01"], absolute=True).iloc[0] == 9.0
    with pytest.raises(ValueError):
        fdf.date_difference(["2020-01-01"], ["2020-01-02"], unit="hours")  # type: ignore[arg-type]

    df = pd.DataFrame(
        {
            "birth": ["1980-01-01", "1990-01-01"],
            "index": ["2020-01-01", "2020-07-01"],
            "scan": ["2019-12-15", "2021-01-01"],
        }
    )
    out = fdf.add_date_difference(df, "index", "scan", "scan_delta_days", allow_negative=True)
    assert out["scan_delta_days"].round().tolist() == [-17.0, 184.0]

    with pytest.raises(ValueError, match="Negative date differences"):
        fdf.add_date_difference(df, "index", "scan", "scan_delta_days", allow_negative=False)

    aged = fdf.age_at_date(df, "birth", "index")
    assert aged["age_years"].iloc[0] >= 39.9

    window = fdf.add_time_window_flag(df, "scan", "index", "baseline_scan", before=30, after=30)
    assert window["baseline_scan"].tolist() == [1, 0]
