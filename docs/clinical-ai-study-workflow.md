# Clinical AI Study Workflow

This guide shows how Fyron functions map to the decisions in a clinical AI study. The goal is not to hide study design behind automation. The goal is to make each assumption explicit and leave behind artifacts that a clinician, statistician, or reviewer can inspect.

## Study Contract

Before modeling, write down the contract for the analysis:

| Decision | Fyron artifact |
| --- | --- |
| Analysis unit | cohort table with one row per patient, lesion, scan, or encounter |
| Index date | column used as time zero |
| Endpoint | event definition, event date, censor date, event coding |
| Features | feature table or matrix with source identifiers preserved |
| Split | train/test or development/external validation cohort |
| Model | fitted estimator, parameters, seed, feature list |
| Validation | metrics, calibration, threshold, subgroup, and decision-curve tables |
| Publication | Table 1, figures, model comparison table, provenance manifest |

## Minimal Study Skeleton

```python
from fyron import audit as fa
from fyron import descriptive as fd
from fyron import preprocessing as fp
from fyron import reporting as fr
from fyron import validation as fv
from fyron.cohort import build_time_to_event_endpoint, cohort_profile, join_cohort_tables

cohort = join_cohort_tables(features, outcomes, on="patient_id")

cohort = build_time_to_event_endpoint(
    cohort,
    index_date_col="baseline_ct_date",
    event_date_col="death_date",
    censor_date_col="last_followup_date",
    time_unit="days",
)

profile = cohort_profile(cohort, endpoint_cols=["event"], group_col="stage")
missingness = fp.summarize_missingness(cohort)
feature_qc = fp.feature_matrix_report(cohort[feature_cols], cohort["event"])

table_one = fd.create_table_one(
    cohort,
    group_col="event",
    numeric=["age", "risk_score"],
    categorical=["sex", "stage"],
)

metric_ci = fv.bootstrap_classification_metrics(
    y_true,
    y_pred,
    y_prob,
    n_rounds=1000,
    random_state=42,
)

model_table = fr.compare_models_table(
    {
        "Random Forest": rf_result,
        "XGBoost": xgb_result,
    }
)

manifest = fa.analysis_run_manifest(
    title="Locked clinical model validation",
    analysis_type="classification",
    cohort_id="cohort-v1",
    inputs=["data/cohort.csv"],
    outputs=["results/table_one.csv", "results/model_table.csv"],
    parameters={"feature_cols": feature_cols, "threshold": 0.4},
    random_seed=42,
)
```

## Research Decisions To Record

| Area | Record explicitly |
| --- | --- |
| Endpoint | index date, event date, censor date, time unit, event coding |
| Cohort | inclusion/exclusion steps, duplicate IDs, missing follow-up |
| Imaging | study UID, series UID, `download_id`, DICOM vs NIfTI, reference DICOM |
| Features | preprocessing, imputation, encoding, leakage exclusions |
| Model | split, seed, hyperparameters, class imbalance handling |
| Validation | locked threshold, calibration bins, subgroup definitions, external cohort |
| Publication | exact tables/figures, package version, input hashes |

## What To Save

Save tables as CSV/Parquet, figures as PNG/PDF/SVG, and manifests as JSON. A defensible Fyron analysis should usually leave these files:

| Artifact | Why it matters |
| --- | --- |
| `cohort.csv` | analysis population and endpoint |
| `cohort_flow.csv` | inclusion/exclusion steps, row loss, and reasons |
| `cohort_profile.csv` | review of IDs, endpoints, and groups |
| `feature_qc.csv` | missingness, constants, rare binary features, leakage flags |
| `table_one.csv` | cohort description |
| `model_metrics.csv` | model performance |
| `calibration.csv` | observed versus predicted risk |
| `subgroups.csv` | performance heterogeneity |
| `figures/*.png` | paper/review visuals |
| `provenance.json` | inputs, outputs, parameters, random seed, Fyron version |

## Critical Reviewer Checklist

- Does every row represent the intended analysis unit?
- Is time zero clinically meaningful?
- Are events and censoring dates mutually interpretable?
- Were post-index or outcome-derived variables excluded from features?
- Was the threshold locked before final validation?
- Are calibration and subgroup performance shown, not only AUC?
- Can every table and figure be reproduced from saved inputs and parameters?
- Is the inclusion/exclusion flow saved beside the final cohort?
