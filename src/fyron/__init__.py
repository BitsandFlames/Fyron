"""Fyron: interoperable healthcare data and AI workflows."""

from __future__ import annotations

from typing import TextIO


def _get_version() -> str:
    try:
        from importlib.metadata import version
        return version("fyron")
    except Exception:
        return "0.3.20b4"


def get_banner(
    version: str | None = None,
    *,
    include_version: bool = True,
    color: bool = True,
    theme: str = "bf",
) -> str:
    """Return the Bits & Flames Fyron banner as text.

    Parameters
    ----------
    version
        Optional version label to show instead of the installed Fyron version.
    include_version
        Whether to include the version label in the banner.
    color
        Whether to include ANSI color escape sequences.
    theme
        Banner color theme passed to :mod:`fyron.banner`.

    Returns
    -------
    str
        Rendered banner text.
    """
    from .banner import get_banner as _get_banner

    return _get_banner(version=version, include_version=include_version, color=color, theme=theme)


def print_banner(
    version: str | None = None,
    *,
    include_version: bool = True,
    color: bool = True,
    theme: str = "bf",
    file: TextIO | None = None,
) -> None:
    """Print the Bits & Flames Fyron banner.

    Parameters
    ----------
    version
        Optional version label to show instead of the installed Fyron version.
    include_version
        Whether to include the version label in the banner.
    color
        Whether to include ANSI color escape sequences.
    theme
        Banner color theme passed to :mod:`fyron.banner`.
    file
        Optional text stream to receive the banner.

    Returns
    -------
    None
        The banner is written to the selected stream.
    """
    from .banner import print_banner as _print_banner

    _print_banner(version=version, include_version=include_version, color=color, theme=theme, file=file)


def get_run_header(*args, **kwargs) -> str:
    """Return a formatted run header for CLI and workflow logs.

    Parameters
    ----------
    args
        Positional arguments forwarded to :func:`fyron.banner.get_run_header`.
    kwargs
        Keyword arguments forwarded to :func:`fyron.banner.get_run_header`.

    Returns
    -------
    str
        Header text suitable for terminal or log output.
    """
    from .banner import get_run_header as _get_run_header

    return _get_run_header(*args, **kwargs)


def get_run_footer(*args, **kwargs) -> str:
    """Return a formatted run footer for CLI and workflow logs.

    Parameters
    ----------
    args
        Positional arguments forwarded to :func:`fyron.banner.get_run_footer`.
    kwargs
        Keyword arguments forwarded to :func:`fyron.banner.get_run_footer`.

    Returns
    -------
    str
        Footer text suitable for terminal or log output.
    """
    from .banner import get_run_footer as _get_run_footer

    return _get_run_footer(*args, **kwargs)


from .fhir.auth import Auth

from .fhir.rest import FHIRRestClient
try:
    from .fhir.sql import FHIRSQLClient, build_sql_partitions
except ImportError:  # optional psycopg / DB not needed for REST-only use
    FHIRSQLClient = None  # type: ignore
    build_sql_partitions = None  # type: ignore
from .dicom.client import DICOMDownloader
from .llm.agent import LLMAgent
from .documents.client import DocumentDownloader
from .fhir.path_presets import FHIR_PATH_PRESETS, get_fhir_path_preset
from .fhir.types import FHIRObj
from .flow import FlowStep, FlowTracker, track_filter
from .fhir.utils import (
    extract_condition,
    extract_diagnostic_report,
    extract_encounter,
    extract_imaging_study,
    extract_observation,
    extract_patient,
    extract_procedure,
    process_condition_bundle,
    process_diagnostic_report_bundle,
    process_encounter_bundle,
    process_imaging_study_bundle,
    process_observation_bundle,
    process_patient_bundle,
    process_procedure_bundle,
    safe_get,
)
from .core.io import (
    DataIO,
    TeableClient,
    describe_file,
    ensure_parent_dir,
    read_csv,
    read_excel,
    read_json,
    read_table,
    summarize_table,
    write_csv,
    write_excel,
    write_json,
    write_table,
)
from .core.env import load_env
from .console import configure_logging, console_message, get_logger
from . import clinical_codes, dataframe

__all__ = [
    "Auth",
    "FHIRRestClient",
    "FHIRSQLClient",
    "build_sql_partitions",
    "DICOMDownloader",
    "LLMAgent",
    "DocumentDownloader",
    "FHIRObj",
    "FHIR_PATH_PRESETS",
    "FlowStep",
    "FlowTracker",
    "extract_condition",
    "extract_diagnostic_report",
    "extract_encounter",
    "extract_imaging_study",
    "extract_observation",
    "extract_patient",
    "extract_procedure",
    "process_condition_bundle",
    "process_diagnostic_report_bundle",
    "process_encounter_bundle",
    "process_imaging_study_bundle",
    "process_observation_bundle",
    "process_patient_bundle",
    "process_procedure_bundle",
    "safe_get",
    "DataIO",
    "TeableClient",
    "describe_file",
    "ensure_parent_dir",
    "load_env",
    "read_csv",
    "read_excel",
    "read_json",
    "read_table",
    "summarize_table",
    "write_csv",
    "write_excel",
    "write_json",
    "write_table",
    "get_banner",
    "get_fhir_path_preset",
    "get_logger",
    "get_run_footer",
    "get_run_header",
    "print_banner",
    "configure_logging",
    "console_message",
    "clinical_codes",
    "dataframe",
    "track_filter",
]
__version__ = _get_version()
