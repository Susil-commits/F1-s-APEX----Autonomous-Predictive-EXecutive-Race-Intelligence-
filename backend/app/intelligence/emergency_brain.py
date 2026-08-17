"""Autonomous Emergency Brain: Instant detection, classification, impact estimation, and tactical response."""
from __future__ import annotations

import logging

from pydantic import BaseModel

from backend.app.simulator.models import (
    RaceState,
    StrategyAction,
    TrackCondition,
    TyreCompound,
)

logger = logging.getLogger(__name__)


class EmergencyEvent(BaseModel):
    """Detected tactical emergency event."""
    event_type: str # SUDDEN_RAIN, SAFETY_CAR_DEPLOYED, PUNCTURE_DEBRIS, MECHANICAL_ALARM, OPPONENT_UNDERCUT
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    detected_lap: int
    impact_loss_s: float
    recommended_action: StrategyAction
    top_reasons: list[str]
    confidence: float


class EmergencyBrain:
    """Fast-path autonomous incident detector and tactical responder."""

    @classmethod
    def process_state(cls, state: RaceState, target_car_id: str | None = None) -> EmergencyEvent | None:
        """
        Executes Emergency Pipeline:
        DETECT -> CLASSIFY -> ESTIMATE IMPACT -> GENERATE ACTIONS -> RANK -> SELECT.
        
        Returns an EmergencyEvent if immediate autonomous intervention is required.
        """
        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0] if state.cars else None)
        if player is None or player.is_dnf:
            return None

        # 1. Sudden Torrential Rain / Weather Emergency
        is_slick = player.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        if (state.weather.condition == TrackCondition.WET or state.weather.rain_intensity > 0.50) and is_slick:
            return EmergencyEvent(
                event_type="SUDDEN_RAIN",
                severity="CRITICAL",
                detected_lap=state.current_lap,
                impact_loss_s=22.0,
                recommended_action=StrategyAction.PIT_WET,
                top_reasons=[
                    "Torrential rain on track while fitted with dry slick compound.",
                    "Standing water causing extreme aquaplaning risk (>20s/lap loss).",
                    "Box immediately for Full Wet tyres.",
                ],
                confidence=0.98,
            )

        if state.weather.condition == TrackCondition.DAMP and state.weather.rain_intensity > 0.20 and is_slick:
            return EmergencyEvent(
                event_type="DAMP_TRACK_TRANSITION",
                severity="HIGH",
                detected_lap=state.current_lap,
                impact_loss_s=12.0,
                recommended_action=StrategyAction.PIT_INTER,
                top_reasons=[
                    "Rainfall onset causing slippery track surface.",
                    "Intermediate crossover threshold breached.",
                    "Box this lap for Intermediate tyres.",
                ],
                confidence=0.94,
            )

        # 2. Acute Tyre Puncture / Extreme Blown Tyre
        if player.tyre_cliff_reached or player.tyre_wear_pct >= 85.0:
            rec_comp = StrategyAction.PIT_HARD if player.tyre_compound != TyreCompound.HARD else StrategyAction.PIT_MEDIUM
            return EmergencyEvent(
                event_type="PUNCTURE_DEBRIS",
                severity="CRITICAL",
                detected_lap=state.current_lap,
                impact_loss_s=15.0,
                recommended_action=rec_comp,
                top_reasons=[
                    f"Acute tyre degradation cliff reached ({player.tyre_wear_pct:.1f}% wear).",
                    "Catastrophic blowout risk and structural carcass failure.",
                    "Box this lap for fresh compound.",
                ],
                confidence=0.95,
            )

        # 3. Opportunistic Safety Car / VSC Pit Stop Trigger
        sc_val = state.safety_car.value if hasattr(state.safety_car, "value") else str(state.safety_car)
        if sc_val in ("SAFETY_CAR", "VSC"):
            if player.tyre_wear_pct > 35.0 and player.laps_since_last_pit > 6 and (state.total_laps - state.current_lap) > 4:
                advantage = state.track.sc_pit_advantage_s if sc_val == "SAFETY_CAR" else state.track.vsc_pit_advantage_s
                rec_comp = StrategyAction.PIT_HARD if player.tyre_compound != TyreCompound.HARD else StrategyAction.PIT_MEDIUM
                return EmergencyEvent(
                    event_type="SAFETY_CAR_DEPLOYED",
                    severity="HIGH",
                    detected_lap=state.current_lap,
                    impact_loss_s=-advantage, # Negative loss is time gained
                    recommended_action=rec_comp,
                    top_reasons=[
                        f"{sc_val} deployed! Free pit stop window active.",
                        f"Saves ~{advantage:.1f}s pit lane delta vs green flag racing.",
                        "Box this lap to capitalize on discounted pit loss.",
                    ],
                    confidence=0.91,
                )

        # 4. Critical Mechanical / Engine Overheat Alert
        if player.health_state and player.health_state.overall_health_score < 45.0:
            return EmergencyEvent(
                event_type="MECHANICAL_ALARM",
                severity="HIGH",
                detected_lap=state.current_lap,
                impact_loss_s=8.0,
                recommended_action=StrategyAction.CONSERVE,
                top_reasons=[
                    f"Powertrain thermal alarm (Health: {player.health_state.overall_health_score:.1f}%).",
                    "High risk of mechanical DNF within 3-5 laps.",
                    "Switch to CONSERVE mode / lift-and-coast to manage temperatures.",
                ],
                confidence=0.89,
            )

        return None
