# APEX System Resilience & Graceful Degradation Architecture

This document formalizes the multi-tier failure tolerance, fallback mechanisms, and graceful degradation strategies designed into **APEX (Autonomous Predictive & Executive Race Intelligence)**.

---

## 1. Executive Resilience Philosophy

In live motorsport strategy, a pit-wall intelligence platform must never crash, hang, or emit fabricated telemetry when upstream services fail. APEX is built with **zero-hard-dependency resilience**: every external service, database, or heavy neural surrogate is fronted by deterministic fallbacks, local in-memory buffers, and explicit status signals.

```
+-------------------------------------------------------------------------------+
|                             APEX DECISION PIPELINE                            |
+-------------------------------------------------------------------------------+
       |                                |                             |
  [POSTGRES]                         [REDIS]                       [OLLAMA]
       |                                |                             |
  Outage?                           Outage?                       Outage?
       |                                |                             |
       v                                v                             v
 [SQLite File/RAM]              [In-Memory Cache]             [Persona Templates]
  (Zero loss, ACID)              (Thread-safe Dict)            (Deterministic Text)
       |                                |                             |
+-------------------------------------------------------------------------------+
|                       NEURAL & ML GOVERNANCE FALLBACKS                        |
+-------------------------------------------------------------------------------+
       |                                |                             |
  [TREESHAP]                        [FASTF1]                  [SENTENCE-TRANS]
       |                                |                             |
  Drift / Missing?                 Network Error?                 Out of Dist?
       |                                |                             |
       v                                v                             v
 [Exact Analytical]              [Physics Envelope]             [Strict Refusal]
  (Game-Theoretic)                (Polynomial Model)           (Honest Attribution)
```

---

## 2. Graceful Degradation Matrix

| Subsystem / Dependency | Primary Function | Failure Mode Detected | Fallback Behavior & Degradation Path | User / API Impact |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL 16** | Persistent telemetry session storage, lap-by-lap decision audit logs. | Connection refused, timeout, or DNS failure on `DATABASE_URL`. | **SQLite In-Memory / Local DB (`apex_twin.db`)**: Transparently falls back to local SQLite engine with identical SQLAlchemy schema. All ticks and decisions remain persisted locally. | **Zero Downtime**. Telemetry persists; analytics queries run against local SQLite storage. |
| **Redis 7** | High-frequency telemetry broadcast caching, real-time race state sync. | Redis socket error, refused connection on `REDIS_URL`. | **In-Memory Store Dict**: Uses thread-safe Python dictionary cache (`store.py`). Real-time state updates continue through FastAPI WebSockets without dropping frames. | **Zero Downtime**. Multi-process distributed caching degrades to single-process in-memory caching. |
| **Ollama / LLM** | Generative conversational commentary with driver radio personas. | Ollama daemon offline (HTTP 404/500/ConnectionRefused). | **Deterministic Persona Template Engine**: `commentary_generator.py` falls back to deterministic rule-based radio synthesis (APEX Core, Race Engineer, Pit Strategist) grounded in current delta Q and tyre cliffs. | **Zero Downtime**. Radio commentary emits structured deterministic messages instead of LLM completions. |
| **TreeSHAP Surrogates** | Microsecond-latency Shapley feature attributions for DQN policy decisions. | Model file missing or SHA-256 weight hash drift detected. | **Analytical Approximation & Drift Alert**: `TreeSHAPExplainer` falls back to exact analytical game-theoretic marginal contribution calculation and emits a `DRIFT_DETECTED` health warning. | **Zero Downtime**. Explanations remain mathematically valid; model registry logs drift warning. |
| **FastF1 Telemetry** | Real-world historical tyre wear data ingestion and calibration. | FastF1 API rate limit, missing session data, or network failure. | **Calibrated Physics Polynomial Envelope**: `TyreModel` loads calibrated baseline wear equations; logs explicit `"synthetic_fallback"` status without fabricating fictitious data. | **Zero Downtime**. Simulation continues using physics-grounded tyre degradation curves. |
| **HuggingFace Embeddings** (`all-MiniLM-L6-v2`) | Dense vector embeddings for RAG over historical race decisions. | PyTorch tensor allocation error or missing model cache. | **Lexical Match & Strict Refusal**: `race_qa.py` falls back to tokenized keyword similarity and explicitly refuses out-of-distribution queries rather than hallucinating answers. | **Zero Downtime**. Answers return with `"model_used": "deterministic_grounded_fallback"`. |
| **PINN Tyre Residuals** | Neural residual compensation on top of empirical tyre degradation. | Missing PyTorch weights (`pinn_tyre_weights.pt`). | **Empirical Physical Model**: Residual $\Delta \mu$ is set to $0.0$, using the base analytical tyre friction model without neural residual corrections. | **Zero Downtime**. Tyre degradation calculations proceed with pure physical modeling. |

---

## 3. Subsystem Health Diagnostics

APEX provides comprehensive health probing via the `GET /api/health` REST endpoint and the `check_model_health` MCP tool.

### Health Probe Response Structure
```json
{
  "status": "ok",
  "service": "APEX Race Intelligence API",
  "timestamp_utc": "2026-08-19T14:15:00.000000Z",
  "subsystems": {
    "simulator": {
      "status": "HEALTHY",
      "active_track": "silverstone",
      "total_cars": 20
    },
    "models": {
      "status": "HEALTHY",
      "dqn_policy_loaded": true,
      "ppo_policy_loaded": true,
      "tyre_model_calibrated": true,
      "pinn_weights_loaded": true,
      "shap_surrogate_in_sync": true
    },
    "database": {
      "status": "HEALTHY",
      "backend": "sqlite",
      "connected": true
    },
    "redis": {
      "status": "DEGRADED_IN_MEMORY",
      "connected": false,
      "fallback": "local_memory_dict"
    },
    "embeddings": {
      "status": "HEALTHY",
      "model": "all-MiniLM-L6-v2",
      "loaded": true
    }
  }
}
```

---

## 4. Rate Limiting & Compute Defense

To prevent thread exhaustion from heavy compute operations (Monte Carlo rollouts, championship tournament sweeps, and counterfactual tree forks), APEX enforces IP-based rate limiting via `slowapi`:

- **Monte Carlo Simulations** (`/api/strategy/monte-carlo`): Bounded to max 5,000 rollouts, rate limited to **15 requests/minute**.
- **Championship Tournaments** (`/api/championship/run`): Bounded to max 100 races, rate limited to **5 requests/minute**.
- **Counterfactual Timeline Forks** (`/api/strategy/fork-counterfactual`): Rate limited to **20 requests/minute**.

When limits are exceeded, the API returns HTTP 429 (`Too Many Requests`) with a standard `Retry-After` header and structured JSON error payload.
