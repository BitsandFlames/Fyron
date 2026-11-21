"""Named text prompts and traceable DataFrame summaries."""

import json
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextvars import copy_context
from threading import local
from pathlib import Path

import pandas as pd

from .._diagnostics import task_outcome
from ..documents._text import TextFailure


_FIELDS = ["prompt_name", "answer", "status", "sources"]


def _names(values, *, optional=False):
    if optional and values is None:
        return []
    if not isinstance(values, (list, tuple)) or not all(
        isinstance(value, str) and value.strip() for value in values
    ) or len(set(values)) != len(values):
        raise ValueError("Expected distinct, nonblank names in a list.")
    return list(values)


def load_prompt_templates(source):
    """Load and validate reusable named text prompts.

    Parameters
    ----------
    source:
        UTF-8 JSON path, list of definitions, or mapping containing a prompts list.
        Each definition has a unique name, instruction (prompt), and optional categories.

    Returns
    -------
    list
        Validated definitions in input order, ready for DataFrame workflows.
    """
    if isinstance(source, (str, Path)):
        source = json.loads(Path(source).read_text(encoding="utf-8"))
    if isinstance(source, dict) and set(source) == {"prompts"}:
        source = source["prompts"]
    if not isinstance(source, list) or not source:
        raise ValueError("A prompt pack requires a nonempty prompts list.")
    pack = []
    for item in source:
        if not isinstance(item, dict) or set(item) - {"name", "prompt", "categories"}:
            raise ValueError("Invalid prompt definition fields.")
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in ("name", "prompt")):
            raise ValueError("Each prompt needs a nonblank name and instruction.")
        pack.append(dict(name=item["name"], prompt=item["prompt"],
                         categories=_names(item.get("categories", []))))
    _names([p["name"] for p in pack])
    return pack


def _select(pack, names):
    indexed = {p["name"]: p for p in pack}
    if names is None:
        return pack
    names = _names(names)
    if not names or set(names) - indexed.keys():
        raise ValueError("Select at least one known prompt name.")
    return [indexed[n] for n in names]


def _run(agent, df, *, prompts, prompt_names, text_col, document_id_col, group_cols,
         keep_cols, order_by, context_cols, category_col, max_input_chars,
         max_workers, summary=False, allow_partial=False, url_col=None,
         document_auth=None, document_origin=None, max_download_bytes=5_000_000, max_extracted_chars=100_000):
    if type(max_workers) is not int or max_workers < 1:
        raise ValueError("max_workers must be a positive integer.")
    pack = _select(load_prompt_templates(prompts), prompt_names)
    groups = _names(group_cols, optional=True)
    keep = _names(keep_cols, optional=True)
    context = _names(context_cols, optional=True)
    output_keys = list(dict.fromkeys(groups + keep))
    if (text_col is None) == (url_col is None):
        raise ValueError("Provide exactly one of text_col and url_col.")
    if url_col is None and (document_auth is not None or document_origin is not None):
        raise ValueError("Document service options require url_col.")
    if url_col is not None:
        for value in (max_download_bytes, max_extracted_chars):
            if type(value) is not int or value < 1:
                raise ValueError("Document limits must be positive integers.")
        if url_col in context:
            raise ValueError("The document URL column cannot be sent as model context.")
        if document_id_col is None:
            document_id_col = url_col
    required = [text_col if url_col is None else url_col, *output_keys, *context]
    required += [c for c in (document_id_col, order_by, category_col) if c is not None]
    if summary:
        required += _FIELDS
    if not df.columns.is_unique or set(required) - set(df.columns):
        raise ValueError("Missing required columns or duplicate DataFrame column labels.")
    if set(output_keys) & {*_FIELDS, "reason"}:
        raise ValueError("Output metadata collides with workflow result fields.")
    if not category_col and any(p["categories"] for p in pack):
        raise ValueError("Filtered prompts require category_col.")
    if isinstance(max_input_chars, bool) or not isinstance(max_input_chars, int) or max_input_chars < 1:
        raise ValueError("max_input_chars must be a positive integer.")
    if summary and not groups:
        raise ValueError("Select group_cols for summarization.")
    if groups and df[groups].isna().any().any():
        raise ValueError("Missing group keys.")
    if not summary:
        if document_id_col is None or df[document_id_col].isna().any() or df[document_id_col].duplicated().any():
            raise ValueError("Documents require distinct nonmissing IDs.")
    if url_col is not None:
        from ._url_documents import _prepare

        selected = slice(None)
        if all(template["categories"] for template in pack):
            categories = {c for template in pack for c in template["categories"]}
            selected = df[category_col].isin(categories)
        df = df.copy(deep=False)
        text_col = object()
        df[text_col] = _prepare(df, url_col, auth=document_auth, origin=document_origin,
                                selected=selected, max_download_bytes=max_download_bytes,
                                max_extracted_chars=max_extracted_chars)
    ordered = df.sort_values(order_by, kind="stable") if order_by else df
    batches = (ordered.groupby(groups, sort=False, observed=True) if groups else
               ((i, ordered.iloc[i:i+1]) for i in range(len(ordered))))
    def tasks():
        for _, batch in batches:
            for template in pack:
                selected = batch
                if template["categories"]:
                    selected = batch[batch[category_col].isin(template["categories"])]
                if selected.empty:
                    continue
                result = {k: selected[k].iloc[0] for k in groups}
                for k in keep:
                    if k not in result:
                        result[k] = selected[k].tolist() if groups else selected[k].iloc[0]
                yield result, selected, template

    def execute(worker, task):
        result, selected, template = task
        result.update(_answer(worker, selected, template, text_col, document_id_col,
                              context, max_input_chars, summary, allow_partial))
        return result

    if max_workers == 1:
        completed = (execute(agent, task) for task in tasks())
    else:
        completed = _parallel(agent, tasks(), execute, max_workers)
    results = []
    for result in completed:
        task_outcome(failed=result["status"] != "ok")
        results.append(result)
    return pd.DataFrame(results, columns=output_keys + _FIELDS + ["reason"])


def _parallel(agent, tasks, execute, workers):
    state = local()
    sessions = []

    def initialize():
        state.agent = agent._workflow_worker()
        sessions.append(state.agent.session)

    def run(task):
        return execute(state.agent, task)

    pool = ThreadPoolExecutor(max_workers=workers, initializer=initialize)
    pending = {}
    ordered_results = {}
    try:
        tasks = enumerate(tasks)
        exhausted = False
        while pending or not exhausted:
            while len(pending) < workers and not exhausted:
                try:
                    index, task = next(tasks)
                except StopIteration:
                    exhausted = True
                    break
                future = pool.submit(copy_context().run, run, task)
                pending[future] = index
            if pending:
                done, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    ordered_results[pending.pop(future)] = future.result()
        for index in range(len(ordered_results)):
            yield ordered_results.pop(index)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        for session in sessions:
            session.close()


def _answer(agent, frame, template, text_col, id_col, context, limit, summary, allow_partial):
    sources = {}
    evidence = []
    incomplete = False
    for number, row in enumerate(frame.to_dict("records"), 1):
        label = f"S{number}"
        sources[label] = ({"prompt_name": row["prompt_name"], "sources": row["sources"],
                           "status": row["status"]} if summary else {"document_id": row[id_col]})
        text = row[text_col]
        usable = isinstance(text, str) and bool(text.strip())
        if summary:
            usable = usable and row["status"] in ("ok", "partial")
        if not usable or (summary and row["status"] != "ok"):
            incomplete = True
            sources[label]["reason"] = ((row.get("reason") or "unusable_answer") if summary
                                        else str(text) if isinstance(text, TextFailure) else "empty_text")
        if usable:
            item = {"source": label, "text": text}
            if context:
                item["context"] = {k: None if pd.api.types.is_scalar(row[k]) and pd.isna(row[k]) else str(row[k]) for k in context}
            evidence.append(item)
    reasons = {s["reason"] for s in sources.values() if "reason" in s}
    reason = next(iter(reasons)) if len(reasons) == 1 else "multiple_reasons" if reasons else None
    result = dict(reason=reason, prompt_name=template["name"], sources=sources, answer=None, status="incomplete")
    if not evidence or (incomplete and not allow_partial):
        return result
    message = template["prompt"] + "\n\n" + json.dumps(evidence, ensure_ascii=False)
    if len(message) > limit:
        result.update(status="oversized", reason="prompt_too_large")
        return result
    try:
        answer = agent.prompt(message)
    except Exception:
        result.update(status="failed", reason="model_failed")
        return result
    if not isinstance(answer, str) or not answer.strip():
        result.update(status="failed", reason="model_failed")
        return result
    result.update(answer=answer, status="partial" if incomplete else "ok")
    return result
