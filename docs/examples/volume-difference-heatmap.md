# Volume Difference Heatmap

This example compares two aligned CT or MR volumes with a three-panel slice figure: volume A, volume B, and a zero-centered difference map. Use it for visual QC of generated images, reconstruction variants, explicitly resampled follow-up images, or model outputs.

## Synthetic CT Example

```python
import numpy as np

from fyron.visualization import plot_volume_difference_heatmap

z, y, x = 12, 64, 64
yy, xx = np.mgrid[:y, :x]
body = ((yy - 32) ** 2 + (xx - 32) ** 2) < 24**2

reference = np.full((z, y, x), -900.0, dtype=np.float32)
comparison = reference.copy()

reference[:, body] = 40.0
comparison[:, body] = 25.0
comparison[6, 28:38, 28:38] += 80.0

fig, axes, diff_table = plot_volume_difference_heatmap(
    reference,
    comparison,
    data_type="ct_hu",
    orientation="axial",
    slice_indices=[4, 6, 8],
    label_a="Reference CT",
    label_b="Comparison CT",
    window_center=40,
    window_width=400,
    title="Synthetic CT difference heatmap",
    save_path="outputs/ct_difference_heatmap.png",
)

diff_table.to_csv("outputs/ct_difference_summary.csv", index=False)
```

The difference table is useful for QC logs and supplements:

| Column | Meaning |
| --- | --- |
| `slice_index` | rendered slice index along the chosen orientation |
| `mean_difference` | mean of `Volume A - Volume B` |
| `mean_absolute_difference` | average absolute difference |
| `rmse` | root mean squared difference |
| `diff_vmax` | symmetric color limit used for the difference panel |

## Stored CT Values

If CT values are stored as unsigned integers, convert them to HU inside the plotting call:

```python
fig, axes, diff_table = plot_volume_difference_heatmap(
    stored_a,
    stored_b,
    data_type="ct_uint16",
    rescale_slope=1.0,
    rescale_intercept=-1024.0,
    slice_fraction=0.5,
)
```

## MR Example

MR intensities are protocol-dependent. Fyron normalizes each volume before computing a normalized-intensity difference.

```python
rng = np.random.default_rng(42)
mr_a = rng.normal(loc=100, scale=20, size=(10, 48, 48)).astype(np.float32)
mr_b = mr_a.copy()
mr_b[:, 20:30, 20:30] *= 0.85

fig, axes, diff_table = plot_volume_difference_heatmap(
    mr_a,
    mr_b,
    data_type="mr",
    mr_normalization="percentile",
    mr_percentile=99,
    orientation="coronal",
    slice_index=24,
    label_a="MR A",
    label_b="MR B",
    title="MR normalized difference",
)
```

## Geometry Rule

The function is strict: shapes must match, and NIfTI/SimpleITK geometry must match when both inputs carry geometry. If the volumes need registration or resampling, do that explicitly before plotting and save the resampling parameters in your audit manifest.

## Related Modules

- [BOA Visualization](../modules/visualization.md) for the full visualization guide.
- [Imaging](../modules/imaging.md) for NIfTI I/O and CT/MR normalization.
- [Audit & Provenance](../modules/audit.md) for recording source files, parameters, and generated artifacts.
