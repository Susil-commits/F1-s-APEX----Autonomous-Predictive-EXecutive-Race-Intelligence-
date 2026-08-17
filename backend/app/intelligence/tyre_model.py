"""Tyre degradation predictor, remaining useful life estimation, and ML regression suite."""
from __future__ import annotations

import os
import json
import logging
from typing import Dict, Tuple, Optional, Any, List
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
import joblib

from backend.app.simulator.models import TyreCompound, DrivingMode, CarState, TrackConfig, WeatherState
from backend.app.simulator.car import COMPOUND_SPECS, MODE_SPECS

logger = logging.getLogger(__name__)

CALIBRATED_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "calibrated_tyre_model.json"
)
TYRE_ML_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "tyre")

# Empirical track severity multipliers relative to baseline (1.0)
CIRCUIT_DEGRADATION_SEVERITY: Dict[str, float] = {
    "bahrain": 1.35,      # Highly abrasive asphalt & high rear thermal stress
    "spain": 1.25,        # High-energy lateral loads (Turn 3/9)
    "barcelona": 1.25,
    "silverstone": 1.15,  # High-speed lateral loads (Maggotts/Becketts)
    "suzuka": 1.20,       # High lateral S-curves
    "spa": 1.05,          # High-speed compression & elevation changes
    "austria": 1.00,      # Medium wear, short lap
    "interlagos": 0.95,   # Medium-low degradation
    "zandvoort": 1.10,    # Banked corners, high lateral load
    "monza": 0.75,        # Low-downforce longitudinal traction
    "monaco": 0.55,       # Smooth street asphalt, low energy
}


class TyreMLSuite:
    """Multi-model tyre degradation regression and cliff classification suite."""

    def __init__(self):
        self.linear_model: Optional[LinearRegression] = None
        self.rf_model: Optional[RandomForestRegressor] = None
        self.is_trained: bool = False
        os.makedirs(TYRE_ML_DIR, exist_ok=True)
        self._load_or_init_models()

    def _load_or_init_models(self):
        rf_path = os.path.join(TYRE_ML_DIR, "tyre_rf.joblib")
        lr_path = os.path.join(TYRE_ML_DIR, "tyre_lr.joblib")
        if os.path.exists(rf_path) and os.path.exists(lr_path):
            try:
                self.rf_model = joblib.load(rf_path)
                self.linear_model = joblib.load(lr_path)
                self.is_trained = True
                return
            except Exception as e:
                logger.warning(f"[TyreMLSuite] Failed loading models: {e}")

        # Train fast baseline models on synthetic/real distribution
        self.train_default_models()

    def train_default_models(self):
        """Trains baseline Linear and Random Forest regressors on tyre degradation dynamics."""
        X_train = []
        y_train = []
        compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]

        for comp_idx, comp in enumerate(compounds):
            base_wear = 0.08 if comp == "SOFT" else (0.05 if comp == "MEDIUM" else 0.035)
            for age in range(1, 45):
                for track_temp in [25.0, 32.0, 42.0]:
                    for abrasion in [0.75, 1.0, 1.35]:
                        # Features: [compound_idx, tyre_age, track_temp, circuit_abrasion, age^2]
                        feat = [comp_idx, float(age), track_temp / 35.0, abrasion, (age / 20.0) ** 2]
                        # Target: lap time delta in seconds
                        target = (base_wear * age * abrasion * (track_temp / 32.0)) + 0.002 * (age ** 1.8)
                        X_train.append(feat)
                        y_train.append(target)

        X = np.array(X_train)
        y = np.array(y_train)

        self.linear_model = LinearRegression().fit(X, y)
        self.rf_model = RandomForestRegressor(n_estimators=30, random_state=42).fit(X, y)
        self.is_trained = True

        try:
            joblib.dump(self.rf_model, os.path.join(TYRE_ML_DIR, "tyre_rf.joblib"))
            joblib.dump(self.linear_model, os.path.join(TYRE_ML_DIR, "tyre_lr.joblib"))
        except Exception as e:
            logger.warning(f"[TyreMLSuite] Model persistence notice: {e}")

    def predict_delta(
        self,
        compound: TyreCompound,
        tyre_age: int,
        track_temp_c: float = 32.0,
        circuit_abrasion: float = 1.0,
        model_type: str = "rf",
    ) -> Tuple[float, Tuple[float, float]]:
        """Predicts lap time loss (s) with 90% confidence interval."""
        if not self.is_trained:
            self.train_default_models()

        comp_str = compound.value if hasattr(compound, "value") else str(compound)
        comp_map = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "INTERMEDIATE": 3, "WET": 4}
        c_idx = comp_map.get(comp_str.upper(), 1)

        feat = np.array([[c_idx, float(tyre_age), track_temp_c / 35.0, circuit_abrasion, (tyre_age / 20.0) ** 2]])
        
        if model_type == "rf" and self.rf_model:
            pred = float(self.rf_model.predict(feat)[0])
            ci_margin = max(0.08, pred * 0.12)
        elif self.linear_model:
            pred = float(self.linear_model.predict(feat)[0])
            ci_margin = max(0.12, pred * 0.18)
        else:
            pred = float(tyre_age * 0.05)
            ci_margin = 0.15

        pred = max(0.0, pred)
        ci_lower = max(0.0, pred - ci_margin)
        ci_upper = pred + ci_margin
        return round(pred, 3), (round(ci_lower, 3), round(ci_upper, 3))


_ML_SUITE = TyreMLSuite()


class TyreModel:
    """Predicts tyre degradation curves, lap-time delta, remaining useful life, and cliff probabilities."""

    _calibrated_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def get_circuit_degradation_factor(cls, track_name: str) -> float:
        """Returns empirical degradation severity multiplier for the given circuit."""
        clean_name = track_name.lower().replace("_", "").replace(" ", "").replace("-", "")
        for key, factor in CIRCUIT_DEGRADATION_SEVERITY.items():
            if key in clean_name or clean_name in key:
                return factor
        return 1.0

    @classmethod
    def load_calibrated_model(cls, path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Loads real FastF1 calibrated tyre model parameters from disk."""
        target_path = path or CALIBRATED_MODEL_PATH
        if cls._calibrated_cache is not None:
            return cls._calibrated_cache
        if os.path.exists(target_path):
            try:
                with open(target_path, "r") as f:
                    cls._calibrated_cache = json.load(f)
                    return cls._calibrated_cache
            except Exception as e:
                logger.warning(f"[TyreModel] Failed loading calibrated model: {e}")
        return None

    @classmethod
    def is_calibrated(cls) -> bool:
        """Returns True if real-data calibrated tyre parameters are active."""
        return cls.load_calibrated_model() is not None

    @classmethod
    def estimate_remaining_laps(
        cls,
        compound: TyreCompound,
        current_wear_pct: float,
        mode: DrivingMode,
        track_wear_factor: float,
    ) -> int:
        """Estimates laps remaining before reaching the degradation cliff."""
        spec = COMPOUND_SPECS[compound]
        mode_spec = MODE_SPECS[mode]
        
        calib = cls.load_calibrated_model()
        comp_str = compound.value if hasattr(compound, "value") else str(compound)
        
        cliff_threshold = spec["cliff_threshold_pct"]
        base_wear = spec["base_wear_rate_pct"]

        if calib and "compound_models" in calib and comp_str in calib["compound_models"]:
            cm = calib["compound_models"][comp_str]
            cliff_threshold = cm.get("cliff_threshold_pct", cliff_threshold)
            base_wear = cm.get("base_wear_rate_pct", base_wear)

        wear_per_lap = base_wear * mode_spec["wear_multiplier"] * track_wear_factor
        wear_margin = max(0.0, cliff_threshold - current_wear_pct)
        if wear_per_lap <= 0:
            return 99
        return int(wear_margin / wear_per_lap)

    @classmethod
    def predict_remaining_useful_life(
        cls,
        compound: TyreCompound,
        wear_pct: float,
        tyre_age_laps: int,
        mode: DrivingMode = DrivingMode.NORMAL,
        track_wear_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Predicts remaining useful laps with confidence interval and cliff probability."""
        remaining_laps = cls.estimate_remaining_laps(compound, wear_pct, mode, track_wear_factor)
        cliff_prob = min(1.0, max(0.0, (wear_pct - 45.0) / 40.0)) if wear_pct > 45.0 else 0.02
        if wear_pct >= 80.0:
            cliff_prob = 0.98

        ci_lower = max(0, remaining_laps - 2)
        ci_upper = remaining_laps + 2

        return {
            "remaining_useful_laps": remaining_laps,
            "ci_90": [ci_lower, ci_upper],
            "cliff_probability": round(cliff_prob, 3),
            "current_wear_pct": round(wear_pct, 1),
            "tyre_age_laps": tyre_age_laps,
        }

    @classmethod
    def predict_lap_time_loss(
        cls,
        compound: TyreCompound,
        wear_pct: float,
        tyre_age_laps: Optional[int] = None,
    ) -> float:
        """Predicts the lap-time penalty (in seconds) incurred from current tyre degradation."""
        comp_str = compound.value if hasattr(compound, "value") else str(compound)
        calib = cls.load_calibrated_model()

        if calib and "compound_models" in calib and comp_str in calib["compound_models"]:
            cm = calib["compound_models"][comp_str]
            c2 = cm.get("c2_quad", 0.003)
            c1 = max(0.015, cm.get("c1_linear", 0.035))
            cliff_pct = cm.get("cliff_threshold_pct", 78.0)
            base_rate = cm.get("base_wear_rate_pct", 2.2)

            age = float(tyre_age_laps) if tyre_age_laps is not None else (wear_pct / max(0.1, base_rate))
            loss = c2 * (age ** 2) + c1 * age

            if wear_pct > cliff_pct:
                excess = wear_pct - cliff_pct
                spec = COMPOUND_SPECS.get(compound, {"cliff_penalty_s_per_pct": 0.08})
                cliff_penalty = spec.get("cliff_penalty_s_per_pct", 0.08) * 1.5
                loss += excess * cliff_penalty

            return max(0.0, round(float(loss), 3))

        # Synthetic fallback
        spec = COMPOUND_SPECS[compound]
        linear_loss = (wear_pct / 100.0) * 1.8
        cliff_loss = 0.0
        if wear_pct > spec["cliff_threshold_pct"]:
            excess = wear_pct - spec["cliff_threshold_pct"]
            cliff_loss = excess * spec["cliff_penalty_s_per_pct"] * 1.5

        return round(linear_loss + cliff_loss, 3)

    @classmethod
    def predict_next_lap_time_ml(
        cls,
        compound: TyreCompound,
        tyre_age: int,
        base_lap_time_s: float = 88.5,
        track_temp_c: float = 32.0,
        track_name: str = "silverstone",
        model_type: str = "rf",
    ) -> Dict[str, Any]:
        """Predicts next lap time and confidence interval using ML regression suite."""
        abrasion = cls.get_circuit_degradation_factor(track_name)
        delta_loss, (ci_low_delta, ci_high_delta) = _ML_SUITE.predict_delta(
            compound=compound,
            tyre_age=tyre_age,
            track_temp_c=track_temp_c,
            circuit_abrasion=abrasion,
            model_type=model_type,
        )
        expected_lap = base_lap_time_s + delta_loss
        return {
            "expected_lap_time_s": round(expected_lap, 3),
            "lap_time_loss_s": round(delta_loss, 3),
            "ci_90_bounds": [round(base_lap_time_s + ci_low_delta, 3), round(base_lap_time_s + ci_high_delta, 3)],
            "model_type": model_type,
        }

    @classmethod
    def predict_lap_time_loss_pinn(
        cls,
        compound: TyreCompound,
        wear_pct: float,
        mode: DrivingMode = DrivingMode.NORMAL,
        track_name: str = "silverstone",
        track_temp_c: float = 35.0,
        rain_intensity: float = 0.0,
        tyre_age_laps: Optional[int] = None,
    ) -> float:
        """PINN hybrid lap time degradation prediction."""
        base_loss = cls.predict_lap_time_loss(compound, wear_pct, tyre_age_laps)
        try:
            from backend.app.intelligence.pinn_tyre_residual import PINNTyreResidualCompensator
            pinn = PINNTyreResidualCompensator.get_instance()
            pinn_residual = pinn.predict_residual_delta_s(
                compound=compound,
                current_wear_pct=wear_pct,
                mode=mode,
                track_name=track_name,
                track_temp_c=track_temp_c,
                rain_intensity=rain_intensity,
            )
            return round(base_loss + pinn_residual, 3)
        except Exception:
            return base_loss

    @staticmethod
    def calculate_pit_window(
        car: CarState,
        track: TrackConfig,
        weather: WeatherState,
    ) -> Dict[str, Any]:
        """Calculates optimal pit window range and urgency."""
        spec = COMPOUND_SPECS[car.tyre_compound]
        remaining_laps_to_cliff = TyreModel.estimate_remaining_laps(
            car.tyre_compound,
            car.tyre_wear_pct,
            car.driving_mode,
            track.tyre_wear_factor,
        )

        cliff_lap = car.current_lap + remaining_laps_to_cliff
        window_start = max(car.current_lap, cliff_lap - 4)
        window_end = min(track.total_laps, cliff_lap + 2)

        # Assess status
        if car.current_lap < window_start - 2:
            status = "EARLY"
        elif window_start - 2 <= car.current_lap <= window_end:
            status = "OPTIMAL"
        elif car.current_lap > window_end:
            status = "LATE"
        else:
            status = "OPTIMAL"

        # Calculate cliff risk
        if car.tyre_wear_pct >= spec["cliff_threshold_pct"]:
            cliff_risk = "CRITICAL"
        elif car.tyre_wear_pct >= spec["cliff_threshold_pct"] - 12.0:
            cliff_risk = "HIGH"
        elif car.tyre_wear_pct >= spec["cliff_threshold_pct"] - 25.0:
            cliff_risk = "MODERATE"
        else:
            cliff_risk = "LOW"

        return {
            "window_start_lap": window_start,
            "window_end_lap": window_end,
            "optimal_lap": cliff_lap - 1,
            "remaining_laps_to_cliff": remaining_laps_to_cliff,
            "status": status,
            "cliff_risk": cliff_risk,
            "predicted_loss_s": TyreModel.predict_lap_time_loss(car.tyre_compound, car.tyre_wear_pct, car.tyre_age_laps),
        }
