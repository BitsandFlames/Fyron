"""Inspectable feature-selection helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

import numpy as np
import pandas as pd

from fyron.ml._arrays import align_feature_names, to_numpy_1d, to_numpy_2d

Task = Literal["classification", "regression"]


def univariate_feature_screening(
    X: Any,
    y: Any,
    *,
    task: Task = "classification",
    alpha: float = 0.05,
    correction: Literal["fdr_bh", "none"] = "fdr_bh",
) -> dict[str, Any]:
    """Screen features with transparent univariate tests and FDR correction."""

    from scipy import stats

    X_df = _as_dataframe(X)
    y_arr = to_numpy_1d(y)
    if len(X_df) != len(y_arr):
        raise ValueError("X and y must contain the same number of rows.")
    rows = []
    for feature in X_df.columns:
        series = X_df[feature]
        valid = ~(series.isna() | pd.isna(y_arr))
        x_valid = series.loc[valid]
        y_valid = y_arr[valid.to_numpy()]
        missing_percent = float(100 * (1 - valid.mean()))
        if len(x_valid) < 3:
            rows.append(_empty_screen_row(feature, missing_percent))
            continue
        if task == "classification":
            groups = [x_valid[y_valid == label] for label in pd.unique(y_valid)]
            groups = [pd.to_numeric(group, errors="coerce").dropna().to_numpy(dtype=float) for group in groups]
            groups = [group for group in groups if len(group) > 0]
            if len(groups) == 2 and pd.api.types.is_numeric_dtype(series):
                result = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
                statistic = float(result.statistic)
                p_value = float(result.pvalue)
                effect_size = float(np.nanmedian(groups[1]) - np.nanmedian(groups[0]))
                method = "mannwhitney_u"
            elif len(groups) > 2 and pd.api.types.is_numeric_dtype(series):
                result = stats.kruskal(*groups)
                statistic = float(result.statistic)
                p_value = float(result.pvalue)
                effect_size = None
                method = "kruskal_wallis"
            else:
                table = pd.crosstab(x_valid.astype(str), y_valid)
                statistic, p_value, _, _ = stats.chi2_contingency(table)
                statistic = float(statistic)
                p_value = float(p_value)
                effect_size = None
                method = "chi_square"
        elif task == "regression":
            x_num = pd.to_numeric(x_valid.reset_index(drop=True), errors="coerce")
            y_num = pd.to_numeric(pd.Series(y_valid), errors="coerce")
            mask = np.isfinite(x_num) & np.isfinite(y_num)
            missing_percent = float(100 * (1 - mask.sum() / len(series)))
            if mask.sum() < 3:
                rows.append(_empty_screen_row(feature, missing_percent))
                continue
            result = stats.spearmanr(x_num[mask], y_num[mask])
            statistic = float(result.statistic)
            p_value = float(result.pvalue)
            effect_size = statistic
            method = "spearman_correlation"
        else:
            raise ValueError("task must be 'classification' or 'regression'.")
        rows.append(
            {
                "feature": feature,
                "method": method,
                "statistic": statistic,
                "p_value": p_value,
                "effect_size": effect_size,
                "n": int(mask.sum()) if task == "regression" else int(len(x_valid)),
                "missing_percent": missing_percent,
            }
        )
    table = pd.DataFrame(rows)
    table["q_value"] = _fdr_bh(table["p_value"]) if correction == "fdr_bh" else table["p_value"]
    table["selected"] = table["q_value"] <= alpha
    table = table.sort_values(["selected", "q_value", "feature"], ascending=[False, True, True])
    return _result(table, selected=table.loc[table["selected"], "feature"].tolist(), method="univariate")


def variance_filter(X: Any, *, threshold: float = 0.0) -> dict[str, Any]:
    """Filter constant or near-constant numeric features."""

    X_df = _as_dataframe(X)
    numeric = X_df.apply(pd.to_numeric, errors="coerce")
    table = pd.DataFrame(
        {
            "feature": X_df.columns,
            "variance": [float(numeric[col].var(skipna=True)) for col in X_df.columns],
            "missing_percent": [float(X_df[col].isna().mean() * 100) for col in X_df.columns],
        }
    )
    table["selected"] = table["variance"] > threshold
    return _result(table, selected=table.loc[table["selected"], "feature"].tolist(), method="variance")


def correlation_filter(
    X: Any,
    *,
    threshold: float = 0.85,
    method: Literal["pearson", "spearman", "kendall"] = "spearman",
) -> dict[str, Any]:
    """Find redundant numeric features and drop later correlated features."""

    X_df = _as_dataframe(X)
    numeric = X_df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        raise ValueError("correlation_filter requires at least two numeric columns.")
    corr = numeric.corr(method=method).abs()
    dropped: set[str] = set()
    pairs = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            value = float(corr.loc[a, b])
            if value >= threshold:
                drop = b if b not in dropped else a
                keep = a if drop == b else b
                dropped.add(drop)
                pairs.append({"feature_a": a, "feature_b": b, "correlation": value, "keep": keep, "drop": drop})
    selected = [col for col in X_df.columns if col not in dropped]
    table = pd.DataFrame(pairs)
    return {
        "selected_features": selected,
        "dropped_features": sorted(dropped),
        "summary_table": table,
        "method_tables": {"correlation_pairs": table, "correlation_matrix": corr},
        "metadata": {"method": "correlation_filter", "threshold": threshold, "correlation_method": method},
    }


def model_importance_selection(
    estimator: Any,
    X: Any,
    y: Any,
    *,
    threshold: float | None = None,
    top_n: int | None = None,
) -> dict[str, Any]:
    """Fit an estimator and select features by importance or coefficient magnitude."""

    model = _fit_clone(estimator, X, y)
    names = list(_as_dataframe(X).columns)
    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_, dtype=float)
    elif hasattr(model, "coef_"):
        values = np.abs(np.asarray(model.coef_, dtype=float)).reshape(-1)
        if values.size != len(names):
            values = values.reshape(-1, len(names)).mean(axis=0)
    else:
        raise TypeError("estimator must expose feature_importances_ or coef_ after fitting.")
    table = pd.DataFrame({"feature": names, "importance": values})
    table = table.sort_values("importance", ascending=False).reset_index(drop=True)
    table["rank"] = np.arange(1, len(table) + 1)
    table = _select_by_threshold_or_top_n(table, value_col="importance", threshold=threshold, top_n=top_n)
    out = _result(table, selected=table.loc[table["selected"], "feature"].tolist(), method="model_importance")
    out["model"] = model
    return out


def permutation_importance_selection(
    estimator: Any,
    X: Any,
    y: Any,
    *,
    n_repeats: int = 10,
    scoring: str | None = None,
    random_state: int = 42,
    threshold: float | None = None,
    top_n: int | None = None,
) -> dict[str, Any]:
    """Select features using sklearn permutation importance."""

    from sklearn.inspection import permutation_importance

    model = _fit_clone(estimator, X, y)
    result = permutation_importance(model, X, y, n_repeats=n_repeats, scoring=scoring, random_state=random_state)
    table = pd.DataFrame(
        {
            "feature": list(_as_dataframe(X).columns),
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    table["rank"] = np.arange(1, len(table) + 1)
    table = _select_by_threshold_or_top_n(table, value_col="importance_mean", threshold=threshold, top_n=top_n)
    out = _result(table, selected=table.loc[table["selected"], "feature"].tolist(), method="permutation_importance")
    out["model"] = model
    return out


def boruta_feature_selection(X: Any, y: Any, **kwargs: Any) -> dict[str, Any]:
    """Run Boruta through the scientific feature-selection namespace."""

    from fyron.ml import run_boruta_feature_selection

    out = run_boruta_feature_selection(X, y, **kwargs)
    table = out["ranking_df"].copy()
    table["selected"] = table["selected"].astype(bool)
    return {
        "selected_features": out["selected_features"],
        "dropped_features": out["rejected_features"],
        "summary_table": table,
        "method_tables": {"boruta": table},
        "metadata": {"method": "boruta"},
        "selector": out["selector"],
        "transform": out["transform"],
    }


def stability_selection(
    estimator: Any,
    X: Any,
    y: Any,
    *,
    n_rounds: int = 100,
    sample_fraction: float = 0.75,
    selection_threshold: float = 0.6,
    random_state: int = 42,
) -> dict[str, Any]:
    """Repeated subsampling feature selection by model importance."""

    if n_rounds <= 0:
        raise ValueError("n_rounds must be positive.")
    if not 0 < sample_fraction <= 1:
        raise ValueError("sample_fraction must be in (0, 1].")
    X_df = _as_dataframe(X)
    y_arr = to_numpy_1d(y)
    rng = np.random.default_rng(random_state)
    counts = pd.Series(0, index=X_df.columns, dtype=float)
    n_sample = max(2, int(len(X_df) * sample_fraction))
    for _ in range(n_rounds):
        idx = rng.choice(len(X_df), size=n_sample, replace=True)
        selected = model_importance_selection(estimator, X_df.iloc[idx], y_arr[idx], top_n=max(1, len(X_df.columns) // 2))
        counts.loc[selected["selected_features"]] += 1
    table = pd.DataFrame({"feature": counts.index, "selection_frequency": counts.values / n_rounds})
    table = table.sort_values("selection_frequency", ascending=False).reset_index(drop=True)
    table["selected"] = table["selection_frequency"] >= selection_threshold
    return _result(table, selected=table.loc[table["selected"], "feature"].tolist(), method="stability_selection")


def combine_feature_selection_results(
    results: Mapping[str, Mapping[str, Any]] | Sequence[Mapping[str, Any]],
    *,
    strategy: Literal["consensus", "union", "intersection"] = "consensus",
    min_methods: int = 2,
) -> dict[str, Any]:
    """Combine several feature-selection result dictionaries."""

    items = results.items() if isinstance(results, Mapping) else [(f"method_{i}", r) for i, r in enumerate(results)]
    rows: dict[str, dict[str, Any]] = {}
    method_names = []
    for method, result in items:
        method_names.append(method)
        selected = set(result.get("selected_features", []))
        features = set(selected)
        table = result.get("summary_table")
        if isinstance(table, pd.DataFrame) and "feature" in table.columns:
            features.update(table["feature"].astype(str))
        for feature in features:
            rows.setdefault(feature, {"feature": feature, "n_selected_methods": 0})
            rows[feature][method] = feature in selected
            if feature in selected:
                rows[feature]["n_selected_methods"] += 1
    table = pd.DataFrame(rows.values()).fillna(False)
    if strategy == "union":
        table["selected"] = table["n_selected_methods"] >= 1
    elif strategy == "intersection":
        table["selected"] = table["n_selected_methods"] == len(method_names)
    elif strategy == "consensus":
        table["selected"] = table["n_selected_methods"] >= min_methods
    else:
        raise ValueError("strategy must be 'consensus', 'union', or 'intersection'.")
    table = table.sort_values(["selected", "n_selected_methods", "feature"], ascending=[False, False, True])
    return _result(table, selected=table.loc[table["selected"], "feature"].tolist(), method=f"combined_{strategy}")


def _as_dataframe(X: Any) -> pd.DataFrame:
    if isinstance(X, pd.DataFrame):
        return X.copy()
    arr = to_numpy_2d(X)
    names = align_feature_names(None, arr.shape[1])
    return pd.DataFrame(arr, columns=names)


def _fit_clone(estimator: Any, X: Any, y: Any) -> Any:
    from sklearn.base import clone

    model = clone(estimator)
    model.fit(X, y)
    return model


def _fdr_bh(p_values: Sequence[Any]) -> np.ndarray:
    p = pd.to_numeric(pd.Series(p_values), errors="coerce").to_numpy(dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    adjusted = ranked * len(ranked) / np.arange(1, len(ranked) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    out = np.empty_like(pv)
    out[order] = np.clip(adjusted, 0, 1)
    q[valid] = out
    return q


def _empty_screen_row(feature: str, missing_percent: float) -> dict[str, Any]:
    return {
        "feature": feature,
        "method": "insufficient_data",
        "statistic": np.nan,
        "p_value": np.nan,
        "effect_size": None,
        "n": 0,
        "missing_percent": missing_percent,
    }


def _select_by_threshold_or_top_n(
    table: pd.DataFrame,
    *,
    value_col: str,
    threshold: float | None,
    top_n: int | None,
) -> pd.DataFrame:
    out = table.copy()
    if top_n is not None:
        out["selected"] = out["rank"] <= top_n
    elif threshold is not None:
        out["selected"] = out[value_col] > threshold
    else:
        out["selected"] = out[value_col] > 0
    return out


def _result(table: pd.DataFrame, *, selected: Sequence[str], method: str) -> dict[str, Any]:
    return {
        "selected_features": list(selected),
        "summary_table": table.reset_index(drop=True),
        "method_tables": {method: table.reset_index(drop=True)},
        "metadata": {"method": method},
    }
