"""Local completion records for staged downloads, not clinical metadata."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


def marker_path(directory, key):
    digest = hashlib.sha256(key.encode()).hexdigest()
    return Path(directory) / f".fyron-complete-{digest}.json"


def file_digest(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified_files(directory, key):
    """Return verified paths, or an empty list for missing/invalid records."""
    directory = Path(directory)
    try:
        payload = json.loads(marker_path(directory, key).read_text())
        if payload.get("version") != 1 or not isinstance(payload.get("files"), list):
            return []
        paths = []
        for item in payload["files"]:
            name = item["name"]
            if not isinstance(name, str) or Path(name).name != name or name in {".", ".."}:
                return []
            path = directory / name
            if path.is_symlink() or not path.is_file():
                return []
            if path.stat().st_size != item["size"] or file_digest(path) != item["sha256"]:
                return []
            paths.append(path)
        return paths
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return []


def publish_files(staging, directory, key, *, overwrite, write_record=True):
    """Publish staged files; write completion last. Multi-file commit is not atomic."""
    staging, directory = Path(staging), Path(directory)
    files = sorted(path for path in staging.iterdir() if path.is_file())
    if not files:
        raise ValueError("No staged files to publish.")
    if not overwrite and any((directory / path.name).exists() for path in files):
        raise FileExistsError("Existing outputs are unverified; explicit overwrite required.")
    records = [{"name": path.name, "size": path.stat().st_size, "sha256": file_digest(path)} for path in files]
    marker = marker_path(directory, key)
    marker.unlink(missing_ok=True)
    for path in files:
        if overwrite:
            os.replace(path, directory / path.name)
        else:
            # An exclusive link prevents a concurrent writer from being overwritten.
            os.link(path, directory / path.name)
            path.unlink()
    if not write_record:
        return
    fd, temporary = tempfile.mkstemp(prefix=".fyron-manifest-", dir=directory)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump({"version": 1, "files": records}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, marker)
    finally:
        Path(temporary).unlink(missing_ok=True)
