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
| **RANDOM** | 7.40 | 13.3% | 26.7% | +87.68s | 19.53 | 0.0 |
| **RULE BASED** | **1.07** | **93.3%** | **100.0%** | **+0.23s** | **0.00** | 3.5 |
| **DQN AGENT** | 4.33 | 53.3% | 60.0% | +79.43s | 9.87 | 2.2 |

---

## 3. Key Findings & Strategic Insights

### 3.1 Degradation Cliff Avoidance
- The **Rule-Based Engine** achieved **0.00 blown tyre laps**, reliably pitting before the 75-80% wear cliff threshold, yielding a 93.3% win rate.
- The **DQN Agent** learned to manage stint lengths and conserve tyres, achieving an average finishing position of **4.33** (substantially outperforming the random floor of 7.40).

### 3.2 Weather Adaptability
- Both the Rule-Based Engine and DQN Agent successfully react to damp/wet track crossover thresholds, swapping from Slicks to Intermediates/Wets when rain intensity exceeds 0.15–0.55.

### 3.3 Explainability Consensus
- In the live system, the Explainability Layer combines the high-certainty rules with the DQN Q-value margins to provide transparent, multi-factor race engineer recommendations.
