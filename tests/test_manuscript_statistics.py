from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")

from fyron import statistics as fst


def _regression_df() -> pd.DataFrame:
    rng = np.random.default_rng(10)
    n = 120
    age = rng.normal(60, 8, size=n)
    score = rng.normal(0, 1, size=n)
    group = rng.choice(["A", "B"], size=n)
    linear = 5 + 0.3 * age - 1.5 * score + rng.normal(0, 1, size=n)
    logit = -8 + 0.11 * age + 0.8 * score + (group == "B") * 0.4
    prob = 1 / (1 + np.exp(-logit))
    event = rng.binomial(1, prob)
    return pd.DataFrame({"age": age, "score": score, "group": group, "linear": linear, "event": event})


def test_linear_and_logistic_regression_tables() -> None:
    df = _regression_df()
    linear = fst.fit_linear_regression_table(
        df,
        outcome_col="linear",
        covariates=["age", "score", "group"],
        p_adjust="fdr_bh",
    )
    assert {"term", "beta", "ci_lower", "ci_upper", "p_value", "p_adjusted", "n", "formula"}.issubset(linear.columns)
    assert "group_B" in set(linear["term"])

    logistic = fst.fit_logistic_regression_table(
        df,
        outcome_col="event",
        covariates=["age", "score", "group"],
    )
    assert {"term", "odds_ratio", "ci_lower", "ci_upper", "p_value", "n"}.issubset(logistic.columns)
    assert (logistic["odds_ratio"] > 0).all()


def test_regression_missing_covariate_error() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        fst.fit_linear_regression_table(
            _regression_df(),
            outcome_col="linear",
            covariates=["age", "missing"],
        )


def test_vif_and_qc_tables() -> None:
    df = _regression_df()
    vif = fst.vif_table(df, ["age", "score", "group"])
    assert {"term", "vif", "n"}.issubset(vif.columns)
    assert (vif["vif"] >= 1).all()

    normality = fst.normality_table(df, ["age", "score"])
    assert set(normality["variable"]) == {"age", "score"}

    corr = fst.correlation_pvalue_table(df, ["age", "score", "linear"])
    assert {"variable_a", "variable_b", "correlation", "p_adjusted"}.issubset(corr.columns)

    df_missing = df.copy()
    df_missing.loc[df_missing.index[:3], "score"] = np.nan
    missing = fst.missingness_by_group_table(df_missing, group_col="group", columns=["score"])
    assert {"overall", "A", "B"}.issubset(set(missing["group"]))

    outliers = fst.outlier_table(df.assign(age=[*df["age"].iloc[:-1], 200]), ["age"])
    assert outliers.loc[0, "outliers"] >= 1
