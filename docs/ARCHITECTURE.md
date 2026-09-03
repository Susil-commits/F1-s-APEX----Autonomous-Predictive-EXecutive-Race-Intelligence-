# APEX System Architecture — V1 Core Predictive Intelligence

A lean, high-fidelity motorsports predictive service:
```
Historical Ingestion (Jolpica / Ergast API)
                 │
                 ▼
Pre-Race Feature Engineering (9 Point-in-Time Features, Zero Data Leakage)
                 │
                 ▼
Temporal Benchmark & Selection (GradientBoosting vs. XGBoost vs. CatBoost)
                 │
                 ▼
Split-Conformal Prediction Engine (Empirically Calibrated 90% Confidence Bounds)
                 │
                 ▼
FastAPI Prediction Service (`/api/core/predict`)
                 │
                 ▼
React Single-Screen Console (Point-in-Time Prediction & Feature Attributions)
```

---

## 1. Architectural Principles

1. **Strict Temporal Integrity (Zero Historical Leakage)**:
   Any feature fed to the model must be known strictly before lights out of the target Grand Prix. No race incidents, intermediate sector times, or future qualifying deltas enter the training matrix. Training occurs chronologically on past seasons ($\le 2023$), and validation evaluates strictly on the subsequent temporal holdout ($2024$).

2. **Model Selection Discipline**:
   Rather than hardcoding a single estimator family, APEX benchmarks three candidate architectures (`GradientBoostingRegressor`, `XGBRegressor`, and `CatBoostRegressor`) on an identical chronological fitting split and selects whichever achieves superior generalization on the temporal holdout.

3. **Guaranteed Uncertainty Bounds via Split Conformal Prediction**:
   Instead of arbitrary heuristic error margins, confidence bounds are calibrated on a dedicated held-out calibration fold using split conformal prediction, ensuring finite-sample coverage guarantees ($1 - \alpha = 0.90$).

4. **Lean, Single-Tier Deployment Footprint**:
   The entire service runs as a single lightweight process without external queue, cache, or broker dependencies (no Kafka, Redis, or heavy background workers required).

---

## 2. Ingestion Layer (`core/ingestion/`)

APEX interfaces with the **Jolpica F1 Ergast-compatible REST API** to retrieve official FIA timing and race outcome data:

- **Seasons covered**: 2022, 2023, 2024
- **Ingestion Adapter**: [`JolpicaAdapter`](file:///core/ingestion/jolpica_adapter.py)
- **Local Disk Cache**: `backend/data/real_prerace_dataset.csv` (~1,360 rows)

```python
adapter = JolpicaAdapter()
records = adapter.fetch_historical_prerace_records([2022, 2023, 2024])
```

The adapter extracts driver qualifying position, race finishing position, constructor points share at that round, driver rolling form, and circuit metadata.

---

## 3. Feature Engineering (`core/features/feature_builder.py`)

Every driver-race observation is transformed into a standardized 9-dimensional vector $\mathbf{x} \in [0, 1]^9$:

| Index | Feature Name | Description | Normalization / Scaling |
|---|---|---|---|
| 0 | `grid_position_norm` | Qualifying grid slot | $(P_{\text{grid}} - 1) / 19$ |
| 1 | `quali_delta_to_pole_s` | Time delta to pole position (seconds) | $\min(\Delta t, 4.0) / 4.0$ |
| 2 | `driver_rolling_finish_norm` | 5-race rolling average finish position | $(P_{\text{rolling}} - 1) / 19$ |
| 3 | `driver_circuit_experience` | Prior Grand Prix starts at this specific venue | $\min(N_{\text{starts}}, 15) / 15$ |
| 4 | `constructor_pts_share` | Constructor points percentage in active championship | Pts share clipped to $[0, 0.40] / 0.40$ |
| 5 | `circuit_power_sensitivity` | Circuit engine power demand index | Track-specific scalar $[0.40, 0.95]$ |
| 6 | `circuit_downforce_index` | Aerodynamic downforce requirement | Track-specific scalar $[0.20, 0.95]$ |
| 7 | `circuit_is_street_track` | Flag for street circuit volatility | Binary ($1.0$ or $0.0$) |
| 8 | `race_rain_prob` | Pre-race weather forecast precipitation probability | Scalar $[0.0, 1.0]$ |

---

## 4. Modeling & Split-Conformal Calibration (`core/training/train.py`)

### 4.1 Chronological Partitions
The pre-race dataset is split strictly by chronological season:
- **Train Split ($\le 2023$)**: Used for model training and conformal calibration.
  - **Fit Fold (80%)**: Primary fitting partition ($N \approx 704$).
  - **Calibration Fold (20%)**: Held-out partition ($N = 176$) reserved strictly for calculating nonconformity scores.
- **Holdout Validation Split ($2024$)**: Test holdout ($N = 480$) used strictly for out-of-sample evaluation.

### 4.2 Candidate Benchmarking
Three model families are fitted on `Fit Fold` with aligned hyperparameters:
1. `GradientBoostingRegressor`: 120 estimators, learning rate 0.06, depth 4
2. `XGBRegressor`: 120 estimators, learning rate 0.06, depth 4, RMSE loss
3. `CatBoostRegressor`: 150 iterations, learning rate 0.06, depth 4

The winner is selected by validation $R^2$ on the $2024$ temporal holdout.

### 4.3 Split Conformal Prediction
On the held-out calibration set $(X_{\text{cal}}, y_{\text{cal}})$, absolute prediction residuals are calculated:
$$R_i = |y_i - \hat{f}(X_i)|, \quad i = 1, \dots, n_{\text{cal}}$$

For target coverage $1 - \alpha = 0.90$, the conformal quantile threshold $\hat{q}$ is derived via:
$$k = \lceil (n_{\text{cal}} + 1)(1 - \alpha) \rceil$$
$$\hat{q} = \text{Quantile}_{k / n_{\text{cal}}}(R)$$

For any new query $X_{\text{test}}$, the prediction band is guaranteed by:
$$C(X_{\text{test}}) = [\text{clip}(\hat{f}(X) - \hat{q}, 1, 20), \quad \text{clip}(\hat{f}(X) + \hat{q}, 1, 20)]$$

---

## 5. API Layer (`core/api/`)

FastAPI provides the REST contract with automatic OpenAPI schemas:

- **Endpoint**: `POST /api/core/predict`
- **Request**:
  ```json
  {
    "race_id": "silverstone",
    "driver_id": "NOR",
    "grid_position": 2,
    "rain_probability": 0.15
  }
  ```
- **Response**:
  ```json
  {
    "race_id": "silverstone",
    "driver_id": "NOR",
    "driver_name": "Lando Norris",
    "team_name": "McLaren",
    "grid_position": 2,
    "predicted_position": 2,
    "confidence_interval": [1, 8],
    "win_probability_pct": 24.5,
    "podium_probability_pct": 85.0,
    "model_version": "core-v1.0.0",
    "winning_model_family": "catboost",
    "model_trained_through_race_id": "season_2023_finale",
    "calibration_samples": 176,
    "data_snapshot_utc": "2026-09-03T14:21:00Z",
    "feature_contributions": [...],
    "summary_explanation": "..."
  }
  ```
- **Auxiliary Endpoints**:
  - `GET /api/health` — Liveness & readiness check
  - `GET /api/core/races` — Available 2024/2025 Grand Prix venues
  - `GET /api/core/drivers` — Standard starting driver roster and priors

---

## 6. Frontend UI (`frontend/src/`)

Built with **React 18 + Vite + TailwindCSS + Lucide Icons**:
- **Single Mode Screen**: [`CoreMode.tsx`](file:///frontend/src/modes/core/CoreMode.tsx)
- **Interactive Controls**: Grand Prix selector, driver selector, grid position override slider, rain probability slider.
- **Results Display**: [`PredictionCard.tsx`](file:///frontend/src/modes/core/PredictionCard.tsx) showing projected position, split-conformal interval, win/podium odds, and feature importance bar.
- **Header**: [`Header.tsx`](file:///frontend/src/components/Header.tsx) with UTC mission clock, brand badge, and live engine status indicator.
