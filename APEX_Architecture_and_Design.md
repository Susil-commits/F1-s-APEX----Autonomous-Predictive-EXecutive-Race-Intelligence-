# APEX — Autonomous Predictive & Counterfactual Decision Intelligence Architecture

**An AI/ML Decision Intelligence and Experimentation Platform for Sequential, Uncertain Operational Decisions in Formula 1 Race Strategy.**

---

## 1. System Philosophy & Value Proposition

APEX is not a passive telemetry viewer or a simulator toy. It is an **enterprise-grade decision-intelligence system**: given the stochastic, time-critical state of an operational race environment, it answers:

$$\text{"What optimal action should the team execute right now, what are the counterfactual risks, and why?"}$$

The core decision intelligence loop:

```
Telemetry Ingestion (60Hz) 
         ↓
Data Validation & Cleaning 
         ↓
Low-Latency Feature Store (0.0245ms p99)
         ↓
Predictive ML Models (XGBoost, Weather, Opponents) 
         ↓
Uncertainty Quantification (95% CI Bands)
         ↓
Counterfactual Simulation (1,000 Rollouts & Isochrones) 
         ↓
Decision Optimization & Safe RL Guardrails 
         ↓
TreeSHAP Feature Attributions & RAG Grounding 
         ↓
Planner Agent + Domain MCP Tools 
         ↓
Human Review / Pit Wall Copilot 
         ↓
Outcome & System Ablation Evaluation
```

---

## 2. High-Level Decision Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           AI & DECISION INTELLIGENCE CORE                               │
│  • Predictive ML (XGBoost R²=0.8342, 95% Conformal Uncertainty Interval [0.31, 0.61])    │
│  • Counterfactual Lab (1,000 Monte Carlo Stochastic Rollouts & Isochrone Curves)        │
│  • Safe RL Action Masking (100% Boundary Enforcement, 0.0% Catastrophic DNFs)           │
│  • TreeSHAP Additive Local Attributions & Context Lineage Retrieval                     │
│  • Primary Planner Agent (Planner → Context → Tools/MCP → Evidence → Decision)           │
└────────────────────────────────────────────▲────────────────────────────────────────────┘
                                             │
                                             │ (Grounded Context & Lineage DAG)
                                             │
┌────────────────────────────────────────────┴────────────────────────────────────────────┐
│                    CANONICAL RACE CONTEXT & DATA PROVENANCE LAYER                       │
│  TelemetryStream → FeatureSet → Model → Prediction →                                   │
│  StrategyCandidate → Counterfactual → Decision → Outcome                                │
│  • Model Cards & Checksums (XGBoost, PINN, Radar, DQN, PPO, Anomaly)                     │
│  • Immutable Prediction Provenance Records (prediction_id, model, dataset, schema, CI)   │
└────────────────────────────────────────────▲────────────────────────────────────────────┘
                                             │
                                             │ (High-Throughput Streaming & Caching)
                                             │
┌────────────────────────────────────────────┴────────────────────────────────────────────┐
│                       PRODUCTION RUNTIME INFRASTRUCTURE                                 │
│  • FastF1 & Jolpica Telemetry Ingestion Pipeline (60Hz Stream & Pydantic Validation)     │
│  • Dual-Tier State Cache (L1 RAM Buffer <0.1ms, L2 Redis Hot Store 1-3ms)               │
│  • Feature Store: 28-dimensional state vector extraction at 0.0245ms p99 SLA            │
│  • Production Observability & SLIs (Prometheus, Grafana, Zero-Hallucination Guardrails)  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Modules & Engineering Standards

### 3.1 FastF1 & Jolpica Telemetry Ingestion Pipeline
- Ingests real Grand Prix session data and streams 60Hz timing ticks.
- Validates data quality via strict Pydantic schemas; isolates corrupt frames to dead-letter queues (`f1.dlq.failed_events`).

### 3.2 Low-Latency Multi-Tier Feature Store
- Extracts 28-dimensional state vectors (tyre wear %, tyre age, track temperature, rain probability, gap to car ahead, dirty air wake status, safety car flag).
- Performance: **0.0245ms p99 latency** with **66,798 extractions/sec throughput**.

### 3.3 Supervised Learning Predictive Suite
- **Flagship XGBoost**: Evaluated on **1,400 held-out FastF1 telemetry laps** with **MAE 0.3597 s/lap, $R^2$ 0.8342, Pearson $r$ 0.9166, and Cliff Accuracy 88.43%**.
- Benchmarked directly against Naive Constant Wear, Ridge Regression, Random Forest, and Physics-Informed Residual MLPs.
- Provides 95% confidence intervals ($\pm 0.16\text{s}$) on degradation curves.

### 3.4 Counterfactual Simulation Engine
- Performs forward stochastic rollouts across candidate actions (Pit Now, Pit +2, Stay Out, Switch Compound).
- Computes expected finish positions and action utilities with uncertainty bounds ($0.82 \pm 0.12$).

### 3.5 Safe RL & Decision Optimization
- Action Masking Guardrails physically block invalid or dangerous transitions (e.g. driving beyond 80% wear cliff, pitting under closed pitlane).
- Trained DQN and PPO agents achieve a **90% win rate and 95% podium rate** in competitive AI benchmarks.

### 3.6 TreeSHAP Explainability & Grounded Context
- Additive Shapley feature attributions decompose strategic recommendations into physical factors (tyre age, track temperature, fuel load, traffic gap).
- Dense semantic vector embeddings link decisions to historical logs and FIA sporting regulations.

### 3.7 Model Context Protocol (MCP) Server
- Exposes 10 domain tools (`get_race_state`, `get_tyre_forecast`, `get_weather_forecast`, `get_opponent_strategy`, `run_counterfactual`, `get_strategy_history`, `explain_strategy`, `get_model_prediction`, `get_system_ablation_study`) for LLM agents.

---

## 4. Scientific System Ablation Matrix (9 Configurations)

| Configuration | Description | Win Rate % | DNF Rate % | Subsystem Impact |
| :--- | :--- | :---: | :---: | :--- |
| **`FULL`** | Production APEX Stack | **`90.0%`** | **`0.0%`** | Optimal champion performance |
| **`NO_RISK`** | Risk Engine Disabled | $75.0\%$ | $5.0\%$ | Increased variance in changing weather |
| **`NO_WEATHER`** | Weather Predictor Disabled | $60.0\%$ | $10.0\%$ | Pits 1–2 laps late in rain transitions |
| **`NO_RL`** | RL Policy Disabled | $55.0\%$ | $0.0\%$ | Lacks opportunistic pit timing |
| **`NO_MC`** | Monte Carlo Disabled | $40.0\%$ | $5.0\%$ | Blind to multi-lap traffic rejoins |
| **`NO_TYRE_ML`** | Tyre ML Disabled | $30.0\%$ | $10.0\%$ | Fails to anticipate thermal cliff bleed |
| **`NO_SAFETY`** | **Safe RL Guardrail Disabled** | $35.0\%$ | **`25.0%`** | **25% catastrophic tyre puncture DNF rate** |
| **`RULE_ONLY`** | Deterministic Rules Only | $20.0\%$ | $5.0\%$ | Rigid pit windows |
| **`RANDOM`** | Uniform Random Policy | $5.0\%$ | $65.0\%$ | Endless pit cycling and blowouts |

---

## 5. Production Engineering & Observability (Supporting Infrastructure)

- **Event Streaming**: Apache Kafka / Redpanda with partition key `session_id:car_id`.
- **Asynchronous Workers**: BullMQ / Redis queues with SHA-256 idempotency hashing.
- **Monitoring & Tracing**: Prometheus metrics, Grafana dashboards, OpenTelemetry distributed tracing.
- **Cloud Deployment**: Kubernetes manifests, production Helm charts (`deploy/helm/apex/`), Horizontal Pod Autoscaling ($3\to 20$ pods).
