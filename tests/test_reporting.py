from __future__ import annotations

import pandas as pd

from fyron import reporting as fr


def test_reporting_tables() -> None:
    df = pd.DataFrame(
        {
            "group": ["A", "A", "B"],
            "age": [60, 70, 80],
            "sex": ["F", "M", "F"],
        }
    )

    baseline = fr.summarize_baseline_table(
        df,
        group_col="group",
        continuous=["age"],
        categorical=["sex"],
    )
    assert {"variable", "level", "group=A", "group=B"}.issubset(baseline.columns)

    assert fr.format_estimate_ci(1.234, 1.0, 1.9) == "1.23 (1.00 to 1.90)"

    metrics = fr.metrics_table({"RF": {"auc": 0.81234, "sensitivity": 0.7}})
    assert metrics.loc[0, "auc"] == 0.812

    comparison = fr.compare_models_table(
        {
            "RF": {"metrics": {"auc": 0.81234, "sensitivity": 0.7}},
            "XGB": {"metrics": {"auc": 0.76543, "sensitivity": 0.8}},
        }
    )
    assert comparison["model"].tolist() == ["RF", "XGB"]
    assert comparison.loc[1, "auc"] == 0.765

    flow = fr.cohort_flow_table(
        [
            {"step": "FHIR patients", "n": 100},
            {"step": "With CT", "n": 80, "reason": "missing CT"},
        ]
    )
    assert flow.loc[1, "excluded"] == 20
    assert fr.cohort_flow_table(flow).loc[1, "excluded"] == 20

    markdown = fr.dataframe_to_markdown(metrics)
    assert "| model | auc | sensitivity |" in markdown
