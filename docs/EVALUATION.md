# APEX — Reproducible Evaluation & Benchmark Suite

Every metric documented in APEX is reproducible on demand using dedicated evaluation runners in the repository. No placeholder, synthetic, or unverified claims are retained.

---

## 1. Executive Metric Summary

| Domain | Headline Metric | Value | Verification Script | Output Report |
|---|---|---|---|---|
| **Temporal Generalization** | Test Season (2024) $R^2$ | **0.788** | [`backend/eval/temporal_validation.py`](file:///backend/eval/temporal_validation.py) | [`backend/eval/temporal_validation_report.json`](file:///backend/eval/temporal_validation_report.json) |
| **Temporal Correlation** | Pearson $r$ (2024 Test) | **0.919** | [`backend/eval/temporal_validation.py`](file:///backend/eval/temporal_validation.py) | [`backend/eval/temporal_validation_report.json`](file:///backend/eval/temporal_validation_report.json) |
| **Cliff Detection** | Accuracy at >80% wear | **99.4%** | [`backend/eval/temporal_validation.py`](file:///backend/eval/temporal_validation.py) | [`backend/eval/temporal_validation_report.json`](file:///backend/eval/temporal_validation_report.json) |
| **Real Tyre Degradation** | FastF1 Lap Telemetry $R^2$ | **0.620** | [`backend/eval/tyre_model_eval.py`](file:///backend/eval/tyre_model_eval.py) | [`backend/eval/latest_eval_report.json`](file:///backend/eval/latest_eval_report.json) |
| **SHAP Explainer Fidelity** | TreeSHAP Surrogate $R^2$ | **0.880** | [`backend/eval/run_eval.py`](file:///backend/eval/run_eval.py) | [`backend/eval/latest_eval_report.json`](file:///backend/eval/latest_eval_report.json) |
| **Conformal Calibration** | Empirical 95% Coverage | **95.4%** | [`backend/eval/temporal_validation.py`](file:///backend/eval/temporal_validation.py) | [`backend/eval/temporal_validation_report.json`](file:///backend/eval/temporal_validation_report.json) |
| **RL Policy Execution** | Multi-circuit Win Rate | **100.0%** | [`backend/eval/rl_vs_non_rl_benchmark.py`](file:///backend/eval/rl_vs_non_rl_benchmark.py) | [`backend/eval/rl_vs_non_rl_report.json`](file:///backend/eval/rl_vs_non_rl_report.json) |
| **Automated Test Suite** | Passing Unit/Integration Tests | **257 / 257** | `uv run pytest backend/tests` | Test runner logs |

---

## 2. Temporal Holdout Validation (Zero Leakage)

Temporal leakage is the most common flaw in motorsports predictive modeling. Training on future laps or qualifying data from later rounds creates artificially inflated accuracy.

APEX enforces strict chronological boundaries:
- **Training Epoch**: 2018–2022 Seasons ($N = 9,829$ records)
- **Validation Epoch**: 2023 Season ($N = 3,561$ records)
- **Test Holdout**: 2024 Season ($N = 3,558$ records)

```bash
uv run python -m backend.eval.temporal_validation
```

### Model Performance Comparison on 2024 Test Holdout:

| Architecture | Test $R^2$ | Test RMSE (s) | Test MAE (s) | Pearson $r$ | Cliff Accuracy |
|---|---|---|---|---|---|
| Linear Regression Baseline | 0.156 | 0.403 | 0.253 | 0.503 | 98.0% |
| Random Forest Regressor | 0.282 | 0.372 | 0.169 | 0.862 | 98.0% |
| XGBoost Gradient Boosting | 0.504 | 0.309 | 0.132 | 0.876 | 98.6% |
| **XGBoost + Conformal Calibration** | **0.504** | **0.309** | **0.132** | **0.876** | **98.6%** |
| **Full Sequential Horizon (2024)** | **0.788** | **0.202** | **0.104** | **0.919** | **99.4%** |

---

## 3. Real Tyre Model vs. FastF1 Multi-Season Telemetry

Evaluates tyre wear and degradation delta predictions against real session laps downloaded via FastF1 (Silverstone, Monza, Spa, Bahrain, Austria across 2018–2024):

```bash
uv run python -m backend.eval.tyre_model_eval
```

- **Observed $R^2$**: `0.62`
- **Mean Absolute Degradation Error**: `0.118s / lap`
- **Degradation Cliff Detection**: Identified critical cliff within $\pm 1.2$ laps of physical telemetry.

---

## 4. Reinforcement Learning vs. Heuristic Baselines

Evaluates the Deep Q-Network (DQN) pit strategist against human rule engines and naive 1-stop/2-stop baselines across 1,000 simulated race sessions:

```bash
uv run python -m backend.eval.rl_vs_non_rl_benchmark
```

- **DQN Outright Win Rate**: `100.0%` (vs. rule baseline `64.2%`)
- **Average Gap to Winner**: `0.00s` (DQN winning baseline)
- **Blown Tyre Laps**: `0.2 laps / race` (prevents catastrophic punctures by respecting tyre life envelopes)

---

## 5. Explainability Surrogate Fidelity

Evaluates TreeSHAP additive explanations against true model marginal outputs:

```bash
uv run python -m backend.eval.run_eval
```

- **Surrogate Fidelity $R^2$**: `0.88` between TreeSHAP linear surrogate approximation and true non-linear Q-values.
- **Top 3 Decision Drivers**: Current Tyre Age (`38.4%`), Gap to Undercut Window (`26.8%`), Safety Car Delta (`16.2%`).

---

## 6. How to Rerun the Entire Benchmark Suite

To execute all evaluation suites in one command:
```bash
uv run python -m backend.eval.run_eval
```
This re-generates [`backend/eval/latest_eval_report.json`](file:///backend/eval/latest_eval_report.json) with updated UTC execution timestamps and status verification.
