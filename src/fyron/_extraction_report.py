"""Internal, process-local collection of extraction decisions."""

from contextvars import ContextVar
from pathlib import Path

import pandas as pd

_active = ContextVar("fyron_extraction_report", default=None)
COLUMNS = ["download_id", "case_path", "family", "label", "status"]


def decision(status, label=None):
    active = _active.get()
    if active is not None:
        context, rows = active
        rows.append({**context, "label": label, "status": status})


def case_result(case, *, extractor, family, kwargs):
    rows = []
    token = _active.set(({
        "download_id": kwargs.get("download_id") or Path(case).name,
        "case_path": str(case), "family": family,
    }, rows))
    try:
        data = extractor(case, **kwargs)
        return data, rows
    finally:
        _active.reset(token)


def validate_cases(cases):
    names = [Path(case).name for case in cases]
    if len(names) != len(set(names)):
        raise ValueError("Case identifiers must be unique before extraction.")


def feature_status(row, missing_value=None):
    values = [value for key, value in row.items() if key != "download_id"]
    return "partial" if not values or any(
        pd.isna(value) or (missing_value is not None and value == missing_value)
        for value in values
    ) else "success"


def report_result(data, rows, enabled):
    if not enabled:
        return data
    table = pd.DataFrame(rows, columns=COLUMNS)
    scoped = table.assign(scope=table["label"].map(lambda value: "case" if pd.isna(value) else "label"))
    summary = scoped.groupby(["family", "scope", "status"], dropna=False).size().reset_index(name="count")
    return {"data": data, "report": {"rows": table, "summary": summary}}


def collect_results(results, enabled):
    records, reports = [], []
    for row, report in results:
        if row is not None:
            records.append(row)
        reports.extend(report)
    data = pd.DataFrame(records)
    if not data.empty and data["download_id"].duplicated().any():
        raise ValueError("Extracted case identifiers must be unique.")
    return report_result(data, reports, enabled)
