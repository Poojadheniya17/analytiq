# core/logger.py
# Analytiq — Structured logging for all modules

import os
import logging
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Formats logs as JSON for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "time":    datetime.utcnow().isoformat(),
            "level":   record.levelname,
            "module":  record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for any module."""
    logger  = logging.getLogger(name)
    is_prod = os.environ.get("ENV") == "production"

    if not logger.handlers:
        handler = logging.StreamHandler()
        if is_prod:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S"
            ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO if is_prod else logging.DEBUG)

    return logger


# Shared loggers
api_logger = get_logger("analytiq.api")
ml_logger  = get_logger("analytiq.ml")
db_logger  = get_logger("analytiq.db")
