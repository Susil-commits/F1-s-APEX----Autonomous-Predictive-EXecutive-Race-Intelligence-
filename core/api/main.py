"""APEX Core Standalone FastAPI App (Tier 1).

Lightweight prediction service without Kafka, Redis, or heavy worker dependencies.
Run with:
    uvicorn core.api.main:app --port 8000 --reload
"""
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.api.metrics import (
    CONTENT_TYPE_LATEST,
    FEATURE_DRIFT_PSI,
    FEATURE_DRIFT_Z_SCORE,
    generate_latest,
)


RateLimitExceeded: Any = None
_rate_limit_exceeded_handler: Any = None
_SLOWAPI_AVAILABLE: bool = False

try:
    from slowapi import _rate_limit_exceeded_handler as _handler
    from slowapi.errors import RateLimitExceeded as _RLE
    RateLimitExceeded = _RLE
    _rate_limit_exceeded_handler = _handler
    _SLOWAPI_AVAILABLE = True
except ImportError:
    pass

from core.api.limiter import limiter
from core.api.predict import router as predict_router
from core.api.narration import router as narration_router
from core.monitoring.drift import WeekendDriftMonitor

_drift_monitor = WeekendDriftMonitor()

app = FastAPI(
    title="APEX Core — Pre-Race Finishing Position Intelligence",
    description="Tier 1 provably-correct baseline service. Predicts driver finishing position from pre-race priors.",
    version="1.0.0",
)

if _SLOWAPI_AVAILABLE and RateLimitExceeded is not None and _rate_limit_exceeded_handler is not None:
    app.state.limiter = limiter

    def _safe_rate_limit_handler(request: Request, exc: Exception) -> Response:
        return _rate_limit_exceeded_handler(request, exc)

    app.add_exception_handler(RateLimitExceeded, _safe_rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(narration_router)


@app.get("/")
async def root():
    return {
        "service": "APEX Core V1 Predictor",
        "status": "ready",
        "docs_url": "/docs",
        "predict_endpoint": "/api/core/predict",
        "narrate_endpoint": "/api/core/predict/narrate",
        "metrics_endpoint": "/metrics",
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "apex-core-v1"}


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus-style telemetry exposition endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/core/drift/baseline")
async def get_drift_baseline():
    """Returns baseline distribution reference stats used for pre-race data drift checks."""
    return {
        "baseline": _drift_monitor.baseline,
        "target_features": ["grid_position", "quali_delta_s", "rain_prob"],
        "psi_reference_bins": _drift_monitor.psi_monitor.to_dict() if _drift_monitor.psi_monitor else None,
        "psi_thresholds": {
            "stable": 0.10,
            "major": 0.25,
        },
    }


@app.post("/api/core/drift/check")
async def check_weekend_drift(records: List[Dict[str, Any]], z_threshold: float = 2.0):
    """Evaluates an incoming race weekend batch for feature distribution drift."""
    report = _drift_monitor.check_weekend_drift(records, z_threshold=z_threshold)
    for feat, f_data in report.get("features", {}).items():
        if isinstance(f_data, dict):
            if "psi" in f_data and f_data["psi"] is not None:
                FEATURE_DRIFT_PSI.labels(feature=feat).set(float(f_data["psi"]))
            if "drift_score_z" in f_data and f_data["drift_score_z"] is not None:
                FEATURE_DRIFT_Z_SCORE.labels(feature=feat).set(float(f_data["drift_score_z"]))
    return report


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.api.main:app", host="0.0.0.0", port=8000, reload=True)
