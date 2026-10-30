"""Hyperparameter search utilities."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from fyron.ml._arrays import ArrayLikeInput, to_numpy_1d, to_numpy_2d
from fyron.ml.metrics import calculate_classification_metrics
from fyron.ml.training import _predict_proba_positive

SearchResult = dict[str, Any]


def grid_search_model(
    estimator: Any,
    param_grid: dict[str, Any],
    X_train: ArrayLikeInput,
    y_train: ArrayLikeInput,
    X_val: ArrayLikeInput | None = None,
    y_val: ArrayLikeInput | None = None,
    *,
    scoring: str = "roc_auc",
    cv: int = 5,
    n_jobs: int = -1,
    refit: bool = True,
    random_state: int = 42,
    pos_label: Any | None = None,
) -> SearchResult:
    """Run :class:`~sklearn.model_selection.GridSearchCV` with stratified folds.

    Examples
    --------
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from fyron.ml import grid_search_model
    >>> gs = grid_search_model(
    ...     RandomForestClassifier(random_state=0),
    ...     {"n_estimators": [5, 10]},
    ...     [[0], [1], [2], [3], [4], [5]],
    ...     [0, 0, 0, 1, 1, 1],
    ...     cv=2,
    ... )
    >>> "best_estimator" in gs
    True
    """
    X_arr = to_numpy_2d(X_train)
    y_arr = to_numpy_1d(y_train)
    cv_splitter = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
    search = GridSearchCV(
        estimator,
        param_grid,
        scoring=scoring,
        cv=cv_splitter,
        n_jobs=n_jobs,
        refit=refit,
    )
    search.fit(X_arr, y_arr)
    result: SearchResult = {
        "best_estimator": search.best_estimator_,
        "best_params": search.best_params_,
        "best_score": float(search.best_score_),
        "cv_results_df": pd.DataFrame(search.cv_results_),
        "search": search,
    }
    if X_val is not None and y_val is not None:
        model = search.best_estimator_
        y_pred = model.predict(to_numpy_2d(X_val))
        y_prob = _predict_proba_positive(model, X_val, pos_label)
        result["val_metrics"] = calculate_classification_metrics(y_val, y_pred, y_prob, pos_label=pos_label)
    return result
