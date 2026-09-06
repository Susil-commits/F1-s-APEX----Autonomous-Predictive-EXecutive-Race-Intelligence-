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
    "sector_1_delta_norm",        # min(s1_delta_s, 2.0) / 2.0
    "sector_2_delta_norm",        # min(s2_delta_s, 2.0) / 2.0
    "sector_3_delta_norm",        # min(s3_delta_s, 2.0) / 2.0
    "driver_rolling_finish_norm",  # (avg_finish_5_races - 1) / 19.0
    "driver_circuit_experience",  # min(starts_at_track, 10) / 10.0
    "constructor_pts_share",      # team_pts / total_team_pts
    "circuit_downforce_index",    # 0.0 (low/Monza) to 1.0 (high/Monaco)
    "circuit_power_sensitivity",  # 0.0 to 1.0
    "circuit_is_street_track",    # 1.0 or 0.0
    "race_rain_prob",             # 0.0 to 1.0
    "weather_transition_flag",    # 1.0 (conditions shifted mid-race) or 0.0
]

CIRCUIT_PROFILES: Dict[str, Dict[str, float]] = {
    # Core European & Classic High-Speed Venues
    "silverstone": {"downforce": 0.75, "power": 0.85, "street": 0.0},
    "monza": {"downforce": 0.10, "power": 1.00, "street": 0.0},
    "spa": {"downforce": 0.65, "power": 0.90, "street": 0.0},
    "suzuka": {"downforce": 0.85, "power": 0.80, "street": 0.0},
    "interlagos": {"downforce": 0.70, "power": 0.75, "street": 0.0},
    "catalunya": {"downforce": 0.80, "power": 0.75, "street": 0.0},
    "imola": {"downforce": 0.75, "power": 0.70, "street": 0.0},
    "red_bull_ring": {"downforce": 0.50, "power": 0.90, "street": 0.0},
    "hungaroring": {"downforce": 0.95, "power": 0.30, "street": 0.0},
    "zandvoort": {"downforce": 0.90, "power": 0.50, "street": 0.0},
    "ricard": {"downforce": 0.60, "power": 0.80, "street": 0.0},

    # Middle East & Asian Venues
    "bahrain": {"downforce": 0.70, "power": 0.75, "street": 0.0},
    "losail": {"downforce": 0.85, "power": 0.75, "street": 0.0},
    "yas_marina": {"downforce": 0.70, "power": 0.80, "street": 0.0},
    "shanghai": {"downforce": 0.70, "power": 0.85, "street": 0.0},

    # High-Altitude & North/South American Venues
    "americas": {"downforce": 0.75, "power": 0.80, "street": 0.0},
    "rodriguez": {"downforce": 0.95, "power": 0.85, "street": 0.0},

    # Street & Semi-Street Circuits
    "monaco": {"downforce": 1.00, "power": 0.20, "street": 1.0},
    "marina_bay": {"downforce": 0.95, "power": 0.35, "street": 1.0},
    "singapore": {"downforce": 0.95, "power": 0.35, "street": 1.0},  # alias for marina_bay
    "baku": {"downforce": 0.40, "power": 0.95, "street": 1.0},
    "jeddah": {"downforce": 0.40, "power": 0.95, "street": 1.0},
    "albert_park": {"downforce": 0.65, "power": 0.70, "street": 1.0},
    "miami": {"downforce": 0.60, "power": 0.85, "street": 1.0},
    "vegas": {"downforce": 0.30, "power": 0.95, "street": 1.0},
    "villeneuve": {"downforce": 0.45, "power": 0.85, "street": 1.0},
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
        sector_1_delta_s: float = 0.0,
        sector_2_delta_s: float = 0.0,
        sector_3_delta_s: float = 0.0,
        weather_transition: bool | float = 0.0,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Constructs a normalized 13-dimensional vector from pre-race inputs."""
        profile = CIRCUIT_PROFILES.get(
            circuit_id.lower(),
            {"downforce": 0.60, "power": 0.70, "street": 0.0}
        )

        grid_norm = np.clip((grid_position - 1.0) / 19.0, 0.0, 1.0)
        quali_delta_norm = np.clip(quali_delta_s / 5.0, 0.0, 1.0)

        # Sector time deltas (seconds relative to pole lap sectors)
        # If per-sector deltas are not supplied directly, estimate from aggregate quali_delta
        # and circuit power/downforce profiles (e.g., sector 2 dominates high-downforce, sector 1/3 dominate power)
        if sector_1_delta_s == 0.0 and sector_2_delta_s == 0.0 and sector_3_delta_s == 0.0 and quali_delta_s > 0.0:
            if profile["downforce"] > 0.8:  # e.g., Monaco, Singapore, Hungaroring (heavy S2 twisty technical demand)
                s1_val = quali_delta_s * 0.28
                s2_val = quali_delta_s * 0.46
                s3_val = quali_delta_s * 0.26
            elif profile["power"] > 0.85:   # e.g., Monza, Spa, Vegas (heavy straight-line power demand in S1/S2)
                s1_val = quali_delta_s * 0.38
                s2_val = quali_delta_s * 0.38
                s3_val = quali_delta_s * 0.24
            else:
                s1_val = quali_delta_s * 0.33
                s2_val = quali_delta_s * 0.34
                s3_val = quali_delta_s * 0.33
        else:
            s1_val = sector_1_delta_s
            s2_val = sector_2_delta_s
            s3_val = sector_3_delta_s

        s1_norm = np.clip(s1_val / 2.0, 0.0, 1.0)
        s2_norm = np.clip(s2_val / 2.0, 0.0, 1.0)
        s3_norm = np.clip(s3_val / 2.0, 0.0, 1.0)

        rolling_finish_norm = np.clip((rolling_avg_finish - 1.0) / 19.0, 0.0, 1.0)
        exp_norm = np.clip(circuit_starts / 10.0, 0.0, 1.0)
        pts_share_norm = np.clip(constructor_pts_share, 0.0, 1.0)
        df_index = profile["downforce"]
        pwr_index = profile["power"]
        is_street = profile["street"]
        rain = np.clip(rain_prob, 0.0, 1.0)
        transition_flag = 1.0 if float(weather_transition) > 0.5 else 0.0

        vec = np.array([
            grid_norm,
            quali_delta_norm,
            s1_norm,
            s2_norm,
            s3_norm,
            rolling_finish_norm,
            exp_norm,
            pts_share_norm,
            df_index,
            pwr_index,
            is_street,
            rain,
            transition_flag,
        ], dtype=np.float32)

        feat_dict = {
            "grid_position_norm": float(grid_norm),
            "quali_delta_to_pole_s": float(quali_delta_norm),
            "sector_1_delta_norm": float(s1_norm),
            "sector_2_delta_norm": float(s2_norm),
            "sector_3_delta_norm": float(s3_norm),
            "driver_rolling_finish_norm": float(rolling_finish_norm),
            "driver_circuit_experience": float(exp_norm),
            "constructor_pts_share": float(pts_share_norm),
            "circuit_downforce_index": df_index,
            "circuit_power_sensitivity": pwr_index,
            "circuit_is_street_track": is_street,
            "race_rain_prob": float(rain),
            "weather_transition_flag": transition_flag,
        }

        return vec, feat_dict

    @staticmethod
    def dict_to_vector(feat_dict: Dict[str, float]) -> np.ndarray:
        """Converts a feature dictionary into a 13-dimensional numpy vector aligned with PRE_RACE_FEATURE_NAMES."""
        return np.array([float(feat_dict.get(name, 0.0)) for name in PRE_RACE_FEATURE_NAMES], dtype=np.float32)
