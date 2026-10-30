"""Lightweight JSON provenance manifests."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from fyron import __version__


def hash_file(path: str | Path, *, algorithm: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    """Hash a file for provenance tracking."""

    hasher = hashlib.new(algorithm)
    with Path(path).open("rb") as file:
        while chunk := file.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_provenance_manifest(
    *,
    title: str | None = None,
    inputs: Sequence[str | Path] | None = None,
    outputs: Sequence[str | Path] | None = None,
    parameters: Mapping[str, Any] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Create a JSON-serializable provenance manifest."""

    return {
        "title": title,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fyron_version": __version__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "inputs": [_path_record(path, include_hash=True) for path in inputs or []],
        "outputs": [_path_record(path, include_hash=False) for path in outputs or []],
        "parameters": dict(parameters or {}),
        "notes": notes,
    }


def analysis_run_manifest(
    *,
    title: str,
    inputs: Sequence[str | Path] | None = None,
    outputs: Sequence[str | Path] | None = None,
    parameters: Mapping[str, Any] | None = None,
    random_seed: int | None = None,
    analysis_type: str | None = None,
    cohort_id: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Create a provenance manifest for one clinical analysis run.

    Parameters
    ----------
    title
        Human-readable run title.
    inputs, outputs
        Input and output artifacts. Existing input files are hashed.
    parameters
        Analysis parameters such as endpoint definition, model choices, and thresholds.
    random_seed
        Optional seed used for splitting, bootstrapping, or model fitting.
    analysis_type
        Optional label such as ``"survival"``, ``"classification"``, or ``"boa_features"``.
    cohort_id
        Optional cohort identifier or version.
    notes
        Free-text provenance notes.

    Returns
    -------
    dict
        JSON-serializable manifest with Fyron/runtime metadata and analysis context.
    """

    params = dict(parameters or {})
    if random_seed is not None:
        params.setdefault("random_seed", random_seed)
    manifest = create_provenance_manifest(
        title=title,
        inputs=inputs,
        outputs=outputs,
        parameters=params,
        notes=notes,
    )
    manifest["analysis_type"] = analysis_type
    manifest["cohort_id"] = cohort_id
    manifest["random_seed"] = random_seed
    return manifest


def write_manifest(manifest: Mapping[str, Any], path: str | Path) -> Path:
    """Write a provenance manifest as pretty JSON."""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return out


def _path_record(path: str | Path, *, include_hash: bool) -> dict[str, Any]:
    p = Path(path)
    record: dict[str, Any] = {
        "path": str(p),
        "exists": p.exists(),
        "size_bytes": p.stat().st_size if p.exists() and p.is_file() else None,
    }
    if include_hash and p.exists() and p.is_file():
        record["sha256"] = hash_file(p)
    return record
