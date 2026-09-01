"""APEX Core Standalone FastAPI App (Tier 1).

Lightweight prediction service without Kafka, Redis, or heavy worker dependencies.
Run with:
    uvicorn core.api.main:app --port 8000 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.predict import router as predict_router

app = FastAPI(
    title="APEX Core — Pre-Race Finishing Position Intelligence",
    description="Tier 1 provably-correct baseline service. Predicts driver finishing position from pre-race priors.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.api.main:app", host="0.0.0.0", port=8000, reload=True)
