import pandas as pd
import pytest

from fyron import FlowTracker


def frame(ids):
    return pd.DataFrame({"id": ids})


def test_membership_and_query_do_not_confuse_exclusions():
    flow = FlowTracker(id_col="id")
    original = frame([1, 1, 2])
    assert flow.add("Source", original) is original
    flow.add("Query", frame([1] * 5), kind="query")
    flow.add("Changed", frame([2, 3]))
    table = flow.to_dataframe()
    assert table["n"].tolist() == [2, 1, 2]
    assert table.loc[2, "excluded"] == 1
    assert table.loc[2, "metadata.added"] == 1
    assert flow.cohort_table()["step"].tolist() == ["Source", "Changed"]
    assert "Query" not in flow.to_text_flowchart()
    pd.testing.assert_frame_equal(original, frame([1, 1, 2]))


def test_context_report_and_safe_failure(capsys):
    flow = FlowTracker(id_col="id", progress=True)
    flow.add("Source", frame([1, 2]))
    result = {"data": frame([1]), "report": {"summary": pd.DataFrame([{
        "execution_complete": True, "retrieval_exhaustive": False,
    }])}}
    with flow.step("Query", kind="query") as step:
        assert step.result(result) is result
    with pytest.raises(RuntimeError):
        with flow.step("Failed query", kind="query") as step:
            step.result(frame([1]))
            raise RuntimeError("SECRET_REMOTE_RESPONSE")
    flow.add("Selected", frame([1]))
    table = flow.to_dataframe()
    assert table.loc[1, "metadata.retrieval_exhaustive"] == False
    assert table.loc[1, "metadata.elapsed_seconds"] >= 0
    assert table.loc[2, "metadata.status"] == "failed"
    assert pd.isna(table.loc[2, "n"])
    assert table.loc[3, "excluded"] == 1
    output = capsys.readouterr()
    assert "SECRET_REMOTE_RESPONSE" not in output.out + output.err
    assert "SECRET_REMOTE_RESPONSE" not in flow.to_markdown()
    assert "running" in output.out + output.err


def test_missing_or_multiple_results_and_interrupt():
    flow = FlowTracker()
    with pytest.raises(ValueError, match="step.result"):
        with flow.step("Missing"):
            pass
    with pytest.raises(ValueError, match="exactly one"):
        with flow.step("Duplicate") as step:
            step.result(frame([1]))
            step.result(frame([2]))
    with pytest.raises(KeyboardInterrupt):
        with flow.step("Cancelled"):
            raise KeyboardInterrupt()
    assert flow.cohort_table().empty
    assert flow.steps[-1].metadata["status"] == "interrupted"


def test_validation_and_legacy_interoperability():
    flow = FlowTracker(id_col="id")
    for invalid in [pd.DataFrame({"other": [1]}), frame([None])]:
        with pytest.raises(ValueError, match="ID column"):
            flow.add("Bad", invalid)
    assert not flow.steps
    flow.add_step("Old API", frame([1, 2]), metadata={"source": "synthetic"})
    flow.add("New API", frame([2]))
    assert flow.to_dataframe().loc[1, "excluded"] == 1
    with pytest.raises(ValueError, match="kind"):
        flow.step("Bad", kind="unknown")


def test_row_growth_and_empty_cohort():
    flow = FlowTracker()
    flow.add("Source", frame([1]))
    flow.add("Expanded", frame([1, 1]))
    flow.add("Empty", frame([]))
    assert flow.to_dataframe()["excluded"].iloc[1:].tolist() == [0, 2]
    assert flow.to_dataframe().loc[2, "retained_percent"] == 0


def test_plot_excludes_query_and_failure(monkeypatch):
    import fyron.plotting

    captured = {}

    def plot(data, **kwargs):
        captured["table"] = data
        return "figure", "axes"

    monkeypatch.setattr(fyron.plotting, "plot_cohort_flow", plot)
    flow = FlowTracker()
    flow.add("Source", frame([1]))
    flow.add("Query", frame([1]), kind="query")
    assert flow.plot() == ("figure", "axes")
    assert captured["table"]["step"].tolist() == ["Source"]
