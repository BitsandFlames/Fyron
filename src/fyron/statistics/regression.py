"""Classical regression tables for scientific manuscripts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from ._deps import require_numpy, require_scipy_stats
from .correction import p_value_correction_table


def fit_linear_regression_table(
    df: pd.DataFrame,
    *,
    outcome_col: str,
    covariates: Sequence[str],
    add_intercept: bool = True,
    alpha: float = 0.05,
    p_adjust: str | None = None,
) -> pd.DataFrame:
    """Fit an ordinary least-squares model and return a manuscript table.

    Parameters
    ----------
    df
        Analysis table containing the outcome and covariate columns.
    outcome_col
        Numeric continuous outcome column.
    covariates
        Predictor columns. Categorical columns are dummy encoded with the first
        level dropped.
    add_intercept
        If True, include an intercept row in the model and output table.
    alpha
        Two-sided confidence interval width, where ``0.05`` gives 95% intervals.
    p_adjust
        Optional multiple-testing correction method applied to non-intercept
        p-values, such as ``"fdr_bh"``, ``"bonferroni"``, or ``"holm"``.

    Returns
    -------
    pandas.DataFrame
        One row per model term with beta estimate, standard error, confidence
        interval, test statistic, p-value, sample size, model name, outcome, and
        formula.
    """
    np = require_numpy()
    stats = require_scipy_stats()
    _validate_alpha(alpha)
    data, X, y, terms = _prepare_regression_data(df, outcome_col=outcome_col, covariates=covariates, add_intercept=add_intercept)
    if X.shape[0] <= X.shape[1]:
        raise ValueError("linear regression requires more complete rows than fitted parameters.")
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ beta
    df_resid = X.shape[0] - X.shape[1]
    sigma2 = float((residuals @ residuals) / df_resid)
    inverse_design = np.linalg.pinv(X)
    cov = sigma2 * (inverse_design @ inverse_design.T)
    se = np.sqrt(np.diag(cov))
    t_stat = beta / se
    p_values = 2 * stats.t.sf(np.abs(t_stat), df=df_resid)
    crit = stats.t.ppf(1 - alpha / 2, df=df_resid)
    rows = []
    for term, estimate, se_value, stat, p_value in zip(terms, beta, se, t_stat, p_values):
        rows.append(
            {
                "term": term,
                "estimate": float(estimate),
                "beta": float(estimate),
                "std_error": float(se_value),
                "ci_lower": float(estimate - crit * se_value),
                "ci_upper": float(estimate + crit * se_value),
                "statistic": float(stat),
                "p_value": float(p_value),
                "n": int(len(data)),
                "model": "linear_regression",
                "outcome": outcome_col,
                "formula": _formula(outcome_col, covariates),
            }
        )
    table = pd.DataFrame(rows)
    return _maybe_adjust(table, p_adjust=p_adjust, alpha=alpha)


def fit_logistic_regression_table(
    df: pd.DataFrame,
    *,
    outcome_col: str,
    covariates: Sequence[str],
    add_intercept: bool = True,
    alpha: float = 0.05,
    p_adjust: str | None = None,
    max_iter: int = 1000,
) -> pd.DataFrame:
    """Fit a binary logistic regression model and return OR/CI/p-value rows.

    Parameters
    ----------
    df
        Analysis table containing a binary outcome and covariate columns.
    outcome_col
        Binary outcome column coded as ``0`` and ``1``.
    covariates
        Predictor columns. Categorical columns are dummy encoded with the first
        level dropped.
    add_intercept
        If True, include an intercept row in the model and output table.
    alpha
        Two-sided confidence interval width, where ``0.05`` gives 95% intervals.
    p_adjust
        Optional multiple-testing correction method applied to non-intercept
        p-values.
    max_iter
        Maximum optimizer iterations for the logistic likelihood fit.

    Returns
    -------
    pandas.DataFrame
        One row per model term with odds ratio, log-odds estimate, standard
        error, confidence interval, z statistic, p-value, sample size, model
        name, outcome, and formula.
    """
    np = require_numpy()
    stats = require_scipy_stats()
    _validate_alpha(alpha)
    data, X, y, terms = _prepare_regression_data(df, outcome_col=outcome_col, covariates=covariates, add_intercept=add_intercept)
    unique = set(y.tolist())
    if unique - {0, 1}:
        raise ValueError("logistic regression outcome must be coded 0/1.")
    if len(unique) < 2:
        raise ValueError("logistic regression requires both outcome classes.")
    if max_iter < 1:
        raise ValueError("max_iter must be positive.")

    from scipy.special import expit

    def nll(beta):
        eta = X @ beta
        return float(np.sum(np.logaddexp(0.0, eta) - y * eta))

    def grad(beta):
        eta = X @ beta
        p = expit(eta)
        return X.T @ (p - y)

    from scipy.optimize import minimize

    opt = minimize(nll, np.zeros(X.shape[1]), jac=grad, method="BFGS", options={"maxiter": max_iter})
    if not opt.success:
        raise ValueError(f"logistic regression did not converge: {opt.message}")
    beta = opt.x
    eta = X @ beta
    p = expit(eta)
    weights = p * (1.0 - p)
    information = X.T @ (X * weights[:, None])
    if not np.isfinite(information).all() or np.linalg.matrix_rank(information) < X.shape[1]:
        raise ValueError("Logistic information matrix is not identifiable.")
    if np.all((2 * y - 1) * eta > 0):
        raise ValueError("Complete separation prevents finite logistic inference.")
    cov = np.linalg.inv(information)
    se = np.sqrt(np.diag(cov))
    z = beta / se
    p_values = 2 * stats.norm.sf(np.abs(z))
    crit = stats.norm.ppf(1 - alpha / 2)
    rows = []
    for term, estimate, se_value, stat, p_value in zip(terms, beta, se, z, p_values):
        rows.append(
            {
                "term": term,
                "estimate": float(np.exp(estimate)),
                "odds_ratio": float(np.exp(estimate)),
                "log_odds": float(estimate),
                "std_error": float(se_value),
                "ci_lower": float(np.exp(estimate - crit * se_value)),
                "ci_upper": float(np.exp(estimate + crit * se_value)),
                "statistic": float(stat),
                "p_value": float(p_value),
                "n": int(len(data)),
                "model": "logistic_regression",
                "outcome": outcome_col,
                "formula": _formula(outcome_col, covariates),
            }
        )
    table = pd.DataFrame(rows)
    return _maybe_adjust(table, p_adjust=p_adjust, alpha=alpha)


def vif_table(df: pd.DataFrame, covariates: Sequence[str]) -> pd.DataFrame:
    """Return variance inflation factors for covariates after dummy encoding.

    Parameters
    ----------
    df
        Analysis table containing the covariate columns.
    covariates
        Predictor columns to inspect for multicollinearity. Categorical columns
        are dummy encoded before VIF calculation.

    Returns
    -------
    pandas.DataFrame
        Table with one row per encoded term and columns ``term``, ``vif``, and
        ``n``.
    """
    np = require_numpy()
    data, X, terms = _prepare_covariates(df, covariates, add_intercept=False)
    rows = []
    for index, term in enumerate(terms):
        y = X[:, index]
        others = np.delete(X, index, axis=1)
        if others.shape[1] == 0:
            vif = 1.0
        else:
            others = np.column_stack([np.ones(len(others)), others])
            beta, *_ = np.linalg.lstsq(others, y, rcond=None)
            pred = others @ beta
            ss_res = float(np.sum((y - pred) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
            vif = float("inf") if r2 >= 1 else 1.0 / (1.0 - r2)
        rows.append({"term": term, "vif": float(vif), "n": int(len(data))})
    return pd.DataFrame(rows)


def _prepare_regression_data(
    df: pd.DataFrame,
    *,
    outcome_col: str,
    covariates: Sequence[str],
    add_intercept: bool,
):
    data, X, terms = _prepare_covariates(df, covariates, add_intercept=add_intercept, outcome_col=outcome_col)
    y = pd.to_numeric(data[outcome_col], errors="raise").to_numpy(dtype=float)
    np = require_numpy()
    if not np.isfinite(y).all() or not np.isfinite(X).all():
        raise ValueError("Regression outcomes and design values must be finite.")
    if X.shape[1] == 0 or np.linalg.matrix_rank(X) < X.shape[1]:
        raise ValueError("Regression design must have full column rank; remove redundant predictors.")
    return data, X, y, terms


def _validate_alpha(alpha: float) -> None:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1).")


def _prepare_covariates(
    df: pd.DataFrame,
    covariates: Sequence[str],
    *,
    add_intercept: bool,
    outcome_col: str | None = None,
):
    np = require_numpy()
    required = list(covariates) + ([outcome_col] if outcome_col else [])
    missing = [col for col in required if col and col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    data = df[required].dropna().copy()
    if data.empty:
        raise ValueError("No complete rows available for regression.")
    X_df = pd.get_dummies(data[list(covariates)], drop_first=True, dtype=float)
    terms = list(X_df.columns)
    X = X_df.to_numpy(dtype=float)
    if add_intercept:
        X = np.column_stack([np.ones(len(X)), X])
        terms = ["Intercept", *terms]
    return data, X, terms


def _maybe_adjust(table: pd.DataFrame, *, p_adjust: str | None, alpha: float) -> pd.DataFrame:
    if p_adjust is None or p_adjust == "none":
        return table
    mask = table["term"] != "Intercept"
    adjusted = p_value_correction_table(table.loc[mask], p_col="p_value", method=p_adjust, alpha=alpha)
    out = table.copy()
    for col in ["p_adjusted", "p_rank", "rejected", "p_adjust_method", "alpha"]:
        out[col] = pd.NA
        out.loc[mask, col] = adjusted[col].to_numpy()
    return out


def _formula(outcome_col: str, covariates: Sequence[str]) -> str:
    return f"{outcome_col} ~ " + " + ".join(covariates)
