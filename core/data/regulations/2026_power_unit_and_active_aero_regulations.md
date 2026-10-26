# FIA 2026 Formula 1 Technical Regulations: Power Unit & Active Aerodynamics

**Document Reference:** FIA-F1-2026-TECH-REG-v2.1  
**Classification:** Sporting & Technical Governance  
**Relevant Levers:** `active_aero_mode`, `manual_override_mode`, `mgu_k_deployment`, `battery_soc`, `sustainable_fuel_flow`

---

## 1. Active Aerodynamics & Dual-State Wings (Article 3.4)

### 1.1 Z-Mode (Cornering / High Downforce Mode)
* **Default State:** Z-Mode is automatically engaged whenever the vehicle enters braking zones and cornering segments.
* **Wing Configuration:** Front and rear movable aerodynamic wing flaps operate at maximum angle of attack.
* **Downforce Delta:** Generates ~30% higher downforce than baseline straight-line trim to ensure high-speed apex stability.

### 1.2 X-Mode (Straight-Line / Low Drag Mode)
* **Engagement Zone:** Activated automatically or driver-commanded on designated straight-line acceleration zones when steering angle is within $\pm 2.5^\circ$.
* **Wing Flap Articulation:** The active rear wing upper flap and front wing active element articulates to reduce parasitic drag by approximately 55%.
* **Speed Gain:** Increases terminal straight-line velocity by 18-24 km/h without requiring DRS slipstream proximity.

---

## 2. 50/50 Hybrid Power Unit & 350kW MGU-K (Article 5.1 - 5.8)

### 2.1 Internal Combustion Engine (ICE)
* **Configuration:** 1.6-litre V6 90° Turbocharged ICE operating at up to 15,000 RPM.
* **Power Output:** Calibrated to approximately 400 kW (~535 hp).
* **Fuel Standard:** 100% Advanced Sustainable Drop-In Fuel (`sustainable_fuel_flow` limited to 70 kg/h energy flow cap).

### 2.2 Electrical Energy Recovery & 350kW MGU-K
* **MGU-K Output:** Increased from legacy 120kW to **350 kW (~470 hp)**, delivering a near 50/50 power split between electric and thermal propulsion.
* **MGU-H Abolishment:** The Motor Generator Unit - Heat (MGU-H) is eliminated to reduce development costs and road relevance barriers.
* **Energy Recovery:** Braking energy harvesting increased up to 8.5 MJ per lap into the Energy Store (ES).

---

## 3. Manual Override Mode (MOM) & Overtaking Boost (Article 5.12)

### 3.1 Eligibility & Activation Trigger
* **Proximity Rule:** Available to a chasing car within **1.000 second** of a car ahead at the intermediate timing detection point.
* **Speed Profile:** Operates dynamically above 290 km/h where standard electrical energy deployment begins tapering off.

### 3.2 Power Curve & Tactical Advantage
* **Leading Car Taper:** At 300 km/h, the leading car's MGU-K deployment tapers down towards zero at 345 km/h.
* **Trailing Car Override:** The chasing car maintains full 350 kW electrical boost through 337 km/h, delivering an extra 0.5s to 1.2s overtaking delta on long straights.
* **Pit Wall Strategy:** Strategists must reserve at least 18% battery State of Charge (`battery_soc`) entering the final sector to exploit MOM opportunities.
