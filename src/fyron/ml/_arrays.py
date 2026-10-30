"""Internal helpers for array/DataFrame coercion."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

ArrayLikeInput = ArrayLike | pd.DataFrame | pd.Series


def to_numpy_2d(X: ArrayLikeInput) -> np.ndarray:
    """Coerce features to a 2-D float-compatible ndarray."""
    if isinstance(X, pd.DataFrame):
        return X.to_numpy()
    arr = np.asarray(X)
    if arr.ndim == 1:
        return arr.reshape(-1, 1)
    return arr


def to_numpy_1d(y: ArrayLikeInput) -> np.ndarray:
    """Coerce target to a 1-D ndarray."""
    if isinstance(y, pd.Series):
        return y.to_numpy()
    arr = np.asarray(y)
    return arr.ravel()


def feature_names(X: ArrayLikeInput) -> list[str] | None:
    if isinstance(X, pd.DataFrame):
        return list(X.columns)
    return None


def n_classes(y: np.ndarray) -> int:
    return int(len(np.unique(y)))


def is_binary(y: np.ndarray) -> bool:
    return n_classes(y) == 2


def resolve_pos_label(y: np.ndarray, pos_label: Any | None) -> Any:
    if pos_label is not None:
        return pos_label
    unique = np.unique(y)
    if len(unique) != 2:
        raise ValueError("pos_label is required for non-binary targets.")
    return max(unique.tolist(), key=lambda v: (isinstance(v, str), v))


def align_feature_names(
    names: Sequence[str] | None,
    n_features: int,
    *,
    prefix: str = "feature",
) -> list[str]:
    if names is not None and len(names) == n_features:
        return list(names)
    return [f"{prefix}_{i}" for i in range(n_features)]
