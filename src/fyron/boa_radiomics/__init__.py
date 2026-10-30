"""Radiomics extraction from BOA segmentation folders.

Install optional dependencies with::

    uv add "fyron[radiomics]"
"""

from __future__ import annotations

from .features import (
    DEFAULT_BODY_REGION_LABELS,
    RADIOMICS_DIAGNOSTIC_PREFIX,
    discover_boa_radiomics_cases,
    extract_boa_radiomics_features,
    extract_case_radiomics_features,
)

__all__ = [
    "DEFAULT_BODY_REGION_LABELS",
    "RADIOMICS_DIAGNOSTIC_PREFIX",
    "discover_boa_radiomics_cases",
    "extract_boa_radiomics_features",
    "extract_case_radiomics_features",
]
