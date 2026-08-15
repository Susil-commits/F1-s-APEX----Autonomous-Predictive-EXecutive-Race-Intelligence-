# APEX — Autonomous Predictive & EXecutive Race Intelligence

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyTorch-2.2+-EE4C2C.svg" alt="PyTorch" />
  <img src="https://img.shields.io/badge/Stable--Baselines3-DQN-brightgreen.svg" alt="Stable-Baselines3" />
  <img src="https://img.shields.io/badge/React-18-61DAFB.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/Vite-6.0-646CFF.svg" alt="Vite 6" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg" alt="TailwindCSS" />
  <img src="https://img.shields.io/badge/Web_Audio_API-DSP-f59e0b.svg" alt="Web Audio" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

**APEX** is a Formula 1 team pit-wall decision intelligence and mission control platform. Given real-time telemetry from race tracks, APEX maintains a high-fidelity stochastic digital twin, forecasts non-linear tyre wear and Markov weather transitions, computes physical lap-time Delta-T decompositions, performs 1,000-rollout Monte Carlo stochastic rollouts, and provides transparent explainability via TreeSHAP and Deep Q-Networks (DQN).

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

    subgraph ExplainabilityXAI ["🔍 Explainability & Attribution"]
        SHAP["TreeSHAP Waterfall Attribution<br/>f(x) = base + &Sigma; &phi;i"]
        TreeReason["Strategic Decision Reasoning Tree"]
        Feat28 --> SHAP
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
- **Explainable AI (TreeSHAP)**: Decomposes strategic policy confidence score $f(x) = \phi_0 + \sum_{i=1}^{28} \phi_i(x)$, attributing positive and negative feature weights in real time.
- **1,000-Rollout Monte Carlo Engine**: Projects 1,000 parallel stochastic forward trajectories with Gaussian pace variance ($\sigma = 0.35\text{ s}$) and dynamic safety car transition probabilities.

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

### 5. Mission Control Frontend Layout & Modular Component Hierarchy

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
1. **🔍 SHAP Feature Attribution Waterfall**: Shapley additive explanation chart decomposing exact positive and negative feature contributions towards AI confidence score $f(x)$.
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

### 🗺️ Circuits, Audio & Mission Control
15. **🗺️ Multi-Circuit Vector Engine**: Bespoke SVG vector geometries for **Silverstone**, **Monza**, **Spa-Francorchamps**, **Monaco**, and **Interlagos**.
16. **🎙️ Multi-Persona Race Engineer Voice Comms**: Voice personas for **APEX Core AI**, **"Bono"** (*"Hammer time, box box box"*), **"GP"** (*"Manage the tyres, delta is good"*), and **"Xavi"** (*"Plan A, we are checking"*).
17. **📻 Authentic F1 Radio Bandpass & Static Filter DSP**: Web Audio API biquad filter + white noise static burst generator simulating cockpit radio communications.
18. **🏎️ V6 Turbo Hybrid Audio Synthesizer**: Web Audio API FM oscillator generating authentic Formula 1 engine whine matching live RPM.
19. **⏱️ Interactive Pit Crew Stopwatch**: 5-gantry light reaction drill measuring stationary pit duration with pneumatic wheel gun audio.
20. **🏆 Live World Championship Leaderboard**: Dynamic Drivers' and Teams' Championship standings with fastest lap (+1 pt) bonus calculation.
21. **📋 Race Event Telemetry Logger & CSV Exporter**: Chronological incident feed with downloadable `.CSV` reports.

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
├── README.md                              # Flagship system documentation
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
│   │   ├── components/                    # 21 Mission Control components (SHAP, Monte Carlo, DVR, Gantt, etc.)
│   │   ├── data/                          # Multi-circuit vector geometries (Silverstone, Monza, Spa, etc.)
│   │   ├── utils/                         # audioEngine (DSP + Personas + V6 Synth), clientSimulator (Twin)
│   │   ├── store/                         # Zustand state store
│   │   └── hooks/                         # useRaceSocket WebSocket client & twin fallback
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

## 🧪 Testing & Automated Verification

```bash
# Run all unit and integration tests (9/9 passing)
uv run pytest

# Re-run automated strategy benchmark evaluation
uv run python benchmarks/run_benchmarks.py

# Train / fine-tune DQN policy
uv run python backend/training/train_dqn.py --steps 15000
```

---

## 📄 License
MIT License. Created by Susil.
