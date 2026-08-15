"""Weather prediction and rain onset transition model."""
from typing import Dict
from backend.app.simulator.models import WeatherState, TrackCondition, TyreCompound


class WeatherPredictor:
    """Estimates weather transitions, rain probability, and tyre cross-over thresholds."""

    CROSSOVER_SLICKS_TO_INTERS = 0.15
    CROSSOVER_INTERS_TO_WETS = 0.55

    @classmethod
    def recommend_compound_for_weather(cls, weather: WeatherState) -> TyreCompound:
        """Determines the optimal compound for current/imminent track conditions."""
        rain = weather.rain_intensity
        if rain >= cls.CROSSOVER_INTERS_TO_WETS or weather.condition == TrackCondition.WET:
            return TyreCompound.WET
        elif rain >= cls.CROSSOVER_SLICKS_TO_INTERS or weather.condition == TrackCondition.DAMP:
            return TyreCompound.INTERMEDIATE
        else:
            return TyreCompound.HARD

    @classmethod
    def evaluate_weather_risk(cls, weather: WeatherState, current_compound: TyreCompound) -> Dict[str, any]:
        """Evaluates whether current tyres are mismatched with weather."""
        is_slick = current_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        is_inter = current_compound == TyreCompound.INTERMEDIATE
        is_wet = current_compound == TyreCompound.WET

        mismatch = False
        urgency = "LOW"
        reason = "Weather condition matches current compound."

        if weather.condition == TrackCondition.WET:
            if is_slick:
                mismatch = True
                urgency = "CRITICAL"
                reason = "Severe aquaplaning risk! Slicks on wet track lose >20s/lap."
            elif is_inter:
                mismatch = True
                urgency = "HIGH"
                reason = "Heavy standing water exceeds Intermediate dispersal capacity."
        elif weather.condition == TrackCondition.DAMP:
            if is_slick and weather.rain_intensity > 0.20:
                mismatch = True
                urgency = "HIGH"
                reason = "Track wetness causing severe slip. Intermediate crossover active."
            elif is_wet:
                mismatch = True
                urgency = "MEDIUM"
                reason = "Track too dry for Full Wets; overheating risk."
        elif weather.condition == TrackCondition.DRY:
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
        }
