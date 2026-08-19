# APEX — Baseline Audit Report
## Phase 0 — Repository Forensic Audit

**Audit Date:** 2026-08-19
**Repository:** https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-

---

## 1. Environment

| Property | Value |
|----------|-------|
| Python (venv) | CPython 3.12 (uv-managed) |
| Python (system) | 3.13 (incompatible — numpy not at system level) |
| Package manager | uv |
| OS | Windows 11 x86_64 |
| Virtual env | .venv at project root |

**CRITICAL:** Always run with .venv\Scripts\python.exe. System Python 3.13 lacks numpy.

---

## 2. Dependency Versions (pyproject.toml)

| Package | Pinned |
|---------|--------|
| fastapi | >=0.115.0 |
| pydantic | >=2.8.0 |
| numpy | >=1.26.0,<2.0.0 |
| torch | >=2.2.0 (CPU) |
| stable-baselines3 | >=2.3.0 |
| gymnasium | >=0.29.1 |
| shap | >=0.45.0 |
| fastf1 | >=3.3.0 |
| xgboost | >=2.1.0 |
| redis | >=5.0.0 |
| prometheus-client | >=0.20.0 |

---

## 3. Test Results — Baseline (2026-08-19)

**Command:** .venv\Scripts\python.exe -m pytest backend/tests/ --tb=short -q

`
149 passed, 7 warnings in 77.61s (0:01:17)
`

Pass rate: 149/149 = **100%**

7 warnings = aiosqlite thread teardown on Windows. Harmless.

### Test Coverage (33 files)

All 33 test files PASS. Coverage spans: API, simulator, gym env, DQN, PPO, Monte Carlo,
SHAP, Safe RL, Redis, MCP, PINN tyre, counterfactual, historical replay, championship,
data pipeline, feature builder, model registry, Prometheus metrics, rate limiting.

---

## 4. Component Status

### Backend Components

| Component | File | Status | Critical Gap |
|-----------|------|--------|-------------|
| FastAPI app | app/main.py | OPERATIONAL | — |
| REST routes | api/routes.py (29 KB) | PARTIAL | Missing /experiments, /replay, /scenarios |
| Pydantic schemas | simulator/models.py | PARTIAL | Missing schema_version, race_id, source, timestamp_s |
| Race simulator | simulator/engine.py (25 KB) | PARTIAL | Missing snapshot()/restore()/state_hash() |
| Car physics | simulator/car.py | PARTIAL | Hardcoded coefficients |
| Tyre model | intelligence/tyre_model.py | PARTIAL | No real-data training, no held-out metrics |
| PINN residual | intelligence/pinn_tyre_residual.py | PARTIAL | Unverified vs physics baseline |
| Weather model | intelligence/weather_model.py | PARTIAL | No calibration/uncertainty |
| Opponent model | intelligence/opponent_model.py | PARTIAL | No Brier score/evaluation |
| Vehicle health | intelligence/vehicle_health_model.py | PARTIAL | — |
| Risk engine | intelligence/risk_engine.py (94 lines) | PARTIAL | No configurable lambda |
| SHAP explainer | intelligence/shap_explainer.py (20 KB) | PARTIAL | Surrogate honesty not enforced |
| DQN agent | strategy/dqn_agent.py | PARTIAL | apex_dqn.zip artifact may not exist |
| PPO agent | strategy/ppo_agent.py (60 lines) | STUB | Heuristic fallback only |
| Gym env | strategy/gym_env.py | IMPLEMENTED | 8 actions, 28 obs, reward shaping |
| Monte Carlo | strategy/monte_carlo.py (16 KB) | PARTIAL | No 10k mode, incomplete output spec |
| Hybrid engine | strategy/hybrid_decision_engine.py | PARTIAL | Not deterministic for identical seeds |
| Safe RL mask | strategy/safe_rl_guardrail.py | PARTIAL | Missing mechanical risk/race-control checks |
| Emergency brain | intelligence/emergency_brain.py | PARTIAL | Not all 13 scenarios have test fixtures |
| Model registry | intelligence/model_registry.py | PARTIAL | No promotion pipeline, no drift tracking |
| Championship | eval/championship.py | PARTIAL | Only 5 archetypes (spec requires 8) |
| FastF1 loader | training/fetch_fastf1_data.py | PARTIAL | No manifest, no race-based splits |
| Dataset manifest | DOES NOT EXIST | MISSING | Required for Gate C |
| Data quality | DOES NOT EXIST | MISSING | Required for Gate C |
| Ablation runner | DOES NOT EXIST | MISSING | Required for Gate F |
| Benchmark runner | DOES NOT EXIST | MISSING | Required for Gate J |

---

## 5. Model Artifacts

| Artifact | Status |
|----------|--------|
| backend/models/apex_dqn.zip | UNKNOWN — likely missing |
| backend/models/ppo/apex_ppo.zip | LIKELY MISSING |
| backend/models/tyre/tyre_rf.joblib | AUTO-GENERATED on import |
| backend/models/calibrated_tyre_model.json | UNKNOWN |

---

## 6. Missing Environment Variables (.env.example)

| Variable | Required | Purpose |
|----------|----------|---------|
| DATABASE_URL | Yes (for persistence) | PostgreSQL connection |
| REDIS_URL | Yes (for pub/sub) | Redis connection |
| OPENAI_API_KEY | Optional | LLM commentary |
| OLLAMA_BASE_URL | Optional | Local LLM endpoint |

---

## 7. Known Gaps (AUDIT IDs)

| ID | Severity | Description |
|----|----------|-------------|
| AUDIT-001 | P0 | docs/PHYSICS_ASSUMPTIONS.md missing |
| AUDIT-002 | P0 | No dataset manifest module |
| AUDIT-003 | P0 | No data quality / leakage detection |
| AUDIT-004 | P0 | Tyre model: no real-data training or held-out metrics |
| AUDIT-005 | P0 | PINN vs ML vs physics comparison not quantified |
| AUDIT-006 | P0 | DQN model artifact likely missing |
| AUDIT-007 | P0 | PPO is 60-line heuristic stub |
| AUDIT-008 | P0 | SHAP: no surrogate-vs-neural-net honesty disclaimer |
| AUDIT-009 | P1 | Pydantic models missing schema_version, race_id, source, timestamp_s |
| AUDIT-010 | P1 | Risk engine: no configurable lambda |
| AUDIT-011 | P1 | Safe RL: missing mechanical risk limit and race-control constraints |
| AUDIT-012 | P1 | Hybrid engine non-deterministic |
| AUDIT-013 | P1 | No ablation runner |
| AUDIT-014 | P1 | Championship only 5/8 required archetypes |
| AUDIT-015 | P1 | No one-command benchmark runner |
| AUDIT-016 | P1 | Missing: DATA_PIPELINE.md, ML_EVALUATION.md, BENCHMARK.md |
| AUDIT-017 | P1 | No conftest.py with shared test fixtures |
| AUDIT-018 | P1 | No race-based train/val/test split |
| AUDIT-019 | P2 | aiosqlite thread teardown warnings (7 occurrences) |

---

## 8. Acceptance Gate Status

| Gate | Condition | Status |
|------|-----------|--------|
| A — Runtime | Docker boot | NOT VERIFIED |
| B — Tests | All tests pass | PASS (149/149) |
| C — Data | Real ingestion + manifest | FAIL |
| D — ML | Held-out metrics | FAIL |
| E — Simulation | Deterministic replay | PARTIAL |
| F — Strategy | DQN + PPO + Hybrid benchmarked | FAIL |
| G — Safety | Invalid actions impossible | PARTIAL |
| H — Explainability | Structured evidence | PARTIAL |
| I — Resilience | Fallbacks tested | PARTIAL |
| J — Reproducibility | One-command benchmark | FAIL |

---

*Re-run this audit after each phase completion.*
