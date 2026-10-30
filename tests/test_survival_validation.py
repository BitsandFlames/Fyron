"""Tests for survival validation helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from fyron.validation import (
    bootstrap_concordance_index,
    brier_score_at_time,
    external_survival_validation,
    survival_calibration_at_time,
    time_dependent_auc_table,
)


def test_survival_validation_tables() -> None:
    pytest.importorskip("sksurv")
    df = pd.DataFrame(
        {
            "time": [5, 10, 15, 20, 25, 30],
            "event": [1, 1, 0, 1, 0, 0],
            "risk": [0.9, 0.8, 0.4, 0.5, 0.2, 0.1],
            "pred": [0.7, 0.6, 0.3, 0.4, 0.2, 0.1],
        }
    )
    boot = bootstrap_concordance_index(df, "time", "event", "risk", n_rounds=10)
    assert 0 <= boot["estimate"] <= 1

    summary, table = survival_calibration_at_time(df, "time", "event", "pred", 18, n_bins=3)
    assert "brier_score" in summary
    assert not table.empty

    brier = brier_score_at_time(df, "time", "event", "pred", 18)
    assert brier["brier_score"] >= 0

    external = external_survival_validation({}, df, duration_col="time", event_col="event", risk_col="risk", prediction_col="pred", time_horizon=12)
    assert "concordance_index" in external


def test_time_dependent_auc_optional_message() -> None:
    pytest.importorskip("sksurv")
    df = pd.DataFrame(
        {
            "time": [5, 10, 15, 20, 25, 30, 35, 40],
            "event": [1, 1, 0, 1, 0, 0, 1, 0],
            "risk": [0.9, 0.8, 0.4, 0.6, 0.2, 0.1, 0.7, 0.3],
        }
    )
    auc = time_dependent_auc_table(
        df,
        df,
        duration_col="time",
        event_col="event",
        risk_col="risk",
        times=[8, 18],
    )
    assert list(auc["time"]) == [8, 18]
    assert "mean_auc" in auc.columns


def test_time_dependent_auc_requires_sksurv_when_missing(monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("sksurv"):
            raise ImportError("no sksurv")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="fyron\\[survival-ml\\]"):
        time_dependent_auc_table(
            pd.DataFrame({"time": [1], "event": [1], "risk": [0.5]}),
            pd.DataFrame({"time": [1], "event": [1], "risk": [0.5]}),
            duration_col="time",
            event_col="event",
            risk_col="risk",
            times=[1],
        )
