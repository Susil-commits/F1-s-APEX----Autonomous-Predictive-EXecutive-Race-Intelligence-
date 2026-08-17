"""Unit tests for Physics-Informed Neural Network (PINN) Tyre Residual Compensator."""
import pytest
from backend.app.simulator.models import TyreCompound, DrivingMode
from backend.app.intelligence.pinn_tyre_residual import PINNTyreResidualCompensator
from backend.app.intelligence.tyre_model import TyreModel


def test_pinn_singleton_initialization():
    """Validates singleton instance retrieval and model readiness."""
    pinn1 = PINNTyreResidualCompensator.get_instance()
    pinn2 = PINNTyreResidualCompensator.get_instance()
    assert pinn1 is pinn2
    assert pinn1.model is not None


def test_pinn_predict_residual():
    """Validates that residual prediction returns non-negative delta loss."""
    pinn = PINNTyreResidualCompensator.get_instance()
    delta_s = pinn.predict_residual_delta_s(
        compound=TyreCompound.SOFT,
        current_wear_pct=72.0,
        mode=DrivingMode.PUSH,
        track_name="bahrain",
        track_temp_c=45.0,
        rain_intensity=0.0,
    )
    assert isinstance(delta_s, float)
    assert delta_s >= 0.0


def test_pinn_fine_tuning_on_session_telemetry():
    """Validates online fine-tuning loop on streaming session telemetry batches."""
    pinn = PINNTyreResidualCompensator.get_instance()
    samples = [
        {
            "compound": TyreCompound.MEDIUM,
            "wear_pct": 55.0,
            "mode": DrivingMode.NORMAL,
            "track_name": "silverstone",
            "track_temp_c": 32.0,
            "rain_intensity": 0.0,
            "actual_lap_time_loss": 0.35,
        },
        {
            "compound": TyreCompound.HARD,
            "wear_pct": 70.0,
            "mode": DrivingMode.PUSH,
            "track_name": "silverstone",
            "track_temp_c": 35.0,
            "rain_intensity": 0.0,
            "actual_lap_time_loss": 0.65,
        },
    ]

    loss = pinn.fine_tune_on_session_telemetry(samples, epochs=3)
    assert isinstance(loss, float)
    assert loss >= 0.0


def test_tyre_model_predict_lap_time_loss_pinn():
    """Validates TyreModel hybrid PINN method integration."""
    loss = TyreModel.predict_lap_time_loss_pinn(
        compound=TyreCompound.SOFT,
        wear_pct=70.0,
        mode=DrivingMode.PUSH,
        track_name="bahrain",
    )
    assert isinstance(loss, float)
    assert loss > 0.5  # Significant degradation on worn soft tyres at Bahrain
