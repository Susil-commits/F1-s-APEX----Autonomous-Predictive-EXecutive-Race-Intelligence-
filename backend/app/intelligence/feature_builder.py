"""Feature engineering pipeline that transforms RaceState into a fixed-size normalized vector."""
from typing import List, Optional
import numpy as np

from backend.app.simulator.models import (
    RaceState,
    CarState,
    TyreCompound,
    DrivingMode,
    TrackCondition,
    SafetyCarStatus,
)

# Fixed feature dimension definition
FEATURE_NAMES: List[str] = [
    "pos_norm",                    # Player position / total_cars
    "laps_remaining_norm",         # (total_laps - current_lap) / total_laps
    "race_progress_pct",           # current_lap / total_laps
    "gap_to_leader_s_norm",        # min(gap_to_leader, 60.0) / 60.0
    "gap_ahead_s_norm",            # min(gap_ahead, 15.0) / 15.0
    "gap_behind_s_norm",           # min(gap_behind, 15.0) / 15.0
    "tyre_is_soft",                # One-hot compound
    "tyre_is_medium",
    "tyre_is_hard",
    "tyre_is_inter",
    "tyre_is_wet",
    "tyre_wear_pct_norm",          # tyre_wear_pct / 100.0
    "tyre_age_laps_norm",          # tyre_age / total_laps
    "tyre_cliff_reached",          # 1.0 if cliff reached else 0.0
    "fuel_remaining_pct",          # fuel_kg / 105.0
    "mode_is_push",                # One-hot driving mode
    "mode_is_normal",
    "mode_is_conserve",
    "weather_is_dry",              # One-hot weather
    "weather_is_damp",
    "weather_is_wet",
    "rain_intensity",              # 0.0 to 1.0
    "rain_prob_5_laps",            # 0.0 to 1.0
    "sc_is_none",                  # One-hot safety car
    "sc_is_vsc",
    "sc_is_full",
    "pit_count_norm",              # min(pit_count, 4) / 4.0
    "laps_since_pit_norm",         # min(laps_since_last_pit, total_laps) / total_laps
]

FEATURE_DIM = len(FEATURE_NAMES)  # 28 dimensions


class FeatureBuilder:
    """Encodes full RaceState into an array consumable by rule engine and RL policies."""

    @staticmethod
    def extract_features(state: RaceState, target_car_id: Optional[str] = None) -> np.ndarray:
        """Extracts fixed 28-dimensional normalized feature vector."""
        total_cars = max(1, len(state.cars))
        total_laps = max(1, state.total_laps)
        current_lap = state.current_lap

        # Target car
        car: Optional[CarState] = None
        if target_car_id:
            car = next((c for c in state.cars if c.car_id == target_car_id), None)
        if car is None:
            car = next((c for c in state.cars if c.is_player), state.cars[0] if state.cars else None)

        if car is None:
            return np.zeros(FEATURE_DIM, dtype=np.float32)

        # 1. Position & Laps
        pos_norm = float(car.position) / float(total_cars)
        laps_remaining = max(0, total_laps - current_lap)
        laps_remaining_norm = float(laps_remaining) / float(total_laps)
        race_progress_pct = float(current_lap) / float(total_laps)

        # 2. Gaps
        gap_to_leader_s_norm = min(max(0.0, car.gap_to_leader_s), 60.0) / 60.0
        gap_ahead_s_norm = min(max(0.0, car.gap_to_car_ahead_s), 15.0) / 15.0
        gap_behind_s_norm = min(max(0.0, car.gap_to_car_behind_s), 15.0) / 15.0

        # 3. Tyre Compound One-Hot
        comp = car.tyre_compound
        tyre_is_soft = 1.0 if comp == TyreCompound.SOFT else 0.0
        tyre_is_medium = 1.0 if comp == TyreCompound.MEDIUM else 0.0
        tyre_is_hard = 1.0 if comp == TyreCompound.HARD else 0.0
        tyre_is_inter = 1.0 if comp == TyreCompound.INTERMEDIATE else 0.0
        tyre_is_wet = 1.0 if comp == TyreCompound.WET else 0.0

        # 4. Tyre Wear & Fuel
        tyre_wear_pct_norm = min(100.0, max(0.0, car.tyre_wear_pct)) / 100.0
        tyre_age_laps_norm = float(car.tyre_age_laps) / float(total_laps)
        tyre_cliff_reached = 1.0 if car.tyre_cliff_reached else 0.0
        fuel_remaining_pct = min(105.0, max(0.0, car.fuel_kg)) / 105.0

        # 5. Driving Mode One-Hot
        mode = car.driving_mode
        mode_is_push = 1.0 if mode == DrivingMode.PUSH else 0.0
        mode_is_normal = 1.0 if mode == DrivingMode.NORMAL else 0.0
        mode_is_conserve = 1.0 if mode == DrivingMode.CONSERVE else 0.0

        # 6. Weather One-Hot & Intensities
        cond = state.weather.condition
        weather_is_dry = 1.0 if cond == TrackCondition.DRY else 0.0
        weather_is_damp = 1.0 if cond == TrackCondition.DAMP else 0.0
        weather_is_wet = 1.0 if cond == TrackCondition.WET else 0.0
        rain_intensity = float(np.clip(state.weather.rain_intensity, 0.0, 1.0))
        rain_prob_5_laps = float(np.clip(state.weather.rain_probability_next_5_laps, 0.0, 1.0))

        # 7. Safety Car One-Hot
        sc = state.safety_car
        sc_is_none = 1.0 if sc == SafetyCarStatus.NONE else 0.0
        sc_is_vsc = 1.0 if sc == SafetyCarStatus.VSC else 0.0
        sc_is_full = 1.0 if sc == SafetyCarStatus.SAFETY_CAR else 0.0

        # 8. Pit stats
        pit_count_norm = min(float(car.pit_count), 4.0) / 4.0
        laps_since_pit_norm = min(float(car.laps_since_last_pit), float(total_laps)) / float(total_laps)

        vec = np.array([
            pos_norm,
            laps_remaining_norm,
            race_progress_pct,
            gap_to_leader_s_norm,
            gap_ahead_s_norm,
            gap_behind_s_norm,
            tyre_is_soft,
            tyre_is_medium,
            tyre_is_hard,
            tyre_is_inter,
            tyre_is_wet,
            tyre_wear_pct_norm,
            tyre_age_laps_norm,
            tyre_cliff_reached,
            fuel_remaining_pct,
            mode_is_push,
            mode_is_normal,
            mode_is_conserve,
            weather_is_dry,
            weather_is_damp,
            weather_is_wet,
            rain_intensity,
            rain_prob_5_laps,
            sc_is_none,
            sc_is_vsc,
            sc_is_full,
            pit_count_norm,
            laps_since_pit_norm,
        ], dtype=np.float32)

        return vec
