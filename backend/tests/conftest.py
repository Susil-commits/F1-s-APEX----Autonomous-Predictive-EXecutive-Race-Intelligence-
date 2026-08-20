"""Shared pytest fixtures for APEX test suite.

Provides deterministic, minimal test harness objects to avoid
duplicated setup code across 33+ test files.
"""
from __future__ import annotations

import pytest

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import (
    CarState,
    DrivingMode,
    RaceState,
    SafetyCarStatus,
    TrackCondition,
    TyreCompound,
    WeatherState,
)
from backend.app.simulator.track import get_track

# ---------------------------------------------------------------------------
# Minimal deterministic RaceState
# ---------------------------------------------------------------------------

@pytest.fixture
def track_config():
    """Standard Silverstone track configuration."""
    return get_track("silverstone")


@pytest.fixture
def weather_dry():
    """Bone-dry track state."""
    return WeatherState(
        condition=TrackCondition.DRY,
        rain_intensity=0.0,
        track_temp_c=32.0,
        air_temp_c=23.0,
        rain_probability_next_5_laps=0.02,
        track_wetness=0.0,
        grip_multiplier=1.0,
    )


@pytest.fixture
def weather_wet():
    """Heavy-wet track state — forces wet tyre requirement."""
    return WeatherState(
        condition=TrackCondition.WET,
        rain_intensity=0.80,
        track_temp_c=18.0,
        air_temp_c=14.0,
        rain_probability_next_5_laps=0.95,
        track_wetness=0.85,
        grip_multiplier=0.55,
    )


@pytest.fixture
def player_car():
    """A minimal player car state with fresh medium tyres, lap 15."""
    return CarState(
        car_id="car_04",
        driver_name="APEX AI (You)",
        team_name="APEX Strategy Team",
        car_number=44,
        is_player=True,
        position=3,
        current_lap=15,
        tyre_compound=TyreCompound.MEDIUM,
        tyre_age_laps=14,
        tyre_wear_pct=29.0,
        fuel_kg=74.0,
        driving_mode=DrivingMode.NORMAL,
        gap_to_leader_s=8.5,
        gap_to_car_ahead_s=2.1,
        gap_to_car_behind_s=1.8,
    )


@pytest.fixture
def player_car_cliff():
    """Player car at tyre cliff — triggers emergency actions."""
    return CarState(
        car_id="car_04",
        driver_name="APEX AI (You)",
        team_name="APEX Strategy Team",
        car_number=44,
        is_player=True,
        position=2,
        current_lap=28,
        tyre_compound=TyreCompound.SOFT,
        tyre_age_laps=27,
        tyre_wear_pct=79.0,
        tyre_cliff_reached=True,
        fuel_kg=52.0,
        driving_mode=DrivingMode.NORMAL,
    )


@pytest.fixture
def minimal_race_state(player_car, weather_dry, track_config):
    """Minimal 2-car RaceState for unit tests."""
    opponent = CarState(
        car_id="car_01",
        driver_name="M. Verstappen",
        team_name="Red Bull Racing",
        car_number=1,
        is_player=False,
        position=1,
        current_lap=15,
        tyre_compound=TyreCompound.HARD,
        tyre_age_laps=14,
        tyre_wear_pct=19.0,
        fuel_kg=74.0,
        gap_to_leader_s=0.0,
        gap_to_car_ahead_s=0.0,
        gap_to_car_behind_s=8.5,
    )
    return RaceState(
        race_id="test_race_001",
        seed=42,
        track=track_config,
        current_lap=15,
        total_laps=52,
        tick=15,
        race_time_s=1380.0,
        weather=weather_dry,
        cars=[opponent, player_car],
        safety_car=SafetyCarStatus.NONE,
    )


@pytest.fixture
def minimal_race_state_wet(player_car, weather_wet, track_config):
    """RaceState with heavy wet weather conditions."""
    opponent = CarState(
        car_id="car_01",
        driver_name="M. Verstappen",
        team_name="Red Bull Racing",
        car_number=1,
        is_player=False,
        position=1,
        current_lap=15,
        tyre_compound=TyreCompound.WET,
        tyre_age_laps=3,
        tyre_wear_pct=6.0,
        fuel_kg=74.0,
    )
    return RaceState(
        race_id="test_race_wet_001",
        seed=99,
        track=track_config,
        current_lap=15,
        total_laps=52,
        tick=15,
        race_time_s=1650.0,
        weather=weather_wet,
        cars=[opponent, player_car],
        safety_car=SafetyCarStatus.NONE,
    )


@pytest.fixture
def safety_car_state(player_car, weather_dry, track_config):
    """RaceState under active Safety Car."""
    opponent = CarState(
        car_id="car_01",
        driver_name="M. Verstappen",
        team_name="Red Bull Racing",
        car_number=1,
        is_player=False,
        position=1,
        current_lap=20,
        tyre_compound=TyreCompound.MEDIUM,
        tyre_age_laps=19,
        tyre_wear_pct=40.0,
        fuel_kg=63.0,
    )
    return RaceState(
        race_id="test_race_sc_001",
        seed=7,
        track=track_config,
        current_lap=20,
        total_laps=52,
        tick=20,
        race_time_s=1840.0,
        weather=weather_dry,
        cars=[opponent, player_car],
        safety_car=SafetyCarStatus.SAFETY_CAR,
        safety_car_laps_remaining=3,
    )


@pytest.fixture
def seeded_engine():
    """Fully initialized deterministic race simulator (seed=42, Silverstone)."""
    return RaceSimulator(track_name="silverstone", seed=42, grid_size=5, enable_dynamic_weather=False)


@pytest.fixture
def advanced_engine():
    """Simulator stepped forward 20 laps (for mid-race tests)."""
    sim = RaceSimulator(track_name="silverstone", seed=42, grid_size=5, enable_dynamic_weather=False)
    for _ in range(20):
        sim.step()
    return sim
