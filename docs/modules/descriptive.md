# Descriptive Analysis

`fyron.descriptive` creates clinical descriptive statistics: numeric summaries, categorical summaries, group comparisons, Table 1 style outputs, standardized mean differences, and endpoint summaries.

Use this module after a cohort table has been built and validated. The goal is to produce structured tables that can be reviewed by clinicians, exported to supplements, or passed into `fyron.reporting`.

## Install

```bash
uv add "fyron[descriptive]"
```

## Imports

```python
from fyron import descriptive as fd
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| numeric columns | Continuous variables such as age, follow-up time, L3 SMA, tumor volume, or lab values. |
| categorical columns | Grouped variables such as sex, stage, treatment, scanner type, or endpoint status. |
| `group_col` | Optional column used to stratify summaries, such as treatment arm or risk group. |
| SMD | Standardized mean difference; useful for balance assessment and less sample-size-dependent than p-values. |
| endpoint summary | Counts and follow-up/event summaries for a clinical outcome column. |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | Patient-level cohort DataFrame, usually one row per patient or analysis unit. |
| Required columns | Explicit numeric, categorical, group, event, and time columns passed to the helper. |
| Return shape | Long-format summary DataFrames suitable for review, reporting, or export. |
| Saved artifacts | Table 1 CSV/Markdown, endpoint summaries, SMD/balance tables, and group comparison tables. |
| Failure modes | Missing columns, inappropriate variable types, invalid event coding, empty groups, or unsupported statistical comparison. |

## Minimal Example

```python
from fyron import descriptive as fd

table_one = fd.create_table_one(
    cohort,
    group_col="risk_group",
    numeric=["age", "l3_sma_cm2", "vat_ml"],
    categorical=["sex", "stage"],
    include_smd=True,
)
```

## Function Guide

| Function | Use it when | Returns |
| --- | --- | --- |
| `describe_numeric` | You need mean/SD/median/IQR style summaries for continuous columns. | numeric summary DataFrame |
| `describe_categorical` | You need counts and percentages for categorical columns. | categorical summary DataFrame |
| `compare_descriptive_groups` | You need p-values and optional SMDs by group. | comparison DataFrame |
| `create_table_one` | You need a combined baseline characteristics table. | long Table 1 DataFrame |
| `summarize_endpoint` | You need event counts and optional time-to-event summaries. | endpoint summary DataFrame |

## Parameter Notes

| Parameter | Practical guidance |
| --- | --- |
| `df` | Use a patient-level cohort table, usually one row per patient. |
| `numeric` / `columns` | Pass explicit continuous variables; do not rely on automatic type guessing for final analyses. |
| `categorical` / `columns` | Pass explicit categorical variables, including binary flags when counts matter. |
| `group_col` | Use when comparing treatment arms, risk groups, cohorts, or endpoint strata. |
| `include_smd` | Recommended for baseline balance tables. |
| `event_col` | Use `1` for event and `0` for no event/censored when summarizing endpoints. |
| `time_col` | Optional follow-up duration column used in endpoint summaries. |

## Common Workflow

```python
numeric = fd.describe_numeric(
    cohort,
    columns=["age", "l3_sma_cm2", "vat_ml"],
    group_col="risk_group",
)

categorical = fd.describe_categorical(
    cohort,
    columns=["sex", "stage"],
    group_col="risk_group",
)

table_one = fd.create_table_one(
    cohort,
    group_col="risk_group",
    numeric=["age", "l3_sma_cm2", "vat_ml"],
    categorical=["sex", "stage"],
    include_smd=True,
)

endpoint = fd.summarize_endpoint(
    cohort,
    event_col="event",
    time_col="time",
    group_col="risk_group",
)
```

## Return Values

All functions return `pandas.DataFrame` outputs. With a `group_col`, `create_table_one` adds columns such as `p_value`, `smd`, and `test` when applicable. Keep these tables as intermediate artifacts so manuscript tables can be audited.

## Common Pitfalls

- Do not interpret baseline p-values as proof of clinical comparability.
- Confirm categorical coding before reporting percentages.
- Do not let post-outcome variables enter baseline descriptive tables.
- Always state whether missing values were excluded, counted, or imputed.

## Related Modules

- [Cohort Tables](cohort.md) for building the patient-level input table.
- [Reporting](reporting.md) for paper-ready baseline and metric tables.
- [Clinical Plotting](plotting.md) for visual summaries of Table 1 and group distributions.
