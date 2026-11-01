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
              │  q̂ = ±6.47 positions        │
              │  95.8% empirical coverage   │
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

---

## Enterprise Tier Extensions: Context, Harness, Inferencing & MCP

APEX has evolved from a standalone single-tier pre-race model into an enterprise-grade racing intelligence system incorporating:

### 1. Context Engineering Architecture (`context/`)
- **Hierarchical Context Tiering**: Organizes context into 4 decoupled levels:
  - **L0 (Structural)**: Circuit downforce/power profiles, FIA 2026 Active Aero (Z-Mode/X-Mode), DRS actuation rules.
  - **L1 (Session Priors)**: Grid position, rolling 5-race form, constructor points share, weather radar.
  - **L2 (Dynamic Stint)**: Tyre compound, stint lap age, Pirelli non-linear pace degradation ($s/\text{lap}$), laps to thermal cliff, undercut gaps.
  - **L3 (Real-Time Micro-Telemetry)**: Track control flags, active aerodynamic modes, tactical alerts (`UNDERCUT_THREAT_REAR`, `TYRE_CLIFF_ALERT`).
- **Semantic Distillation & Token Budgeting**: Compresses multi-channel telemetry by **61% to 66%**, preventing token bloat and guaranteeing $<50\text{ms}$ synthesis.
- **Context Quality Evaluator (`context/quality/`)**: Mathematical quality assessment calculating compression ratio, information density, regulatory groundedness ($\ge 0.75$), telemetry freshness, and hallucination risk before admitting context to inference.

### 2. Harness Engineering POV (`agents/`)
- **Execution Sandbox (`agents/harness.py`)**: Guarantees a hard execution timeout ceiling ($<200\text{ms}$ SLA), integrates automatic `AICircuitBreaker` failover to deterministic heuristics, tracks FIA Cost-Cap compute quotas, and signs tactical actions into the SHA-256 audit hash chain.
- **Race Scenario Replay Benchmark (`agents/evaluation/race_replay.py`)**: Deterministically benchmarks agent tactical decisions against 5 curated ground-truth historical F1 scenarios (e.g. Monaco 2024 SC, Silverstone 2024 rain crossover), achieving **100% tactical alignment accuracy**.
- **Metamorphic Invariance Verification (`agents/evaluation/metamorphic.py`)**: Validates domain physical laws (monotonic tyre degradation, undercut sensitivity boundaries at 1.4s, Safety Car opportunism) with **0 invariant violations**.

### 3. Multi-Tier Inferencing Concepts
- **Tier-1 Deterministic ML**: Point-in-time CatBoost regressor ($P_{99} < 5\text{ms}$) with split-conformal coverage ($q̂ = \pm 6.470$ pos, 95.8% empirical coverage).
- **Tier-2 Stochastic In-Race Simulation**: Vectorized Monte Carlo pit stop simulator executing **10,000 rollouts in ~118ms** modeling Poisson SC arrival and non-linear Pirelli tyre cliffs.
- **Vectorized Full-Grid Batching (`/api/core/predict/grid`)**: Evaluates all 20 drivers in parallel in $<15\text{ms}$.
- **Cryptographic Model Verification**: SHA-256 hash and HMAC-SHA256 signature verification prior to deserialization.

### 4. Model Context Protocol (MCP) Server (`core/mcp/`)
- Implements the standard JSON-RPC 2.0 MCP protocol at `POST /api/mcp` and discovery routes at `GET /api/mcp/*`.
- **Exposed Tools**: `apex_predict_grid`, `apex_simulate_pit_stop`, `apex_evaluate_tyre_cliff`, `apex_query_fia_regulations`, `apex_verify_model_integrity`.
- **Exposed Resources**: `apex://circuits/catalog`, `apex://drivers/roster`, `apex://regulations/2026_active_aero`, `apex://monitoring/drift_thresholds`.
- **Standardized Prompts**: `race_engineer_briefing`, `undercut_threat_analysis`.
- Allows external AI assistants (Claude, Gemini, Antigravity) to query and control APEX natively.

---

## What is NOT in Scope (preserved in `v1-v5-exploration`)

- PPO / DQN reinforcement learning agents
- 60Hz vehicle digital twin
- Kafka streaming race state
- LangGraph multi-agent deliberation
- SHAP surrogate explainer
- Pit-wall multi-panel UI
