"""Unit tests for Phase 3: Opponent, Driver, and Vehicle Health Intelligence."""
from backend.app.intelligence.driver_model import DriverIntelligenceEngine
from backend.app.intelligence.opponent_model import OpponentIntelligenceEngine
from backend.app.intelligence.vehicle_health_model import (
    VehicleHealthIntelligence,
    VehicleTelemetrySample,
)
from backend.app.simulator.models import (
    CarState,
    TrackCondition,
    TrackConfig,
    TyreCompound,
    WeatherState,
)


def test_opponent_intelligence_predictions():
    track = TrackConfig(name="Silverstone", total_laps=52)
    weather = WeatherState(condition=TrackCondition.DRY)

    player = CarState(car_id="car_04", driver_name="APEX AI", team_name="APEX", car_number=44, is_player=True, position=2)

    # Rival car with high tyre wear
    rival = CarState(
        car_id="car_01",
        driver_name="M. Verstappen",
        team_name="Red Bull",
        car_number=1,
        position=1,
        tyre_compound=TyreCompound.SOFT,
        tyre_age_laps=22,
        tyre_wear_pct=78.0,
        gap_to_car_behind_s=0.6,
    )

    pred = OpponentIntelligenceEngine.predict_opponent_state(rival, player, track, weather, race_lap=22)
    assert pred.pit_next_1_lap_prob > 0.60
    assert pred.defence_probability > 0.70 # Defending close gap behind
    assert pred.expected_pace_delta > 0.50


def test_driver_intelligence_profiles():
    max_prof = DriverIntelligenceEngine.get_profile("M. Verstappen")
    alonso_prof = DriverIntelligenceEngine.get_profile("F. Alonso")

    assert max_prof.pace_bias_s < 0.0
    assert alonso_prof.consistency_score > 0.90

    car = CarState(
        car_id="car_01",
        driver_name="M. Verstappen",
        team_name="Red Bull",
        car_number=1,
        position=1,
        gap_to_car_behind_s=0.4, # Chased closely
    )
    state_eval = DriverIntelligenceEngine.evaluate_driver_state(car, race_lap=45, total_laps=52)
    assert state_eval["mistake_probability"] > 0.0


def test_vehicle_health_synthetic_and_isolation_forest():
    samples, is_anoms = VehicleHealthIntelligence.generate_synthetic_telemetry(n_samples=20, anomaly_rate=0.20, seed=123)
    assert len(samples) == 20

    # Test normal sample health
    normal_sample = VehicleTelemetrySample(
        engine_temp_c=105.0,
        oil_temp_c=110.0,
        coolant_temp_c=90.0,
        brake_temp_c=600.0,
        battery_temp_c=50.0,
        battery_voltage_v=780.0,
        ers_output_kw=110.0,
        brake_pressure_bar=95.0,
        power_output_kw=720.0,
        cooling_efficiency=0.95,
    )
    norm_report = VehicleHealthIntelligence.evaluate_health(normal_sample)
    assert norm_report.overall_health_score > 80.0
    assert norm_report.failure_probability < 0.10

    # Test overheating anomaly sample
    anom_sample = VehicleTelemetrySample(
        engine_temp_c=135.0,
        oil_temp_c=140.0,
        coolant_temp_c=115.0,
        brake_temp_c=650.0,
        battery_temp_c=55.0,
        battery_voltage_v=770.0,
        ers_output_kw=100.0,
        brake_pressure_bar=90.0,
        power_output_kw=680.0,
        cooling_efficiency=0.45,
    )
    anom_report = VehicleHealthIntelligence.evaluate_health(anom_sample)
    assert anom_report.overall_health_score < 70.0
    assert "ENGINE_OVERHEATING_CRITICAL" in anom_report.active_alarms
    assert anom_report.failure_probability > 0.50
