"""Read-only data adapters. Configure connections outside the model conversation."""
import csv
import json
import os
import re
from fyron.documents._text import extract_text, TextFailure
from email.message import Message
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

import requests
from fyron import DocumentDownloader, FHIRRestClient, FHIRSQLClient

LIMIT = 30
MAX_CHARS = 8000


class Incomplete(Exception):
    """The requested evidence could not be supplied in full."""


def inside(root, relative):
    root = root.resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Invalid source path")
    return path


def rows(path, patient, required):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"patient_id", *required}.issubset(reader.fieldnames or []):
            raise ValueError("Missing CSV columns")
        return [r for r in reader if r["patient_id"] == patient]


def bounded(items):
    if len(items) > LIMIT:
        raise Incomplete("record_limit")
    return items


def extract(path, media_type, charset="utf-8-sig"):
    if path.stat().st_size > 5_000_000:
        raise Incomplete("file_limit")
    try:
        return extract_text(path, media_type, charset=charset, limit=MAX_CHARS, timeout=30).strip()
    except TextFailure as exc:
        raise Incomplete(str(exc)) from None


def index_documents(records, location):
    result = {}
    for row in bounded(records):
        label = row["label"]
        if not re.fullmatch(r"D[1-9][0-9]*", label) or label in result or not row[location]:
            raise ValueError("Invalid or duplicate document label")
        result[label] = row
    return result


def sandbox(root, patient):
    def studies():
        bundle = json.loads(inside(root, "fhir/studies.bundle.json").read_text())
        if bundle.get("resourceType") != "Bundle":
            raise ValueError("Expected a FHIR Bundle")
        resources = [entry["resource"] for entry in bundle["entry"]]
        return bounded([r.get("started") for r in resources if r.get("resourceType") == "ImagingStudy"
                        and r.get("subject", {}).get("reference") == f"Patient/{patient}"])

    def encounters():
        return bounded([r["date"] for r in rows(inside(root, "tables/encounters.csv"), patient, ["date"])])

    records = rows(inside(root, "documents/manifest.csv"), patient, ["label", "category", "date", "path"])
    index = index_documents(records, "path")

    def read(label):
        relative = Path(index[label]["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid document path")
        path = inside(root, Path("documents") / relative)
        media = {".txt": "text/plain", ".pdf": "application/pdf"}.get(path.suffix.lower())
        return extract(path, media)
    return studies, encounters, index, read


def fhir_studies(client, patient):
    ref = f"Patient/{patient}"
    result = client.search_df("ImagingStudy", params={"patient": ref, "_count": 20},
                              max_pages=2, use_multiprocessing=False,
                              fhir_paths=[("owner", "subject.reference"), ("date", "started")],
                              return_report=True)
    if not result["report"]["summary"].iloc[0]["retrieval_exhaustive"]:
        raise Incomplete("pagination_limit")
    frame = result["data"]
    if frame.empty:
        return []
    if not frame.owner.eq(ref).fillna(False).all():
        raise Incomplete("patient_mismatch")
    return bounded(frame.date.tolist())


def sql_encounters(client, patient):
    # Adapt this fixed view and its columns to your site's approved schema.
    data = client.query_df(
        "SELECT patient_id, encounter_date FROM research.encounters "
        "WHERE patient_id = %(patient)s ORDER BY encounter_date LIMIT 31",
        params={"patient": patient})
    if not data.patient_id.eq(patient).fillna(False).all():
        raise Incomplete("patient_mismatch")
    return bounded(data.encounter_date.tolist())


def checked_origin(url):
    if not url.isascii() or any(ord(c) <= 32 for c in url) or "\\" in url:
        raise ValueError("Invalid document URL")
    u = urlsplit(url)
    if u.scheme != "https" or not u.hostname or u.username is not None or u.password is not None:
        raise ValueError("Expected a credential-free HTTPS URL")
    return u.hostname, u.port if u.port is not None else 443


def connected(stack, patient, enabled):
    studies = encounters = index = read = None
    mapped = {"fhir_id": patient, "sql_id": patient}
    if os.environ.get("HARNESS_PATIENT_MAP"):
        matches = rows(Path(os.environ["HARNESS_PATIENT_MAP"]), patient, ["fhir_id", "sql_id"])
        if len(matches) != 1:
            raise ValueError("Expected exactly one patient mapping")
        mapped = matches[0]
    if "fhir" in enabled:
        base = os.environ["FHIR_BASE_URL"]
        checked_origin(base)
        client = stack.enter_context(FHIRRestClient(base_url=base,
                                                   bearer_token=os.environ["HARNESS_FHIR_TOKEN"]))
        def studies():
            return fhir_studies(client, mapped["fhir_id"])
    if "sql" in enabled:
        from psycopg.conninfo import make_conninfo
        dsn = make_conninfo(os.environ["FHIR_DB_DSN"], options="-c default_transaction_read_only=on")
        db = stack.enter_context(FHIRSQLClient(dsn=dsn, statement_timeout=15))
        def encounters():
            return sql_encounters(db, mapped["sql_id"])
    if "documents" in enabled:
        index = index_documents(rows(Path(os.environ["HARNESS_DOCUMENT_INDEX"]), patient,
                                     ["label", "category", "date", "url"]), "url")
        origin = checked_origin(os.environ["HARNESS_DOCUMENT_ORIGIN"])
        if any(checked_origin(row["url"]) != origin for row in index.values()):
            raise ValueError("Document outside approved origin")
        session = stack.enter_context(requests.Session())
        session.trust_env = False
        session.headers["Authorization"] = "Bearer " + os.environ["HARNESS_DOCUMENT_TOKEN"]
        directory = stack.enter_context(TemporaryDirectory())
        loader = stack.enter_context(DocumentDownloader(auth=session, output_dir=directory,
            allow_redirects=False, max_download_bytes=5_000_000, write_completion_record=False,
            expected_content_types=["application/pdf", "text/plain"]))
        def read(label):
            with TemporaryDirectory(dir=directory) as staging:
                result = loader.download_url(index[label]["url"], output_path=Path(staging) / "document")
                if result.error or result.status_code != 200:
                    raise Incomplete(getattr(result, "reason", None) or "download_failed")
                header = Message()
                header["Content-Type"] = result.content_type or ""
                return extract(Path(result.path), header.get_content_type(), header.get_content_charset() or "utf-8-sig")
    return studies, encounters, index, read
