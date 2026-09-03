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

## Features & Domain Reasoning (Zero-Leakage Pre-Race Priors)

APEX constructs a normalized 9-dimensional feature vector using **strictly point-in-time facts verifiably known prior to race start**. No live telemetry, lap times, pitstop deltas, or in-race sensor streams are utilized, ensuring absolute immunity to lookahead bias.

Every feature was selected based on fundamental aerodynamic, mechanical, and sporting principles governing Formula 1:

| Feature | Feature Key | Source | Domain Reasoning |
|---|---|---|---|
| **Constructor Points Share** | `constructor_pts_share` | Constructors' Standings | Team machinery pace dominates modern Formula 1. The top 3 constructors routinely capture >60% of all championship points. Car aerodynamic efficiency and power unit reliability set the baseline envelope for both drivers. |
| **Starting Grid Slot** | `grid_position_norm` | Official Qualifying Result | Starting grid position strongly dictates race finish (Spearman $\rho = 0.78$). First-corner track position determines traffic exposure, dirty air severity, and vulnerability to lap-1 collisions. |
| **Driver 5-Race Rolling Average** | `driver_rolling_finish_norm` | Historical Race Results | Recent form over the last 5 Grands Prix captures short-term driver confidence, tyre management form, and synergy with recent aerodynamic upgrade packages far better than lifetime career averages. |
| **Qualifying Pace Delta to Pole** | `quali_delta_to_pole_s` | Q3 Session Classification | The absolute time delta (in seconds) to the pole-sitter provides an unbiased quantitative measurement of single-lap raw package pace and tyre activation efficiency. |
| **Circuit Downforce Demand** | `circuit_downforce_index` | Track Engineering Profile | High-downforce circuits (Monaco, Singapore, Hungaroring) are highly overtaking-resistant, heavily preserving starting grid positions. Low-drag circuits (Monza, Spa) allow significantly more DRS-assisted overtakes. |
| **Circuit Power Sensitivity** | `circuit_power_sensitivity` | Track Engineering Profile | Circuits with prolonged full-throttle sections (Monza, Spa, Baku) reward engine thermal efficiency and MGU-K deployment over low-speed mechanical cornering grip. |
| **Street Circuit Indicator** | `circuit_is_street_track` | Track Classification | Street circuits feature zero runoff, unforgiving concrete barriers, and elevated Safety Car probabilities (~75%+ at Singapore/Monaco/Baku), dramatically amplifying non-linear outcome variance. |
| **Forecasted Rain Probability** | `race_rain_prob` | Official Meteorological Prior | Precipitation reduces tyre grip thresholds, nullifies pure aerodynamic downforce advantages, introduces intermediate/wet pitstop crossover gambles, and multiplies attrition. |
| **Driver Circuit Experience** | `driver_circuit_experience` | Historical Career Starts | Previous race starts at the specific track capture driver familiarity with braking reference markers, kerb ride characteristics, and thermal tyre degradation nuances. |

```
Pre-Race Inputs  ──▶  PreRaceFeatureBuilder  ──▶  9-dim Float32 Tensor [0.0, 1.0]  ──▶  CatBoost Model
```

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
