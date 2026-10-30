"""Lightweight end-to-end classification pipeline."""

from __future__ import annotations

from typing import Any, Literal

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

from fyron.ml._arrays import is_binary, to_numpy_1d, to_numpy_2d
from fyron.ml.class_weights import compute_class_weights, compute_scale_pos_weight
from fyron.ml.defaults import get_default_param_grid
from fyron.ml.search import grid_search_model
from fyron.ml.splitting import train_test_split_data
from fyron.ml.training import _evaluate_classifier

PipelineResult = dict[str, Any]


class _BorutaTransformer(TransformerMixin, BaseEstimator):
    """Cloneable selection step so CV fits Boruta only on each training fold."""

    def __init__(self, *, random_state=42, boruta_kwargs=None, feature_names=None):
        self.random_state = random_state
        self.boruta_kwargs = boruta_kwargs
        self.feature_names = feature_names

    def fit(self, X, y):
        import pandas as pd
        from fyron.ml.boruta_selection import run_boruta_feature_selection

        data = pd.DataFrame(X, columns=self.feature_names) if self.feature_names is not None else X
        kwargs = dict(self.boruta_kwargs or {})
        kwargs.setdefault("random_state", self.random_state)
        self.result_ = run_boruta_feature_selection(data, y, **kwargs)
        self.result_.pop("transform", None)
        if not self.result_["selected_features"]:
            raise ValueError("Boruta selected no features; adjust selection settings or disable Boruta.")
        return self

    def transform(self, X):
        return self.result_["selector"].transform(to_numpy_2d(X))


def run_classification_pipeline(
    X: Any,
    y: Any,
    *,
    model: Literal["random_forest", "xgboost"] = "random_forest",
    test_size: float = 0.2,
    stratify: bool = True,
    random_state: int = 42,
    handle_imbalance: bool = True,
    use_boruta: bool = False,
    boruta_kwargs: dict[str, Any] | None = None,
    use_grid_search: bool = False,
    param_grid: dict[str, Any] | None = None,
    plot: bool = False,
    pos_label: Any | None = None,
    **model_params: Any,
) -> PipelineResult:
    """Split, optionally select features within training folds, then evaluate.

    With Boruta, the returned model is an sklearn Pipeline accepting the original
    feature space. Returned train/test data are never preselected. Grid keys may
    remain unprefixed; classifier parameters are routed to the model step.
    All predictions, metrics and figures describe the returned fitted model.

    Examples
    --------
    >>> from fyron.ml import run_classification_pipeline
    >>> X = [[i % 3] for i in range(40)]
    >>> y = [0] * 20 + [1] * 20
    >>> out = run_classification_pipeline(
    ...     X, y, model="random_forest", n_estimators=20, random_state=0
    ... )
    >>> "metrics" in out
    True
    """
    X_train, X_test, y_train, y_test = train_test_split_data(
        X, y, test_size=test_size, stratify=stratify, random_state=random_state,
    )
    class_weight = compute_class_weights(y_train) if handle_imbalance else None
    scale_pos_weight = None
    if handle_imbalance and is_binary(to_numpy_1d(y_train)):
        scale_pos_weight = compute_scale_pos_weight(y_train)

    params = dict(model_params)
    params.setdefault("random_state", random_state)
    if model == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        if handle_imbalance:
            params.setdefault("class_weight", class_weight)
        estimator = RandomForestClassifier(**params)
    elif model == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as exc:
            raise ImportError('Install XGBoost with: uv add "fyron[ml]"') from exc
        binary = is_binary(to_numpy_1d(y_train))
        params.setdefault("eval_metric", "logloss" if binary else "mlogloss")
        if not binary:
            params.setdefault("objective", "multi:softprob")
            if params.get("scale_pos_weight") is not None:
                raise ValueError("scale_pos_weight is only valid for binary classification.")
        if scale_pos_weight is not None:
            params.setdefault("scale_pos_weight", scale_pos_weight)
        estimator = XGBClassifier(**params)
    else:
        raise ValueError("model must be 'random_forest' or 'xgboost'")

    if use_boruta:
        names = list(X.columns) if hasattr(X, "columns") else None
        estimator = Pipeline([
            ("selection", _BorutaTransformer(
                random_state=random_state, boruta_kwargs=boruta_kwargs, feature_names=names,
            )),
            ("model", estimator),
        ])

    gs = None
    if use_grid_search:
        grid = param_grid or get_default_param_grid(model)
        if use_boruta:
            grid = {key if "__" in key else f"model__{key}": value for key, value in grid.items()}
        gs = grid_search_model(
            estimator, grid, X_train, y_train,
            random_state=random_state, pos_label=pos_label,
        )
        estimator = gs["best_estimator"]
    else:
        estimator.fit(to_numpy_2d(X_train), to_numpy_1d(y_train))

    result = _evaluate_classifier(
        estimator, X_test, y_test, pos_label=pos_label,
        plot=plot, title=model.replace("_", " ").title(),
    )
    if gs is not None:
        gs["val_metrics"] = result["metrics"]
        result["grid_search"] = gs
    boruta_out = None
    if use_boruta:
        selection = estimator.named_steps["selection"]
        boruta_out = {**selection.result_, "transform": selection.transform}
    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "boruta": boruta_out,
        "class_weight": class_weight,
        "scale_pos_weight": scale_pos_weight,
        **result,
    }
