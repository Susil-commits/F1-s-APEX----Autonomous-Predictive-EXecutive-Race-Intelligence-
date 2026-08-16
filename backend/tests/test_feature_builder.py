"""Unit tests for feature builder and predictive models."""
import numpy as np
from backend.app.simulator.engine import RaceSimulator
from backend.app.intelligence.feature_builder import FeatureBuilder, FEATURE_DIM
from backend.app.intelligence.tyre_model import TyreModel
from backend.app.intelligence.weather_model import WeatherPredictor
from backend.app.simulator.models import TyreCompound, DrivingMode, TrackCondition


def test_feature_vector_dimension_and_bounds():
    """Verify that feature extraction produces the exact expected dimensions and bounded values."""
    sim = RaceSimulator(seed=123)
    state = sim.step()

    vec = FeatureBuilder.extract_features(state)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (FEATURE_DIM,)
    assert vec.dtype == np.float32

    # Verify no NaN or Inf
    assert not np.isnan(vec).any()
    assert not np.isinf(vec).any()

    # Verify all normalized values are roughly within [0.0, 1.0]
    assert (vec >= 0.0).all()
    assert (vec <= 1.05).all()


def test_tyre_model_cliff_estimation():
    """Verify tyre model correctly calculates remaining laps and cliff penalty."""
    rem_laps = TyreModel.estimate_remaining_laps(
        compound=TyreCompound.SOFT,
        current_wear_pct=20.0,
        mode=DrivingMode.NORMAL,
        track_wear_factor=1.0,
    )
    assert rem_laps > 10

    # Past cliff loss
    loss_fresh = TyreModel.predict_lap_time_loss(TyreCompound.SOFT, 10.0)
    loss_cliff = TyreModel.predict_lap_time_loss(TyreCompound.SOFT, 85.0)
    assert loss_cliff > loss_fresh + 1.0


def test_weather_crossover():
    """Verify weather crossover logic recommends intermediate/wet when raining."""
    sim = RaceSimulator(seed=55)
    sim.weather.condition = TrackCondition.WET
    sim.weather.rain_intensity = 0.75

    rec = WeatherPredictor.recommend_compound_for_weather(sim.weather)
    assert rec == TyreCompound.WET
