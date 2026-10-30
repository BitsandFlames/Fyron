"""Physical spacing validation shared by imaging summaries and metrics."""

import numpy as np


def validate_spacing(spacing, ndim):
    values = np.asarray(spacing, dtype=float)
    if values.shape != (ndim,) or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("spacing must contain one finite positive value per image axis.")
    return values


def voxel_volume_ml(spacing, ndim):
    if spacing is None or ndim != 3:
        raise ValueError("Physical volumes require 3D masks and explicit spacing in millimetres.")
    return float(np.prod(validate_spacing(spacing, ndim)) / 1000.0)
