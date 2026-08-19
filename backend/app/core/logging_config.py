"""Structured JSON Logging Configuration for APEX Production Observability."""
import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONLogFormatter(logging.Formatter):
    """Formats standard Python logging records into machine-parseable JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include custom extra metadata if passed
        if hasattr(record, "session_id"):
            log_obj["session_id"] = record.session_id
        if hasattr(record, "race_id"):
            log_obj["race_id"] = record.race_id
        if hasattr(record, "action"):
            log_obj["action"] = record.action

        return json.dumps(log_obj)


def setup_structured_logging(level: int = logging.INFO):
    """Configures root logger with JSON log formatting for cloud log scrapers."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Remove existing stream handlers to avoid duplicates
    root_logger.handlers = [handler]
