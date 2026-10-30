"""Fail on new documentation gaps or stale baseline entries; never add exemptions."""

import argparse
import json
from pathlib import Path

from generate_function_reference import collect_api_docs, weak_docstring_entries

BASELINE = Path(__file__).with_name("docstring_baseline.json")


def compare(current, baseline):
    def issues(text):
        result = set()
        for item in text.split("; "):
            if item.startswith("missing parameter descriptions: "):
                result.update("parameter:" + name for name in item.split(": ", 1)[1].split(", "))
            else:
                result.add(item)
        return result

    added = {key: value for key, value in current.items()
             if key not in baseline or not issues(value) <= issues(baseline[key])}
    repaired = sorted(key for key in baseline if key not in current or
                      (key not in added and issues(current[key]) < issues(baseline[key])))
    return added, repaired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prune", action="store_true", help="Remove repaired entries; never add new gaps.")
    args = parser.parse_args()
    current = {row["import_path"]: row["issues"] for row in weak_docstring_entries(collect_api_docs())}
    baseline = json.loads(BASELINE.read_text())
    added, repaired = compare(current, baseline)
    if args.prune and not added:
        BASELINE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        repaired = []
    if added:
        print("New or changed documentation gaps:", ", ".join(sorted(added)))
    if repaired:
        print("Remove repaired baseline entries with --prune:", ", ".join(repaired))
    print(f"Existing public API documentation gaps: {len(current)}")
    return int(bool(added or repaired))


if __name__ == "__main__":
    raise SystemExit(main())
