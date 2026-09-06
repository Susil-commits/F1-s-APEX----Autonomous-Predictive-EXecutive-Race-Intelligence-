"""Prometheus-style metrics definition and registry for APEX Core API."""
from __future__ import annotations

import time
from typing import Any

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    class _DummyMetric:
        """No-op metric fallback when prometheus_client is not installed."""
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def labels(self, *args: Any, **kwargs: Any) -> "_DummyMetric":
            return self

        def inc(self, amount: float = 1) -> None:
            pass

        def dec(self, amount: float = 1) -> None:
            pass

        def set(self, value: float) -> None:
            pass

        def observe(self, amount: float) -> None:
            pass

    Counter = _DummyMetric  # type: ignore[assignment,misc]
    Histogram = _DummyMetric  # type: ignore[assignment,misc]
    Gauge = _DummyMetric  # type: ignore[assignment,misc]
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    def generate_latest() -> bytes:  # type: ignore[misc]
        return b"# prometheus_client library not installed\n"


# Counter tracking predictions by driver abbreviation and outcome status
PREDICTION_REQUESTS_TOTAL = Counter(
    "apex_predictions_total",
    "Total count of finishing position predictions requested",
    ["driver_id", "status"],
)

# Histogram tracking inference latency per circuit venue
PREDICTION_LATENCY_SECONDS = Histogram(
    "apex_prediction_latency_seconds",
    "Latency of finishing position predictions in seconds",
    ["circuit"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Gauge tracking model loading time
MODEL_LOAD_TIMESTAMP = Gauge(
    "apex_model_loaded_timestamp",
    "Epoch timestamp when APEX Core model artifact was loaded into memory",
)
MODEL_LOAD_TIMESTAMP.set(time.time())
