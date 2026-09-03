# APEX — F1 Pre-Race Finishing Position Predictor

[![CI](https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/ci.yml/badge.svg?branch=v1-only)](https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions)

> **Point-in-time race prediction** — predicts each driver's finishing position using only facts verifiably known before lights-out: qualifying grid slot, constructor championship pace share, driver rolling average, tyre compound, circuit characteristics, and rain forecast.

---

## What it does

APEX takes pre-race priors and returns:
- **Predicted finishing position** (P1–P20)
- **90% split-conformal confidence interval** — mathematically guaranteed coverage, calibrated on N=176 held-out historical races
- **Win & podium probability**
- **Feature attribution breakdown** showing which inputs drove the prediction

## Model

| Candidate | Holdout R² | Holdout MAE |
|-----------|-----------|------------|
| GradientBoostingRegressor | 0.669 | 2.36 pos |
| XGBRegressor | 0.687 | 2.31 pos |
| **CatBoostRegressor ✓** | **0.688** | **2.34 pos** |

Training data: Jolpica / FastF1 historical seasons 2020–2023 (N=882 driver-races).  
Holdout: 2024 season (N=480, never seen during training or calibration).  
Conformal coverage on holdout: **95.6%** (target ≥ 90%).

Zero data leakage — no lap times, sector times, or live telemetry used.

---

## Run in 2 minutes

### Local (Python)

```bash
git clone https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-.git
cd F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-
git checkout v1-only

pip install -r core/requirements.txt
uvicorn core.api.main:app --reload
```

Open [http://localhost:8000/api/health](http://localhost:8000/api/health).

### Docker

```bash
docker build -t f1apex .
docker run -p 8000:8000 f1apex
```

### Frontend

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

---

## API

### `GET /api/health`
```json
{"status": "ok", "version": "core-v1.0.0"}
```

### `POST /api/core/predict`
```json
{
  "race_id": "silverstone",
  "driver_id": "NOR",
  "grid_position": 2,
  "rain_probability": 0.15
}
```

Response includes `predicted_position`, `confidence_interval`, `win_probability_pct`, `podium_probability_pct`, `feature_contributions`, and metadata.

---

## Structure

```
core/                  ← the entire service
├── api/               ← FastAPI routes (health + predict)
├── features/          ← zero-leakage feature builder
├── ingestion/         ← Jolpica adapter
├── training/          ← CatBoost/XGB/GBR benchmark + conformal calibration
├── data/              ← real_prerace_dataset.csv (2020–2023)
├── models/            ← apex_core_v1_model.joblib
└── requirements.txt
frontend/              ← React + Vite + Tailwind UI
tests/                 ← test_tier1_core.py (3 tests)
Dockerfile             ← single-stage Python 3.12-slim
.github/workflows/     ← lean CI (pytest + npm build)
```

---

## Earlier V2–V5 work

All prior exploration (PPO/DQN RL agents, 60Hz digital twin, Kafka streaming, LangGraph multi-agent deliberation, SHAP explainer, MCP server) is permanently preserved in:

```
git checkout v1-v5-exploration
```

The `v1-only` branch is the clean, deployable baseline.
