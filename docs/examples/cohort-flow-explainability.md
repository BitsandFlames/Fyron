# Cohort Flow And Model Explainability

This tutorial shows how to track cohort filters, export a text flow chart, plot the cohort flow, train a small classifier, and assemble a reviewer-facing explanation table.

## Synthetic Cohort

```python
import pandas as pd

raw = pd.DataFrame(
    {
        "patient_id": [f"p{i:03d}" for i in range(1, 9)],
        "age": [72, 66, 58, 17, 81, 69, 55, 62],
        "baseline_ct": ["ct1", "ct2", None, "ct4", "ct5", None, "ct7", "ct8"],
        "followup_days": [400, 220, 100, 50, 500, 90, 300, None],
        "l3_sma_cm2": [120, 112, 130, 90, 105, 99, 140, 118],
        "vat_ml": [230, 180, 210, 160, 300, 250, 175, 205],
        "event": [1, 0, 0, 0, 1, 1, 0, 0],
    }
)
```

Use one row per patient throughout this example. If your workflow switches to one row per lesion, series, or prediction, record that as a separate manual step with metadata.

## Track Filters

```python
from fyron.flow import FlowTracker, track_filter

flow = FlowTracker("Synthetic CT model cohort")
flow.add_step(
    "Source cohort",
    raw,
    metadata={
        "source": "synthetic",
        "row_unit": "patient",
        "id_col": "patient_id",
    },
)

deduplicated = raw.drop_duplicates("patient_id")
flow.add_step(
    "Deduplicated patient IDs",
    deduplicated,
    reason="duplicate patient_id",
    metadata={"rule": "keep first reviewed row"},
)

@track_filter(flow, label="Age >= 18", reason="age < 18")
def filter_adults(df):
    return df[df["age"] >= 18]

@track_filter(flow, label="Has baseline CT", reason="missing baseline CT")
def filter_ct(df):
    return df[df["baseline_ct"].notna()]

@track_filter(flow, label="Has follow-up", reason="missing follow-up")
def filter_followup(df):
    return df[df["followup_days"].notna()]

cohort = filter_followup(filter_ct(filter_adults(deduplicated)))
```

Decorators are best for DataFrame-in/DataFrame-out filters. Use manual `add_step` for deduplication, joins, endpoint construction, reviewed exports, or external tools.

## Track A Join

Joins can remove rows because a matching table is missing, not because the patient failed a clinical criterion. Record those steps manually.

```python
imaging = cohort[["patient_id", "baseline_ct"]].copy()
imaging["series_instance_uid"] = [f"1.2.3.{i}" for i in range(len(imaging))]

with_imaging = cohort.merge(imaging, on=["patient_id", "baseline_ct"], how="inner")
flow.add_step(
    "Joined imaging metadata",
    with_imaging,
    reason="no matching imaging metadata",
    metadata={"join": "inner", "on": ["patient_id", "baseline_ct"]},
)
```

## Export Review Artifacts

```python
flow_table = flow.to_dataframe()
markdown = flow.to_markdown()
text_chart = flow.to_text_flowchart()

print(text_chart)
flow.print(color=False)

flow_table.to_csv("cohort-flow.csv", index=False)
with open("cohort-flow.md", "w", encoding="utf-8") as f:
    f.write(markdown)
with open("cohort-flow.txt", "w", encoding="utf-8") as f:
    f.write(text_chart)
```

```python
from fyron import plotting as fp

fig, ax = fp.plot_cohort_flow(flow_table, title="Synthetic cohort flow")
fig.savefig("cohort-flow.png", bbox_inches="tight", dpi=300)
```

## Add Flow Artifacts To Provenance

```python
from fyron.audit import analysis_run_manifest

manifest = analysis_run_manifest(
    title="Synthetic cohort flow example",
    inputs=["raw synthetic cohort"],
    parameters={"row_unit": "patient", "minimum_followup_required": True},
    outputs=[
        "cohort-flow.csv",
        "cohort-flow.md",
        "cohort-flow.txt",
        "cohort-flow.png",
    ],
    random_seed=42,
)
```

## Model Explanation Summary

```python
from fyron import explainability as fe
from fyron.preprocessing import feature_matrix_report

X = with_imaging[["age", "l3_sma_cm2", "vat_ml"]]
y = with_imaging["event"]

# In a real analysis, use held-out validation data and a fitted model.
importance = pd.DataFrame(
    {
        "feature": ["age", "l3_sma_cm2", "vat_ml"],
        "importance_mean": [0.12, 0.08, 0.04],
        "importance_std": [0.02, 0.01, 0.01],
    }
)

qc = feature_matrix_report(X, y)

summary = fe.explain_model_summary(
    importance=importance,
    feature_qc=qc,
    metrics={"auc": 0.78, "balanced_accuracy": 0.70},
    notes={"l3_sma_cm2": "Check direction against sarcopenia hypothesis."},
)
```

## Patient-Level Drivers

```python
contributions = pd.DataFrame(
    {
        "row_index": [0, 0, 0],
        "feature": ["age", "l3_sma_cm2", "vat_ml"],
        "feature_value": [72, 120, 230],
        "shap_value": [0.18, -0.12, 0.04],
    }
)

drivers = fe.explain_patient_prediction(contributions, row_index=0, top_n=2)
```

The flow table explains cohort membership. The explanation summary and patient drivers explain model behavior. Keep both with your manuscript artifacts and provenance manifest.
