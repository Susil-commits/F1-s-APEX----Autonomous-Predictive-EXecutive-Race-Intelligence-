"""Tyre degradation predictor and pit window estimation intelligence."""
from typing import Dict, Tuple, Optional, Any
import numpy as np

from backend.app.simulator.models import TyreCompound, DrivingMode, CarState, TrackConfig, WeatherState
from backend.app.simulator.car import COMPOUND_SPECS, MODE_SPECS


class TyreModel:
    """Predicts tyre degradation curves, lap-time delta, and remaining useful life."""

    @staticmethod
    def estimate_remaining_laps(
        compound: TyreCompound,
        current_wear_pct: float,
        mode: DrivingMode,
        track_wear_factor: float,
    ) -> int:
        """Estimates laps remaining before reaching the degradation cliff."""
        spec = COMPOUND_SPECS[compound]
        mode_spec = MODE_SPECS[mode]
        wear_per_lap = spec["base_wear_rate_pct"] * mode_spec["wear_multiplier"] * track_wear_factor

        wear_margin = max(0.0, spec["cliff_threshold_pct"] - current_wear_pct)
        if wear_per_lap <= 0:
            return 99
        return int(wear_margin / wear_per_lap)

    @staticmethod
    def predict_lap_time_loss(
        compound: TyreCompound,
        wear_pct: float,
    ) -> float:
        """Predicts the lap-time penalty (in seconds) incurred from current tyre degradation."""
        spec = COMPOUND_SPECS[compound]
        linear_loss = (wear_pct / 100.0) * 1.8

        cliff_loss = 0.0
        if wear_pct > spec["cliff_threshold_pct"]:
            excess = wear_pct - spec["cliff_threshold_pct"]
            cliff_loss = excess * spec["cliff_penalty_s_per_pct"] * 1.5

        return round(linear_loss + cliff_loss, 3)

    @staticmethod
    def calculate_pit_window(
        car: CarState,
        track: TrackConfig,
        weather: WeatherState,
    ) -> Dict[str, Any]:
        """Calculates optimal pit window range and urgency."""
        spec = COMPOUND_SPECS[car.tyre_compound]
        remaining_laps_to_cliff = TyreModel.estimate_remaining_laps(
            car.tyre_compound,
            car.tyre_wear_pct,
            car.driving_mode,
            track.tyre_wear_factor,
        )

        cliff_lap = car.current_lap + remaining_laps_to_cliff
        window_start = max(car.current_lap, cliff_lap - 4)
        window_end = min(track.total_laps, cliff_lap + 2)

        # Assess status
        if car.current_lap < window_start - 2:
            status = "EARLY"
        elif window_start - 2 <= car.current_lap <= window_end:
            status = "OPTIMAL"
        elif car.current_lap > window_end:
            status = "LATE"
        else:
            status = "OPTIMAL"

        # Calculate cliff risk
        if car.tyre_wear_pct >= spec["cliff_threshold_pct"]:
            cliff_risk = "CRITICAL"
        elif car.tyre_wear_pct >= spec["cliff_threshold_pct"] - 12.0:
            cliff_risk = "HIGH"
        elif car.tyre_wear_pct >= spec["cliff_threshold_pct"] - 25.0:
            cliff_risk = "MODERATE"
        else:
            cliff_risk = "LOW"

        return {
            "window_start_lap": window_start,
            "window_end_lap": window_end,
            "optimal_lap": cliff_lap - 1,
            "remaining_laps_to_cliff": remaining_laps_to_cliff,
            "status": status,
            "cliff_risk": cliff_risk,
            "predicted_loss_s": TyreModel.predict_lap_time_loss(car.tyre_compound, car.tyre_wear_pct),
        }
