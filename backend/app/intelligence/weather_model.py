"""Weather prediction, track wetness evolution, grip calculation, and tyre crossover intelligence."""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from backend.app.simulator.models import TrackCondition, TyreCompound, WeatherState

logger = logging.getLogger(__name__)


class WeatherPredictor:
    """Predictive weather model forecasting rain onset, track drying, grip coefficients, and tyre crossovers."""

    # Crossover thresholds based on track wetness index (0.0 = bone dry, 1.0 = heavy downpour)
    CROSSOVER_SLICKS_TO_INTERS = 0.18
    CROSSOVER_INTERS_TO_WETS = 0.58

    @classmethod
    def calculate_track_wetness(cls, weather: WeatherState) -> float:
        """Calculates normalized track wetness index (0.0 - 1.0) from rain intensity and condition."""
        if weather.condition == TrackCondition.WET:
            base = 0.65 + 0.35 * min(1.0, weather.rain_intensity)
        elif weather.condition == TrackCondition.DAMP:
            base = 0.20 + 0.30 * min(1.0, weather.rain_intensity)
        else:
            base = 0.05 * min(1.0, weather.rain_intensity)
        return float(np.clip(base, 0.0, 1.0))

    @classmethod
    def calculate_drying_rate(cls, weather: WeatherState) -> float:
        """Calculates track drying rate per lap based on track temperature and air conditions."""
        temp_factor = max(0.5, (weather.track_temp_c - 15.0) / 20.0)
        base_rate = getattr(weather, "drying_rate_per_lap", 0.08)
        # If it is currently raining, drying rate is zero
        if weather.rain_intensity > 0.05:
            return 0.0
        return float(round(base_rate * temp_factor, 4))

    @classmethod
    def calculate_grip_factor(cls, weather: WeatherState, compound: TyreCompound) -> float:
        """
        Calculates physical grip multiplier (0.40 - 1.05) depending on track wetness and fitted tyre compound.
        """
        wetness = cls.calculate_track_wetness(weather)
        comp_str = compound.value if hasattr(compound, "value") else str(compound).upper()

        if "WET" in comp_str:
            if wetness >= 0.55:
                return 0.88 # Optimal full wet grip
            elif wetness >= 0.25:
                return 0.76
            else:
                return 0.52 # Severe overheating on dry line
        elif "INTER" in comp_str:
            if 0.18 <= wetness <= 0.60:
                return 0.92 # Optimal intermediate window
            elif wetness < 0.18:
                return 0.72 # Excessive wear and thermal blister on dry
            else:
                return 0.68 # Aquaplaning risk in standing water
        else:
            # Slicks (Soft, Medium, Hard)
            if wetness < 0.15:
                base_slick = 1.05 if "SOFT" in comp_str else (1.00 if "MEDIUM" in comp_str else 0.96)
                return base_slick
            elif wetness < 0.30:
                return 0.70 # Significant traction loss
            else:
                return 0.45 # Severe aquaplaning (near total loss of lateral adhesion)

    @classmethod
    def predict_rain_probabilities(cls, weather: WeatherState) -> dict[str, float]:
        """Predicts 5-minute and 10-minute rain onset/continuation probabilities."""
        base_prob = float(getattr(weather, "rain_probability_next_5_laps", 0.10))
        if weather.rain_intensity > 0.1:
            prob_5m = min(1.0, 0.75 + weather.rain_intensity * 0.25)
            prob_10m = min(1.0, 0.60 + weather.rain_intensity * 0.35)
        else:
            prob_5m = float(np.clip(base_prob, 0.0, 1.0))
            prob_10m = float(np.clip(base_prob * 1.35, 0.0, 1.0))

        return {
            "rain_probability_5m": round(prob_5m, 3),
            "rain_probability_10m": round(prob_10m, 3),
            "current_rain_intensity": round(float(weather.rain_intensity), 2),
            "track_wetness": round(cls.calculate_track_wetness(weather), 3),
            "drying_rate_per_lap": cls.calculate_drying_rate(weather),
        }

    @classmethod
    def recommend_compound_for_weather(cls, weather: WeatherState) -> TyreCompound:
        """Determines the optimal compound for current/imminent track conditions."""
        wetness = cls.calculate_track_wetness(weather)
        if wetness >= cls.CROSSOVER_INTERS_TO_WETS:
            return TyreCompound.WET
        elif wetness >= cls.CROSSOVER_SLICKS_TO_INTERS:
            return TyreCompound.INTERMEDIATE
        else:
            return TyreCompound.HARD

    @classmethod
    def evaluate_weather_risk(cls, weather: WeatherState, current_compound: TyreCompound) -> dict[str, Any]:
        """Evaluates whether current tyres are mismatched with weather."""
        wetness = cls.calculate_track_wetness(weather)
        is_slick = current_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        is_inter = current_compound == TyreCompound.INTERMEDIATE
        is_wet = current_compound == TyreCompound.WET

        mismatch = False
        urgency = "LOW"
        reason = "Weather condition matches current compound."

        if wetness >= cls.CROSSOVER_INTERS_TO_WETS:
            if is_slick:
                mismatch = True
                urgency = "CRITICAL"
                reason = "Severe aquaplaning risk! Slicks on wet track lose >20s/lap."
            elif is_inter:
                mismatch = True
                urgency = "HIGH"
                reason = "Heavy standing water exceeds Intermediate dispersal capacity."
        elif wetness >= cls.CROSSOVER_SLICKS_TO_INTERS:
            if is_slick:
                mismatch = True
                urgency = "HIGH"
                reason = "Track wetness causing severe slip. Intermediate crossover active."
            elif is_wet:
                mismatch = True
                urgency = "MEDIUM"
                reason = "Track too dry for Full Wets; overheating risk."
        else:
            if is_wet or is_inter:
                mismatch = True
                urgency = "HIGH"
                reason = "Dry line present. Rain tyres degrading rapidly."

        return {
            "mismatch": mismatch,
            "urgency": urgency,
            "reason": reason,
            "recommended_compound": cls.recommend_compound_for_weather(weather),
            "rain_prob_5_laps": weather.rain_probability_next_5_laps,
            "track_wetness": round(wetness, 3),
            "grip_multiplier": round(cls.calculate_grip_factor(weather, current_compound), 3),
            "slick_to_inter_crossover": cls.CROSSOVER_SLICKS_TO_INTERS,
            "inter_to_wet_crossover": cls.CROSSOVER_INTERS_TO_WETS,
        }
