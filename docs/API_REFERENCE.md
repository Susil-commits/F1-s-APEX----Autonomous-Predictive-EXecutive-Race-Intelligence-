# APEX REST & WebSocket API Reference

The APEX backend exposes a suite of REST endpoints and high-frequency WebSocket streams for real-time race digital twin operations, predictive ML inference, and strategic analysis.

---

## 1. Digital Twin & Race Simulation Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/race/init` | Initializes a new race digital twin session on a specified track. |
| `GET` | `/api/race/state` | Returns the full validated `RaceState` snapshot. |
| `POST` | `/api/race/step` | Advances the digital twin simulation by 1 lap or tick. |
| `POST` | `/api/race/action` | Applies an executive strategy directive (e.g. `PIT_SOFT`, `PUSH`). |
| `POST` | `/api/race/scenario` | Injects live hazards (Safety Car, VSC, Torrential Rain, Puncture). |
| `POST` | `/api/race/clear-hazards` | Clears active synthetic hazards. |
| `POST` | `/api/race/time-travel/{tick}` | Reverts simulator state to an exact historical tick. |
| `GET` | `/api/race/export/{race_id}` | Exports structured markdown debrief and decision audit log. |
| `WS` | `/ws/race` | Bi-directional WebSocket stream for sub-second telemetry and controls. |

---

## 2. Predictive Intelligence Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/intelligence/tyre` | Returns FastF1 calibration metadata, RUL estimates, and degradation curves. |
| `GET` | `/api/intelligence/weather` | Returns track wetness index, drying rates, and 5-lap rain probabilities. |
| `GET` | `/api/intelligence/opponents` | Returns rival pit probability forecasts, undercut threats, and tactical intent. |
| `GET` | `/api/intelligence/drivers` | Returns driver behavioral profiles, fatigue levels, and mistake risks. |
| `GET` | `/api/intelligence/health` | Returns powertrain multi-sensor telemetry and Isolation Forest anomaly status. |
| `GET` | `/api/strategy/hybrid-decision` | Returns unified Hybrid Decision Aggregator recommendations and alternatives. |
| `POST` | `/api/strategy/counterfactual` | Executes high-performance forward rollouts across strategic candidates. |

---

## 3. Replay, Tournament & Observability Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/replays` | Lists catalogue of pre-configured historical Grand Prix replays. |
| `GET` | `/api/replays/{race_key}` | Replays historical GP events and audits APEX recommendations vs actual pit walls. |
| `GET` | `/api/championship/run` | Runs a multi-agent AI tournament championship simulation (5 to 100 races). |
| `GET` | `/api/observability/metrics` | Returns system telemetry, AI model readiness, and memory cache diagnostics. |
| `POST` | `/api/race/ask` | Natural language RAG query engine answering questions about session history. |
