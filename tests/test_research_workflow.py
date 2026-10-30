from __future__ import annotations

from pathlib import Path

from fyron import audit as fa
from fyron import descriptive as fd
from fyron import ml
from fyron import preprocessing as fp
from fyron import reporting as fr
from fyron import validation as fv
from fyron.datasets import make_classification_cohort, make_survival_cohort
from fyron.survival import plot_kaplan_meier


def test_synthetic_research_workflow_writes_review_artifacts(tmp_path: Path) -> None:
    survival = make_survival_cohort(n=60, random_state=4)
    km_path = tmp_path / "km.png"
    km = plot_kaplan_meier(
        survival,
        duration_col="time",
        event_col="event",
        group_col="risk_group",
        save_path=km_path,
    )
    assert km_path.is_file()
    assert km.n_per_group

    table_one = fd.create_table_one(
        survival,
        group_col="risk_group",
        numeric=["time"],
        categorical=["event"],
    )
    table_one_path = tmp_path / "table_one.csv"
    table_one.to_csv(table_one_path, index=False)

    X, y = make_classification_cohort(n=80, random_state=4)
    feature_qc = fp.feature_matrix_report(X, y)
    assert not feature_qc.empty

    result = ml.run_classification_pipeline(
        X,
        y,
        model="random_forest",
        n_estimators=20,
        random_state=4,
    )
    metric_ci = fv.bootstrap_classification_metrics(
        result["y_test"],
        result["y_pred"],
        result["y_prob"],
        n_rounds=20,
        random_state=4,
    )
    assert "auc" in set(metric_ci["metric"])

    model_table = fr.compare_models_table({"Random Forest": result})
    model_path = tmp_path / "model_table.csv"
    model_table.to_csv(model_path, index=False)

    manifest = fa.analysis_run_manifest(
        title="Synthetic research workflow",
        analysis_type="classification",
        inputs=[table_one_path],
        outputs=[km_path, model_path],
        parameters={"model": "random_forest"},
        random_seed=4,
    )
    manifest_path = fa.write_manifest(manifest, tmp_path / "provenance.json")
    assert manifest_path.is_file()
    assert manifest["parameters"]["random_seed"] == 4
