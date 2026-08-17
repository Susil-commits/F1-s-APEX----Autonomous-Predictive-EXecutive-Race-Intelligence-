"""Tyre degradation and thermal wear feature engineering."""
from __future__ import annotations

import numpy as np
import pandas as pd

CIRCUIT_ABRASION = {
    "bahrain": 1.35,
    "barcelona": 1.25,
    "spain": 1.25,
    "silverstone": 1.15,
    "suzuka": 1.20,
    "spa": 1.05,
    "austria": 1.00,
    "interlagos": 0.95,
    "zandvoort": 1.10,
    "monza": 0.75,
    "monaco": 0.55,
}


def compute_tyre_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generates rich tyre-specific features for regression and classification models."""
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    # Compound one-hot
    out["is_soft"] = (out["compound"] == "SOFT").astype(float)
    out["is_medium"] = (out["compound"] == "MEDIUM").astype(float)
    out["is_hard"] = (out["compound"] == "HARD").astype(float)
    out["is_inter"] = (out["compound"] == "INTERMEDIATE").astype(float)
    out["is_wet"] = (out["compound"] == "WET").astype(float)

    # Tyre Age nonlinear transformations
    out["tyre_age_norm"] = out["tyre_age"] / 40.0
    out["tyre_age_sq"] = (out["tyre_age"] / 20.0) ** 2

    # Circuit abrasion factor
    def get_abrasion(c: str) -> float:
        c_clean = str(c).lower().replace(" ", "").replace("_", "")
        for k, v in CIRCUIT_ABRASION.items():
            if k in c_clean or c_clean in k:
                return v
        return 1.0

    out["circuit_abrasion"] = out["circuit"].apply(get_abrasion)

    # Thermal stress interaction
    track_temp = out.get("track_temp_c", 30.0)
    out["thermal_stress"] = (track_temp / 35.0) * out["circuit_abrasion"] * (1.2 if out["is_soft"].any() else 1.0)

    # Stint relative wear estimate
    out["estimated_wear_pct"] = np.clip(
        out["tyre_age"] * (3.0 * out["is_soft"] + 2.0 * out["is_medium"] + 1.4 * out["is_hard"]) * out["circuit_abrasion"],
        0.0,
        100.0,
    )
    out["is_cliff_risk"] = (out["estimated_wear_pct"] > 70.0).astype(float)

    return out
