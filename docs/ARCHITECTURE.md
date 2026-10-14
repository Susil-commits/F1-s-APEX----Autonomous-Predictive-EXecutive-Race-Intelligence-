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
              │  10 deterministic features  │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  core/models/               │
              │  apex_core_v1_model.joblib  │
              │  CatBoostRegressor          │
              │  (selected on 2023 val      │
              │   benchmark vs XGB / GBR,   │
              │   refitted on 2022+2023)    │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  Split-Conformal Calibration│
              │  N=176 calibration samples  │
              │  q̂ = ±5.67 positions        │
              │  94.4% empirical coverage   │
              │  (exceeds 90% target)       │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │  core/api/                  │
              │  FastAPI  POST /predict     │
              │  GET /health  GET /version  │
              │  GET /metrics               │
              │  POST /api/core/drift/check │
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

## Features & Domain Reasoning (Zero-Leakage Pre-Race Priors)

APEX constructs a normalized 10-dimensional feature vector using **strictly point-in-time facts verifiably known prior to race start**. No live telemetry, lap times, pitstop deltas, or in-race sensor streams are utilized, ensuring absolute immunity to lookahead bias.

Every feature was selected based on fundamental aerodynamic, mechanical, and sporting principles governing Formula 1:

| Feature | Feature Key | Source | Domain Reasoning |
|---|---|---|---|
| **Constructor Points Share** | `constructor_pts_share` | Constructors' Standings | Team machinery pace dominates modern Formula 1. The top 3 constructors routinely capture >60% of all championship points. Car aerodynamic efficiency and power unit reliability set the baseline envelope for both drivers. |
| **Starting Grid Slot** | `grid_position_norm` | Official Qualifying Result | Starting grid position strongly dictates race finish (Spearman $\rho = 0.82$). First-corner track position determines traffic exposure, dirty air severity, and vulnerability to lap-1 collisions. |
| **Driver 5-Race Rolling Average** | `driver_rolling_finish_norm` | Historical Race Results | Recent form over the last 5 Grands Prix captures short-term driver confidence, tyre management form, and synergy with recent aerodynamic upgrade packages far better than lifetime career averages. |
| **Qualifying Pace Delta to Pole** | `quali_delta_to_pole_s` | Q3 Session Classification | The absolute time delta (in seconds) to the pole-sitter provides an unbiased quantitative measurement of single-lap raw package pace and tyre activation efficiency. |
| **Circuit Downforce Demand** | `circuit_downforce_index` | Track Engineering Profile | High-downforce circuits (Monaco, Singapore, Hungaroring) are highly overtaking-resistant, heavily preserving starting grid positions. Low-drag circuits (Monza, Spa) allow significantly more DRS-assisted overtakes. |
| **Circuit Power Sensitivity** | `circuit_power_sensitivity` | Track Engineering Profile | Circuits with prolonged full-throttle sections (Monza, Spa, Baku) reward engine thermal efficiency and MGU-K deployment over low-speed mechanical cornering grip. |
| **Street Circuit Indicator** | `circuit_is_street_track` | Track Classification | Street circuits feature zero runoff, unforgiving concrete barriers, and elevated Safety Car probabilities (~75%+ at Singapore/Monaco/Baku), dramatically amplifying non-linear outcome variance. |
| **Forecasted Rain Probability** | `race_rain_prob` | Official Meteorological Prior | Precipitation reduces tyre grip thresholds, nullifies pure aerodynamic downforce advantages, introduces intermediate/wet pitstop crossover gambles, and multiplies attrition. |
| **Mid-Race Weather Transition Flag** | `weather_transition_flag` | Official Weather Forecast | Binary flag indicating high probability of rain onset or drying conditions mid-race, triggering mandatory intermediate/wet crossover pit-stops. |
| **Driver Circuit Experience** | `driver_circuit_experience` | Historical Career Starts | Previous race starts at the specific track capture driver familiarity with braking reference markers, kerb ride characteristics, and thermal tyre degradation nuances. |

> **Removed Dead Features**:
> `sector_1_delta_norm`, `sector_2_delta_norm`, and `sector_3_delta_norm` were previously defined but absent from `real_prerace_dataset.csv` (filled with 0.0 constant values). They were permanently dropped in v1.0.1, reducing dimensionality from 13 to 10 with zero loss in predictive fidelity (+0.008 MAE delta) while eliminating synthetic zero-imputation and cleaning up the API contract.

```
Pre-Race Inputs  ──▶  PreRaceFeatureBuilder  ──▶  10-dim Float32 Tensor [0.0, 1.0]  ──▶  CatBoost Model
```

## Data Architecture & Training Pipeline

- **Training & Selection Data**: Jolpica F1 API historical seasons 2022–2023 (N=880 driver-race entries)
  - **Selection Training Set**: 2022 season (N=440) — used to fit candidate architectures (GBR, XGBoost, CatBoost)
  - **Selection Validation Set**: 2023 season (N=440) — used to select the winning architecture without touching 2024 data
  - **Refit Set**: 2022 + 2023 combined (N=880) — winner is refitted on all historical data prior to 2024
- **Calibration Fold**: Last 20% of 2022–2023 chronologically (N=176 driver entries) — used to calibrate the conformal prediction interval width ($q̂ = \pm 5.673$)
- **Holdout Test Set**: Full 2024 season (N=479 driver entries) — strictly held out chronologically and evaluated **once** after refit
- **Regulations Corpus**: `core/data/regulations/` contains **3 curated domain summaries** (DRS, Parc Fermé, Tyre/Weather rules) used for tactical lever grounding by the RAG narration layer (`core/api/narration.py`). These are concise curated summaries, not official FIA statutory documents.

## Deployment

- **Backend**: Single Uvicorn process, Python 3.12-slim Docker image (~280MB) with threadpool offloading for CPU-bound inference
- **Frontend**: Static Vite build served via Nginx or Vercel CDN
- **No external stateful services required** — zero dependency on external databases, Redis, or Kafka for core inference

## What is NOT in V1 (preserved in `v1-v5-exploration`)

- PPO / DQN reinforcement learning agents
- 60Hz vehicle digital twin
- Kafka streaming race state
- LangGraph multi-agent deliberation
- SHAP surrogate explainer
- MCP tool server
- Pit-wall multi-panel UI
