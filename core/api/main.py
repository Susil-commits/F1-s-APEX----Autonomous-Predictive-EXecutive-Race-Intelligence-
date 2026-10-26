"""APEX Core Standalone FastAPI App (Tier 1).

Lightweight prediction service without Kafka, Redis, or heavy worker dependencies.
Run with:
    uvicorn core.api.main:app --port 8000 --reload
"""
from typing import Any, Dict, List
from fastapi import Depends, FastAPI
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
from core.security import (
    EnterpriseSecurityHeadersMiddleware,
    Role,
    configure_enterprise_cors,
    get_audit_logger,
    require_role,
)
from core.security.circuit_breaker import get_failover_manager

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

# Enterprise Security Headers & CORS Policy
app.add_middleware(EnterpriseSecurityHeadersMiddleware)
configure_enterprise_cors(app)

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
        "security_telemetry": "/api/security/telemetry",
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "apex-core-v1", "security_active": True}


# ── ENTERPRISE AI SECURITY ENDPOINTS ─────────────────────────────────────────

@app.get("/api/security/telemetry")
async def get_security_telemetry():
    """Returns runtime telemetry for active enterprise security and AI guardrails."""
    failover_mgr = get_failover_manager()
    return {
        "status": "operational",
        "guardrails_active": True,
        "anti_prompt_injection": True,
        "canary_traps_enabled": True,
        "pii_redaction_enabled": True,
        "security_headers_enforced": True,
        "circuit_breakers": failover_mgr.all_statuses(),
    }


@app.get("/api/security/audit-trail")
async def get_audit_trail(role: Role = Depends(require_role(Role.ADMIN))):
    """Retrieves cryptographically chained audit events (SOC 2 / ISO 27001). Requires ADMIN role."""
    audit_logger = get_audit_logger()
    return {
        "events": audit_logger.get_recent_events(limit=50),
        "chain_verified": audit_logger.verify_chain()[0],
    }


@app.get("/api/security/verify-chain")
async def verify_audit_chain(role: Role = Depends(require_role(Role.ADMIN))):
    """Cryptographically verifies tamper evidence across the audit hash chain."""
    audit_logger = get_audit_logger()
    is_valid, error = audit_logger.verify_chain()
    return {
        "is_valid": is_valid,
        "error": error,
        "algorithm": "SHA-256",
    }


@app.get("/api/security/circuit-status")
async def get_circuit_status(role: Role = Depends(require_role(Role.ENGINEER))):
    """Returns AI provider circuit breaker operational states. Requires ENGINEER role."""
    failover_mgr = get_failover_manager()
    return {
        "providers": failover_mgr.all_statuses(),
    }


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
