"""IO helpers for local files, tables, JSON, S3-compatible storage, and Teable."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class DataIO:
    """Convenience wrappers for local table and JSON IO."""

    @staticmethod
    def read_csv(path: str, **kwargs: Any) -> pd.DataFrame:
        return pd.read_csv(path, **kwargs)

    @staticmethod
    def write_csv(df: pd.DataFrame, path: str, **kwargs: Any) -> None:
        df.to_csv(path, index=False, **kwargs)

    @staticmethod
    def read_excel(path: str, **kwargs: Any) -> pd.DataFrame:
        return pd.read_excel(path, **kwargs)

    @staticmethod
    def write_excel(df: pd.DataFrame, path: str, **kwargs: Any) -> None:
        df.to_excel(path, index=False, **kwargs)

    @staticmethod
    def read_json(path: str | Path, **kwargs: Any) -> Any:
        return read_json(path, **kwargs)

    @staticmethod
    def write_json(
        payload: Any,
        path: str | Path,
        *,
        indent: int | None = 2,
        create_parent: bool = True,
        **kwargs: Any,
    ) -> Path:
        return write_json(payload, path, indent=indent, create_parent=create_parent, **kwargs)

    @staticmethod
    def read_table(path: str | Path, *, file_format: str | None = None, **kwargs: Any) -> pd.DataFrame:
        return read_table(path, file_format=file_format, **kwargs)

    @staticmethod
    def write_table(
        df: pd.DataFrame,
        path: str | Path,
        *,
        file_format: str | None = None,
        create_parent: bool = True,
        index: bool = False,
        **kwargs: Any,
    ) -> Path:
        return write_table(df, path, file_format=file_format, create_parent=create_parent, index=index, **kwargs)

    @staticmethod
    def summarize_table(df: pd.DataFrame, *, name: str | None = None) -> dict[str, Any]:
        return summarize_table(df, name=name)

    @staticmethod
    def describe_file(path: str | Path) -> dict[str, Any]:
        return describe_file(path)


@dataclass
class TeableConfig:
    base_url: str
    token: str


class TeableClient:
    """Minimal Teable table client for reading/writing DataFrames.

    Environment variables:
    - TEABLE_BASE_URL
    - TEABLE_TOKEN
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.config = TeableConfig(
            base_url=base_url or os.environ.get("TEABLE_BASE_URL", "https://app.teable.ai"),
            token=token or os.environ.get("TEABLE_TOKEN", ""),
        )
        if not self.config.token:
            raise ValueError("Teable token is required (set TEABLE_TOKEN or pass token).")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json",
            }
        )

    def list_records(
        self,
        table_id: str,
        *,
        view_id: Optional[str] = None,
        take: int = 1000,
        skip: int = 0,
        field_key_type: str = "name",
        cell_format: str = "json",
        projection: Optional[List[str]] = None,
        **params: Any,
    ) -> Dict[str, Any]:
        url = self._url(f"/api/table/{table_id}/record")
        query: Dict[str, Any] = {
            "take": take,
            "skip": skip,
            "fieldKeyType": field_key_type,
            "cellFormat": cell_format,
        }
        if view_id:
            query["viewId"] = view_id
        if projection:
            query["projection"] = projection
        query.update(params)
        resp = self.session.get(url, params=query, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def list_spaces(self) -> List[Dict[str, Any]]:
        """List spaces available to the current token."""
        url = self._url("/api/space")
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def list_bases(self, *, space_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List bases for a space or all accessible bases."""
        if space_id:
            url = self._url(f"/api/space/{space_id}/base")
        else:
            url = self._url("/api/base/access/all")
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def create_base(
        self,
        *,
        space_id: str,
        name: str,
        icon: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a base in a space."""
        url = self._url("/api/base")
        body: Dict[str, Any] = {"spaceId": space_id, "name": name}
        if icon:
            body["icon"] = icon
        resp = self.session.post(url, json=body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_or_create_base(
        self,
        *,
        name: str,
        space_id: Optional[str] = None,
        space_name: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a base by name, creating it if it doesn't exist."""
        resolved_space_id = space_id
        if not resolved_space_id and space_name:
            spaces = self.list_spaces()
            matches = [s for s in spaces if s.get("name") == space_name]
            if not matches:
                raise ValueError(f"Space '{space_name}' not found.")
            resolved_space_id = matches[0].get("id")
        if not resolved_space_id:
            spaces = self.list_spaces()
            if len(spaces) == 1:
                resolved_space_id = spaces[0].get("id")
            else:
                raise ValueError("space_id (or space_name) is required to create a base.")

        bases = self.list_bases(space_id=resolved_space_id)
        for base in bases:
            if base.get("name") == name:
                return base
        return self.create_base(space_id=resolved_space_id, name=name, icon=icon)

    def list_tables(self, base_id: str) -> List[Dict[str, Any]]:
        """List tables in a base."""
        url = self._url(f"/api/base/{base_id}/table")
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def create_table(
        self,
        *,
        base_id: str,
        name: str,
        db_table_name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        views: Optional[List[Dict[str, Any]]] = None,
        records: Optional[List[Dict[str, Any]]] = None,
        order: Optional[int] = None,
        field_key_type: str = "name",
    ) -> Dict[str, Any]:
        """Create a table in a base."""
        url = self._url(f"/api/base/{base_id}/table")
        body: Dict[str, Any] = {"name": name, "fieldKeyType": field_key_type}
        if db_table_name:
            body["dbTableName"] = db_table_name
        if description:
            body["description"] = description
        if icon:
            body["icon"] = icon
        if fields is not None:
            body["fields"] = fields
        if views is not None:
            body["views"] = views
        if records is not None:
            body["records"] = records
        if order is not None:
            body["order"] = order
        resp = self.session.post(url, json=body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_or_create_table(
        self,
        *,
        base_id: str,
        name: str,
        db_table_name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        views: Optional[List[Dict[str, Any]]] = None,
        records: Optional[List[Dict[str, Any]]] = None,
        order: Optional[int] = None,
        field_key_type: str = "name",
    ) -> Dict[str, Any]:
        """Return a table by name (or db_table_name), creating it if missing."""
        tables = self.list_tables(base_id)
        for table in tables:
            if table.get("name") == name:
                return table
            if db_table_name and table.get("dbTableName") == db_table_name:
                return table
        return self.create_table(
            base_id=base_id,
            name=name,
            db_table_name=db_table_name,
            description=description,
            icon=icon,
            fields=fields,
            views=views,
            records=records,
            order=order,
            field_key_type=field_key_type,
        )

    def read_table(
        self,
        table_id: str,
        *,
        view_id: Optional[str] = None,
        field_key_type: str = "name",
        cell_format: str = "json",
        projection: Optional[List[str]] = None,
        take: int = 1000,
        max_records: Optional[int] = None,
    ) -> pd.DataFrame:
        records: List[Dict[str, Any]] = []
        skip = 0
        while True:
            payload = self.list_records(
                table_id,
                view_id=view_id,
                take=take,
                skip=skip,
                field_key_type=field_key_type,
                cell_format=cell_format,
                projection=projection,
            )
            batch = payload.get("records", [])
            records.extend(batch)
            if max_records is not None and len(records) >= max_records:
                records = records[:max_records]
                break
            if len(batch) < take:
                break
            skip += take
        rows = [record.get("fields", {}) for record in records]
        df = pd.DataFrame(rows)
        if "id" not in df.columns and records:
            df.insert(0, "record_id", [r.get("id") for r in records])
        return df

    def create_records(
        self,
        table_id: str,
        records: Iterable[Dict[str, Any]],
        *,
        field_key_type: str = "name",
        typecast: bool = True,
        order: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self._url(f"/api/table/{table_id}/record")
        body: Dict[str, Any] = {
            "records": [{"fields": r} for r in records],
            "fieldKeyType": field_key_type,
            "typecast": typecast,
        }
        if order:
            body["order"] = order
        resp = self.session.post(url, json=body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def delete_records(
        self,
        table_id: str,
        record_ids: List[str],
    ) -> None:
        """Delete records by ID."""
        if not record_ids:
            return
        url = self._url(f"/api/table/{table_id}/record")
        resp = self.session.delete(url, params={"recordIds": record_ids}, timeout=self.timeout)
        resp.raise_for_status()

    def clear_table(
        self,
        table_id: str,
        *,
        batch_size: int = 200,
        take: int = 1000,
    ) -> int:
        """Delete all records in a table and return deleted count."""
        deleted = 0
        skip = 0
        while True:
            payload = self.list_records(table_id, take=take, skip=skip)
            records = payload.get("records", [])
            record_ids = [r.get("id") for r in records if r.get("id")]
            if not record_ids:
                break
            for idx in range(0, len(record_ids), batch_size):
                self.delete_records(table_id, record_ids[idx : idx + batch_size])
                deleted += len(record_ids[idx : idx + batch_size])
            if len(records) < take:
                break
            skip += take
        return deleted

    def write_dataframe(
        self,
        table_id: str,
        df: pd.DataFrame,
        *,
        field_key_type: str = "name",
        typecast: bool = True,
        chunk_size: int = 200,
    ) -> List[str]:
        record_ids: List[str] = []
        rows = df.to_dict(orient="records")
        for idx in range(0, len(rows), chunk_size):
            batch = rows[idx : idx + chunk_size]
            payload = self.create_records(
                table_id,
                batch,
                field_key_type=field_key_type,
                typecast=typecast,
            )
            record_ids.extend([r.get("id") for r in payload.get("records", [])])
        return record_ids

    def overwrite_table(
        self,
        table_id: str,
        df: pd.DataFrame,
        *,
        delete_batch_size: int = 200,
        create_chunk_size: int = 200,
        field_key_type: str = "name",
        typecast: bool = True,
    ) -> List[str]:
        """Delete all records in a table, then write the DataFrame."""
        self.clear_table(table_id, batch_size=delete_batch_size)
        return self.write_dataframe(
            table_id,
            df,
            field_key_type=field_key_type,
            typecast=typecast,
            chunk_size=create_chunk_size,
        )

    def read_cohort(
        self,
        table_id: str,
        *,
        id_col: str | None = None,
        required_columns: list[str] | None = None,
        view_id: str | None = None,
        max_records: int | None = None,
    ) -> pd.DataFrame:
        """Read a reviewed Teable cohort and validate basic cohort shape."""
        df = self.read_table(table_id, view_id=view_id, max_records=max_records)
        _validate_cohort_dataframe(df, id_col=id_col, required_columns=required_columns)
        return df

    def write_research_cohort(
        self,
        table_id: str,
        df: pd.DataFrame,
        *,
        mode: str = "append",
        cohort_name: str | None = None,
        version: str | None = None,
        metadata: dict[str, Any] | None = None,
        id_col: str | None = None,
        field_key_type: str = "name",
        typecast: bool = True,
        chunk_size: int = 200,
    ) -> dict[str, Any]:
        """Write a finished research cohort to Teable and return an audit summary."""
        if mode not in {"append", "overwrite"}:
            raise ValueError("mode must be 'append' or 'overwrite'.")
        _validate_cohort_dataframe(df, id_col=id_col)
        if mode == "overwrite":
            record_ids = self.overwrite_table(
                table_id,
                df,
                field_key_type=field_key_type,
                typecast=typecast,
                create_chunk_size=chunk_size,
            )
        else:
            record_ids = self.write_dataframe(
                table_id,
                df,
                field_key_type=field_key_type,
                typecast=typecast,
                chunk_size=chunk_size,
            )
        return {
            "table_id": table_id,
            "mode": mode,
            "rows": int(len(df)),
            "columns": list(df.columns),
            "record_ids": record_ids,
            "record_count": len(record_ids),
            "cohort_name": cohort_name,
            "version": version,
            "metadata": metadata or {},
            "written_at": datetime.now(timezone.utc).isoformat(),
        }

    def create_research_cohort_table(
        self,
        *,
        base_id: str,
        name: str,
        df: pd.DataFrame | None = None,
        description: str | None = None,
        fields: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a Teable table for a research cohort."""
        inferred_fields = fields
        if inferred_fields is None and df is not None:
            inferred_fields = _infer_teable_fields(df)
        table = self.create_table(
            base_id=base_id,
            name=name,
            description=description or _cohort_description(metadata),
            fields=inferred_fields,
        )
        return {"table": table, "fields": inferred_fields or [], "metadata": metadata or {}}

    def summarize_teable_table(
        self,
        table_id: str,
        *,
        view_id: str | None = None,
        projection: list[str] | None = None,
        max_records: int | None = None,
    ) -> dict[str, Any]:
        """Return a compact summary for a Teable table."""
        df = self.read_table(table_id, view_id=view_id, projection=projection, max_records=max_records)
        summary = summarize_table(df, name=table_id)
        summary.update({"table_id": table_id, "view_id": view_id, "projection": projection})
        return summary

    def _url(self, path: str) -> str:
        return self.config.base_url.rstrip("/") + path


def ensure_parent_dir(path: str | Path) -> Path:
    """Create the parent directory for a file path and return the path."""
    resolved = Path(path)
    if resolved.parent and str(resolved.parent) not in {"", "."}:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def read_json(path: str | Path, **kwargs: Any) -> Any:
    """Read a UTF-8 JSON file."""
    with Path(path).open("r", encoding=kwargs.pop("encoding", "utf-8")) as handle:
        return json.load(handle, **kwargs)


def write_json(
    payload: Any,
    path: str | Path,
    *,
    indent: int | None = 2,
    create_parent: bool = True,
    **kwargs: Any,
) -> Path:
    """Write a UTF-8 JSON file and return the output path."""
    output = ensure_parent_dir(path) if create_parent else Path(path)
    with output.open("w", encoding=kwargs.pop("encoding", "utf-8")) as handle:
        json.dump(payload, handle, indent=indent, **kwargs)
    return output


def read_table(path: str | Path, *, file_format: str | None = None, **kwargs: Any) -> pd.DataFrame:
    """Read a table from CSV, TSV, Excel, JSON, or JSONL."""
    input_path = Path(path)
    fmt = _normalize_table_format(file_format or input_path.suffix)
    if fmt == "csv":
        return pd.read_csv(input_path, **kwargs)
    if fmt == "tsv":
        return pd.read_csv(input_path, sep="\t", **kwargs)
    if fmt == "excel":
        return pd.read_excel(input_path, **kwargs)
    if fmt == "json":
        return pd.read_json(input_path, **kwargs)
    if fmt == "jsonl":
        return pd.read_json(input_path, lines=True, **kwargs)
    raise ValueError(f"Unsupported table format: {file_format or input_path.suffix}")


def write_table(
    df: pd.DataFrame,
    path: str | Path,
    *,
    file_format: str | None = None,
    create_parent: bool = True,
    index: bool = False,
    **kwargs: Any,
) -> Path:
    """Write a table to CSV, TSV, Excel, JSON, or JSONL and return the path."""
    output = ensure_parent_dir(path) if create_parent else Path(path)
    fmt = _normalize_table_format(file_format or output.suffix)
    if fmt == "csv":
        df.to_csv(output, index=index, **kwargs)
    elif fmt == "tsv":
        df.to_csv(output, sep="\t", index=index, **kwargs)
    elif fmt == "excel":
        df.to_excel(output, index=index, **kwargs)
    elif fmt == "json":
        df.to_json(output, orient=kwargs.pop("orient", "records"), **kwargs)
    elif fmt == "jsonl":
        df.to_json(output, orient=kwargs.pop("orient", "records"), lines=True, **kwargs)
    else:
        raise ValueError(f"Unsupported table format: {file_format or output.suffix}")
    return output


def summarize_table(df: pd.DataFrame, *, name: str | None = None) -> dict[str, Any]:
    """Return compact metadata for a DataFrame."""
    return {
        "name": name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
    }


def describe_file(path: str | Path) -> dict[str, Any]:
    """Return file metadata without reading the payload."""
    file_path = Path(path)
    exists = file_path.exists()
    stat = file_path.stat() if exists else None
    return {
        "path": str(file_path.resolve()) if exists else str(file_path),
        "exists": exists,
        "suffix": file_path.suffix,
        "size_bytes": int(stat.st_size) if stat else None,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat() if stat else None,
    }


def read_csv(path: str, **kwargs: Any) -> pd.DataFrame:
    """Read a CSV file (shortcut for DataIO.read_csv)."""
    return DataIO.read_csv(path, **kwargs)


def write_csv(df: pd.DataFrame, path: str, **kwargs: Any) -> None:
    """Write a DataFrame to CSV (shortcut for DataIO.write_csv)."""
    DataIO.write_csv(df, path, **kwargs)


def read_excel(path: str, **kwargs: Any) -> pd.DataFrame:
    """Read an Excel file (shortcut for DataIO.read_excel)."""
    return DataIO.read_excel(path, **kwargs)


def write_excel(df: pd.DataFrame, path: str, **kwargs: Any) -> None:
    """Write a DataFrame to Excel (shortcut for DataIO.write_excel)."""
    DataIO.write_excel(df, path, **kwargs)


def _normalize_table_format(value: str | None) -> str:
    fmt = (value or "").lower().lstrip(".")
    aliases = {
        "csv": "csv",
        "tsv": "tsv",
        "xlsx": "excel",
        "xls": "excel",
        "excel": "excel",
        "json": "json",
        "jsonl": "jsonl",
        "ndjson": "jsonl",
    }
    if fmt not in aliases:
        raise ValueError(f"Unsupported table format: {value}")
    return aliases[fmt]


def _validate_cohort_dataframe(
    df: pd.DataFrame,
    *,
    id_col: str | None = None,
    required_columns: list[str] | None = None,
) -> None:
    missing = [column for column in (required_columns or []) if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required cohort columns: {missing}")
    if id_col:
        if id_col not in df.columns:
            raise ValueError(f"id_col '{id_col}' is not present in the cohort table.")
        if df[id_col].duplicated().any():
            raise ValueError(f"id_col '{id_col}' contains duplicate values.")


def _infer_teable_fields(df: pd.DataFrame) -> list[dict[str, Any]]:
    fields = []
    for column, dtype in df.dtypes.items():
        if pd.api.types.is_bool_dtype(dtype):
            field_type = "checkbox"
        elif pd.api.types.is_numeric_dtype(dtype):
            field_type = "number"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            field_type = "date"
        else:
            field_type = "singleLineText"
        fields.append({"name": str(column), "type": field_type})
    return fields


def _cohort_description(metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None
    parts = [f"{key}: {value}" for key, value in metadata.items()]
    return "Fyron research cohort. " + "; ".join(parts)
