"""Pirelli Physics-Informed Tyre Degradation & Thermal Cliff Engine.

Models non-linear pace degradation per lap across dry compounds (C1-C5)
and wet compounds (Intermediate, Full Wet) factoring:
- Carcass & tread thermal wear sensitivity
- Track surface macro-roughness & circuit lateral energy demand
- Non-linear performance cliff (exponential pace drop-off when wear > 75%)
- Undercut / Overcut pit delta crossover calculation
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TyreCompoundSpec(BaseModel):
    compound_name: str
    compound_code: str  # C1, C2, C3, C4, C5, INT, WET
    color: str
    base_delta_s: float = Field(description="Initial laptime delta vs C3 reference (seconds)")
    linear_deg_per_lap: float = Field(description="Alpha: linear pace loss per lap (s/lap)")
    quadratic_deg_factor: float = Field(description="Beta: thermal acceleration degradation factor")
    optimal_track_temp_c: float = Field(default=30.0, description="Optimum track surface temperature")
    temp_sensitivity_factor: float = Field(default=0.012, description="Degradation penalty per deg C deviation")
    cliff_lap: int = Field(description="Nominal lap where tire cliff (exponential drop-off) begins")
    cliff_penalty_s_per_lap: float = Field(default=1.6, description="Additional pace loss per lap after cliff")


PIRELLI_COMPOUNDS: Dict[str, TyreCompoundSpec] = {
    "C1": TyreCompoundSpec(
        compound_name="Pirelli C1 (Hardest)",
        compound_code="C1",
        color="#FFFFFF",
        base_delta_s=0.90,
        linear_deg_per_lap=0.045,
        quadratic_deg_factor=0.0008,
        optimal_track_temp_c=38.0,
        temp_sensitivity_factor=0.008,
        cliff_lap=38,
        cliff_penalty_s_per_lap=1.2,
    ),
    "C2": TyreCompoundSpec(
        compound_name="Pirelli C2 (Hard)",
        compound_code="C2",
        color="#FFFFFF",
        base_delta_s=0.55,
        linear_deg_per_lap=0.065,
        quadratic_deg_factor=0.0011,
        optimal_track_temp_c=34.0,
        temp_sensitivity_factor=0.010,
        cliff_lap=32,
        cliff_penalty_s_per_lap=1.4,
    ),
    "C3": TyreCompoundSpec(
        compound_name="Pirelli C3 (Medium Baseline)",
        compound_code="C3",
        color="#FFD700",
        base_delta_s=0.00,
        linear_deg_per_lap=0.095,
        quadratic_deg_factor=0.0015,
        optimal_track_temp_c=30.0,
        temp_sensitivity_factor=0.012,
        cliff_lap=25,
        cliff_penalty_s_per_lap=1.6,
    ),
    "C4": TyreCompoundSpec(
        compound_name="Pirelli C4 (Soft)",
        compound_code="C4",
        color="#FF2D55",
        base_delta_s=-0.60,
        linear_deg_per_lap=0.145,
        quadratic_deg_factor=0.0022,
        optimal_track_temp_c=26.0,
        temp_sensitivity_factor=0.016,
        cliff_lap=18,
        cliff_penalty_s_per_lap=1.9,
    ),
    "C5": TyreCompoundSpec(
        compound_name="Pirelli C5 (Hyper-Soft)",
        compound_code="C5",
        color="#FF2D55",
        base_delta_s=-1.05,
        linear_deg_per_lap=0.210,
        quadratic_deg_factor=0.0035,
        optimal_track_temp_c=24.0,
        temp_sensitivity_factor=0.020,
        cliff_lap=12,
        cliff_penalty_s_per_lap=2.3,
    ),
    "INT": TyreCompoundSpec(
        compound_name="Pirelli Intermediate (Green)",
        compound_code="INT",
        color="#34C759",
        base_delta_s=3.50,
        linear_deg_per_lap=0.080,
        quadratic_deg_factor=0.0012,
        optimal_track_temp_c=20.0,
        temp_sensitivity_factor=0.025,
        cliff_lap=28,
        cliff_penalty_s_per_lap=1.8,
    ),
    "WET": TyreCompoundSpec(
        compound_name="Pirelli Full Wet (Blue)",
        compound_code="WET",
        color="#007AFF",
        base_delta_s=7.00,
        linear_deg_per_lap=0.060,
        quadratic_deg_factor=0.0010,
        optimal_track_temp_c=18.0,
        temp_sensitivity_factor=0.015,
        cliff_lap=35,
        cliff_penalty_s_per_lap=1.5,
    ),
}


class TyreDegradationModel:
    """Simulates realistic stint wear and lap time degradation curves."""

    def __init__(self, compounds: Optional[Dict[str, TyreCompoundSpec]] = None):
        self.compounds = compounds or PIRELLI_COMPOUNDS

    def calculate_lap_degradation(
        self,
        compound_code: str,
        tyre_age_laps: int,
        track_temp_c: float = 30.0,
        circuit_downforce_index: float = 0.70,
        dirty_air_proximity: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculates pace delta for a tyre at a given age.

        Args:
            compound_code: Tyre code (C1, C2, C3, C4, C5, INT, WET).
            tyre_age_laps: Current tyre age in laps (1-based).
            track_temp_c: Current track temperature in Celsius.
            circuit_downforce_index: Circuit downforce demand (0.0=Monza, 1.0=Monaco).
            dirty_air_proximity: Proximity to leading car (0.0=clean air, 1.0=within 0.8s).

        Returns:
            Dict containing pace delta, wear percentage, cliff warning, and thermal status.
        """
        spec = self.compounds.get(compound_code.upper().strip(), self.compounds["C3"])
        age = max(1, tyre_age_laps)

        # Baseline linear + quadratic thermal degradation
        linear_loss = spec.linear_deg_per_lap * age
        quadratic_loss = spec.quadratic_deg_factor * (age ** 2)

        # Temperature deviation impact
        temp_delta = max(0.0, abs(track_temp_c - spec.optimal_track_temp_c))
        thermal_penalty = temp_delta * spec.temp_sensitivity_factor

        # Circuit abrasion & dirty air aero sliding penalty
        aero_sliding_penalty = (circuit_downforce_index * 0.05) + (dirty_air_proximity * 0.12)

        nominal_delta = (
            spec.base_delta_s
            + linear_loss
            + quadratic_loss
            + thermal_penalty
            + aero_sliding_penalty
        )

        # Non-linear cliff onset calculation
        is_past_cliff = age >= spec.cliff_lap
        cliff_laps_exceeded = max(0, age - spec.cliff_lap)
        cliff_penalty = cliff_laps_exceeded * spec.cliff_penalty_s_per_lap

        total_pace_delta = round(nominal_delta + cliff_penalty, 3)

        # Estimated tire wear percentage (100% = unusable/puncture risk)
        wear_pct = min(100.0, round((age / (spec.cliff_lap * 1.25)) * 100.0, 1))

        # Cliff proximity warning
        laps_to_cliff = spec.cliff_lap - age
        warning = None
        if is_past_cliff:
            warning = "CRITICAL: Tyre is operating past performance cliff! Heavy pace bleed."
        elif 0 <= laps_to_cliff <= 3:
            warning = f"WARNING: Tyre cliff imminent in {laps_to_cliff} laps. Box window active."

        return {
            "compound": spec.compound_code,
            "compound_name": spec.compound_name,
            "tyre_age_laps": age,
            "pace_delta_seconds": total_pace_delta,
            "wear_pct": wear_pct,
            "is_past_cliff": is_past_cliff,
            "laps_to_cliff": laps_to_cliff,
            "warning": warning,
            "track_temp_c": track_temp_c,
        }

    def simulate_stint_curve(
        self,
        compound_code: str,
        total_laps: int = 40,
        track_temp_c: float = 30.0,
        circuit_downforce_index: float = 0.70,
    ) -> List[Dict[str, Any]]:
        """Generates a complete degradation trajectory across a multi-lap stint."""
        curve: List[Dict[str, Any]] = []
        for lap in range(1, total_laps + 1):
            deg = self.calculate_lap_degradation(
                compound_code=compound_code,
                tyre_age_laps=lap,
                track_temp_c=track_temp_c,
                circuit_downforce_index=circuit_downforce_index,
            )
            curve.append(deg)
        return curve

    def evaluate_undercut_window(
        self,
        driver_current_age: int,
        driver_compound: str,
        rival_gap_s: float,
        fresh_compound: str = "C2",
        pit_loss_seconds: float = 21.5,
        track_temp_c: float = 30.0,
    ) -> Dict[str, Any]:
        """Calculates expected position advantage for pitting 1 lap earlier (undercut).

        Args:
            driver_current_age: Current laps on driver's tires.
            driver_compound: Current tire compound code.
            rival_gap_s: Gap to rival in front (positive means trailing by seconds).
            fresh_compound: Target compound fitted in pit stop.
            pit_loss_seconds: Green-flag pit stop time loss in seconds (typically 20-24s).
            track_temp_c: Track temperature in Celsius.

        Returns:
            Dict containing undercut feasibility, net delta gained, and recommendation.
        """
        # Pace on current degraded tire
        current_deg = self.calculate_lap_degradation(
            driver_compound, driver_current_age, track_temp_c
        )
        # Pace on fresh out-lap tire (age=1 lap)
        fresh_deg = self.calculate_lap_degradation(
            fresh_compound, 1, track_temp_c
        )

        # Pace advantage of fresh tire on the single out-lap
        outlap_pace_advantage = current_deg["pace_delta_seconds"] - fresh_deg["pace_delta_seconds"]

        # Net undercut delta: outlap delta minus the gap to rival
        net_gap_after_outlap = rival_gap_s - outlap_pace_advantage
        undercut_successful = net_gap_after_outlap < 0.0

        return {
            "driver_current_compound": driver_compound,
            "target_fresh_compound": fresh_compound,
            "rival_gap_before_s": round(rival_gap_s, 3),
            "outlap_pace_advantage_s": round(outlap_pace_advantage, 3),
            "projected_gap_after_outlap_s": round(net_gap_after_outlap, 3),
            "undercut_successful": undercut_successful,
            "recommendation": (
                f"EXECUTE UNDERCUT: Pitting now gains ~{outlap_pace_advantage:.2f}s over rival on out-lap!"
                if undercut_successful
                else f"HOLD TRACK POSITION: Current gap ({rival_gap_s:.2f}s) exceeds single-lap undercut advantage ({outlap_pace_advantage:.2f}s)."
            ),
        }
