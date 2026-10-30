"""Shared clinical code parsing utilities."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Sequence
from typing import Any

import pandas as pd


def normalize_code(
    value: Any,
    *,
    uppercase: bool = True,
    remove_spaces: bool = True,
    remove_dots: bool = False,
) -> str | None:
    """Normalize one clinical code value for matching.

    Parameters
    ----------
    value
        Raw code value such as an ICD-10, OPS, medication, or local registry code.
    uppercase
        If True, convert the returned code to uppercase.
    remove_spaces
        If True, remove whitespace within the code.
    remove_dots
        If True, remove dots from the code.

    Returns
    -------
    str or None
        Normalized code string, or None for missing/empty values.
    """

    if _is_missing(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    if remove_spaces:
        text = re.sub(r"\s+", "", text)
    if remove_dots:
        text = text.replace(".", "")
    if uppercase:
        text = text.upper()
    return text or None


def split_code_string(value: Any, *, sep: str = ";", normalize: bool = True) -> list[str]:
    """Split one cell containing one or more clinical codes.

    Parameters
    ----------
    value
        Scalar value containing one or more codes, usually separated by semicolons.
    sep
        Delimiter used between codes.
    normalize
        If True, normalize each code with :func:`normalize_code`.

    Returns
    -------
    list[str]
        Ordered list of non-empty codes.
    """

    if _is_missing(value):
        return []
    codes: list[str] = []
    for part in str(value).split(sep):
        code = normalize_code(part) if normalize else str(part).strip()
        if code:
            codes.append(code)
    return codes


def _split_code_values(value: Any, *, separators: str = r"[,;|\s]+", normalize: bool = True) -> list[str]:
    """Parse scalar or iterable code values into a clean code list.

    Parameters
    ----------
    value
        Missing value, scalar code, delimited string, Python-style list string,
        or iterable of code values.
    separators
        Regular expression used to split ordinary strings.
    normalize
        If True, normalize parsed codes with :func:`normalize_code`.

    Returns
    -------
    list[str]
        Parsed non-empty codes in source order.
    """

    if _is_missing(value):
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                parsed = None
            if isinstance(parsed, list):
                return _clean_code_iterable(parsed, normalize=normalize)
        return _clean_code_iterable(re.split(separators, text), normalize=normalize)
    if isinstance(value, Iterable):
        return _clean_code_iterable(value, normalize=normalize)
    code = normalize_code(value) if normalize else str(value).strip()
    return [code] if code else []


def explode_code_column(
    df: pd.DataFrame,
    code_col: str,
    *,
    sep: str = ";",
    output_col: str = "code",
    keep_empty: bool = False,
) -> pd.DataFrame:
    """Explode a delimited clinical code column into one row per code.

    Parameters
    ----------
    df
        DataFrame containing a delimited code column.
    code_col
        Column with one or more codes per row.
    sep
        Delimiter between codes.
    output_col
        Name of the exploded output code column.
    keep_empty
        If True, keep rows without codes and set ``output_col`` to missing.

    Returns
    -------
    pandas.DataFrame
        Exploded DataFrame with one row per parsed code.
    """

    _require_columns(df, [code_col])
    rows: list[pd.Series] = []
    for _, row in df.iterrows():
        codes = split_code_string(row[code_col], sep=sep)
        if not codes and keep_empty:
            new_row = row.copy()
            new_row[output_col] = pd.NA
            rows.append(new_row)
        for code in codes:
            new_row = row.copy()
            new_row[output_col] = code
            rows.append(new_row)
    if not rows:
        columns = list(df.columns)
        if output_col not in columns:
            columns.append(output_col)
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).reset_index(drop=True)


def aggregate_code_rows(
    df: pd.DataFrame,
    group_cols: str | Sequence[str],
    code_col: str,
    *,
    display_col: str | None = None,
    date_col: str | None = None,
    code_list_col: str | None = None,
    display_list_col: str | None = None,
    first_date_col: str | None = None,
    last_date_col: str | None = None,
    count_col: str | None = None,
    complete_groups: pd.DataFrame | None = None,
    sort_items: bool = True,
    unique: bool = True,
    strip_strings: bool = True,
) -> pd.DataFrame:
    """Aggregate one-code-per-row data into list-valued group rows.

    Parameters
    ----------
    df
        Long DataFrame with one clinical code per row.
    group_cols
        Column or columns defining the output row, such as patient and
        encounter identifiers.
    code_col
        Source column containing the clinical code.
    display_col
        Optional source column containing code display text.
    date_col
        Optional date column used for first/last date outputs and sorting.
    code_list_col
        Output column for code lists. Defaults to ``f"{code_col}_list"``.
    display_list_col
        Output column for display text lists. Defaults to
        ``f"{display_col}_list"`` when ``display_col`` is provided.
    first_date_col
        Output column for the earliest date. Defaults to
        ``f"{date_col}_first"`` when ``date_col`` is provided.
    last_date_col
        Output column for the latest date. Defaults to
        ``f"{date_col}_last"`` when ``date_col`` is provided.
    count_col
        Output column for the number of distinct codes. Defaults to
        ``f"n_{code_col}s"``.
    complete_groups
        Optional DataFrame with all desired output groups. Groups with no
        codes are retained with empty lists, missing dates, and a zero count.
    sort_items
        If True, list outputs are sorted for stable CSV/JSON artifacts.
    unique
        If True, each code/display appears once per output group.
    strip_strings
        If True, trim whitespace from string-like group, code, and display
        columns before aggregation.

    Returns
    -------
    pandas.DataFrame
        One row per group with list-valued code/display columns, optional
        first/last dates, and a code count.
    """

    groups = _as_column_list(group_cols)
    required = [*groups, code_col]
    if display_col is not None:
        required.append(display_col)
    if date_col is not None:
        required.append(date_col)
    _require_columns(df, required)

    code_list_col = code_list_col or f"{code_col}_list"
    display_list_col = display_list_col or (f"{display_col}_list" if display_col is not None else None)
    first_date_col = first_date_col or (f"{date_col}_first" if date_col is not None else None)
    last_date_col = last_date_col or (f"{date_col}_last" if date_col is not None else None)
    count_col = count_col or f"n_{code_col}s"

    columns = list(dict.fromkeys(required))
    data = df[columns].copy()
    if strip_strings:
        _strip_columns(data, [*groups, code_col, *([display_col] if display_col else [])])
    data = data.dropna(subset=groups)
    data = data[_valid_code_mask(data[code_col])].copy()
    if date_col is not None:
        data[date_col] = pd.to_datetime(data[date_col], utc=True, errors="coerce")

    output_columns = _aggregate_output_columns(
        groups,
        code_list_col,
        display_list_col=display_list_col,
        first_date_col=first_date_col,
        last_date_col=last_date_col,
        count_col=count_col,
    )
    if data.empty:
        aggregated = pd.DataFrame(columns=output_columns)
        return _complete_aggregated_groups(
            aggregated,
            complete_groups,
            groups,
            list_cols=[col for col in [code_list_col, display_list_col] if col is not None],
            date_cols=[col for col in [first_date_col, last_date_col] if col is not None],
            count_col=count_col,
            strip_strings=strip_strings,
        )

    sort_columns = [*groups, *([date_col] if date_col is not None else []), code_col]
    data = data.sort_values(sort_columns, na_position="last")
    agg_kwargs: dict[str, Any] = {
        code_list_col: (code_col, lambda values: _list_values(values, unique=unique, sort_items=sort_items)),
        count_col: (code_col, lambda values: int(pd.Series(_list_values(values, unique=True, sort_items=False)).nunique())),
    }
    if display_col is not None and display_list_col is not None:
        agg_kwargs[display_list_col] = (display_col, lambda values: _list_values(values, unique=unique, sort_items=sort_items))
    if date_col is not None and first_date_col is not None and last_date_col is not None:
        agg_kwargs[first_date_col] = (date_col, "min")
        agg_kwargs[last_date_col] = (date_col, "max")

    aggregated = data.groupby(groups, dropna=False).agg(**agg_kwargs).reset_index()
    return _complete_aggregated_groups(
        aggregated,
        complete_groups,
        groups,
        list_cols=[col for col in [code_list_col, display_list_col] if col is not None],
        date_cols=[col for col in [first_date_col, last_date_col] if col is not None],
        count_col=count_col,
        strip_strings=strip_strings,
    )


def _indicator_prevalence(
    df: pd.DataFrame,
    *,
    group_cols: Sequence[str] | None,
    prefix: str,
    label_col: str,
) -> pd.DataFrame:
    """Summarize binary indicator columns with counts and percentages."""

    cols = list(group_cols or [col for col in df.columns if col.startswith(prefix)])
    if not cols:
        raise ValueError(f"No indicator columns found with prefix {prefix!r}.")
    _require_columns(df, cols)
    denom = len(df)
    rows = []
    for col in cols:
        n = int(pd.to_numeric(df[col], errors="coerce").fillna(0).astype(bool).sum())
        rows.append(
            {
                label_col: col.removeprefix(prefix),
                "column": col,
                "n_patients": n,
                "percent": round(100 * n / denom, 1) if denom else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("n_patients", ascending=False).reset_index(drop=True)


def _slug(value: str) -> str:
    """Create a stable snake-case column suffix from a display label."""

    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def _require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    """Raise a clear error when a DataFrame is missing required columns."""

    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _clean_code_iterable(values: Iterable[Any], *, normalize: bool) -> list[str]:
    codes = []
    for value in values:
        code = normalize_code(value) if normalize else str(value).strip()
        if code:
            codes.append(code)
    return codes


def _as_column_list(columns: str | Sequence[str]) -> list[str]:
    if isinstance(columns, str):
        return [columns]
    result = list(columns)
    if not result:
        raise ValueError("group_cols must contain at least one column.")
    return result


def _strip_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        df[column] = df[column].map(lambda value: value.strip() if isinstance(value, str) else value)


def _valid_code_mask(values: pd.Series) -> pd.Series:
    text = values.astype("string").str.strip()
    return text.notna() & text.ne("") & text.str.lower().ne("nan") & text.str.lower().ne("none")


def _list_values(values: Iterable[Any], *, unique: bool, sort_items: bool) -> list[str]:
    cleaned = []
    for value in values:
        if _is_missing(value):
            continue
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "<na>"}:
            continue
        cleaned.append(text)
    if unique:
        cleaned = list(dict.fromkeys(cleaned))
    if sort_items:
        cleaned = sorted(cleaned)
    return cleaned


def _aggregate_output_columns(
    groups: Sequence[str],
    code_list_col: str,
    *,
    display_list_col: str | None,
    first_date_col: str | None,
    last_date_col: str | None,
    count_col: str,
) -> list[str]:
    return [
        *groups,
        code_list_col,
        *([display_list_col] if display_list_col is not None else []),
        *([first_date_col, last_date_col] if first_date_col is not None and last_date_col is not None else []),
        count_col,
    ]


def _complete_aggregated_groups(
    aggregated: pd.DataFrame,
    complete_groups: pd.DataFrame | None,
    group_cols: Sequence[str],
    *,
    list_cols: Sequence[str],
    date_cols: Sequence[str],
    count_col: str,
    strip_strings: bool,
) -> pd.DataFrame:
    if complete_groups is None:
        return aggregated
    _require_columns(complete_groups, group_cols)
    complete = complete_groups[list(group_cols)].dropna(subset=list(group_cols)).copy()
    if strip_strings:
        _strip_columns(complete, group_cols)
    complete = complete.drop_duplicates(subset=list(group_cols), keep="first")
    result = complete.merge(aggregated, on=list(group_cols), how="left", validate="one_to_one")
    for column in list_cols:
        if column not in result.columns:
            result[column] = pd.NA
        result[column] = result[column].apply(lambda value: value if isinstance(value, list) else [])
    for column in date_cols:
        if column not in result.columns:
            result[column] = pd.NaT
        result[column] = pd.to_datetime(result[column], utc=True, errors="coerce")
    result[count_col] = pd.to_numeric(result.get(count_col), errors="coerce").fillna(0).astype(int)
    return result


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    if isinstance(missing, bool):
        return missing
    try:
        return bool(missing)
    except (TypeError, ValueError):
        return False
