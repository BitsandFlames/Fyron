"""Shared endpoint decisions for construction and review."""

import pandas as pd

from fyron._dates import parse_dates, time_unit_factor


def endpoint_rows(df, index_col, event_col, censor_col, unit, cutoff):
    factor = time_unit_factor(unit)
    values = [df[index_col], df[event_col], df[censor_col]]
    if cutoff is not None:
        if not pd.api.types.is_scalar(cutoff) or pd.isna(cutoff):
            raise ValueError("administrative_censor_date must be a nonmissing scalar date.")
        # Validate even for empty cohorts.
        parse_dates(cutoff, errors="raise")
        values.append(cutoff)
    parsed, invalid = parse_dates(*values)
    start, event, censor = parsed[:3]
    if cutoff is not None and invalid[3].any():
        raise ValueError("administrative_censor_date contains an invalid date.")
    use_event = event.notna() & (censor.isna() | (event <= censor))
    endpoint = event.where(use_event, censor)
    truncated = pd.Series(False, index=df.index)
    cutoff_before_index = truncated.copy()
    if cutoff is not None:
        cutoff_dates = parsed[3]
        truncated = endpoint.notna() & (endpoint > cutoff_dates)
        cutoff_before_index = cutoff_dates < start
        endpoint = endpoint.where(~truncated, cutoff_dates)
        use_event = use_event & ~truncated
    source = pd.Series("censor", index=df.index, dtype=object)
    source.loc[use_event] = "event"
    source.loc[endpoint.isna()] = "missing"
    duration = (endpoint - start).dt.total_seconds() / 86400.0 / factor
    flags = pd.DataFrame({
        "missing_index_date": df[index_col].isna(),
        "invalid_index_date": invalid[0],
        "missing_event_date": df[event_col].isna(),
        "invalid_event_date": invalid[1],
        "missing_censor_date": df[censor_col].isna(),
        "invalid_censor_date": invalid[2],
        "event_before_index": event < start,
        "censor_before_index": censor < start,
        "cutoff_before_index": cutoff_before_index,
        "missing_endpoint": endpoint.isna(),
        "negative_followup": duration < 0,
        "zero_followup": duration == 0,
        "event_censor_tie": event.notna() & censor.notna() & (event == censor),
        "event_after_followup": event.notna() & censor.notna() & (event > censor),
        "cutoff_truncated": truncated,
    }, index=df.index)
    blocking = ["missing_index_date", "invalid_index_date", "invalid_event_date",
                "invalid_censor_date", "cutoff_before_index", "missing_endpoint",
                "negative_followup"]
    flags["valid_endpoint"] = ~flags[blocking].any(axis=1)
    flags["positive_duration_eligible"] = flags.valid_endpoint & (duration > 0)
    rows = pd.DataFrame({"time": duration, "event": use_event.astype(int),
                         "endpoint_date": endpoint, "endpoint_source": source}, index=df.index)
    rows = pd.concat([rows, flags], axis=1)
    summary = pd.DataFrame([
        {"metric": "rows", "count": len(df), "severity": "count"},
        {"metric": "valid_events", "count": int((flags.valid_endpoint & use_event).sum()), "severity": "count"},
        {"metric": "valid_censored", "count": int((flags.valid_endpoint & ~use_event).sum()), "severity": "count"},
        *[{"metric": name, "count": int(flags[name].sum()),
           "severity": "blocking" if name in blocking else
                       "eligibility" if name in {"valid_endpoint", "positive_duration_eligible"} else "review"}
          for name in flags],
    ])
    return {"rows": rows, "summary": summary}


def validate_output_names(outputs, date_inputs):
    if len(set(outputs)) != len(outputs):
        raise ValueError("Endpoint output column names must be distinct.")
    if set(outputs) & set(date_inputs):
        raise ValueError("Endpoint output columns must not overwrite required date inputs.")
