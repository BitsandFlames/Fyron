# Clinical Codes

`fyron.clinical_codes` provides explicit helpers for turning ICD-10, OPS, encounter type, MDC partition, and Charlson comorbidity fields into inspectable cohort columns. Use it when raw clinical code strings need to become protocol-reviewable features before cohort construction, descriptive statistics, survival analysis, or machine learning.

These helpers are pragmatic feature derivations. Broad ICD-10 disease groups and OPS/MDC partitions are not validated phenotype definitions, and Charlson scoring depends on the selected mapping implementation.

## Install

ICD-10, OPS, MDC, encounter, and Charlson helpers are available with Fyron:

```bash
uv add fyron
```

## Imports

```python
from fyron import clinical_codes as fcc
```

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | One-row-per-patient, one-row-per-encounter, one-row-per-stay, or one-code-per-row DataFrames with ICD-10, OPS, encounter type, or ID columns. Scalar classifiers also accept single code strings. |
| Required columns | Source columns named in the call; `add_mdc_partition` can discover common OPS column names; Charlson can use an explicit ID column or a temporary row ID. |
| Return shape | DataFrame copies with derived indicator, partition, encounter, Charlson, or list-valued code columns; prevalence summary DataFrames; scalar classifier outputs. |
| Saved artifacts | Save enriched cohort tables, raw source code columns, prevalence summaries, Charlson skipped reasons, and any study-specific coding assumptions. |
| Failure modes | Missing source columns, malformed code strings, unknown encounter types, no parsable ICD codes, or code ranges that need study-specific clinical review. |

## Common Workflow

```python
procedures_by_encounter = fcc.aggregate_ops_by_encounter(
    procedures,
    complete_encounters=cohort[["patient_id", "encounter_id"]],
)

cohort = cohort.merge(procedures_by_encounter, on=["patient_id", "encounter_id"], how="left")
cohort = fcc.add_icd10_disease_groups(cohort, icd_col="diagnosis_codes")
cohort = fcc.add_ops_categories(cohort, ops_col="ops_codes")
cohort = fcc.add_mdc_partition(cohort, ops_column="ops_codes")
cohort = fcc.add_encounter_type_features(cohort, "encounter_type")

cohort, skipped = fcc.add_charlson_comorbidity_columns(
    cohort,
    icd_column="diagnosis_codes",
    id_column="encounter_id",
)
```

Save the raw source columns next to derived features. For audit, also save prevalence summaries from `icd10_group_prevalence` and `ops_category_prevalence`.

## Long Code Rows To Lists

Clinical extractions often produce one code per row. Use `aggregate_code_rows` to convert those long tables into one row per patient, encounter, stay, or other grouping key with list-valued code columns.

```python
diagnoses_by_encounter = fcc.aggregate_code_rows(
    diagnoses,
    group_cols=["patient_id", "encounter_id"],
    code_col="icd10_code",
    display_col="icd10_display",
    date_col="recorded_date",
    code_list_col="icd10_code_list",
    display_list_col="icd10_display_list",
    first_date_col="icd10_first_recorded_date",
    last_date_col="icd10_last_recorded_date",
    count_col="n_icd10_codes",
    complete_groups=cohort[["patient_id", "encounter_id"]],
)
```

For OPS procedures, `aggregate_ops_by_encounter` uses Fyron's procedure defaults:

```python
procedures_by_encounter = fcc.aggregate_ops_by_encounter(
    procedures,
    complete_encounters=cohort[["patient_id", "encounter_id"]],
)
```

It expects one procedure per row with columns like `patient_id`, `encounter_id`, `performed_date`, `ops_code`, and `ops_display`, and returns `ops_code_list`, `ops_display_list`, `ops_first_performed_date`, `ops_last_performed_date`, and `n_ops_codes`. Encounters supplied through `complete_encounters` are retained with empty lists and zero counts when no OPS code is present.

## ICD-10 Groups

ICD-10 helpers map chapter-style code signals into broad disease groups:

```python
fcc.classify_icd10("C34")
# "Cancer"

cohort = fcc.add_icd10_disease_groups(cohort, "icd10_codes")
prevalence = fcc.icd10_group_prevalence(cohort)
```

The DataFrame helper adds binary columns such as `icd10_group_cancer`, a readable `icd10_groups` summary, and `n_icd10_groups`.

## OPS And MDC

OPS helpers support broad procedure categories and MDC medical/surgical partitioning:

```python
fcc.classify_ops("5-470.0")
# "Surgery"

fcc.classify_mdc_partition("8-930; 5-470.0")
# "surgical"
```

`add_mdc_partition` adds:

| Column | Meaning |
| --- | --- |
| `mdc_partition` | `surgical`, `medical`, or `other` |
| `mdc_partition_source` | OPS source column used for the derivation |

Surgical takes precedence when both chapter-5 surgical OPS codes and medical OPS codes appear in the same stay.

## Encounter Status

Encounter type helpers classify common encounter codes into elective status:

| Encounter code | Status |
| --- | --- |
| `AMB` | `elective` |
| `IMP` | `elective` |
| `EMER` | `non_elective` |
| missing or unknown | `unknown` |

```python
cohort = fcc.add_encounter_type_features(cohort, "encounter_type")
```

## Charlson Comorbidity Index

Charlson scoring uses explicit ICD-10 code ranges and standard Charlson weights. The helper returns `(DataFrame, skipped_reason)` so pipelines can continue when the source column is missing or has no parsable ICD codes.

```python
cohort, skipped = fcc.add_charlson_comorbidity_columns(
    cohort,
    icd_column="diagnosis_codes",
    id_column="encounter_id",
)

if skipped:
    print(skipped)
```

The returned DataFrame includes:

| Column | Meaning |
| --- | --- |
| `charlson_comorbidity_index` | Numeric Charlson score |
| `charlson_comorbidity_category` | Ordered category: `0`, `1-2`, `3-4`, `>=5` |
| `charlson_*` | Binary Charlson comorbidity indicator columns |

## Function Guide

| Function | Purpose |
| --- | --- |
| `normalize_code`, `split_code_string`, `explode_code_column` | Shared code parsing |
| `aggregate_code_rows` | Convert one-code-per-row tables to list-valued grouped rows |
| `classify_icd10`, `classify_icd10_string` | Broad ICD-10 disease groups |
| `add_icd10_disease_groups`, `icd10_group_prevalence` | ICD-10 DataFrame features and summaries |
| `classify_ops`, `classify_ops_string` | Broad OPS procedure categories |
| `normalize_ops_codes`, `get_ops_chapter` | Robust OPS parsing |
| `aggregate_ops_by_encounter` | Convert one-OPS-per-row procedure tables to encounter-level lists |
| `classify_mdc_partition`, `add_mdc_partition` | Medical/surgical/other MDC partition |
| `classify_elective_status`, `add_encounter_type_features` | Encounter elective status |
| `classify_charlson_comorbidities`, `charlson_comorbidity_index` | Scalar Charlson comorbidity flags and score |
| `derive_charlson_category`, `add_charlson_comorbidity_columns` | Charlson DataFrame features |

## Related Modules

- [DataFrame Operations](dataframe.md) still re-export these helpers for existing table-feature workflows.
- [Phenotyping](phenotyping.md) defines explicit study-specific rules from code tables.
- [Cohort Tables](cohort.md) joins derived features with outcomes.
- [Preprocessing QC](preprocessing.md) handles imputation, encoding, and leakage checks after coding features are derived.
