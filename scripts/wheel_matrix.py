"""Emit weekly wheel checks from declared extras (Python 3.11+)."""

import json
from pathlib import Path
import tomllib


def matrix():
    project = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())
    rows = [{"extra": name, "python": "3.11" if name == "radiomics" else "3.12",
             "workaround": "--radiomics-build-workaround" if name == "radiomics" else ""}
            for name in project["project"]["optional-dependencies"]]
    return {"include": [{"extra": "base", "python": "3.12", "workaround": ""}, *rows,
                        {"extra": "all", "python": "3.11", "workaround": "--radiomics-build-workaround"}]}


if __name__ == "__main__":
    print(json.dumps(matrix()))
