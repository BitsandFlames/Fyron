"""FHIR SQL client helpers for Postgres-backed FHIR databases."""

from __future__ import annotations

from .._diagnostics import event, safe_error, batch_report, error_event, task_outcome

import logging
import os
import multiprocessing as mp
import re
import time
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

import pandas as pd
try:
    import psycopg
except Exception as exc:  # pragma: no cover
    psycopg = None  # type: ignore
    _PSYCOPG_IMPORT_ERROR = exc

logger = logging.getLogger(__name__)


class SQLQueryError(RuntimeError):
    """Raised when a SQL query fails or returns invalid results."""


@dataclass
class SQLConfig:
    dsn: Optional[str]
    host: Optional[str]
    port: Optional[int]
    dbname: Optional[str]
    user: Optional[str]
    password: Optional[str]
    sslmode: Optional[str]


@dataclass
class SQLPartition:
    """One SQL extraction partition with query params and trace metadata."""

    params: Dict[str, Any]
    metadata: Dict[str, Any]


class FHIRSQLClient:
    """Lightweight SQL client for FHIR-backed databases.

    Environment variables (optional):
    - FHIR_DB_DSN
    - FHIR_DB_HOST
    - FHIR_DB_PORT
    - FHIR_DB_NAME
    - FHIR_DB_USER
    - FHIR_DB_PASSWORD
    - FHIR_DB_SSLMODE
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        dbname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        sslmode: Optional[str] = None,
        connect_timeout: int = 10,
        log_queries: bool = False,
    ) -> None:
        """Initialize a SQL client for Postgres-backed FHIR data."""
        if psycopg is None:
            raise ImportError(
                "psycopg is required for FHIRSQLClient. Install with `uv add psycopg` "
                "and ensure libpq is available."
            ) from _PSYCOPG_IMPORT_ERROR
        self.config = SQLConfig(
            dsn=dsn or os.environ.get("FHIR_DB_DSN"),
            host=host or os.environ.get("FHIR_DB_HOST"),
            port=port or _maybe_int(os.environ.get("FHIR_DB_PORT")),
            dbname=dbname or os.environ.get("FHIR_DB_NAME"),
            user=user or os.environ.get("FHIR_DB_USER"),
            password=password or os.environ.get("FHIR_DB_PASSWORD"),
            sslmode=sslmode or os.environ.get("FHIR_DB_SSLMODE"),
        )
        self.connect_timeout = connect_timeout
        self.log_queries = log_queries
        self._conn = self._connect()

    def __enter__(self) -> "FHIRSQLClient":
        """Return self for context manager usage."""
        return self

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        """Close the connection on context manager exit."""
        self.close()

    def query(
        self,
        sql: str,
        params: Optional[Dict[str, Any] | Sequence[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a SQL query and return rows as dicts."""
        try:
            with self._conn.cursor() as cur:
                if self.log_queries:
                    event(logger, "sql", "activity", level=logging.DEBUG)
                    event(logger, "sql", "activity", level=logging.DEBUG)
                cur.execute(sql, params)
                if cur.description is None:
                    return []
                columns = [col.name for col in cur.description]
                rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except psycopg.Error as exc:
            error_event(logger, "sql", exc)
            raise SQLQueryError("SQL query failed") from None

    def query_to_dataframe(
        self,
        sql: str,
        params: Optional[Dict[str, Any] | Sequence[Any]] = None,
        rename: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """Execute a SQL query and return a DataFrame.

        Parameters
        ----------
        sql:
            SQL statement with placeholders.
        params:
            Optional parameters (dict for named, sequence for positional).
        rename:
            Optional mapping to rename columns in the resulting DataFrame.
        """
        try:
            if self.log_queries:
                event(logger, "sql", "activity", level=logging.DEBUG)
                event(logger, "sql", "activity", level=logging.DEBUG)
            df = pd.read_sql_query(sql, self._conn, params=params)
            if rename:
                df = df.rename(columns=rename)
            return df
        except Exception as exc:
            error_event(logger, "sql", exc)
            raise SQLQueryError("SQL query_to_dataframe failed") from None

    def query_df(
        self,
        sql: str,
        params: Optional[Dict[str, Any] | Sequence[Any]] = None,
        rename: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """Backward-compatible alias for query_to_dataframe."""
        return self.query_to_dataframe(sql=sql, params=params, rename=rename)

    @batch_report("sql")
    def query_df_partitioned(
        self,
        sql: str,
        *,
        start: Union[str, pd.Timestamp],
        end: Union[str, pd.Timestamp],
        params: Optional[Dict[str, Any]] = None,
        frequency: str = "YS",
        window_days: Optional[int] = None,
        param_grid: Optional[Mapping[str, Sequence[Any]]] = None,
        derived_params: Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]] = None,
        chunksize: int = 10000,
        rename: Optional[Dict[str, str]] = None,
        include_partition_columns: bool = True,
        deduplicate_by: Optional[Union[str, Sequence[str]]] = None,
        continue_on_error: bool = False,
        errors: str = "raise",
    ) -> pd.DataFrame:
        """Run a parameterized SQL query over time/grid partitions.

        Parameters
        ----------
        sql
            SQL statement using named placeholders such as ``%(start_ts)s``.
        start
            Inclusive start timestamp for the first partition.
        end
            Exclusive end timestamp for the final partition.
        params
            Base SQL parameters included in every partition.
        frequency
            Pandas date frequency used to build windows, for example ``YS`` or
            ``MS``.
        window_days
            Fixed partition width in days; overrides ``frequency``.
        param_grid
            Optional categorical grid, for example ``{"med": ["heparin"]}``.
        derived_params
            Optional callables that derive additional params from each
            partition, for example ``med_pattern`` from ``med``.
        chunksize
            Number of rows per streamed pandas chunk.
        rename
            Optional output column rename mapping.
        include_partition_columns
            Whether to append partition metadata columns to result rows.
        deduplicate_by
            Optional column or columns used to drop duplicate rows.
        continue_on_error
            Whether failed partitions should be skipped or recorded instead of
            stopping immediately.
        errors
            ``raise`` to raise failed partitions or ``record`` to append error
            rows with partition metadata.
        """
        if errors not in {"raise", "record"}:
            raise ValueError("errors must be 'raise' or 'record'.")
        partitions = build_sql_partitions(
            start=start,
            end=end,
            params=params,
            frequency=frequency,
            window_days=window_days,
            param_grid=param_grid,
            derived_params=derived_params,
        )
        frames: List[pd.DataFrame] = []
        error_rows: List[Dict[str, Any]] = []
        for partition in partitions:
            partition_frames: List[pd.DataFrame] = []
            try:
                for chunk in self.query_df_stream(
                    sql,
                    params=partition.params,
                    rename=rename,
                    chunksize=chunksize,
                ):
                    if include_partition_columns:
                        if set(chunk.columns).intersection(partition.metadata):
                            raise ValueError("Partition metadata conflicts with result columns.")
                        chunk = chunk.copy()
                        for key, value in partition.metadata.items():
                            chunk[key] = value
                    partition_frames.append(chunk)
            except Exception as exc:
                if not continue_on_error and errors == "raise":
                    raise
                row = dict(partition.metadata)
                row["_fyron_partition_status"] = "error"
                row["_fyron_partition_error"] = safe_error(exc)
                error_rows.append(row)
                task_outcome(failed=True)
                if errors == "raise" and not continue_on_error:
                    raise
            else:
                frames.extend(partition_frames)
                task_outcome()
        if error_rows and errors == "record":
            frames.append(pd.DataFrame(error_rows))
        result = _merge_frames(frames, merge="concat")
        if deduplicate_by and not result.empty:
            subset = [deduplicate_by] if isinstance(deduplicate_by, str) else list(deduplicate_by)
            result = result.drop_duplicates(subset=subset).reset_index(drop=True)
        return result

    def query_df_stream(
        self,
        sql: str,
        params: Optional[Dict[str, Any] | Sequence[Any]] = None,
        rename: Optional[Dict[str, str]] = None,
        chunksize: int = 10000,
    ) -> Iterator[pd.DataFrame]:
        """Stream a large SQL query as DataFrame chunks."""
        try:
            if self.log_queries:
                event(logger, "sql", "activity", level=logging.DEBUG)
                event(logger, "sql", "activity", level=logging.DEBUG)
            for chunk in pd.read_sql_query(sql, self._conn, params=params, chunksize=chunksize):
                if rename:
                    chunk = chunk.rename(columns=rename)
                yield chunk
        except Exception as exc:
            error_event(logger, "sql", exc)
            raise SQLQueryError("SQL query_df_stream failed") from None

    @batch_report("sql")
    def export_query_partitioned(
        self,
        sql: str,
        output_dir: Union[str, Path],
        *,
        start: Union[str, pd.Timestamp],
        end: Union[str, pd.Timestamp],
        params: Optional[Dict[str, Any]] = None,
        frequency: str = "YS",
        window_days: Optional[int] = None,
        param_grid: Optional[Mapping[str, Sequence[Any]]] = None,
        derived_params: Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]] = None,
        output_columns: Optional[Sequence[str]] = None,
        part_filename: str = "{date}.csv",
        combine_by: Optional[str] = None,
        combined_filename: str = "combined_{value}.csv",
        chunksize: int = 10000,
        skip_existing: bool = True,
        continue_on_error: bool = False,
        rename: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """Stream partitioned SQL query results to resumable CSV part files.

        Parameters
        ----------
        sql
            SQL statement using named placeholders such as ``%(start_ts)s``.
        output_dir
            Directory where ``_parts`` and optional combined CSVs are written.
        start
            Inclusive start timestamp for the first partition.
        end
            Exclusive end timestamp for the final partition.
        params
            Base SQL parameters included in every partition.
        frequency
            Pandas date frequency used to build windows.
        window_days
            Fixed partition width in days; overrides ``frequency``.
        param_grid
            Optional categorical grid expanded across every time window.
        derived_params
            Optional callables that derive additional params from each
            partition.
        output_columns
            Optional ordered columns to keep in exported CSVs.
        part_filename
            Relative filename template for partition CSVs.
        combine_by
            Optional metadata field used to combine parts, such as ``year``.
        combined_filename
            Filename template for combined CSVs.
        chunksize
            Number of rows per streamed pandas chunk.
        skip_existing
            Whether existing non-empty part files are treated as complete.
        continue_on_error
            Whether failed partitions should be recorded in the manifest instead
            of raising immediately.
        rename
            Optional output column rename mapping.
        """
        out_dir = Path(output_dir).expanduser().resolve()
        parts_dir = out_dir / "_parts"
        parts_dir.mkdir(parents=True, exist_ok=True)
        partitions = build_sql_partitions(
            start=start,
            end=end,
            params=params,
            frequency=frequency,
            window_days=window_days,
            param_grid=param_grid,
            derived_params=derived_params,
        )
        manifest_rows: List[Dict[str, Any]] = []
        for partition in partitions:
            context = _filename_context(partition)
            relative = _format_partition_template(part_filename, context)
            part_path = parts_dir / relative
            tmp_path = part_path.with_suffix(part_path.suffix + ".tmp")
            part_path.parent.mkdir(parents=True, exist_ok=True)
            row = dict(partition.metadata)
            row.update(
                {
                    "output_path": part_path,
                    "row_count": 0,
                    "status": "ok",
                    "message": "",
                }
            )
            if skip_existing and _file_done(part_path):
                row["status"] = "skipped"
                row["row_count"] = _csv_row_count(part_path)
                manifest_rows.append(row)
                continue
            if tmp_path.exists():
                tmp_path.unlink()
            wrote_rows = False
            total_rows = 0
            try:
                for chunk in self.query_df_stream(
                    sql,
                    params=partition.params,
                    rename=rename,
                    chunksize=chunksize,
                ):
                    if output_columns is not None:
                        missing = [col for col in output_columns if col not in chunk.columns]
                        if missing:
                            raise ValueError(f"Missing output columns: {missing}")
                        chunk = chunk[list(output_columns)]
                    chunk.to_csv(tmp_path, mode="a", header=not wrote_rows, index=False)
                    wrote_rows = True
                    total_rows += len(chunk)
                if not wrote_rows:
                    pd.DataFrame(columns=list(output_columns or [])).to_csv(tmp_path, index=False)
                tmp_path.replace(part_path)
                row["row_count"] = total_rows
            except Exception as exc:
                if tmp_path.exists():
                    tmp_path.unlink()
                row["status"] = "error"
                row["message"] = safe_error(exc)
                manifest_rows.append(row)
                task_outcome(failed=True)
                if not continue_on_error:
                    raise
                continue
            manifest_rows.append(row)
            task_outcome()

        manifest = pd.DataFrame(manifest_rows)
        if combine_by:
            _combine_partition_exports(
                manifest,
                output_dir=out_dir,
                combine_by=combine_by,
                combined_filename=combined_filename,
                output_columns=output_columns,
            )
        return manifest

    @batch_report("sql")
    def query_df_parallel(
        self,
        jobs: Sequence[Tuple[str, Optional[Dict[str, Any] | Sequence[Any]]]],
        rename: Optional[Dict[str, str]] = None,
        max_workers: Optional[int] = None,
        merge: str = "concat",
        unique_on: Optional[Sequence[str]] = None,
    ) -> pd.DataFrame:
        """Run multiple SQL queries in parallel and merge results.

        Parameters
        ----------
        jobs:
            List of (sql, params) pairs.
        rename:
            Optional mapping to rename output columns.
        max_workers:
            Number of worker processes (defaults to CPU count).
        """
        if not jobs:
            return pd.DataFrame()
        if self.log_queries:
            event(logger, "sql", "activity", level=logging.DEBUG)
        worker_args = [
            (self.config, self.connect_timeout, sql, params, rename)
            for sql, params in jobs
        ]
        try:
            with mp.Pool(processes=max_workers) as pool:
                frames = pool.map(_worker_query_df, worker_args)
            for _ in frames:
                task_outcome()
        except Exception as exc:
            error_event(logger, "sql", exc)
            raise SQLQueryError("Parallel SQL execution failed") from None
        if not frames:
            return pd.DataFrame()
        return _merge_frames(frames, merge=merge, unique_on=unique_on)

    @batch_report("sql")
    def query_df_for_keys(
        self,
        df: pd.DataFrame,
        sql: str,
        *,
        key_columns: Sequence[str],
        params: Optional[Mapping[str, Any]] = None,
        result_key_columns: Optional[Sequence[str]] = None,
        chunk_size: int = 1000,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        return_report: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """Query PostgreSQL with distinct single or composite cohort keys.

        Parameters
        ----------
        df:
            Cohort table; key values must be nonmissing scalar values.
        sql:
            SQL containing exactly one executable ``{cohort_keys}`` block
            inside an IN clause. Composite keys use ``(a, b) IN (...)``.
        key_columns:
            Ordered input key columns. Complete keys are deduplicated.
        params:
            Additional named scalar parameters; ``_fyron_key_`` is reserved.
        result_key_columns:
            Ordered output columns corresponding to the input keys. Enables
            matched/unmatched coverage; values must retain their key types.
        chunk_size:
            Maximum distinct keys per batch, reduced to fit 45,000 parameters.
        parallel:
            Execute batches in separate worker connections when true.
        max_workers:
            Worker count; defaults to four for parallel execution.
        return_report:
            Return data plus batch rows, a summary, and unmatched keys.

        Returns
        -------
        pandas.DataFrame or dict
            Database rows, or ``{data, report}`` with report DataFrames.
            Unmatched means no row returned by this query, not an absent patient.
            Any failed batch raises; partial results are never returned.
        """
        _positive_integer(chunk_size, "chunk_size")
        if max_workers is not None:
            _positive_integer(max_workers, "max_workers")
        if isinstance(key_columns, str) or not key_columns or len(set(key_columns)) != len(key_columns):
            raise ValueError("key_columns must be a nonempty sequence of unique columns.")
        keys = list(key_columns)
        if not df.columns.is_unique or any(key not in df.columns for key in keys):
            raise ValueError("Input columns must be unique and contain all key columns.")
        if df[keys].isna().any().any():
            raise ValueError("Input keys must not contain missing values.")
        tokens = _template_tokens(sql)
        if len(tokens) != 1 or tokens[0][2] != "cohort_keys" or sql[tokens[0][0]:tokens[0][1]] != "{cohort_keys}":
            raise ValueError("SQL requires exactly one executable {cohort_keys} block.")
        base = dict(params or {})
        if any(not isinstance(key, str) or key.startswith("_fyron_key_") for key in base):
            raise ValueError("Parameter names must be strings outside the reserved _fyron_key_ namespace.")
        if any(not pd.api.types.is_scalar(value) for value in base.values()):
            raise ValueError("Additional parameters must be scalar values.")
        if any(not pd.api.types.is_scalar(value) for row in df[keys].itertuples(index=False, name=None) for value in row):
            raise ValueError("Input keys must be scalar values.")
        output_keys = None
        if result_key_columns is not None:
            if isinstance(result_key_columns, str) or len(result_key_columns) != len(keys) or len(set(result_key_columns)) != len(keys):
                raise ValueError("result_key_columns must map each input key to a unique output column.")
            output_keys = list(result_key_columns)
        capacity = (45000 - len(base)) // len(keys)
        if capacity < 1:
            raise ValueError("Parameter budget cannot accommodate one complete key.")
        size = min(chunk_size, capacity)
        distinct = df[keys].drop_duplicates().reset_index(drop=True)
        jobs = []
        counts = []
        for chunk in _iter_chunks(distinct, size):
            bound = dict(base)
            groups = []
            for row_number, row in enumerate(chunk.itertuples(index=False, name=None)):
                names = [f"_fyron_key_{row_number}_{col}" for col in range(len(keys))]
                bound.update(zip(names, row))
                expression = ",".join(f"%({name})s" for name in names)
                groups.append(expression if len(keys) == 1 else f"({expression})")
            jobs.append((_safe_replace_placeholder(sql, "cohort_keys", ",".join(groups)), bound))
            counts.append(len(chunk))
        completed = []
        try:
            if parallel and jobs:
                args = [(self.config, self.connect_timeout, statement, bound, None) for statement, bound in jobs]
                with mp.Pool(processes=max_workers or 4) as pool:
                    for item in pool.imap(_timed_worker_query_df, args):
                        completed.append(item)
                        task_outcome()
            else:
                for statement, bound in jobs:
                    started = time.monotonic()
                    frame = self.query_df(statement, params=bound)
                    completed.append((frame, time.monotonic() - started))
                    task_outcome()
        except Exception as exc:
            error_event(logger, "sql", exc)
            raise SQLQueryError("Cohort SQL extraction failed; no partial result returned.") from None
        frames = [frame for frame, _ in completed]
        data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        unmatched = pd.DataFrame(columns=keys)
        matched_count = None
        if output_keys is not None:
            expected = set(distinct.itertuples(index=False, name=None))
            observed = set()
            for frame in frames:
                if not frame.columns.is_unique or any(key not in frame.columns for key in output_keys):
                    raise SQLQueryError("Result key columns are missing or ambiguous.")
                if frame[output_keys].isna().any().any():
                    raise SQLQueryError("Result keys contain missing values.")
                try:
                    observed.update(frame[output_keys].itertuples(index=False, name=None))
                except TypeError:
                    raise SQLQueryError("Result keys must be scalar values.") from None
            if not observed.issubset(expected):
                raise SQLQueryError("Result keys do not correspond to the requested cohort keys.")
            unmatched = distinct.loc[[row not in observed for row in distinct.itertuples(index=False, name=None)]].reset_index(drop=True)
            matched_count = len(observed)
        if not return_report:
            return data
        rows = pd.DataFrame([
            {"batch": i + 1, "requested_keys": counts[i], "returned_rows": len(frame),
             "elapsed_s": elapsed, "status": "completed"}
            for i, (frame, elapsed) in enumerate(completed)
        ], columns=["batch", "requested_keys", "returned_rows", "elapsed_s", "status"])
        summary = pd.DataFrame([{
            "input_rows": len(df), "distinct_keys": len(distinct),
            "duplicate_keys_removed": len(df) - len(distinct),
            "completed_batches": len(completed), "returned_rows": len(data),
            "coverage_available": output_keys is not None, "matched_keys": matched_count,
            "unmatched_keys": len(unmatched) if output_keys is not None else None,
        }])
        return {"data": data, "report": {"rows": rows, "summary": summary, "unmatched_keys": unmatched}}

    def query_from_dataframe(
        self,
        df: pd.DataFrame,
        sql: str,
        column_map: Dict[str, str],
        rename: Optional[Dict[str, str]] = None,
        param_limit: int = 50000,
        chunk_size: Optional[int] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        merge: str = "concat",
        unique_on: Optional[Sequence[str]] = None,
        param_style: str = "positional",
        param_safety_factor: float = 0.9,
    ) -> pd.DataFrame:
        """Run a query with parameters sourced from a DataFrame.

        The SQL must contain named placeholder blocks using `{name}` or `{{name}}` for each column_map key.
        Example:
        `SELECT * FROM observation WHERE patient_id IN ({patient_ids})`

        Parameters
        ----------
        df:
            Input DataFrame containing values.
        sql:
            SQL statement with `{name}` placeholder blocks.
        column_map:
            Mapping from placeholder name -> DataFrame column name.
        rename:
            Optional mapping to rename output columns.
        param_limit:
            Max number of parameters per query (Postgres limit is 65535).
        chunk_size:
            Optional explicit chunk size for splitting the DataFrame.
        parallel:
            Whether to execute chunks in parallel and merge results.
        max_workers:
            Number of worker processes when parallel is True.
        merge:
            How to merge results: "concat" or "drop_duplicates".
        unique_on:
            Columns to use for duplicate dropping when merge="drop_duplicates".
        param_style:
            "positional" (default) or "named".
        param_safety_factor:
            Fraction of param_limit used for chunk sizing (0.0-1.0).
        """
        if not df.columns.is_unique:
            raise ValueError("Input DataFrame columns must be unique.")
        if not column_map:
            raise ValueError("column_map must not be empty.")
        tokens = _template_tokens(sql)
        names = [token[2] for token in tokens]
        if set(names) != set(column_map):
            raise ValueError("SQL template blocks must match column_map.")
        for col in column_map.values():
            if col not in df.columns:
                raise ValueError("Mapped column not found in DataFrame.")
            if df[col].isnull().any():
                raise ValueError("Mapped columns contain null values.")
        if param_style not in {"positional", "named"}:
            raise ValueError("param_style must be 'positional' or 'named'.")
        _positive_integer(param_limit, "param_limit")
        if chunk_size is not None:
            _positive_integer(chunk_size, "chunk_size")
        if max_workers is not None:
            _positive_integer(max_workers, "max_workers")
        if isinstance(param_safety_factor, bool) or not math.isfinite(param_safety_factor) or not 0 < param_safety_factor <= 1:
            raise ValueError("param_safety_factor must be within (0.0, 1.0].")
        if merge not in {"concat", "drop_duplicates"}:
            raise ValueError("merge must be 'concat' or 'drop_duplicates'.")
        per_row = len(names) if param_style == "positional" else len(column_map)
        capacity = int(min(param_limit, 65535) * param_safety_factor) // per_row
        if capacity < 1:
            raise ValueError("Parameter budget cannot accommodate one input row.")
        chunk_size = min(chunk_size or capacity, capacity)
        if df.empty:
            return pd.DataFrame()

        frames: List[pd.DataFrame] = []
        if parallel:
            jobs: List[Tuple[str, Union[Sequence[Any], Dict[str, Any]]]] = []
            for chunk in _iter_chunks(df, chunk_size):
                query_sql, params = _expand_sql_placeholders(
                    sql=sql,
                    df=chunk,
                    column_map=column_map,
                    param_style=param_style,
                )
                jobs.append((query_sql, params))
            frames = [
                self.query_df_parallel(
                    jobs=jobs,
                    rename=rename,
                    max_workers=max_workers,
                    merge=merge,
                    unique_on=unique_on,
                )
            ]
        else:
            for chunk in _iter_chunks(df, chunk_size):
                query_sql, params = _expand_sql_placeholders(
                    sql=sql,
                    df=chunk,
                    column_map=column_map,
                    param_style=param_style,
                )
                frame = self.query_to_dataframe(query_sql, params=params, rename=rename)
                frames.append(frame)
        if not frames:
            return pd.DataFrame()
        return _merge_frames(frames, merge=merge, unique_on=unique_on)

    def query_df_from(
        self,
        df: pd.DataFrame,
        sql: str,
        column_map: Dict[str, str],
        rename: Optional[Dict[str, str]] = None,
        param_limit: int = 50000,
        chunk_size: Optional[int] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        merge: str = "concat",
        unique_on: Optional[Sequence[str]] = None,
        param_style: str = "positional",
        param_safety_factor: float = 0.9,
    ) -> pd.DataFrame:
        """Short alias for query_from_dataframe."""
        return self.query_from_dataframe(
            df=df,
            sql=sql,
            column_map=column_map,
            rename=rename,
            param_limit=param_limit,
            chunk_size=chunk_size,
            parallel=parallel,
            max_workers=max_workers,
            merge=merge,
            unique_on=unique_on,
            param_style=param_style,
            param_safety_factor=param_safety_factor,
        )

    def _connect(self) -> psycopg.Connection:
        """Create a database connection from config."""
        try:
            if self.config.dsn:
                conn = psycopg.connect(self.config.dsn, connect_timeout=self.connect_timeout)
            else:
                if not all([self.config.host, self.config.dbname, self.config.user]):
                    raise ValueError("Missing DB connection info. Set FHIR_DB_* env vars or pass args.")
                conn = psycopg.connect(
                    host=self.config.host,
                    port=self.config.port or 5432,
                    dbname=self.config.dbname,
                    user=self.config.user,
                    password=self.config.password,
                    sslmode=self.config.sslmode,
                    connect_timeout=self.connect_timeout,
                )
            if self.log_queries:
                event(logger, "sql", "activity", level=logging.DEBUG)
            return conn
        except Exception as exc:
            error_event(logger, "sql", exc)
            raise SQLQueryError("Failed to connect to SQL database") from None


def build_sql_partitions(
    *,
    start: Union[str, pd.Timestamp],
    end: Union[str, pd.Timestamp],
    params: Optional[Dict[str, Any]] = None,
    frequency: str = "YS",
    window_days: Optional[int] = None,
    param_grid: Optional[Mapping[str, Sequence[Any]]] = None,
    derived_params: Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]] = None,
) -> List[SQLPartition]:
    """Build SQL partitions with ``start_ts``/``end_ts`` params and metadata.

    Parameters
    ----------
    start
        Inclusive start timestamp for the first partition.
    end
        Exclusive end timestamp for the final partition.
    params
        Base SQL parameters copied into every partition.
    frequency
        Pandas date frequency used to build windows.
    window_days
        Fixed partition width in days; overrides ``frequency``.
    param_grid
        Optional categorical grid expanded across every time window.
    derived_params
        Optional callables that derive additional params from each partition.
    """
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if pd.isna(start_ts) or pd.isna(end_ts):
        raise ValueError("start and end must be valid dates.")
    if start_ts >= end_ts:
        raise ValueError("start must be earlier than end.")
    if window_days is not None:
        if window_days <= 0:
            raise ValueError("window_days must be positive.")
        boundaries = list(pd.date_range(start=start_ts, end=end_ts, freq=f"{int(window_days)}D"))
    else:
        if not frequency:
            raise ValueError("frequency is required when window_days is not set.")
        boundaries = list(pd.date_range(start=start_ts, end=end_ts, freq=frequency))
    if not boundaries or boundaries[0] != start_ts:
        boundaries.insert(0, start_ts)
    if boundaries[-1] != end_ts:
        boundaries.append(end_ts)

    base_params = dict(params or {})
    for reserved in ("start_ts", "end_ts"):
        if reserved in base_params:
            raise ValueError(f"params must not contain reserved key {reserved!r}.")

    grid = dict(param_grid or {})
    for key, values in grid.items():
        if key in {"start_ts", "end_ts"}:
            raise ValueError(f"param_grid must not contain reserved key {key!r}.")
        if not values:
            raise ValueError(f"param_grid[{key!r}] must contain at least one value.")

    grid_items = list(grid.items())
    grid_products = [()] if not grid_items else list(product(*[values for _, values in grid_items]))
    partitions: List[SQLPartition] = []
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        for values in grid_products:
            extra = {key: value for (key, _), value in zip(grid_items, values)}
            query_params = dict(base_params)
            query_params["start_ts"] = _format_sql_boundary(left)
            query_params["end_ts"] = _format_sql_boundary(right)
            query_params.update(extra)
            if derived_params:
                for key, func in derived_params.items():
                    if key in {"start_ts", "end_ts"}:
                        raise ValueError(f"derived_params must not override reserved key {key!r}.")
                    query_params[key] = func(dict(query_params))

            metadata: Dict[str, Any] = {
                "_fyron_partition_start": _format_sql_boundary(left),
                "_fyron_partition_end": _format_sql_boundary(right),
            }
            for key, value in extra.items():
                metadata[f"_fyron_partition_{key}"] = value
            partitions.append(SQLPartition(params=query_params, metadata=metadata))
    return partitions


def _iter_chunks(df: pd.DataFrame, size: int) -> Iterable[pd.DataFrame]:
    """Yield DataFrame chunks of a given size."""
    for start in range(0, len(df), size):
        yield df.iloc[start : start + size]


def _template_tokens(sql: str) -> List[Tuple[int, int, str]]:
    """Find template blocks outside PostgreSQL quoted text and comments."""
    tokens = []
    i = 0
    while i < len(sql):
        if sql.startswith("--", i):
            end = sql.find("\n", i)
            i = len(sql) if end < 0 else end + 1
        elif sql.startswith("/*", i):
            depth = 1
            i += 2
            while i < len(sql) and depth:
                if sql.startswith("/*", i):
                    depth += 1
                    i += 2
                elif sql.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("Unterminated SQL comment.")
        elif sql[i] in ("'", '"'):
            quote = sql[i]
            escaped = quote == "'" and i > 0 and sql[i - 1] in "eE" and (i < 2 or not (sql[i - 2].isalnum() or sql[i - 2] == "_"))
            i += 1
            while i < len(sql):
                if escaped and sql[i] == "\\":
                    i += 2
                elif sql[i] == quote:
                    i += 1
                    if i < len(sql) and sql[i] == quote:
                        i += 1
                    else:
                        break
                else:
                    i += 1
            else:
                raise ValueError("Unterminated SQL quoted text.")
        elif sql[i] == "$" and (match := re.match(r"\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$", sql[i:])):
            delimiter = match.group()
            end = sql.find(delimiter, i + len(delimiter))
            if end < 0:
                raise ValueError("Unterminated SQL dollar-quoted text.")
            i = end + len(delimiter)
        elif sql[i] == "{" and (match := re.match(r"\{\{([A-Za-z_][A-Za-z_0-9]*)\}\}|\{([A-Za-z_][A-Za-z_0-9]*)\}", sql[i:])):
            tokens.append((i, i + len(match.group()), match.group(1) or match.group(2)))
            i += len(match.group())
        else:
            i += 1
    return tokens


def _positive_integer(value: Any, label: str) -> None:
    """Validate integer execution limits before submitting work."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer.")


def _expand_sql_placeholders(
    sql: str,
    df: pd.DataFrame,
    column_map: Dict[str, str],
    param_style: str = "positional",
) -> Tuple[str, Union[List[Any], Dict[str, Any]]]:
    """Bind list values in SQL occurrence order, including repeated blocks."""
    params_list: List[Any] = []
    params_named: Dict[str, Any] = {}
    pieces = []
    last = 0
    for start, end, name in _template_tokens(sql):
        if name not in column_map:
            raise ValueError("SQL contains an unmapped template block.")
        values = df[column_map[name]].tolist()
        if param_style == "named":
            keys = [f"{name}_{i}" for i in range(len(values))]
            replacement = ",".join(f"%({key})s" for key in keys)
            params_named.update(zip(keys, values))
        else:
            replacement = ",".join("%s" for _ in values)
            params_list.extend(values)
        pieces.extend([sql[last:start], replacement])
        last = end
    pieces.append(sql[last:])
    return "".join(pieces), params_named if param_style == "named" else params_list


def _maybe_int(value: Optional[str]) -> Optional[int]:
    """Parse an optional int from string."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _format_sql_boundary(value: pd.Timestamp) -> str:
    """Format a SQL partition timestamp as an ISO-like string."""
    if value.hour == 0 and value.minute == 0 and value.second == 0 and value.microsecond == 0:
        return value.strftime("%Y-%m-%d")
    return value.isoformat()


def _safe_filename_value(value: Any) -> str:
    text = str(value)
    text = re.sub(r"[^A-Za-z0-9_.=-]+", "_", text)
    return text.strip("_") or "value"


def _filename_context(partition: SQLPartition) -> Dict[str, Any]:
    start = pd.Timestamp(partition.params["start_ts"])
    context: Dict[str, Any] = {
        "start": _safe_filename_value(partition.params["start_ts"]),
        "end": _safe_filename_value(partition.params["end_ts"]),
        "date": start.strftime("%Y-%m-%d"),
        "year": start.strftime("%Y"),
        "month": start.strftime("%m"),
        "day": start.strftime("%d"),
    }
    for key, value in partition.params.items():
        if key in {"start_ts", "end_ts"}:
            continue
        context[key] = _safe_filename_value(value)
    return context


def _format_partition_template(template: str, context: Mapping[str, Any]) -> Path:
    """Format a partition filename and reject parent-directory traversal."""
    rendered = template.format(**context)
    path = Path(rendered)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Partition filename templates must be relative and stay inside output_dir.")
    return path


def _file_done(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _csv_row_count(path: Path) -> int:
    if not _file_done(path):
        return 0
    count = 0
    for chunk in pd.read_csv(path, chunksize=50000):
        count += len(chunk)
    return count


def _combine_partition_exports(
    manifest: pd.DataFrame,
    *,
    output_dir: Path,
    combine_by: str,
    combined_filename: str,
    output_columns: Optional[Sequence[str]],
) -> None:
    """Combine successful part files by one manifest metadata group."""
    column = f"_fyron_partition_{combine_by}"
    if combine_by in {"year", "month", "day", "date"}:
        starts = pd.to_datetime(manifest["_fyron_partition_start"], errors="coerce")
        if combine_by == "year":
            manifest = manifest.assign(_fyron_partition_year=starts.dt.strftime("%Y"))
        elif combine_by == "month":
            manifest = manifest.assign(_fyron_partition_month=starts.dt.strftime("%m"))
        elif combine_by == "day":
            manifest = manifest.assign(_fyron_partition_day=starts.dt.strftime("%d"))
        elif combine_by == "date":
            manifest = manifest.assign(_fyron_partition_date=starts.dt.strftime("%Y-%m-%d"))
    if column not in manifest.columns:
        raise ValueError(f"Cannot combine by {combine_by!r}; manifest column {column!r} is missing.")
    successful = manifest[manifest["status"].isin(["ok", "skipped"])].copy()
    for value, group in successful.groupby(column, dropna=False):
        safe_value = _safe_filename_value(value)
        context = {
            "value": safe_value,
            "year": safe_value,
            "month": safe_value,
            "day": safe_value,
            "date": safe_value,
            combine_by: safe_value,
        }
        filename = combined_filename.format(**context)
        output_path = output_dir / filename
        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if tmp_path.exists():
            tmp_path.unlink()
        wrote_rows = False
        for part_path in group["output_path"]:
            path = Path(part_path)
            if not _file_done(path):
                continue
            for chunk in pd.read_csv(path, chunksize=50000):
                if output_columns is not None:
                    chunk = chunk[list(output_columns)]
                chunk.to_csv(tmp_path, mode="a", header=not wrote_rows, index=False)
                wrote_rows = True
        if not wrote_rows:
            pd.DataFrame(columns=list(output_columns or [])).to_csv(tmp_path, index=False)
        tmp_path.replace(output_path)


def _timed_worker_query_df(args):
    """Execute one owned worker query and record its elapsed time."""
    started = time.monotonic()
    return _worker_query_df(args), time.monotonic() - started


def _worker_query_df(
    args: Tuple[SQLConfig, int, str, Optional[Dict[str, Any] | Sequence[Any]], Optional[Dict[str, str]]]
) -> pd.DataFrame:
    """Worker helper for parallel SQL queries."""
    config, connect_timeout, sql, params, rename = args
    conn = _connect_from_config(config, connect_timeout)
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        if rename:
            df = df.rename(columns=rename)
        return df
    except Exception as exc:
        raise SQLQueryError("Parallel SQL query failed") from None
    finally:
        conn.close()


def _connect_from_config(config: SQLConfig, connect_timeout: int) -> "psycopg.Connection":
    """Connect to Postgres using a SQLConfig."""
    if config.dsn:
        return psycopg.connect(config.dsn, connect_timeout=connect_timeout)  # type: ignore[union-attr]
    if not all([config.host, config.dbname, config.user]):
        raise ValueError("Missing DB connection info. Set FHIR_DB_* env vars or pass args.")
    return psycopg.connect(  # type: ignore[union-attr]
        host=config.host,
        port=config.port or 5432,
        dbname=config.dbname,
        user=config.user,
        password=config.password,
        sslmode=config.sslmode,
        connect_timeout=connect_timeout,
    )


def _safe_replace_placeholder(sql: str, name: str, replacement: str) -> str:
    """Replace {name} or {{name}} placeholders safely."""
    matches = [token for token in _template_tokens(sql) if token[2] == name]
    if not matches:
        raise ValueError("Missing executable SQL template block.")
    for start, end, _ in reversed(matches):
        sql = sql[:start] + replacement + sql[end:]
    return sql


def _merge_frames(
    frames: Sequence[pd.DataFrame],
    merge: str = "concat",
    unique_on: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Merge a list of DataFrames with optional deduplication."""
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    if merge == "drop_duplicates":
        return df.drop_duplicates(subset=list(unique_on) if unique_on else None).reset_index(drop=True)
    if merge != "concat":
        raise ValueError("merge must be 'concat' or 'drop_duplicates'.")
    return df
