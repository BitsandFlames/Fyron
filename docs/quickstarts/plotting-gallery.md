# Quickstart: Plotting Gallery

Use this when you need to choose a manuscript figure style before adapting it to a real cohort.

## Install

```bash
uv add "fyron[ml,survival]"
```

## Browse The Gallery

Start with the [Visual Figure Gallery](../examples/visual-figure-gallery.md). Each figure is generated from deterministic synthetic data so you can copy the call shape safely.

Good first choices:

| Question | Start with |
| --- | --- |
| Survival by group | Kaplan-Meier or KM reference bands |
| Biomarker distribution | histogram, density, raincloud, grouped boxplot |
| Clinical reference intervals | reference band grid |
| Classifier performance | ROC, PR, calibration, decision curve |
| Feature selection or explainability | feature importance, stability selection, signed feature weights |

## Use A Figure Function

```python
import pandas as pd
from fyron import plotting as fp

df = pd.DataFrame(
    {
        "age": [54, 58, 61, 69, 73, 77],
        "group": ["A", "A", "B", "B", "B", "A"],
        "marker": [1.2, 1.4, 2.1, 2.5, 2.8, 1.9],
    }
)

fig, ax = fp.plot_grouped_boxplot(
    df,
    x="group",
    y="marker",
    ylabel="Marker value",
    title="Synthetic biomarker distribution",
)
```

## Next Steps

- Read [Clinical Plotting](../modules/plotting.md) for parameters shared across plot helpers.
- Read [Colors And Styles](../colors.md) for palettes and publication styling.
