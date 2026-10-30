"""Train/test splitting utilities."""

from __future__ import annotations

from typing import Any, Tuple, Union

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from sklearn.model_selection import train_test_split as sk_train_test_split

from fyron.ml._arrays import ArrayLikeInput, to_numpy_1d, to_numpy_2d

SplitReturn = Tuple[
    Union[np.ndarray, pd.DataFrame],
    Union[np.ndarray, pd.DataFrame],
    Union[np.ndarray, pd.Series],
    Union[np.ndarray, pd.Series],
]


def train_test_split_data(
    X: ArrayLikeInput,
    y: ArrayLikeInput,
    *,
    test_size: float = 0.2,
    stratify: bool = True,
    random_state: int = 42,
) -> SplitReturn:
    """Split features and target into train and test sets.

    Accepts pandas DataFrames/Series or NumPy arrays. When the inputs are
    pandas objects, the returned splits preserve their types.

    Parameters
    ----------
    X
        Feature matrix.
    y
        Target vector.
    test_size
        Fraction of samples held out for testing.
    stratify
        If True, stratify on ``y``.
    random_state
        Random seed passed to scikit-learn.

    Returns
    -------
    X_train, X_test, y_train, y_test

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.ml import train_test_split_data
    >>> X = pd.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]})
    >>> y = pd.Series([0, 0, 1, 1])
    >>> X_train, X_test, y_train, y_test = train_test_split_data(
    ...     X, y, test_size=0.25, stratify=True, random_state=0
    ... )
    """
    is_x_df = isinstance(X, pd.DataFrame)
    is_y_series = isinstance(y, pd.Series)
    X_arr = to_numpy_2d(X)
    y_arr = to_numpy_1d(y)
    stratify_y = y_arr if stratify else None
    X_train, X_test, y_train, y_test = sk_train_test_split(
        X_arr,
        y_arr,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_y,
    )
    if is_x_df:
        cols = list(X.columns)  # type: ignore[union-attr]
        X_train = pd.DataFrame(X_train, columns=cols)
        X_test = pd.DataFrame(X_test, columns=cols)
    if is_y_series:
        name = y.name if getattr(y, "name", None) is not None else "target"  # type: ignore[union-attr]
        y_train = pd.Series(y_train, name=name)
        y_test = pd.Series(y_test, name=name)
    return X_train, X_test, y_train, y_test
