"""Tyre degradation predictor and pit window estimation intelligence."""
from typing import Dict, Tuple, Optional, Any
import numpy as np

from backend.app.simulator.models import TyreCompound, DrivingMode, CarState, TrackConfig, WeatherState
from backend.app.simulator.car import COMPOUND_SPECS, MODE_SPECS


import os
import json
import logging

logger = logging.getLogger(__name__)

CALIBRATED_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "calibrated_tyre_model.json"
)

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


class TyreModel:
    """Predicts tyre degradation curves, lap-time delta, and remaining useful life.
    
    Prefers real-world FastF1 calibrated polynomial degradation models when available,
    falling back gracefully to domain-heuristic physical simulation equations.
    """

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
    def predict_lap_time_loss(
        cls,
        compound: TyreCompound,
        wear_pct: float,
        tyre_age_laps: Optional[int] = None,
    ) -> float:
        """Predicts the lap-time penalty (in seconds) incurred from current tyre degradation."""
        comp_str = compound.value if hasattr(compound, "value") else str(compound)
        calib = cls.load_calibrated_model()

        # Real-world FastF1 calibrated polynomial degradation path
        if calib and "compound_models" in calib and comp_str in calib["compound_models"]:
            cm = calib["compound_models"][comp_str]
            c2 = cm.get("c2_quad", 0.003)
            c1 = max(0.015, cm.get("c1_linear", 0.035))
            cliff_pct = cm.get("cliff_threshold_pct", 78.0)
            base_rate = cm.get("base_wear_rate_pct", 2.2)

            # Map wear_pct to effective tyre age if age not explicitly passed
            age = float(tyre_age_laps) if tyre_age_laps is not None else (wear_pct / max(0.1, base_rate))
            # Marginal degradation loss relative to fresh tyre
            loss = c2 * (age ** 2) + c1 * age

            # Add degradation cliff penalty when tyre exceeds cliff threshold
            if wear_pct > cliff_pct:
                excess = wear_pct - cliff_pct
                spec = COMPOUND_SPECS.get(compound, {"cliff_penalty_s_per_pct": 0.08})
                cliff_penalty = spec.get("cliff_penalty_s_per_pct", 0.08) * 1.5
                loss += excess * cliff_penalty

            return max(0.0, round(float(loss), 3))

        # Synthetic fallback equation
        spec = COMPOUND_SPECS[compound]
        linear_loss = (wear_pct / 100.0) * 1.8

        cliff_loss = 0.0
        if wear_pct > spec["cliff_threshold_pct"]:
            excess = wear_pct - spec["cliff_threshold_pct"]
            cliff_loss = excess * spec["cliff_penalty_s_per_pct"] * 1.5

        return round(linear_loss + cliff_loss, 3)

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
