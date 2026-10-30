"""Synthetic, reproducible endpoint-to-validation workflow. No patient data."""

import argparse
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fyron.cohort import (
    build_time_to_event_endpoint, audit_time_to_event_endpoint,
    audit_cohort_join, join_cohort_tables,
)
from fyron.survival import fit_multivariate_cox, fit_weibull_aft, check_ph_assumptions
from fyron.validation import external_survival_validation
from fyron.plotting import plot_kaplan_meier


def run(output_dir):
    rng = np.random.default_rng(724)
    n = 240
    x = rng.normal(size=n)
    event_days = np.ceil(rng.exponential(500 * np.exp(-.4 * x)))
    start = pd.Timestamp("2020-01-01")
    frame = pd.DataFrame({
        "patient_id": np.arange(n + 1),
        "index_date": start,
        "event_date": start + pd.to_timedelta(np.r_[event_days, np.nan], unit="D"),
        "censor_date": start + pd.Timedelta(days=900),
        "x": np.r_[x, 0.0],
    })
    # Deliberately unresolved follow-up is reviewed, not counted as censoring.
    frame.loc[n, "censor_date"] = pd.NaT
    endpoint_options = dict(
        index_date_col="index_date", event_date_col="event_date",
        censor_date_col="censor_date", time_unit="days",
        administrative_censor_date=start + pd.Timedelta(days=730),
    )
    quality = audit_time_to_event_endpoint(frame, **endpoint_options)
    cohort = build_time_to_event_endpoint(
        frame.drop(columns="x"), **endpoint_options, require_endpoint=False,
    )
    cohort = cohort.loc[quality["rows"]["positive_duration_eligible"]].copy()
    features = frame[["patient_id", "x"]]
    join_quality = audit_cohort_join(features, cohort)
    cohort = join_cohort_tables(features, cohort)
    train, evaluation = cohort.iloc[:160].copy(), cohort.iloc[160:].copy()
    # Explicit complete-case demonstration; do not impute outcome columns.
    train.loc[train.index[:3], "x"] = np.nan
    cox = fit_multivariate_cox(train, "time", "event", covariates=["x"])
    aft = fit_weibull_aft(train, "time", "event", covariates=["x"])
    ph = check_ph_assumptions(cox["training_df"], cox["fitter"], show_plots=False)
    horizon = 365.0
    evaluation["risk"] = cox["fitter"].predict_partial_hazard(evaluation).to_numpy()
    survival = cox["fitter"].predict_survival_function(evaluation, times=[horizon])
    evaluation["event_probability"] = 1 - survival.iloc[0].to_numpy()
    validation = external_survival_validation(
        cox, evaluation, duration_col="time", event_col="event", risk_col="risk",
        prediction_col="event_probability", time_horizon=horizon,
        censoring_df=cox["training_df"],
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    quality["summary"].to_csv(output_dir / "endpoint-quality.csv", index=False)
    join_quality.to_csv(output_dir / "join-quality.csv", index=False)
    cox["results"].to_csv(output_dir / "cox.csv", index=False)
    aft["results"].to_csv(output_dir / "aft.csv", index=False)
    ph["summary"].to_csv(output_dir / "ph.csv", index=False)
    pd.DataFrame([validation["calibration"]]).to_csv(output_dir / "calibration.csv", index=False)
    km = plot_kaplan_meier(
        evaluation.assign(cohort="Evaluation"), "time", "event", group_col="cohort",
        xlabel="Follow-up (days)",
    )
    km.figure.savefig(output_dir / "evaluation-km.png", dpi=120)
    plt.close(km.figure)
    assert cox["n_used"] == aft["n_used"] == 157
    assert cox["n_excluded"] == aft["n_excluded"] == 3
    assert len(evaluation) == 80 and quality["rows"].missing_endpoint.sum() == 1
    assert np.isfinite(validation["concordance_index"])
    for filename in ("cox.csv", "aft.csv", "ph.csv", "calibration.csv", "endpoint-quality.csv",
                     "join-quality.csv", "evaluation-km.png"):
        assert (output_dir / filename).stat().st_size > 0
    logging.getLogger("fyron.example").info(
        "Training rows=%d excluded=%d evaluation rows=%d concordance=%.3f",
        cox["n_used"], cox["n_excluded"], len(evaluation), validation["concordance_index"],
    )
    return cox, aft, validation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    run(args.output_dir)
