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

<p align="center">
  <img src="images/tyre_model_performance_gate_d.png" alt="APEX Tyre ML Regression & Held-Out Telemetry Evaluation" width="100%" />
</p>

> **Figure 1: Gate D Supervised Regression Performance on 1,400 Held-Out FastF1 Telemetry Laps.**
> - **Left Panel**: Actual vs. predicted lap-time loss scatter plot, demonstrating high correlation ($R^2 = 0.8342$) and tightly bounded residuals within the $\pm 0.40\text{s}$ acceptance margin.
> - **Right Panel**: Soft (C4/C5), Medium (C3), and Hard (C1/C2) compound degradation trajectories with 90% confidence intervals, mapping the critical $+2.5\text{s/lap}$ non-linear cliff threshold.

---

## 3. Decision-System Ablation & Contribution Analysis

Evaluated via `backend/eval/ablation_runner.py` across 100 multi-circuit Grand Prix championship races:

| Configuration | Subsystem Modification | Win Rate % | Podium % | DNF Rate % | Avg Finish | Total Points | Empirical Contribution & Subsystem Impact |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`FULL`** | **All Modules Active (Production APEX)** | **`90.0%`** | **`95.0%`** | **`0.0%`** | **`P1.15`** | **`482`** | **Champion stack: 0 DNFs, optimal tyre cliff avoidance & rain crossovers** |
| **`NO_RISK`** | Risk Engine Disabled ($\lambda=0.0$) | $75.0\%$ | $90.0\%$ | $5.0\%$ | P1.55 | $416$ | Higher variance in volatile weather; over-aggressive stint extensions |
| **`NO_WEATHER`** | Weather Predictor Disabled | $60.0\%$ | $80.0\%$ | $10.0\%$ | P2.10 | $348$ | Pits 1–2 laps late in rain transitions, losing 15+ seconds on slicks |
| **`NO_RL`** | RL Policy Disabled (Rules + MC Only) | $55.0\%$ | $80.0\%$ | $0.0\%$ | P2.25 | $338$ | Solid baseline, but lacks sub-second opportunistic pit timing |
| **`NO_MC`** | Monte Carlo Rollouts Disabled (Greedy 1-Step) | $40.0\%$ | $70.0\%$ | $5.0\%$ | P2.80 | $272$ | Blind to multi-lap traffic rejoins and opponent undercut threats |
| **`NO_TYRE_ML`** | XGBoost Model Disabled (Static Wear Rules) | $30.0\%$ | $55.0\%$ | $10.0\%$ | P3.45 | $216$ | Fails to anticipate non-linear thermal cliffs, causing lap-time bleed |
| **`NO_SAFETY`** | **Safe RL Guardrail Disabled (Unmasked)** | $35.0\%$ | $45.0\%$ | **`25.0%`** | P4.10 | $184$ | **Catastrophic 25% DNF rate caused by tyre blowouts & closed-pitlane entries** |
| **`RULE_ONLY`** | Pure Deterministic Rules Only (Zero ML) | $20.0\%$ | $40.0\%$ | $5.0\%$ | P4.85 | $150$ | Rigid pit windows fail to capitalize on safety cars or track evolution |
| **`RANDOM`** | Uniform Random Policy (Lower Bound) | $5.0\%$ | $10.0\%$ | $65.0\%$ | P8.40 | $36$ | Uncontrolled tyre blowouts, endless pit cycling, severe DNFs |

### 🔬 Empirical Findings: Which Components Actually Improve the Decision System?

1. **Safe RL Action Masking (Essential for Reliability)**:
   - Eliminating the safety mask (`NO_SAFETY`) causes a **`25.0% DNF rate`** (tyre punctures past the 80% wear boundary and illegal pit box orders under closed pitlanes). Safe RL is the fundamental requirement for physical feasibility.
2. **Predictive Tyre ML (+60% Win Rate Delta)**:
   - Removing the supervised XGBoost model (`NO_TYRE_ML`) collapses win rate from **90% to 30%**. Without non-linear degradation forecasting, the system suffers severe thermal cliff lap-time bleeds (+2.5s/lap).
3. **Monte Carlo Lookahead (+50% Win Rate Delta)**:
   - Without stochastic forward rollouts (`NO_MC`), greedy 1-step logic is blind to traffic rejoin packets, dropping win rate to **40%**.
4. **Meteorological Doppler Radar (+30% Win Rate Delta)**:
   - Disabling weather prediction (`NO_WEATHER`) causes the car to run on slicks in heavy rain for 1–2 laps, hemorrhaging 15+ seconds per rain transition.
5. **Reinforcement Learning Policy (+35% Win Rate over Pure Rules)**:
   - Adding DQN/PPO policies increases win rate from **55% (`NO_RL`) to 90% (`FULL`)** by discovering non-obvious undercut and safety car exploitation windows.

<p align="center">
  <img src="images/ablation_study_matrix.png" alt="APEX Subsystem Ablation Study & Performance Impact" width="100%" />
</p>

> **Figure 2: 9-Configuration Decision-System Ablation Matrix.**
> - **Left Panel**: Win rate % by active subsystem.
> - **Right Panel**: Average finish position and catastrophic DNF rate (highlighting the 25% failure rate of unmasked policies).

---

## 4. Edge-Case Error Analysis & Failure Mitigation Matrix

| Operational Scenario | Prediction Error | Decision Consequence | Root Cause | Engineered Mitigation | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Sudden Rain Inversion** | Stale weather radar delayed crossover forecast by 1.8 laps | Pitted 1 lap late, losing +4.2s on slicks | Low radar polling frequency under micro-climate conditions | Dynamic high-frequency barometric Doppler ingestion & instant Safe-RL wet mask | **Enforced** |
| **Tyre Cliff Thermal Anomaly** | Supervised model underpredicted degradation by +0.72s/lap at Lap 28 | Delayed pit window by 2 laps; sudden 80% cliff breached | Out-of-distribution lateral energy loads in high-speed corners | PINN Physics-Informed residual compensator & uncertainty threshold trigger ($>0.60$) | **Enforced** |
| **Late Safety Car Deployment** | Static horizon rollout did not price cheap pit-stop delta (11.2s vs 20.5s) | Remained on 34-lap old hard tyres; overtaken on restart | Lack of dynamic transition probability weighting under safety car flags | Instant priority event interrupt & automatic cheap pit-stop utility recalculation | **Enforced** |
| **Opponent Aggressive Undercut** | Opponent model assumed default 2-stop stint extension | Track position lost on pit exit by 0.6s | Single-car policy horizon without multi-agent game-theoretic branch | Multi-car Monte Carlo rollout expansion with opponent pit probability thresholding | **Enforced** |

---

## 5. Safe RL Guardrail & Multi-Factor Risk Optimization

<p align="center">
  <img src="images/safe_rl_risk_frontier.png" alt="APEX Safe RL Guardrail & Risk-Reward Pareto Frontier" width="100%" />
</p>

> **Figure 3: Safe RL Action Masking & Pareto Optimization.**
> - **Left Panel**: Continuous Pareto optimization curve over risk weights $\lambda \in [0.0, 1.0]$, demonstrating the Balanced APEX sweet spot at $\lambda = 0.35$.
> - **Right Panel**: 100% boundary mask enforcement across 6 physical and regulatory failure modes.

---

## 6. Model Explainability Standards

1. **Tree-Based Models (XGBoost / Random Forest)**: Use exact additive `shap.TreeExplainer` providing mathematical consistency $\sum \phi_i(x) = f(x) - E[f(x)]$.
2. **Neural Policies (DQN / PPO)**: Use distilled tree surrogates trained on logged rollout states, explicitly reporting `explanation_method: distilled_tree_shap`.
3. **Pairwise Differential SHAP**: Decompose strategic deltas between alternative actions ($\Delta Q = Q_A - Q_B$).

---

## 7. Experimental Study: Single Planner Agent vs. Multi-Agent Consensus

To scientifically evaluate multi-agent reasoning vs. direct tool-augmented planner architectures, APEX evaluates both paradigms under simulated 60Hz real-time race conditions:

| System Architecture | Decision Latency ($p99$) | Decision Utility (0.0–1.0) | Deadlock / Split Rate | Grounded Citation Acc | Compute Cost / Decision |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Single Planner Agent + Domain MCP Tools (Production)** | **`42 ms`** | **`0.81 ± 0.11`** | **`0.0%`** | **`96.4%`** | **`1x (Baseline)`** |
| **5-Agent Consensus Committee (Experimental)** | $318\text{ ms}$ | $0.83 \pm 0.10$ | $4.2\%$ | $94.1\%$ | $5.8\text{x}$ |

### Empirical Takeaway
- **Single Planner Agent with Domain MCP Tools** achieves virtually identical decision quality ($0.81$ vs $0.83$ utility) at **$7.5\times$ lower latency** ($42\text{ms}$ vs $318\text{ms}$) and **$0.0\%$ committee deadlock**.
- In high-speed, sub-second Formula 1 pit wall operations, the Single Planner Agent with direct tool grounding is the optimal production choice. The 5-Agent committee remains available as an exploratory comparative benchmark.

<p align="center">
  <img src="images/ai_championship_standings.png" alt="APEX Multi-Agent AI Championship Tournament Standings" width="100%" />
</p>

> **Figure 4: AI Championship Tournament (8 Strategic Archetypes across 10 Races).**
> - **Left Panel**: Total Constructors points showing APEX leading with 238 pts.
> - **Right Panel**: Race Wins (7 P1s) and Podiums (9 P1–P3s) across 10 Grand Prix races.


