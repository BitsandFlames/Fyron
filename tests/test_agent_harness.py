"""Exercise the copyable starter with synthetic data and mocked readers."""
import json
from contextlib import ExitStack, nullcontext
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest


@pytest.fixture
def harness(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "examples/agent_harness"
    monkeypatch.syspath_prepend(str(root))
    import run
    import readers
    return run, readers, root / "demo_data"


def test_demo_and_model_adapter(harness):
    h, r, root = harness
    data = r.sandbox(root, "0007")
    def prompt(message):
        request = json.loads(message.split("\n", 1)[1])
        assert "0007" not in message
        return json.dumps(h.scripted(request["question"], request["tools"], request["history"]))
    result = h.run(h.QUESTION, h.model_adapter(SimpleNamespace(prompt=prompt)), data)
    assert result["status"] == "ok"
    assert "six weeks" in result["answer"] and "7 days" in result["answer"]
    assert result["sources"] == ["D1", "I1", "D2"]
    assert "weeks" not in json.dumps(result["trace"])
    assert r.sandbox(root, "0008")[3]("D1") == "No interval change described."
    with pytest.raises(KeyError):
        r.sandbox(root, "0008")[3]("D2")


@pytest.mark.parametrize(("action", "status"), [
    ({"tool": "execute", "args": {}}, "unknown_tool"),
    ({"tool": "read_document", "args": {"label": "D9"}}, "invalid_arguments"),
    ({"answer": "claimed", "sources": ["D1"]}, "invalid_citation"),
    ({"tool": "list_documents", "args": {}}, "step_limit"),
    ([], "invalid_response"),
])
def test_boundaries(harness, action, status):
    h, r, root = harness
    assert h.run("test", lambda *_: action, r.sandbox(root, "0007"), 1)["status"] == status


def test_containment(harness, tmp_path):
    _, r, _ = harness
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.touch()
    (root / "escape").symlink_to(outside)
    for name in ["../outside.txt", "escape"]:
        with pytest.raises(ValueError):
            r.inside(root, name)


def test_connected_contract(harness, monkeypatch, tmp_path):
    h, r, _ = harness
    from psycopg.conninfo import conninfo_to_dict
    index = tmp_path / "index.csv"
    index.write_text("patient_id,label,category,date,url\n0007,D1,report,2025-01-08,https://docs.example.org/a\n")
    for name, value in {"HARNESS_DOCUMENT_INDEX":str(index), "HARNESS_DOCUMENT_ORIGIN":"https://docs.example.org",
                        "HARNESS_DOCUMENT_TOKEN":"placeholder", "HARNESS_FHIR_TOKEN":"placeholder",
                        "FHIR_BASE_URL":"https://fhir.example.org", "FHIR_DB_DSN":"dbname=synthetic"}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("HARNESS_PATIENT_MAP", raising=False)
    def search(resource, **kwargs):
        assert resource == "ImagingStudy" and kwargs["params"]["patient"] == "Patient/0007"
        assert kwargs["max_pages"] == 2
        return {"data":pd.DataFrame([{"owner":"Patient/0007","date":"2025-01-01"}]),
                "report":{"summary":pd.DataFrame([{"retrieval_exhaustive":True}])}}
    def query(sql, params):
        assert "0007" not in sql and params == {"patient":"0007"}
        return pd.DataFrame([{"patient_id":"0007","encounter_date":"2025-01-08"}])
    def db(dsn, **kwargs):
        assert "default_transaction_read_only=on" in conninfo_to_dict(dsn)["options"]
        return nullcontext(SimpleNamespace(query_df=query))
    def download(url, output_path):
        assert url == "https://docs.example.org/a"
        output_path.write_text("Repeat imaging in six weeks.")
        return SimpleNamespace(error=None,status_code=200,path=output_path,content_type="text/plain")
    monkeypatch.setattr(r, "FHIRRestClient", lambda **kw: nullcontext(SimpleNamespace(search_df=search)))
    monkeypatch.setattr(r, "FHIRSQLClient", db)
    monkeypatch.setattr(r, "DocumentDownloader", lambda **kw: nullcontext(SimpleNamespace(download_url=download)))
    with ExitStack() as stack:
        tools, _ = h.registry(r.connected(stack, "0007", ["fhir","sql","documents"]))
        assert tools["list_imaging_studies"][1]()[0]["label"] == "I1"
        assert tools["list_encounters"][1]()[0]["label"] == "E1"
        assert tools["read_document"][1]("D1")["text"].startswith("Repeat")
        assert tools["days_between"][1]("I1","D1")["days"] == 7
        monkeypatch.setenv("HARNESS_DOCUMENT_ORIGIN","https://different.example.org")
        with pytest.raises(ValueError):
            r.connected(stack, "0007", ["documents"])


def test_incomplete_read_and_missing_date(harness):
    h, r, _ = harness
    client = SimpleNamespace(search_df=lambda *a, **k: {"report":{"summary":pd.DataFrame(
        [{"retrieval_exhaustive":False}])}})
    with pytest.raises(r.Incomplete):
        r.fhir_studies(client, "0007")
    tools, _ = h.registry((lambda: [None, "2025-01-01"], None, None, None))
    tools["list_imaging_studies"][1]()
    with pytest.raises(r.Incomplete):
        tools["days_between"][1]("I1","I2")
