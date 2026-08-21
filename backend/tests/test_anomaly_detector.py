"""Unit tests for Telemetry Sensor Fusion Autoencoder and Failure Predictor."""
import pytest
from backend.app.intelligence.anomaly_detector import telemetry_anomaly_detector, TelemetryAnomalyReport
from backend.app.simulator.engine import RaceSimulator


def test_anomaly_detector_nominal_evaluation():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.get_state()
    player = state.cars[0]

    report = telemetry_anomaly_detector.evaluate_telemetry(player, lap=1)
    assert isinstance(report, TelemetryAnomalyReport)
    assert len(report.channels) == 16
    assert len(report.components) > 0
    assert not report.is_anomaly_critical
    assert report.overall_anomaly_score < 40.0


def test_anomaly_detector_with_injected_chaos():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.get_state()
    player = state.cars[0]

    # Inject severe MGU-K and Turbo overheating anomalies
    injections = {
        "mguk_stator_temp_c": 55.0,
        "turbo_boost_pressure_bar": 1.2,
    }

    report = telemetry_anomaly_detector.evaluate_telemetry(
        player,
        lap=5,
        injected_anomalies=injections,
    )

    assert report.is_anomaly_critical
    mguk_channel = next(c for c in report.channels if c.channel_name == "mguk_stator_temp_c")
    assert mguk_channel.status == "CRITICAL"
    assert mguk_channel.anomaly_score > 70.0

    mguk_comp = next(c for c in report.components if "MGU-K" in c.component)
    assert mguk_comp.anomaly_detected
    assert mguk_comp.failure_risk_pct > 50.0
