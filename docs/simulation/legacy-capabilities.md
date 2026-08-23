# Historical Simulation & Experimental Features Archive

> [!NOTE]
> This document archives auxiliary simulation modules, telemetry rigs, and exploratory physics sandboxes developed during early research phases of the APEX project. 
> 
> The core production APEX system is positioned strictly as an **AI/ML Decision Intelligence and Counterfactual Experimentation Platform** centered on supervised telemetry regression, Monte Carlo counterfactual branching, Safe Reinforcement Learning action masking, TreeSHAP explainability, and Model Context Protocol (MCP) planner agents.

---

## 1. Auxiliary Engineering Sandboxes

The following auxiliary modules were engineered during early exploratory phases to model localized physical dynamics and sensory feedback loops:

| Module / System | Domain | Description & Experimental Purpose |
| :--- | :--- | :--- |
| **CFD Lab & Aerodynamic Rig** | Fluid Dynamics | Exploratory boundary-layer and vortex decay approximations under dirty-air wake profiles. |
| **Driver Thermal System** | Human Factors | Core body temperature and cognitive fatigue modeling during high-heat Grand Prix stints. |
| **Brake Pyrometry Rig** | Thermal Dynamics | Carbon-carbon brake disc surface temperature curves and thermal fading thresholds under sustained deceleration. |
| **Gearbox & Drivetrain Lab** | Mechanical Wear | Dog-ring wear modeling and gear-ratio torque curve simulation. |
| **Oil Spectroscopy Analyzer** | Tribology | Micro-metallic particle density accumulation curves across extended engine mileage. |
| **Composite Autoclave Rig** | Materials | Structural stress-strain curves under sustained high-G vertical and lateral load cycles. |
| **Crash Sled Dynamicist** | Impact Physics | Deceleration impulse calculations under barrier impact vectors. |
| **Tyre Blanket Thermal Rig** | Pre-Stint Physics | Initial thermodynamic heat-soak curves for tyre compound carcass activation. |
| **WebXR / Cockpit Visualizer** | Spatial UI | Experimental 3D driver cockpit perspective rendered via Three.js / WebXR protocols. |
| **Radio Audio DSP Synthesizer** | Web Audio | Audio oscillator synthesis simulating trackside pit wall telemetry alerts. |
| **FIA Stewards Tribunal Simulator** | Regulations | Rulebook decision-tree evaluator for track limits and overtaking infringements. |
| **Trophy & Championship Cabinet** | Gamification | Visual trophy showcase for automated championship simulation tournaments. |

---

## 2. Integration with Core Decision Intelligence

While these auxiliary sandboxes provided rich synthetic dynamics for sandbox testing, APEX’s production decision intelligence relies directly on:
1. **Real-World Telemetry Data** via `FastF1` and Jolpica API.
2. **Supervised Machine Learning** (XGBoost, LightGBM, Random Forest, Ridge, PINN Residuals) evaluated on held-out test splits.
3. **Counterfactual Simulation Engine** running stochastic forward Monte Carlo rollouts.
4. **Safe RL Guardrails** providing provable action masking over vehicle physical boundaries.
5. **TreeSHAP Explainability** delivering local additive feature attributions for human-in-the-loop pit wall strategists.
6. **Model Context Protocol (MCP) Server** exposing the entire intelligence loop to autonomous LLM reasoning agents.
