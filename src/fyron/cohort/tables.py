"""Join and validate patient-level cohort tables."""

from __future__ import annotations

from typing import Literal, Sequence

import pandas as pd
from fyron._survival_data import duration_column, event_column
from fyron._dates import date_difference, time_unit_factor
from ._endpoints import endpoint_rows, validate_output_names

TimeUnit = Literal["days", "weeks", "months", "years"]


def join_cohort_tables(
    features: pd.DataFrame,
    outcomes: pd.DataFrame,
    *,
    on: str = "patient_id",
    how: str = "inner",
    validate: str = "one_to_one",
) -> pd.DataFrame:
    """Join feature and outcome tables on a patient identifier.

    Parameters
    ----------
    features
        Patient-level predictors (must include ``on``).
    outcomes
        Patient-level outcomes (must include ``on``).
    on
        Join key column name.
    how
        Merge strategy passed to :meth:`pandas.DataFrame.merge`.
    validate
        Merge validation (e.g. ``one_to_one``) to catch duplicate keys.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.cohort import join_cohort_tables
    >>> f = pd.DataFrame({"patient_id": ["p1", "p2"], "age": [50, 60]})
    >>> o = pd.DataFrame({"patient_id": ["p1", "p2"], "event": [1, 0]})
    >>> join_cohort_tables(f, o).shape[0]
    2
    """
    if on not in features.columns:
        raise ValueError(f"Join key {on!r} not in features.")
    if on not in outcomes.columns:
        raise ValueError(f"Join key {on!r} not in outcomes.")
    if features[on].isna().any() or outcomes[on].isna().any():
        raise ValueError(f"Join key {on!r} contains missing identifiers.")
    return features.merge(outcomes, on=on, how=how, validate=validate)


def validate_cohort_table(
    df: pd.DataFrame,
    *,
    required_columns: Sequence[str],
    id_column: str | None = "patient_id",
    allow_duplicate_ids: bool = False,
) -> pd.DataFrame:
    """Validate a cohort DataFrame for analysis-ready use.

    Returns the input frame unchanged when validation passes.

    Parameters
    ----------
    df
        Cohort table with one row per patient, lesion, study, or other declared
        analysis unit.
    required_columns
        Column names that must be present before the cohort can be used
        downstream.
    id_column
        Optional identifier column used to detect missing or duplicate analysis
        units. Pass ``None`` to skip identifier checks.
    allow_duplicate_ids
        If False, duplicate values in ``id_column`` raise a ``ValueError``.

    Returns
    -------
    pandas.DataFrame
        The original input DataFrame, unchanged, when all validation checks pass.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.cohort import validate_cohort_table
    >>> df = pd.DataFrame({"patient_id": ["a"], "time": [1.0], "event": [1]})
    >>> validate_cohort_table(df, required_columns=["time", "event"]).equals(df)
    True
    """
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if df.empty:
        raise ValueError("Cohort table is empty.")
    if id_column is not None:
        if id_column not in df.columns:
            raise ValueError(f"id_column {id_column!r} not in dataframe.")
        if df[id_column].isna().any():
            raise ValueError(f"Missing identifiers in {id_column!r}.")
        if not allow_duplicate_ids and df[id_column].duplicated().any():
            raise ValueError(f"Duplicate values in {id_column!r}.")
    return df


def build_survival_columns(
    df: pd.DataFrame,
    *,
    start_col: str,
    end_col: str,
    event_col: str,
    time_col: str = "time",
    event_out_col: str = "event",
) -> pd.DataFrame:
    """Build standard survival ``time`` and ``event`` columns from date fields.

    ``time`` is ``end - start`` in days when columns are datetimes; numeric
    columns are subtracted directly.

    Parameters
    ----------
    df
        Cohort table containing start, end, and event columns.
    start_col
        Baseline or index-date column where follow-up begins.
    end_col
        Endpoint or censoring column where follow-up ends.
    event_col
        Existing column indicating whether the event occurred.
    time_col
        Name of the output duration column.
    event_out_col
        Name of the output event-indicator column.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with duration and event columns appended. Negative
        durations raise a ``ValueError``.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.cohort import build_survival_columns
    >>> df = pd.DataFrame({
    ...     "start": pd.to_datetime(["2020-01-01", "2020-01-01"]),
    ...     "end": pd.to_datetime(["2020-06-01", "2020-03-01"]),
    ...     "died": [1, 0],
    ... })
    >>> out = build_survival_columns(df, start_col="start", end_col="end", event_col="died")
    >>> "time" in out.columns and "event" in out.columns
    True
    """
    _require_columns(df, [start_col, end_col, event_col])
    validate_output_names([time_col, event_out_col], [start_col, end_col])
    if time_col == event_col:
        raise ValueError("Duration output must not overwrite the input event column.")
    out = df.copy()
    start = out[start_col]
    end = out[end_col]
    if pd.api.types.is_datetime64_any_dtype(start) and pd.api.types.is_datetime64_any_dtype(end):
        delta = date_difference(start, end, errors="raise")
    else:
        delta = end - start
    out[time_col] = delta.astype(float)
    out[event_out_col] = out[event_col]
    if (out[time_col] < 0).any():
        raise ValueError("Negative survival times computed; check start/end columns.")
    duration_column(out[time_col].dropna(), name=time_col)
    event_column(out[event_out_col].dropna(), name=event_out_col)
    return out


def build_time_to_event_endpoint(
    df: pd.DataFrame,
    *,
    index_date_col: str,
    event_date_col: str,
    censor_date_col: str,
    time_col: str = "time",
    event_col: str = "event",
    endpoint_date_col: str = "endpoint_date",
    endpoint_source_col: str = "endpoint_source",
    time_unit: TimeUnit = "days",
    require_endpoint: bool = True,
    administrative_censor_date=None,
) -> pd.DataFrame:
    """Build time-to-event columns from index, event, and censor dates.

    Parameters
    ----------
    df
        Cohort table with one row per patient or analysis unit.
    index_date_col
        Start date for follow-up, such as diagnosis, baseline CT, or treatment start.
    event_date_col
        Date of the event of interest. Missing values are treated as censored.
    censor_date_col
        Last known follow-up or administrative censoring date.
    time_col
        Name of the output follow-up duration column.
    event_col
        Name of the output binary event-indicator column.
    endpoint_date_col
        Name of the output column storing the selected event or censoring date.
    endpoint_source_col
        Name of the output column storing ``"event"``, ``"censor"``, or
        ``"missing"``.
    time_unit
        Unit for the computed follow-up time: ``"days"``, ``"weeks"``, ``"months"``, or ``"years"``.
    require_endpoint
        If True, rows with neither an event nor a censor date raise an error.
        If False, unresolved rows retain missing time, event=0, and source
        ``missing``; they are not valid observed censoring.
    administrative_censor_date
        Optional scalar date limiting an otherwise available endpoint. Cannot
        manufacture missing follow-up. Events exactly on the cutoff count as
        events. Timezone-aware dates are normalized to UTC; mixing aware and
        naive nonmissing dates raises.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with time, event, endpoint date, and endpoint source columns.

    Raises
    ------
    ValueError
        Raised for missing required columns, invalid index dates, missing endpoint
        dates when ``require_endpoint=True``, invalid time units, or negative
        follow-up times.
    """

    _require_columns(df, [index_date_col, event_date_col, censor_date_col])
    validate_output_names(
        [time_col, event_col, endpoint_date_col, endpoint_source_col],
        [index_date_col, event_date_col, censor_date_col],
    )
    out = df.copy()
    rows = endpoint_rows(out, index_date_col, event_date_col, censor_date_col,
                         time_unit, administrative_censor_date)["rows"]
    if rows[["invalid_index_date", "invalid_event_date", "invalid_censor_date",
             "missing_index_date"]].any().any():
        raise ValueError("Endpoint inputs contain missing index dates or invalid dates.")
    if require_endpoint and rows.missing_endpoint.any():
        raise ValueError("At least one row has neither an event date nor a censor date.")
    if rows.negative_followup.any() or rows.cutoff_before_index.any():
        raise ValueError("Negative endpoint times computed; check index/event/censor dates.")
    out[time_col] = rows["time"].astype(float)
    out[event_col] = rows["event"]
    out[endpoint_date_col] = rows["endpoint_date"]
    out[endpoint_source_col] = rows["endpoint_source"]
    return out


def audit_time_to_event_endpoint(
    df: pd.DataFrame,
    *,
    index_date_col: str,
    event_date_col: str,
    censor_date_col: str,
    time_unit: TimeUnit = "days",
    administrative_censor_date=None,
) -> dict[str, pd.DataFrame]:
    """Inspect endpoint decisions without dropping or repairing any rows.

    Parameters
    ----------
    df
        One row per analysis unit. Original indices and ordering are retained.
    index_date_col, event_date_col, censor_date_col
        Baseline, event, and last-follow-up date columns.
    time_unit
        Elapsed days, weeks, months (30.4375 days), or years (365.25 days).
    administrative_censor_date
        Optional scalar cutoff; cannot create otherwise missing follow-up.

    Returns
    -------
    dict
        ``rows`` contains tentative time/event/endpoint decisions and boolean
        quality flags. Use ``valid_endpoint`` or ``positive_duration_eligible``
        before interpreting outcomes. ``summary`` contains metric, count, and
        severity columns. Flags may overlap; counts are not additive exclusions.

    Notes
    -----
    Malformed values are flagged, not raised. Structural problems such as missing
    columns, mixed naive/aware dates, or an invalid cutoff still raise. Missing
    endpoints are never counted as valid censoring. Row-level output is sensitive.
    """
    _require_columns(df, [index_date_col, event_date_col, censor_date_col])
    return endpoint_rows(df, index_date_col, event_date_col, censor_date_col,
                         time_unit, administrative_censor_date)


def audit_cohort_join(
    features: pd.DataFrame, outcomes: pd.DataFrame, *, on: str = "patient_id",
) -> pd.DataFrame:
    """Report key coverage and hypothetical pandas merge sizes without joining rows.

    Parameters
    ----------
    features, outcomes
        Research tables to inspect. Neither table is modified.
    on
        Shared identifier column, as in ``join_cohort_tables``.

    Returns
    -------
    pandas.DataFrame
        ``metric`` and integer ``count`` columns. Key and duplicate counts refer
        to nonmissing keys; missing rows are reported separately. Expected join
        sizes include pandas' null-to-null matching, but ``join_cohort_tables``
        deliberately rejects missing keys. No identifiers are returned or logged.
    """
    _require_columns(features, [on])
    _require_columns(outcomes, [on])
    left, right = features[on], outcomes[on]
    left_counts = left.dropna().value_counts()
    right_counts = right.dropna().value_counts()
    counts = pd.concat([left_counts.rename("left"), right_counts.rename("right")], axis=1).fillna(0)
    matched = (counts.left > 0) & (counts.right > 0)
    left_only = (counts.left > 0) & (counts.right == 0)
    right_only = (counts.right > 0) & (counts.left == 0)
    missing_left, missing_right = int(left.isna().sum()), int(right.isna().sum())
    inner = sum(int(a) * int(b) for a, b in counts.itertuples(index=False, name=None))
    inner += missing_left * missing_right
    unmatched_left = int(counts.loc[left_only, "left"].sum()) + (missing_left if not missing_right else 0)
    unmatched_right = int(counts.loc[right_only, "right"].sum()) + (missing_right if not missing_left else 0)
    metrics = {
        "features.rows": len(left), "outcomes.rows": len(right),
        "features.missing_key_rows": missing_left, "outcomes.missing_key_rows": missing_right,
        "features.duplicate_key_rows": int(left.dropna().duplicated(keep=False).sum()),
        "outcomes.duplicate_key_rows": int(right.dropna().duplicated(keep=False).sum()),
        "matched_keys": int(matched.sum()), "features.unmatched_keys": int(left_only.sum()),
        "outcomes.unmatched_keys": int(right_only.sum()),
        "features.matched_rows": int(counts.loc[matched, "left"].sum()),
        "outcomes.matched_rows": int(counts.loc[matched, "right"].sum()),
        "features.unmatched_nonmissing_rows": int(counts.loc[left_only, "left"].sum()),
        "outcomes.unmatched_nonmissing_rows": int(counts.loc[right_only, "right"].sum()),
        "expected.inner_rows": inner, "expected.left_rows": inner + unmatched_left,
        "expected.right_rows": inner + unmatched_right,
        "expected.outer_rows": inner + unmatched_left + unmatched_right,
    }
    return pd.DataFrame([{"metric": key, "count": value} for key, value in metrics.items()])


def cohort_profile(
    df: pd.DataFrame,
    *,
    id_col: str = "patient_id",
    endpoint_cols: Sequence[str] | None = None,
    group_col: str | None = None,
) -> pd.DataFrame:
    """Create a compact audit table for a patient-level cohort.

    Parameters
    ----------
    df
        Cohort table to profile.
    id_col
        Patient or analysis-unit identifier.
    endpoint_cols
        Optional binary or numeric endpoint columns to summarize.
    group_col
        Optional subgroup column for distribution checks.

    Returns
    -------
    pandas.DataFrame
        Rows named by ``metric`` with values useful for cohort review.
    """

    _require_columns(df, [id_col] + list(endpoint_cols or []) + ([group_col] if group_col else []))
    rows: list[dict[str, object]] = [
        {"metric": "rows", "value": int(len(df))},
        {"metric": "unique_ids", "value": int(df[id_col].nunique(dropna=True))},
        {"metric": "missing_ids", "value": int(df[id_col].isna().sum())},
        {"metric": "duplicate_id_rows", "value": int(df[id_col].duplicated(keep=False).sum())},
        {"metric": "columns", "value": int(df.shape[1])},
    ]
    for col in endpoint_cols or []:
        series = pd.to_numeric(df[col], errors="coerce")
        rows.extend(
            [
                {"metric": f"{col}.missing", "value": int(series.isna().sum())},
                {"metric": f"{col}.non_missing", "value": int(series.notna().sum())},
                {"metric": f"{col}.sum", "value": float(series.sum(skipna=True))},
                {"metric": f"{col}.mean", "value": float(series.mean()) if series.notna().any() else float("nan")},
            ]
        )
    if group_col is not None:
        counts = df[group_col].value_counts(dropna=False)
        for group, count in counts.items():
            label = "<missing>" if pd.isna(group) else str(group)
            rows.append({"metric": f"{group_col}.{label}.n", "value": int(count)})
    return pd.DataFrame(rows)


def _time_unit_factor(unit: TimeUnit) -> float:
    return time_unit_factor(unit)


def _require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
