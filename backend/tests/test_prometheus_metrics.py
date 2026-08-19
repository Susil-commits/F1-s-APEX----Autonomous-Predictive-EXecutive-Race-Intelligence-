"""Tests for Prometheus metrics exposition and structured logging."""
import pytest
from starlette.testclient import TestClient

from backend.app.api.metrics import (
    APEX_ACTIVE_SESSIONS,
    APEX_DECISION_LATENCY,
    APEX_LAPS_SIMULATED,
    APEX_MODEL_DRIFT_STATUS,
    APEX_RATE_LIMIT_HITS,
)
from backend.app.main import app


def test_prometheus_metrics_endpoint_exposition():
    """Verifies that GET /metrics returns standard Prometheus text with APEX metrics."""
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    content = response.text
    assert "apex_active_sessions_count" in content
    assert "apex_connected_websockets_count" in content
    assert "apex_decision_latency_seconds" in content
    assert "apex_model_drift_status" in content
    assert "apex_laps_simulated_total" in content


def test_metrics_gauges_and_counters_mutation():
    """Verifies that Prometheus metrics can be incremented and observed."""
    APEX_LAPS_SIMULATED.inc(5)
    APEX_RATE_LIMIT_HITS.inc(1)
    APEX_DECISION_LATENCY.observe(0.012)
    APEX_ACTIVE_SESSIONS.set(3)
    APEX_MODEL_DRIFT_STATUS.set(1.0)

    client = TestClient(app)
    content = client.get("/metrics").text
    assert "apex_laps_simulated_total" in content
    assert "apex_rate_limit_exceeded_total" in content
