
# APEX — MASTER ENGINEERING & REMEDIATION SPECIFICATION
## Autonomous Predictive & EXecutive Race Intelligence
### Target: production-grade research prototype / ~90% architecture completeness

**Repository:** https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-

## 0. PURPOSE

This document is the single source of truth for an implementation agent upgrading APEX.
Do not treat the README as the implementation contract. Inspect the actual code first.

Current public repository already advertises a substantially expanded architecture:
FastF1 data, 60 Hz digital twin, DQN, PINN tyre residuals, Safe-RL masking,
TreeSHAP, Monte Carlo, agentic strategy, MCP, RAG, self-healing/evaluation,
React cockpit, Docker, Redis and PostgreSQL. The repository also exposes training,
benchmark and championship commands.

The goal of this document is NOT to add technologies for appearance. The goal is to
make every subsystem real, connected, testable, measurable and reproducible.

TARGET:
    DATA -> STATE -> PREDICTION -> SIMULATION -> OPTIMIZATION -> RL -> RISK
    -> DECISION -> ACTION -> UPDATED STATE -> LOGGING -> LEARNING

RULE:
Never claim a component is complete unless:
1. implementation exists,
2. it is wired into the runtime path,
3. it has tests,
4. it has measurable evaluation,
5. it has documentation,
6. it has deterministic/reproducible execution where applicable.

---

# 1. FIRST ACTION: REPOSITORY FORENSIC AUDIT

Before changing code:

1. Clone repository.
2. Create a clean branch:
   `feat/apex-v2-autonomous-race-intelligence`
3. Install backend with uv.
4. Install frontend.
5. Run all tests.
6. Run evaluation harness.
7. Run benchmark suite.
8. Run DQN/PPO training smoke tests.
9. Run Docker Compose.
10. Build frontend.
11. Record exact failures.

Create:
`docs/BASELINE_AUDIT.md`

Record:
- Python version
- Node version
- dependency versions
- test count/pass/fail
- lint/type-check status
- benchmark results
- startup errors
- API errors
- frontend build errors
- missing environment variables
- model artifact availability
- data availability
- performance
- memory/CPU use

Do NOT "fix" failures by weakening tests.

---

# 2. TARGET ARCHITECTURE

                    REAL / SYNTHETIC F1 DATA
                              |
                       Data ingestion
                              |
                    Raw immutable storage
                              |
                  Cleaning + schema validation
                              |
                    Feature engineering
                              |
                 Versioned Feature/Dataset Layer
                              |
          +-------------------+--------------------+
          |                   |                    |
       Tyre AI             Weather AI         Opponent AI
          |                   |                    |
       Driver AI           Health AI            Pace AI
          +-------------------+--------------------+
                              |
                        State Estimator
                              |
                     Race Digital Twin
                              |
              +---------------+---------------+
              |               |               |
         Monte Carlo     Counterfactual    Optimizer
              |               |               |
              +---------------+---------------+
                              |
                     RL policy (DQN/PPO)
                              |
                         Risk Engine
                              |
                     Safe Action Mask
                              |
                    Decision Aggregator
                              |
                            ACTION
                              |
                    Digital Twin update
                              |
                    Event / Decision Log
                              |
                Replay / Evaluation / RAG

LLM/RAG/MCP must sit around the structured decision engine, not replace
physics, prediction, optimization or RL.

---

# 3. SYSTEM OF RECORD AND DATA CONTRACTS

Define Pydantic models for:

RaceState
CarState
DriverState
TyreState
WeatherState
TrackState
VehicleHealthState
OpponentState
StrategyState
DecisionState
ScenarioState
Prediction
RiskAssessment
DecisionExplanation
ModelMetadata

Every object must have:
- timestamp / simulation time
- race_id
- car_id where relevant
- schema_version
- source
- confidence when probabilistic

Never pass arbitrary dictionaries between major modules.

---

# 4. REAL F1 DATA PIPELINE

Primary source:
FastF1 for timing/telemetry/session/weather data.

Secondary source:
Jolpica/F1 API or other permitted public source for complementary race metadata.

Pipeline:

raw -> validate -> clean -> normalize -> align -> feature-engineer
     -> dataset snapshot -> train/validation/test split

Required modules:

backend/training/
  data/
    fastf1_loader.py
    jolpica_loader.py
    session_loader.py
    raw_store.py
  preprocessing/
    telemetry_cleaner.py
    lap_cleaner.py
    weather_cleaner.py
    race_control_cleaner.py
    alignment.py
  features/
    tyre_features.py
    weather_features.py
    opponent_features.py
    driver_features.py
    vehicle_features.py
    strategy_features.py
  datasets/
    dataset_builder.py
    dataset_validator.py
    dataset_manifest.py

Data requirements:
- cache raw downloads
- never silently replace missing values
- log missingness
- preserve units
- normalize timestamps
- align telemetry to lap/sector/race time
- keep source metadata
- version feature schemas

Dataset manifest must include:
dataset_version
source_versions
seasons
races
sessions
row_count
feature_count
missingness
hash
creation_time
split_definition

CRITICAL:
Never randomly split rows from the same race into train and test.
Use race-based / event-based / season-based splits.

---

# 5. DATA QUALITY / LEAKAGE

Implement automated checks:

- duplicate rows
- impossible tyre ages
- negative fuel
- invalid compounds
- future-information leakage
- target leakage
- timestamp ordering
- missing telemetry bursts
- outlier speed/RPM
- invalid race position
- impossible pit-stop timing

Fail the training job if severe leakage is detected.

---

# 6. FEATURE STORE

Build a canonical feature builder.

Core features:

Race:
lap, laps_remaining, race_position, pit_count, safety_car, VSC, red_flag

Gaps:
gap_ahead, gap_behind, leader_gap, undercut_window

Tyre:
compound, tyre_age, wear, thermal_state, cliff_probability

Weather:
air_temp, track_temp, rain_probability, rain_intensity,
track_wetness, drying_rate, grip

Car:
fuel, ERS, brake_state, power_state, aero_state

Opponent:
pace_delta, strategy_probability, pit_probability,
attack_probability, defence_probability

Driver:
pace, consistency, aggression, tyre_management, overtake_probability

Health:
engine_temp, brake_temp, battery_temp, voltage, anomaly_score,
failure_probability

Every feature must have:
name, unit, range, source, update frequency, missing-value policy.

---

# 7. TYRE INTELLIGENCE

Objective:
Predict pace/degradation and pit-window value.

Models:
1. baseline linear/ridge regression
2. tree model (XGBoost/LightGBM if allowed; otherwise RandomForest)
3. temporal model only if baselines justify it
4. existing PINN residual model

Targets:
next_lap_time
degradation_rate
remaining_useful_life
cliff_probability
optimal_pit_window

Metrics:
MAE, RMSE, R2, calibration, error by compound, error by track, error by tyre age.

Do not use the PINN merely as a decorative model.
Compare:
physics-only
ML-only
physics + residual
and quantify improvement.

---

# 8. WEATHER INTELLIGENCE

State:
dry / damp / wet / heavy_wet

Predict:
rain probability at 1/3/5/10 laps
rain intensity
wetness
drying rate
grip
slick-intermediate crossover
intermediate-wet crossover

Weather predictions must affect:
tyre model
pace
strategy
Monte Carlo
RL observation

Maintain uncertainty/calibration.

---

# 9. OPPONENT INTELLIGENCE

For every opponent maintain an OpponentState.

Features:
position
gap
pace
tyre
tyre_age
pit history
driver
team
weather
traffic
recent actions

Predict:
P(pit next lap)
P(pit within 2 laps)
P(attack)
P(defend)
expected pace delta
compound probability
strategy probability

Start with interpretable baselines before deep sequence models.

Evaluation:
Brier score for probabilities
log loss
MAE for pace
precision/recall for pit events
calibration curve.

---

# 10. DRIVER INTELLIGENCE

Driver state:
pace
variance
consistency
aggression
defence
overtake
tyre management
mistake proxy

Do not hardcode famous driver stereotypes.
Infer behavior from data where possible.
If insufficient data, use neutral priors and clearly label them.

---

# 11. VEHICLE HEALTH

Real F1 failure telemetry is limited. Do NOT claim unavailable proprietary telemetry.

Build a synthetic telemetry generator calibrated to plausible ranges.

Signals:
engine temp
oil temp
coolant temp
brake temp
battery temp
voltage
ERS output
brake pressure
power output
cooling efficiency

Inject controlled anomalies:
thermal drift
voltage sag
power loss
brake degradation
battery anomaly
sensor drift

Models:
Isolation Forest baseline
Autoencoder optional

Outputs:
health_score
anomaly_score
failure_probability
failure_horizon

Health must affect:
push permission
strategy
risk
race outcome.

---

# 12. DIGITAL TWIN

The digital twin is the authoritative state machine.

It must support:
- deterministic seed
- replay
- snapshot
- restore
- branch/fork
- event log
- state hash

State transition:

previous_state + action + environment + random_seed
-> next_state + event_list

Do not let UI mutate simulation state directly.

Use command/event semantics:
Command -> validation -> state transition -> event -> subscribers.

---

# 13. PHYSICS / SIMULATION VALIDATION

Audit every hardcoded physical coefficient.

Classify each parameter:
- sourced from public data
- calibrated from empirical data
- engineering assumption
- synthetic scenario parameter

Never present an assumption as real-world F1 physics.

Create:
`docs/PHYSICS_ASSUMPTIONS.md`

For each equation:
- formula
- units
- source
- calibration method
- valid range
- test

---

# 14. COUNTERFACTUAL ENGINE

Existing Monte Carlo/counterfactual capability must be converted into a reusable engine.

Candidate actions:
MAINTAIN
PUSH
CONSERVE
PIT_SOFT
PIT_MEDIUM
PIT_HARD
PIT_INTER
PIT_WET
ENERGY_DEPLOY
ENERGY_HARVEST
ATTACK
DEFEND

For each action:
1. clone state
2. apply action
3. run stochastic rollout
4. collect outcome
5. aggregate distribution
6. calculate risk
7. return explanation

Support:
100, 1000, 10000 rollouts.

Do not use a fixed random outcome.
Seed all experiments.

Outputs:
win_probability
podium_probability
expected_finish
finish_distribution
DNF_probability
expected_time_delta
pit_loss
tyre_risk
weather_risk
confidence_interval

---

# 15. STRATEGY OPTIMIZATION

Maintain multiple independent baselines:

Random
Greedy
Rule
Monte Carlo
DQN
PPO
Hybrid

Where useful, use OR-Tools for constrained strategy planning.
Do not make OR-Tools or RL the sole authority.

---

# 16. RL ENVIRONMENT

Use Gymnasium-compatible environment.

Observation must include only information available at decision time.

Action space must be discrete and explicitly validated.

Implement:
reset(seed)
step(action)
action_mask
observation_space
action_space

Reward components:
position gain/loss
finish result
lap pace
tyre health
pit loss
fuel/energy efficiency
mechanical risk
collision/DNF
strategic success

Log each reward component separately.

---

# 17. DQN REMEDIATION

Current DQN must be treated as an experiment, not assumed superior.

Diagnose:
state normalization
reward scale
action masking
episode length
exploration
terminal conditions
replay distribution
reward sparsity

Then benchmark:
vanilla DQN
Double DQN
Dueling DQN
Prioritized replay if implemented correctly

Use separate train and evaluation seeds.

Do not select the model by training reward.
Select using held-out race scenarios.

---

# 18. PPO

Add PPO only after the environment is stable.

Compare DQN vs PPO on identical scenario seeds.

Report:
win
podium
average finish
DNF
reward
decision latency
strategy stability

---

# 19. SAFE DECISION LAYER

Safety mask must be independent of the learned policy.

Examples:
- incompatible tyre in extreme rain
- invalid pit action while pit lane unavailable
- push when mechanical risk exceeds hard limit
- impossible action due to race control
- action violating simulator constraints

Architecture:

policy scores -> safety mask -> feasible actions -> decision aggregation.

Never allow the LLM to bypass safety constraints.

---

# 20. RISK ENGINE

Risk vector:
tyre
weather
traffic
mechanical
pit
collision
strategy
DNF

Compute:
expected reward
risk-adjusted reward
confidence

Use configurable risk appetite.

Example:
score = expected_finish_value - lambda * total_risk

Do not use arbitrary weights without documenting them.

---

# 21. HYBRID DECISION AGGREGATOR

Inputs:
rule score
Monte Carlo expected outcome
DQN policy
PPO policy
predictive models
risk engine
safety mask

Output:
action
confidence
expected_finish
win_probability
podium_probability
risk
alternatives
reasons

The aggregator must be deterministic given identical inputs/seed.

---

# 22. EMERGENCY BRAIN

Scenario handlers:
rain onset
heavy rain
drying track
Safety Car
VSC
red flag
puncture
brake degradation
engine issue
battery issue
unexpected opponent pit
crash/debris

Pipeline:
DETECT -> CLASSIFY -> ESTIMATE -> GENERATE -> SIMULATE -> RANK -> ACT -> LOG

Every scenario needs a test fixture.

---

# 23. HISTORICAL REPLAY

Use historical FastF1 races.

At decision points:
- reconstruct state
- hide future information
- ask APEX for decision
- record actual decision
- simulate counterfactual
- compare

Metrics:
decision agreement
counterfactual delta
prediction error
strategy stability

Never claim causal superiority over a real race unless scientifically established.

---

# 24. AI VS AI CHAMPIONSHIP

Agents:
Random
Rule
Conservative
Aggressive
Tyre Optimizer
DQN
PPO
Hybrid APEX

Run at least 100 seeded races across multiple circuits/scenario distributions.

Track:
points
wins
podiums
DNF
average finish
pit stops
risk
decision latency

Persist raw results.

---

# 25. ABLATION

Required experiments:

Full APEX
-no weather
-no tyre AI
-no opponent AI
-no health AI
-no Monte Carlo
-no risk
-no RL
-no PINN

Each run uses identical seeds.

This proves which components actually add value.

---

# 26. EXPLAINABILITY

TreeSHAP should explain a surrogate or suitable interpretable model.
Do not imply SHAP mathematically explains the original neural network if it only explains a surrogate.

Decision explanation:

ACTION
CONFIDENCE
TOP FEATURES
COUNTERFACTUALS
RISK
ALTERNATIVES

Use:
"What changed?"
"Why now?"
"What happens if we don't act?"

---

# 27. RAG / LLM / MCP

RAG is for historical knowledge and decision provenance.
LLM is for explanation/commentary and operator interaction.

Do NOT use LLM output as an uncontrolled race decision.

MCP tools should expose structured operations:
get_state
explain_decision
simulate_strategy
run_monte_carlo
trigger_scenario
query_history
get_model_status

Validate all MCP inputs with schemas.

Remove/avoid hidden Chain-of-Thought exposure.
Return concise decision rationale and evidence, not private reasoning traces.

---

# 28. SELF-HEALING

Self-healing must be bounded and safe.

Allowed:
- restart failed worker
- reload model if checksum verified
- fall back to previous model
- disable degraded optional service
- alert operator

Not allowed:
- autonomous source-code rewriting in production
- silently changing physics constants
- silently changing model weights

Use:
current model -> candidate -> validation gates -> promotion/rollback.

---

# 29. MODEL REGISTRY / MLOPS

Every model artifact needs:
model_name
version
dataset_version
feature_version
training_seed
hyperparameters
metrics
checksum
created_at
status

Promotion:
candidate -> validation -> staging -> production

Drift:
feature drift
prediction drift
performance drift
calibration drift

Use MLflow or a lightweight equivalent if it does not overcomplicate the project.

---

# 30. OBSERVABILITY

Metrics:
simulation step latency
decision latency
model latency
Monte Carlo latency
WebSocket latency
API latency
queue depth
memory
CPU

ML metrics:
prediction confidence
uncertainty
drift
action distribution
fallback rate

Use Prometheus/Grafana only where useful.

---

# 31. DATABASE / CACHE

PostgreSQL:
historical races
sessions
telemetry metadata
decisions
experiments
model registry
scenario results

Redis:
current race state
pub/sub
short-lived Monte Carlo jobs
rate limiting

Never use Redis as permanent source of truth.

---

# 32. API CONTRACT

Version endpoints:
`/api/v1/...`

Required:
health
race
telemetry
strategy
prediction
counterfactual
monte-carlo
scenarios
models
experiments
replay
explainability

Use Pydantic response schemas.
Return correlation/request IDs.

---

# 33. FRONTEND

Required views:
Live Race
Strategy Center
Tyre Intelligence
Weather
Opponent
Driver
Vehicle Health
Counterfactual Lab
Replay
RL Training
Benchmark
Explainability
AI Championship
System Health

Frontend must not calculate authoritative race physics.
It consumes backend state.

---

# 34. ERROR HANDLING

Classify:
DATA_ERROR
MODEL_ERROR
SIMULATION_ERROR
SAFETY_ERROR
API_ERROR
DB_ERROR
CACHE_ERROR
EXTERNAL_DATA_ERROR
UI_ERROR

Every exception:
- structured log
- request/race ID
- safe fallback
- user-facing status
- no secrets

Fallback hierarchy:
real data -> cached data -> synthetic mode
primary model -> previous verified model -> rule baseline
Redis -> in-memory cache
Postgres -> read-only/cached mode where safe
LLM -> deterministic explanation

---

# 35. SECURITY

Never commit:
API keys
database passwords
LLM credentials
tokens

Validate:
MCP inputs
scenario injection permissions
admin operations
file paths
model paths

Rate-limit:
Monte Carlo
training
benchmark
scenario injection

---

# 36. PERFORMANCE

Benchmark:
1 rollout
100
1,000
10,000

Profile:
Python loops
Monte Carlo
WebSocket serialization
DB writes
model inference

Use vectorization/batching/process pools where safe.

Do not parallelize mutable digital-twin state without isolation.

---

# 37. TEST STRATEGY

Unit:
physics
features
models
risk
strategy
state transitions

Integration:
data -> features
features -> model
model -> twin
twin -> strategy
strategy -> API

E2E:
full race
scenario injection
replay
frontend/backend

Property tests:
- fuel never negative
- tyre age monotonic
- lap never decreases
- invalid action never executes
- masked action never executes
- state hash changes only after valid transition

Regression:
fixed seeds and golden outputs with tolerances.

---

# 38. ERROR / BUG TRIAGE

P0:
security breach
data corruption
invalid physics state
unsafe action
non-deterministic corruption
production startup failure

P1:
model inference failure
incorrect strategy state
benchmark failure
data leakage
API contract break
training crash

P2:
UI defect
slow query
minor visualization
optional service failure

Every bug gets:
reproduction
root cause
fix
test
regression proof

---

# 39. CI/CD

Pipeline:
lint
type-check
unit tests
integration tests
frontend build
benchmark smoke
model artifact checksum
Docker build
security scan

PR must not merge if required gates fail.

---

# 40. REQUIRED ACCEPTANCE GATES FOR ~90%

Gate A — runtime:
clean clone boots via Docker.

Gate B — tests:
all tests pass.

Gate C — data:
real-data ingestion works and dataset manifest generated.

Gate D — ML:
held-out metrics exist for tyre/weather/opponent/health where implemented.

Gate E — simulation:
fixed-seed replay is deterministic.

Gate F — strategy:
baselines + DQN + PPO + Hybrid are benchmarked.

Gate G — safety:
invalid actions are impossible to execute.

Gate H — explainability:
every decision has structured evidence.

Gate I — resilience:
fallbacks are tested.

Gate J — reproducibility:
one command regenerates benchmark report.

---

# 41. IMPLEMENTATION ORDER

Phase 0:
audit + baseline

Phase 1:
data pipeline + schemas + feature store

Phase 2:
tyre + weather + opponent + health models

Phase 3:
digital twin validation + Monte Carlo

Phase 4:
DQN remediation + PPO

Phase 5:
risk + hybrid decision engine + emergency brain

Phase 6:
historical replay + AI championship + ablation

Phase 7:
MLOps + observability + API hardening

Phase 8:
frontend + docs + Docker + CI

Never implement all phases in one unreviewed change.

---

# 42. DEFINITION OF DONE

A subsystem is DONE only when:

[ ] code exists
[ ] runtime path uses it
[ ] schema exists
[ ] tests exist
[ ] benchmark exists
[ ] error handling exists
[ ] fallback exists where relevant
[ ] docs exist
[ ] reproducible command exists

The agent must report:
implemented / partial / blocked / intentionally deferred.

Never use "complete" for a mocked or unverified component.

---

# 43. FINAL PROJECT CLAIM

After completion, APEX should be defensibly described as:

"An autonomous race-operations decision-intelligence platform that combines
real F1 telemetry ingestion, a stochastic digital twin, physics-informed
prediction, opponent/vehicle intelligence, counterfactual simulation,
constraint-aware reinforcement learning, risk-aware action selection,
explainability and real-time mission-control tooling."

Do not claim it is an actual F1 team's production system.
It is a research/simulation platform.

