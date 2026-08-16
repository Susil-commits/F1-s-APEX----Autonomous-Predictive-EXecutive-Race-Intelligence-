# APEX — Autonomous Predictive & EXecutive Race Intelligence

**An AI-driven race strategy system that maintains a digital twin of an F1-style race, predicts future states, and recommends optimal decisions (pit, push, defend, conserve) under uncertainty.**

---

## 1. Overview

APEX is not a lap-time predictor. It is a **decision-intelligence system**: given the current state of a race, it answers *"what should the team do right now, and why?"*

The system is built around one repeating loop:

```
Observe State → Predict Future → Simulate Options → Decide → Act → Update State → Learn
```

This loop is the actual portfolio value — it's the same pattern used in robotics, autonomous trading, and operations research. Everything below exists to implement that loop cleanly, end to end, with one real racing domain wrapped around it.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          RACE SIMULATOR                              │
│         (deterministic physics + event engine — ground truth)        │
└───────────────────────────────┬───────────────────────────────────┘
                                 │ race telemetry (state ticks)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DIGITAL TWIN LAYER                            │
│   Live mirrored state: cars, tyres, fuel, weather, track, gaps       │
│   Stored in Redis (hot state) + PostgreSQL (historical/event log)    │
└───────────────────────────────┬───────────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
        ┌────────────────┐ ┌───────────┐ ┌────────────────┐
        │ Tyre Model      │ │ Weather   │ │ Race State      │
        │ (degradation,   │ │ Model     │ │ Feature Builder │
        │ pit-window ETA) │ │ (rain     │ │ (encodes state  │
        │                 │ │ prob.)    │ │ → vector)       │
        └────────┬────────┘ └─────┬─────┘ └────────┬────────┘
                 └───────────────┼────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │      STRATEGY ENGINE      │
                    │  Rule-based baseline  +   │
                    │  DQN Agent (learned policy)│
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │  COUNTERFACTUAL CHECK     │
                    │  "What if we pit now vs   │
                    │   in 3 laps?" — quick      │
                    │   rollout comparison       │
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   EXPLAINABILITY LAYER    │
                    │  Structured reasoning:    │
                    │  state → decision → why   │
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   FastAPI + WebSocket      │
                    │   API / Event Broadcast    │
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   React Dashboard          │
                    │   Live race view + replay   │
                    │   + strategy reasoning      │
                    └─────────────────────────┘
```

---

## 3. Core Modules (Detailed)

### 3.1 Race Simulator (Ground Truth Engine)
The deterministic core everything else depends on. It owns lap-time calculation, fuel burn, tyre wear accumulation, gaps between cars, and event injection (Safety Car, rain onset, incidents).

- Runs as a discrete-event or fixed-timestep loop (1 tick = 1 lap or sub-lap segment).
- Must be **fully deterministic given a seed** — this is what makes your DQN agent trainable and your benchmarks reproducible.
- Exposes a clean `RaceState` object (Pydantic model) every tick — this is the single contract every other module reads from.
- Design this module *first* and get it boring and correct before touching any ML. If the ground truth is wrong, every model built on top of it is wrong.

### 3.2 Digital Twin Layer
The live, queryable mirror of race state — not a separate ML model, an *infrastructure layer*.

- **Redis**: current tick's full state (cars, tyres, gaps, flags) — sub-millisecond reads for the dashboard and the strategy engine.
- **PostgreSQL**: append-only event log of every tick + every decision made + outcome. This is what lets you do replay, benchmarking, and "show your work" in interviews.
- Twin update is push-based: simulator emits a state diff each tick, twin layer applies it, WebSocket layer broadcasts it.

### 3.3 Tyre Intelligence
Predicts degradation curve, remaining useful life, and lap-time loss per compound.

- Start with a physics-informed baseline (linear/quadratic wear model) so you always have a sane fallback.
- Layer a gradient-boosted regressor (XGBoost) trained on simulated laps to predict lap-time delta from tyre age, compound, track temp, and driving mode (push/conserve).
- Output: `pit_window_start`, `pit_window_end`, `predicted_lap_time_loss`.

### 3.4 Weather Intelligence
Rain probability and drying-rate estimation, feeding into "should we switch to wets/inters."

- Can run on a synthetic weather generator for the simulator (Markov-chain rain state transitions) — you don't need real meteorological data to make this legitimate; you need to show you understand probabilistic forecasting.
- A simple classifier (logistic regression or small gradient-boosted model) predicting `rain_probability_next_N_laps` from current trend is enough. Don't over-build this one.

### 3.5 Race State Feature Builder
Converts the raw digital twin state into a fixed-size feature vector — this is what both the rule engine and the DQN agent consume.

- This is a deceptively important module: your RL agent's performance depends entirely on what you choose to encode (gap to car ahead/behind, tyre age, fuel load, laps remaining, rain probability, track position).
- Keep it as a single well-tested function: `RaceState -> np.ndarray`. Version it — if you change the feature vector, old trained models become invalid.

### 3.6 Strategy Engine
Two tiers, built in this order:

1. **Rule-based baseline** — explicit if/else logic (pit if tyre_life < threshold AND no undercut risk, etc). This is your fallback, your sanity check, and your benchmark opponent.
2. **DQN Agent** — trained via self-play against the deterministic simulator using Gymnasium + Stable-Baselines3. Action space: `{push, conserve, pit_soft, pit_medium, pit_hard, no_pit}`. Reward: shaped around finishing position / time delta, not just "did it pit at the right lap" — naive reward shaping is the #1 way these agents fail, budget real time here.

### 3.7 Counterfactual Check (lightweight, not full Monte Carlo)
Before committing to a decision, roll the simulator forward N laps under 2-3 candidate strategies and compare outcomes.

- This is NOT the full "thousands of simulated futures" from the original spec — it's 3-5 fast forward-rollouts per decision point. Honest scope, still demonstrates the concept.

### 3.8 Explainability & Model Distillation Layer
For every recommendation, APEX provides transparent, multi-tiered explainability:
1. **Rule Engine & Margin Decomposition**: Structured `DecisionExplanation` object capturing which heuristic rules fired, DQN $Q$-value margin ($\Delta Q = Q_1 - Q_2$), and tyre cliff risk.
2. **TreeSHAP via Model Distillation**: TreeSHAP requires a tree-based architecture, whereas the DQN is a neural network (`MlpPolicy`). APEX trains a tree surrogate model (`GradientBoostingRegressor` / `XGBoost`) distilled directly from thousands of real DQN rollout steps across tracks and logged database telemetry (`DecisionLogModel`). `shap.TreeExplainer` decomposes this distilled surrogate into exact additive Shapley contributions $f(x) = \phi_0 + \sum \phi_i(x)$, providing a mathematically defensible and faithful explanation of policy preferences.
3. **Graceful Fallback**: If no distilled model is present on disk, `TreeSHAPExplainer` falls back to a calibrated domain heuristic surrogate with an explicit log warning.

---

## 4. Modern Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Simulation & ML | Python 3.12, NumPy, Pandas | Core numerical work |
| Tyre/Weather models | XGBoost, scikit-learn | Fast, explainable, no GPU needed |
| RL | Gymnasium + Stable-Baselines3 (DQN) | Standard, well-documented RL stack |
| Experiment tracking | MLflow (self-hosted, local) | Track training runs, compare policies — strong signal in interviews |
| Backend API | FastAPI (async) + Pydantic v2 | Modern, typed, auto-generates OpenAPI docs |
| Real-time updates | WebSockets (native FastAPI) | Live race feed to dashboard |
| Hot state | Redis | Sub-ms current-state reads |
| Persistent store | PostgreSQL + SQLAlchemy 2.0 (async) + Alembic | Event log, replay, migrations |
| Task/dependency mgmt | `uv` (or Poetry) | Modern, fast Python dependency management |
| Frontend | React 18 + Vite + TypeScript | Type-safe, fast dev loop |
| Styling | Tailwind CSS | Fast, consistent design system |
| Charts | Recharts | Tyre wear, lap time, gap graphs |
| State mgmt (frontend) | Zustand or TanStack Query | Simple, modern, avoids Redux boilerplate |
| Containerization | Docker + docker-compose | One-command local spin-up (Postgres + Redis + API + frontend) |
| CI | GitHub Actions | Lint + test on push — shows engineering hygiene |
| Testing | Pytest (backend), Vitest (frontend) | Standard modern test stacks |

---

## 5. Data Flow (Single Decision Cycle)

1. Simulator advances one tick → emits new `RaceState`.
2. Digital Twin layer writes state to Redis, appends event to Postgres.
3. Feature Builder converts state → feature vector.
4. Tyre + Weather models score the current vector, attach predictions to state.
5. Strategy Engine (rule engine + DQN) proposes an action.
6. Counterfactual Check rolls forward 2-3 alternatives, compares.
7. Explainability Layer logs the reasoning trail.
8. Decision + explanation broadcast over WebSocket to the dashboard, and persisted to Postgres.
9. Simulator applies the action (or the human overrides it via the dashboard) and the loop repeats.

---

## 6. Database Design (Core Tables)

- `races` — race_id, config (track, laps, weather_seed), created_at
- `race_ticks` — race_id, lap_number, full state snapshot (JSONB), timestamp
- `decisions` — race_id, lap_number, action_taken, source (rule_engine/dqn), confidence, explanation (JSONB)
- `model_runs` — model_version, training_config, metrics, mlflow_run_id
- `benchmark_results` — race_id, policy_name (dqn/rule_based/random), final_position, total_time_delta

---

## 7. Evaluation & Benchmarking (Your Strongest Interview Material)

Run the same set of race seeds through three policies and compare:

1. **Random baseline** — sanity floor.
2. **Rule-based engine** — your honest, explainable baseline.
3. **DQN agent** — your learned policy.

Report: average finishing position, average time delta vs optimal (computed via exhaustive search on a small race), pit-timing accuracy vs a known-good window. **This comparison table is the single most valuable artifact in the whole project** — it proves you understand evaluation, not just training.

---

## 8. Development Roadmap

1. Deterministic race simulator + `RaceState` contract
2. Digital Twin layer (Redis + Postgres wiring)
3. Feature Builder
4. Tyre degradation model
5. Weather model
6. Rule-based Strategy Engine (get this solid — it's your fallback and benchmark)
7. Gymnasium environment wrapper around the simulator
8. DQN training loop + MLflow tracking
9. Lightweight counterfactual rollout check
10. Explainability layer
11. FastAPI + WebSocket backend
12. React dashboard (live view + replay + reasoning panel)
13. Benchmark suite (rule-based vs DQN vs random) + write-up

---

## 9. What Makes This "Advanced" Without Overreaching

- Full async backend (FastAPI + SQLAlchemy 2.0 async) — most fresher projects are sync Flask/Express CRUD; this signals real backend maturity.
- Real RL, not "I called an API" — trained, benchmarked, explainable.
- MLflow experiment tracking — shows you understand ML engineering, not just model-fitting.
- Explainability as a first-class system component, not an afterthought.
- Deterministic, seeded simulation — shows you understand reproducibility, a real ML engineering concern.
- Benchmarked against baselines — most portfolio projects skip this entirely; it's the difference between "I built a model" and "I evaluated a system."

---

## 10. Explicitly Out of Scope (and why)

- Multi-agent AI-vs-AI championships — adds complexity without adding interview signal.
- Full Monte Carlo (thousands of rollouts) — replaced with a lightweight 3-5 rollout counterfactual check that demonstrates the same concept honestly.
- PPO / advanced RL algorithms — DQN is enough to demonstrate RL competence; overreaching here risks a shallow, unexplainable implementation.
- Real-world F1 data ingestion — synthetic/simulated data is fine and actually preferable, since it keeps the simulator deterministic and trainable.
