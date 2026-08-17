"""Multi-Factor Risk Engine: Tracks DNF, tyre, weather, traffic, mechanical, and pit loss risks."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
import numpy as np

from backend.app.simulator.models import (
    RaceState,
    CarState,
    RiskState,
    TrackCondition,
    TyreCompound,
    DrivingMode,
)

logger = logging.getLogger(__name__)


class RiskEngine:
    """Calculates multi-dimensional operational risk scores and risk-adjusted expected outcomes."""

    @classmethod
    def evaluate_risk(cls, state: RaceState, target_car_id: Optional[str] = None) -> RiskState:
        """
        Computes composite risk profile:
        - DNF risk
        - Tyre blowout risk
        - Weather transition risk
        - Traffic / undercut risk
        - Mechanical failure risk
        - Strategy vulnerability risk
        """
        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0] if state.cars else None)
        if player is None or player.is_dnf:
            return RiskState(overall_risk_score=1.0, dnf_risk=1.0)

        # 1. Tyre blowout risk
        wear = player.tyre_wear_pct
        if player.tyre_cliff_reached or wear >= 85.0:
            tyre_risk = 0.95
        elif wear >= 70.0:
            tyre_risk = 0.65
        elif wear >= 50.0:
            tyre_risk = 0.25
        else:
            tyre_risk = 0.05

        # 2. Weather transition risk
        wetness = getattr(state.weather, "track_wetness", 0.0)
        is_slick = player.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        if wetness > 0.35 and is_slick:
            weather_risk = 0.92
        elif wetness > 0.15 and is_slick:
            weather_risk = 0.55
        else:
            weather_risk = float(np.clip(state.weather.rain_probability_next_5_laps * 0.5, 0.0, 0.40))

        # 3. Traffic / undercut risk
        gap_behind = player.gap_to_car_behind_s
        if 0.0 < gap_behind <= 1.5 and wear > 45.0:
            traffic_risk = 0.75
        elif 0.0 < gap_behind <= 3.0:
            traffic_risk = 0.40
        else:
            traffic_risk = 0.10

        # 4. Mechanical failure risk
        if player.health_state:
            mech_risk = float(np.clip(player.health_state.failure_probability, 0.0, 1.0))
        else:
            mech_risk = 0.02

        # 5. Composite DNF risk
        dnf_risk = float(np.clip((tyre_risk * 0.40) + (weather_risk * 0.35) + (mech_risk * 0.25), 0.01, 0.99))

        # 6. Strategy vulnerability risk
        laps_left = max(1, state.total_laps - state.current_lap)
        if player.pit_count == 0 and laps_left < 10:
            strat_risk = 0.85 # Mandatory compound rule risk
        elif player.tyre_age_laps > 35:
            strat_risk = 0.60
        else:
            strat_risk = 0.15

        overall_score = round(float(np.mean([dnf_risk, tyre_risk, weather_risk, traffic_risk, mech_risk, strat_risk])), 3)

        return RiskState(
            overall_risk_score=overall_score,
            dnf_risk=round(dnf_risk, 3),
            tyre_blowout_risk=round(tyre_risk, 3),
            weather_transition_risk=round(weather_risk, 3),
            traffic_undercut_risk=round(traffic_risk, 3),
            mechanical_failure_risk=round(mech_risk, 3),
            strategy_vulnerability_risk=round(strat_risk, 3),
        )
