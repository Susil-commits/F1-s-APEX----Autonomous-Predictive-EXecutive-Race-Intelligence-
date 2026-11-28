"""Point-in-Time Safe Pre-Race Feature Builder for APEX Core (Tier 1).

Constructs the feature vector using ONLY information available prior to the race start:
- Grid qualifying position
- Qualifying delta to pole (seconds)
- Driver recent 5-race rolling average finish
- Constructor points share prior to round
- Circuit downforce and power demand
- Forecasted rain probability at race start

Guarantees ZERO lookahead bias.

Note: Sector-time delta features (sector_1/2/3_delta_norm) were removed in v1.0.1
because real_prerace_dataset.csv contains no sector columns.  The heuristic
estimate (proportional split of quali_delta) added negligible signal (+0.008 MAE)
while misrepresenting data fidelity.  The 10-feature vector is the shipped model.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple
import numpy as np

PRE_RACE_FEATURE_NAMES: List[str] = [
    "grid_position_norm",          # (grid - 1) / 19.0
    "quali_delta_to_pole_s",       # min(delta_s, 5.0) / 5.0
    "driver_rolling_finish_norm",  # (avg_finish_5_races - 1) / 19.0
    "driver_circuit_experience",   # min(starts_at_track, 10) / 10.0
    "constructor_pts_share",       # team_pts / total_team_pts (strictly prior to round)
    "circuit_downforce_index",     # 0.0 (low/Monza) to 1.0 (high/Monaco)
    "circuit_power_sensitivity",   # 0.0 to 1.0
    "circuit_is_street_track",     # 1.0 or 0.0
    "race_rain_prob",              # 0.0 to 1.0
    "weather_transition_flag",     # 1.0 (conditions shifted mid-race) or 0.0
    "driver_dnf_rate",             # rolling 10-race DNF rate [0.0, 1.0]
    "constructor_race_gain_norm",  # (constructor_race_gain + 5.0) / 10.0
]

CIRCUIT_PROFILES: Dict[str, Dict[str, float]] = {
    # Core European & Classic High-Speed Venues
    "silverstone": {"downforce": 0.75, "power": 0.85, "street": 0.0, "laps": 52, "sc_probability": 0.45},
    "monza": {"downforce": 0.10, "power": 1.00, "street": 0.0, "laps": 53, "sc_probability": 0.25},
    "spa": {"downforce": 0.65, "power": 0.90, "street": 0.0, "laps": 44, "sc_probability": 0.55},
    "suzuka": {"downforce": 0.85, "power": 0.80, "street": 0.0, "laps": 53, "sc_probability": 0.45},
    "interlagos": {"downforce": 0.70, "power": 0.75, "street": 0.0, "laps": 71, "sc_probability": 0.60},
    "catalunya": {"downforce": 0.80, "power": 0.75, "street": 0.0, "laps": 66, "sc_probability": 0.30},
    "imola": {"downforce": 0.75, "power": 0.70, "street": 0.0, "laps": 63, "sc_probability": 0.50},
    "red_bull_ring": {"downforce": 0.50, "power": 0.90, "street": 0.0, "laps": 71, "sc_probability": 0.35},
    "hungaroring": {"downforce": 0.95, "power": 0.30, "street": 0.0, "laps": 70, "sc_probability": 0.30},
    "zandvoort": {"downforce": 0.90, "power": 0.50, "street": 0.0, "laps": 72, "sc_probability": 0.50},
    "ricard": {"downforce": 0.60, "power": 0.80, "street": 0.0, "laps": 53, "sc_probability": 0.30},

    # Middle East & Asian Venues
    "bahrain": {"downforce": 0.70, "power": 0.75, "street": 0.0, "laps": 57, "sc_probability": 0.35},
    "losail": {"downforce": 0.85, "power": 0.75, "street": 0.0, "laps": 57, "sc_probability": 0.40},
    "yas_marina": {"downforce": 0.70, "power": 0.80, "street": 0.0, "laps": 58, "sc_probability": 0.35},
    "shanghai": {"downforce": 0.70, "power": 0.85, "street": 0.0, "laps": 56, "sc_probability": 0.45},
    "sepang": {"downforce": 0.75, "power": 0.85, "street": 0.0, "laps": 56, "sc_probability": 0.40},

    # High-Altitude & North/South American Venues
    "americas": {"downforce": 0.75, "power": 0.80, "street": 0.0, "laps": 56, "sc_probability": 0.45},
    "austin": {"downforce": 0.75, "power": 0.80, "street": 0.0, "laps": 56, "sc_probability": 0.45},  # alias for americas
    "rodriguez": {"downforce": 0.95, "power": 0.85, "street": 0.0, "laps": 71, "sc_probability": 0.40},

    # Street & Semi-Street Circuits
    "monaco": {"downforce": 1.00, "power": 0.20, "street": 1.0, "laps": 78, "sc_probability": 0.75},
    "marina_bay": {"downforce": 0.95, "power": 0.35, "street": 1.0, "laps": 62, "sc_probability": 0.85},
    "singapore": {"downforce": 0.95, "power": 0.35, "street": 1.0, "laps": 62, "sc_probability": 0.85},  # alias for marina_bay
    "baku": {"downforce": 0.40, "power": 0.95, "street": 1.0, "laps": 51, "sc_probability": 0.70},
    "jeddah": {"downforce": 0.40, "power": 0.95, "street": 1.0, "laps": 50, "sc_probability": 0.70},
    "albert_park": {"downforce": 0.65, "power": 0.70, "street": 1.0, "laps": 58, "sc_probability": 0.60},
    "melbourne": {"downforce": 0.65, "power": 0.70, "street": 1.0, "laps": 58, "sc_probability": 0.60},  # alias for albert_park
    "miami": {"downforce": 0.60, "power": 0.85, "street": 1.0, "laps": 57, "sc_probability": 0.55},
    "vegas": {"downforce": 0.30, "power": 0.95, "street": 1.0, "laps": 50, "sc_probability": 0.55},
    "villeneuve": {"downforce": 0.45, "power": 0.85, "street": 1.0, "laps": 70, "sc_probability": 0.65},
    "madring": {"downforce": 0.75, "power": 0.75, "street": 1.0, "laps": 57, "sc_probability": 0.60},
}


CIRCUIT_ALIASES: Dict[str, str] = {
    "interlagos": "interlagos",
    "sao_paulo": "interlagos",
    "austin": "americas",
    "cota": "americas",
    "singapore": "marina_bay",
    "melbourne": "albert_park",
    "australia": "albert_park",
    "mexico_city": "rodriguez",
    "mexico": "rodriguez",
    "canada": "villeneuve",
    "montreal": "villeneuve",
    "las_vegas": "vegas",
    "abu_dhabi": "yas_marina",
    "qatar": "losail",
    "lusail": "losail",
    "austria": "red_bull_ring",
    "spielberg": "red_bull_ring",
    "uk": "silverstone",
    "britain": "silverstone",
    "italy": "monza",
    "belgium": "spa",
    "spain": "catalunya",
    "japan": "suzuka",
    "china": "shanghai",
    "madrid": "madring",
}


def normalize_circuit_id(race_id: str) -> str:
    """Normalizes race/circuit IDs by stripping season suffixes and resolving known aliases."""
    cleaned = re.sub(r"_(?:20\d{2})$", "", (race_id or "").strip().lower())
    return CIRCUIT_ALIASES.get(cleaned, cleaned)


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
        weather_transition: bool | float = 0.0,
        dnf_rate: float = 0.08,
        constructor_race_gain: float = 0.0,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Constructs a normalized 12-dimensional vector from pre-race inputs."""
        canonical_circuit = normalize_circuit_id(circuit_id)
        profile = CIRCUIT_PROFILES.get(
            canonical_circuit,
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
        transition_flag = 1.0 if float(weather_transition) > 0.5 else 0.0
        dnf_norm = np.clip(dnf_rate, 0.0, 1.0)
        gain_norm = np.clip((constructor_race_gain + 5.0) / 10.0, 0.0, 1.0)

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
            transition_flag,
            dnf_norm,
            gain_norm,
        ], dtype=np.float32)

        feat_dict = {
            "grid_position_norm": float(grid_norm),
            "quali_delta_to_pole_s": float(quali_delta_norm),
            "driver_rolling_finish_norm": float(rolling_finish_norm),
            "driver_circuit_experience": float(exp_norm),
            "constructor_pts_share": float(pts_share_norm),
            "circuit_downforce_index": df_index,
            "circuit_power_sensitivity": pwr_index,
            "circuit_is_street_track": is_street,
            "race_rain_prob": float(rain),
            "weather_transition_flag": transition_flag,
            "driver_dnf_rate": float(dnf_norm),
            "constructor_race_gain_norm": float(gain_norm),
        }

        return vec, feat_dict

    @staticmethod
    def dict_to_vector(feat_dict: Dict[str, float]) -> np.ndarray:
        """Converts a feature dictionary into a 12-dimensional numpy vector aligned with PRE_RACE_FEATURE_NAMES."""
        return np.array([float(feat_dict.get(name, 0.0)) for name in PRE_RACE_FEATURE_NAMES], dtype=np.float32)
