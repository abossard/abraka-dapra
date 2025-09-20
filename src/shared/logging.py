"""Structured logging helpers shared across services."""

import logging
from typing import Any

_LOGGER_NAME = "snacktopus"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging with a consistent formatter."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )


def get_logger(*names: Any) -> logging.Logger:
    """Return a child logger under the project namespace."""
    qualified_name = ".".join(str(name) for name in names if name)
    if qualified_name:
        return logging.getLogger(f"{_LOGGER_NAME}.{qualified_name}")
    return logging.getLogger(_LOGGER_NAME)
