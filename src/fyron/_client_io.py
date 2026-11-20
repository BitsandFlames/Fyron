"""Private, value-free client progress and atomic result-report helpers."""

import hashlib
import json
import os
from pathlib import Path
import tempfile

import pandas as pd


def fingerprint(*values):
    """Fingerprint configuration in memory; never persist source values."""
    def typed(value):
        if isinstance(value, dict):
            return ["mapping", sorted([(str(key), typed(item)) for key, item in value.items()])]
        if isinstance(value, (tuple, list)):
            return [type(value).__name__, [typed(item) for item in value]]
        return [type(value).__module__ + "." + type(value).__qualname__, str(value)]
    encoded = json.dumps(typed(values), separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def atomic_csv(frame, destination, *, forbidden=()):
    """Replace a report only after serialization succeeds, preserving prior files."""
    path = Path(destination).expanduser().absolute()
    resolved = path.resolve()
    if any(resolved == Path(item).resolve() for item in forbidden if item):
        raise ValueError("Result report would overwrite a document or downloaded output.")
    if path.name.startswith(".fyron-") or path.name == "study_manifest.json":
        raise ValueError("Result report must not replace client metadata.")
    if path.is_symlink():
        raise ValueError("Result report must not be a symbolic link.")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".fyron-report-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            frame.to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def task_row(number, results, elapsed):
    """Summarize one task without serializing identifying result fields."""
    failed = sum(item.error is not None for item in results)
    skipped = sum(item.error is None and item.skipped for item in results)
    status = "failed" if failed else ("no_match" if not results else
             ("skipped" if skipped == len(results) else "success"))
    return {"task": number, "status": status, "returned_rows": len(results),
            "succeeded": len(results) - failed - skipped, "failed": failed,
            "skipped": skipped, "elapsed_s": elapsed}


def extraction_report(rows, requested, input_rows):
    """Keep requested tasks distinct from returned result objects."""
    columns = ["task", "status", "returned_rows", "succeeded", "failed", "skipped", "elapsed_s"]
    table = pd.DataFrame(rows, columns=columns).sort_values("task").reset_index(drop=True)
    summary = pd.DataFrame([{
        "input_rows": input_rows, "requested_tasks": requested, "completed_tasks": len(rows),
        "succeeded_tasks": sum(row["status"] == "success" for row in rows),
        "failed_tasks": sum(row["status"] == "failed" for row in rows),
        "skipped_tasks": sum(row["status"] == "skipped" for row in rows),
        "no_match_tasks": sum(row["status"] == "no_match" for row in rows),
        "unfinished_tasks": requested - len(rows),
        "execution_complete": len(rows) == requested,
        "successful": len(rows) == requested and all(row["status"] in {"success", "skipped"} for row in rows),
        "returned_rows": sum(row["returned_rows"] for row in rows),
    }])
    return {"rows": table, "summary": summary}
