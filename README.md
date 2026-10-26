# APEX — F1 Pre-Race Finishing Position Predictor

[![CI](https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/ci.yml/badge.svg?branch=v1-only)](https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions)

**[Live Demo](https://f1-apex.vercel.app)** · [API Docs](https://f1-s-apex-autonomous-predictive.onrender.com/docs) · [Architecture](docs/ARCHITECTURE.md) · [Evaluation Suite](docs/EVALUATION.md) · [Run Guide](docs/HOW_TO_RUN.md)

> **Point-in-time race prediction** — predicts each driver's finishing position using only facts verifiably known before lights-out: qualifying grid slot, constructor championship pace share, driver rolling average, circuit characteristics, and rain forecast.

---

## What it does

APEX takes pre-race priors and returns:
- **Predicted finishing position** (P1–P20)
- **90% split-conformal confidence interval** — mathematically guaranteed coverage, calibrated on N=176 held-out samples from 2022–2023
- **Win & podium probability**
- **Feature attribution breakdown** showing which inputs drove the prediction

## Model & Benchmark Comparison

Selection was performed on 2023 validation (trained on 2022 only).  
The winner was then refitted on 2022+2023 and evaluated **once** on the 2024 holdout.

| Model / Benchmark Strategy | Selection R² (2023 val) | Selection MAE | 2024 Holdout R² | 2024 Holdout MAE | Status |
|----------------------------|------------------------|---------------|-----------------|------------------|--------|
| Naive Mean Predictor (P10.5) | — | 4.99 pos | — | 4.99 pos | Heuristic |
| GradientBoostingRegressor | 0.569 | 2.708 | — | — | Candidate |
| XGBRegressor | 0.579 | 2.708 | — | — | Candidate |
| **CatBoostRegressor ✓** | **0.597** | **2.680** | **0.686** | **2.362 pos** | **WINNER (Selected)** |

- **Training data**: Jolpica real F1 seasons 2022–2023 (N=880 driver-race entries).
- **Holdout**: 2024 season (N=479 driver entries — strictly held-out, never used in selection).
- **Conformal coverage on holdout**: **95.8%** (exceeds 90% target, q̂ = ±6.47 pos).
- **Gain vs. Baseline**: CatBoost explains **68.6% of finishing variance** and reduces MAE by **52.7%** vs naive prediction.

---

## Example Predictions (2024 Holdout Validation)

| Grand Prix | Driver | Starting Grid | Pre-Race Priors | Predicted Finish | 90% Conformal Window | Actual Finish | Validation |
|---|---|---|---|---|---|---|---|
| **Silverstone 2024** | Max Verstappen (`VER`) | P4 | Rain forecast 45% (Mixed) | **P2** | [P1–P5] | **P2** | ✓ Exact hit |
| **Monza 2024** | Lando Norris (`NOR`) | P1 | Dry, low drag track | **P1** | [P1–P4] | **P3** | ✓ Within 90% band |
| **Monaco 2024** | Charles Leclerc (`LEC`) | P1 | Street track, high downforce | **P1** | [P1–P3] | **P1** | ✓ Exact win predicted |

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

## Enterprise Pit Wall War Room & 2026 Engine Upgrades

APEX Enterprise extends the baseline pre-race predictor into a full pit wall intelligence suite:
- **Vectorized Full 20-Car Grid Classification (`POST /api/core/predict/grid`)**: Evaluates all 20 drivers simultaneously in a single vectorized pass with non-overlapping rankings and conformal bounds.
- **Monte Carlo Pit Stop & Safety Car Simulator (`POST /api/core/simulate/pit-stop`)**: 10,000 stochastic rollouts per second modeling undercut/overcut windows, tire wear, and Safety Car delta leverage (saving ~10.8s pit loss).
- **Pirelli Non-Linear Tyre Degradation & Cliff Matrix (`GET /api/core/tyres/stint-curve`, `POST /api/core/tyres/undercut`)**: Physics-informed wear modeling predicting exponential pace drop-off when tire wear exceeds 75%.
- **Zero-Trust Cryptographic Model Integrity**: HMAC-SHA256 model signing and verification (`core.security.model_integrity`) guarding against tampering and unauthorized weight manipulation.
- **Dynamic Driver Roster Service**: Decoupled driver profiles supporting mid-season reserve substitutions and real-time points standings.
- **2026 Regulation Future-Proofing**: Full modeling of Dual-State Active Aerodynamics (Z-Mode cornering downforce vs X-Mode low drag) and 350kW MGU-K Manual Override Mode (MOM).

---

## API Endpoints

### Core Prediction & Strategy
- `POST /api/core/predict` — Single driver pre-race finishing position & conformal interval.
- `POST /api/core/predict/grid` — Full 20-car grid vectorized finish classification.
- `POST /api/core/simulate/pit-stop` — 10,000-rollout in-race Monte Carlo pit strategy simulator.
- `GET /api/core/tyres/stint-curve` — Pirelli tire compound degradation trajectory.
- `POST /api/core/tyres/undercut` — Live undercut delta and out-lap gap evaluator.
- `GET /api/core/drivers` — Dynamic Formula 1 driver roster and priors.
- `GET /api/core/races` — Grand Prix calendar venues.

### Security, Drift & Observability
- `GET /api/security/telemetry` — Active guardrails, Canary traps, and circuit breaker status.
- `GET /api/security/audit-trail` — Cryptographically chained SHA-256 audit log (SOC 2).
- `POST /api/core/drift/check` — Z-score and PSI population stability drift detection.
- `GET /metrics` — Prometheus metrics for prediction latency and drift gauges.

---

## Structure

```
core/                  ← the entire service
├── api/               ← FastAPI routes (predict, grid, simulate, tyres, narration, drift, security)
├── data/              ← real_prerace_dataset.csv, dynamic roster service, and regulations
│   └── regulations/   ← Sporting, technical, and 2026 Active Aero regulations
├── features/          ← 10-feature pre-race builder + Pirelli tyre degradation physics model
├── ingestion/         ← FastF1 and Jolpica adapters
├── models/            ← apex_core_v1_model.joblib + HMAC signature (.sig) + metadata + PSI bins
├── monitoring/        ← z-score + PSI drift monitors + Prometheus gauges
├── security/          ← HMAC model integrity, canary traps, audit chain, circuit breaker
├── simulation/        ← Vectorized Monte Carlo pit stop and Safety Car rollout engine
├── training/          ← CatBoost/XGB/GBR benchmark + model signing + conformal calibration
└── requirements.txt
frontend/              ← React + Vite + Three.js + Pit Wall War Room Command Console
tests/                 ← 64 tests (100% passing across unit, security, and Monte Carlo suites)
Dockerfile.hardened    ← Non-root, multi-stage hardened enterprise container
.github/workflows/     ← Lean CI (pytest + npm build)
```
