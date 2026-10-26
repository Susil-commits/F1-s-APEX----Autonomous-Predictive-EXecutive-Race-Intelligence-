"""Unit tests for Pirelli Physics-Informed Tyre Degradation Engine."""
import pytest
from core.features.tyre_model import TyreDegradationModel, PIRELLI_COMPOUNDS


def test_tyre_model_initialization():
    model = TyreDegradationModel()
    assert "C1" in model.compounds
    assert "C3" in model.compounds
    assert "C5" in model.compounds
    assert "INT" in model.compounds


def test_degradation_increases_with_lap_age():
    model = TyreDegradationModel()
    deg_lap1 = model.calculate_lap_degradation("C3", tyre_age_laps=1)
    deg_lap15 = model.calculate_lap_degradation("C3", tyre_age_laps=15)
    deg_lap30 = model.calculate_lap_degradation("C3", tyre_age_laps=30)

    assert deg_lap1["pace_delta_seconds"] < deg_lap15["pace_delta_seconds"]
    assert deg_lap15["pace_delta_seconds"] < deg_lap30["pace_delta_seconds"]


def test_tyre_cliff_detection():
    model = TyreDegradationModel()
    # C4 cliff nominal lap is 18
    fresh_c4 = model.calculate_lap_degradation("C4", tyre_age_laps=10)
    assert fresh_c4["is_past_cliff"] is False

    past_cliff_c4 = model.calculate_lap_degradation("C4", tyre_age_laps=22)
    assert past_cliff_c4["is_past_cliff"] is True
    assert past_cliff_c4["warning"] is not None


def test_undercut_window_evaluation():
    model = TyreDegradationModel()
    # If trailing by 0.8s on worn Mediums (age 20) vs fitting fresh Hards
    eval_close = model.evaluate_undercut_window(
        driver_current_age=20,
        driver_compound="C3",
        rival_gap_s=0.8,
        fresh_compound="C2",
    )
    assert "outlap_pace_advantage_s" in eval_close
    assert "undercut_successful" in eval_close


def test_simulate_stint_trajectory():
    model = TyreDegradationModel()
    stint = model.simulate_stint_curve("C2", total_laps=25)
    assert len(stint) == 25
    assert stint[0]["tyre_age_laps"] == 1
    assert stint[-1]["tyre_age_laps"] == 25
