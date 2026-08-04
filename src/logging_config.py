"""Logging configuration for reproducible VibeMatch runs."""

from __future__ import annotations

import logging
from pathlib import Path


LOGGER_NAME = "vibematch"


def configure_logging(
    log_path: str = "logs/vibematch.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure one console handler and one persistent file handler."""

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_path = Path(log_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(component: str | None = None) -> logging.Logger:
    """Return the shared VibeMatch logger or a named child logger."""

    base = logging.getLogger(LOGGER_NAME)
    return base.getChild(component) if component else base
