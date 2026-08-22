# ==============================================================================
# APEX — Autonomous Predictive & EXecutive Race Intelligence
# Production Multi-Stage Dockerfile (Frontend SPA + Python 3.12 ML/RL Engine)
# ==============================================================================

# --- Stage 1: Build React Vite Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline --no-audit

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Runtime ---
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="APEX Race Intelligence" \
      org.opencontainers.image.description="Autonomous Predictive & EXecutive Race Intelligence Engine" \
      org.opencontainers.image.authors="Susil" \
      org.opencontainers.image.source="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8000 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install minimal system runtime dependencies (libgomp1 for PyTorch/XGBoost OpenMP, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary for fast, reproducible dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Step 1: Copy dependency manifests and project docs required by pyproject.toml
COPY pyproject.toml uv.lock APEX_Architecture_and_Design.md README.md ./
RUN uv sync --frozen --no-install-project --no-dev

# Step 2: Copy application source code and benchmarks
COPY backend/ /app/backend/
COPY benchmarks/ /app/benchmarks/

# Step 3: Install the project
RUN uv sync --frozen --no-dev

# Step 4: Copy compiled frontend from Stage 1 into FastAPI's static mount directory
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose HTTP / WebSocket port
EXPOSE 8000

# Container healthcheck against APEX health API
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Launch APEX application server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
