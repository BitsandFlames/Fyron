"""Explicit elapsed-time contracts without optional dependencies."""

import pandas as pd


def time_unit_factor(unit):
    factors = {"days": 1.0, "weeks": 7.0, "months": 30.4375, "years": 365.25}
    if unit not in factors:
        raise ValueError("time_unit must be one of 'days', 'weeks', 'months', or 'years'.")
    return factors[unit]


def align_dates(*values):
    """Broadcast scalars; never silently align distinct Series indices."""
    series = [value for value in values if isinstance(value, pd.Series)]
    vectors = [value for value in values if not pd.api.types.is_scalar(value)]
    index = series[0].index if series else pd.RangeIndex(len(vectors[0]) if vectors else 1)
    for value in series:
        if not value.index.equals(index):
            raise ValueError("Date Series must have identical indices and order.")
    result = []
    for value in values:
        if pd.api.types.is_scalar(value):
            result.append(pd.Series(value, index=index))
        else:
            if len(value) != len(index):
                raise ValueError("Date vectors must have equal lengths.")
            result.append(pd.Series(list(value), index=index))
    return result


def parse_dates(*values, errors="coerce"):
    """Return aligned timestamps and distinguish absent from malformed values."""
    if errors not in {"coerce", "raise"}:
        raise ValueError("errors must be 'coerce' or 'raise'.")
    inputs = align_dates(*values)
    parsed, invalid, awareness = [], [], set()
    for source in inputs:
        timestamps, bad = [], []
        for value in source:
            missing = pd.isna(value)
            try:
                timestamp = pd.NaT if missing else pd.Timestamp(value)
                if not pd.isna(timestamp):
                    timestamp = timestamp.as_unit("ns")
            except (ValueError, TypeError, OverflowError):
                timestamp = pd.NaT
            malformed = not missing and pd.isna(timestamp)
            if malformed and errors == "raise":
                raise ValueError("Date input contains invalid dates.") from None
            if not pd.isna(timestamp):
                awareness.add(timestamp.tzinfo is not None)
            timestamps.append(timestamp)
            bad.append(malformed)
        parsed.append(timestamps)
        invalid.append(pd.Series(bad, index=source.index, dtype=bool))
    if len(awareness) > 1:
        raise ValueError("Cannot mix timezone-naive and timezone-aware dates.")
    aware = True in awareness
    result = [pd.Series(pd.to_datetime(items, utc=aware), index=source.index)
              for items, source in zip(parsed, inputs)]
    return result, invalid


def date_difference(start, end, *, unit="days", errors="coerce"):
    factor = time_unit_factor(unit)
    (start, end), _ = parse_dates(start, end, errors=errors)
    return ((end - start).dt.total_seconds() / 86400.0 / factor).astype(float)
