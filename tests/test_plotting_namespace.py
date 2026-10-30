"""Tests for the fyron.plotting facade."""

from __future__ import annotations

import matplotlib.pyplot as plt

from fyron import ml
from fyron import plotting as fp
from fyron.datasets import make_survival_cohort


def test_plotting_namespace_exposes_ml_and_survival_plots() -> None:
    cohort = make_survival_cohort(n=12)
    km = fp.plot_kaplan_meier(cohort, "time", "event", group_col="risk_group")
    fig, _ = fp.plot_roc_curve([0, 1, 1, 0], [0.1, 0.8, 0.7, 0.2])

    assert km.figure is not None
    assert set(km.fitters)
    assert fp.plot_directional_ratio_rows is ml.plot_directional_ratio_rows
    assert fp.plot_volcano is ml.plot_volcano
    assert fp.plot_swimmer is ml.plot_swimmer
    assert fp.plot_raincloud is ml.plot_raincloud
    assert fp.plot_qq is ml.plot_qq
    assert fp.plot_reference_band_grid is ml.plot_reference_band_grid
    assert fp.plot_alluvial_flow is ml.plot_alluvial_flow
    assert fp.plot_binned_marker_heatmap is ml.plot_binned_marker_heatmap
    plt.close(km.figure)
    plt.close(fig)
