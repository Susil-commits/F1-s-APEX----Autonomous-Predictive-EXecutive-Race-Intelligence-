"""Shared rate limiter instance for APEX Core API.

Centralised here so both ``main.py`` (which registers the exception handler)
and any router module (e.g. ``predict.py``) can import the same object without
creating a circular import.
"""
from __future__ import annotations

import os
import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

# Automatically disable rate limiting under pytest unless explicitly requested
_is_testing = "pytest" in sys.modules or os.getenv("TESTING", "").lower() in ("1", "true")
_rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "false" if _is_testing else "true").lower() in ("1", "true")

limiter = Limiter(
    key_func=get_remote_address,
    enabled=_rate_limit_enabled,
)
