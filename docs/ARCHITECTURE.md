# APEX System Architecture & Subsystem Micro-Architectures

> **In Plain English:** APEX predicts race finishing positions using real Formula 1 data, then layers live strategy intelligence (tyre degradation, pit windows, Monte Carlo counterfactuals) and agentic deliberation on top, matching how an actual F1 pit wall functions.

---

## 0. Three-Tier Architectural Decomposition

The repository is cleanly partitioned into three tiers mapping directly to the V1 → V2 → V4 design lifecycle:

```
f1-apex/
├── core/             # Tier 1 — The Provably-Correct Predictive Baseline (V1)
│   ├── ingestion/    # Jolpica / FastF1 adapters with point-in-time constraints
│   ├── features/     # Pre-race feature builder (zero outcome leakage)
│   ├── training/     # XGBoost + conformal calibration trainer & evaluators
│   └── api/          # Lightweight standalone predict service (race_id + driver_id -> finish)
├── intelligence/     # Tier 2 — Live Race Strategy, Digital Twin & Physics ML (V2)
│   ├── strategy/     # Monte Carlo rollouts, DQN/PPO policies, counterfactual optimizer
│   ├── models/       # FastF1 tyre degradation, weather radar, vehicle health, TreeSHAP
│   ├── simulator/    # Millisecond race physics engine with safety cars & pit windows
│   ├── twin/         # State store, SQLite/PostgreSQL persistence, telemetry buffers
│   └── streaming/    # Kafka event broker & FastF1 producer/consumer daemons
└── agents/           # Tier 3 — Multi-Agent Deliberation, RAG & MCP (V3/V4)
    ├── langgraph/    # LangGraph state machine & 5-agent consensus deliberation
    ├── rag/          # Hybrid BM25/Dense retrieval over historical Grand Prix decisions
    └── mcp/          # FastMCP tool server exposing real-time telemetry to LLMs
```

| Tier | Primary Capability | Key Contract | Operational Footprint |
|---|---|---|---|
| **Tier 1: Core (V1)** | Real F1 pre-race priors → trained model → predicted finish | `race_id + driver_id → predicted finish + model version + data snapshot` | Lightweight single process (no Kafka/Redis required) |
| **Tier 2: Intelligence (V2)** | 60Hz vehicle digital twin, tyre physics, Monte Carlo what-if | 1,000+ stochastic rollouts, TreeSHAP feature attributions | Full race digital twin with telemetry cache |
| **Tier 3: Agents (V3/V4)** | LangGraph orchestration, RAG, domain MCP tools | Multi-agent consensus, structured debrief evidence | Orchestrated agentic tools |

---

## 1. Master System Architecture: Decision Intelligence Pipeline

```
FastF1 / Jolpica (60Hz Telemetry & Timing Ingestion)
      │
      ▼
Data Validation & Schema Contracts (Pydantic & DLQ Isolation)
      │
      ▼
Feature Engineering & Low-Latency Feature Store (28-D Vector @ 0.0245ms p99)
      │
      ▼
Predictive Machine Learning Models
 ┌───────────────┬─────────────────┬──────────────────┬─────────────────┐
 │ Tyre Degradation │ Weather Doppler │ Opponent Intent  │ Vehicle Health  │
 │ (XGBoost GBDT)   │ (Radar & Rain)  │ (Undercut Model) │ (Anomaly Det)   │
 └───────────────┴─────────────────┴──────────────────┴─────────────────┘
      │
      ▼
Uncertainty Quantification (95% Confidence Intervals & Conformal Variance)
      │
      ▼
Counterfactual Simulation Engine (1,000+ Stochastic Monte Carlo Rollouts)
      │
      ▼
Decision Policies & Safety Envelopes
 ┌───────────────┬─────────────────────────────┬────────────────────────┐
 │ Rule Baseline │ Safe RL (Action Masking)    │ Monte Carlo Rollouts   │
 └───────────────┴─────────────────────────────┴────────────────────────┘
      │
      ▼
Explainability Engine (TreeSHAP & Additive Feature Attribution)
      │
      ▼
Planner Agent + Domain MCP Tools (Live Telemetry & Evidence Grounding)
      │
      ▼
Strategic Pit Wall Decision (Box vs Stay Out Recommendation)
      │
      ▼
Outcome & Action Execution (Net Delta Tracking)
      │
      ▼
Closed-Loop Evaluation & Feedback (System Ablation & Model Drift Monitoring)
```

### Production Infrastructure & Supporting Execution Layer
```
┌─────────────────────────────────────────────────────────────────────────┐
│ • Apache Kafka / Redpanda (60Hz Telemetry Stream & DLQ Buffer)          │
│ • Redis Cluster & BullMQ (Asynchronous Worker Pools for MC Rollouts)   │
│ • PostgreSQL (Historical Telemetry & Decision Audit Cold Store)         │
│ • Docker & Kubernetes / Helm (Horizontal Pod Autoscaling 3 -> 20 pods)  │
│ • Prometheus & OpenTelemetry (Distributed Tracing with W3C traceparent) │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Dedicated Subsystem Micro-Architectures

---

### 🏎️ Sub-Architecture 1: Data Engineering & Feature Store Pipeline

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion"]
        FF1["FastF1 API (Laps, Telemetry, Weather, Race Control)"]
        Jolpica["Jolpica / Ergast API (Calendar, Results, Pit Stops)"]
        RawDisk[("Persistent Raw Storage (JSON/Parquet/CSV)")]
        
        FF1 --> RawDisk
        Jolpica --> RawDisk
    end

    subgraph Cleaning ["2. Preprocessing & Cleansing"]
        CleanLaps["clean_laps.py (In/Out Laps, Non-Green Flags, Fuel Delta)"]
        CleanTel["clean_telemetry.py (Throttle, Brake, RPM, Gear, Speed Norm)"]
        CleanWeather["clean_weather.py (Air/Track Temp, Humidity, Rain Intensity)"]
        CleanRC["clean_race_control.py (SC, VSC, Red Flag Event Intervals)"]
        MergeSessions["merge_sessions.py (Multi-Source Stream Alignment)"]
        
        RawDisk --> CleanLaps
        RawDisk --> CleanTel
        RawDisk --> CleanWeather
        RawDisk --> CleanRC
        CleanLaps & CleanTel & CleanWeather & CleanRC --> MergeSessions
    end

    subgraph Features ["3. Feature Engineering Store"]
        TyreFeats["tyre_features.py (Compound 1-Hot, Age, Thermal Stress)"]
        WeatherFeats["weather_features.py (Track Wetness Index, Drying Rate)"]
        OpponentFeats["opponent_features.py (DRS Gaps, Undercut Threat Score)"]
        DriverFeats["driver_features.py (Pace Bias, Consistency, Aggression)"]
        VehicleFeats["vehicle_features.py (Fuel Burn, ERS Pack, Thermal Margin)"]
        StrategyFeats["strategy_features.py (Stint Progression, Pit Windows)"]
        
        MergeSessions --> TyreFeats & WeatherFeats & OpponentFeats & DriverFeats & VehicleFeats & StrategyFeats
    end

    subgraph Validation ["4. Validation & Split Registry"]
        Validator["dataset_validator.py (Nulls & Range Integrity)"]
        VersionSplitter["dataset_version.py (Leak-Free Season/Race Splits)"]
        DatasetStore[("Versioned Feature Datasets")]
        
        TyreFeats & WeatherFeats & OpponentFeats & DriverFeats & VehicleFeats & StrategyFeats --> Validator
        Validator --> VersionSplitter --> DatasetStore
    end
```

---

### 🧠 Sub-Architecture 2: Predictive Intelligence Model Hierarchy

```mermaid
flowchart LR
    subgraph Inputs ["Input State Vectors"]
        RawTel["Raw Vehicle Telemetry"]
        FieldState["Field Gaps & Positions"]
        EnvState["Atmospheric Weather"]
    end

    subgraph Models ["Specialized Predictive ML Suite"]
        TyreModel["TyreMLSuite (Random Forest Regressor + 90% CIs + Sigmoid Cliff)"]
        WeatherModel["WeatherPredictor (Wetness Index 0-1 + Grip Multiplier 0.40-1.05 + 5m Rain)"]
        OpponentModel["OpponentIntelligenceEngine (1-2 Lap Pit Prob + Attack/Defence Likelihood)"]
        DriverModel["DriverIntelligenceEngine (Fatigue Curves + Mistake Prob Under Pressure)"]
        HealthModel["VehicleHealthIntelligence (Isolation Forest Anomaly + Failure Horizon)"]
    end

    subgraph Outputs ["Structured Sub-States"]
        TyreOut["TyreState (RUL, Wear, Cliff Prob)"]
        WeatherOut["WeatherState (Wetness, Grip, Rain Prob)"]
        OppOut["OpponentState (Intent, Undercut Risk)"]
        DriverOut["DriverState (Fatigue, Consistency)"]
        HealthOut["VehicleHealthState (Health %, Anomaly Flag)"]
    end

    RawTel --> TyreModel --> TyreOut
    RawTel --> HealthModel --> HealthOut
    FieldState --> OpponentModel --> OppOut
    FieldState --> DriverModel --> DriverOut
    EnvState --> WeatherModel --> WeatherOut
```

---

### 💾 Sub-Architecture 3: Digital Twin 3-Tier Memory & Persistence

```mermaid
flowchart TD
    Simulator["RaceSimulator (60 Hz Deterministic Physics Tick)"]
    
    subgraph TwinStore ["Three-Tier Digital Twin Store (store.py)"]
        L1["L1 Hot Cache (In-Memory Dictionary, Sub-ms Read/Write)"]
        L2["L2 Write-Behind Queue (Async Redis Buffer)"]
        L3["L3 Relational Persistence (SQLite / PostgreSQL)"]
        
        L1 -- "Async Flush Queue" --> L2
        L2 -- "Periodic Commit" --> L3
    end

    Snapshots["Snapshot Serialization & Rolling Window Querying (10-35 Laps)"]
    
    Simulator <--> L1
    L1 <--> Snapshots
```

---

### 🎲 Sub-Architecture 4: Vectorized Monte Carlo & Counterfactual Engine

```mermaid
flowchart TD
    CurrentState["Current RaceState (Lap, Position, Tyres, Weather, Safety Car)"]
    
    subgraph CandidateActions ["9 Candidate Actions Evaluated in Parallel"]
        A1["PIT_NOW"]
        A2["PIT_NEXT_LAP"]
        A3["PIT_PLUS_2"]
        A4["STAY_OUT"]
        A5["PUSH"]
        A6["NORMAL"]
        A7["CONSERVE"]
        A8["ATTACK"]
        A9["DEFEND"]
    end

    CurrentState --> CandidateActions

    subgraph VectorizedEngine ["NumPy Vectorized Batch Rollout Engine (<15ms)"]
        AR1Noise["AR(1) Autoregressive Pace Noise: pace(t) = 0.65*pace(t-1) + noise"]
        ScMarkov["Poisson / Markov Safety Car Transition Matrix (SC / VSC Windows)"]
        TyreDegCliff["Non-Linear Stint Degradation & Thermal Cliff Penalty"]
        DNFSim["Stochastic Field Collision & Mechanical DNF Sim"]
        
        AR1Noise & ScMarkov & TyreDegCliff & DNFSim --> BatchSim["Matrix Array: (N_Rollouts, Laps_Remaining)"]
    end

    CandidateActions --> VectorizedEngine

    subgraph OutputDistributions ["Outcome Probability Metrics"]
        PWin["Win Probability (%)"]
        PPod["Podium Probability (%)"]
        PDNF["DNF Risk (%)"]
        ExpPos["Expected Finish Position"]
        PosHist["P1 - P10 Histogram Distribution"]
    end

    VectorizedEngine --> OutputDistributions
```

---

### 🤖 Sub-Architecture 5: Reinforcement Learning & Safe RL Guardrail

```mermaid
flowchart TD
    subgraph Env ["APEX Gymnasium Environment (gym_env.py)"]
        Obs["28-D Continuous Normalized State Tensor s_t"]
        Reward["Dense Intermediate Reward Function:
        R(s, a) = pos_gain*3.0 + clean_air_delta - cliff_pen - mismatch_pen + finish_bonus"]
    end

    subgraph Policies ["Neural Decision Policies"]
        DQN["Deep Q-Network (DQN) + Boltzmann Softmax Distribution"]
        PPO["Proximal Policy Optimization (PPO) + Value Critic"]
    end

    subgraph Guardrail ["Safe RL Action Masking Guardrail (safe_rl_guardrail.py)"]
        Mask["Dynamic 8-D Boolean Mask M(s) ∈ {0, 1}^8:
        • Pit Lane Double-Pit Invalidation
        • Torrential Rain Slick Invalidation
        • Dry Bone Wet-Tyre Invalidation
        • 80% Cliff Push Invalidation"]
    end

    Obs --> DQN & PPO
    Obs --> Mask
    DQN & PPO --> MaskedQ["Masked Action Selection: a* = argmax (Q(s, a) · M(s))"]
    MaskedQ --> ActionExec["Execute Strategic Action a_t"]
    ActionExec --> Reward
```

---

### 🚨 Sub-Architecture 6: Autonomous Emergency Brain Pipeline

```mermaid
stateDiagram-v2
    [*] --> MONITORING : Ingest RaceState Every Tick
    
    MONITORING --> DETECT : Incident Trigger Detected
    
    state DETECT {
        [*] --> CheckWeather : Rain Intensity > 0.50 on Slicks?
        [*] --> CheckSafetyCar : Physical SC / VSC Deployed?
        [*] --> CheckTyres : Wear > 85% or Puncture Cliff?
        [*] --> CheckPowertrain : Health < 45% or Thermal Alarm?
    }

    DETECT --> CLASSIFY : Event Type Assigned
    
    state CLASSIFY {
        SUDDEN_RAIN : Severity = CRITICAL
        SAFETY_CAR_DEPLOYED : Severity = HIGH
        PUNCTURE_DEBRIS : Severity = CRITICAL
        MECHANICAL_ALARM : Severity = HIGH
    }

    CLASSIFY --> ESTIMATE_IMPACT : Compute Time Delta (e.g. +22s/lap or -12s SC gain)
    ESTIMATE_IMPACT --> GENERATE_ACTIONS : Generate Candidates (PIT_WET, PIT_HARD, CONSERVE)
    GENERATE_ACTIONS --> RANK_AND_SELECT : Verify Safe RL Mask & Select Optimal Action
    RANK_AND_SELECT --> EXECUTE : Direct Pit Wall Box Order
    EXECUTE --> LOG_AND_DEBRIEF : Append to Incident Journal & Radio DSP Audio
    LOG_AND_DEBRIEF --> MONITORING : Resume Green-Flag Monitoring
```

---

### ⚖️ Sub-Architecture 7: Multi-Factor Risk Engine & Decision Aggregator

```mermaid
flowchart TD
    subgraph RiskInputs ["Multi-Dimensional Risk Inputs"]
        R1["Tyre Blowout Risk (Wear > 75%, Cliff Flag)"]
        R2["Weather Transition Risk (Wetness > 0.35 on Slicks)"]
        R3["Traffic / Undercut Risk (Gap Behind < 1.5s)"]
        R4["Mechanical Failure Risk (Isolation Forest Anomaly)"]
        R5["Strategy Vulnerability Risk (Mandatory Compound Regulation)"]
    end

    subgraph RiskEngine ["Risk Engine (risk_engine.py)"]
        RiskScore["Composite Risk Score: R_overall ∈ [0.0, 1.0]"]
        R1 & R2 & R3 & R4 & R5 --> RiskScore
    end

    subgraph DecisionAggregator ["Hybrid Decision Aggregator (hybrid_decision_engine.py)"]
        RuleBase["Expert Rules Baseline"]
        PredictiveML["Predictive ML Predictions"]
        MCOutputs["Monte Carlo Candidate Outcomes"]
        RLPolicy["DQN / PPO Policy Actions"]
        EmergBrain["Emergency Brain Interrupts"]
        
        RuleBase & PredictiveML & MCOutputs & RLPolicy & EmergBrain & RiskScore --> Aggregator["Unified Decision Arbitrator"]
    end

    subgraph FinalDecision ["Explainable Decision Output"]
        Recommendation["Recommended StrategyAction"]
        Confidence["Confidence Score (0-100%)"]
        Urgency["Urgency: LOW | MEDIUM | HIGH | CRITICAL"]
        PrimaryFactors["Primary Physical Drivers"]
        AlternativesTable["Ranked Alternative Actions Table"]
    end

    Aggregator --> FinalDecision
```

---

### 🏆 Sub-Architecture 8: Historical Race Replay & Championship Tournament

```mermaid
flowchart LR
    subgraph Historical ["Historical Replay Engine (historical_replay.py)"]
        RealGP["Real F1 Sessions (Silverstone 2023, Monaco 2023, Zandvoort 2023)"]
        DecisionPoints["Key Decision Points (Rain Onset, Safety Cars, Undercuts)"]
        APEXAudit["APEX Multi-Model Evaluation vs Real Pit Wall Action"]
        CounterfactualAdv["Counterfactual Time Delta & Audit Debrief"]
        
        RealGP --> DecisionPoints --> APEXAudit --> CounterfactualAdv
    end

    subgraph Tournament ["AI-vs-AI Championship (championship.py)"]
        Teams["5 AI Teams:
        • Team Alpha (Aggressive Attack)
        • Team Beta (Conservative Safe)
        • Team Gamma (Tyre Preserver)
        • Team Delta (Risk Defensive)
        • Team APEX (Hybrid Autonomous AI)"]
        SeasonSim["100+ Race Multi-Circuit Simulation"]
        Leaderboard["Championship Standings, Points (25-18-15...), Wins & Podiums"]
        
        Teams --> SeasonSim --> Leaderboard
    end
```

---

### 🖥️ Sub-Architecture 9: Frontend 10-Workspace React/Zustand Cockpit

```mermaid
flowchart TD
    BackendWS["FastAPI WebSocket Streamer (/ws/race @ 60Hz)"]
    
    subgraph FrontendCore ["Frontend Architecture (React 18 + Zustand)"]
        SocketHook["useRaceSocket.ts (Auto-Reconnect + Local Twin Fallback)"]
        ZustandStore["raceStore.ts (Global State + Telemetry History + Real-Time Sync)"]
        
        BackendWS <--> SocketHook --> ZustandStore
    end

    subgraph Workspaces ["10 Core Mission-Control AI/ML Workspaces"]
        W1["1. AI Strategy Assistant (Hero Decision Bar)"]
        W2["2. Live Race State & Timing Tower"]
        W3["3. Prediction Explorer (FastF1 Metrics & Baselines)"]
        W4["4. Counterfactual Simulation Lab"]
        W5["5. Decision Optimization & Safe RL Policy"]
        W6["6. Model Explainability (TreeSHAP & Delta-Q)"]
        W7["7. Data Quality & Feature Store Lineage"]
        W8["8. Agent Trace & MCP Tool Reasoner"]
        W9["9. System Ablation Matrix (9-Config Study)"]
        W10["10. Resilience & Edge-Case Error Monitoring"]
        
        ZustandStore --> W1 & W2 & W3 & W4 & W5 & W6 & W7 & W8 & W9 & W10
    end
```

---

### 🤖 Sub-Architecture 10: LangGraph StateGraph Autonomous Orchestrator

```mermaid
stateDiagram-v2
    [*] --> INTENT_EXTRACTION : User Strategic Query / Tick Event
    INTENT_EXTRACTION --> METADATA_RESOLUTION : Resolve Query Intent
    METADATA_RESOLUTION --> TELEMETRY_AUDIT : Fetch Context Graph Governance Cards
    TELEMETRY_AUDIT --> ANOMALY_DETECTION : Ingest 60Hz Telemetry & Weather
    ANOMALY_DETECTION --> TACTICAL_RANKING : Evaluate Degradation & Thermal Blistering
    
    state RiskCheck <<choice>>
    TACTICAL_RANKING --> RiskCheck : Evaluate Risk Profile
    
    RiskCheck --> DEEP_RISK_MITIGATION : High Risk (Rain / SC / Cliff / Query Risk)
    RiskCheck --> MCP_TOOL_EXECUTION : Nominal Risk
    
    DEEP_RISK_MITIGATION --> REASONING_SYNTHESIS : 500-Rollout Counterfactuals
    MCP_TOOL_EXECUTION --> REASONING_SYNTHESIS : Domain MCP Tools Dispatched
    
    REASONING_SYNTHESIS --> SAFE_RL_VERIFICATION : DQN + TreeSHAP + Conformal CI + PINN
    SAFE_RL_VERIFICATION --> RESPONSE_FORMATTING : Enforce 8-D Constrained MDP Action Mask
    RESPONSE_FORMATTING --> [*] : Emit Executive Dossier & Lineage Hash
```

---

### 🔍 Sub-Architecture 11: Hybrid Mission RAG (FAISS + BM25 via RRF)

```mermaid
flowchart TD
    Query["Strategic Natural-Language Query"]
    
    subgraph DenseSearch ["Dense Vector Retrieval"]
        Embedder["SentenceTransformer ('all-MiniLM-L6-v2') -> [384-D]"]
        FAISS["FAISS IndexFlatIP (Cosine Inner Product on L2-Norm Vectors)"]
        DenseRanks["Dense Ranked Candidates (r_dense)"]
        
        Query --> Embedder --> FAISS --> DenseRanks
    end

    subgraph SparseSearch ["Sparse Lexical Retrieval"]
        Tokenizer["Regex Alphanumeric Tokenizer"]
        BM25["BM25Okapi Sparse Index"]
        SparseRanks["Sparse Ranked Candidates (r_sparse)"]
        
        Query --> Tokenizer --> BM25 --> SparseRanks
    end

    subgraph Fusion ["Reciprocal Rank Fusion (RRF)"]
        RRFFormula["RRF(d) = 0.6 / (60 + r_dense) + 0.4 / (60 + r_sparse) + LapBoost"]
        DenseRanks & SparseRanks --> RRFFormula
        SortedDocs["Top-k Grounded Decision Logs"]
        RRFFormula --> SortedDocs
    end

    subgraph LangChainWrapper ["LangChain BaseRetriever Interface"]
        Retriever["ApexHybridRAGRetriever"]
        Docs["LangChain Documents with Provenance Metadata"]
        SortedDocs --> Retriever --> Docs
    end

    subgraph DiskPersistence ["Storage & Persistence Layer"]
        IndexBin[("faiss_rag.index (Binary FAISS)")]
        MetaJSON[("faiss_rag_metadata.json")]
        FAISS <--> IndexBin
        SortedDocs <--> MetaJSON
    end
```

---

### ⚡ Sub-Architecture 12: Strategy Transformer & PEFT LoRA Fine-Tuning

```mermaid
flowchart LR
    subgraph Input ["Sequential Telemetry Stint Tokens"]
        Tokens["[Batch, SeqLen, 28-D Features]"]
    end

    subgraph BaseTransformer ["Strategy Transformer (Frozen >98.5% Weights)"]
        InProj["Linear Projection -> [d_model=128]"]
        PosEmbed["Positional Embedding (64 Stint Steps)"]
        Attn1["Multi-Head Self-Attention Layer 1 (Frozen W_0)"]
        Attn2["Multi-Head Self-Attention Layer 2 (Frozen W_0)"]
        FFN["Feed-Forward Network (Frozen)"]
        
        Tokens --> InProj --> PosEmbed --> Attn1 --> Attn2 --> FFN
    end

    subgraph LoRAAdapters ["Trainable Low-Rank Adapters (r=8, alpha=16)"]
        LoRA_A["Matrix A (128 x 8, Gaussian Init)"]
        LoRA_B["Matrix B (8 x 128, Zero Init)"]
        DeltaW["Delta W = (alpha/r) * B * A"]
        
        Attn1 & Attn2 -.-> LoRA_A --> LoRA_B --> DeltaW
    end

    subgraph Heads ["Dual Strategic Prediction Heads"]
        BidHead["Bid Value Head -> Expected Stint Advantage (-5s to +15s)"]
        PolicyHead["Action Policy Head -> 8-D Strategic Distribution"]
        
        FFN & DeltaW --> BidHead & PolicyHead
    end

    subgraph Checkpoint ["Adapter Serialization"]
        AdapterDir[("backend/models/lora_adapters/stint_bid_value/")]
        LoRAAdapters --> AdapterDir
    end
```

---

### 🛡️ Sub-Architecture 13: System Resilience & Graceful Degradation

APEX is engineered with zero-hard-dependency resilience: every database, cache, or neural model is fronted by deterministic fallbacks, local buffers, and explicit status signals.

| Subsystem / Dependency | Failure Mode | Fallback Path | Impact |
|---|---|---|---|
| **PostgreSQL 16** | Connection refused / timeout | SQLite local engine (`apex_twin.db`) | **Zero Downtime**. All telemetry & audit logs persist locally. |
| **Redis 7** | Socket error / connection refused | Thread-safe in-memory cache dict (`store.py`) | **Zero Downtime**. Telemetry broadcasts without dropping frames. |
| **Ollama / LLM** | HTTP connection refused / 500 | Deterministic rule-based radio synthesis | **Zero Downtime**. Emits structured radio messages grounded in delta Q. |
| **TreeSHAP Surrogates** | Model missing / weight drift | Exact analytical game-theoretic marginal calculation | **Zero Downtime**. Emits `DRIFT_DETECTED` warning; explanations valid. |
| **FastF1 Telemetry** | Rate limit / network error | Calibrated physics polynomial wear envelope | **Zero Downtime**. Logs `"synthetic_fallback"` status without fake data. |
| **Dense Embeddings** | PyTorch allocation error | Lexical BM25 token matching with strict refusal | **Zero Downtime**. Returns `"model_used": "deterministic_grounded_fallback"`. |
| **PINN Tyre Residuals** | Missing PyTorch weights | Base analytical tyre friction model ($\Delta \mu = 0$) | **Zero Downtime**. Proceeds with verified physical equations. |


