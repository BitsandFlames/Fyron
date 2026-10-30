"""Optional S3 and S3-compatible object storage helpers."""

from __future__ import annotations

from .._diagnostics import safe_network_errors

import io
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd

from .io import ensure_parent_dir


def _require_boto3():
    try:
        import boto3  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised in tests with import hook
        raise ImportError('boto3 is required for S3 support. Install with `uv add "fyron[s3]"`.') from exc
    return boto3


def parse_s3_uri(uri: str) -> dict[str, str]:
    """Parse an s3://bucket/key URI."""
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError("S3 URI must look like s3://bucket/key")
    return {"bucket": parsed.netloc, "key": parsed.path.lstrip("/")}


class S3Storage:
    """Small S3 wrapper for clinical data science tables and sidecar files.

    Parameters
    ----------
    bucket:
        Bucket name. Defaults to ``S3_BUCKET``.
    prefix:
        Optional key prefix prepended to reads and writes. Defaults to
        ``S3_PREFIX`` when omitted.
    endpoint_url:
        Optional S3-compatible endpoint URL such as MinIO. Defaults to
        ``S3_ENDPOINT_URL``.
    region_name:
        AWS region name. Defaults to ``AWS_REGION`` or ``AWS_DEFAULT_REGION``.
    profile_name:
        Optional boto3 profile name for local credential resolution.
    access_key_id:
        Optional explicit access key ID for S3-compatible deployments.
    secret_access_key:
        Optional explicit secret access key. Prefer environment variables or a
        profile for shared research environments.
    session_token:
        Optional temporary session token.
    """

    @safe_network_errors
    def __init__(
        self,
        bucket: str | None = None,
        *,
        prefix: str = "",
        endpoint_url: str | None = None,
        region_name: str | None = None,
        profile_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        session_token: str | None = None,
    ) -> None:
        """Create an S3 storage client.

        Parameters
        ----------
        bucket:
            Bucket name. Defaults to ``S3_BUCKET``.
        prefix:
            Optional key prefix prepended to reads and writes. Defaults to
            ``S3_PREFIX`` when omitted.
        endpoint_url:
            Optional S3-compatible endpoint URL such as MinIO. Defaults to
            ``S3_ENDPOINT_URL``.
        region_name:
            AWS region name. Defaults to ``AWS_REGION`` or
            ``AWS_DEFAULT_REGION``.
        profile_name:
            Optional boto3 profile name for local credential resolution.
        access_key_id:
            Optional explicit access key ID for S3-compatible deployments.
        secret_access_key:
            Optional explicit secret access key. Prefer environment variables
            or a profile for shared research environments.
        session_token:
            Optional temporary session token.
        """
        boto3 = _require_boto3()
        self.bucket = bucket or os.environ.get("S3_BUCKET")
        if not self.bucket:
            raise ValueError("S3 bucket is required. Pass bucket=... or set S3_BUCKET.")
        self.prefix = _clean_prefix(prefix or os.environ.get("S3_PREFIX", ""))
        endpoint = endpoint_url or os.environ.get("S3_ENDPOINT_URL")
        region = region_name or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        session_kwargs: dict[str, Any] = {}
        if profile_name:
            session_kwargs["profile_name"] = profile_name
        session = boto3.Session(**session_kwargs)
        client_kwargs: dict[str, Any] = {"endpoint_url": endpoint, "region_name": region}
        if access_key_id:
            client_kwargs["aws_access_key_id"] = access_key_id
        if secret_access_key:
            client_kwargs["aws_secret_access_key"] = secret_access_key
        if session_token:
            client_kwargs["aws_session_token"] = session_token
        self.client = session.client("s3", **{k: v for k, v in client_kwargs.items() if v is not None})

    def key(self, key: str) -> str:
        """Return a key with the configured prefix applied."""
        key = key.lstrip("/")
        return f"{self.prefix}/{key}" if self.prefix else key

    @safe_network_errors
    def exists(self, key: str) -> bool:
        """Return false only for an explicit not-found response; other errors raise."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=self.key(key))
            return True
        except Exception as exc:
            response = getattr(exc, "response", {})
            if isinstance(response, dict):
                status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                code = response.get("Error", {}).get("Code")
                if status == 404 or (status is None and code in {"404", "NoSuchKey", "NotFound"}):
                    return False
            raise

    @safe_network_errors
    def list(self, prefix: str | None = None, *, suffix: str | None = None, max_keys: int | None = None) -> list[dict[str, Any]]:
        """List all pages; max_keys limits returned items after suffix filtering."""
        if max_keys is not None and (type(max_keys) is not int or max_keys < 0):
            raise ValueError("max_keys must be a nonnegative integer or None.")
        if max_keys == 0:
            return []
        search_prefix = self.key(prefix or "")
        kwargs: dict[str, Any] = {"Bucket": self.bucket, "Prefix": search_prefix}
        items = []
        seen = set()
        while True:
            kwargs["MaxKeys"] = min(1000, max_keys - len(items)) if max_keys is not None else 1000
            response = self.client.list_objects_v2(**kwargs)
            for item in response.get("Contents", []):
                if not suffix or item.get("Key", "").endswith(suffix):
                    items.append(item)
                    if max_keys is not None and len(items) >= max_keys:
                        return items
            if not response.get("IsTruncated", False):
                return items
            token = response.get("NextContinuationToken")
            if not isinstance(token, str) or not token or token in seen:
                raise RuntimeError("Invalid S3 pagination continuation.")
            seen.add(token)
            kwargs["ContinuationToken"] = token

    @safe_network_errors
    def read_bytes(self, key: str) -> bytes:
        """Read an object as bytes."""
        response = self.client.get_object(Bucket=self.bucket, Key=self.key(key))
        return response["Body"].read()

    @safe_network_errors
    def write_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        """Write bytes to S3 and return the s3 URI."""
        kwargs: dict[str, Any] = {"Bucket": self.bucket, "Key": self.key(key), "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        self.client.put_object(**kwargs)
        return f"s3://{self.bucket}/{self.key(key)}"

    def read_json(self, key: str) -> Any:
        """Read a JSON object."""
        return json.loads(self.read_bytes(key).decode("utf-8"))

    def write_json(self, key: str, payload: Any, *, indent: int | None = 2) -> str:
        """Write a JSON object."""
        data = json.dumps(payload, indent=indent).encode("utf-8")
        return self.write_bytes(key, data, content_type="application/json")

    def read_table(self, key: str, *, file_format: str | None = None, **kwargs: Any) -> pd.DataFrame:
        """Read a table from S3."""
        data = self.read_bytes(key)
        fmt = _table_format(file_format or Path(key).suffix)
        if fmt == "csv":
            return pd.read_csv(io.BytesIO(data), **kwargs)
        if fmt == "tsv":
            return pd.read_csv(io.BytesIO(data), sep="\t", **kwargs)
        if fmt == "excel":
            return pd.read_excel(io.BytesIO(data), **kwargs)
        if fmt == "json":
            return pd.read_json(io.BytesIO(data), **kwargs)
        if fmt == "jsonl":
            return pd.read_json(io.BytesIO(data), lines=True, **kwargs)
        raise ValueError(f"Unsupported table format: {file_format or Path(key).suffix}")

    def write_table(
        self,
        key: str,
        df: pd.DataFrame,
        *,
        file_format: str | None = None,
        index: bool = False,
        **kwargs: Any,
    ) -> str:
        """Write a table to S3."""
        fmt = _table_format(file_format or Path(key).suffix)
        buffer = io.BytesIO()
        if fmt == "csv":
            data = df.to_csv(index=index, **kwargs).encode("utf-8")
            return self.write_bytes(key, data, content_type="text/csv")
        if fmt == "tsv":
            data = df.to_csv(index=index, sep="\t", **kwargs).encode("utf-8")
            return self.write_bytes(key, data, content_type="text/tab-separated-values")
        if fmt == "excel":
            df.to_excel(buffer, index=index, **kwargs)
            return self.write_bytes(key, buffer.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if fmt == "json":
            data = df.to_json(orient=kwargs.pop("orient", "records"), **kwargs).encode("utf-8")
            return self.write_bytes(key, data, content_type="application/json")
        if fmt == "jsonl":
            data = df.to_json(orient=kwargs.pop("orient", "records"), lines=True, **kwargs).encode("utf-8")
            return self.write_bytes(key, data, content_type="application/x-ndjson")
        raise ValueError(f"Unsupported table format: {file_format or Path(key).suffix}")

    @safe_network_errors
    def download_file(self, key: str, local_path: str | Path, *, create_parent: bool = True) -> Path:
        """Download an object to a local file."""
        output = ensure_parent_dir(local_path) if create_parent else Path(local_path)
        self.client.download_file(self.bucket, self.key(key), str(output))
        return output

    @safe_network_errors
    def upload_file(self, local_path: str | Path, key: str | None = None, *, content_type: str | None = None) -> str:
        """Upload a local file and return the s3 URI."""
        source = Path(local_path)
        target_key = self.key(key or source.name)
        extra_args = {"ContentType": content_type} if content_type else None
        if extra_args:
            self.client.upload_file(str(source), self.bucket, target_key, ExtraArgs=extra_args)
        else:
            self.client.upload_file(str(source), self.bucket, target_key)
        return f"s3://{self.bucket}/{target_key}"


def read_s3_table(uri: str, **kwargs: Any) -> pd.DataFrame:
    """Read a table from an s3:// URI."""
    parsed = parse_s3_uri(uri)
    return S3Storage(bucket=parsed["bucket"]).read_table(parsed["key"], **kwargs)


def write_s3_table(df: pd.DataFrame, uri: str, **kwargs: Any) -> str:
    """Write a DataFrame to an s3:// URI."""
    parsed = parse_s3_uri(uri)
    return S3Storage(bucket=parsed["bucket"]).write_table(parsed["key"], df, **kwargs)


def _clean_prefix(prefix: str) -> str:
    return prefix.strip("/")


def _table_format(value: str | None) -> str:
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
