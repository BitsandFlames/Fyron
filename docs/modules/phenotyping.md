# Phenotyping

`fyron.phenotyping` builds transparent rule-based clinical phenotypes from tabular FHIR-derived or registry-style data. Use it when diagnosis codes, procedure codes, lab thresholds, or medication exposure rows need to become patient-level cohort flags.

Phenotyping rules are explicit definitions, not validated clinical truth. Keep the rule inputs, code lists, thresholds, and evidence counts with the analysis so clinicians and reviewers can inspect what happened.

For broad ICD-10 disease groups, German OPS procedure categories, delimited code parsing, and date interval columns, see [DataFrame Operations](dataframe.md). Use `fyron.phenotyping` when the study needs explicit rule definitions with evidence counts and patient-level flags.

## Imports

```python
from fyron import phenotyping as fph
```

## Function Reference

Lab threshold rules require a finite threshold. Missing, nonnumeric, and infinite
measurements never count as evidence, including for `direction="!="`. Rebuild
phenotypes previously derived with inequality rules and invalid measurements.

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `define_code_phenotype` | table, code column, codes | patient/date/code-system columns, phenotype name | patient-level phenotype table |
| `define_lab_threshold_phenotype` | table, value column, threshold | direction, patient/date columns, phenotype name | patient-level phenotype table |
| `define_medication_exposure` | table, medication column, medications | patient/start/end columns, phenotype name | patient-level exposure table |
| `combine_phenotypes` | phenotype tables | `strategy="any"` or `"all"` | combined patient-level table |
| `phenotype_summary` | phenotype table, phenotype column | patient/group columns | prevalence summary table |

## Code Phenotype

```python
condition_flag = fph.define_code_phenotype(
    conditions,
    code_col="code",
    codes=["I50", "I50.1"],
    patient_col="patient_id",
    date_col="recorded_date",
    code_system_col="system",
    code_systems=["ICD-10"],
    phenotype_name="heart_failure",
)
```

Outputs include `patient_id`, `heart_failure`, `evidence_count`, `evidence_values`, and optional `first_date` / `last_date`.

## Lab Threshold Phenotype

```python
anemia = fph.define_lab_threshold_phenotype(
    observations,
    value_col="hemoglobin",
    threshold=12.0,
    direction="<",
    date_col="effective_datetime",
    phenotype_name="anemia",
)
```

## Medication Exposure

```python
exposure = fph.define_medication_exposure(
    medications,
    medication_col="medication_name",
    medications=["cisplatin", "carboplatin"],
    start_col="start_date",
    end_col="end_date",
    phenotype_name="platinum_exposure",
)
```

## Combine Rules

```python
case_definition = fph.combine_phenotypes(
    [condition_flag, anemia],
    strategy="any",
    phenotype_name="study_case",
)

summary = fph.phenotype_summary(
    case_definition.merge(cohort[["patient_id", "sex"]], on="patient_id"),
    phenotype_col="study_case",
    group_col="sex",
)
```

## Common Pitfalls

- Store the exact code lists used for a study.
- Review date windows before interpreting first/last evidence dates.
- Treat medication names/codes as site-specific unless they come from normalized terminology.
- Validate rule outputs on a small manually reviewed sample before modeling.

## Matching And Population Contracts

Code rules use exact string matching, not ICD prefix expansion: selecting `I50`
does not automatically select `I50.1`. Code-system filtering is also exact when
both the system column and allowed systems are supplied. Medication names use
case-insensitive exact matching, not terminology reconciliation.

Single-rule outputs contain patients with matching evidence. `evidence_count`
counts matching source rows, including repeated rows; `evidence_values` collects
distinct values. First/last dates summarize matched records and do not impose
an eligibility window. Apply baseline or follow-up windows before rule evaluation.
Lab values must already use the intended unit; these helpers do not convert units
or choose a clinically appropriate threshold.

Combine rules only after deciding what absent evidence means for the study.
Combination uses the union of supplied patient keys and treats a rule absent for
a patient as false for that combination. Its `evidence_count` counts positive
rules, not original evidence rows. It does not establish disease absence.

Combination inputs must have unique, nonmissing patient keys and one unambiguous
binary flag. Summary helpers accept repeated consistent patient rows, but reject
conflicting flags or group assignments. Missing flags, string labels such as
`"False"`, and values other than boolean or numeric 0/1 are rejected. Resolve
uncertainty explicitly instead of relying on Boolean coercion.

## Executable Population Example

```bash
uv run python examples/research_contracts.py --output-dir /tmp/fyron-contracts
```

The synthetic example filters evidence to an explicit calendar window, matches
an exact demonstration code, and left-joins the evidence onto a three-person
population with `validate="one_to_one"`. It finds one patient with two matching
records; the other patients are labeled `no_matching_evidence`, not confirmed
negative. Its summary denominator is the declared population, not only patients
returned by the rule.

Save the population definition, observation window, source coverage, code list,
units, and handling of absent evidence with the analysis. Passing only positive
rule outputs to `phenotype_summary` produces a positive-only denominator and is
not a prevalence estimate for the full study population.
