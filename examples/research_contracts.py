"""Synthetic preprocessing, phenotype, imaging, and provenance workflow."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from fyron import audit, phenotyping, preprocessing
from fyron.imaging.segmentation import volume_difference


def run(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    train = pd.DataFrame({"age": [40, 60, None], "site": ["A", "A", "B"]}, index=[2, 7, 9])
    evaluation = pd.DataFrame({"age": [None, 90], "site": ["unseen", None]}, index=[14, 12])
    imputer = preprocessing.fit_imputer(
        train, numeric=["age"], categorical=["site"],
        strategy_categorical="constant", add_missing_indicators=True,
    )
    train_imp = preprocessing.apply_imputer(train, imputer)
    evaluation_imp = preprocessing.apply_imputer(evaluation, imputer)
    encoder = preprocessing.fit_categorical_encoder(train_imp, columns=["site"], rare_min_count=2)
    x_train = preprocessing.apply_categorical_encoder(train_imp, encoder)
    x_evaluation = preprocessing.apply_categorical_encoder(evaluation_imp, encoder)
    feature_columns = list(x_train.columns)
    x_evaluation = x_evaluation.loc[:, feature_columns]
    assert x_evaluation.loc[14, "age"] == 50
    assert x_evaluation.index.tolist() == [14, 12]
    assert x_train.columns.equals(x_evaluation.columns)
    assert x_evaluation["site____rare__"].tolist() == [1, 1]
    assert x_evaluation["age_was_missing"].tolist() == [1, 0]
    x_train.to_csv(output_dir / "training_features.csv", index=False)
    x_evaluation.to_csv(output_dir / "evaluation_features.csv", index=False)

    population = pd.DataFrame({"patient_id": ["synthetic-a", "synthetic-b", "synthetic-c"]})
    records = pd.DataFrame({
        "patient_id": ["synthetic-a", "synthetic-a", "synthetic-b", "synthetic-c"],
        "code": ["DEMO", "DEMO", "DEMO.1", "DEMO"],
        "recorded": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-04", "2021-01-01"]),
    })
    # The eligibility window is explicit and applied before evidence aggregation.
    eligible = records.loc[records["recorded"].between("2020-01-01", "2020-12-31")]
    evidence = phenotyping.define_code_phenotype(
        eligible, "code", ["DEMO"], date_col="recorded", phenotype_name="recorded_evidence",
    )
    cohort = population.merge(evidence, on="patient_id", how="left", validate="one_to_one")
    cohort["recorded_evidence"] = cohort["recorded_evidence"].eq(True)
    cohort["interpretation"] = np.where(cohort["recorded_evidence"], "matching_evidence", "no_matching_evidence")
    summary = phenotyping.phenotype_summary(cohort, "recorded_evidence")
    assert summary.loc[0, "n_patients"] == 3
    assert summary.loc[0, "n_phenotype"] == 1
    assert evidence.loc[0, "evidence_count"] == 2
    cohort.to_csv(output_dir / "phenotype_evidence.csv", index=False)

    reference, predicted = np.zeros((3, 3, 3)), np.zeros((3, 3, 3))
    reference[0, 0, 0] = 1
    predicted[0:2, 0, 0] = 1
    metrics = volume_difference(reference, predicted, spacing=(4, 2, 1))
    assert metrics["true_volume_ml"] == .008
    assert metrics["pred_volume_ml"] == .016
    pd.DataFrame([metrics]).to_csv(output_dir / "mask_volumes.csv", index=False)

    internal = audit.create_provenance_manifest(
        title="Synthetic module contracts",
        inputs=[output_dir / "training_features.csv"],
        outputs=[output_dir / "evaluation_features.csv"],
        parameters={"age_imputation": "training_median", "spacing_zyx_mm": [4, 2, 1]},
        notes="Internal record: review before sharing.",
    )
    audit.write_manifest(internal, output_dir / "internal_manifest.json")
    # Construct a separate, reviewed summary; never copy arbitrary fields.
    publication_summary = {
        "fyron_version": internal["fyron_version"],
        "data_source": "synthetic",
        "preprocessing": "Training-only median imputation and fitted categorical encoding",
        "volume_spacing_zyx_mm": [4, 2, 1],
    }
    audit.write_manifest(publication_summary, output_dir / "publication_summary.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    run(parser.parse_args().output_dir)
