# Fyron Plotting Agent Notes

Use `fyron.plotting` for clinical and manuscript figures. Plot functions return Matplotlib objects, usually `(fig, ax)` or `(fig, ax, table)`.

Common choices:

| Need | Function family |
| --- | --- |
| Survival curves | Kaplan-Meier helpers |
| Binary classifier performance | ROC, PR, calibration, confusion, decision curves |
| Clinical group comparisons | grouped bars, boxplots, rainclouds |
| Reference ranges | `plot_reference_band_grid` |
| Feature screening | volcano plots |
| Patient timelines | swimmer plots |
| OR/HR rows | `plot_directional_ratio_rows` |
| Patient-feature marker panels | binned marker heatmaps |
| Transitions or attrition | alluvial flow |
| Segmentation QC | segmentation and image QC plots |

Directional ratio rows:

```python
from fyron import plotting as fp

fig, ax = fp.plot_directional_ratio_rows(
    data=ratios,
    feature_col="feature",
    ratio_col="odds_ratio",
    ci_low_col="ci_low",
    ci_high_col="ci_high",
    p_value_col="p_value",
    ratio_label="Odds ratio",
)
```

Reference band grids:

```python
from fyron import plotting as fp

fig, axes = fp.plot_reference_band_grid(
    data=reference_bands,
    x="age",
    lower_col="lower",
    upper_col="upper",
    band_col="band",
    col="feature",
    row="sex",
    band_preset="sd",
    line_df=trend,
    line_y="value",
)
```

Rules:

- Use synthetic labels in examples.
- State whether values are odds ratios, hazard ratios, or another effect measure.
- For reference bands, make clear that Fyron visualizes precomputed intervals and does not estimate the normative model.
- Keep confidence intervals and p-values optional, but label them clearly when present.
- Prefer colorblind-safe palettes and readable figure sizes.
- Save publication outputs as SVG plus PNG when useful.
