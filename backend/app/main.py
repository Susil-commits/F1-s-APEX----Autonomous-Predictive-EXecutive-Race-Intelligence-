"""FastAPI application entry point for APEX Race Intelligence."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.api.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize default race session on startup
    await manager.init_race(track_name="silverstone", seed=42)
    print("[APEX] Backend server initialized with default Silverstone race.")

    # Pre-warm ML singletons in background to eliminate live demo first-request cold starts
    try:
        from backend.app.intelligence.embeddings import get_embedding_model
        from backend.app.intelligence.pinn_tyre_residual import PINNTyreResidualCompensator
        from backend.app.intelligence.shap_explainer import TreeSHAPExplainer
        from backend.app.intelligence.tyre_model import TyreModel
        from backend.app.strategy.dqn_agent import DQNAgent

        DQNAgent()
        TreeSHAPExplainer.get_instance()
        TyreModel.load_calibrated_model()
        PINNTyreResidualCompensator.get_instance()
        get_embedding_model()
        print("[APEX] Pre-warmed ML singletons (DQN, TreeSHAP, TyreModel, PINN, Embeddings).")
    except Exception as e:
        print(f"[APEX] Model warmup notice: {e}")

    yield
    manager.stop_loop()
    print("[APEX] Backend server shutting down.")


app = FastAPI(
    title="APEX — Autonomous Predictive & EXecutive Race Intelligence",
    description="Real-time race digital twin, tyre intelligence, DQN strategy RL, and explainability API.",
    version="0.1.0",
    lifespan=lifespan,
)

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

# Register REST router
app.include_router(router)

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
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "PLAY":
                await manager.start_loop()
            elif msg_type == "PAUSE":
                manager.stop_loop()
            elif msg_type == "STEP":
                await manager.step_once()
            elif msg_type == "SET_SPEED":
                manager.set_speed(float(data.get("speed", 1.0)))
            elif msg_type == "ACTION":
                manager.queue_action(data.get("action"))
            elif msg_type == "INJECT_EVENT":
                manager.inject_incident(data.get("event"))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
