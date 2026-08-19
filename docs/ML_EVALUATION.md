# APEX — ML Evaluation Protocol
## Spec Section 25 — Model Evaluation Standards

**Document Version:** 1.0
**Last Updated:** 2026-08-19

---

## 1. Evaluation Philosophy

Every ML model in APEX must report held-out metrics on a test set that was
never used during training or hyperparameter selection.

RULE: No model may be promoted to production without a documented test-set
evaluation with a minimum of 3 metrics. Evaluation code must be reproducible.

---

## 2. Tyre Degradation Model

**File:** backend/app/intelligence/tyre_model.py
**Target:** lap_time_delta (seconds of degradation per lap)

### Required Metrics (held-out test set)

| Metric | Target |
|--------|--------|
| MAE | < 0.4 s/lap |
| RMSE | < 0.6 s/lap |
| Pearson R | > 0.85 |
| Cliff prediction accuracy | > 85% |
| Calibration ECE (XGBoost) | < 0.05 |

### Model Tiers

| Tier | Algorithm | Condition |
|------|-----------|-----------|
| 1 | XGBoost | Real FastF1 data available |
| 2 | RandomForest | XGBoost unavailable |
| 3 | LinearRegression | No training data |

### Running the Evaluation

.venv/Scripts/python.exe backend/eval/tyre_model_eval.py

---

## 3. Weather Model

| Metric | Target |
|--------|--------|
| Brier Score | < 0.15 |
| Rain onset recall | > 0.80 |
| Rain onset precision | > 0.75 |

---

## 4. Opponent Model

| Metric | Target |
|--------|--------|
| Brier Score | < 0.18 |
| AUC-ROC | > 0.75 |
| Calibration ECE | < 0.08 |

---

## 5. SHAP Explainability Honesty

When explaining a tree model: use TreeExplainer.
When explaining a neural net / PPO policy:
1. Use KernelExplainer (not TreeExplainer)
2. Include disclaimer: SHAP computed via surrogate approximation
3. Report explanation_method: surrogate_shap in API response

---

## 6. RL Agent Targets

| Metric | DQN Target | PPO Target |
|--------|-----------|-----------|
| 100-race avg finish | < 4.5 | < 4.5 |
| Win rate | > 15% | > 15% |
| Catastrophic pit rate | < 5% | < 5% |

---

## 7. Promotion Pipeline

Models promoted via backend/app/intelligence/model_registry.py
Required: mae, rmse, r2 all above gate thresholds
Stored with: training data manifest hash, eval metrics, timestamp

