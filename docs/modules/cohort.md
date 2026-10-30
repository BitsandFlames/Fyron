# Cohort Tables

For time-to-event studies, follow the [survival workflow](../survival-workflow.md). `build_survival_columns` converts an already-selected endpoint; `build_time_to_event_endpoint` selects event versus censor dates. These are distinct operations, not aliases.

`fyron.cohort` helps create patient-level tables suitable for survival analysis and machine learning. It sits between data acquisition and modeling: once FHIR, SQL, imaging, or document features are extracted, cohort helpers validate and combine them into one analysis table.

The cohort table is the contract between extraction and analysis. It should contain one row per analysis unit, stable identifiers, explicit index/follow-up dates, endpoint columns, and covariates that are available at the intended prediction or analysis time.

## Audit Endpoints Before Fitting

`audit_time_to_event_endpoint` shares endpoint decisions with
`build_time_to_event_endpoint`, but returns `{"rows": ..., "summary": ...}`.
Neither repairs or drops rows. Structural errors such as missing columns, mixed
naive/aware dates, or an invalid cutoff still raise.

```python
from fyron.cohort import audit_time_to_event_endpoint, build_time_to_event_endpoint

options = dict(
    index_date_col="baseline_date", event_date_col="event_date",
    censor_date_col="last_followup_date", time_unit="days",
    administrative_censor_date="2025-12-31",
)
audit = audit_time_to_event_endpoint(df, **options)
summary = audit["summary"]
# Review blocking flags first. Construction still rejects malformed dates.
endpoints = build_time_to_event_endpoint(df, **options, require_endpoint=False)
analysis = endpoints.loc[audit["rows"]["positive_duration_eligible"]].copy()
```

The cutoff caps available event/follow-up endpoints; it does not create follow-up
when both dates are absent. Events on the follow-up or cutoff boundary count as
events. `endpoint_source` remains `event`, `censor`, or `missing`; the audit flag
`cutoff_truncated` identifies administrative censoring. Define last follow-up
clinically, separately from the study cutoff.

Row output includes `time`, `event`, `endpoint_date`, `endpoint_source`, and flags:

| Flags | Meaning |
| --- | --- |
| `missing_index_date`, `invalid_index_date`, `invalid_event_date`, `invalid_censor_date` | Blocking input problems |
| `missing_endpoint`, `negative_followup`, `cutoff_before_index` | Blocking endpoint problems |
| `missing_event_date`, `missing_censor_date` | Review available evidence; one date can suffice |
| `event_before_index`, `censor_before_index` | Review chronology; selected negative follow-up blocks fitting |
| `zero_followup`, `event_censor_tie`, `event_after_followup`, `cutoff_truncated` | Review boundary decisions |
| `valid_endpoint` | Nonnegative, usable endpoint; not proof of clinical validity |
| `positive_duration_eligible` | Also requires positive time for AFT/boosting/validation |

The summary contains `metric`, `count`, and `severity`. Flags overlap, so their
counts are not additive exclusions. `valid_events` and `valid_censored` exclude
invalid/unresolved rows. With `require_endpoint=False`, unresolved rows retain
`event=0` for compatibility, but missing duration/source means they are **not
observed censored cases**. Do not summarize event indicators before eligibility.

Original row order and indices, including duplicate indices, are preserved.
Row-level audit outputs are sensitive research data, not shareable logs.

## Audit Joins

`audit_cohort_join(features, outcomes, on="patient_id")` returns a `metric`/`count`
table without merging clinical rows. It reports missing-key rows, duplicate rows
among nonmissing keys, matched/unmatched keys and rows, and expected inner, left,
right, and outer join sizes. Duplicate keys can multiply rows.

Expected sizes describe pandas behavior, including null-to-null matching. These
are hypothetical when keys are missing: `join_cohort_tables` still rejects
missing identifiers and defaults to `validate="one_to_one"`. Auditing does not
weaken safeguards. The join report contains no identifiers.

## Date Contracts

Endpoint dates are parsed strictly. Aware timestamps use UTC elapsed time; naive
dates stay naive. Mixing the two is rejected. Date-only strings therefore cannot
be mixed with aware timestamps without explicitly choosing a timezone first.
Weeks mean seven days, months 30.4375 days, and years 365.25 days. These are fixed
elapsed-time units, not calendar arithmetic or completed birthdays. Output names
must be distinct and must not overwrite required date inputs.

## What This Module Is For

Joins reject missing identifiers on either side, even when duplicate IDs are
allowed. `validate_cohort_table` also rejects missing IDs unless
`id_column=None`. Endpoint construction distinguishes truly missing event dates
from supplied but unparseable event/censor dates: malformed dates raise
`ValueError`, including with `require_endpoint=False`. They are not silently
treated as censored. Audit prior joins containing null IDs and rebuild endpoints
if malformed date strings were present.

Use `fyron.cohort` when you already have feature and outcome tables and need to create a reviewable analysis table. It does not decide your inclusion criteria or endpoint definition for you; it helps encode those decisions into explicit joins, survival columns, and validation checks.

Use [DataFrame Operations](dataframe.md) before this step when raw ICD-10, OPS, local code, or date columns need to become explicit feature columns.

## When To Use It

| Situation | Use |
| --- | --- |
| Feature and outcome tables need to become one analysis table | `join_cohort_tables` |
| You need `time` and `event` columns for survival analysis | `build_survival_columns` |
| You have separate index, event, and censor dates | `build_time_to_event_endpoint` |
| You need a compact cohort audit summary | `cohort_profile` |
| You need to fail early on missing columns or duplicate IDs | `validate_cohort_table` |
| You are preparing a cohort for Table 1, KM curves, Cox models, or ML | all three helpers |

## Why Cohort Tables Matter

Most downstream functions assume one row per patient or one row per analysis unit. A good cohort table should make these choices explicit:

- unique patient identifier,
- baseline/index date,
- outcome/event date or last follow-up,
- event indicator,
- covariates measured before the outcome,
- no duplicated patient rows unless intentionally modeled.

## Cohort Design Checklist

- Define the analysis unit before joining tables.
- Keep raw source identifiers so joins can be audited.
- Separate baseline covariates from outcome-derived columns.
- Build `time` and `event` from documented date fields.
- Validate required columns before running survival or ML functions.

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | Patient-level or analysis-unit-level `pandas.DataFrame` objects. |
| Required columns | Stable ID column for joins/QC; date and event columns for endpoint builders; explicit required columns for validation. |
| Return shape | DataFrame copies or compact QC/profile DataFrames; validation helpers raise on invalid inputs. |
| Saved artifacts | Caller exports cohort CSVs, endpoint tables, profiles, and flow tables as study artifacts. |
| Failure modes | Missing columns, duplicate IDs, invalid date order, negative/zero follow-up, missing censoring, or invalid event coding. |

## Imports

```python
from fyron.cohort import (
    build_time_to_event_endpoint,
    build_survival_columns,
    cohort_profile,
    join_cohort_tables,
    validate_cohort_table,
)
```

## Join Features And Outcomes

```python
cohort = join_cohort_tables(
    features_df,
    outcomes_df,
    on="patient_id",
    how="inner",
)
```

### Required and Optional Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `features` | yes | `DataFrame` | none | Feature table, usually one row per patient. |
| `outcomes` | yes | `DataFrame` | none | Outcome/follow-up table. |
| `on` | no | `str` | `"patient_id"` | Join key present in both tables. |
| `how` | no | `str` | `"inner"` | Pandas merge strategy. |
| `validate` | no | `str` | `"one_to_one"` | Pandas merge validation mode. |

Returns a merged DataFrame.

Typical inputs:

| Table | Example columns |
| --- | --- |
| `features_df` | `patient_id`, `age`, `stage`, `risk_score`, `tumor_volume` |
| `outcomes_df` | `patient_id`, `event`, `last_followup_or_event_date` |
| `cohort` | merged feature/outcome table |

Use `how="inner"` when final analysis requires both features and outcomes. Use left joins during quality control to inspect missing outcomes.

## Validate Required Columns

```python
validate_cohort_table(
    cohort,
    required_columns=["patient_id", "age", "stage", "event"],
    id_column="patient_id",
)
```

### Required and Optional Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `DataFrame` | none | Cohort table to validate. |
| `required_columns` | yes | `Sequence[str]` | none | Columns that must be present. |
| `id_column` | no | `str | None` | `"patient_id"` | ID column checked for duplicates. Pass `None` to skip ID checks. |
| `allow_duplicate_ids` | no | `bool` | `False` | Permit duplicated IDs. |

Returns a validated copy/reference of the DataFrame or raises a clear error.

Validation should be early and loud. It is better to fail at cohort construction than to fit a model on a silently malformed table.

## Build Survival Columns

```python
cohort = build_survival_columns(
    cohort,
    start_col="diagnosis_date",
    end_col="last_followup_or_event_date",
    event_col="death_event",
    time_col="time",
)
```

### Required and Optional Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `DataFrame` | none | Input table. |
| `start_col` | yes | `str` | none | Start/index date column. |
| `end_col` | yes | `str` | none | Event/follow-up date column. |
| `event_col` | yes | `str` | none | Existing event indicator column. |
| `time_col` | no | `str` | `"time"` | Name of output duration column in days. |
| `event_out_col` | no | `str` | `"event"` | Name of normalized output event column. |

Returns a DataFrame with `time_col` and `event_out_col`.

The resulting `time` and `event` columns are ready for `fyron.survival`.

## Build Endpoint From Event And Censor Dates

Use `build_time_to_event_endpoint` when event and censor dates are stored separately. It records both the final endpoint date and whether that date came from an event or censoring.

```python
cohort = build_time_to_event_endpoint(
    cohort,
    index_date_col="baseline_ct_date",
    event_date_col="death_date",
    censor_date_col="last_followup_date",
    time_unit="days",
)
```

Returned columns include `time`, `event`, `endpoint_date`, and `endpoint_source`. If an event happens after the censor date, the row is treated as censored at the censor date.

## Cohort Profile

```python
profile = cohort_profile(
    cohort,
    id_col="patient_id",
    endpoint_cols=["event"],
    group_col="stage",
)
```

Use this table before modeling. It summarizes row counts, unique IDs, missing IDs, duplicate ID rows, endpoint counts/rates, and group sizes.

## Full Cohort Pattern

```python
from fyron.cohort import (
    build_survival_columns,
    join_cohort_tables,
    validate_cohort_table,
)

cohort = join_cohort_tables(
    features_df,
    outcomes_df,
    on="patient_id",
    how="inner",
)

cohort = build_survival_columns(
    cohort,
    start_col="index_date",
    end_col="last_followup_or_event_date",
    event_col="event",
)

validate_cohort_table(
    cohort,
    required_columns=["patient_id", "time", "event", "age", "risk_score"],
    id_column="patient_id",
)
```

## Quality-Control Checklist

- Confirm `patient_id` uniqueness.
- Confirm index dates precede outcome/follow-up dates.
- Check missingness before dropping rows.
- Confirm event coding: `1` means event and `0` means censored for survival.
- Keep feature measurement windows before the index/outcome.
- Save cohort-building code with the analysis, not only the final CSV.

## Common Downstream Uses

```python
from fyron.survival import plot_kaplan_meier
from fyron import ml

plot_kaplan_meier(cohort, "time", "event", group_col="stage")

result = ml.run_classification_pipeline(
    cohort[["age", "risk_score"]],
    cohort["binary_endpoint"],
)
```

## Return Values

| Function | Return shape | Notes |
| --- | --- | --- |
| `join_cohort_tables` | merged DataFrame | Uses pandas merge semantics and optional merge validation. |
| `validate_cohort_table` | validated DataFrame | Raises clear errors for missing columns or duplicate IDs. |
| `build_survival_columns` | DataFrame with duration/event columns | Duration is computed from date columns; event is normalized into the requested output column. |
| `build_time_to_event_endpoint` | DataFrame with endpoint columns | Uses index, event, and censor dates to create `time`, `event`, `endpoint_date`, and `endpoint_source`. |
| `cohort_profile` | audit DataFrame | Compact cohort-level counts for review. |

## Related Modules

- [Preprocessing QC](preprocessing.md) for missingness, imputation, encoding, leakage checks, and split balance.
- [Descriptive Analysis](descriptive.md) for Table 1 and endpoint summaries.
- [Survival Analysis](survival.md) for KM, RMST, Cox, and AFT workflows.
- [Machine Learning](ml.md) for classification pipelines.
