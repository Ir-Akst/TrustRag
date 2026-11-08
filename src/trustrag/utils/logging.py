# src/trustrag/utils/logging.py
"""Structured logging utilities for TrustRAG.

The module provides a simple function ``get_logger`` that returns a configured
``logging.Logger`` instance. The logger emits messages in a JSON‑compatible
format with the following fields:

- ``timestamp`` – ISO‑8601 UTC time
- ``level`` – log level name
- ``module`` – ``logging`` module name (``__name__``)
- ``message`` – the log message
- ``extra`` – any additional keyword arguments passed to the logger

Sensitive values such as API keys are never logged automatically because the
configuration values are stored under the ``llm`` section and the ``get_logger``
function explicitly filters out any keys containing ``key`` (case‑insensitive).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Mapping


class JsonFormatter(logging.Formatter):
    """Format log records as a single‑line JSON string.

    The formatter extracts standard record attributes and merges any ``extra``
    mapping provided via the ``extra`` argument of ``logger.info`` etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Mapping[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        # Include extra attributes that are not part of the default LogRecord
        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__ and not k.startswith("_")
        }
        if extra:
            # Filter out potential secret keys
            filtered = {k: v for k, v in extra.items() if "key" not in k.lower()}
            log_entry = {**log_entry, **filtered}
        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str = "trustrag", level: str | None = None) -> logging.Logger:
    """Return a configured logger.

    Parameters
    ----------
    name: str
        Logger name. Defaults to ``"trustrag"``.
    level: str | None
        Log level name (e.g., ``"INFO"``). If ``None``, the level is read from the
        ``TRUSTRAG_LOG_LEVEL`` environment variable or falls back to ``INFO``.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Logger already configured – avoid duplicate handlers.
        return logger

    env_level = os.getenv("TRUSTRAG_LOG_LEVEL", "INFO")
    log_level = getattr(logging, (level or env_level).upper(), logging.INFO)
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger

