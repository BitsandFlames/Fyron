"""Tests for imputation and categorical encoding."""

from __future__ import annotations

import pandas as pd

from fyron.preprocessing import (
    apply_categorical_encoder,
    apply_imputer,
    encode_categorical,
    fit_categorical_encoder,
    fit_imputer,
    impute_dataframe,
    summarize_encoding_plan,
    summarize_imputation_plan,
)


def test_imputer_fit_apply_and_indicators() -> None:
    train = pd.DataFrame({"age": [60.0, None, 70.0], "sex": ["F", None, "F"]})
    plan = summarize_imputation_plan(train)
    assert set(plan["column"]) == {"age", "sex"}

    imputed, imputer = impute_dataframe(train, add_missing_indicators=True)
    assert imputed["age"].isna().sum() == 0
    assert "age_was_missing" in imputed

    test = pd.DataFrame({"age": [None], "sex": [None]})
    applied = apply_imputer(test, imputer)
    assert applied.loc[0, "age"] == 65.0
    assert applied.loc[0, "sex"] == "F"


def test_categorical_encoder_fit_apply_unseen_and_rare() -> None:
    train = pd.DataFrame({"stage": ["I", "II", "II", "III"], "site": ["a", "a", "b", "c"]})
    plan = summarize_encoding_plan(train, columns=["stage"])
    assert plan.loc[0, "n_levels"] == 3

    encoded, encoder = encode_categorical(train, columns=["site"], rare_min_count=2)
    assert "site__a" in encoded
    assert "site____rare__" in encoded

    test = pd.DataFrame({"stage": ["IV"], "site": ["new"]})
    encoder = fit_categorical_encoder(train, columns=["site"], rare_min_count=2)
    applied = apply_categorical_encoder(test, encoder)
    assert applied.loc[0, "site____rare__"] == 1
