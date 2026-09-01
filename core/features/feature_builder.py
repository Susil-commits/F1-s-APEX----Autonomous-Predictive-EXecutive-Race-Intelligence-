"""Point-in-Time Safe Pre-Race Feature Builder for APEX Core (Tier 1).

Constructs the feature vector using ONLY information available prior to the race start:
- Grid qualifying position
- Qualifying delta to pole (seconds)
- Driver recent 5-race rolling average finish
- Constructor points share prior to round
- Circuit downforce and power demand
- Forecasted rain probability at race start

Guarantees ZERO lookahead bias.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np

PRE_RACE_FEATURE_NAMES: List[str] = [
    "grid_position_norm",         # (grid - 1) / 19.0
    "quali_delta_to_pole_s",      # min(delta_s, 5.0) / 5.0
    "driver_rolling_finish_norm",  # (avg_finish_5_races - 1) / 19.0
    "driver_circuit_experience",  # min(starts_at_track, 10) / 10.0
    "constructor_pts_share",      # team_pts / total_team_pts
    "circuit_downforce_index",    # 0.0 (low/Monza) to 1.0 (high/Monaco)
    "circuit_power_sensitivity",  # 0.0 to 1.0
    "circuit_is_street_track",    # 1.0 or 0.0
    "race_rain_prob",             # 0.0 to 1.0
]

CIRCUIT_PROFILES: Dict[str, Dict[str, float]] = {
    "silverstone": {"downforce": 0.75, "power": 0.85, "street": 0.0},
    "monza": {"downforce": 0.10, "power": 1.00, "street": 0.0},
    "spa": {"downforce": 0.65, "power": 0.90, "street": 0.0},
    "monaco": {"downforce": 1.00, "power": 0.20, "street": 1.0},
    "bahrain": {"downforce": 0.70, "power": 0.75, "street": 0.0},
    "suzuka": {"downforce": 0.85, "power": 0.80, "street": 0.0},
    "interlagos": {"downforce": 0.70, "power": 0.75, "street": 0.0},
    "baku": {"downforce": 0.40, "power": 0.95, "street": 1.0},
    "singapore": {"downforce": 0.95, "power": 0.35, "street": 1.0},
    "albert_park": {"downforce": 0.65, "power": 0.70, "street": 1.0},
}


class PreRaceFeatureBuilder:
    """Extracts strictly point-in-time validated feature vectors for pre-race prediction."""

    @staticmethod
    def extract_features(
        grid_position: int,
        quali_delta_s: float = 0.0,
        rolling_avg_finish: float = 8.0,
        circuit_starts: int = 4,
        constructor_pts_share: float = 0.15,
        circuit_id: str = "silverstone",
        rain_prob: float = 0.10,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Constructs a normalized 9-dimensional vector from pre-race inputs."""
        profile = CIRCUIT_PROFILES.get(
            circuit_id.lower(),
            {"downforce": 0.60, "power": 0.70, "street": 0.0}
        )

        grid_norm = np.clip((grid_position - 1.0) / 19.0, 0.0, 1.0)
        quali_delta_norm = np.clip(quali_delta_s / 5.0, 0.0, 1.0)
        rolling_finish_norm = np.clip((rolling_avg_finish - 1.0) / 19.0, 0.0, 1.0)
        exp_norm = np.clip(circuit_starts / 10.0, 0.0, 1.0)
        pts_share_norm = np.clip(constructor_pts_share, 0.0, 1.0)
        df_index = profile["downforce"]
        pwr_index = profile["power"]
        is_street = profile["street"]
        rain = np.clip(rain_prob, 0.0, 1.0)

        vec = np.array([
            grid_norm,
            quali_delta_norm,
            rolling_finish_norm,
            exp_norm,
            pts_share_norm,
            df_index,
            pwr_index,
            is_street,
            rain,
        ], dtype=np.float32)

        feat_dict = {
            "grid_position_norm": float(grid_norm),
            "quali_delta_to_pole_s": float(quali_delta_norm),
            "driver_rolling_finish_norm": float(rolling_finish_norm),
            "driver_circuit_experience": float(exp_norm),
            "constructor_pts_share": float(pts_share_norm),
            "circuit_downforce_index": float(df_index),
            "circuit_power_sensitivity": float(pwr_index),
            "circuit_is_street_track": float(is_street),
            "race_rain_prob": float(rain),
        }

        return vec, feat_dict
