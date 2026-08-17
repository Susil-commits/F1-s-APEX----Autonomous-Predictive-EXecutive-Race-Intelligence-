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
    yield
    manager.stop_loop()
    print("[APEX] Backend server shutting down.")


app = FastAPI(
    title="APEX — Autonomous Predictive & EXecutive Race Intelligence",
    description="Real-time race digital twin, tyre intelligence, DQN strategy RL, and explainability API.",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
