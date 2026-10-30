from __future__ import annotations

import pandas as pd
import pytest

from fyron import preprocessing as fp


def test_preprocessing_qc_tables() -> None:
    df = pd.DataFrame(
        {
            "patient_id": ["p1", "p1", "p2"],
            "age": [60, None, 71],
            "sex": ["F", "F", "M"],
            "outcome_event": [1, 0, 1],
        }
    )

    missing = fp.summarize_missingness(df, columns=["age", "sex"])
    assert missing.loc[missing["column"] == "age", "missing"].iloc[0] == 1

    duplicates = fp.find_duplicate_ids(df)
    assert set(duplicates["patient_id"]) == {"p1"}

    levels = fp.summarize_categorical_levels(df, columns=["sex"])
    assert set(levels["level"]) == {"F", "M"}

    leakage = fp.detect_potential_leakage(df)
    assert "outcome_event" in set(leakage["column"])


def test_compare_train_test_balance_and_missing_column() -> None:
    train = pd.DataFrame({"age": [50, 60], "sex": ["F", "M"]})
    test = pd.DataFrame({"age": [70], "sex": ["F"]})

    balance = fp.compare_train_test_balance(train, test)
    assert set(balance["column"]) == {"age", "sex"}

    with pytest.raises(ValueError):
        fp.summarize_missingness(train, columns=["missing"])


def test_feature_matrix_report_flags_constant_rare_and_leakage() -> None:
    X = pd.DataFrame(
        {
            "age": [50, 60, 70, 80],
            "constant": [1, 1, 1, 1],
            "outcome_score": [0.1, 0.2, 0.3, 0.4],
            "rare_flag": [0, 0, 0, 1],
        }
    )
    report = fp.feature_matrix_report(X, y=[0, 0, 1, 1], rare_threshold=0.3)
    rows = report.set_index("feature")
    assert bool(rows.loc["constant", "is_constant"])
    assert bool(rows.loc["outcome_score", "leakage_flag"])
    assert bool(rows.loc["rare_flag", "rare_binary"])
