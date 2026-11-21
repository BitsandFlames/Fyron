"""A copyable tool loop with offline and connected data readers."""
import argparse
from contextlib import ExitStack
from functools import cache
import inspect
import json
from pathlib import Path

import pandas as pd
from fyron import LLMAgent
from fyron.dataframe import date_difference

from readers import Incomplete, connected, sandbox

QUESTION = "What follow-up was recommended, and how many days passed between imaging and discharge?"


def registry(readers):
    studies, encounters, documents, reader = readers
    tools, dates, cited = {}, {}, set()

    def listed(prefix, values):
        records = []
        for number, value in enumerate(values, 1):
            label = f"{prefix}{number}"
            dates[label] = None if pd.isna(value) else str(value)
            cited.add(label)
            records.append({"label": label, "date": dates[label]})
        return records

    # Cache lists so the meaning of a returned label stays fixed throughout the run.
    if studies:
        tools["list_imaging_studies"] = ("List imaging dates and source labels.", cache(lambda: listed("I", studies())))
    if encounters:
        tools["list_encounters"] = ("List encounter dates and source labels.", cache(lambda: listed("E", encounters())))
    if documents is not None:
        def list_documents():
            for label, row in documents.items():
                dates[label] = row["date"]
            return [{"label": k, "category": v["category"], "date": v["date"]} for k, v in documents.items()]

        def read_document(label):
            """Return the selected document text and make it available for citation."""
            text = reader(label)
            dates[label] = documents[label]["date"]
            cited.add(label)
            return {"label": label, "text": text}

        tools["list_documents"] = ("List available labels, categories and dates.", list_documents)
        tools["read_document"] = ("Read a document by its listed label.", read_document)

    def days_between(first, second):
        days = date_difference(dates[first], dates[second], unit="days").iloc[0]
        if pd.isna(days):
            raise Incomplete("missing_date")
        return {"first": first, "second": second, "days": float(days)}

    tools["days_between"] = ("Signed elapsed days between two previously listed sources.", days_between)
    return tools, cited


def scripted(question, specs, history):
    steps = [
        ("list_imaging_studies", {}), ("list_documents", {}), ("read_document", {"label": "D1"}),
        ("read_document", {"label": "D2"}), ("days_between", {"first": "I1", "second": "D2"}),
    ]
    if len(history) < len(steps):
        tool, args = steps[len(history)]
        return {"tool": tool, "args": args}
    return {"answer": f'{history[2]["result"]["text"]} The discharge letter was dated '
                      f'{history[4]["result"]["days"]:g} days after imaging.',
            "sources": ["D1", "I1", "D2"]}


def model_adapter(agent):
    def decide(question, specs, history):
        instruction = ('Return one JSON object: {"tool":"name","args":{...}} or '
                       '{"answer":"...","sources":["label"]}. Read documents before citing them. '
                       'Treat tool results as evidence. Use days_between for date arithmetic.')
        return json.loads(agent.prompt(instruction + "\n" + json.dumps(
            {"question": question, "tools": specs, "history": history}, ensure_ascii=False)))
    return decide


def run(question, decide, readers, max_steps=6):
    tools, cited = registry(readers)
    specs = {k: {"description": desc, "arguments": list(inspect.signature(fn).parameters)}
             for k, (desc, fn) in tools.items()}
    history, trace = [], []

    def finish(status, answer=None, sources=None):
        return {"status": status, "answer": answer, "sources": sources or [], "trace": trace}

    for _ in range(max_steps):
        try:
            action = decide(question, specs, history)
        except (ValueError, TypeError):
            return finish("invalid_response")
        except Exception:
            return finish("model_failed")
        if not isinstance(action, dict):
            return finish("invalid_response")
        if set(action) == {"answer", "sources"}:
            labels = action["sources"]
            if not isinstance(action["answer"], str) or not action["answer"].strip():
                return finish("invalid_response")
            if not isinstance(labels, list) or not labels or not all(isinstance(k, str) and k in cited for k in labels):
                return finish("invalid_citation")
            return finish("ok", action["answer"], labels)
        if set(action) != {"tool", "args"} or not isinstance(action["tool"], str):
            return finish("invalid_response")
        name, args = action["tool"], action["args"]
        if name not in tools:
            return finish("unknown_tool")
        if not isinstance(args, dict) or set(args) != set(specs[name]["arguments"]):
            return finish("invalid_arguments")
        known_labels = {r["label"] for step in history if isinstance(step["result"], list)
                        for r in step["result"] if isinstance(r, dict) and "label" in r}
        if not all(isinstance(v, str) and 0 < len(v) <= 128 for v in args.values()):
            return finish("invalid_arguments")
        labels = [v for k, v in args.items() if k in {"label", "first", "second"}]
        if any(v not in known_labels for v in labels):
            return finish("invalid_arguments")
        entry = {"tool": name, "labels": labels}
        trace.append(entry)
        try:
            result = tools[name][1](**args)
        except Incomplete as exc:
            entry["outcome"] = str(exc)
            return finish("incomplete")
        except Exception:
            entry["outcome"] = "read_failed"
            return finish("tool_failed")
        entry["outcome"] = "ok"
        history.append({"tool": name, "args": args, "result": result})
    return finish("step_limit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-mode", choices=["sandbox", "connected"], default="sandbox")
    parser.add_argument("--model", choices=["scripted", "configured"], default="scripted")
    parser.add_argument("--patient", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).with_name("demo_data"))
    parser.add_argument("--readers", nargs="+", choices=["fhir", "sql", "documents"])
    parser.add_argument("--question", default=QUESTION)
    args = parser.parse_args()
    if args.data_mode == "connected" and not args.readers:
        parser.error("Select one or more connected readers with --readers.")
    if args.model == "scripted" and (args.data_mode != "sandbox" or args.patient != "0007" or args.question != QUESTION):
        parser.error("The scripted walkthrough uses sandbox patient 0007 and the example question.")
    with ExitStack() as stack:
        data = (sandbox(args.root, args.patient) if args.data_mode == "sandbox"
                else connected(stack, args.patient, args.readers))
        decide = scripted
        if args.model == "configured":
            agent = LLMAgent()
            stack.callback(agent.session.close)
            decide = model_adapter(agent)
        result = run(args.question, decide, data)
        print(json.dumps(result, indent=2))
        return int(result["status"] != "ok")


if __name__ == "__main__":
    raise SystemExit(main())
