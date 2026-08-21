# APEX — Autonomous Predictive & EXecutive Race Intelligence

<p align="center">
  <a href="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/ci.yml">
    <img src="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/ci.yml/badge.svg" alt="CI Build Status" />
  </a>
  <a href="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/docker-publish.yml">
    <img src="https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-/actions/workflows/docker-publish.yml/badge.svg" alt="Docker Build & Publish" />
  </a>
  <img src="https://img.shields.io/badge/Kafka-Distributed_Streaming-231F20.svg?logo=apachekafka&logoColor=white" alt="Kafka Streaming" />
  <img src="https://img.shields.io/badge/BullMQ-Redis_Job_Queue-CC0000.svg?logo=redis&logoColor=white" alt="BullMQ Queue" />
  <img src="https://img.shields.io/badge/Kubernetes-Helm_Ready-326CE5.svg?logo=kubernetes&logoColor=white" alt="Kubernetes Helm" />
  <img src="https://img.shields.io/badge/Prometheus-Grafana_Obs-E6522C.svg?logo=prometheus&logoColor=white" alt="Prometheus Grafana" />
  <img src="https://img.shields.io/badge/OpenTelemetry-Tracing-4053D6.svg?logo=opentelemetry&logoColor=white" alt="OpenTelemetry" />
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/Tests-172%2F172_Passed-brightgreen.svg" alt="172 Tests Passed" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

**APEX** is an enterprise-grade, distributed, autonomous Formula 1 race strategy intelligence and pit-wall mission control platform. Grounded in real-world F1 timing telemetry (`fastf1` and Jolpica/Ergast API), APEX couples a high-fidelity stochastic digital twin with multi-tier machine learning models, vectorized Monte Carlo rollouts (9 candidate actions), Deep Reinforcement Learning (DQN & PPO), Safe RL action masking guardrails, multi-action TreeSHAP explainability, an Autonomous Emergency Brain, a Multi-Agent Pit Wall Consensus Protocol, Apache Kafka event streaming, BullMQ / Redis asynchronous compute queues, full-stack Prometheus/Grafana observability, OpenTelemetry distributed tracing, cloud-native Kubernetes Helm deployments, and an interactive 14-page React 18 cockpit dashboard alongside a Rich terminal CLI.

---

## 🌟 Executive Project Overview (STAR Method)

### 🏎️ 1. Situation (The Problem We Faced)
* **High-Speed Stakes:** In Formula 1 racing, split-second strategy calls (such as reacting to sudden rain, safety cars, or opponent undercut threats) determine race victory or defeat.
* **Flawed Existing Systems:** Traditional systems rely on static rulebooks (failing during unpredictable chaos) or "black-box" AI that lacks interpretability, causing engineers to distrust recommendations.
* **Scalability & Latency Bottlenecks:** Simulating 10,000+ forward rollouts and streaming 60Hz telemetry across 20 cars synchronously blocks web servers and causes unacceptable latency spikes.

---

### 🎯 2. Task (What We Set Out to Build)
* **An Autonomous Pit-Wall Brain:** Create an intelligent, end-to-end race strategist ("APEX") that acts like a veteran chief race engineer.
* **Event-Driven Distributed Architecture:** Decouple telemetry ingestion from compute-heavy rollouts using Kafka streaming brokers, background worker queues, and multi-tier caching (L1 RAM $\to$ L2 Redis $\to$ L3 PostgreSQL).
* **Explainability, Multi-Agent Consensus & Safety:** Ensure every strategic decision is physically safe (Safe RL Action Masking), explained via TreeSHAP feature attributions, and debated across 5 specialized autonomous pit wall agents.
* **Production Cloud-Native Readiness:** Package with Kubernetes manifests, Helm charts, automated chaos resilience harnesses, and Prometheus/Grafana observability dashboards.

---

### ⚡ 3. Action (What We Built & Implemented)
1. **Kafka Telemetry Event Streaming Pipeline**:
   - Dispatches and consumes 60Hz telemetry across dedicated topics (`f1.telemetry.raw`, `f1.weather.events`, `f1.tyre.degradation`, `f1.race.control`, `f1.strategy.decisions`).
   - Partitioned routing by `session_id:car_id` for deterministic in-order per-car delivery with automated Dead-Letter Queue (`f1.dlq.failed_events`) poison-pill isolation.
   - Dual-engine execution: connects to Kafka/Redpanda when configured, with high-performance `InMemoryEventBus` fallback for zero-dependency local runs and tests.
2. **Asynchronous Job Processing Queue (BullMQ / Redis Streams)**:
   - Offloads 10,000+ Monte Carlo rollouts, FastF1 session parsing, ML retrain, and radio alert synthesis to background worker pools.
   - **Deterministic Idempotency**: SHA-256 parameter hashing (`apex:job:<type>:<hash>`) eliminates redundant computations under network storms.
   - Resilient worker execution with exponential backoff ($2^{\text{retry}-1} \times 0.5\text{s}$).
3. **Multi-Agent Pit Wall Consensus & Deliberation Protocol**:
   - 5 specialized autonomous agents (Chief Strategist, Tyre Specialist, Meteorologist, Powertrain Engineer, Driver Coach) debate in real time, cast weighted votes, and synthesize a unified executive order with live radio speech verbalization.
4. **Multi-Tier Storage & Low-Latency Feature Store**:
   - L1 Zero-Copy In-Memory Ring Buffer ($<0.1\text{ms}$ access) + L2 Redis hot cache ($1\text{--}3\text{ms}$) + L3 PostgreSQL cold store.
   - Feature Builder throughput: **`66,798 extractions/sec`** with **`0.0245ms p99 latency`**.
5. **Observability, Tracing & Chaos Resilience**:
   - Full Prometheus metrics registry, 2 pre-configured Grafana dashboards, and OpenTelemetry distributed tracing with W3C `traceparent` context propagation.
   - Automated Chaos Engineering Harness validating burst streaming, broker disconnections, worker retries, and poison-pill isolation.
6. **Cloud-Native Kubernetes Deployment & Production Tooling**:
   - Production Helm Charts (`deploy/helm/apex/`), Horizontal Pod Autoscaling ($3\to 20$ pods), and multi-service Docker Compose stack.
   - Interactive React UI Mission Control + Terminal Rich Cockpit CLI (`interactive_pitwall_cli.py`).

---

### 🏆 4. Result (The Proven Outcomes)
* **100% Test Pass Rate:** All **172 automated unit, integration, invariant, and streaming tests** pass with zero failures.
* **Sub-Millisecond Feature Extraction:** Feature Store extracts 28-dimensional vectors in **`0.0245 ms` ($p99$)** ($>20\times$ faster than the $0.50\text{ms}$ SLA).
* **High Predictive Accuracy:** The tyre degradation model predicts lap times with an average error of only **0.35s per lap** ($R^2 = 0.834$) on held-out race data.
* **Zero Chaos Crashes:** 100% self-healing resilience during 500-message bursts, poison-pill injection, and worker node failovers.
* **Winning Race Strategy:** Achieved a **90% win rate and 95% podium rate** across tournament benchmarks against rival AI teams.

---

## ⚡ Modern Tech Advancements Suite 

APEX has expanded into a next-generation motorsport digital twin platform with 50+ interactive workspaces and high-tech simulations:

### 🏎️ 3D Spatial Digital Twin & WebXR VR Cockpit
* **Three.js 3D WebGL Digital Twin**: Real-time track elevation spline extrusion, realistic team liveries, glowing brake discs under deceleration, and Cockpit Chase Cam.
* **WebXR Stereoscopic 3D VR Cockpit**: Dual-eye VR rendering with IPD adjustment ($58-72\text{mm}$) and 6DoF pitch/yaw head-tracking.
* **3D Wind Tunnel & CFD Lab**: Interactive aerodynamic smoke flow with 2,800 active particles and real-time downforce/drag calculations.
* **Interactive 3D Pit Crew Lab**: Full 3D pit box with 4-corner wheel gun torque telemetry (450 Nm) and reaction drills.

### 🧠 Advanced AI, Strategy & Acoustic Audio Engines
* **AlphaZero-Style MCTS Engine**: Deep Monte Carlo Tree Search with Upper Confidence bounds for Trees (UCT) and visual decision graph.
* **Driver Radio Voice Emotion AI**: Real-time fundamental frequency pitch ($F_0$), vocal jitter tremor, speech rate, and automatic race engineer de-escalation scripts.
* **Neural Voice AI & Hybrid Audio Synth**: Bidirectional hands-free voice radio recognition (PTT), VHF team radio bandpass filtering, and 1.6L V6 hybrid turbo acoustic engine.
* **Historical FastF1 Duel Mode**: Real-world pole and victory telemetry synchronization against live APEX AI cars.

### 🌡️ Vehicle Physics, Materials & Forensics Labs
* **Driver Thermal Heatmap & Liquid Cooling Suit**: Core body temperature monitoring ($38.5^\circ\text{C}$), chilled water vest flow ($1.2\text{ L/min}$), and in-helmet hydration dispenser.
* **Brembo Carbon-Carbon Brake Pyrometry**: 1,480-hole disc ventilation pyrometry ($350-1,150^\circ\text{C}$ glowing rotor) and brake cooling duct drag tradeoffs.
* **Seamless Shift Gearbox Lab**: Sub-millisecond ($2\text{ms}$) zero-torque-loss shifts, $45\text{ bar}$ pneumatic shift rail, and 8-speed gear ratio optimization.
* **Engine Oil ICP Chemical Spectroscopy**: Atomic emission trace metal analysis ($\text{Fe, Cu, Ti, Al, Si}$ in PPM) and engine wear forensics.
* **Carbon Fiber Autoclave & Crash Sled Rig**: Pre-preg composite curing ($180^\circ\text{C}$, $7.0\text{ bar}$) and FIA 50G nosecone destructive crash sled testing.
* **Tyre Blanket Induction Rig**: 4-corner electromagnetic induction warming ($100^\circ\text{C}$ tread / $70^\circ\text{C}$ rim) and Pirelli cold starting PSI balancer.

### 🚩 Race Operations, FIA Stewards & Atmospheric Intelligence
* **FIA Steward Hearing & Disciplinary Tribunal**: Driver testimonies, apex telemetry overlap evidence, 4-steward jury voting, and penalty points tracker.
* **FIA Safety Car & VSC Mission Control**: Full SC, VSC, and Red Flag race director deployment with pit window delta bonus calculator.
* **20-Panel Electronic LED Track Marshall Matrix**: High-intensity trackside flag boards with immediate cockpit flag sync.
* **Paddock Weather Balloon Atmospheric Sounding**: High-altitude air density ($\rho$), barometric pressure ($1013\to 780\text{ hPa}$), and turbocharger overspin modeling.
* **Formula 1 Championship Trophy Cabinet**: Silverware showcase (Monaco Gold Cup, RAC Trophy, WDC Cup) with career statistics.

---

## 🏎️ Master Distributed Architecture Pipeline

```
                        FastF1 / Jolpica Live Ingestion Daemon (60Hz Multi-Car Bridge)
                                                      │
                                                      ▼
                        ┌─────────────────────────────────────────────────────────┐
                        │               KAFKA DISTRIBUTED BROKER                  │
                        │ ┌───────────────────┐     ┌───────────────────────────┐ │
                        │ │ f1.telemetry.raw  │     │ f1.weather.events         │ │
                        │ ├───────────────────┤     ├───────────────────────────┤ │
                        │ │ f1.tyre.degrade   │     │ f1.race.control           │ │
                        │ ├───────────────────┤     ├───────────────────────────┤ │
                        │ │ f1.strategy.orders│     │ f1.dlq.failed_events (DLQ)│ │
                        │ └───────────────────┘     └───────────────────────────┘ │
                        └───────────┬─────────────────────────────┬───────────────┘
                                    │ Consumer Group 1            │ Consumer Group 2
                                    ▼                             ▼
                 ┌───────────────────────────────────┐  ┌───────────────────────────────────┐
                 │   STREAM PROCESSING INGESTION     │  │   TELEMETRY RECORDER & STORAGE    │
                 │  • Schema Validation (Pydantic)   │  │  • PostgreSQL Batch Flush         │
                 │  • Anomaly & Outlier Filter       │  │  • Session Replay Store           │
                 │  • Dead-Letter Queue (DLQ)        │  │  • S3 / Parquet Cold Archive      │
                 └──────────────────┬────────────────┘  └───────────────────────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────────────────────────────────┐
                 │             DIGITAL TWIN & L1/L2 CACHE HIERARCHY                 │
                 │  • L1: Zero-copy In-Memory Ring Buffer (<0.1ms access)           │
                 │  • L2: Redis Pub/Sub + Distributed State Store (Hot Window)      │
                 └──────────────────┬───────────────────────────────────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────────────────────────────────┐
                 │     MULTI-AGENT PIT WALL CONSENSUS (5 Autonomous Specialists)     │
                 │  • Chief Strategist (0.30)  • Tyre Specialist (0.25)             │
                 │  • Meteorologist (0.20)     • Powertrain Eng. (0.15)             │
                 │  • Driver Coach (0.10)      • Intercom Debate Synthesis          │
                 └──────────────────┬───────────────────────────────────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────────────────────────────────┐
                 │               HYBRID DECISION & RISK AGGREGATOR                  │
                 │  • Physics-Informed ML Inference (PINN + Random Forest)          │
                 │  • Autonomous Emergency Brain (Incident Interceptor)             │
                 │  • Safe RL Action Masking Guardrail                              │
                 └──────────────────┬───────────────────────────────────────────────┘
                                    │ Heavy Compute Offload
                                    ▼
                 ┌──────────────────────────────────────────────────────────────────┐
                 │         DISTRIBUTED ASYNC WORKER QUEUE (BullMQ / Redis)          │
                 │ ┌──────────────────────┐         ┌─────────────────────────────┐ │
                 │ │ strategy-queue       │         │ replay-queue                │ │
                 │ │ (Monte Carlo 10k)    │         │ (Historical Telemetry Replay│ │
                 │ ├──────────────────────┤         ├─────────────────────────────┤ │
                 │ │ ml-training-queue    │         │ alert-dispatch-queue        │ │
                 │ │ (TreeSHAP & PINN fit)│         │ (Radio DSP / Push Alarms)   │ │
                 │ └──────────────────────┘         └─────────────────────────────┘ │
                 │  • Idempotency Deduplication Key: hash(session_id:lap:action)   │
                 │  • Exponential Backoff & Circuit Breaker Handlers                │
                 └──────────────────┬───────────────────────────────────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────────────────────────────────┐
                 │        REAL-TIME WEBSOCKET BROADCASTER & REACT COCKPIT           │
                 │  • Low-latency Delta Streaming (60Hz State Broadcast)            │
                 │  • JWT Authenticated + Role-Gated Command Dispatch               │
                 │  • 14 Specialized Pit Wall Workspaces + Audio Synth DSP          │
                 │  • Terminal Rich Cockpit CLI (interactive_pitwall_cli.py)        │
                 └──────────────────────────────────────────────────────────────────┘
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

## 🏛️ Comprehensive Architecture Pillars

### 1. Kafka Telemetry Streaming Pipeline
- **Broker Configuration**: [`kafka_config.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/streaming/kafka_config.py) manages bootstrap servers, compression (`gzip`), batching ($5\text{ms}$ linger), and dual-engine execution.
- **Event Schemas**: [`event_schemas.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/streaming/event_schemas.py) defines Pydantic payloads for telemetry, weather, tyre degradation, race control, strategy decisions, and DLQ errors.
- **Producer & Consumer Groups**: [`producer.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/streaming/producer.py) routes partitioned keys (`session_id:car_id`) and [`consumer.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/streaming/consumer.py) dispatches callbacks with at-least-once offset management and DLQ isolation.
- **Live Stream Daemon**: [`stream_producer_daemon.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/streaming/stream_producer_daemon.py) streams 60Hz multi-car grids continuously via CLI.

### 2. Asynchronous Job Processing Queue (BullMQ / Redis Streams)
- **Job Orchestrator**: [`job_manager.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/jobs/job_manager.py) manages job dispatching, SHA-256 deterministic idempotency deduplication (`apex:job:<type>:<hash>`), and live progress tracking (`0% → 100%`).
- **Worker Pool**: [`workers.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/jobs/workers.py) executes 10,000 Monte Carlo stochastic rollouts, FastF1 session parsing, TreeSHAP model fitting, and alert synthesis with exponential backoff retries.
- **REST Endpoints**: [`jobs_router.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/api/jobs_router.py) exposes `/api/jobs/enqueue`, `/api/jobs/status/{job_id}`, and `/api/jobs/list`.

### 3. Multi-Agent Pit Wall Consensus Protocol
- **Specialist Deliberation**: [`multi_agent_consensus.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/intelligence/multi_agent_consensus.py) coordinates 5 autonomous specialist agents (Chief Strategist, Tyre Specialist, Meteorologist, Powertrain Engineer, Driver Coach) with weighted voting and intercom dialogue transcript generation.
- **Interactive Cockpit Modal**: [`PitWallConsensusModal.tsx`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/frontend/src/components/PitWallConsensusModal.tsx) allows users to inspect individual specialist arguments, review vote distributions, and hear synthesized radio verbalizations.

### 4. Full-Stack Observability & Tracing
- **Prometheus Metrics**: [`metrics.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/api/metrics.py) exposes `/metrics` with gauges and histograms for Kafka produced/consumed messages, consumer lag, BullMQ queue depth, and model drift status.
- **Grafana Dashboards**: Pre-configured JSON dashboards in [`deploy/grafana/dashboards/`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/deploy/grafana/dashboards/) for system health and streaming queues.
- **OpenTelemetry Distributed Tracing**: [`telemetry.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/core/telemetry.py) injects and propagates W3C `traceparent` headers across asynchronous service boundaries.

### 5. Security, Tiered Rate Limiting & RBAC
- **Stateless JWT Tokens**: [`security.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/core/security.py) and [`auth.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/api/auth.py) manage HMAC-SHA256 tokens and password hashing.
- **Role Permission Matrix**: `VIEWER` (Read telemetry), `ANALYST` (Simulate sandbox), `STRATEGIST` (Execute pit orders), and `ADMIN` (Retrain models).
- **Tiered Token Bucket Limiting**: [`limiter.py`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/backend/app/api/limiter.py) enforces rate limits based on JWT identity (120 req/min for viewers up to 3,000 req/min for admins).

### 6. Cloud-Native Kubernetes & Helm Packaging
- **Helm Package**: [`deploy/helm/apex/`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/deploy/helm/apex/) contains full declarative charts (`Chart.yaml`, `values.yaml`, templates for deployments, services, ingress, and HPA).
- **Horizontal Pod Autoscaler (HPA)**: Automatically scales backend web pods from 3 to 20 replicas based on CPU and WebSocket connection loads.
- **Docker Compose**: Multi-container stack in [`docker-compose.yml`](file:///c:/Users/nayak/OneDrive/Desktop/Projects/AIML/APEX/docker-compose.yml) orchestrating Redpanda Kafka, Redis, PostgreSQL, Prometheus, Grafana, Jaeger, BullMQ Worker, and App.

---

## 📁 Repository Structure

```
APEX/
├── backend/
│   ├── app/
│   │   ├── intelligence/                  # Predictive ML models & Multi-Agent Pit Wall Consensus
│   │   ├── jobs/                          # BullMQ / Redis Asynchronous Job Queue & Worker Pool
│   │   ├── streaming/                     # Kafka event schemas, producers, consumers, and live streamers
│   │   ├── simulator/                     # 60 Hz physics engine, models, track geometry & historical replay
│   │   ├── strategy/                      # Rule engine, Gymnasium RL env, DQN, PPO, Monte Carlo
│   │   ├── twin/                          # Digital twin state store (L1 Hot Memory, L2 Redis, L3 DB)
│   │   ├── core/                          # Security (JWT/RBAC) and OpenTelemetry distributed tracing
│   │   ├── api/                           # FastAPI REST endpoints, Auth, Jobs, and WebSocket broadcaster
│   │   ├── mcp_server/                    # Model Context Protocol (MCP) Server (server.py)
│   │   └── main.py                        # FastAPI entry point & lifespan hooks
│   ├── eval/                              # Evaluation harness, baseline scores & championship simulator
│   ├── models/                            # Trained DQN, PPO checkpoints & multi-action distilled TreeSHAP artifacts
│   ├── training/                          # Data pipelines (FastF1/Jolpica), preprocessing, feature store, training scripts
│   └── tests/                             # Automated test suite (172 tests across all modules)
├── frontend/                              # React 18 + Vite + Tailwind Mission Control
│   ├── src/
│   │   ├── components/                    # 45+ Mission Control components & 14 workspace views
│   │   ├── data/                          # Multi-circuit vector geometries (Silverstone, Monza, Spa, Monaco, etc.)
│   │   ├── utils/                         # audioEngine (DSP + Personas + V6 Synth), clientSimulator (Twin)
│   │   ├── store/                         # Zustand state store with 14-workspace routing
│   │   └── hooks/                         # useRaceSocket WebSocket client & twin fallback
│   └── package.json
├── deploy/                                # Cloud-Native Deployment Manifests
│   ├── helm/apex/                         # Production Helm Chart Package
│   ├── k8s/                               # Kubernetes Deployments, HPA, Ingress, StatefulSets
│   ├── prometheus/                        # Prometheus scraper & alerting rules
│   └── grafana/dashboards/                # Pre-configured Grafana dashboards
├── docs/                                  # Comprehensive architecture, ML model & API documentation
│   ├── SYSTEM_DESIGN.md                   # Enterprise System Design Blueprint
│   ├── INTERVIEW_TALKING_POINTS.md        # Curated Interview Q&A Guide
│   ├── ARCHITECTURE.md
│   ├── ML_MODELS.md
│   └── API_REFERENCE.md
└── benchmarks/                            # Automated benchmarking, load testing & chaos suite
    ├── k6/                                # k6 WebSocket stress, API benchmark & chaos scripts
    ├── chaos_harness.py                   # Automated chaos engineering runner
    ├── interactive_pitwall_cli.py         # Rich-powered terminal Pit Wall Cockpit
    ├── benchmark_feature_store.py         # Low-latency feature store benchmark
    └── run_benchmarks.py                  # Standard benchmark runner
```

---

## 🐳 Deployment & Quickstart

### Option A: Complete Multi-Container Stack via Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-.git
cd F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-

# Launch APEX App, Worker, Redpanda Kafka, Redis, PostgreSQL, Prometheus, Grafana, and Jaeger
docker compose up -d --build
```

Access the system endpoints:
- **Mission Control Cockpit**: `http://localhost:8000`
- **Swagger / OpenAPI Documentation**: `http://localhost:8000/docs`
- **Prometheus Metrics**: `http://localhost:8000/metrics` & `http://localhost:9090`
- **Grafana Dashboards**: `http://localhost:3000` (admin/admin)
- **Jaeger Distributed Tracing**: `http://localhost:16686`

---

### Option B: Kubernetes Deployment via Helm

```bash
# Deploy APEX using the production Helm chart
helm upgrade --install apex deploy/helm/apex \
  --set replicaCount=3 \
  --set autoscaling.enabled=true \
  --set autoscaling.maxReplicas=20
```

---

### Option C: Local Development Quick Start

```bash
# 1. Install Python dependencies with uv
uv sync

# 2. Build Frontend production bundle
cd frontend
npm install
npm run build
cd ..

# 3. Launch APEX backend server
uv run uvicorn backend.app.main:app --port 8000 --reload
```

---

## 🧪 Testing, Benchmarking & Tooling Commands

```bash
# Run full automated test suite (172/172 tests passing in <55s)
uv run pytest backend/tests -v

# Run specialized streaming, worker, RBAC, and chaos tests
uv run pytest backend/tests/test_streaming_kafka.py -v
uv run pytest backend/tests/test_async_jobs.py -v
uv run pytest backend/tests/test_jwt_rbac.py -v
uv run pytest backend/tests/test_multi_agent_consensus.py -v
uv run pytest backend/tests/test_chaos_recovery.py -v

# Run Automated Chaos Engineering & Recovery Harness
uv run python benchmarks/chaos_harness.py

# Run Feature Store Latency & Throughput Benchmark (66k+ feats/sec)
uv run python benchmarks/benchmark_feature_store.py

# Launch Interactive Terminal Pit Wall Cockpit CLI
uv run python benchmarks/interactive_pitwall_cli.py

# Launch Standalone 60Hz Telemetry Streaming Daemon
uv run python -m backend.app.streaming.stream_producer_daemon --circuit silverstone --fps 60 --laps 52

# Run Gate J Reproducibility Benchmark Suite
uv run python -m backend.eval.benchmark_runner --quick --seed 42

# Run Gate D Tyre Model Held-Out Evaluation on Real Telemetry
uv run python backend/eval/tyre_model_eval.py

# Run 4-Pillar Evaluation & Regression Harness (CI integrated)
uv run python backend/eval/run_eval.py
```

---

## 📚 System Design & Technical Documentation

For complete architectural breakdowns and interview preparation:
- 🏗️ **[System Design Blueprint (docs/SYSTEM_DESIGN.md)](docs/SYSTEM_DESIGN.md)**: Deep dive into event-driven streaming, partition keys, consumer groups, BullMQ worker queues, backpressure, multi-tier caching, and distributed tracing.
- 🎯 **[System Design Interview Talking Points (docs/INTERVIEW_TALKING_POINTS.md)](docs/INTERVIEW_TALKING_POINTS.md)**: Curated questions and answers for Backend, Full-Stack, and ML System Design interviews.
- 🔌 **[API Reference (docs/API_REFERENCE.md)](docs/API_REFERENCE.md)**: Specifications for all REST endpoints, WebSocket protocols, Kafka topics, and JWT authentication headers.
- 📊 **[Forensic Baseline Audit (docs/BASELINE_AUDIT.md)](docs/BASELINE_AUDIT.md)**: Acceptance criteria tracking across all 10 architectural gates.
- ⚛️ **[Physics Constants & Assumptions (docs/PHYSICS_ASSUMPTIONS.md)](docs/PHYSICS_ASSUMPTIONS.md)**: Catalogue of 40+ physical constants and aerodynamic equations.
- 🧠 **[Predictive ML Models (docs/ML_MODELS.md)](docs/ML_MODELS.md)**: Formulations for Tyre PINN, Weather, Opponent, Driver, and Vehicle Health models.
- 🛡️ **[Resilience & Degradation Architecture (RESILIENCE.md)](RESILIENCE.md)**: Zero-hard-dependency fallback matrix across all services.

---

<p align="center">
  Built with ❤️ for Formula 1 engineering, autonomous intelligence, and enterprise distributed systems.
</p>
