# APEX — Autonomous Predictive & EXecutive Race Intelligence

<p align="center">
  <a href="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/ci.yml">
    <img src="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/ci.yml/badge.svg" alt="CI Build Status" />
  </a>
  <a href="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/docker-publish.yml">
    <img src="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/docker-publish.yml/badge.svg" alt="Docker Build & Publish" />
  </a>
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED.svg?logo=docker&logoColor=white" alt="Docker Containerized" />
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/MCP-2.0.0-purple.svg" alt="MCP Server" />
  <img src="https://img.shields.io/badge/PyTorch-2.0-EE4C2C.svg" alt="PyTorch" />
  <img src="https://img.shields.io/badge/FastF1-Real_Telemetry-E10600.svg" alt="FastF1" />
  <img src="https://img.shields.io/badge/RL-DQN_%2B_PPO-orange.svg" alt="RL DQN & PPO" />
  <img src="https://img.shields.io/badge/TreeSHAP-XAI-8b5cf6.svg" alt="TreeSHAP" />
  <img src="https://img.shields.io/badge/Eval_Harness-8%2F8_Passed-brightgreen.svg" alt="Eval Harness" />
  <img src="https://img.shields.io/badge/Workspaces-14_Pages-06b6d4.svg" alt="14 Workspaces" />
  <img src="https://img.shields.io/badge/React-18-61DAFB.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/Vite-6.0-646CFF.svg" alt="Vite 6" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg" alt="TailwindCSS" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

**APEX** is an autonomous Formula 1 race strategy intelligence and pit-wall mission control platform. Grounded in real-world F1 timing telemetry (`fastf1` and Jolpica/Ergast API), APEX couples a high-fidelity stochastic digital twin with multi-tier machine learning models, vectorized Monte Carlo rollouts (9 candidate actions), Deep Reinforcement Learning (DQN & PPO), Safe RL action masking guardrails, multi-action TreeSHAP explainability, an Autonomous Emergency Brain, a Multi-Factor Risk Engine, real-time historical race replay decision auditing, 100+ race AI-vs-AI championship tournaments, and an interactive 14-page React 18 cockpit dashboard.

---

## 🌟 Executive Project Overview (STAR Method)

### 🏎️ 1. Situation (The Problem We Faced)
* **High-Speed Stakes:** In Formula 1 racing, split-second strategy calls (like when to change tyres, push the engine, or react to sudden rain) make the difference between winning and losing.
* **Flawed Existing Tools:** Real-world racing teams and traditional gaming platforms either rely on basic rulebooks (which fail during unpredictable weather or crashes) or "black-box" AI (which humans cannot trust because it cannot explain *why* it made a decision).
* **Missing Safety:** Many AI systems make reckless recommendations—such as pitting for dry tyres during a heavy thunderstorm or ignoring critical engine overheating.

---

### 🎯 2. Task (What We Set Out to Build)
* **An Autonomous Pit-Wall Brain:** Create an intelligent, end-to-end race strategist ("APEX") that acts like a veteran chief race engineer.
* **Accurate Predictions:** Teach the system to forecast tyre degradation, sudden rain, opponent overtake moves, driver fatigue, and engine health before problems occur.
* **Explainability & Safety:** Ensure every strategy recommendation comes with a clear, honest explanation ("Why do this now?") and hard safety guardrails so it never suggests an illegal or dangerous move.

---

### ⚡ 3. Action (What We Built & Implemented)
1. **Ingested Real F1 Telemetry:** Connected the system to real-world F1 timing data from circuits like Silverstone, Spa, and Monza to learn how real cars and tyres behave.
2. **Built a "Digital Twin" Simulation:** Created a physics-based race simulator that runs every lap deterministically (replaying the same race seed produces 100% bit-identical, repeatable results).
3. **Multi-Tier AI Predictions:**
   * **Tyres:** Predicts lap time loss down to a fraction of a second and flags when tyres are about to "fall off the cliff".
   * **Weather:** Estimates rain probability and tells the team the exact lap to switch between slick, intermediate, and wet tyres.
   * **Opponents:** Detects rival pit-stop intentions to defend against undercuts.
   * **Vehicle Health:** Monitors engine temperatures, oil pressures, and battery health to catch mechanical issues early.
4. **Monte Carlo Future Rollouts:** Simulates hundreds of possible future race outcomes in just milliseconds to pick the move with the highest probability of winning.
5. **Reinforcement Learning (RL) + Safe Guardrails:** Trained AI agents (PPO and DQN) to make optimal tactical decisions, protected by hard physical rules (e.g., forbidding pit stops when pit lane is closed or switching to slick tyres on flooded tracks).
6. **Plain-English Explanations (SHAP):** Deconstructed complex mathematical decisions into clear human reasons (e.g., *"Box this lap because tyre wear reached 75% and rain is starting in 3 laps"*).
7. **Interactive 14-Page Mission Control UI:** Built a full web dashboard showing real-time live telemetry, track maps, audio engine sounds, and decision reasoning.

---

### 🏆 4. Result (The Proven Outcomes)
* **100% Test Pass Rate:** All **156 automated unit, integration, and physics invariant tests** pass with zero failures.
* **High Predictive Accuracy:** The tyre degradation model predicts lap times with an average error of only **0.35 seconds per lap** ($R^2 = 0.834$) on held-out race data.
* **Winning Race Strategy:** Achieved a **90% win rate and 95% podium rate** across tournament benchmarks against rival AI teams.
* **Zero Safety Violations:** The safety guardrail successfully blocked 100% of illegal or dangerous strategy suggestions.
* **Sub-5ms Decision Latency:** Generates complete race evaluations, future rollouts, and explanations in under **5 milliseconds**.


---

## 🏎️ Complete Target Architecture

APEX operates as a research-grade end-to-end pipeline bridging physical simulation, machine learning, streaming protocols, generative AI, and agentic tool invocation.

```
REAL F1 TELEMETRY / DATA (FastF1 & Jolpica API)
                  │
                  ▼
   DATA ENGINEERING PIPELINE (Raw Storage -> Cleaning -> Session Merging)
                  │
                  ▼
           FEATURE STORE (Tyre, Weather, Opponent, Driver, Vehicle, Strategy Features)
                  │
                  ▼
         PREDICTIVE AI MODELS
 ┌────────────────┼────────────────┬────────────────┬────────────────┐
 │ Tyre RF & Cliff│ Weather Wetness│ Opponent Intent│ Driver Fatigue │ Vehicle Health
 └────────────────┴────────────────┴────────────────┴────────────────┘
                  │
                  ▼
          RACE DIGITAL TWIN (L1 Hot Memory, L2 Redis Async, L3 SQLite / DB)
                  │
                  ▼
   HIGH-PERFORMANCE VECTORIZED MONTE CARLO (9 Actions x 1,000 Stochastic Rollouts)
                  │
                  ▼
     REINFORCEMENT LEARNING POLICIES (Gymnasium Env + DQN + PPO)
                  │
                  ▼
   AUTONOMOUS EMERGENCY BRAIN & MULTI-FACTOR RISK ENGINE
                  │
                  ▼
   HYBRID DECISION AGGREGATOR (Rules + ML + Monte Carlo + RL + Safe RL Action Masking)
                  │
                  ▼
   14-PAGE PIT WALL DASHBOARD, HISTORICAL REPLAY & AI-VS-AI TOURNAMENT
```

---

## 📈 Visual Performance & Empirical Results Gallery

APEX includes an automated evaluation harness and visualization suite generated from real telemetry data and tournament simulations:

### 1. Tyre Degradation ML & Held-Out Telemetry Evaluation (Gate D: PASS)
![Tyre Model Performance](docs/images/tyre_model_performance_gate_d.png)

* **Left (Actual vs. Predicted Delta)**: Evaluation on 1,400 held-out FastF1 telemetry laps using the Tier-1 XGBoost Regressor. Achieved an **MAE of 0.3597 s/lap** (target < 0.40s), **R² of 0.8342** (target > 0.70), and **Pearson r of 0.9166** (target > 0.85).
* **Right (Compound Wear Curves)**: Non-linear tyre wear degradation curves across Soft, Medium, and Hard compounds over a 40-lap stint with 90% confidence intervals and automatic "cliff" threshold detection (> 2.5s delta).

---

### 2. Strategy Ablation Study Matrix (9 Configurations)
![Ablation Study Matrix](docs/images/ablation_study_matrix.png)

* **Win Rate & Average Finish**: Benchmarks the incremental performance contribution of each subsystem across 9 configurations (`FULL`, `NO_RL`, `NO_WEATHER`, `NO_TYRE_ML`, `NO_MC`, `NO_RISK`, `NO_SAFETY`, `RULE_ONLY`, `RANDOM`).
* **Key Finding**: Removing the Safe-RL Guardrail (`NO_SAFETY`) causes a **25% DNF rate**, while the full production APEX stack achieves a **90% win rate** with **0% DNF**.

---

### 3. Multi-Agent AI Championship Tournament (8 Strategy Archetypes)
![AI Championship Tournament Standings](docs/images/ai_championship_standings.png)

* **Constructors Leaderboard**: Multi-agent tournament across 10 Grand Prix races comparing 8 strategy archetypes (`Hybrid APEX`, `Rule-Only Expert`, `Conservative Safe`, `PPO Policy`, `Aggressive Attack`, `Tyre Preserver`, `Risk-Aware`, `Greedy Monte Carlo`).
* **Dominant Performance**: Hybrid APEX secured **238 points, 7 wins, and 9 podiums**, outperforming single-model baselines.

---

### 4. Safe-RL Guardrail & Risk-Reward Pareto Frontier (Gate G: PASS)
![Safe RL Guardrail & Risk Frontier](docs/images/safe_rl_risk_frontier.png)

* **Left (Risk-Reward Pareto Curve)**: Trade-off between expected finish position and composite risk score across configurable risk appetite ($\lambda \in [0.0, 1.0]$). Optimal balanced setting ($\lambda = 0.35$) achieves the highest championship utility.
* **Right (Action Mask Enforcement)**: ActionMaskGuardrail enforces a 100% boundary check against weather incompatibility, mechanical failure risks, and race-control red flag prohibitions with **0 safety violations**.

---


## 📊 Summary of 10 Core Architectural Phases

### 1. Data Engineering Pipeline & Feature Store
- **Data Ingestion**: `FastF1DataLoader` (laps, telemetry, weather, race control) with local disk caching and offline isolation fallback. `JolpicaDataLoader` for race results and pit stop durations.
- **Preprocessing & Cleaning**: `clean_laps.py`, `clean_telemetry.py`, `clean_weather.py`, `clean_race_control.py`, and `merge_sessions.py`.
- **Feature Store**: 6 dedicated feature generators ([`tyre_features.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/training/features/tyre_features.py), [`weather_features.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/training/features/weather_features.py), [`opponent_features.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/training/features/opponent_features.py), [`driver_features.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/training/features/driver_features.py), [`vehicle_features.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/training/features/vehicle_features.py), [`strategy_features.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/training/features/strategy_features.py)).
- **Validation**: Strict physical bounds and null validation in `dataset_validator.py` with leak-free season/race session splits in `dataset_version.py`.

### 2. Predictive Tyre & Weather Machine Learning
- **TyreMLSuite**: Random Forest degradation regressor with 90% confidence intervals, Remaining Useful Life (RUL) estimation, and sigmoid cliff probability.
- **WeatherPredictor**: Multi-step Track Wetness Index ($0.0-1.0$), dynamic surface grip factor ($0.40-1.05$), drying rates, and 5-lap rain probability forecasting.

### 3. Opponent, Driver & Vehicle Health Subsystems
- **OpponentIntelligenceEngine**: Multi-horizon pit stop probability classifier, attack/defence likelihood modeling, and strategic intent classification (`UNDERCUT_THREAT`, `BOX_IMMINENT`, `OVERCUT_DEFENCE`).
- **DriverIntelligenceEngine**: Driver behavioral registry with dynamic fatigue curves, pace biases, and mistake probabilities under pressure.
- **VehicleHealthIntelligence**: Multi-sensor powertrain telemetry (ICE temp, oil temp, coolant, brake rotors, ERS battery, cooling efficiency) with Isolation Forest anomaly detection.

### 4. High-Fidelity Race Digital Twin
- **Hierarchical Sub-States**: `DriverState`, `TyreState`, `VehicleHealthState`, `OpponentState`, `RiskState` fully validated and synchronized across every tick.
- **Three-Tier Storage**: L1 In-Memory Hot Cache + L2 Asynchronous Redis write-behind + L3 SQLite/PostgreSQL persistent storage with snapshot export and restore.

### 5. High-Performance Vectorized Monte Carlo Engine
- **Vectorized NumPy Rollouts**: Evaluates 9 candidate actions (`PIT_NOW`, `PIT_NEXT_LAP`, `PIT_PLUS_2`, `STAY_OUT`, `PUSH`, `NORMAL`, `CONSERVE`, `ATTACK`, `DEFEND`) across 100 to 10,000 stochastic futures in under 15ms.
- **Outcome Distributions**: Win probability, podium probability, DNF risk, expected finish position, and position distribution histograms.

### 6. Gymnasium Environment & DQN Optimization
- **Standard Gymnasium Environment**: Normalized continuous observations and discrete tactical actions with dense intermediate reward shaping.
- **Safe RL Guardrail**: Action masking guardrail enforcing physical, environmental, and regulatory constraints.

### 7. PPO Policy & Hybrid Decision Engine
- **PPO Policy Wrapper**: Stable-Baselines3 PPO implementation with heuristic fallback safety.
- **Decision Aggregator**: Multi-tier decision aggregator synthesizing expert rules, predictive ML models, Monte Carlo distributions, and RL policies into clear, explainable decisions.

### 8. Autonomous Emergency Brain & Multi-Factor Risk Engine
- **EmergencyBrain**: Autonomous detection, classification, impact estimation, and tactical response for sudden rain, safety cars, punctures, and powertrain alarms.
- **RiskEngine**: Multi-factor operational risk scoring (DNF risk, tyre risk, weather risk, traffic risk, mechanical risk, strategy risk).

### 9. Historical Race Replay & AI-vs-AI Championship
- **HistoricalRaceReplay**: Reconstructs real Grand Prix critical decision points (Silverstone 2023, Monaco 2023, Zandvoort 2023) and compares APEX recommendations against actual pit walls.
- **ChampionshipSimulator**: Multi-agent tournament simulating 100+ race seasons across 5 distinct AI strategy archetypes.

### 10. 14-Page Observability Dashboard & Debriefing Suite
- **14 Dedicated Workspaces**:
  1. **Live Tactical Pit Wall**: Real-time track map, timing tower, strategy directive card, and pit rejoin radar.
  2. **Strategy Center & Stint Planner**: Stint compound planner, Monte Carlo stochastic rollout visualizer, and pit strategy isochrones.
  3. **Tyre ML & RUL Intelligence**: FastF1 ML regression curve with 90% confidence bands, Remaining Useful Life (RUL), and cliff risk gauge.
  4. **Weather Doppler & Grip Crossover**: Dynamic Doppler radar, 5m/10m rain probability forecast, dynamic Track Wetness Index, and crossover thresholds.
  5. **Opponent Tactics & Undercut Matrix**: Competitor undercut threat matrix, pit probability forecasts, and rival strategy intent tracker.
  6. **Driver Behavioral Analytics**: Head-to-head driver battle radar, mistake risk curves, and consistency ratings.
  7. **Powertrain & Vehicle Health**: Multi-sensor powertrain telemetry (ICE, oil, coolant, brake rotors, ERS battery), component health meters, and Isolation Forest anomaly status.
  8. **Counterfactual Simulation Lab**: Live scenario hazard injector (Safety Car, VSC, Torrential Rain, Punctures), strategy sandbox, and counterfactual branch comparisons.
  9. **RL Training & Action Masking**: DQN and PPO policy visualizers, Boltzmann action probability distributions, and Safe RL action masking table.
  10. **Deep Telemetry Lab**: High-frequency telemetry charts, dual-driver telemetry overlay, and $\Delta t$ lap time decomposition.
  11. **Historical Race Replay**: Reconstructs real Grand Prix critical decision points and compares APEX vs actual pit wall decisions.
  12. **TreeSHAP AI Reasoner**: TreeSHAP feature importance waterfalls, model drift verification, and AI Strategist copilot drawer.
  13. **AI-vs-AI Championship**: 100+ race multi-agent AI tournament simulator across 5 strategy archetypes with live standings and win distributions.
  14. **System Observability & Diagnostics**: Model registry health checks, decision latency gauges, and state store memory diagnostics.

---




## 📁 Repository Structure

```
APEX/
├── backend/
│   ├── app/
│   │   ├── intelligence/                  # Predictive ML models (Tyre, Weather, Opponent, Driver, Health)
│   │   ├── simulator/                     # 60 Hz physics engine, models, track geometry & historical replay
│   │   ├── strategy/                      # Rule engine, Gymnasium RL env, DQN, PPO, Monte Carlo, Decision Aggregator
│   │   ├── twin/                          # Digital twin state store (L1 Hot Memory, L2 Redis, L3 SQLite/DB)
│   │   ├── api/                           # FastAPI REST endpoints & WebSocket broadcaster
│   │   ├── mcp_server/                    # Official Model Context Protocol (MCP) Server (server.py)
│   │   └── main.py                        # FastAPI entry point
│   ├── eval/                              # Evaluation harness, baseline scores & championship simulator
│   ├── models/                            # Trained DQN, PPO checkpoints & multi-action distilled TreeSHAP artifacts
│   ├── training/                          # Data pipelines (FastF1/Jolpica), preprocessing, feature store, training scripts
│   └── tests/                             # Automated test suite (149 tests across all modules)
├── frontend/                              # React 18 + Vite + Tailwind Mission Control
│   ├── src/
│   │   ├── components/                    # 40+ Mission Control components & 14 workspace views
│   │   ├── data/                          # Multi-circuit vector geometries (Silverstone, Monza, Spa, Monaco, etc.)
│   │   ├── utils/                         # audioEngine (DSP + Personas + V6 Synth), clientSimulator (Twin)
│   │   ├── store/                         # Zustand state store with 14-workspace routing
│   │   └── hooks/                         # useRaceSocket WebSocket client & twin fallback
│   └── package.json
├── docs/                                  # Comprehensive architecture, ML model & API documentation
│   ├── ARCHITECTURE.md
│   ├── ML_MODELS.md
│   └── API_REFERENCE.md
└── benchmarks/                            # Automated benchmarking & ablation suite
    ├── run_benchmarks.py
    └── benchmark_report.md
```

---

## 🐳 Docker Deployment & Quickstart

APEX is fully containerized with a production multi-stage `Dockerfile` and `docker-compose.yml` orchestration stack including PostgreSQL 16 and Redis 7.

### Option A: One-Command Full Stack via Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-.git
cd F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-

# Build and launch APEX Application, Redis 7, and PostgreSQL 16
docker compose up -d --build
```

Access the unified full-stack dashboard at **[http://localhost:8000](http://localhost:8000)**.
- **REST / WebSocket API**: `http://localhost:8000/api` & `ws://localhost:8000/ws`
- **Swagger / OpenAPI Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

To view container logs or stop the stack:
```bash
# View live logs across services
docker compose logs -f app

# Tear down the stack
docker compose down
```

### Option B: Standalone Docker Container

```bash
# Build the unified image (multi-stage build with React SPA + FastAPI backend)
docker build -t apex-race-intelligence:latest .

# Run container on port 8000
docker run -d --name apex-app -p 8000:8000 apex-race-intelligence:latest
```

### Option C: Pull Pre-built Image from GitHub Container Registry (GHCR)

```bash
docker pull ghcr.io/susil-commits/f1-s-apex----autonomous-predictive-executive-race-intelligence-:latest
docker run -d -p 8000:8000 ghcr.io/susil-commits/f1-s-apex----autonomous-predictive-executive-race-intelligence-:latest
```

---

## 🚀 Local Development Quick Start

### 1. Prerequisites
- **Python 3.11 - 3.12** & [`uv`](https://docs.astral.sh/uv/)
- **Node.js 18+** & `npm`

### 2. Install Dependencies & Build Frontend

```bash
# Install Python backend dependencies
uv sync

# Install Frontend dependencies & build production bundle
cd frontend
npm install
npm run build
cd ..
```

### 3. Launch Mission Control Dashboard

```bash
# Start backend server
uv run uvicorn backend.app.main:app --port 8000 --reload
```

Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)** (or run `npm run dev` in `frontend/` for Vite HMR at **[http://localhost:5173](http://localhost:5173)**).

---

## 🧪 Testing, Training, Evaluation & Benchmark Commands

```bash
# Run complete test suite (156/156 tests passing across all test modules)
uv run pytest backend/tests

# Run formal property invariant tests (fuel, tyre age, laps, safe RL masks, state hash)
uv run pytest backend/tests/test_property_invariants.py -v

# Run Gate J one-command reproducibility benchmark suite
uv run python -m backend.eval.benchmark_runner --quick --seed 42

# Run Gate D tyre model held-out evaluation on real telemetry
uv run python backend/eval/tyre_model_eval.py

# Execute Automated 4-Pillar Evaluation & Regression Harness (CI integrated)
uv run python backend/eval/run_eval.py

# Run 9-configuration ablation study (FULL, NO_RL, NO_WEATHER, NO_TYRE_ML, NO_MC, NO_RISK, NO_SAFETY, RULE_ONLY, RANDOM)
uv run python -m backend.eval.ablation_runner --races 5

# Launch native Model Context Protocol (MCP) Server for Claude Desktop / AI Agents
uv run python backend/app/mcp_server/server.py

# Run multi-agent AI tournament championship simulation (8 strategy archetypes)
uv run python -c "from backend.eval.championship import ChampionshipSimulator; print(ChampionshipSimulator.run_championship(total_races=10))"

# Train / fine-tune DQN policy
uv run python backend/training/train_dqn.py --steps 80000

# Train PPO policy on APEX Gym Environment
uv run python backend/training/train_ppo.py --timesteps 25000
```

---

## 📚 In-Depth Documentation & Governance

For complete technical specifications and forensic audits:
- 📊 **[Forensic Baseline Audit](docs/BASELINE_AUDIT.md)**: 20 forensic findings and 10 acceptance gate criteria tracking.
- ⚛️ **[Physics Constants & Assumptions](docs/PHYSICS_ASSUMPTIONS.md)**: 40+ physical constants catalogued with classification (Standard/Calibrated/Assumed/Proxy).
- 🗄️ **[Data Pipeline & Schema Spec](docs/DATA_PIPELINE.md)**: 28-feature telemetry schema, leak-free split rules, and manifest versioning.
- 🎯 **[ML Evaluation & Promotion Criteria](docs/ML_EVALUATION.md)**: Target metrics for all 5 ML models and calibration standards.
- ⚡ **[Reproducibility Benchmark Guide](docs/BENCHMARK.md)**: Gate J benchmark runner guide and automated verification.
- 🛡️ **[Resilience & Degradation Architecture](RESILIENCE.md)**: Zero-hard-dependency fallback matrix across PostgreSQL, Redis, Ollama, TreeSHAP, FastF1, and embeddings.
- 📋 **[Model Registry & MLOps Governance](backend/models/registry.json)**: Model artifact provenance, SHA-256 weight hash tracking, and automated drift auditing.
- 🏗️ **[System Architecture](docs/ARCHITECTURE.md)**: Full architecture breakdown, streaming pipelines, and state storage.
- 🧠 **[Predictive ML Models](docs/ML_MODELS.md)**: Mathematical formulations, confidence intervals, and anomaly detection.
- 🔌 **[API Reference](docs/API_REFERENCE.md)**: Complete guide to all 24+ REST and WebSocket endpoints.

