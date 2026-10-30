# Clinical DataFrame Operations

## Explicit Date Handling

`date_difference`, `add_date_difference`, `age_at_date`, and `add_time_window_flag`
accept keyword-only `errors="coerce"` (the existing default) or `errors="raise"`.
Coercion makes malformed dates missing. Strict mode rejects malformed values but
permits genuinely absent dates. Missing dates yield missing differences and zero
time-window flags.

Scalars broadcast against vectors. Vectors must have equal lengths; Series must
have identical indices in the same order. Results preserve indices rather than
silently aligning unrelated rows. Aware timestamps use UTC elapsed time, including
DST offsets. Mixing naive and aware nonmissing dates raises.

Window bounds must be finite and nonnegative. Months mean 30.4375 days and years
365.25 days; `age_at_date` is elapsed age, not completed birthdays. For event/censor
selection and quality flags, use the [cohort module](cohort.md), not an absolute
date difference that could hide invalid chronology.

`fyron.dataframe` provides small, explicit helpers for deriving clinical columns from ordinary pandas DataFrames. Use it when you need stable one-hot indicators for delimited code strings or reusable date/time interval columns before cohort construction, phenotyping, preprocessing, survival analysis, or machine learning. ICD-10, OPS, MDC partition, encounter status, and Charlson helpers are also available here for compatibility, with their dedicated home in [`fyron.clinical_codes`](clinical-codes.md).

This module is not a replacement for pandas and it is not a validated terminology ontology. It gives researchers transparent, reviewable feature derivations that can be saved, inspected, and challenged in a study protocol.

## Install

```bash
uv add fyron
```

## Imports

```python
from fyron import dataframe as fdf
```

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | One-row-per-patient or one-row-per-event DataFrames with code or date columns. Scalar helpers also accept single code strings. |
| Required columns | Code columns named in the call, date columns for interval helpers, and optional ID columns kept by the caller for audit. |
| Return shape | DataFrame copies with derived columns, prevalence summary DataFrames, exploded long code tables, or `pandas.Series` interval outputs. |
| Saved artifacts | Save the enriched cohort table, code prevalence tables, date interval definitions, and the original raw code columns. |
| Failure modes | Missing columns, invalid time units, negative intervals when disallowed, malformed code strings, or overly broad categories requiring clinical review. |

## When To Use It

| Task | Helper |
| --- | --- |
| Convert ICD-10 strings into broad comorbidity features | `add_icd10_disease_groups` |
| Summarize ICD-10 disease-group prevalence | `icd10_group_prevalence` |
| Convert German OPS strings into broad procedure categories | `add_ops_categories` |
| Summarize OPS category prevalence | `ops_category_prevalence` |
| Add MDC medical/surgical/other partition from OPS codes | `add_mdc_partition` |
| Add Charlson Comorbidity Index columns | `add_charlson_comorbidity_columns` |
| Convert one-code-per-row tables into grouped code lists | `aggregate_code_rows`, `aggregate_ops_by_encounter` |
| Parse semicolon-separated code columns | `split_code_string`, `explode_code_column` |
| Add stable indicators for selected codes | `add_code_indicators` |
| Compute days, weeks, months, or years between dates | `date_difference`, `add_date_difference` |
| Compute age at baseline or scan date | `age_at_date` |
| Flag events inside an index-relative window | `add_time_window_flag` |

## Study Pattern

In most projects this module is used early, right after extraction and before statistical modeling:

```python
from fyron import dataframe as fdf

cohort = fdf.add_icd10_disease_groups(cohort, icd_col="icd10_codes")
cohort = fdf.add_ops_categories(cohort, ops_col="ops_codes")
cohort = fdf.age_at_date(
    cohort,
    birth_date_col="birth_date",
    reference_date_col="index_date",
    output_col="age_at_index",
)

code_qc = fdf.icd10_group_prevalence(cohort)
```

Save both `cohort` and `code_qc`. The enriched cohort becomes the modeling table; the prevalence table becomes a lightweight audit artifact for the methods supplement or internal review.

## ICD-10 Disease Groups

For new clinical coding work, prefer [`fyron.clinical_codes`](clinical-codes.md). The same ICD-10 helpers remain available here for existing DataFrame workflows.

ICD-10 helpers use broad pragmatic chapter-style groups such as cancer, cardiovascular, respiratory, gastrointestinal, renal/urologic, trauma, external cause, and healthcare encounter. These are useful for quick cohort description and feature engineering, but they should not replace a study-specific phenotype definition or validated comorbidity score.

```python
cohort = fdf.add_icd10_disease_groups(
    cohort,
    icd_col="diagnosis_codes",
    sep=";",
    prefix="icd10_group_",
)

prevalence = fdf.icd10_group_prevalence(cohort)
```

The output keeps the original `diagnosis_codes` column and adds binary columns such as `icd10_group_cancer`, `icd10_group_cardiovascular`, plus `icd10_groups` and `n_icd10_groups`.

### Built-In ICD-10 Groups

| Group | Typical ICD-10 chapter signal |
| --- | --- |
| Cancer | `C*` |
| Benign / In Situ Neoplasm | `D00-D48` |
| Hematologic / Immune | `D50-D89` |
| Infectious | `A*`, `B*` |
| Endocrine / Metabolic | `E*` |
| Mental Health | `F*` |
| Neurological | `G*` |
| Cardiovascular | `I*` |
| Respiratory | `J*` |
| Gastrointestinal | `K*` |
| Dermatologic | `L*` |
| Musculoskeletal / Autoimmune | `M*` |
| Renal / Urologic | `N*` |
| Obstetric / Perinatal | `O*`, `P*` |
| Congenital | `Q*` |
| Symptoms / Findings | `R*` |
| Trauma | `S*`, `T*` |
| Healthcare Encounter | `Z*` |
| External Cause | `V*`, `W*`, `X*`, `Y*` |
| Other | malformed or uncategorized non-empty codes |

## OPS Procedure Categories

For new OPS/MDC work, prefer [`fyron.clinical_codes`](clinical-codes.md). The same broad OPS category helpers remain available here for existing DataFrame workflows.

German OPS codes are grouped into broad procedure categories: diagnostic procedures, imaging, surgery, medication/therapy, radiation/nuclear medicine, intensive care, rehabilitation, and other. OPS coding can be site-specific, so treat these as transparent research features that still need clinical review.

```python
cohort = fdf.add_ops_categories(
    cohort,
    ops_col="ops_codes",
    sep=";",
    prefix="ops_category_",
)

ops_summary = fdf.ops_category_prevalence(cohort)
```

Use the summary table in supplements or QC notebooks to check whether procedure features match clinical expectations.

### Built-In OPS Categories

| Category | Typical OPS chapter signal |
| --- | --- |
| Diagnostic Procedures | `1-*`, `2-*` |
| Imaging | `3-*` |
| Surgery | `5-*` |
| Medication / Therapy | `6-*`, most `8-*` therapy codes |
| Radiation / Nuclear Medicine | `7-*` |
| Intensive Care | `8-98*` |
| Rehabilitation | `9-*` |
| Other | malformed or uncategorized non-empty codes |

## Generic Code Columns

Use the generic helpers for medication codes, local registry fields, procedure codes, or any delimited string column where exact code membership matters.

```python
long_codes = fdf.explode_code_column(
    cohort,
    code_col="medication_codes",
    output_col="medication_code",
)

cohort = fdf.add_code_indicators(
    cohort,
    code_col="medication_codes",
    codes=["L01XA01", "L01XA02"],
    prefix="atc_",
)
```

By default, codes are uppercased and spaces are removed. Dots are preserved unless you pass `remove_dots=True` through `normalize_code` directly. Preserve the raw source column alongside derived indicators so reviewers can trace the feature.

For multiple local definitions, pass a mapping. This gives stable, readable output names without repeating code lists across notebooks.

```python
cohort = fdf.add_code_indicators(
    cohort,
    code_col="procedure_codes",
    codes={
        "has_biopsy": ["1-440", "1-444"],
        "has_resection": ["5-324", "5-325"],
    },
    prefix="proc_",
)
```

## Date And Time Features

Date helpers use the same clinical time-unit convention as cohort endpoint helpers: months are `30.4375` days and years are `365.25` days.

```python
cohort = fdf.add_date_difference(
    cohort,
    start_col="baseline_ct_date",
    end_col="surgery_date",
    output_col="days_ct_to_surgery",
    unit="days",
    allow_negative=False,
)

cohort = fdf.age_at_date(
    cohort,
    birth_date_col="birth_date",
    reference_date_col="baseline_ct_date",
    output_col="age_at_ct",
)

cohort = fdf.add_time_window_flag(
    cohort,
    date_col="biopsy_date",
    index_date_col="baseline_ct_date",
    output_col="biopsy_within_30d",
    before=30,
    after=30,
)
```

`add_time_window_flag` computes the event date relative to the index date. Negative values are before the index, positive values are after the index.

## Function Guide

| Function | Purpose | Returns |
| --- | --- | --- |
| `normalize_code` | Normalize one clinical code string. | string or `None` |
| `split_code_string` | Parse one delimited code cell. | list of codes |
| `explode_code_column` | Convert a wide delimited code column to one row per code. | DataFrame |
| `aggregate_code_rows` | Convert one-code-per-row tables to grouped code lists. | DataFrame |
| `aggregate_ops_by_encounter` | Convert one-OPS-per-row procedure tables to encounter-level lists. | DataFrame |
| `add_code_indicators` | Add exact-code binary indicators. | DataFrame copy |
| `classify_icd10` | Classify one ICD-10 code into a broad disease group. | group name or `None` |
| `classify_icd10_string` | Classify all ICD-10 codes in one delimited cell. | set of group names |
| `add_icd10_disease_groups` | Add ICD-10 disease-group indicator columns. | DataFrame copy |
| `icd10_group_prevalence` | Summarize ICD-10 group indicator columns. | prevalence DataFrame |
| `classify_ops` | Classify one German OPS code into a broad procedure category. | category name or `None` |
| `classify_ops_string` | Classify all OPS codes in one delimited cell. | set of category names |
| `add_ops_categories` | Add OPS category indicator columns. | DataFrame copy |
| `ops_category_prevalence` | Summarize OPS category indicator columns. | prevalence DataFrame |
| `normalize_ops_codes` | Parse scalar, delimited, list-like, or iterable OPS values. | list of codes |
| `get_ops_chapter` | Extract the one-digit OPS chapter. | string or `None` |
| `classify_mdc_partition` | Classify OPS values as `surgical`, `medical`, or `other`. | string |
| `add_mdc_partition` | Add MDC partition and source columns. | DataFrame copy |
| `classify_elective_status` | Classify encounter type as elective, non-elective, or unknown. | string |
| `add_encounter_type_features` | Add normalized encounter type and elective-status columns. | DataFrame copy |
| `derive_charlson_category` | Bin Charlson scores into ordered categories. | Categorical |
| `classify_charlson_comorbidities` | Classify ICD-10 values into Charlson indicators. | dict |
| `charlson_comorbidity_index` | Calculate a scalar Charlson score from ICD-10 values. | integer or `None` |
| `add_charlson_comorbidity_columns` | Add Charlson score/category and indicator columns. | `(DataFrame, skipped_reason)` |
| `date_difference` | Compute interval between two date arrays/scalars. | Series |
| `add_date_difference` | Add an interval column to a DataFrame. | DataFrame copy |
| `age_at_date` | Add age in years at a reference date. | DataFrame copy |
| `add_time_window_flag` | Flag whether a date falls inside an index-relative window. | DataFrame copy |

## Common Pitfalls

- Broad ICD-10 and OPS groups are feature-engineering assumptions, not validated disease ontologies.
- Keep raw code columns and code-system metadata whenever possible.
- Use prefixed indicator columns to avoid spaces and slashes in downstream ML formulas.
- Check whether repeated codes should count once per patient or once per event before exploding.
- Define the index date before creating time-window flags.
- Use `allow_negative=False` when a negative interval indicates a data error for the study.

## Related Modules

- [FHIR REST](fhir/rest.md) extracts source resources that often contain ICD, OPS, medication, and observation codes.
- [Clinical Codes](clinical-codes.md) is the dedicated namespace for ICD-10, OPS, MDC partition, encounter status, and Charlson helpers.
- [Phenotyping](phenotyping.md) builds explicit rule-based patient flags from code, lab, and medication tables.
- [Cohort Tables](cohort.md) joins derived features with endpoints and validates cohort shape.
- [Preprocessing QC](preprocessing.md) handles imputation, train/test encoding, and leakage checks after feature derivation.
- [Machine Learning](ml.md) trains and evaluates models once a cohort table and feature matrix are ready.
