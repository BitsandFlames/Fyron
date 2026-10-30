"""Gradient survival boosting helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fyron._survival_data import outcome_arrays, concordance
from numpy.typing import ArrayLike

ArrayLikeInput = ArrayLike | pd.DataFrame | pd.Series

SurvivalBoostingResult = dict[str, Any]


def _structured_survival_array(duration: ArrayLike, event: ArrayLike) -> Any:
    from fyron.ml._arrays import to_numpy_1d
    try:
        from sksurv.util import Surv
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Gradient survival boosting requires scikit-survival. "
            'Install with: uv add "fyron[survival-ml]"'
        ) from exc

    duration_arr, event_arr = outcome_arrays(to_numpy_1d(duration), to_numpy_1d(event))
    return Surv.from_arrays(event=event_arr, time=duration_arr)


def _concordance_index(duration: ArrayLike, event: ArrayLike, risk_score: ArrayLike) -> float:
    from fyron.ml._arrays import to_numpy_1d
    return concordance(to_numpy_1d(duration), to_numpy_1d(event), to_numpy_1d(risk_score))


def train_gradient_survival_boosting(
    X_train: ArrayLikeInput,
    duration_train: ArrayLike,
    event_train: ArrayLike,
    X_test: ArrayLikeInput | None = None,
    duration_test: ArrayLike | None = None,
    event_test: ArrayLike | None = None,
    *,
    random_state: int = 42,
    **model_params: Any,
) -> SurvivalBoostingResult:
    """Train a gradient boosting survival model.

    This wraps :class:`sksurv.ensemble.GradientBoostingSurvivalAnalysis` for
    right-censored clinical outcomes. Higher predicted scores indicate higher
    event risk. For ``squared`` and ``ipcwls`` losses, returned risk scores are
    negated time predictions; the fitted model's own predictions are unchanged.

    Parameters
    ----------
    X_train
        Feature matrix.
    duration_train, event_train
        Survival time and event indicator for the training set.
    X_test, duration_test, event_test
        Optional held-out data. When supplied, the returned risk scores and
        concordance index are computed on this set; otherwise in-sample scores
        are returned.
    random_state
        Random seed passed to the estimator.
    **model_params
        Additional parameters passed to
        ``GradientBoostingSurvivalAnalysis``.

    Returns
    -------
    dict
        ``model``, ``risk_score``, ``concordance_index``, ``train_concordance_index``,
        and the structured survival arrays used for fitting/evaluation.

    Examples
    --------
    >>> import pytest
    >>> pytest.importorskip("sksurv")
    >>> from fyron.survival import train_gradient_survival_boosting
    >>> out = train_gradient_survival_boosting(
    ...     [[0.0], [1.0], [2.0], [3.0], [4.0]],
    ...     [5, 4, 3, 2, 1],
    ...     [0, 1, 1, 1, 1],
    ...     n_estimators=5,
    ... )
    >>> "concordance_index" in out
    True
    """
    try:
        from sksurv.ensemble import GradientBoostingSurvivalAnalysis
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "train_gradient_survival_boosting requires scikit-survival. "
            'Install with: uv add "fyron[survival-ml]"'
        ) from exc

    from fyron.ml._arrays import to_numpy_2d

    supplied = [X_test is not None, duration_test is not None, event_test is not None]
    if any(supplied) and not all(supplied):
        raise ValueError("X_test, duration_test and event_test must be supplied together.")
    y_train_struct = _structured_survival_array(duration_train, event_train)
    if len(to_numpy_2d(X_train)) != len(y_train_struct):
        raise ValueError("X_train and survival outcomes must have the same length.")
    if all(supplied):
        y_test_struct = _structured_survival_array(duration_test, event_test)
        if len(to_numpy_2d(X_test)) != len(y_test_struct):
            raise ValueError("X_test and survival outcomes must have the same length.")
    params = dict(model_params)
    params.setdefault("random_state", random_state)
    model = GradientBoostingSurvivalAnalysis(**params)
    model.fit(to_numpy_2d(X_train), y_train_struct)

    direction = 1.0 if model.loss == "coxph" else -1.0
    train_risk = direction * model.predict(to_numpy_2d(X_train))
    train_c_index = _concordance_index(duration_train, event_train, train_risk)

    has_test = X_test is not None
    if has_test and (duration_test is None or event_test is None):
        raise ValueError("duration_test and event_test are required when X_test is provided.")

    if has_test:
        assert X_test is not None
        assert duration_test is not None
        assert event_test is not None
        eval_X = X_test
        eval_duration = duration_test
        eval_event = event_test
        y_eval_struct = _structured_survival_array(duration_test, event_test)
    else:
        eval_X = X_train
        eval_duration = duration_train
        eval_event = event_train
        y_eval_struct = y_train_struct

    risk_score = direction * model.predict(to_numpy_2d(eval_X))
    c_index = _concordance_index(eval_duration, eval_event, risk_score)

    return {
        "model": model,
        "risk_score": risk_score,
        "concordance_index": c_index,
        "train_risk_score": train_risk,
        "train_concordance_index": train_c_index,
        "y_train": y_train_struct,
        "y_eval": y_eval_struct,
    }
