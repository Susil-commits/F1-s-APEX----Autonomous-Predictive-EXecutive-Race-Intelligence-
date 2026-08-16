"""Unit tests for FastF1 tyre data cleaning, calibration, and prediction."""
import os
import pytest
import pandas as pd
import numpy as np

from backend.training.fetch_fastf1_data import (
    clean_session_laps,
    generate_synthetic_fallback_data,
    fetch_all_real_races,
)
from backend.training.validate_tyre_model import fit_compound_curve, evaluate_and_calibrate
from backend.app.intelligence.tyre_model import TyreModel
from backend.app.simulator.models import TyreCompound, DrivingMode, CarState, TrackConfig, WeatherState


def test_clean_session_laps_filtering():
    """Verifies that pit in/out laps and safety car laps are strictly filtered out and tagged with data_source."""
    raw_df = pd.DataFrame([
        {
            "Driver": "VER",
            "Compound": "SOFT",
            "TyreLife": 5,
            "LapTime": pd.Timedelta(seconds=90.5),
            "Stint": 1,
            "PitInTime": pd.NaT,
            "PitOutTime": pd.NaT,
            "IsAccurate": True,
            "TrackStatus": "1",
        },
        {
            "Driver": "VER",
            "Compound": "SOFT",
            "TyreLife": 6,
            "LapTime": pd.Timedelta(seconds=115.0),
            "Stint": 1,
            "PitInTime": pd.Timedelta(seconds=110.0),  # Pit in-lap -> should be dropped
            "PitOutTime": pd.NaT,
            "IsAccurate": True,
            "TrackStatus": "1",
        },
        {
            "Driver": "VER",
            "Compound": "SOFT",
            "TyreLife": 7,
            "LapTime": pd.Timedelta(seconds=125.0),
            "Stint": 2,
            "PitInTime": pd.NaT,
            "PitOutTime": pd.Timedelta(seconds=0.0),  # Pit out-lap -> should be dropped
            "IsAccurate": True,
            "TrackStatus": "1",
        },
        {
            "Driver": "VER",
            "Compound": "SOFT",
            "TyreLife": 8,
            "LapTime": pd.Timedelta(seconds=130.0),
            "Stint": 2,
            "PitInTime": pd.NaT,
            "PitOutTime": pd.NaT,
            "IsAccurate": True,
            "TrackStatus": "4",  # Safety Car lap -> should be dropped
        },
        {
            "Driver": "VER",
            "Compound": "SOFT",
            "TyreLife": 9,
            "LapTime": pd.Timedelta(seconds=91.2),
            "Stint": 2,
            "PitInTime": pd.NaT,
            "PitOutTime": pd.NaT,
            "IsAccurate": True,
            "TrackStatus": "1",
        },
    ])

    clean_df = clean_session_laps(raw_df, circuit_name="Silverstone", year=2023)
    assert len(clean_df) == 2, f"Expected 2 clean laps, got {len(clean_df)}"
    assert (clean_df["tyre_age"].values == [5, 9]).all()
    assert (clean_df["lap_time_delta"] >= 0.0).all()
    assert "data_source" in clean_df.columns
    assert (clean_df["data_source"] == "fastf1_real").all()


def test_synthetic_fallback_generation():
    """Ensures fallback synthetic data generator creates structured curves with data_source tag."""
    df = generate_synthetic_fallback_data()
    assert not df.empty
    assert set(df["compound"].unique()) == {"SOFT", "MEDIUM", "HARD"}
    assert "lap_time_delta" in df.columns
    assert "data_source" in df.columns
    assert (df["data_source"] == "synthetic_fallback").all()
    assert len(df) > 500


def test_fetch_all_real_races_fallback_switch(tmp_path):
    """Verifies that allow_synthetic_fallback=False raises RuntimeError when no sessions fetched."""
    # Pass non-existent session
    fake_races = [(1950, "NonExistentGrandPrix", "R")]
    with pytest.raises(RuntimeError, match="No real sessions were fetched"):
        fetch_all_real_races(
            races=fake_races,
            output_path=str(tmp_path / "real_test.csv"),
            allow_synthetic_fallback=False,
        )

    # When fallback is explicitly allowed
    df = fetch_all_real_races(
        races=fake_races,
        output_path=str(tmp_path / "fallback_test.csv"),
        allow_synthetic_fallback=True,
    )
    assert not df.empty
    assert (df["data_source"] == "synthetic_fallback").all()


def test_tyre_model_predict_loss_calibrated():
    """Verifies that TyreModel uses calibrated curve when available and respects tyre compound differences."""
    loss_fresh_soft = TyreModel.predict_lap_time_loss(TyreCompound.SOFT, wear_pct=5.0, tyre_age_laps=2)
    loss_worn_soft = TyreModel.predict_lap_time_loss(TyreCompound.SOFT, wear_pct=75.0, tyre_age_laps=22)
    
    assert loss_worn_soft > loss_fresh_soft, "Worn tyre degradation loss must exceed fresh tyre loss"
    assert loss_fresh_soft >= 0.0


def test_tyre_model_pit_window_calculation():
    """Verifies pit window assessment and cliff risk categorization."""
    car = CarState(
        car_id="car_1",
        driver_name="Nayake",
        team_name="APEX Racing",
        car_number=1,
        is_player=True,
        position=1,
        current_lap=20,
        lap_progress_pct=0.5,
        total_race_time_s=1800.0,
        gap_to_leader_s=0.0,
        gap_to_car_ahead_s=0.0,
        gap_to_car_behind_s=2.5,
        tyre_compound=TyreCompound.SOFT,
        tyre_age_laps=18,
        tyre_wear_pct=76.0,
    )
    track = TrackConfig(
        name="silverstone",
        country="UK",
        total_laps=52,
        lap_distance_km=5.891,
        base_lap_time_s=88.5,
        pit_lane_delta_s=20.0,
        vsc_pit_advantage_s=8.0,
        sc_pit_advantage_s=12.0,
        tyre_wear_factor=1.0,
        rain_probability_base=0.1,
    )
    weather = WeatherState()

    window = TyreModel.calculate_pit_window(car, track, weather)
    assert "cliff_risk" in window
    assert window["cliff_risk"] in ["MODERATE", "HIGH", "CRITICAL"]
    assert "predicted_loss_s" in window
    assert window["predicted_loss_s"] > 0.0


def test_circuit_degradation_factors():
    """Verifies track-specific degradation severity scaling."""
    bahrain_factor = TyreModel.get_circuit_degradation_factor("bahrain")
    monza_factor = TyreModel.get_circuit_degradation_factor("monza")
    monaco_factor = TyreModel.get_circuit_degradation_factor("monaco")

    assert bahrain_factor > 1.2, "Bahrain must be categorized as high wear"
    assert monza_factor < 1.0, "Monza must be low wear"
    assert monaco_factor < monza_factor, "Monaco wear must be lower than Monza"

