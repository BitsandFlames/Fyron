from __future__ import annotations

import pandas as pd

from fyron import clinical_codes as fcc
from fyron import dataframe as fdf


def test_clinical_codes_icd10_groups_match_dataframe_surface() -> None:
    assert fcc.classify_icd10("C34") == "Cancer"
    assert fcc.classify_icd10("d05") == "Benign / In Situ Neoplasm"
    assert fcc.classify_icd10("D70") == "Hematologic / Immune"
    assert fcc.classify_icd10("I50.1") == "Cardiovascular"
    assert fcc.classify_icd10("not-a-code") == "Other"
    assert fcc.classify_icd10(None) is None

    source = pd.DataFrame({"icd": ["C34; I50", "D70", None]})
    out = fcc.add_icd10_disease_groups(source, "icd")

    assert out.loc[0, "icd10_group_cancer"] == 1
    assert out.loc[0, "icd10_group_cardiovascular"] == 1
    assert out.loc[1, "icd10_group_hematologic_immune"] == 1
    assert out.loc[2, "icd10_groups"] == "Unknown"
    assert fdf.classify_icd10("C34") == fcc.classify_icd10("C34")


def test_ops_parsing_and_mdc_partition() -> None:
    assert fcc.normalize_ops_codes('["5-470.0", "8-930"]') == ["5-470.0", "8-930"]
    assert fcc.normalize_ops_codes("5-470.0, 8-930") == ["5-470.0", "8-930"]
    assert fcc.normalize_ops_codes(["1-632", None, ""]) == ["1-632"]
    assert fcc.normalize_ops_codes(None) == []

    assert fcc.get_ops_chapter("5-470.0") == "5"
    assert fcc.classify_mdc_partition("8-930; 3-20") == "medical"
    assert fcc.classify_mdc_partition("8-930; 5-470.0") == "surgical"
    assert fcc.classify_mdc_partition(None) == "other"
    assert fcc.classify_mdc_partition("not-a-code") == "other"

    source = pd.DataFrame({"ops_codes": ["8-930", "5-470.0; 8-930", None]})
    out = fcc.add_mdc_partition(source)

    assert out["mdc_partition"].tolist() == ["medical", "surgical", "other"]
    assert out["mdc_partition_source"].tolist() == ["ops_codes", "ops_codes", "ops_codes"]
    assert fdf.classify_mdc_partition("5-470.0") == "surgical"


def test_aggregate_one_code_per_row_tables_to_group_lists() -> None:
    procedures = pd.DataFrame(
        {
            "patient_id": ["p1", "p1", "p1", "p2", "p2", "p3"],
            "encounter_id": ["e1", "e1", "e1", "e2", "e2", "e3"],
            "performed_date": ["2024-01-03", "2024-01-01", "2024-01-01", None, "2024-02-01", "2024-03-01"],
            "ops_code": ["8-930", "5-470.0", "5-470.0", "", "3-20", None],
            "ops_display": ["Monitoring", "Resection", "Resection", "Missing", "Imaging", "Missing"],
        }
    )
    cohort = pd.DataFrame({"patient_id": ["p1", "p2", "p4"], "encounter_id": ["e1", "e2", "e4"]})

    out = fcc.aggregate_ops_by_encounter(procedures, complete_encounters=cohort)

    assert out["patient_id"].tolist() == ["p1", "p2", "p4"]
    assert out.loc[0, "ops_code_list"] == ["5-470.0", "8-930"]
    assert out.loc[0, "ops_display_list"] == ["Monitoring", "Resection"]
    assert str(out.loc[0, "ops_first_performed_date"]) == "2024-01-01 00:00:00+00:00"
    assert str(out.loc[0, "ops_last_performed_date"]) == "2024-01-03 00:00:00+00:00"
    assert out["n_ops_codes"].tolist() == [2, 1, 0]
    assert out.loc[2, "ops_code_list"] == []
    assert fdf.aggregate_ops_by_encounter(procedures, complete_encounters=cohort).equals(out)

    generic = fcc.aggregate_code_rows(
        procedures,
        ["patient_id", "encounter_id"],
        "ops_code",
        date_col="performed_date",
        code_list_col="codes",
        first_date_col="first_date",
        last_date_col="last_date",
        count_col="n_codes",
    )
    assert generic.loc[0, "codes"] == ["5-470.0", "8-930"]
    assert generic.loc[0, "n_codes"] == 2


def test_encounter_type_features() -> None:
    assert fcc.classify_elective_status("amb") == "elective"
    assert fcc.classify_elective_status("IMP") == "elective"
    assert fcc.classify_elective_status("EMER") == "non_elective"
    assert fcc.classify_elective_status("other") == "unknown"
    assert fcc.classify_elective_status(None) == "unknown"

    source = pd.DataFrame({"encounter_type": [" amb ", "EMER", "", None]})
    out = fcc.add_encounter_type_features(source, "encounter_type")

    assert out["pni_encounter_type_normalized"].tolist()[:2] == ["AMB", "EMER"]
    assert out["pni_encounter_elective_status"].tolist() == [
        "elective",
        "non_elective",
        "unknown",
        "unknown",
    ]


def test_charlson_category_and_missing_dependency_fallback() -> None:
    category = fcc.derive_charlson_category(pd.Series([0, 1, 2, 3, 4, 5, None]))

    values = list(category.astype("object"))
    assert values[:6] == ["0", "1-2", "1-2", "3-4", "3-4", ">=5"]
    assert pd.isna(values[6])
    assert category.ordered
    assert list(category.categories) == fcc.CHARLSON_CATEGORY_ORDER

    assert fcc.charlson_comorbidity_index("C34; I50") == 3
    assert fcc.charlson_comorbidity_index(None) is None
    indicators = fcc.classify_charlson_comorbidities("E11.9; E11.2; K74")
    assert indicators["diabetes_with_complication"] == 1
    assert indicators["diabetes_without_complication"] == 0
    assert indicators["mild_liver_disease"] == 1
    assert fcc.classify_charlson_comorbidities("E14.9")["diabetes_without_complication"] == 1

    source = pd.DataFrame({"encounter_id": ["e1", "e2"], "pni_icd": ["C34; I50", None]})
    out, skipped = fcc.add_charlson_comorbidity_columns(source)

    assert skipped is None
    assert "charlson_comorbidity_index" in out.columns
    assert "charlson_comorbidity_category" in out.columns
    assert out["charlson_comorbidity_index"].tolist() == [3, 0]
    assert out["charlson_congestive_heart_failure"].tolist() == [1, 0]


def test_missing_clinical_code_columns_are_explicit() -> None:
    missing_mdc = fcc.add_mdc_partition(pd.DataFrame({"x": [1]}))

    assert missing_mdc.loc[0, "mdc_partition"] == "other"
    assert pd.isna(missing_mdc.loc[0, "mdc_partition_source"])

    missing_charlson, skipped = fcc.add_charlson_comorbidity_columns(pd.DataFrame({"x": [1]}))

    assert skipped == "missing pni_icd"
    assert pd.isna(missing_charlson.loc[0, "charlson_comorbidity_index"])
