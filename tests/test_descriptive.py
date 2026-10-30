from __future__ import annotations

import pandas as pd
import pytest

from fyron import descriptive as fd
from fyron import ml
from fyron import preprocessing as fp


def _cohort() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "group": ["A", "A", "B", "B"],
            "age": [60, 64, 70, 74],
            "sex": ["F", "M", "F", None],
            "event": [0, 1, 1, 1],
            "time": [10, 12, 8, 6],
        }
    )


def test_descriptive_tables() -> None:
    df = _cohort()
    numeric = fd.describe_numeric(df, columns=["age"], group_col="group")
    assert set(numeric["group"]) == {"A", "B"}
    assert "median" in numeric.columns

    categorical = fd.describe_categorical(df, columns=["sex"], group_col="group")
    assert "<missing>" in set(categorical["level"])

    comparisons = fd.compare_descriptive_groups(df, group_col="group", numeric=["age"], categorical=["sex"])
    assert set(comparisons["variable"]) == {"age", "sex"}

    table_one = fd.create_table_one(df, group_col="group", numeric=["age"], categorical=["sex"])
    assert "p_value" in table_one.columns

    endpoint = fd.summarize_endpoint(df, event_col="event", time_col="time", group_col="group")
    assert endpoint.loc[endpoint["group"] == "B", "events"].iloc[0] == 2


def test_descriptive_missing_column_and_plots() -> None:
    df = _cohort()
    with pytest.raises(ValueError):
        fd.describe_numeric(df, columns=["missing"])

    missing = fp.summarize_missingness(df)
    fig1, _ = ml.plot_missingness_bar(missing)
    fig2, _ = ml.plot_table_one_summary(fd.create_table_one(df, group_col="group", numeric=["age"], categorical=["sex"]))
    fig3, _ = ml.plot_bland_altman([1, 2, 3], [1.1, 1.9, 3.2])
    fig4, _ = ml.plot_waterfall([-0.2, 0.4, -0.5], labels=["p1", "p2", "p3"])
    import matplotlib.pyplot as plt

    for fig in [fig1, fig2, fig3, fig4]:
        plt.close(fig)
