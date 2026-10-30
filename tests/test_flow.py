from io import StringIO

import pandas as pd
import pytest

from fyron import FlowStep, FlowTracker, track_filter


def test_flow_tracker_manual_steps_and_outputs():
    raw = pd.DataFrame({"patient_id": ["p1", "p2", "p3", "p4"], "age": [70, 60, 15, 80]})
    adults = raw[raw["age"] >= 18]
    flow = FlowTracker("NSCLC CT cohort")

    returned = flow.add_step("Source cohort", raw, metadata={"source": "FHIR"})
    assert returned is raw
    flow.add_step("Age >= 18", adults, reason="age < 18")

    table = flow.to_dataframe()
    assert table.loc[0, "step"] == "Source cohort"
    assert table.loc[0, "n"] == 4
    assert pd.isna(table.loc[0, "excluded"])
    assert table.loc[1, "excluded"] == 1
    assert table.loc[1, "retained_percent"] == 75.0
    assert table.loc[0, "metadata.source"] == "FHIR"

    markdown = flow.to_markdown()
    assert "| step |" in markdown
    assert "Age >= 18" in markdown

    text = flow.to_text_flowchart()
    assert "Source cohort (n=4" in text
    assert "=> Final cohort" in text

    stream = StringIO()
    rendered = flow.print(stream=stream, color=False)
    assert "Final cohort: 3 / 4 retained (75.0%)" in rendered
    assert stream.getvalue() == rendered + "\n"


def test_flow_tracker_decorator_records_dataframe_filters():
    raw = pd.DataFrame({"patient_id": ["p1", "p2", "p3"], "has_ct": [True, False, True]})
    flow = FlowTracker("Decorated cohort")
    flow.add_step("Source", raw)

    @track_filter(flow, label="Has baseline CT", reason="missing CT")
    def filter_ct(df):
        return df[df["has_ct"]]

    out = filter_ct(raw)
    assert len(out) == 2
    table = flow.to_dataframe()
    assert table.loc[1, "step"] == "Has baseline CT"
    assert table.loc[1, "excluded"] == 1
    assert table.loc[1, "reason"] == "missing CT"


def test_flow_tracker_allows_empty_final_cohort():
    raw = pd.DataFrame({"patient_id": ["p1"], "eligible": [False]})
    flow = FlowTracker("Empty final")
    flow.add_step("Source", raw)
    flow.add_step("Eligible", raw[raw["eligible"]])
    table = flow.to_dataframe()
    assert table.loc[1, "n"] == 0
    assert table.loc[1, "retained_percent"] == 0.0


def test_flow_tracker_rejects_non_dataframe_steps():
    flow = FlowTracker("Bad flow")
    with pytest.raises(TypeError, match="pandas DataFrame"):
        flow.add_step("Bad step", {"n": 1})

    @track_filter(flow, label="Bad decorated")
    def bad_filter(df):
        return {"not": "a dataframe"}

    with pytest.raises(TypeError, match="pandas DataFrame"):
        bad_filter(pd.DataFrame({"x": [1]}))


def test_flow_step_is_public_dataclass():
    step = FlowStep(order=1, label="Source", n=10)
    assert step.label == "Source"
