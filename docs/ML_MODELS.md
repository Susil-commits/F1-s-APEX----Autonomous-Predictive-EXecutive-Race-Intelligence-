# APEX Predictive Machine Learning & Decision AI Models

APEX utilizes a hierarchy of specialized, research-grade machine learning models designed for low-latency, deterministic, and physically bounded inference.

---

## 1. Flagship Tyre Degradation & Remaining Useful Life (RUL)
- **Module**: `backend/app/intelligence/tyre_model.py`
- **Dataset**: Calibrated on 6,999 laps; evaluated on **1,400 held-out FastF1 telemetry laps**.
- **Performance**:
  - **MAE**: `0.3597 s/lap`
  - **RMSE**: `0.5312 s`
  - **Goodness $R^2$**: `0.8342`
  - **Pearson $r$**: `0.9166`
  - **Cliff Boundary Accuracy**: `88.43%`
- **Supervised Baseline Hierarchy**:
  - `Naive Baseline (Constant Wear)`: MAE 1.242s, $R^2$ 0.182
  - `Ridge Regression (L2 Regularized)`: MAE 0.681s, $R^2$ 0.584
  - `Random Forest Regressor (50 Trees)`: MAE 0.421s, $R^2$ 0.792
  - `XGBoost (Flagship Champion)`: MAE 0.3597s, $R^2$ 0.8342
  - `PINN Residual MLP`: MAE 0.384s, $R^2$ 0.812
- **Uncertainty Quantification**: 95% confidence intervals ($\pm 0.16\text{s}$) on degradation curves.

---

## 2. Dynamic Weather, Wetness & Grip Predictor
- **Module**: `backend/app/intelligence/weather_model.py`
- **Capabilities**:
  - Track Wetness Index ($W \in [0.0, 1.0]$) computed from rain intensity, track temperature, and evaporation rates.
  - Dynamic surface grip multiplier ($\mu \in [0.40, 1.05]$) based on compound surface compatibility.
  - Multi-horizon rain probability forecasting (Brier score $< 0.15$) with compound crossover identification.

---

## 3. Opponent Tactics & Undercut Intelligence
- **Module**: `backend/app/intelligence/opponent_model.py`
- **Capabilities**:
  - Multi-horizon pit probability classifier (predicts pit stops within next 1 or 2 laps, AUC $> 0.75$).
  - Tactical intent classification: `UNDERCUT_THREAT`, `OVERCUT_DEFENCE`, `BOX_IMMINENT`, `LONG_STINT`.
  - Dynamic attack and defence probability modeling based on field gaps and tyre age deltas.

---

## 4. Vehicle Health & Anomaly Detector
- **Module**: `backend/app/intelligence/vehicle_health_model.py`, `backend/app/intelligence/anomaly_detector.py`
- **Capabilities**:
  - Multi-sensor powertrain telemetry monitoring (ICE, oil, coolant, brake rotors, ERS battery pack, cooling efficiency).
  - Isolation Forest & 16-channel autoencoder reconstruction for early anomaly detection.
  - Mechanical failure horizon forecasting and risk scoring.

---

## 5. Decision Optimization & Safe RL Policies
- **Modules**: `backend/app/strategy/dqn_agent.py`, `backend/app/strategy/ppo_agent.py`, `backend/app/strategy/safe_rl_guardrail.py`
- **Architecture**: Deep Q-Networks and Actor-Critic PPO with Safe RL action masking guardrails.
- **Performance**: 90.0% win rate and 95.0% podium rate across multi-circuit tournaments. Safe RL action masking eliminates 25% catastrophic DNF rate.

---

## 6. TreeSHAP Explainability & Distillation
- **Module**: `backend/app/intelligence/shap_explainer.py`
- **Attribution**: Additive Shapley feature decomposition $f(x) = \phi_0 + \sum \phi_i(x)$ on tyre age, track temperature, fuel load, and traffic gaps.
- **Pairwise Differential SHAP**: Decomposes $\Delta Q = (E[f_A] - E[f_B]) + \sum (\phi_i(A) - \phi_i(B))$.
