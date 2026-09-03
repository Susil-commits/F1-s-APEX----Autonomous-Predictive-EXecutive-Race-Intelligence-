# APEX — Architecture

## Single-Tier Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  Pre-Race Inputs (no live telemetry — zero leakage)             │
│  race_id · driver_id · grid_position · rain_probability         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  core/features/             │
              │  PreRaceFeatureBuilder      │
              │  11 deterministic features  │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  core/models/               │
              │  apex_core_v1_model.joblib  │
              │  CatBoostRegressor          │
              │  (winner of 3-way holdout   │
              │   benchmark vs XGB / GBR)   │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  Split-Conformal Calibration│
              │  N=176 held-out races       │
              │  q̂ = ±6.39 positions        │
              │  90% guaranteed coverage    │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  core/api/                  │
              │  FastAPI  POST /predict     │
              │  GET /health  GET /version  │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  frontend/                  │
              │  React + Vite + Tailwind    │
              │  F1 design system           │
              │  Driver cards, GP selector  │
              │  Broadcast prediction card  │
              └────────────────────────────┘
```

## Features (zero-leakage pre-race priors)

| Feature | Source |
|---------|--------|
| Grid position (normalised) | Qualifying result |
| Constructor points share | Championship standings |
| Driver rolling avg finish (5-race) | Historical results |
| Driver total starts | Historical results |
| Quali Δ to pole (seconds) | Qualifying lap times |
| Circuit downforce index | Circuit metadata |
| Circuit overtaking index | Circuit metadata |
| Rain probability | Weather forecast |
| Compound soft indicator | Pre-race tyre nominations |
| Compound wet indicator | Pre-race tyre nominations |
| Circuit lap count | Circuit metadata |

## Data

- **Training**: Jolpica F1 API + FastF1 — seasons 2020–2023 (N=882 driver-races)
- **Calibration fold**: last 20% of training chronologically (N=176 races, 2023 season)
- **Holdout**: full 2024 season (N=480, never touched until final evaluation)

## Deployment

- **Backend**: Single Uvicorn process, Python 3.12-slim Docker image (~280MB)
- **Frontend**: Static Vite build served via Nginx or Vercel CDN
- **No external services required** — no Postgres, Redis, Kafka, or message queues

## What is NOT in V1 (preserved in `v1-v5-exploration`)

- PPO / DQN reinforcement learning agents
- 60Hz vehicle digital twin
- Kafka streaming race state
- LangGraph multi-agent deliberation
- SHAP surrogate explainer
- MCP tool server
- Pit-wall multi-panel UI
