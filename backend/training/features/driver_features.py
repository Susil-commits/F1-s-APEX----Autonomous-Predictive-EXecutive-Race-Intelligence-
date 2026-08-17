"""Driver behavioral profiling and performance index feature engineering."""
from __future__ import annotations

import pandas as pd
import numpy as np

# Empirical driver baseline profiles
DRIVER_BASELINES = {
    "VER": {"pace_bias": -0.25, "consistency": 0.94, "tyre_mgmt": 0.92, "aggression": 0.90},
    "NOR": {"pace_bias": -0.15, "consistency": 0.90, "tyre_mgmt": 0.88, "aggression": 0.85},
    "LEC": {"pace_bias": -0.10, "consistency": 0.87, "tyre_mgmt": 0.84, "aggression": 0.88},
    "HAM": {"pace_bias": 0.05, "consistency": 0.93, "tyre_mgmt": 0.95, "aggression": 0.82},
    "RUS": {"pace_bias": 0.05, "consistency": 0.88, "tyre_mgmt": 0.85, "aggression": 0.86},
    "PIA": {"pace_bias": 0.00, "consistency": 0.89, "tyre_mgmt": 0.86, "aggression": 0.80},
    "SAI": {"pace_bias": 0.08, "consistency": 0.89, "tyre_mgmt": 0.87, "aggression": 0.78},
    "ALO": {"pace_bias": 0.15, "consistency": 0.95, "tyre_mgmt": 0.96, "aggression": 0.88},
    "PER": {"pace_bias": 0.25, "consistency": 0.82, "tyre_mgmt": 0.86, "aggression": 0.75},
}


def compute_driver_features(df: pd.DataFrame) -> pd.DataFrame:
    """Attaches driver behavioral, consistency, and tyre management indices."""
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    def lookup_driver_trait(driver_code: str, trait: str, default_val: float) -> float:
        d_code = str(driver_code).upper().strip()
        for k, v in DRIVER_BASELINES.items():
            if k in d_code:
                return v.get(trait, default_val)
        return default_val

    drv_col = out["Driver"] if "Driver" in out.columns else pd.Series(["UNKNOWN"] * len(out), index=out.index)
    out["driver_pace_bias"] = drv_col.apply(lambda d: lookup_driver_trait(str(d), "pace_bias", 0.0))
    out["driver_consistency"] = drv_col.apply(lambda d: lookup_driver_trait(str(d), "consistency", 0.85))
    out["driver_tyre_mgmt"] = drv_col.apply(lambda d: lookup_driver_trait(str(d), "tyre_mgmt", 0.85))
    out["driver_aggression"] = drv_col.apply(lambda d: lookup_driver_trait(str(d), "aggression", 0.80))

    return out
