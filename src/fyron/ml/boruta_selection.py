"""Boruta feature selection (optional dependency)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from fyron.ml._arrays import ArrayLikeInput, align_feature_names, to_numpy_1d, to_numpy_2d

BorutaResult = dict[str, Any]


def _import_boruta() -> Any:
    """Import BorutaPy, applying a NumPy 1.26+ compatibility shim when needed."""
    import numpy as _np

    for _name, _type in (("int", int), ("float", float), ("bool", bool)):
        if not hasattr(_np, _name):
            setattr(_np, _name, _type)
    try:
        from boruta import BorutaPy
    except ImportError as exc:
        raise ImportError(
            "Boruta feature selection requires the Boruta package. "
            'Install with: uv add "fyron[boruta]"'
        ) from exc
    return BorutaPy


def run_boruta_feature_selection(
    X: ArrayLikeInput,
    y: ArrayLikeInput,
    estimator: Any | None = None,
    *,
    class_weight: str | dict[Any, float] | None = "balanced",
    max_iter: int = 100,
    random_state: int = 42,
) -> BorutaResult:
    """Run Boruta all-relevant feature selection.

    Requires the optional ``boruta`` extra. Pass a pandas DataFrame for ``X`` to
    preserve feature names in the output tables.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.ml import run_boruta_feature_selection
    >>> X = pd.DataFrame({"a": range(40), "b": range(40)})
    >>> y = [0] * 20 + [1] * 20
    >>> out = run_boruta_feature_selection(X, y, max_iter=20, random_state=0)
    >>> "selected_features" in out
    True
    """
    BorutaPy = _import_boruta()
    X_arr = to_numpy_2d(X)
    y_arr = to_numpy_1d(y)
    names = align_feature_names(
        list(X.columns) if isinstance(X, pd.DataFrame) else None,
        X_arr.shape[1],
    )

    if estimator is None:
        estimator = RandomForestClassifier(
            n_estimators=100,
            class_weight=class_weight,
            random_state=random_state,
            n_jobs=-1,
        )
    selector = BorutaPy(estimator, max_iter=max_iter, random_state=random_state)
    selector.fit(X_arr, y_arr)

    support = selector.support_
    ranking = getattr(selector, "ranking_", np.ones(len(names), dtype=int))
    tentative_mask = getattr(selector, "support_weak_", np.zeros(len(names), dtype=bool))

    selected = [names[i] for i, ok in enumerate(support) if ok]
    tentative = [names[i] for i, ok in enumerate(tentative_mask) if ok and not support[i]]
    rejected = [names[i] for i, ok in enumerate(support) if not ok and names[i] not in tentative]

    ranking_df = pd.DataFrame(
        {
            "feature": names,
            "ranking": ranking,
            "selected": support,
            "tentative": tentative_mask,
        }
    ).sort_values(["ranking", "feature"])

    return {
        "selected_features": selected,
        "rejected_features": rejected,
        "tentative_features": tentative,
        "ranking_df": ranking_df,
        "selector": selector,
        "transform": lambda data: selector.transform(to_numpy_2d(data)),
    }
