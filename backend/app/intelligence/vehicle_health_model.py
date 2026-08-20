"""Vehicle Health Intelligence: Synthetic telemetry generator, Isolation Forest anomaly detection, and component health scoring."""
from __future__ import annotations

import logging
import os
from typing import Any, cast

import joblib
import numpy as np
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

HEALTH_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "health")


class VehicleTelemetrySample(BaseModel):
    """Synthetic or real vehicle health telemetry sample."""
    engine_temp_c: float
    oil_temp_c: float
    coolant_temp_c: float
    brake_temp_c: float
    battery_temp_c: float
    battery_voltage_v: float
    ers_output_kw: float
    brake_pressure_bar: float
    power_output_kw: float
    cooling_efficiency: float


class VehicleHealthReport(BaseModel):
    """Component health analysis, anomaly classification, and failure horizon."""
    overall_health_score: float # 0.0 to 100.0%
    is_anomalous: bool
    anomaly_score: float # -1.0 (severe anomaly) to +1.0 (normal)
    failure_probability: float # 0.0 to 1.0
    failure_horizon_laps: int | None # Estimated laps until mechanical failure
    subsystem_health: dict[str, float] # engine, brakes, battery, cooling (0-100)
    active_alarms: list[str]
    recommended_mitigation: str | None


class VehicleHealthIntelligence:
    """Monitors multi-sensor powertrain and chassis telemetry for anomaly detection and preventive strategy."""

    _detector: IsolationForest | None = None

    @classmethod
    def get_detector(cls) -> IsolationForest:
        if cls._detector is not None:
            return cls._detector

        os.makedirs(HEALTH_MODEL_DIR, exist_ok=True)
        model_path = os.path.join(HEALTH_MODEL_DIR, "iso_forest_health.joblib")
        if os.path.exists(model_path):
            try:
                loaded = joblib.load(model_path)
                if isinstance(loaded, IsolationForest):
                    cls._detector = loaded
                    return cls._detector
            except Exception as e:
                logger.warning(f"[VehicleHealth] Model load error: {e}")

        # Train default baseline Isolation Forest on synthetic normal/anomalous bounds
        detector = IsolationForest(n_estimators=50, contamination=cast(Any, 0.08), random_state=42)
        normal_data, _ = cls.generate_synthetic_telemetry(n_samples=500, anomaly_rate=0.05)
        X = np.array([[
            s.engine_temp_c, s.oil_temp_c, s.coolant_temp_c, s.brake_temp_c,
            s.battery_temp_c, s.battery_voltage_v, s.ers_output_kw,
            s.brake_pressure_bar, s.power_output_kw, s.cooling_efficiency
        ] for s in normal_data])
        detector.fit(X)
        cls._detector = detector
        try:
            joblib.dump(detector, model_path)
        except Exception:
            pass
        return detector

    @staticmethod
    def generate_synthetic_telemetry(
        n_samples: int = 100,
        anomaly_rate: float = 0.08,
        anomaly_type: str | None = None,
        seed: int = 42,
    ) -> tuple[list[VehicleTelemetrySample], list[bool]]:
        """
        Generates realistic F1 powertrain & chassis telemetry sequences:
        - Normal operation
        - Anomalies (overheating, voltage_drop, power_loss, brake_degradation, battery_anomaly)
        """
        rng = np.random.default_rng(seed)
        samples: list[VehicleTelemetrySample] = []
        is_anom_list: list[bool] = []

        for i in range(n_samples):
            is_anomaly = rng.uniform(0.0, 1.0) < anomaly_rate
            selected_anomaly = anomaly_type if is_anomaly else None

            # Normal baseline ranges
            eng_temp = rng.normal(105.0, 3.0)
            oil_temp = rng.normal(110.0, 2.5)
            cool_temp = rng.normal(92.0, 2.0)
            brk_temp = rng.normal(620.0, 45.0)
            bat_temp = rng.normal(52.0, 2.0)
            bat_volt = rng.normal(780.0, 12.0)
            ers_out = rng.normal(110.0, 5.0)
            brk_press = rng.normal(95.0, 8.0)
            pwr_out = rng.normal(720.0, 10.0)
            cool_eff = rng.normal(0.92, 0.03)

            if is_anomaly:
                if selected_anomaly == "overheating" or (not selected_anomaly and rng.uniform() < 0.25):
                    eng_temp += rng.uniform(25.0, 45.0)
                    oil_temp += rng.uniform(20.0, 35.0)
                    cool_eff -= rng.uniform(0.25, 0.45)
                elif selected_anomaly == "voltage_drop" or (not selected_anomaly and rng.uniform() < 0.50):
                    bat_volt -= rng.uniform(120.0, 220.0)
                    ers_out -= rng.uniform(40.0, 75.0)
                elif selected_anomaly == "power_loss" or (not selected_anomaly and rng.uniform() < 0.75):
                    pwr_out -= rng.uniform(80.0, 180.0)
                else: # brake degradation
                    brk_temp += rng.uniform(350.0, 550.0)
                    brk_press -= rng.uniform(25.0, 45.0)

            sample = VehicleTelemetrySample(
                engine_temp_c=round(float(eng_temp), 1),
                oil_temp_c=round(float(oil_temp), 1),
                coolant_temp_c=round(float(cool_temp), 1),
                brake_temp_c=round(float(brk_temp), 1),
                battery_temp_c=round(float(bat_temp), 1),
                battery_voltage_v=round(float(bat_volt), 1),
                ers_output_kw=round(float(ers_out), 1),
                brake_pressure_bar=round(float(brk_press), 1),
                power_output_kw=round(float(pwr_out), 1),
                cooling_efficiency=round(float(np.clip(cool_eff, 0.1, 1.0)), 3),
            )
            samples.append(sample)
            is_anom_list.append(is_anomaly)

        return samples, is_anom_list

    @classmethod
    def evaluate_health(cls, sample: VehicleTelemetrySample) -> VehicleHealthReport:
        """Runs Isolation Forest anomaly detection and health metric computation."""
        detector = cls.get_detector()
        X = np.array([[
            sample.engine_temp_c, sample.oil_temp_c, sample.coolant_temp_c, sample.brake_temp_c,
            sample.battery_temp_c, sample.battery_voltage_v, sample.ers_output_kw,
            sample.brake_pressure_bar, sample.power_output_kw, sample.cooling_efficiency
        ]])

        pred = detector.predict(X)[0] # -1 anomaly, +1 normal
        score = float(detector.score_samples(X)[0]) # Higher is more normal
        is_anomalous = (pred == -1)

        # Subsystem health calculation (0 - 100%)
        eng_health = np.clip(100.0 - max(0.0, sample.engine_temp_c - 115.0) * 3.5, 0.0, 100.0)
        oil_health = np.clip(100.0 - max(0.0, sample.oil_temp_c - 120.0) * 3.0, 0.0, 100.0)
        brk_health = np.clip(100.0 - max(0.0, sample.brake_temp_c - 850.0) * 0.25, 0.0, 100.0)
        bat_health = np.clip(100.0 - max(0.0, 720.0 - sample.battery_voltage_v) * 0.5, 0.0, 100.0)
        cool_health = sample.cooling_efficiency * 100.0

        overall_health = round(float(np.mean([eng_health, oil_health, brk_health, bat_health, cool_health])), 1)

        alarms: list[str] = []
        mitigation: str | None = None
        failure_prob = 0.01
        failure_horizon: int | None = None

        if sample.engine_temp_c > 125.0 or sample.cooling_efficiency < 0.65:
            alarms.append("ENGINE_OVERHEATING_CRITICAL")
            mitigation = "LIFT_AND_COAST / INCREASE_CLEAN_AIR"
            failure_prob = 0.65
            failure_horizon = 4
        if sample.brake_temp_c > 950.0:
            alarms.append("BRAKE_FADE_ALARM")
            mitigation = "SHIFT_BRAKE_BIAS_REAR"
            failure_prob = max(failure_prob, 0.45)
            failure_horizon = failure_horizon or 6
        if sample.battery_voltage_v < 680.0:
            alarms.append("ERS_VOLTAGE_DROP")
            mitigation = "HARVEST_ENERGY_MODE"
            failure_prob = max(failure_prob, 0.35)

        if overall_health < 50.0:
            failure_prob = max(failure_prob, 0.85)
            failure_horizon = min(failure_horizon or 8, 3)

        return VehicleHealthReport(
            overall_health_score=overall_health,
            is_anomalous=bool(is_anomalous),
            anomaly_score=round(score, 3),
            failure_probability=round(failure_prob, 3),
            failure_horizon_laps=failure_horizon,
            subsystem_health={
                "engine": round(eng_health, 1),
                "oil": round(oil_health, 1),
                "brakes": round(brk_health, 1),
                "battery": round(bat_health, 1),
                "cooling": round(cool_health, 1),
            },
            active_alarms=alarms,
            recommended_mitigation=mitigation,
        )
