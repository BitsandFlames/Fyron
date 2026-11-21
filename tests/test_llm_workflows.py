import json
from pathlib import Path
from threading import Barrier

import pandas as pd
import pytest

from fyron.llm import LLMAgent, load_prompt_templates

PACK = Path(__file__).resolve().parents[1] / "examples/research_prompts.json"


def setup_data():
    return pd.DataFrame([
        ("private1", "privateA", "rad", "old", 1),
        ("private2", "privateC", "rad", "other", 1),
        ("private1", "privateB", "letter", "new", 2),
    ], columns=["patient", "id", "category", "text", "date"])


def test_parallel_isolation_and_summary(monkeypatch):
    agent = LLMAgent(provider="custom")
    barrier = Barrier(2)
    calls = []

    def prompt(worker, message):
        assert "private" not in message
        evidence = json.loads(message.split("\n\n", 1)[1])
        calls.append((worker.session, evidence))
        if worker is not agent:
            barrier.wait(timeout=5)
        return " ".join(item["text"] for item in evidence)

    monkeypatch.setattr(LLMAgent, "prompt", prompt)
    params = dict(text_col="text", document_id_col="id", group_cols=["patient"],
                  order_by="date", context_cols=["date"], prompt_names=["timeline"])
    parallel = agent.run_prompts_on_dataframe(setup_data(), prompts=PACK, **params, max_workers=2)
    assert len({session for session, _ in calls}) == 2
    assert all(session is not agent.session for session, _ in calls)
    sequential = agent.run_prompts_on_dataframe(setup_data(), prompts=load_prompt_templates(PACK), **params)
    pd.testing.assert_frame_equal(sequential, parallel)
    assert list(parallel.answer) == ["old new", "other"]
    assert parallel.sources[0]["S2"]["document_id"] == "privateB"


def test_filtered_partial_and_provenance(monkeypatch):
    agent = LLMAgent(provider="custom")
    def prompt(message):
        assert "private" not in message and '"context"' not in message
        if '"new"' in message:
            raise RuntimeError("private error")
        return "ok"
    monkeypatch.setattr(agent, "prompt", prompt)
    answers = agent.run_prompts_on_dataframe(
        setup_data().replace({"rad": "radiology"}), text_col="text", document_id_col="id",
        category_col="category", keep_cols=["patient"], prompts=PACK, prompt_names=["findings", "follow_up"])
    assert answers.status.tolist() == ["ok"] * 4 + ["failed"]
    opts = dict(prompts=PACK, prompt_names=["timeline"], source_prompt_names=["follow_up"], group_cols=["patient"])
    assert agent.summarize_dataframe(answers, **opts).status.tolist() == ["incomplete", "ok"]
    partial = agent.summarize_dataframe(answers, allow_partial=True, **opts)
    assert partial.status.tolist() == ["partial", "ok"]
    assert partial.sources[0]["S1"]["sources"]["S1"]["document_id"] == "privateA"


def test_preflight_and_oversized(monkeypatch):
    agent = LLMAgent(provider="custom")
    monkeypatch.setattr(agent, "prompt", lambda *args: pytest.fail("unexpected request"))
    opts = dict(text_col="text", document_id_col="id", prompt_names=["timeline"])
    with pytest.raises(ValueError):
        agent.run_prompts_on_dataframe(setup_data(), prompts=[{"name":"timeline","prompt":"x"}, {}], **opts)
    with pytest.raises(ValueError):
        agent.run_prompts_on_dataframe(setup_data(), prompts=PACK, max_workers=0, **opts)
    assert set(agent.run_prompts_on_dataframe(setup_data(), prompts=PACK, max_input_chars=1, **opts).status) == {"oversized"}


def test_parallel_failure_preserves_other_documents_and_closes_sessions(monkeypatch):
    from requests import Session

    agent = LLMAgent(provider="custom")
    sessions = []
    closed = []
    original_close = Session.close

    def close(session):
        closed.append(session)
        original_close(session)

    def prompt(worker, message):
        sessions.append(worker.session)
        if '"other"' in message:
            raise RuntimeError("private")
        return "usable"

    monkeypatch.setattr(Session, "close", close)
    monkeypatch.setattr(LLMAgent, "prompt", prompt)
    answers = agent.run_prompts_on_dataframe(
        setup_data(), text_col="text", document_id_col="id", keep_cols=["patient"],
        prompt_names=["timeline"], prompts=PACK, max_workers=2,
    )
    assert answers.status.tolist() == ["ok", "failed", "ok"]
    assert set(sessions) <= set(closed)
    assert agent.session not in closed
    summaries = agent.summarize_dataframe(
        answers, group_cols=["patient"], prompts=PACK, prompt_names=["timeline"], max_workers=2,
    )
    assert summaries.status.tolist() == ["ok", "incomplete"]


def test_url_workflow_fetches_once_and_cleans(monkeypatch):
    from types import SimpleNamespace
    from fyron.documents import DocumentDownloader

    agent = LLMAgent(provider="custom")
    paths = []
    messages = []
    def download(self, url, *, output_path):
        paths.append(output_path)
        output_path.write_bytes("café".encode("latin1"))
        return SimpleNamespace(error=None, status_code=200, path=output_path,
                               content_type="text/plain; charset=iso-8859-1")

    monkeypatch.setattr(DocumentDownloader, "download_url", download)
    monkeypatch.setattr(agent, "prompt", lambda message: messages.append(message) or "ok")
    frame = pd.DataFrame({"link": ["https://docs.example.org/a"]})
    result = agent.run_prompts_on_dataframe(frame, url_col="link", prompts=PACK,
                                             prompt_names=["follow_up", "timeline"])
    assert len(paths) == 1 and not paths[0].exists()
    assert result.status.tolist() == ["ok", "ok"]
    assert all("café" in m and "example.org" not in m for m in messages)
    assert result.sources[0]["S1"]["document_id"] == frame.link[0]
    with pytest.raises(ValueError, match="outside"):
        agent.run_prompts_on_dataframe(frame, url_col="link", prompts=PACK, prompt_names=["timeline"],
                                       document_origin="https://other.example.org")
    assert len(paths) == 1


def test_pdf_url_without_usable_text_withholds_group(monkeypatch):
    from types import SimpleNamespace
    from fyron.documents import DocumentDownloader

    def download(self, url, *, output_path):
        output_path.write_bytes(b"%PDF-invalid")
        return SimpleNamespace(error=None, status_code=200, path=output_path, content_type="application/pdf")

    monkeypatch.setattr(DocumentDownloader, "download_url", download)
    agent = LLMAgent(provider="custom")
    monkeypatch.setattr(agent, "prompt", lambda *args: pytest.fail("unexpected model request"))
    frame = pd.DataFrame({"url": ["https://docs.example.org/1"], "patient": ["001"]})
    result = agent.run_prompts_on_dataframe(frame, url_col="url", group_cols=["patient"],
                                             prompts=PACK, prompt_names=["timeline"])
    assert result.status.tolist() == ["incomplete"]


def test_reason_preserved_in_partial_summary(monkeypatch):
    agent = LLMAgent(provider="custom")
    monkeypatch.setattr(agent, "prompt", lambda _: "answer")
    df = setup_data()
    df.loc[2, "text"] = ""
    kwargs = dict(prompts=PACK, prompt_names=["timeline"])
    answers = agent.run_prompts_on_dataframe(df, text_col="text", document_id_col="id",
                                              keep_cols=["patient"], **kwargs)
    for partial, expected in [(False, "incomplete"), (True, "partial")]:
        result = agent.summarize_dataframe(answers, group_cols=["patient"], allow_partial=partial, **kwargs)
        row = result.iloc[0]
        assert row.status == expected and row.reason == "empty_text"
        assert row.sources["S2"]["sources"]["S1"] == {"document_id": "privateB", "reason": "empty_text"}
        assert result.iloc[1].reason is None
    for names in [["typo"], ["timeline", "typo"]]:
        with pytest.raises(ValueError, match="typo.*Available.*timeline"):
            agent.summarize_dataframe(answers, group_cols=["patient"], source_prompt_names=names, **kwargs)
    assert agent.summarize_dataframe(answers.iloc[:0], group_cols=["patient"],
                                     source_prompt_names=["timeline"], **kwargs).empty


def test_character_limit_and_converter_failures(tmp_path, monkeypatch):
    import os
    import sys
    from fyron.documents._text import extract_text, TextFailure
    source = tmp_path / "document"
    source.write_text("éé")
    assert extract_text(source, "text/plain", limit=2) == "éé"
    with pytest.raises(TextFailure, match="extracted_text_too_large"):
        extract_text(source, "text/plain", limit=1)
    source.write_bytes(b"\xff")
    with pytest.raises(TextFailure, match="decoding_failed"):
        extract_text(source, "text/plain", limit=1)
    source.write_bytes(b"%PDF-test")
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(TextFailure, match="pdf_converter_unavailable"):
        extract_text(source, "application/pdf", limit=10)
    if os.name == "nt":
        return  # Executable shebang fixtures require POSIX.
    converter = tmp_path / "pdftotext"
    converter.write_text(f"#!{sys.executable}\nimport sys,time\nsys.stdout.write('x'*65536);sys.stdout.flush();time.sleep(10)\n")
    converter.chmod(0o700)
    with pytest.raises(TextFailure, match="extracted_text_too_large"):
        extract_text(source, "application/pdf", limit=4, timeout=2)
    converter.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(10)\n")
    with pytest.raises(TextFailure, match="pdf_conversion_timeout"):
        extract_text(source, "application/pdf", limit=4, timeout=0.1)
