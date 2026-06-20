"""Structured logging configuration using structlog.

`console` format is human-friendly for local development; `json` emits one
JSON object per line for log aggregation in staging/production.
"""

from __future__ import annotations

import logging
import sys
from typing import cast

import structlog

from app.core.config import LogFormat, Settings


def configure_logging(settings: Settings) -> None:
    """Configure structlog and the stdlib logging bridge.

    Idempotent: safe to call once at application startup.
    """
    level = logging.getLevelName(settings.log_level.upper())

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format == LogFormat.JSON:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    # structlog.get_logger is typed as returning Any; the configured wrapper
    # class is a stdlib BoundLogger.
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
