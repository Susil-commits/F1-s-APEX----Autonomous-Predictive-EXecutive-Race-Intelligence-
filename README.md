# APEX — Autonomous Predictive & EXecutive Race Intelligence

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/FastF1-Real_Telemetry-E10600.svg" alt="FastF1" />
  <img src="https://img.shields.io/badge/Ollama-Radio_LLM-000000.svg" alt="Ollama" />
  <img src="https://img.shields.io/badge/RAG-Decision_Provenance-10b981.svg" alt="RAG" />
  <img src="https://img.shields.io/badge/TreeSHAP-XAI-8b5cf6.svg" alt="TreeSHAP" />
  <img src="https://img.shields.io/badge/Tests-71%2F71_Passed-brightgreen.svg" alt="Tests" />
  <img src="https://img.shields.io/badge/React-18-61DAFB.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/Vite-6.0-646CFF.svg" alt="Vite 6" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg" alt="TailwindCSS" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

**APEX** is a Formula 1 team pit-wall decision intelligence and mission control platform. Grounded in real-world F1 timing telemetry (`fastf1`), APEX maintains a high-fidelity stochastic digital twin, calibrates non-linear tyre wear on multi-season race telemetry, broadcasts local LLM team radio commentary (`ollama`), facilitates natural-language historical debrief queries via RAG (`sentence-transformers`), computes physical lap-time Delta-T decompositions, performs 1,000-rollout Monte Carlo stochastic rollouts, persists auditable race events in async SQLAlchemy, and provides transparent explainability via TreeSHAP and Deep Q-Networks (DQN).

---

## 🏎️ Complete Enterprise Architecture

APEX is structured into a high-performance modular pipeline spanning physical simulation, reinforcement learning, real-time data streaming, digital twin synchronization, cockpit audio DSP, and an interactive React mission control dashboard.

```mermaid
flowchart TD
    subgraph Layer1 ["🏎️ Layer 1: Physics Engine & Stochastic Twin"]
        Track["Track Vectors & 20 Mini-Sectors"]
        Physics["Vehicle Dynamics & 4-Corner Thermals"]
        WeatherModel["Markov Weather State Engine"]
        Track --> Physics
        WeatherModel --> Physics
    end

    subgraph Layer2 ["🧠 Layer 2: AI Strategy & Decision Intelligence"]
        Feat["28-D Feature Extraction Vector"]
        DQNNet["DQN Reinforcement Learning Policy"]
        SHAPEngine["TreeSHAP Feature Attribution"]
        MonteEngine["1,000-Rollout Monte Carlo Sim"]
        Isochrone["Multi-Lap Isochrone Surface"]
        
        Physics --> Feat
        Feat --> DQNNet
        Feat --> SHAPEngine
        Feat --> MonteEngine
        Feat --> Isochrone
    end

    subgraph Layer3 ["⚡ Layer 3: FastAPI Backend & Data Broadcaster"]
        WSServer["WebSocket Telemetry Streamer (60Hz)"]
        REST["FastAPI REST Endpoints (/strategy, /telemetry)"]
        TwinStore["In-Memory State Store & Persistence"]
        
        DQNNet --> WSServer
        SHAPEngine --> WSServer
        MonteEngine --> WSServer
        WSServer <--> TwinStore
        REST <--> TwinStore
    end

    subgraph Layer4 ["🖥️ Layer 4: Mission Control Frontend & Audio DSP"]
        Zustand["Zustand Global State Store"]
        DVR["Time-Travel Telemetry DVR"]
        UIPanels["21 Mission Control UI Panels"]
        Audio["Web Audio DSP & Multi-Persona Voice Engine"]
        
        WSServer ==>|JSON Telemetry Frame| Zustand
        Zustand --> DVR
        Zustand --> UIPanels
        Zustand --> Audio
    end
```

---

### 1. Deterministic Physics, Vehicle Dynamics & Micro-Sectors

The physics engine computes continuous telemetry, vehicle dynamics, tyre degradation, and weather conditions at 60 Hz.

```mermaid
flowchart LR
    subgraph EnvConditions ["🌦️ Environmental Dynamics"]
        WeatherState["Markov Chain Weather Model<br/>(Dry ➔ Damp ➔ Wet)"]
        RainIntensity["Rain Intensity: 0.0 - 1.0"]
        TrackGrip["Dynamic Grip Coefficient &mu;"]
        WeatherState --> RainIntensity --> TrackGrip
    end

    subgraph TyreDynamics ["🛞 Pirelli Tyre Physical Model"]
        Compound["Compound (Soft, Med, Hard, Inter, Wet)"]
        Thermal["4-Corner Carcass & Surface Thermals (FL, FR, RL, RR)"]
        NonLinearWear["Non-Linear Degradation & Cliff Penalty Curve"]
        Compound --> Thermal --> NonLinearWear
    end

    subgraph VehicleDynamics ["🏎️ Chassis & Aerodynamics"]
        FuelMass["Fuel Burn (+0.035 s/kg delta)"]
        AeroDownforce["Front/Rear Wing & Balance Tuner"]
        DirtyAir["Dirty Air Wake Model (+0.8s within 1.2s gap)"]
        DRSBoost["DRS Aero Drag Reduction (-0.45s)"]
        FuelMass --> AeroDownforce
        DirtyAir --> AeroDownforce
        DRSBoost --> AeroDownforce
    end

    subgraph OutputPace ["⏱️ Lap Time Delta-T Decomposition"]
        MiniSectors["20 Mini-Sector Micro-Splits"]
        LapDelta["&Delta;t = Base + Wear + Fuel + Wake - DRS - ERS"]
        NonLinearWear --> LapDelta
        TrackGrip --> LapDelta
        AeroDownforce --> LapDelta
        LapDelta --> MiniSectors
    end
```

#### Physical Equations & Dynamic Factors:
- **Lap Time Delta-T Decomposition**:
  $$\Delta t_{\text{lap}} = t_{\text{base}} + \Delta t_{\text{tyre}}(\text{wear}, T) + \Delta t_{\text{fuel}}(m_{\text{fuel}}) + \Delta t_{\text{wake}}(d_{\text{gap}}) - \Delta t_{\text{DRS}} - \Delta t_{\text{ERS}}$$
- **Fuel Effect**: $+0.035\text{ s/kg}$ penalty for every kilogram of on-board fuel.
- **Tyre Thermal & Wear Cliff**: Non-linear degradation curve with exponential pace penalty once wear exceeds $70\%$, tracking carcass ($T_{\text{carcass}}$) and surface ($T_{\text{surface}}$) temperatures across all 4 wheels.
- **Dirty Air Turbulence**: $+0.8\text{ s/lap}$ aerodynamic downforce loss when trailing within a $1.2\text{ s}$ slipstream wake window.

---

### 2. AI Decision Intelligence, Reinforcement Learning & Explainability (XAI)

APEX fuses Deep Reinforcement Learning (DQN), TreeSHAP feature attributions, Monte Carlo stochastic forward projections, and deterministic expert rule engines.

```mermaid
flowchart TD
    subgraph InputVector ["📊 State Vector Pipeline"]
        RawState["Live RaceState Frame"]
        Feat28["28-D Normalized Tensor<br/>(Gaps, Compounds, Wear%, Weather, Safety Car, Fuel%)"]
        RawState --> Feat28
    end

    subgraph InferenceDecision ["🧠 Reinforcement Learning & Rules"]
        DQN["Deep Q-Network (DQN) Neural Policy"]
        RuleEng["Deterministic Expert Race Rule Engine"]
        ActionSpace["8 Discrete Strategic Actions<br/>(MAINTAIN, PUSH, CONSERVE, PIT_SOFT, PIT_MED, PIT_HARD, PIT_INTER, PIT_WET)"]
        Feat28 --> DQN
        Feat28 --> RuleEng
        DQN --> ActionSpace
        RuleEng --> ActionSpace
    end

    subgraph ExplainabilityXAI ["🔍 Explainability & Model Distillation"]
        DistilledSurrogate["Distilled Tree Surrogate Model<br/>(Fit on DQN Q-Values & Telemetry)"]
        SHAP["TreeSHAP Waterfall Attribution<br/>f(x) = base + &Sigma; &phi;i"]
        TreeReason["Strategic Decision Reasoning Tree"]
        Feat28 --> DistilledSurrogate
        DistilledSurrogate --> SHAP
        ActionSpace --> TreeReason
    end

    subgraph StochasticForward ["🎲 Forward Horizon Simulators"]
        MonteCarlo["1,000-Rollout Monte Carlo Engine<br/>(Gaussian Pace Variance + Safety Car Probability)"]
        Counterfactual["4-Lap Forward Counterfactual Projector"]
        IsochroneMatrix["Multi-Lap Pit Strategy Isochrone Surface"]
        ThreatRadar["Competitor Undercut / Overcut Threat Radar"]
        
        ActionSpace --> MonteCarlo
        ActionSpace --> Counterfactual
        ActionSpace --> IsochroneMatrix
        ActionSpace --> ThreatRadar
    end
```

#### Decision Engine Specifications:
- **28-D State Tensor**: Normalizes position, laps remaining, relative gaps (ahead/behind/leader), one-hot tyre compound, tyre wear %, tyre age, cliff flag, fuel %, driving mode, weather state, rain intensity, 5-lap rain probability, safety car status, and pit stop counts.
- **Discrete Action Space (8 Strategic Modes)**:
  - `0: MAINTAIN` — Preserve current baseline race pace and tyre life.
  - `1: PUSH` — Deploy maximum engine mapping and aggressive cornering ($-0.4\text{ s/lap}$, $+2.5\times$ wear rate).
  - `2: CONSERVE` — Lift-and-coast fuel/tyre preservation mode ($+0.3\text{ s/lap}$, $-40\%$ wear rate).
  - `3: PIT_SOFT`, `4: PIT_MEDIUM`, `5: PIT_HARD`, `6: PIT_INTER`, `7: PIT_WET` — Execute box call for designated compound.
- **Explainable AI (TreeSHAP on Distilled Surrogate)**: Decomposes strategic policy confidence via model distillation: a tree-based surrogate model (`backend/models/shap_surrogate.joblib`) is distilled from the trained DQN's actual $Q(s, a)$ decision surface over thousands of simulated race rollouts and logged DB telemetry. `shap.TreeExplainer` computes exact Shapley attributions $f(x) = \phi_0 + \sum_{i=1}^{28} \phi_i(x)$ via `/api/strategy/shap`, with graceful fallback to heuristic baselines if no distilled model is present.
- **1,000-Rollout Monte Carlo Engine**: Projects 1,000 parallel stochastic forward trajectories via `MonteCarloEngine` and `/api/strategy/monte-carlo` with Gaussian pace variance ($\sigma = 0.38\text{ s}$) and dynamic safety car transition probabilities.

---

### 3. Real-Time Telemetry Streaming, State Sync & Digital Twin

The communication architecture provides bi-directional 60 Hz WebSocket streaming with automatic offline fallback to an embedded deterministic client-side digital twin.

```mermaid
sequenceDiagram
    autonumber
    participant Physics as 🏎️ Physics Engine
    participant FastAPI as ⚡ FastAPI Backend
    participant WS as 📡 WebSocket Streamer
    participant Store as 💾 Zustand Store
    participant DVR as ⏪ Telemetry DVR Buffer
    participant Twin as 🔄 Client Twin Fallback

    loop 60Hz Telemetry Frame Generation
        Physics->>FastAPI: Compute vehicle dynamics & lap splits
        FastAPI->>WS: Broadcast RaceState JSON payload
        alt Online Connection
            WS->>Store: Ingest live telemetry frame
            Store->>DVR: Append to ring buffer (Time-Travel DVR)
        else Offline / Disconnected
            Twin->>Store: Execute deterministic client-side physics twin
        end
    end
```

#### State & Storage Specifications:
- **WebSocket Telemetry Streamer**: Low-overhead JSON frame broadcaster pushing full race telemetry, timing deltas, and tyre statuses at 60 Hz.
- **Async SQLAlchemy Persistence**: Write-through storage engine (`backend/app/twin/store.py`) persisting `RaceSession`, `TelemetryTick`, and `DecisionLog` models to PostgreSQL / SQLite.
- **Zero-Latency Client Twin Fallback**: If the backend connection drops, the frontend transparently switches to the client-side `clientSimulator.ts` twin with identical deterministic physics.
- **Time-Travel Telemetry DVR**: In-memory ring buffer capturing up to 200 laps of historical high-frequency telemetry for instantaneous post-session or in-race timeline scrubbing.

---

### 4. Web Audio DSP, Cockpit Radio & V6 Engine Synthesis

APEX features an integrated Web Audio API digital signal processing (DSP) engine and a Web Speech API multi-persona voice synthesizer.

```mermaid
flowchart LR
    subgraph AudioEngineGraph ["🔊 Web Audio API DSP Signal Chain"]
        direction TB
        V6Osc["V6 Sawtooth Oscillator<br/>f = (RPM / 60) * 3"]
        LowpassFilt["Biquad Lowpass Filter<br/>Cutoff: 2.2 * f"]
        V6Gain["Engine Throttle Gain Node"]
        
        RadioOsc["2.4 kHz Roger Beep Oscillator"]
        StaticNoise["White Noise Buffer Generator"]
        BandpassFilt["Biquad Bandpass Filter<br/>300 Hz - 3.4 kHz"]
        RadioGain["Radio Static Gain Node"]
        
        V6Osc --> LowpassFilt --> V6Gain
        RadioOsc --> BandpassFilt
        StaticNoise --> BandpassFilt --> RadioGain
        
        MasterGain["Master Audio Destination<br/>(AudioContext.destination)"]
        V6Gain --> MasterGain
        RadioGain --> MasterGain
    end

    subgraph SpeechDispatcher ["🎙️ Multi-Persona Speech Synthesis"]
        direction TB
        Trigger["Tactical Event Trigger<br/>(Pit Box, Sector Best, Safety Car, Tyre Cliff)"]
        PersonaRouter{"Persona Router"}
        Bono["'Bono' Voice (Mercedes F1 Tone)"]
        GP["'GP' Voice (Red Bull Racing Tone)"]
        Xavi["'Xavi' Voice (Ferrari Tone)"]
        ApexAI["'APEX Core' AI Voice"]
        
        Trigger --> PersonaRouter
        PersonaRouter --> Bono
        PersonaRouter --> GP
        PersonaRouter --> Xavi
        PersonaRouter --> ApexAI
    end
```

#### Audio & Voice Specifications:
- **Cockpit Radio Acoustic Simulation**: Roger beep ($2.4\text{ kHz}$ sine wave), custom white noise burst generator, and a $300\text{ Hz} - 3.4\text{ kHz}$ biquad bandpass filter replicating FIA telemetry radio transmissions.
- **V6 Turbo Hybrid FM Synth**: Live sawtooth oscillator parameterized dynamically:
  $$f_{\text{engine}} = \left(\frac{\text{RPM}}{60}\right) \times 3 \text{ combustion pulses/rev}$$
- **Multi-Persona Voice Dispatcher**: Authentic race engineer audio callouts with custom voice tuning:
  - **APEX Core AI**: Neutral, data-driven mission control voice.
  - **"Bono"** (Peter Bonnington / Mercedes): *"Hammer time, box box box"*, *"Lewis, it's Bono"*.
  - **"GP"** (Gianpiero Lambiase / Red Bull): *"Manage the tyres, delta is good"*, *"Understood Max"*.
  - **"Xavi"** (Xavier Marcos Padros / Ferrari): *"Plan A, we are checking"*, *"Box now for Hard"*.

---

### 5. Real F1 Telemetry Datasets & FastF1 Tyre Degradation Calibration

To replace synthetic degradation formulas with empirical ground truth, APEX ingests and models real-world Formula 1 timing telemetry via the `fastf1` API across multiple seasons and circuit profiles.

```mermaid
flowchart TD
    subgraph DataIngestion ["📥 FastF1 Ingestion & Cleaning Pipeline"]
        F1API["FastF1 Timing API (2022-2023 Grand Prix)"] --> Fetcher["backend/training/fetch_fastf1_data.py"]
        Fetcher --> Filter1["Exclude Pit In/Out Laps & Inaccurate Markers"]
        Filter1 --> Filter2["Exclude Safety Car & VSC Periods (TrackStatus != '1')"]
        Filter2 --> DeltaTCalc["Compute lap_time_delta = lap_time - driver_fastest_lap"]
        DeltaTCalc --> FuelCorrect["Fuel Effect Correction (+0.055s / lap car burn-off)"]
        FuelCorrect --> RawCSV["backend/data/real_tyre_data.csv<br/>(4,276 Clean Telemetry Laps)"]
    end

    subgraph CalibrationValidation ["📊 Polynomial Calibration & Held-Out Validation"]
        RawCSV --> PolyFit["Quadratic Polynomial Regression<br/>loss(age) = c2 * age^2 + c1 * age"]
        PolyFit --> CrossVal["Held-Out Race Circuit Validation (e.g. Spa / Silverstone)"]
        CrossVal --> Metrics["Compute R² & RMSE vs Naive Linear Baseline"]
        CrossVal --> ModelJSON["backend/models/calibrated_tyre_model.json"]
        CrossVal --> PlotPNG["backend/models/tyre_model_validation.png"]
    end

    subgraph RuntimeEngine ["🏎️ Digital Twin Runtime Integration"]
        ModelJSON --> TyreIntelligence["backend/app/intelligence/tyre_model.py"]
        TyreIntelligence --> DegPredictor["Empirical Degradation & Cliff Prediction"]
        TyreIntelligence -.-> SyntheticFallback["Graceful Synthetic Fallback (Offline Safe)"]
    end
```

#### Real Data Calibration Specifications:
- **Telemetry Volume**: **4,276 clean race laps** collected from 5 real Grand Prix sessions (2023 Silverstone, 2023 Monza, 2023 Spain, 2022 Silverstone, 2022 Monza).
- **Fuel Mass Decoupling**: In Formula 1, cars shed approximately $1.7 - 1.9\text{ kg/lap}$ of fuel, yielding a $\approx -0.055\text{ s/lap}$ pace advantage that masks tyre degradation during stint progression. APEX corrects for stint-relative fuel burn to isolate pure tyre degradation loss $\Delta t_{\text{tyre}}(a)$.
- **Empirical Degradation Equation**:
  $$\Delta t_{\text{loss}}(a) = c_2 \cdot a^2 + c_1 \cdot a + \mathbb{I}_{\{w > w_{\text{cliff}}\}} \cdot \left(w - w_{\text{cliff}}\right) \cdot \lambda_{\text{cliff}}$$
  where $a$ is tyre age in laps, $w$ is tyre wear %, and $c_1, c_2$ are empirically calibrated per compound (`SOFT`, `MEDIUM`, `HARD`).

---

### 6. Local LLM Race Engineer Commentary & Fact Verification

APEX translates complex multidimensional decision attributions into authentic F1 team radio calls in real time using local instruction-tuned LLMs (`ollama` + `llama3.2:3b`) operating under strict zero-hallucination constraints.

```mermaid
flowchart LR
    subgraph DecisionAttribution ["🧠 Strategic Attribution Input"]
        State["RaceState Telemetry"] --> Explainer["ExplainabilityEngine"]
        Explainer --> DecObj["DecisionExplanation<br/>• recommendation<br/>• confidence_score<br/>• urgency<br/>• primary_factors (SHAP)<br/>• tyre_cliff_risk"]
    end

    subgraph LLMTranslation ["🎙️ Local LLM Radio Generator"]
        DecObj --> PromptBuilder["Constrained Prompt Builder<br/>• Limit: < 20 words<br/>• Strict Fact Grounding<br/>• Radio Comms Tone"]
        PromptBuilder --> OllamaClient["Local Ollama Client<br/>(model: llama3.2:3b)"]
        OllamaClient --> FactChecker{"is_fact_consistent()<br/>No Invented Numbers?"}
        FactChecker -- Passed --> RadioText["Verified Radio Message"]
        FactChecker -- Violated / Offline --> PersonaFallback["Persona-Aligned Template Fallback<br/>(Bono, GP, Xavi, Apex Core)"]
    end

    subgraph UIComms ["📻 Cockpit Broadcasting"]
        RadioText --> WSServer["WebSocket Streamer"]
        PersonaFallback --> WSServer
        WSServer --> StrategyCard["StrategyCard.tsx (Radio Bubble)"]
        WSServer --> SpeechSynth["Web Audio TTS Dispatcher"]
    end
```

#### Commentary Architecture Specifications:
- **LLM as Pure Translator, Not Decision-Maker**: The LLM never selects strategy actions or invents metrics. It strictly translates verified telemetry attributions (DQN policy, TreeSHAP drivers, and pit window status) into concise team radio transmissions.
- **Deterministic Fact Consistency Validator**: Module `is_fact_consistent()` performs regex token verification on all generated numbers. If the LLM generates a numerical claim absent from the ground-truth explanation, it immediately rejects the output and triggers the persona template fallback.
- **Tick Debouncing**: To conserve local inference compute, the generator debounces calls, only generating new transmissions when the recommendation changes, urgency shifts, or every 5 laps.

---

### 7. Historical Race Strategy RAG (`sentence-transformers` + SQL Audit)

APEX includes a Retrieval-Augmented Generation (RAG) system enabling race directors and strategists to interrogate past race decisions using natural-language questions grounded strictly in persisted `DecisionLogModel` records.

```mermaid
flowchart TD
    subgraph StorageLayer ["💾 Persisted Decision Logs"]
        DB[(PostgreSQL / SQLite Database)] --> StoredLogs["DecisionLogModel Rows<br/>(race_id, lap, recommendation, confidence, urgency, SHAP factors)"]
        StoredLogs --> Serializer["format_decision_log()<br/>Rich Semantic Serialization"]
    end

    subgraph VectorRetrieval ["🔍 Dense Vector Embeddings & Similarity Search"]
        Serializer --> DenseEmbed["SentenceTransformer (all-MiniLM-L6-v2)<br/>Normalized 384-D Embeddings"]
        UserQuery["User Natural-Language Query<br/>'Why did we pit on lap 23?'"] --> QueryEmbed["embed_text(query)"]
        DenseEmbed --> CosSim["NumPy Cosine Similarity Engine<br/>sim = (A · B) / (||A|| * ||B||)"]
        QueryEmbed --> CosSim
        CosSim --> TopK["Top-k Ground-Truth Citations (k=5)"]
    end

    subgraph GroundedSynthesis ["📝 Zero-Hallucination Answer Generation"]
        TopK --> PromptContext["Grounded Context Block<br/>(Verified Decision Logs 1..k)"]
        PromptContext --> OllamaQA["Ollama Local LLM / Grounded Extractor"]
        OllamaQA --> FormattedResponse["Structured Q&A Payload<br/>• answer<br/>• citations / source logs<br/>• similarity scores<br/>• model provenance"]
    end

    subgraph FrontendAudit ["🖥️ Mission Control RAG Debrief"]
        FormattedResponse --> RESTRoute["POST /api/race/ask"]
        RESTRoute --> UIModal["RaceHistoryQA.tsx Debrief Modal"]
    end
```

#### Strategy RAG Specifications:
- **Vector Space**: Embeds serialized decision trails into a 384-dimensional dense semantic space using `all-MiniLM-L6-v2`, with a fallback hash vectorizer for disconnected environments.
- **NumPy Brute-Force Vector Retrieval**: Because race sessions contain hundreds to a few thousand decision logs, in-memory NumPy cosine similarity provides microsecond latency without external vector database dependencies.
- **Citation Provenance**: Every response returned by `/api/race/ask` attaches full decision citations (Lap #, Directive, Confidence %, Urgency, Rule/DQN consensus, and Top SHAP factors) so every answer is auditable.
- **Out-of-Scope Guarantee**: Queries regarding laps or events absent from the database trigger explicit refusals (*"I don't have that information in the race history logs"*) rather than hallucinatory extrapolations.

---

### 8. Mission Control Frontend Layout & Modular Component Hierarchy

The React 18 dashboard is structured into 4 synchronized workspaces driven by Zustand state management.

```mermaid
flowchart TD
    RootApp["App.tsx (Root Layout)"]
    
    subgraph TopNav ["🎛️ Header & Mode Switcher"]
        Header["Header (Circuit Selector, Live Clock, Status)"]
        RaceControls["Race Controls (Play/Pause, 1x-10x Speed, Reset)"]
        VoiceSelector["Voice Persona Selector & Mute"]
    end

    subgraph LeftCol ["🗺️ Circuit & Timing"]
        TrackMap["2D Vector SVG Circuit Map<br/>(Silverstone, Monza, Spa, Monaco, Interlagos)"]
        TimingTower["Live Timing Tower (Gaps, Sectors, Intervals)"]
        MiniSectors["20 Mini-Sector Micro-Timing Grid"]
        TrackRibbon["Linear Gap Progression Ribbon"]
    end

    subgraph CenterCol ["📊 Telemetry & Dynamics Lab"]
        DeltaT["Lap Time Delta-T Physical Decomposition"]
        ChassisTuner["Chassis Aerodynamics & Setup Balancer"]
        TyreThermal["4-Corner Tyre Thermal Matrix"]
        DualDriver["Dual-Driver Overlay Comparator"]
        WeatherRadar["10-Lap Doppler Weather Radar"]
        DVRScrubber["Telemetry DVR Time-Travel Scrubber"]
    end

    subgraph RightCol ["🧠 Strategy & Decision Intelligence"]
        Copilot["AI Pit Wall Strategist Copilot"]
        DQNViewer["DQN Policy & Q-Value Tensor Inspector"]
        SHAPChart["SHAP Feature Attribution Waterfall"]
        MonteCarloSim["Monte Carlo 1,000-Rollout Sim"]
        IsochroneGrid["Pit Strategy Isochrone Matrix"]
        UndercutMatrix["Undercut / Overcut Threat Radar"]
        StintGantt["Stint Strategy Gantt Matrix"]
    end

    subgraph BottomCol ["📋 Event Logs & Championship"]
        RaceLogger["Event Logger & CSV Exporter"]
        Standings["FIA Championship Leaderboard"]
        PostRaceModal["Podium & Post-Race Debrief"]
    end

    RootApp --> TopNav
    RootApp --> LeftCol
    RootApp --> CenterCol
    RootApp --> RightCol
    RootApp --> BottomCol
```

---

## 🌟 Flagship Feature Suite (21 Modules)

### 🧠 Explainable AI & Decision Intelligence
1. **🔍 SHAP Feature Attribution Waterfall**: Shapley additive explanation chart decomposing exact positive and negative feature contributions towards AI confidence score $f(x)$ powered by backend `shap.TreeExplainer`.
2. **🧠 DQN Neural Network Policy Tensor Inspector**: Live 28-D normalized input state tensor and Q-value distribution across all 8 strategic actions (`MAINTAIN`, `PUSH`, `CONSERVE`, `PIT_SOFT`, `PIT_MEDIUM`, `PIT_HARD`, `PIT_INTER`, `PIT_WET`).
3. **🎲 Monte Carlo 1,000-Rollout Strategy Simulator**: 1,000 parallel stochastic forward simulations with Gaussian pace variance and safety car probability distributions.
4. **🗺️ Multi-Lap Pit Strategy Isochrone Matrix**: 2D parameter grid identifying the global minimum total race time valley across laps and compounds.
5. **🤖 AI Pit Wall Strategist Copilot**: Conversational AI assistant with quick tactical prompts and text-to-speech audio dispatcher.
6. **🎯 Competitor Undercut & Overcut Threat Radar**: Real-time threat matrix evaluating pit box overlap and outlap pace deltas.

### 📊 Telemetry, Vehicle Physics & Aerodynamics
7. **⏱️ Lap Time Delta-T Physical Decomposition**: Decomposes lap times into fuel mass $(+s)$, tyre degradation $(+s)$, dirty air wake $(+s)$, ERS hybrid boost $(-s)$, and DRS gain $(-s)$.
8. **🏎️ Chassis Aerodynamics & Setup Balancer**: Live tuning for Front/Rear Wing angles, Brake Bias %, Differential lock %, and Top Speed vs Lateral G curves.
9. **👥 Dual-Driver Comparative Telemetry Overlay**: Overlaid waypoint velocity curves and tyre wear differentials vs any competitor.
10. **⏱️ 20 Mini-Sector Micro-Timing Matrix**: Micro-sector splits across 20 track segments (**Purple** = Session Best, **Green** = Personal Best, **Yellow** = Slower).
11. **⏪ Race Telemetry DVR & Time-Travel Scrubber**: Historical replay scrubber allowing engineers to inspect telemetry at any past lap.
12. **🏎️ 4-Corner Tyre Thermal Matrix**: Real-time FL, FR, RL, RR carcass thermals and surface wear rates.
13. **🌦️ 10-Lap Doppler Weather Radar**: Forward rain probability curve with intermediate (35%) and wet (70%) crossover lines.
14. **⚔️ Head-to-Head Driver Battle Radar**: DRS detection, slipstream delta (+14.2 km/h), and overtake probability %.

### 🧠 Real Data, LLMs & Retrieval Intelligence
15. **🛞 FastF1 Real Data Tyre Calibration**: Polynomial degradation models calibrated on 4,276 real Grand Prix race laps across Silverstone, Monza, and Spa with fuel effect isolation.
16. **🎙️ Local LLM Race Engineer Commentary (Ollama)**: Real-time radio transmissions generated from decision attributions via `llama3.2:3b` with strict zero-hallucination fact verification.
17. **🔍 Historical Race Strategy RAG (`sentence-transformers`)**: Semantic question answering over persisted decision logs with cosine similarity vector retrieval and citation cards.

### 🗺️ Circuits, Audio & Mission Control
18. **🗺️ Multi-Circuit Vector Engine**: Bespoke SVG vector geometries for **Silverstone**, **Monza**, **Spa-Francorchamps**, **Monaco**, and **Interlagos**.
19. **🎙️ Multi-Persona Race Engineer Voice Comms**: Voice personas for **APEX Core AI**, **"Bono"** (*"Hammer time, box box box"*), **"GP"** (*"Manage the tyres, delta is good"*), and **"Xavi"** (*"Plan A, we are checking"*).
20. **📻 Authentic F1 Radio Bandpass & Static Filter DSP**: Web Audio API biquad filter + white noise static burst generator simulating cockpit radio communications.
21. **🏎️ V6 Turbo Hybrid Audio Synthesizer**: Web Audio API FM oscillator generating authentic Formula 1 engine whine matching live RPM.
22. **⏱️ Interactive Pit Crew Stopwatch**: 5-gantry light reaction drill measuring stationary pit duration with pneumatic wheel gun audio.
23. **🏆 Live World Championship Leaderboard**: Dynamic Drivers' and Teams' Championship standings with fastest lap (+1 pt) bonus calculation.
24. **📋 Race Event Telemetry Logger & CSV Exporter**: Chronological incident feed with downloadable `.CSV` reports and async DB persistence.

---

## 📊 Evaluation & Benchmark Matrix

Automated head-to-head evaluation across 15 seeded multi-circuit races (Silverstone, Monza, Spa, Monaco, Interlagos) with real-calibrated tyre degradation:

| Policy | Avg Finishing Position | Win Rate (%) | Podium Rate (%) | Avg Gap to P1 (s) | Blown Tyre Laps | Avg Pit Stops |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RANDOM BASELINE** | 6.53 | 26.7% | 33.3% | +58.65s | 19.46 | 0.0 |
| **RULE-BASED ENGINE** | **1.27** | **86.7%** | **93.3%** | **+1.19s** | **0.00** | 4.4 |
| **RETRAINED DQN POLICY** | **1.07** | **93.3%** | **100.0%** | **+0.12s** | **0.00** | 4.3 |

---

## 📁 Repository Structure

```
APEX/
├── .github/
│   └── workflows/ci.yml                   # Continuous Integration (pytest + build verification)
├── pyproject.toml                         # Python project & dependencies (uv managed)
├── docker-compose.yml                     # Redis + Postgres container configuration
├── README.md                              # Flagship system documentation
├── backend/
│   ├── app/
│   │   ├── simulator/                     # Deterministic physics engine, car physics & Pydantic models
│   │   ├── intelligence/                  # Feature builder, TreeSHAP explainer, tyre & weather models
│   │   ├── strategy/                      # Rule engine, Gymnasium RL env, DQN agent, Monte Carlo, explainability
│   │   ├── twin/                          # SQLAlchemy database models, Redis hot cache & write-through store
│   │   ├── api/                           # FastAPI routes & WebSocket broadcaster
│   │   └── main.py                        # FastAPI entry point
│   ├── models/                            # Trained DQN checkpoints & multi-action distilled TreeSHAP artifacts
│   ├── training/                          # RL training (train_dqn.py) & surrogate distillation (distill_dqn_surrogate.py)
│   └── tests/                             # Automated unit & integration tests
├── frontend/                              # React 18 + Vite + Tailwind Mission Control
│   ├── src/
│   │   ├── components/                    # 34 Mission Control components (SHAP Comparator, Scenario Injector, DVR, etc.)
│   │   ├── data/                          # Multi-circuit vector geometries (Silverstone, Monza, Spa, etc.)
│   │   ├── utils/                         # audioEngine (DSP + Personas + V6 Synth), clientSimulator (Twin)
│   │   ├── store/                         # Zustand state store
│   │   └── hooks/                         # useRaceSocket WebSocket client & twin fallback
│   └── package.json
└── benchmarks/                            # Automated evaluation suite
    ├── run_benchmarks.py
    └── benchmark_report.md
```

> [!NOTE]
> **Reproducibility & Model Artifacts**: Binary model artifacts (`apex_dqn.zip`, `best_model.zip`, `shap_surrogate.joblib`, `shap_multi_action_surrogate.joblib`, `training_rewards.png`) are committed directly to the repository to guarantee deterministic out-of-the-box runnability without requiring multi-hour RL retraining loops in CI. Policy-surrogate alignment is validated at runtime via SHA-256 checkpoint hashing.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11 - 3.12** & [`uv`](https://docs.astral.sh/uv/)
- **Node.js 18+** & `npm`

### 2. Install Dependencies & Build Frontend

```bash
# Install Python backend dependencies
uv sync

# Install Frontend dependencies & build bundle
cd frontend
npm install
npm run build
cd ..
```

### 3. Launch Mission Control Dashboard

```bash
uv run uvicorn backend.app.main:app --port 8000 --reload
```

Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)** (or run `npm run dev` in `frontend/` for Vite HMR at **[http://localhost:5173](http://localhost:5173)**).

---

## 🧪 Testing, Training & Distillation

```bash
# Run all unit and integration tests (71/71 passing across 14 modules)
uv run pytest

# Download & clean real-world FastF1 multi-circuit telemetry
uv run python backend/training/fetch_fastf1_data.py

# Fit real tyre degradation curves & generate validation benchmark plot
uv run python backend/training/validate_tyre_model.py

# Distill multi-action DQN policy decision surface into TreeSHAP surrogate
uv run python backend/training/distill_dqn_surrogate.py --episodes 80

# Re-run automated strategy benchmark evaluation across all 5 circuits
uv run python benchmarks/run_benchmarks.py --races-per-track 5

# Train / fine-tune DQN policy with EvalCallback
uv run python backend/training/train_dqn.py --steps 80000
```

