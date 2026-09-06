"""Prometheus-style metrics definition and registry for APEX Core API."""
from __future__ import annotations

import time
from prometheus_client import Counter, Histogram, Gauge

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
