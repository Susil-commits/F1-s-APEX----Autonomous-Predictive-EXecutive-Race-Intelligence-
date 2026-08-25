"""Unit tests for Phase 2: Tyre ML suite, RUL, and Weather Intelligence."""
from backend.app.intelligence.tyre_model import TyreMLSuite, TyreModel
from backend.app.intelligence.weather_model import WeatherPredictor
from backend.app.simulator.models import (
    DrivingMode,
    TrackCondition,
    TyreCompound,
    WeatherState,
)


def test_tyre_ml_suite_predictions():
    suite = TyreMLSuite()
    assert suite.is_trained

    # Test Soft vs Hard delta prediction
    delta_soft, (ci_l_s, ci_u_s), _ = suite.predict_delta(TyreCompound.SOFT, tyre_age=15, track_temp_c=35.0, model_type="rf")
    delta_hard, (ci_l_h, ci_u_h), _ = suite.predict_delta(TyreCompound.HARD, tyre_age=15, track_temp_c=35.0, model_type="rf")

    assert delta_soft > delta_hard
    assert ci_l_s <= delta_soft <= ci_u_s
    assert ci_l_h <= delta_hard <= ci_u_h


def test_tyre_remaining_useful_life():
    rul = TyreModel.predict_remaining_useful_life(
        compound=TyreCompound.MEDIUM,
        wear_pct=30.0,
        tyre_age_laps=10,
        mode=DrivingMode.NORMAL,
    )
    assert rul["remaining_useful_laps"] > 0
    assert rul["cliff_probability"] < 0.20
    assert len(rul["ci_90"]) == 2

    # Heavily worn tyre
    rul_worn = TyreModel.predict_remaining_useful_life(
        compound=TyreCompound.MEDIUM,
        wear_pct=85.0,
        tyre_age_laps=32,
    )
    assert rul_worn["cliff_probability"] > 0.90


def test_weather_track_wetness_and_grip():
    dry_weather = WeatherState(condition=TrackCondition.DRY, rain_intensity=0.0, track_temp_c=32.0)
    wet_weather = WeatherState(condition=TrackCondition.WET, rain_intensity=0.85, track_temp_c=20.0)

    dry_wetness = WeatherPredictor.calculate_track_wetness(dry_weather)
    wet_wetness = WeatherPredictor.calculate_track_wetness(wet_weather)

    assert dry_wetness < 0.10
    assert wet_wetness > 0.80

    # Grip on dry: Soft > Inter > Wet
    grip_soft_dry = WeatherPredictor.calculate_grip_factor(dry_weather, TyreCompound.SOFT)
    grip_wet_dry = WeatherPredictor.calculate_grip_factor(dry_weather, TyreCompound.WET)
    assert grip_soft_dry > grip_wet_dry

    # Grip on wet: Wet > Soft
    grip_soft_wet = WeatherPredictor.calculate_grip_factor(wet_weather, TyreCompound.SOFT)
    grip_wet_wet = WeatherPredictor.calculate_grip_factor(wet_weather, TyreCompound.WET)
    assert grip_wet_wet > grip_soft_wet


def test_weather_probabilities_and_crossovers():
    weather = WeatherState(
        condition=TrackCondition.DAMP,
        rain_intensity=0.25,
        track_temp_c=22.0,
        rain_probability_next_5_laps=0.60,
    )
    probs = WeatherPredictor.predict_rain_probabilities(weather)
    assert 0.0 <= probs["rain_probability_5m"] <= 1.0
    assert 0.0 <= probs["rain_probability_10m"] <= 1.0

    eval_risk = WeatherPredictor.evaluate_weather_risk(weather, TyreCompound.SOFT)
    assert eval_risk["mismatch"] is True
    assert eval_risk["recommended_compound"] == TyreCompound.INTERMEDIATE
