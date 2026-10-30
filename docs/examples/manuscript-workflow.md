# Survival And ML Manuscript Workflow

This tutorial shows the artifact-oriented pattern Fyron encourages for papers: cohort table, QC report, model table, figure, and manifest.

```python
from pathlib import Path

from fyron.datasets import make_classification_cohort, make_survival_cohort
from fyron import audit as fa
from fyron import ml
from fyron import preprocessing as fp
from fyron import reporting as fr
from fyron import validation as fv
from fyron.survival import plot_kaplan_meier

out = Path("results")
out.mkdir(exist_ok=True)

survival = make_survival_cohort(n=80, random_state=42)
km = plot_kaplan_meier(
    survival,
    duration_col="time",
    event_col="event",
    group_col="risk_group",
    at_risk_counts=True,
    save_path=out / "km.png",
)

X, y = make_classification_cohort(n=100, random_state=42)
feature_qc = fp.feature_matrix_report(X, y)
feature_qc.to_csv(out / "feature_qc.csv", index=False)

rf = ml.run_classification_pipeline(
    X,
    y,
    model="random_forest",
    n_estimators=100,
    random_state=42,
)

metric_ci = fv.bootstrap_classification_metrics(
    rf["y_test"],
    rf["y_pred"],
    rf["y_prob"],
    n_rounds=200,
    random_state=42,
)
metric_ci.to_csv(out / "metric_ci.csv", index=False)

model_table = fr.compare_models_table({"Random Forest": rf})
model_table.to_csv(out / "model_table.csv", index=False)

manifest = fa.analysis_run_manifest(
    title="Synthetic manuscript workflow",
    analysis_type="classification",
    outputs=[out / "km.png", out / "feature_qc.csv", out / "metric_ci.csv", out / "model_table.csv"],
    parameters={"random_state": 42, "model": "random_forest"},
    random_seed=42,
)
fa.write_manifest(manifest, out / "provenance.json")
```

The important habit is that every reported result has a matching saved artifact and an explicit parameter record.
