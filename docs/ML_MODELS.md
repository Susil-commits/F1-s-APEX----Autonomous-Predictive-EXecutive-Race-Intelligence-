# APEX Predictive Machine Learning & Decision AI Models

APEX utilizes a hierarchy of specialized, research-grade machine learning models designed for low-latency, deterministic, and physically bounded inference.

---

## 1. Tyre Degradation & Remaining Useful Life (RUL)
- **Module**: `backend/app/intelligence/tyre_model.py`
- **Models**:
  - `BaselineDegradationModel`: Non-linear exponential physics model calibrated to circuit severity indices.
  - `TyreMLSuite`: Random Forest regressor trained on fuel-corrected telemetry laps. Generates 90% confidence intervals via ensemble variance.
  - `CliffProbabilityEstimator`: Logistic sigmoid model tracking wear and thermal stress.
- **Key Metrics**: $R^2 \ge 0.82$, Mean Absolute Error $< 0.18$s/lap.

---

## 2. Dynamic Weather, Wetness & Grip Predictor
- **Module**: `backend/app/intelligence/weather_model.py`
- **Capabilities**:
  - Track Wetness Index ($W \in [0.0, 1.0]$) computed from rain intensity, track temperature, and evaporation rates.
  - Dynamic surface grip multiplier ($\mu \in [0.40, 1.05]$) based on compound surface compatibility.
  - 5-minute and 10-minute rain probability forecasting with compound crossover identification.

---

## 3. Opponent Tactics & Undercut Intelligence
- **Module**: `backend/app/intelligence/opponent_model.py`
- **Capabilities**:
  - Multi-horizon pit probability classifier (predicts pit stops within next 1 or 2 laps).
  - Tactical intent classification: `UNDERCUT_THREAT`, `OVERCUT_DEFENCE`, `BOX_IMMINENT`, `LONG_STINT`.
  - Dynamic attack and defence probability modeling based on field gaps and tyre age deltas.

---

## 4. Driver Behavioral Analytics & Pressure Modeling
- **Module**: `backend/app/intelligence/driver_model.py`
- **Capabilities**:
  - Driver profile registry (Pace bias, tyre management skill, aggression, consistency, defence strength).
  - Dynamic fatigue curves and pressure-induced mistake probability calculations ($P(\text{mistake}) \in [0.01, 0.20]$).

---

## 5. Vehicle Health & Anomaly Detector
- **Module**: `backend/app/intelligence/vehicle_health_model.py`
- **Capabilities**:
  - Multi-sensor powertrain telemetry monitoring (ICE, oil, coolant, brake rotors, ERS battery pack, cooling efficiency).
  - Isolation Forest anomaly detector for early detection of uncharacteristic thermal or pressure divergence.
  - Mechanical failure horizon forecasting and risk scoring.

---

## 6. Deep Q-Network (DQN) & Proximal Policy Optimization (PPO) Policies
- **Modules**: `backend/app/strategy/dqn_agent.py`, `backend/app/strategy/ppo_agent.py`
- **Architecture**: Multi-Layer Perceptrons with dense intermediate reward shaping and Safe RL action masking guardrails.
- **Actions**: Discrete strategic actions mapping to tire compounds, engine modes, and ERS states.
