# APEX Strategy Intelligence — Evaluation Benchmark Report

## 1. Executive Summary
This evaluation measures the strategic decision performance across 15 identically seeded, deterministic 52-lap races on the **Silverstone Grand Prix Circuit** with dynamic weather transitions and safety car occurrences.

Three policies were evaluated in head-to-head competition against an AI field with realistic driving styles and competitor pit heuristics:
1. **Random Action Policy** (Sanity baseline)
2. **APEX Rule-Based Expert Engine** (Deterministic strategic heuristic baseline)
3. **APEX DQN Deep Reinforcement Learning Agent** (Learned Q-policy via Gymnasium + Stable-Baselines3)

---

## 2. Benchmark Comparison Matrix

| Policy | Avg Finishing Position | Win Rate (%) | Podium Rate (%) | Avg Gap to P1 (s) | Blown Tyre Laps | Avg Pit Stops |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RANDOM BASELINE** | 7.40 | 13.3% | 26.7% | +87.68s | 19.53 | 0.0 |
| **RULE-BASED ENGINE** | **1.07** | **93.3%** | **100.0%** | **+0.23s** | **0.00** | 3.5 |
| **RETRAINED DQN POLICY** | **2.67** | **66.7%** | **80.0%** | **+14.86s** | **0.13** | 4.3 |

---

## 3. Key Findings & Strategic Insights

### 3.1 RL Diagnosis & Retraining Optimization
- **Diagnosis**: Initial naive DQN training suffered from sample starvation (15,000 timesteps, 8,000 buffer size) and inadequate cliff penalties, causing the agent to stay out on blown tyres (>80% wear) to avoid the pit delta penalty.
- **Optimization Applied**:
  1. **Reward Formulation**: Added quadratic tyre cliff penalties $\left(\frac{\text{wear} - 75}{10}\right)^2$ and catastrophic penalties ($-10.0$) above $85\%$ wear, paired with positive incentives ($+6.0$) for timely box calls and safety car pit window exploitation ($+5.0$).
  2. **Hyperparameter Tuning**: Scaled replay buffer to 50,000, `learning_starts` to 2,000, batch size to 128, and utilized `EvalCallback` saving the optimal checkpoint across 80,000 timesteps.
- **Result**: Blown tyre laps plummeted from **9.87 down to 0.13** (a 98.7% reduction), the average finishing position improved from **4.33 to 2.67**, the podium rate jumped from **60% to 80%**, and the average gap to P1 narrowed from **+79.43s to +14.86s**.

### 3.2 Weather Adaptability
- Both the Rule-Based Engine and DQN Agent successfully react to damp/wet track crossover thresholds, swapping from Slicks to Intermediates/Wets when rain intensity exceeds 0.15–0.55.

### 3.3 Explainability Consensus
- In the live system, the Explainability Layer combines the high-certainty rules with the DQN Q-value margins and TreeSHAP attributions to provide transparent, multi-factor race engineer recommendations.

