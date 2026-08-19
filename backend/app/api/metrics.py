"""Prometheus Observability Metrics Registry and Endpoint for APEX."""

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

metrics_router = APIRouter()

# --- Custom APEX Prometheus Metrics ---

APEX_ACTIVE_SESSIONS = Gauge(
    "apex_active_sessions_count",
    "Number of active race simulation sessions currently loaded in memory",
)

APEX_CONNECTED_CLIENTS = Gauge(
    "apex_connected_websockets_count",
    "Number of active WebSocket clients streaming race telemetry",
)

APEX_DECISION_LATENCY = Histogram(
    "apex_decision_latency_seconds",
    "Latency of neural RL policy and decision engine formulation in seconds",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

APEX_MODEL_DRIFT_STATUS = Gauge(
    "apex_model_drift_status",
    "Current ML model registry integrity status (1.0 = ALL_HEALTHY, 0.0 = DRIFT_DETECTED)",
)

APEX_LAPS_SIMULATED = Counter(
    "apex_laps_simulated_total",
    "Total count of race simulation laps processed across all active sessions",
)

APEX_RATE_LIMIT_HITS = Counter(
    "apex_rate_limit_exceeded_total",
    "Total count of 429 Too Many Requests rate limit rejections triggered by compute endpoints",
)


def update_system_gauges():
    """Refreshes live system gauges from memory and model registry before metric exposition."""
    try:
        from backend.app.api.websocket import manager
        APEX_ACTIVE_SESSIONS.set(len(manager.sessions))
        total_connections = sum(len(s.active_connections) for s in manager.sessions.values())
        APEX_CONNECTED_CLIENTS.set(total_connections)
    except Exception:
        pass

    try:
        from backend.app.intelligence.model_registry import ModelRegistry
        audit = ModelRegistry.verify_all_models()
        is_healthy = 1.0 if audit.get("overall_status") == "ALL_MODELS_HEALTHY" else 0.0
        APEX_MODEL_DRIFT_STATUS.set(is_healthy)
    except Exception:
        pass


@metrics_router.get("/metrics")
async def get_prometheus_metrics():
    """Exposes standard Prometheus text metrics for Prometheus / Grafana / Datadog scrapers."""
    update_system_gauges()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
