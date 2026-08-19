# APEX — Physics Assumptions & Parameter Catalogue
## Required by Spec §13

**Document Version:** 1.0
**Last Updated:** 2026-08-19
**Source Files Audited:**
- ackend/app/simulator/car.py
- ackend/app/simulator/engine.py
- ackend/app/simulator/models.py
- ackend/app/intelligence/tyre_model.py

---

## Classification Key

| Class | Meaning |
|-------|---------|
| **S** | Sourced from verifiable public F1 data or engineering literature |
| **C** | Calibrated from FastF1 empirical telemetry |
| **A** | Engineering assumption — plausible but unverified |
| **P** | Synthetic/scenario parameter — for simulation realism only |

---

## 1. Tyre Compound Parameters

**Source file:** ackend/app/simulator/car.py — COMPOUND_SPECS

### 1.1 SOFT Tyre

| Parameter | Value | Unit | Class | Source / Rationale |
|-----------|-------|------|-------|-------------------|
| pace_delta_s | -0.85 | s/lap | A | Approximate peak qualifying advantage of soft over medium; varies 0.4–1.2s by circuit |
| base_wear_rate_pct | 3.40 | %/lap | A | Representative of high-degradation circuits (Bahrain, Spain). Real range: 2.5–5.0%/lap |
| cliff_threshold_pct | 75.0 | % | A | Cliff onset point. Real-world soft cliff typically 20–28 laps on high-wear circuits |
| cliff_penalty_s_per_pct | 0.08 | s/% | A | Lap time loss per additional % wear past cliff |
| ideal_track_temp_c | 35.0 | °C | S | Pirelli published optimal operating window: 30–40°C for soft |

### 1.2 MEDIUM Tyre

| Parameter | Value | Unit | Class | Source / Rationale |
|-----------|-------|------|-------|-------------------|
| pace_delta_s | 0.00 | s/lap | A | Reference baseline compound |
| base_wear_rate_pct | 2.10 | %/lap | A | Mid-range degradation rate |
| cliff_threshold_pct | 80.0 | % | A | Mediums last ~35–40 laps on standard circuits |
| cliff_penalty_s_per_pct | 0.06 | s/% | A | Lower cliff severity than soft |
| ideal_track_temp_c | 30.0 | °C | S | Pirelli: 25–35°C for medium |

### 1.3 HARD Tyre

| Parameter | Value | Unit | Class | Source / Rationale |
|-----------|-------|------|-------|-------------------|
| pace_delta_s | 0.75 | s/lap | A | Approximate hard vs medium delta; real range 0.4–1.0s |
| base_wear_rate_pct | 1.35 | %/lap | A | Low degradation; may last 45–55 laps |
| cliff_threshold_pct | 85.0 | % | A | Hards rarely reach cliff in single stint |
| cliff_penalty_s_per_pct | 0.05 | s/% | A | Gentlest cliff of dry compounds |
| ideal_track_temp_c | 28.0 | °C | S | Pirelli: 20–32°C for hard |

### 1.4 INTERMEDIATE Tyre

| Parameter | Value | Unit | Class | Source / Rationale |
|-----------|-------|------|-------|-------------------|
| pace_delta_s | 3.50 | s/lap | A | Rough penalty on dry track; real penalty is large and track-dependent |
| base_wear_rate_pct | 2.40 | %/lap | A | Intermediates wear fast on drying tracks |
| cliff_threshold_pct | 75.0 | % | A | |
| ideal_track_temp_c | 22.0 | °C | A | Lower temp optimum for wet compounds |

### 1.5 WET Tyre

| Parameter | Value | Unit | Class | Source / Rationale |
|-----------|-------|------|-------|-------------------|
| pace_delta_s | 7.00 | s/lap | A | Heavy penalty on dry track; wets destroy themselves on dry asphalt |
| base_wear_rate_pct | 2.20 | %/lap | A | Wets wear faster on damp or drying tracks |

---

## 2. Driving Mode Parameters

**Source file:** ackend/app/simulator/car.py — MODE_SPECS

| Mode | pace_delta_s | wear_multiplier | fuel_burn_multiplier | Class | Note |
|------|-------------|-----------------|---------------------|-------|------|
| PUSH | -0.75 | 1.45 | 1.20 | A | Push gains ~0.75s, +45% wear, +20% fuel burn |
| NORMAL | 0.00 | 1.00 | 1.00 | A | Baseline reference |
| CONSERVE | +0.65 | 0.65 | 0.80 | A | Save ~0.65s slower, -35% wear, -20% fuel |

---

## 3. Lap Time Computation

**Source file:** ackend/app/simulator/car.py — CarPhysics.calculate_lap_time()

| Parameter | Value | Unit | Class | Source |
|-----------|-------|------|-------|--------|
| Fuel weight lap time cost | 0.033 | s/kg | S | Published aerodynamic sensitivity; FIA data suggests 0.03–0.04 s/kg |
| Linear wear degradation | wear_pct / 100 * 1.8 | s | A | Max 1.8s penalty at 100% wear |
| Cliff penalty multiplier | 1.5x cliff_penalty_s_per_pct | s/% | A | 50% uplift on cliff penalty vs linear |
| Traffic dirty air penalty | 0.35 | s/lap | A | When gap_to_car_ahead < 1.2s; literature estimates 0.2–0.5s |
| Driver variance noise | normal(0, 0.12) | s | P | ±1σ ~0.12s per lap driver variance |
| Safety Car delta time | 1.40x base_lap_time | — | A | Approximate SC pace |
| VSC delta time | 1.25x base_lap_time | — | A | Approximate VSC pace |

### Weather Penalties

| Condition | Compound | Penalty | Unit | Class | Note |
|-----------|----------|---------|------|-------|------|
| Dry (rain<0.10) | INTERMEDIATE | +3.50 | s | A | Inters on dry |
| Dry (rain<0.10) | WET | +7.00 | s | A | Wets on dry |
| Damp (0.10-0.50) | SOFT/MED/HARD | 8.0 * (rain/0.50) | s | A | Slicks on damp; up to +8s |
| Damp (0.10-0.50) | INTERMEDIATE | -1.00 | s | A | Optimal compound |
| Damp (0.10-0.50) | WET | +2.50 | s | A | Too wet for damp |
| Wet (rain>0.50) | SOFT/MED/HARD | +22.00 | s | A | Slicks aquaplaning |
| Wet (rain>0.50) | INTERMEDIATE | +4.50 | s | A | Inters struggling |
| Wet (rain>0.50) | WET | -0.50 | s | A | Optimal compound bonus |

---

## 4. Tyre Wear Dynamics

**Source file:** ackend/app/simulator/car.py — CarPhysics.calculate_tyre_wear()

| Parameter | Value | Unit | Class | Source |
|-----------|-------|------|-------|--------|
| Temperature excess wear factor | 0.01 per °C (max 25°C) | multiplier | A | Linear temperature effect up to 25°C outside ideal |
| Slick in heavy rain wear multiplier | 1.30 | — | A | Slick compounds wear faster in rain |
| Rain tyre on dry wear multiplier | 3.00 | — | A | Full wets destroy themselves on dry track |
| Micro-variance noise | normal(1.0, 0.02) | multiplier | P | ±2% lap-to-lap wear variation |
| Minimum wear delta floor | 0.10 | % | P | Ensures wear never stalls |

---

## 5. Circuit Degradation Severity

**Source file:** ackend/app/intelligence/tyre_model.py — CIRCUIT_DEGRADATION_SEVERITY

| Circuit | Multiplier | Class | Rationale |
|---------|-----------|-------|-----------|
| bahrain | 1.35 | C | Highly abrasive asphalt, high rear thermal stress |
| spain / barcelona | 1.25 | C | High-energy lateral loads (T3, T9) |
| silverstone | 1.15 | C | High-speed lateral loads (Maggotts/Becketts) |
| suzuka | 1.20 | C | High-lateral S-curves |
| spa | 1.05 | C | High-speed compression, elevation changes |
| austria | 1.00 | C | Medium wear, short lap (reference baseline) |
| interlagos | 0.95 | C | Medium-low degradation |
| zandvoort | 1.10 | A | Banked corners, high lateral load |
| monza | 0.75 | C | Low-downforce longitudinal traction |
| monaco | 0.55 | C | Smooth street asphalt, low energy |

---

## 6. Fuel Load

**Source file:** ackend/app/simulator/engine.py — RaceSimulator.__init__()

| Parameter | Value | Unit | Class | Source |
|-----------|-------|------|-------|--------|
| Starting fuel load | 100.0 | kg | A | Real F1: ~95–110 kg depending on circuit |
| Fuel burn per lap | total_laps / 100.0 kg/lap | kg/lap | A | Evenly spread burn approximation |
| Fuel burn PUSH multiplier | 1.20 | — | A | +20% burn in push mode |
| Fuel burn CONSERVE multiplier | 0.80 | — | A | -20% burn in conserve mode |
| Minimum fuel floor | 0.5 | kg | P | Prevents negative fuel |

---

## 7. Safety Car / VSC Pit Advantage

**Source file:** ackend/app/simulator/models.py — TrackConfig

| Parameter | Value | Unit | Class | Source |
|-----------|-------|------|-------|--------|
| VSC pit advantage | 9.5 | s | A | Approximate time advantage of pitting under VSC vs green |
| SC pit advantage | 12.0 | s | A | Approximate time advantage under full SC |
| Pit lane delta (Silverstone) | 21.5 | s | S | Publicly available pit lane time for Silverstone (~21–22s) |

---

## 8. Starting Grid Spacing

**Source file:** ackend/app/simulator/engine.py — RaceSimulator.__init__()

| Parameter | Value | Unit | Class | Source |
|-----------|-------|------|-------|--------|
| Grid interval spacing | 0.4 | s | P | Synthetic; real F1 starts are from standing start — gap builds naturally |

---

## 9. Valid Ranges & Test Coverage

| Parameter | Valid Range | Test |
|-----------|-------------|------|
| tyre_wear_pct | 0.0 – 100.0 | test_simulator.py (property: wear monotonic) |
| fuel_kg | 0.5 – 110.0 | test_simulator.py (property: fuel never negative) |
| lap_time_s | 50.0 – 200.0 (race), min floor 50s | test_simulator.py |
| cliff_probability | 0.0 – 1.0 | test_pinn_tyre.py |
| rain_intensity | 0.0 – 1.0 | test_tyre_weather_ml.py |

---

## 10. Required Improvements

The following parameters need calibration from real FastF1 data (tracked in AUDIT-004/005):

1. ase_wear_rate_pct — calibrate by compound per circuit from FastF1 lap deltas
2. cliff_threshold_pct — calibrate from when lap time acceleration exceeds 2x baseline degradation rate
3. cliff_penalty_s_per_pct — calibrate from FastF1 post-cliff lap time loss regression
4. pace_delta_s — per-compound — calibrate from qualifying vs race stint data
5. uel_weight_cost (0.033 s/kg) — validate against published aerodynamic sensitivity

After real-data calibration, the calibrated_tyre_model.json file will be populated and used
in preference to these engineering assumptions (see TyreModel.load_calibrated_model()).

---

> **IMPORTANT:** No parameter in this file should ever be silently changed in production.
> Any update requires: (1) updated entry in this document, (2) updated unit test, (3) code review.
