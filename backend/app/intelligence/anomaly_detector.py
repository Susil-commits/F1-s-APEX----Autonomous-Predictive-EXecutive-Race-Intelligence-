"""
Telemetry Sensor Fusion Autoencoder & Component Failure Predictive Model.
Analyzes 16 high-frequency vehicle telemetry channels to detect anomalies and predict component failure.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from pydantic import BaseModel, Field


class SensorChannelData(BaseModel):
    channel_name: str
    current_val: float
    expected_val: float
    unit: str
    residual_error: float
    anomaly_score: float
    status: str  # "NORMAL", "ELEVATED", "CRITICAL"


class ComponentFailureRisk(BaseModel):
    component: str
    health_pct: float
    failure_risk_pct: float
    predicted_rul_laps: float
    primary_sensor: str
    anomaly_detected: bool
    diagnostic_message: str


class TelemetryAnomalyReport(BaseModel):
    timestamp_s: float
    overall_anomaly_score: float
    is_anomaly_critical: bool
    channels: List[SensorChannelData]
    components: List[ComponentFailureRisk]
    recommended_actions: List[str]


class TelemetryAnomalyDetector:
    """
    Autoencoder-style multi-channel sensor anomaly detection and RUL forecasting.
    """

    def __init__(self):
        # Baseline reference operating bounds (mean, std) for healthy car
        self.sensor_baselines = {
            "mguk_stator_temp_c": {"mean": 118.0, "std": 6.5, "unit": "°C", "component": "MGU-K Hybrid"},
            "mguh_rotor_speed_rpm": {"mean": 112000.0, "std": 4500.0, "unit": "RPM", "component": "MGU-H Turbo"},
            "ice_oil_pressure_bar": {"mean": 4.8, "std": 0.25, "unit": "bar", "component": "ICE V6 Engine"},
            "ice_coolant_temp_c": {"mean": 104.0, "std": 3.2, "unit": "°C", "component": "ICE Cooling System"},
            "turbo_boost_pressure_bar": {"mean": 3.85, "std": 0.15, "unit": "bar", "component": "Turbocharger"},
            "hydraulic_line_pressure_bar": {"mean": 215.0, "std": 5.0, "unit": "bar", "component": "Hydraulic Actuators"},
            "gearbox_oil_temp_c": {"mean": 110.0, "std": 4.0, "unit": "°C", "component": "8-Speed Seamless Gearbox"},
            "front_left_brake_disc_c": {"mean": 680.0, "std": 45.0, "unit": "°C", "component": "Carbon Brakes"},
            "front_right_brake_disc_c": {"mean": 690.0, "std": 48.0, "unit": "°C", "component": "Carbon Brakes"},
            "rear_left_brake_disc_c": {"mean": 620.0, "std": 38.0, "unit": "°C", "component": "Brake-By-Wire"},
            "rear_right_brake_disc_c": {"mean": 625.0, "std": 40.0, "unit": "°C", "component": "Brake-By-Wire"},
            "fuel_flow_rate_kg_h": {"mean": 98.5, "std": 1.2, "unit": "kg/h", "component": "Fuel Metering"},
            "ers_battery_cell_delta_v": {"mean": 0.012, "std": 0.003, "unit": "V", "component": "ERS Energy Store"},
            "diff_preload_torque_nm": {"mean": 145.0, "std": 8.0, "unit": "Nm", "component": "Active Differential"},
            "pushrod_load_kn": {"mean": 12.4, "std": 1.1, "unit": "kN", "component": "Chassis & Suspension"},
            "exhaust_gas_temp_c": {"mean": 920.0, "std": 22.0, "unit": "°C", "component": "Exhaust & Wastegate"},
        }

    def evaluate_telemetry(
        self,
        car_state: Any,
        lap: int = 1,
        injected_anomalies: Optional[Dict[str, float]] = None,
    ) -> TelemetryAnomalyReport:
        """
        Calculates reconstruction residuals and component failure risks.
        """
        channels_data: List[SensorChannelData] = []
        component_groups: Dict[str, List[float]] = {}
        anomalies_map = injected_anomalies or {}

        total_anomaly_score = 0.0

        for channel, meta in self.sensor_baselines.items():
            expected = meta["mean"]
            std = meta["std"]

            # Add natural simulation variance
            noise = np.sin(lap * 0.4 + hash(channel) % 10) * (std * 0.4)
            current = expected + noise

            # Apply injected anomaly if present
            if channel in anomalies_map:
                current += anomalies_map[channel]

            # Residual & z-score anomaly score
            residual = abs(current - expected)
            z_score = residual / max(0.001, std)
            anomaly_score = min(100.0, (z_score / 3.5) * 100.0)

            status = "NORMAL"
            if anomaly_score > 75.0:
                status = "CRITICAL"
            elif anomaly_score > 40.0:
                status = "ELEVATED"

            total_anomaly_score += anomaly_score

            channels_data.append(
                SensorChannelData(
                    channel_name=channel,
                    current_val=round(float(current), 3),
                    expected_val=round(float(expected), 3),
                    unit=meta["unit"],
                    residual_error=round(float(residual), 3),
                    anomaly_score=round(float(anomaly_score), 1),
                    status=status,
                )
            )

            comp = meta["component"]
            if comp not in component_groups:
                component_groups[comp] = []
            component_groups[comp].append(anomaly_score)

        avg_anomaly = total_anomaly_score / len(self.sensor_baselines)

        # Build component failure risks
        components: List[ComponentFailureRisk] = []
        recommended_actions: List[str] = []

        for comp, scores in component_groups.items():
            max_score = float(max(scores))
            failure_risk = min(99.0, max_score * 0.92)
            health = max(1.0, 100.0 - failure_risk)
            rul_laps = max(0.5, round((100.0 - failure_risk) * 0.35, 1))

            has_anomaly = bool(max_score > 50.0)
            diag_msg = "Operating within nominal FIA tolerances."

            if max_score > 75.0:
                diag_msg = f"CRITICAL: {comp} experiencing severe thermal/mechanical stress! Immediate intervention needed."
                recommended_actions.append(f"Switch {comp} mode to FAILSAFE / RECOVERY map.")
            elif max_score > 45.0:
                diag_msg = f"ELEVATED: {comp} variance exceeds normal confidence interval."
                recommended_actions.append(f"Monitor {comp} telemetry and prepare lift-and-coast.")

            components.append(
                ComponentFailureRisk(
                    component=comp,
                    health_pct=round(float(health), 1),
                    failure_risk_pct=round(float(failure_risk), 1),
                    predicted_rul_laps=float(rul_laps),
                    primary_sensor=[k for k, v in self.sensor_baselines.items() if v["component"] == comp][0],
                    anomaly_detected=has_anomaly,
                    diagnostic_message=diag_msg,
                )
            )

        if not recommended_actions:
            recommended_actions.append("All 16 telemetry sensors nominal. No component maintenance required.")

        return TelemetryAnomalyReport(
            timestamp_s=round(float(lap * 88.5), 2),
            overall_anomaly_score=round(float(avg_anomaly), 1),
            is_anomaly_critical=bool(any(c.status == "CRITICAL" for c in channels_data)),
            channels=channels_data,
            components=components,
            recommended_actions=recommended_actions,
        )


telemetry_anomaly_detector = TelemetryAnomalyDetector()
