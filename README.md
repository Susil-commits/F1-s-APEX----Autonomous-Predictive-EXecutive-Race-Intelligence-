# F1 APEX — Autonomous Pre-Race Predictive Intelligence

Point-in-time Formula 1 finishing position predictor with mathematically calibrated split-conformal confidence intervals and zero historical data leakage.

[![CI Status](https://img.shields.io/badge/CI-passing-brightgreen?style=flat-square&logo=githubactions)](.github/workflows/ci.yml)
[![Temporal Holdout R²](https://img.shields.io/badge/2024%20Holdout%20R%C2%B2-0.688-00F0FF?style=flat-square)](docs/EVALUATION.md)
[![Pearson Correlation](https://img.shields.io/badge/Pearson%20r-0.831-E10600?style=flat-square)](docs/EVALUATION.md)
[![Conformal Coverage](https://img.shields.io/badge/90%25%20Coverage-95.6%25-emerald?style=flat-square)](docs/EVALUATION.md)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue?style=flat-square&logo=python)](pyproject.toml)
[![Frontend](https://img.shields.io/badge/frontend-React%2018%20%2B%20Tailwind-purple?style=flat-square&logo=react)](frontend/)

---

## What It Predicts

Pick a real Formula 1 Grand Prix and driver. APEX evaluates verified facts known **strictly before lights out** — Qualifying grid slot, constructor championship points share, 5-race rolling form, circuit downforce profile, and precipitation forecast — to output:

1. **Projected Finish Position** (P1–P20)
2. **Split-Conformal 90% Confidence Window** (guaranteed empirical coverage calibrated on held-out data)
3. **Win & Podium Probabilities**
4. **Attribution Weights** (transparent feature importance breakdown)

```
[ Qualifying Grid ] + [ Constructor Share ] + [ Rolling Form ] + [ Circuit Index ] + [ Rain Forecast ]
                                          │
                                          ▼
                                   [ F1 APEX Core ]
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
       [ Projected Finish: P2 ]                      [ 90% Conformal Window: P1 – P3 ]
       [ Win: 24.5% | Podium: 85.0% ]                [ Calibration N=176 | Coverage=95.6% ]
```

> [!TIP]
> **V2–V5 Historical Exploration**: Looking for the earlier 60Hz vehicle digital twin, Deep Q-Network/PPO RL strategy agents, Kafka streaming pipeline, or LangGraph multi-agent consensus exploration? All V2–V5 work is permanently preserved on the [`v1-v5-exploration`](https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/tree/v1-v5-exploration) git tag.

---

## Quick Start (Run in 2 Minutes)

### Option A — Local Development (`uv` / Python & Node)

```bash
# 1. Clone the repository
git clone https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-.git
cd F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-

# 2. Start FastAPI Core backend (port 8000)
uv run uvicorn core.api.main:app --port 8000 --reload
```
Interactive OpenAPI documentation is live at [http://localhost:8000/docs](http://localhost:8000/docs).

In a separate terminal:
```bash
# 3. Start React UI (port 5173)
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

---

### Option B — Lean Docker Container

The entire prediction runtime packages into a lean container (~250MB):

```bash
docker build -t f1-apex-core .
docker run -p 8000:8000 f1-apex-core
```

Verify service health:
```bash
curl http://localhost:8000/api/health
```

---

## Verified Evaluation & Model Benchmarks

Every metric is directly reproducible on the genuine Jolpica F1 dataset:

```bash
# Benchmark all three candidate architectures on temporal holdout
uv run python -m core.training.train
```

### 2024 Temporal Holdout Comparison (2022–2023 Train, 2024 Test)

| Architecture | Validation $R^2$ | Validation MAE | Pearson $r$ | Empirical 90% Coverage | Status |
|---|---|---|---|---|---|
| `GradientBoostingRegressor` | 0.669 | 2.36 pos | 0.818 | — | Baseline |
| `XGBRegressor` | 0.687 | 2.31 pos | 0.830 | — | Candidate |
| **`CatBoostRegressor`** | **0.688** | **2.34 pos** | **0.831** | **95.6%** | **WINNER** |

### Why CatBoost?
Benchmarking reveals CatBoost slightly edging out XGBoost on temporal holdout generalization ($R^2 = 0.688$), primarily due to superior continuous-feature boundary handling and well-calibrated residual distributions on small, structured tabular splits.

---

## Engineering Highlights

1. **Strict Temporal Integrity (Zero Historical Leakage)**:
   Chronological train/test partitions ensure the model never learns from future qualifying sessions, later rounds, or mid-race safety car deployments.
2. **Inductive Split Conformal Prediction**:
   The chronological final 20% of the training set ($N = 176$) is reserved strictly for nonconformity calibration, generating distribution-free coverage guarantees ($\hat{q} = \pm 6.39$ positions).
3. **Automated Retraining & Regression Guard**:
   GitHub Actions CI executes weekly scheduled retraining and asserts that test holdout $R^2 \ge 0.40$, preventing silent model drift.
4. **Single-Tier Architecture**:
   Zero Kafka, Redis, or heavy Celery/BullMQ dependencies. One lean process, one REST endpoint, one focused UI.

---

## Project Structure

```
├── core/
│   ├── ingestion/       # Jolpica / FastF1 REST adapters
│   ├── features/        # Pre-race feature builder (9-D vector, zero outcome leakage)
│   ├── training/        # Multi-model benchmark & split-conformal trainer
│   └── api/             # Standalone FastAPI service (/api/core/predict)
├── frontend/
│   └── src/
│       ├── modes/core/  # CoreMode console, PredictionCard, FeatureImportanceBar
│       ├── components/  # Header with UTC mission clock and online status
│       └── App.tsx      # Focused single-screen React application
├── tests/
│   └── test_tier1_core.py # Feature invariant, training, and API integration tests
├── Dockerfile           # Minimal Python 3.12 production runtime
└── pyproject.toml       # Lean dependencies (FastAPI, Scikit-Learn, XGBoost, CatBoost)
```

---

## Automated Verification

```bash
# Run test suite
uv run pytest tests/ -v

# Build frontend production bundle
cd frontend && npm run build
```

---

## License

MIT License. Designed and developed by Susil Nayak.
