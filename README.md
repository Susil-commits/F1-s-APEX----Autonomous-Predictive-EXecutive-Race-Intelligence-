# APEX — Autonomous Predictive & EXecutive Race Intelligence

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyTorch-2.2+-EE4C2C.svg" alt="PyTorch" />
  <img src="https://img.shields.io/badge/Stable--Baselines3-DQN-brightgreen.svg" alt="Stable-Baselines3" />
  <img src="https://img.shields.io/badge/React-18-61DAFB.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg" alt="TailwindCSS" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

**APEX** is an AI-driven race strategy decision-intelligence system. Given the live telemetry and state of an F1-style race, APEX maintains a real-time digital twin, forecasts tyre degradation curves and weather transitions, executes forward counterfactual rollouts ("what-if" simulations), and recommends optimal pit/push/conserve decisions under uncertainty with structured explainability.

---

## 🏎️ Core Architecture Loop

```mermaid
graph LR
    Observe["1. Observe State (Digital Twin)"] --> Predict["2. Predict Future (Tyre & Weather)"]
    Predict --> Simulate["3. Simulate Options (Counterfactuals)"]
    Simulate --> Decide["4. Decide (Rule Engine + DQN)"]
    Decide --> Explain["5. Explain (Reasoning Trail)"]
    Explain --> Act["6. Act & Broadcast (WebSocket + UI)"]
```

```
Observe State ➔ Predict Future ➔ Simulate Options ➔ Decide ➔ Explain ➔ Act & Learn
```

---

## 🌟 Key Features

1. **Deterministic Ground Truth Race Simulator**:
   - Seeded, 100% reproducible multi-car physics engine.
   - Non-linear tyre wear per compound (`SOFT`, `MEDIUM`, `HARD`, `INTERMEDIATE`, `WET`) with sharp cliff penalties.
   - Dynamic fuel burn, dirty air turbulence in corners, DRS slipstream, and Safety Car / VSC state machine.

2. **Predictive Intelligence & Feature Builder**:
   - 28-dimensional normalized feature extractor.
   - Remaining useful life (RUL) estimator and weather transition Markov model.

3. **Hybrid Decision Engine (Rule Baseline + DQN Policy)**:
   - **Rule-Based Expert Baseline**: Multi-tier strategic heuristics for pit windows, safety car opportunities, undercut attacks, and tyre preservation.
   - **Deep Q-Network (DQN) Agent**: Trained in Gymnasium with shaped reward signals for overtaking, clean air delta, and tyre cliff avoidance.

4. **Counterfactual "What-If" Rollout Comparator**:
   - Clones current race state and simulates 4-5 alternative strategies forward 4 laps in milliseconds to validate why one choice outperforms others.

5. **Transparent Explainability Layer**:
   - Multi-factor structured reasoning logs (`State ➔ Logic ➔ Decision`), combining rule checks and Q-value margins.

6. **React 18 + Vite Mission Control Dashboard**:
   - **Timing Tower**: Positions P1–P10, gap to leader, tyre compound badges, live wear bars, and fastest lap highlights.
   - **2D Circuit Map**: Animated SVG track map tracking all 10 cars in real-time.
   - **Live Telemetry Charts**: Recharts tyre degradation vs 78% cliff limit and pace delta vs leader.
   - **Strategy Card & Overrides**: Active recommendation with AI confidence score, urgency badge, and pit wall override triggers.
   - **Explainability & Counterfactual Panel**: Live reasoning tree and what-if rollout comparison table.

---

## 📊 Evaluation & Benchmark Matrix

Automated head-to-head evaluation across 15 seeded 52-lap races on the **Silverstone Grand Prix Circuit**:

| Policy | Avg Finishing Position | Win Rate (%) | Podium Rate (%) | Avg Gap to P1 (s) | Blown Tyre Laps | Avg Pit Stops |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RANDOM BASELINE** | 7.40 | 13.3% | 26.7% | +87.68s | 19.53 | 0.0 |
| **RULE-BASED ENGINE** | **1.07** | **93.3%** | **100.0%** | **+0.23s** | **0.00** | 3.5 |
| **TRAINED DQN POLICY** | 4.33 | 53.3% | 60.0% | +79.43s | 9.87 | 2.2 |

---

## 📁 Repository Structure

```
APEX/
├── pyproject.toml                         # Python project & dependencies (uv managed)
├── docker-compose.yml                     # Redis + Postgres container configuration
├── backend/
│   ├── app/
│   │   ├── simulator/                     # Deterministic physics engine & Pydantic models
│   │   ├── intelligence/                  # Feature builder, tyre & weather models
│   │   ├── strategy/                      # Rule engine, Gymnasium RL env, DQN agent, counterfactuals, explainability
│   │   ├── twin/                          # State persistence store
│   │   ├── api/                           # FastAPI routes & WebSocket broadcaster
│   │   └── main.py                        # FastAPI entry point
│   ├── training/                          # RL training scripts
│   └── tests/                             # Pytest integration & unit test suite
├── frontend/                              # React 18 + Vite + Tailwind Mission Control
│   ├── src/
│   │   ├── components/                    # TimingTower, TrackMap, TelemetryCharts, StrategyCard, etc.
│   │   ├── store/                         # Zustand state store
│   │   └── hooks/                         # useRaceSocket WebSocket client
│   └── package.json
└── benchmarks/                            # Automated evaluation suite
    ├── run_benchmarks.py
    └── benchmark_report.md
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11 - 3.12** & [`uv`](https://docs.astral.sh/uv/)
- **Node.js 18+** & `npm`

### 2. Install Dependencies

```bash
# Install Python backend dependencies
uv sync

# Install Frontend dependencies
cd frontend
npm install
npm run build
cd ..
```

### 3. Launch Mission Control Dashboard

```bash
uv run uvicorn backend.app.main:app --port 8000 --reload
```

Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)**.

---

## 🧪 Testing & Benchmarks

```bash
# Run all unit and integration tests
uv run pytest

# Re-run automated strategy benchmark evaluation
uv run python benchmarks/run_benchmarks.py

# Train / fine-tune DQN policy
uv run python backend/training/train_dqn.py --steps 15000
```

---

## 📄 License
MIT License. Created by Susil.
