"""FastAPI application entry point for APEX Race Intelligence with Kafka and Worker Pools."""
import os
from contextlib import asynccontextmanager
from typing import Any, Optional, cast

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.api.auth import auth_router
from backend.app.api.jobs_router import jobs_router
from backend.app.api.limiter import limiter
from backend.app.api.metrics import metrics_router
from backend.app.api.routes import router
from backend.app.api.websocket import manager
from backend.app.core.security import decode_access_token
from backend.app.jobs.workers import worker_pool
from backend.app.streaming.consumer import ApexTelemetryConsumerGroup
from backend.app.streaming.producer import ApexKafkaProducer

global_consumer: Optional[ApexTelemetryConsumerGroup] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global global_consumer
    # Initialize default race session on startup
    await manager.init_race(track_name="silverstone", seed=42)
    print("[APEX] Backend server initialized with default Silverstone race.")

    # Start Kafka Producer & Consumer Group
    try:
        producer = ApexKafkaProducer.get_instance()
        await producer.start()
        global_consumer = ApexTelemetryConsumerGroup()
        await global_consumer.start()
        print("[APEX] Kafka / Event Streaming layer active.")
    except Exception as e:
        print(f"[APEX] Streaming initialization notice: {e}")

    # Start Asynchronous Worker Pool
    try:
        await worker_pool.start()
        print("[APEX] Asynchronous Worker Pool active.")
    except Exception as e:
        print(f"[APEX] Worker pool initialization notice: {e}")

    # Pre-warm ML singletons in background to eliminate live demo first-request cold starts
    try:
        from backend.app.intelligence.embeddings import DecisionEmbedder
        from backend.app.intelligence.pinn_tyre_residual import PINNTyreResidualCompensator
        from backend.app.intelligence.shap_explainer import TreeSHAPExplainer
        from backend.app.intelligence.tyre_model import TyreModel
        from backend.app.strategy.dqn_agent import DQNAgent

        DQNAgent()
        TreeSHAPExplainer.get_instance()
        TyreModel.load_calibrated_model()
        PINNTyreResidualCompensator.get_instance()
        DecisionEmbedder.get_instance()
        print("[APEX] Pre-warmed ML singletons (DQN, TreeSHAP, TyreModel, PINN, Embeddings).")
    except Exception as e:
        print(f"[APEX] Model warmup notice: {e}")

    yield

    # Shutdown sequence
    if global_consumer:
        await global_consumer.stop()
    await worker_pool.stop()
    await ApexKafkaProducer.get_instance().stop()
    manager.stop_loop()
    print("[APEX] Backend server shutting down.")


app = FastAPI(
    title="APEX — Autonomous Predictive & EXecutive Race Intelligence",
    description="Enterprise real-time race digital twin, Kafka event broker, BullMQ worker queue, DQN RL, and explainability API.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register SlowAPI rate limiter state and 429 exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))

# Enable CORS with configurable origins via environment variable
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env.strip():
    allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST & WebSocket routers
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(router)
app.include_router(metrics_router)

# Mount frontend static build if present
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    @app.get("/")
    async def serve_spa_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


@app.websocket("/ws")
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
    # Optional token verification from query parameters (e.g., /ws?token=...)
    token = websocket.query_params.get("token")
    user_info = None
    if token:
        user_info = decode_access_token(token)

    query_session = websocket.query_params.get("race_id") or websocket.query_params.get("session_id")
    effective_session = query_session or session_id or "default"

    await manager.connect(websocket, session_id=effective_session)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            target_sid = data.get("session_id", effective_session)

            if msg_type == "PLAY":
                await manager.start_loop(session_id=target_sid)
            elif msg_type == "PAUSE":
                manager.stop_loop(session_id=target_sid)
            elif msg_type == "STEP":
                await manager.step_once(session_id=target_sid)
            elif msg_type == "SET_SPEED":
                manager.set_speed(float(data.get("speed", 1.0)), session_id=target_sid)
            elif msg_type == "ACTION":
                manager.queue_action(data.get("action"), session_id=target_sid)
            elif msg_type == "INJECT_EVENT":
                manager.inject_incident(data.get("event"), session_id=target_sid)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id=effective_session)
    except Exception:
        manager.disconnect(websocket, session_id=effective_session)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
