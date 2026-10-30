# Filled KDE Plot

Use `plot_filled_kde` when two continuous variables form clinically meaningful clusters. It is useful for acquisition timing versus scan duration, imaging feature pairs, paired lab markers, or quality-control summaries where a scatter plot becomes too dense.

The API mirrors the familiar Seaborn shape:

```python
import numpy as np
import pandas as pd

from fyron import plotting as fp

rng = np.random.default_rng(42)

short = pd.DataFrame(
    {
        "waiting": rng.normal(58, 5.5, 90),
        "duration": rng.normal(2.2, 0.35, 90),
        "kind": "short",
    }
)
long = pd.DataFrame(
    {
        "waiting": rng.normal(80, 7.0, 110),
        "duration": rng.normal(4.1, 0.45, 110),
        "kind": "long",
    }
)
geyser_like = pd.concat([short, long], ignore_index=True)

fig, ax = fp.plot_filled_kde(
    data=geyser_like,
    x="waiting",
    y="duration",
    hue="kind",
    fill=True,
    title="Waiting time and duration density",
    xlabel="Waiting time",
    ylabel="Duration",
    palette="okabe_ito",
)
fig.savefig("filled_kde.svg", bbox_inches="tight")
```

## Parameters To Tune

| Parameter | Use |
| --- | --- |
| `hue` | draw separate filled KDE contours for each group |
| `fill` | switch between filled contours and contour lines |
| `levels` | control how many density bands are drawn |
| `thresh` | hide very low-density outer regions |
| `bandwidth` | smooth more or less; pass one value or `(x_bandwidth, y_bandwidth)` |
| `show_points` | overlay source points for small and medium cohorts |

## Interpretation

Filled KDE plots summarize where two variables are jointly dense. They are not counts, and they can hide small outlier clusters if the bandwidth is too large. For final figures, check the result against a scatter plot or set `show_points=True` during review.

For one-dimensional distributions, use `plot_density`. For absolute bin counts, use `plot_histogram`.
