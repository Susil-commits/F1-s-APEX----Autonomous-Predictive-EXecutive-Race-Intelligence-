"""Opponent behavior prediction, pit probability modeling, and tactical intent estimation."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import numpy as np

from backend.app.simulator.models import CarState, TyreCompound, DrivingMode, WeatherState, TrackConfig
from backend.app.intelligence.tyre_model import TyreModel

logger = logging.getLogger(__name__)


class OpponentPrediction(BaseModel):
    """Structured tactical predictions for a single rival car."""
    driver_name: str
    car_id: str
    position: int
    pit_next_1_lap_prob: float
    pit_next_2_laps_prob: float
    attack_probability: float
    defence_probability: float
    expected_pace_delta: float
    expected_next_compound: str
    strategy_intent: str # UNDERCUT, OVERCUT, STINT_EXTEND, PUSH_DEFEND
    risk_tolerance: float
    confidence: float


class OpponentIntelligenceEngine:
    """Predicts rival behavior, pit timing, and offensive/defensive tactical maneuvers."""

    @classmethod
    def predict_opponent_state(
        cls,
        opponent: CarState,
        player_car: Optional[CarState],
        track: TrackConfig,
        weather: WeatherState,
        race_lap: int,
    ) -> OpponentPrediction:
        """Evaluates rival telemetry, wear, gaps, and past pit count to infer strategic intentions."""
        tyre_age = opponent.tyre_age_laps
        wear_pct = opponent.tyre_wear_pct
        comp_str = opponent.tyre_compound.value if hasattr(opponent.tyre_compound, "value") else str(opponent.tyre_compound)

        # Baseline pit probability based on tyre cliff proximity
        pit_window = TyreModel.calculate_pit_window(opponent, track, weather)
        cliff_risk = pit_window.get("cliff_risk", "LOW")
        
        base_pit_prob = 0.05
        if cliff_risk == "CRITICAL" or wear_pct >= 75.0:
            base_pit_prob = 0.88
        elif cliff_risk == "HIGH" or wear_pct >= 65.0:
            base_pit_prob = 0.65
        elif cliff_risk == "MODERATE" or wear_pct >= 50.0:
            base_pit_prob = 0.35

        # If weather crossover is active, pit prob surges
        if weather.condition.value in ("WET", "DAMP") and comp_str in ("SOFT", "MEDIUM", "HARD"):
            base_pit_prob = max(base_pit_prob, 0.92)

        pit_1_lap = round(float(np.clip(base_pit_prob, 0.0, 1.0)), 2)
        pit_2_laps = round(float(np.clip(base_pit_prob * 1.35, 0.0, 1.0)), 2)

        # Tactical Attack vs Defence
        gap_ahead = opponent.gap_to_car_ahead_s
        gap_behind = opponent.gap_to_car_behind_s

        attack_prob = 0.15
        if 0.0 < gap_ahead <= 1.2:
            attack_prob = 0.82 if wear_pct < 60.0 else 0.55
        elif 1.2 < gap_ahead <= 2.5:
            attack_prob = 0.45

        defence_prob = 0.20
        if 0.0 < gap_behind <= 1.0:
            defence_prob = 0.85
        elif 1.0 < gap_behind <= 2.0:
            defence_prob = 0.50

        # Pace delta prediction relative to clean air
        pace_loss = TyreModel.predict_lap_time_loss(opponent.tyre_compound, wear_pct, tyre_age)
        expected_pace_delta = round(pace_loss, 3)

        # Expected next compound
        laps_left = max(1, track.total_laps - race_lap)
        if weather.condition.value == "WET":
            next_compound = "WET"
        elif weather.condition.value == "DAMP":
            next_compound = "INTERMEDIATE"
        elif laps_left <= 15:
            next_compound = "SOFT"
        elif laps_left <= 30:
            next_compound = "MEDIUM"
        else:
            next_compound = "HARD"

        # Strategic intent classification
        if player_car and opponent.position == player_car.position + 1 and gap_behind <= 2.0:
            intent = "UNDERCUT_THREAT"
        elif pit_1_lap > 0.60:
            intent = "BOX_IMMINENT"
        elif attack_prob > 0.70:
            intent = "ATTACK_AHEAD"
        elif defence_prob > 0.70:
            intent = "DEFEND_REAR"
        else:
            intent = "STINT_EXTEND"

        return OpponentPrediction(
            driver_name=opponent.driver_name,
            car_id=opponent.car_id,
            position=opponent.position,
            pit_next_1_lap_prob=pit_1_lap,
            pit_next_2_laps_prob=pit_2_laps,
            attack_probability=round(attack_prob, 2),
            defence_probability=round(defence_prob, 2),
            expected_pace_delta=expected_pace_delta,
            expected_next_compound=next_compound,
            strategy_intent=intent,
            risk_tolerance=0.70 if "VER" in opponent.driver_name or "NOR" in opponent.driver_name else 0.50,
            confidence=0.87,
        )

    @classmethod
    def predict_all_opponents(
        cls,
        cars: List[CarState],
        player_car_id: Optional[str],
        track: TrackConfig,
        weather: WeatherState,
        race_lap: int,
    ) -> List[OpponentPrediction]:
        """Runs predictions across all non-player cars in grid."""
        player = next((c for c in cars if (player_car_id and c.car_id == player_car_id) or c.is_player), None)
        predictions = []
        for c in cars:
            if player and c.car_id == player.car_id:
                continue
            pred = cls.predict_opponent_state(c, player, track, weather, race_lap)
            predictions.append(pred)
        return predictions
