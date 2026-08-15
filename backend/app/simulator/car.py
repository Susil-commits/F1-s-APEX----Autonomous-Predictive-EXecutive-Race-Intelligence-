"""Car physics, tyre degradation models, and lap time computation engine."""
from typing import Tuple, Dict
import numpy as np

from backend.app.simulator.models import (
    CarState,
    TrackConfig,
    WeatherState,
    TyreCompound,
    DrivingMode,
    TrackCondition,
    SafetyCarStatus,
)


COMPOUND_SPECS: Dict[TyreCompound, Dict[str, float]] = {
    TyreCompound.SOFT: {
        "pace_delta_s": -0.85,          # Fastest in dry
        "base_wear_rate_pct": 3.40,     # % wear per standard lap
        "cliff_threshold_pct": 75.0,    # Cliff point where performance falls off rapidly
        "cliff_penalty_s_per_pct": 0.08,# Extra time penalty per % wear past cliff
        "ideal_track_temp_c": 35.0,
    },
    TyreCompound.MEDIUM: {
        "pace_delta_s": 0.00,           # Reference baseline
        "base_wear_rate_pct": 2.10,
        "cliff_threshold_pct": 80.0,
        "cliff_penalty_s_per_pct": 0.06,
        "ideal_track_temp_c": 30.0,
    },
    TyreCompound.HARD: {
        "pace_delta_s": 0.75,           # Slower but durable
        "base_wear_rate_pct": 1.35,
        "cliff_threshold_pct": 85.0,
        "cliff_penalty_s_per_pct": 0.05,
        "ideal_track_temp_c": 28.0,
    },
    TyreCompound.INTERMEDIATE: {
        "pace_delta_s": 3.50,           # Slow in dry, optimal in damp (rain_intensity 0.15-0.55)
        "base_wear_rate_pct": 2.40,
        "cliff_threshold_pct": 75.0,
        "cliff_penalty_s_per_pct": 0.07,
        "ideal_track_temp_c": 22.0,
    },
    TyreCompound.WET: {
        "pace_delta_s": 7.00,           # Slow in dry, optimal in heavy wet (rain_intensity > 0.55)
        "base_wear_rate_pct": 2.20,
        "cliff_threshold_pct": 75.0,
        "cliff_penalty_s_per_pct": 0.07,
        "ideal_track_temp_c": 20.0,
    },
}

MODE_SPECS: Dict[DrivingMode, Dict[str, float]] = {
    DrivingMode.PUSH: {
        "pace_delta_s": -0.75,
        "wear_multiplier": 1.45,
        "fuel_burn_multiplier": 1.20,
    },
    DrivingMode.NORMAL: {
        "pace_delta_s": 0.00,
        "wear_multiplier": 1.00,
        "fuel_burn_multiplier": 1.00,
    },
    DrivingMode.CONSERVE: {
        "pace_delta_s": 0.65,
        "wear_multiplier": 0.65,
        "fuel_burn_multiplier": 0.80,
    },
}


class CarPhysics:
    """Computes deterministic car dynamics, degradation, and lap times."""

    @staticmethod
    def calculate_tyre_wear(
        compound: TyreCompound,
        current_wear_pct: float,
        mode: DrivingMode,
        track_wear_factor: float,
        weather: WeatherState,
        rng: np.random.Generator,
    ) -> Tuple[float, bool]:
        """Calculates new tyre wear percentage and cliff status for a lap."""
        spec = COMPOUND_SPECS[compound]
        mode_spec = MODE_SPECS[mode]

        # Base wear modified by mode and track abrasiveness
        wear_delta = spec["base_wear_rate_pct"] * mode_spec["wear_multiplier"] * track_wear_factor

        # Temperature effect
        temp_delta = abs(weather.track_temp_c - spec["ideal_track_temp_c"])
        wear_delta *= (1.0 + 0.01 * min(temp_delta, 25.0))

        # Wet weather mismatch wear acceleration
        if compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD):
            if weather.rain_intensity > 0.40:
                # Slicks in heavy rain slip and wear violently
                wear_delta *= 1.3
        elif compound in (TyreCompound.INTERMEDIATE, TyreCompound.WET):
            if weather.condition == TrackCondition.DRY:
                # Rain tyres destroy themselves on a bone-dry track
                wear_delta *= 3.0

        # Small micro-variance for realism
        noise = rng.normal(1.0, 0.02)
        wear_delta = max(0.1, wear_delta * noise)

        new_wear_pct = min(100.0, current_wear_pct + wear_delta)
        cliff_reached = new_wear_pct >= spec["cliff_threshold_pct"]

        return round(new_wear_pct, 2), cliff_reached

    @staticmethod
    def calculate_lap_time(
        car: CarState,
        track: TrackConfig,
        weather: WeatherState,
        safety_car: SafetyCarStatus,
        in_traffic: bool,
        rng: np.random.Generator,
    ) -> float:
        """Calculates lap time in seconds considering all physical factors."""
        if safety_car == SafetyCarStatus.SAFETY_CAR:
            # Under Safety Car, delta time is ~140% of base lap time
            return round(track.base_lap_time_s * 1.40 + rng.normal(0.0, 0.3), 3)
        elif safety_car == SafetyCarStatus.VSC:
            # Under VSC, delta time is ~125% of base lap time
            return round(track.base_lap_time_s * 1.25 + rng.normal(0.0, 0.2), 3)

        spec = COMPOUND_SPECS[car.tyre_compound]
        mode_spec = MODE_SPECS[car.driving_mode]

        # 1. Base track lap time
        lap_time = track.base_lap_time_s

        # 2. Compound natural delta
        lap_time += spec["pace_delta_s"]

        # 3. Driving mode delta (Push vs Conserve)
        lap_time += mode_spec["pace_delta_s"]

        # 4. Fuel weight effect (each kg adds ~0.035s)
        fuel_penalty = car.fuel_kg * 0.033
        lap_time += fuel_penalty

        # 5. Tyre degradation penalty
        # Linear degradation up to cliff
        linear_wear_penalty = (car.tyre_wear_pct / 100.0) * 1.8
        lap_time += linear_wear_penalty

        # Non-linear cliff penalty
        if car.tyre_wear_pct > spec["cliff_threshold_pct"]:
            excess = car.tyre_wear_pct - spec["cliff_threshold_pct"]
            cliff_penalty = excess * spec["cliff_penalty_s_per_pct"] * 1.5
            lap_time += cliff_penalty

        # 6. Weather & tyre matching penalty
        weather_penalty = 0.0
        rain = weather.rain_intensity

        if rain < 0.10: # Dry track
            if car.tyre_compound == TyreCompound.INTERMEDIATE:
                weather_penalty += 3.50 # Intermediates on dry track
            elif car.tyre_compound == TyreCompound.WET:
                weather_penalty += 7.00 # Wets on dry track
        elif 0.10 <= rain <= 0.50: # Damp / Intermediate conditions
            if car.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD):
                # Slicks on damp track lose huge grip
                weather_penalty += 8.0 * (rain / 0.50)
            elif car.tyre_compound == TyreCompound.INTERMEDIATE:
                weather_penalty -= 1.0 # Optimal tyre for damp
            elif car.tyre_compound == TyreCompound.WET:
                weather_penalty += 2.5 # Too wet tyre for light rain
        else: # Heavy wet conditions (rain > 0.50)
            if car.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD):
                weather_penalty += 22.0 # Slicks aquaplaning
            elif car.tyre_compound == TyreCompound.INTERMEDIATE:
                weather_penalty += 4.5 # Inters struggling with standing water
            elif car.tyre_compound == TyreCompound.WET:
                weather_penalty -= 0.5 # Optimal tyre

        lap_time += weather_penalty

        # 7. Dirty air / Traffic penalty
        if in_traffic:
            lap_time += 0.35

        # 8. Micro-noise (driver variance ±0.15s)
        driver_variance = rng.normal(0.0, 0.12)
        lap_time += driver_variance

        # Pit stop delta if car made a pit stop this lap
        if car.in_pit:
            lap_time += track.pit_lane_delta_s

        return max(50.0, round(lap_time, 3))
