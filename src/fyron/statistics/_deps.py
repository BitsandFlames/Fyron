"""Optional dependency helpers for statistics."""

from __future__ import annotations


def require_numpy():
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'fyron.statistics requires numpy. Install it with: uv add "fyron[statistics]"'
        ) from exc
    return np


def require_scipy_stats():
    try:
        from scipy import stats
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'fyron.statistics tests require scipy. Install it with: uv add "fyron[statistics]"'
        ) from exc
    return stats
