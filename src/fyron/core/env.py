"""Environment loading helpers."""

from __future__ import annotations

import logging
from typing import Optional

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)


def load_env(
    path: Optional[str] = None,
    *,
    override: bool = False,
    warn_if_missing: bool = True,
) -> Optional[str]:
    """Load environment variables from a .env file.

    Parameters
    ----------
    path:
        Optional path to a .env file. If None, searches from the current working directory.
    override:
        Whether to override existing environment variables.
    warn_if_missing:
        If True, logs a warning when no .env file is found.
    """
    env_path = path or find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path, override=override)
        logger.info("Loaded environment from %s", env_path)
        return env_path
    if warn_if_missing:
        logger.warning("No .env file found. Set environment variables or create a .env file.")
    return None
