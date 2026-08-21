# APEX REST, WebSocket & Streaming API Reference

The APEX backend exposes an enterprise suite of REST endpoints, distributed message broker streaming topics, asynchronous background job queues, and high-frequency WebSocket channels for real-time race digital twin operations.

---

## 1. Authentication & Role-Based Access Control (RBAC)

| Method | Endpoint | Min Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | None | Authenticates user credentials and returns signed JWT access & refresh tokens. |
| `POST` | `/api/auth/refresh` | None | Refreshes an expired access token using a valid refresh token. |
| `GET` | `/api/auth/me` | VIEWER | Returns current user profile and permission list. |
| `GET` | `/api/auth/demo-tokens` | None | Returns pre-generated tokens for all 4 RBAC roles (`VIEWER`, `ANALYST`, `STRATEGIST`, `ADMIN`). |

---

## 2. Asynchronous Compute Job Queue (BullMQ / Redis)

| Method | Endpoint | Min Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/jobs/enqueue` | ANALYST | Enqueues heavy compute jobs (`STRATEGY_MONTE_CARLO`, `HISTORICAL_REPLAY`, `ML_RETRAIN_BATCH`, `ALERT_DISPATCH`) with idempotency deduplication. |
| `GET` | `/api/jobs/status/{job_id}` | VIEWER | Polls real-time job execution status, progress %, and computed results. |
| `GET` | `/api/jobs/list` | VIEWER | Lists recent background compute jobs with type/status filtering. |

---

## 3. Kafka Distributed Streaming Topics

| Topic Name | Partition Key | Schema Payload | Description |
| :--- | :--- | :--- | :--- |
| `f1.telemetry.raw` | `session_id:car_id` | `TelemetryEvent` | 60Hz per-vehicle telemetry (speed, throttle, brake, RPM, gear, tyre temps, fuel). |
| `f1.weather.events` | `session_id` | `WeatherEvent` | Track wetness index, rain intensity, drying rate, and 10-min rain forecasts. |
| `f1.tyre.degradation` | `session_id:car_id` | `TyreDegradationEvent` | Physical wear percentage, PINN residuals, and thermal cliff alerts. |
| `f1.race.control` | `session_id` | `RaceControlEvent` | Official flag states (`GREEN`, `YELLOW`, `VSC`, `SAFETY_CAR`, `RED_FLAG`). |
| `f1.strategy.decisions`| `session_id:car_id` | `StrategyDecisionEvent` | Recommendations from the Hybrid Decision Aggregator & RL policies. |
| `f1.dlq.failed_events` | `dlq_id` | `DeadLetterEvent` | Poison pills and schema validation rejections for inspection and replay. |

---

## 4. Digital Twin & Race Simulation Endpoints

| Method | Endpoint | Min Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/race/init` | ANALYST | Initializes a new race digital twin session on a specified track. |
| `GET` | `/api/race/state/{race_id}` | VIEWER | Returns the full validated `RaceState` snapshot. |
| `POST` | `/api/race/step` | ANALYST | Advances the digital twin simulation by 1 lap or tick. |
| `POST` | `/api/race/action` | STRATEGIST | Applies an executive strategy directive (e.g. `PIT_SOFT`, `PUSH`). |
| `POST` | `/api/race/scenario` | STRATEGIST | Injects live hazards (Safety Car, VSC, Torrential Rain, Puncture). |
| `POST` | `/api/race/clear-hazards` | STRATEGIST | Clears active synthetic hazards. |
| `POST` | `/api/race/time-travel/{tick}` | STRATEGIST | Reverts simulator state to an exact historical tick. |
| `GET` | `/api/race/export/{race_id}` | VIEWER | Exports structured markdown debrief and decision audit log. |
| `WS` | `/ws` or `/ws/{session_id}` | Optional JWT | Bi-directional WebSocket stream for 60Hz telemetry, actions, and audio commentary. |

---

## 5. Predictive Intelligence & Strategy Endpoints

| Method | Endpoint | Min Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/intelligence/tyre` | VIEWER | FastF1 calibration metadata, RUL estimates, and degradation curves. |
| `GET` | `/api/intelligence/weather` | VIEWER | Track wetness index, drying rates, and 5-lap rain probabilities. |
| `GET` | `/api/intelligence/opponents`| VIEWER | Rival pit probability forecasts, undercut threats, and tactical intent. |
| `GET` | `/api/intelligence/drivers` | VIEWER | Driver behavioral profiles, fatigue levels, and mistake risks. |
| `GET` | `/api/intelligence/health` | VIEWER | Powertrain multi-sensor telemetry and Isolation Forest anomaly status. |
| `GET` | `/api/strategy/recommendation/{race_id}` | VIEWER | Unified Hybrid Decision Aggregator recommendations and alternatives. |
| `POST` | `/api/strategy/monte-carlo` | ANALYST | Vectorized forward Monte Carlo rollouts across candidate tactical actions. |
| `POST` | `/api/strategy/counterfactual` | ANALYST | Parallel counterfactual analysis evaluating alternative decision paths. |
| `POST` | `/api/strategy/explain` | VIEWER | TreeSHAP feature attributions and multi-action differential rationale. |

---

## 6. Observability & System Metrics

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/metrics` | Standard Prometheus metric exposition (Kafka counters, lag, queue depths, latencies). |
| `GET` | `/api/health` | Deep health check (PostgreSQL, Redis, Kafka, ML Model Registry). |
| `GET` | `/api/observability/metrics` | System telemetry, active session counts, memory cache diagnostics. |
