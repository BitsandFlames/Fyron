"""Model persistence via joblib."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import joblib
except ImportError as exc:  # pragma: no cover
    raise ImportError("joblib is required (installed with scikit-learn).") from exc


def save_estimator(model: Any, path: str | Path) -> None:
    """Serialize a fitted estimator with joblib.

    Examples
    --------
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from fyron.ml import save_estimator, load_estimator
    >>> import tempfile
    >>> from pathlib import Path
    >>> clf = RandomForestClassifier(n_estimators=5, random_state=0)
    >>> clf.fit([[0], [1]], [0, 1])
    >>> with tempfile.TemporaryDirectory() as d:
    ...     p = Path(d) / "model.joblib"
    ...     save_estimator(clf, p)
    ...     loaded = load_estimator(p)
    ...     list(loaded.predict([[0]]))
    [0]
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_estimator(path: str | Path) -> Any:
    """Load an estimator saved with :func:`save_estimator`."""
    return joblib.load(Path(path))
