"""FastAPI application entry point for APEX Core Race Intelligence."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.predict import router as core_predict_router

app = FastAPI(
    title="APEX — Autonomous Predictive Race Intelligence",
    description="Tier 1 pre-race finishing position predictor with conformal prediction intervals.",
    version="1.0.0",
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Core V1 predictor router
app.include_router(core_predict_router)


@app.get("/")
async def root():
    return {
        "service": "APEX Core V1 Predictor",
        "status": "ready",
        "docs_url": "/docs",
        "predict_endpoint": "/api/core/predict",
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "apex-core-v1"}


@app.get("/api/version")
async def get_version():
    return {
        "version": "1.0.0",
        "theme": "Formula 1 Red & Carbon",
        "status": "ready",
    }


# Mount frontend static build if present (catch-all for SPA)
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    @app.get("/app")
    async def serve_spa_app():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
