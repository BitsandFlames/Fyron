# Manuscript Plotting Workflow

This tutorial uses synthetic clinical rows to show the new Matplotlib-native plotting workflow: distributions, statistical annotations, grouped correlations, Kaplan-Meier curves with at-risk counts, and Cox hazard-ratio forest plots.

## Synthetic Cohort

```python
import numpy as np
import pandas as pd

from fyron import plotting as fp
from fyron.survival import fit_multivariate_cox

rng = np.random.default_rng(42)
n = 120
cohort = pd.DataFrame(
    {
        "patient_id": [f"P{i:03d}" for i in range(n)],
        "risk_group": np.where(np.arange(n) < 60, "Low", "High"),
        "sex": rng.choice(["Female", "Male"], size=n),
        "age": rng.normal(66, 8, size=n),
        "l3_sma_cm2": np.r_[rng.normal(48, 7, 60), rng.normal(39, 7, 60)],
        "risk_score": np.r_[rng.normal(0.32, 0.10, 60), rng.normal(0.68, 0.12, 60)],
        "time": rng.exponential(24, size=n) + 2,
        "event": rng.binomial(1, np.r_[np.repeat(0.35, 60), np.repeat(0.62, 60)]),
    }
)
```

## Palette Setup

Start by choosing a named scientific palette. Use qualitative palettes for groups, sequential palettes for magnitude, and diverging palettes for centered values such as correlations.

```python
fp.set_plot_style(style="paper", palette="okabe_ito")

fig, ax = fp.preview_palette("okabe_ito")
fig.savefig("figures/okabe_ito_palette.svg", bbox_inches="tight")

palette_audit = fp.palette_luminance_table("okabe_ito")
palette_contrast = fp.palette_grayscale_contrast("okabe_ito")
palette_audit.to_csv("tables/okabe_ito_luminance.csv", index=False)
palette_contrast.to_csv("tables/okabe_ito_grayscale_contrast.csv", index=False)
```

## Distribution Figures With Statistics

```python
fig, ax = fp.plot_histogram(
    cohort,
    x="risk_score",
    hue="risk_group",
    stat="percent",
    multiple="dodge",
    palette="okabe_ito",
    title="Risk score distribution",
)
fig.savefig("figures/risk_score_histogram.svg", bbox_inches="tight")

fig, ax = fp.plot_density(
    cohort,
    x="risk_score",
    hue="risk_group",
    rug=True,
    palette="okabe_ito",
    title="Risk score density",
)
fig.savefig("figures/risk_score_density.svg", bbox_inches="tight")

fig, ax, stats = fp.plot_grouped_boxplot(
    cohort,
    x="risk_group",
    y="l3_sma_cm2",
    comparisons=[("Low", "High")],
    stat_test="mannwhitney",
    p_adjust="fdr_bh",
    palette="okabe_ito",
    return_stats=True,
    title="L3 muscle area by risk group",
)
stats.to_csv("tables/l3_sma_boxplot_tests.csv", index=False)
fig.savefig("figures/l3_sma_boxplot.svg", bbox_inches="tight")

fig, ax, stats = fp.plot_swarmplot(
    cohort,
    x="risk_group",
    y="risk_score",
    hue="sex",
    comparisons=[(("High", "Female"), ("High", "Male"))],
    palette="okabe_ito",
    return_stats=True,
    title="Risk score by group and sex",
)
stats.to_csv("tables/risk_score_swarm_tests.csv", index=False)
fig.savefig("figures/risk_score_swarm.svg", bbox_inches="tight")
```

## Correlation Figures

```python
fig, ax, corr = fp.plot_correlation_heatmap(
    cohort,
    columns=["age", "l3_sma_cm2", "risk_score"],
    annotate_significance=True,
    p_adjust="fdr_bh",
    mask_upper=True,
    cmap="fyron_diverging_blue_red",
    title="Feature correlation",
)
corr.to_csv("tables/feature_correlation.csv")
fig.savefig("figures/feature_correlation.svg", bbox_inches="tight")

fig, axes, corr_long = fp.plot_grouped_correlation_heatmaps(
    cohort,
    group_col="risk_group",
    columns=["age", "l3_sma_cm2", "risk_score"],
    annotate_significance=True,
    cmap="fyron_diverging_teal_orange",
    title="Feature correlation by risk group",
)
corr_long.to_csv("tables/grouped_feature_correlation.csv", index=False)
fig.savefig("figures/grouped_feature_correlation.svg", bbox_inches="tight")
```

## Survival Figures

```python
km = fp.plot_kaplan_meier(
    cohort,
    duration_col="time",
    event_col="event",
    group_col="risk_group",
    at_risk_counts=True,
    show_censors=True,
    annotate_logrank=True,
    xlim=(0, 60),
    palette="okabe_ito",
    title="Overall survival by risk group",
)
km.figure.savefig("figures/km_risk_group.svg", bbox_inches="tight")

cox = fit_multivariate_cox(
    cohort,
    duration_col="time",
    event_col="event",
    covariates=["age", "risk_score"],
)

fig, ax = fp.plot_hazard_ratios(
    cox,
    title="Cox model hazard ratios",
)
fig.savefig("figures/cox_hazard_ratios.svg", bbox_inches="tight")
```

## What To Save

Save both the figures and their computed tables:

| Artifact | Why |
| --- | --- |
| `*_tests.csv` | Documents exact pairwise tests, p-values, correction method, and annotations. |
| `okabe_ito_luminance.csv` | Documents palette luminance and recommended text colors. |
| `okabe_ito_grayscale_contrast.csv` | Documents adjacent grayscale differences for print checks. |
| `feature_correlation.csv` | Preserves the numeric correlation matrix behind the heatmap. |
| `grouped_feature_correlation.csv` | Preserves subgroup correlation values. |
| `km.logrank` | Stores log-rank test details and group counts. |
| Cox result table | Stores hazard ratios, confidence intervals, and p-values behind the forest plot. |
