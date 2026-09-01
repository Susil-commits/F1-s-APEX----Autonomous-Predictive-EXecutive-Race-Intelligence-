"""APEX Intelligence Predictive Models (Tier 2).

Includes tyre degradation, weather forecasting, driver performance, vehicle health,
PINN thermal residual compensators, and TreeSHAP explainers.
"""
from backend.app.intelligence.tyre_model import TyreModel
from backend.app.intelligence.weather_model import WeatherModel
from backend.app.intelligence.driver_model import DriverModel
from backend.app.intelligence.opponent_model import OpponentModel
from backend.app.intelligence.vehicle_health_model import VehicleHealthModel
from backend.app.intelligence.pinn_tyre_residual import PINNTyreResidualCompensator
from backend.app.intelligence.shap_explainer import TreeSHAPExplainer
from backend.app.intelligence.conformal_calibration import ConformalCalibrator
from backend.app.intelligence.anomaly_detector import AnomalyDetector

__all__ = [
    "TyreModel",
    "WeatherModel",
    "DriverModel",
    "OpponentModel",
    "VehicleHealthModel",
    "PINNTyreResidualCompensator",
    "TreeSHAPExplainer",
    "ConformalCalibrator",
    "AnomalyDetector",
]
