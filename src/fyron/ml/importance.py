"""Feature importance extraction and plotting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from fyron.ml._arrays import align_feature_names
from fyron.ml.plots import plot_feature_importance as _plot_importance_df


def get_feature_importance(
    model: Any,
    feature_names: list[str] | None = None,
) -> pd.DataFrame:
    """Extract sorted feature importances from a tree-based model.

    Supports :class:`~sklearn.ensemble.RandomForestClassifier` and
    :class:`xgboost.XGBClassifier`.

    Examples
    --------
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from fyron.ml import get_feature_importance
    >>> clf = RandomForestClassifier(n_estimators=5, random_state=0)
    >>> clf.fit([[0], [1], [2], [3]], [0, 0, 1, 1])
    >>> df = get_feature_importance(clf, ["x"])
    >>> list(df.columns) == ["feature", "importance"]
    True
    """
    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_, dtype=float)
    elif hasattr(model, "get_booster"):
        booster = model.get_booster()
        score = booster.get_score(importance_type="weight")
        if feature_names is None:
            feature_names = [f"f{i}" for i in range(len(score))]
        values = np.array(
            [score.get(f, 0.0) for f in (feature_names or list(score.keys()))],
            dtype=float,
        )
        if values.sum() > 0:
            values = values / values.sum()
    else:
        raise TypeError("Model does not expose feature importances.")

    names = align_feature_names(feature_names, len(values))
    df = pd.DataFrame({"feature": names, "importance": values})
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


def plot_feature_importance(
    model: Any,
    feature_names: list[str] | None = None,
    *,
    top_n: int = 20,
    title: str = "Feature importance",
    save_path: str | None = None,
    fmt: str = "png",
) -> tuple[Any, Any]:
    """Plot feature importances for a fitted model.

    Examples
    --------
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from fyron.ml import plot_feature_importance
    >>> clf = RandomForestClassifier(n_estimators=5, random_state=0)
    >>> clf.fit([[0], [1], [2], [3]], [0, 0, 1, 1])
    >>> fig, ax = plot_feature_importance(clf, ["x"], top_n=1)
    >>> import matplotlib.pyplot as plt
    >>> plt.close(fig)
    """
    df = get_feature_importance(model, feature_names)
    return _plot_importance_df(
        df,
        top_n=top_n,
        title=title,
        save_path=save_path,
        fmt=fmt,
    )
