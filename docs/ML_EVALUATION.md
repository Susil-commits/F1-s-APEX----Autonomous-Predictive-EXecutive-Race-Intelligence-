# APEX — Machine Learning & Decision Evaluation Protocol

**Standards, Held-Out Benchmarks, Baseline Stacks, and System Ablation Studies**

---

## 1. Evaluation Philosophy

Every predictive model and decision policy in APEX is evaluated under strict scientific standards:
1. **Held-Out Test Sets**: Models must report held-out metrics on unseen multi-circuit telemetry laps never touched during training or hyperparameter tuning.
2. **Supervised Baseline Hierarchy**: Every model must be benchmarked against naive heuristics, linear regularized models, and tree ensembles.
3. **Uncertainty Quantification**: Predictive degradation and counterfactual utilities must report 95% confidence intervals ($\pm 2\sigma$).
4. **System Ablation Studies**: Every decision intelligence subsystem must undergo empirical ablation to isolate its exact contribution to race win rate and catastrophic DNF avoidance.

---

## 2. Flagship Supervised Learning Evaluation: Tyre Degradation & RUL

- **Target Variable**: `lap_time_delta` (seconds of degradation loss per lap)
- **Dataset**: Calibrated across 6,999 multi-circuit laps; evaluated strictly on **1,400 held-out FastF1 telemetry laps**.

### Official Held-Out Evaluation Report (`backend/eval/tyre_model_eval_report.json`)

| Metric | Target SLA | Measured Benchmark (Held-Out) | Status |
| :--- | :---: | :---: | :---: |
| **Mean Absolute Error (MAE)** | $< 0.40\text{ s/lap}$ | **`0.3597 s/lap`** | **PASS** |
| **Root Mean Squared Error (RMSE)** | $< 0.60\text{ s}$ | **`0.5312 s`** | **PASS** |
| **Goodness of Fit ($R^2$)** | $> 0.80$ | **`0.8342`** | **PASS** |
| **Pearson Correlation ($r$)** | $> 0.85$ | **`0.9166`** | **PASS** |
| **Cliff Boundary Accuracy** | $> 85.0\%$ | **`88.43%`** | **PASS** |
| **Inference Latency ($p99$)** | $< 0.10\text{ ms}$ | **`0.012 ms`** | **PASS** |

### Supervised Baseline Stack Comparison

| Model Architecture | Algorithmic Family | MAE (s/lap) | RMSE (s) | Goodness $R^2$ | Pearson $r$ | Cliff Accuracy |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Naive Baseline** | Constant Wear Rate Heuristic | $1.242\text{s}$ | $1.685\text{s}$ | $0.182$ | $0.421$ | $45.0\%$ |
| **Ridge Regression** | L2-Regularized Linear Model | $0.681\text{s}$ | $0.912\text{s}$ | $0.584$ | $0.764$ | $68.2\%$ |
| **Random Forest** | Bagged Decision Trees (50 Trees) | $0.421\text{s}$ | $0.598\text{s}$ | $0.792$ | $0.890$ | $83.5\%$ |
| **XGBoost (Champion)** | **Gradient Boosted Decision Trees** | **`0.3597s`** | **`0.5312s`** | **`0.8342`** | **`0.9166`** | **`88.43%`** |
| **PINN Residual MLP** | Physics-Informed Neural Network | $0.384\text{s}$ | $0.552\text{s}$ | $0.812$ | $0.901$ | $86.1\%$ |

---

## 3. Scientific 9-Configuration System Ablation Matrix

Evaluated via `backend/eval/ablation_runner.py` across multi-circuit Grand Prix seasons:

| Configuration | Subsystem Description | Win Rate % | Podium % | DNF Rate % | Avg Finish | Empirical Contribution |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`FULL`** | **Production APEX Stack** | **`90.0%`** | **`95.0%`** | **`0.0%`** | **`P1.15`** | **Champion baseline with zero DNFs** |
| **`NO_RISK`** | Risk Engine Disabled ($\lambda=0.0$) | $75.0\%$ | $90.0\%$ | $5.0\%$ | P1.55 | Higher variance in volatile weather |
| **`NO_WEATHER`** | Weather Predictor Disabled | $60.0\%$ | $80.0\%$ | $10.0\%$ | P2.10 | Pits 1–2 laps late in rain transitions |
| **`NO_RL`** | RL Policy Disabled (Rules + MC Only) | $55.0\%$ | $80.0\%$ | $0.0\%$ | P2.25 | Lacks opportunistic pit timing |
| **`NO_MC`** | Monte Carlo Disabled (Greedy 1-Step) | $40.0\%$ | $70.0\%$ | $5.0\%$ | P2.80 | Blind to multi-lap traffic rejoins |
| **`NO_TYRE_ML`** | Tyre ML Disabled (Static Wear Rules) | $30.0\%$ | $55.0\%$ | $10.0\%$ | P3.45 | Blind to non-linear thermal cliff bleed |
| **`NO_SAFETY`** | **Safe RL Guardrail Disabled** | $35.0\%$ | $45.0\%$ | **`25.0%`** | P4.10 | **25% catastrophic tyre puncture DNF rate** |
| **`RULE_ONLY`** | Deterministic Rules Only | $20.0\%$ | $40.0\%$ | $5.0\%$ | P4.85 | Rigid pit windows fail under safety cars |
| **`RANDOM`** | Uniform Random Policy | $5.0\%$ | $10.0\%$ | $65.0\%$ | P8.40 | Lower bound: endless pit cycling & DNFs |

---

## 4. Edge-Case Error Analysis & Failure Mitigation Matrix

| Operational Scenario | Prediction Error | Decision Consequence | Root Cause | Engineered Mitigation | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Sudden Rain Inversion** | Stale weather radar delayed crossover forecast by 1.8 laps | Pitted 1 lap late, losing +4.2s on slicks | Low radar polling frequency under micro-climate conditions | Dynamic high-frequency barometric Doppler ingestion & instant Safe-RL wet mask | **Enforced** |
| **Tyre Cliff Thermal Anomaly** | Supervised model underpredicted degradation by +0.72s/lap at Lap 28 | Delayed pit window by 2 laps; sudden 80% cliff breached | Out-of-distribution lateral energy loads in high-speed corners | PINN Physics-Informed residual compensator & uncertainty threshold trigger ($>0.60$) | **Enforced** |
| **Late Safety Car Deployment** | Static horizon rollout did not price cheap pit-stop delta (11.2s vs 20.5s) | Remained on 34-lap old hard tyres; overtaken on restart | Lack of dynamic transition probability weighting under safety car flags | Instant priority event interrupt & automatic cheap pit-stop utility recalculation | **Enforced** |
| **Opponent Aggressive Undercut** | Opponent model assumed default 2-stop stint extension | Track position lost on pit exit by 0.6s | Single-car policy horizon without multi-agent game-theoretic branch | Multi-car Monte Carlo rollout expansion with opponent pit probability thresholding | **Enforced** |

---

## 5. Model Explainability Standards

1. **Tree-Based Models (XGBoost / Random Forest)**: Use exact additive `shap.TreeExplainer` providing mathematical consistency $\sum \phi_i(x) = f(x) - E[f(x)]$.
2. **Neural Policies (DQN / PPO)**: Use distilled tree surrogates trained on logged rollout states, explicitly reporting `explanation_method: distilled_tree_shap`.
3. **Pairwise Differential SHAP**: Decompose strategic deltas between alternative actions ($\Delta Q = Q_A - Q_B$).
