"""Vehicle telemetry, fuel load effect, and thermal strain feature engineering."""
from __future__ import annotations

import pandas as pd
import numpy as np


def _get_numeric_series(df: pd.DataFrame, col: str, default: float) -> pd.Series:
    if col in df.columns:
        return pd.Series(pd.to_numeric(df[col], errors="coerce")).fillna(default)
    return pd.Series(default, index=df.index)


def compute_vehicle_features(df: pd.DataFrame, total_laps: int = 52) -> pd.DataFrame:
    """Computes fuel mass effects, cooling strain, and vehicle telemetry features."""
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    # Lap number progression
    if "LapNumber" in out.columns:
        lap_num = pd.Series(pd.to_numeric(out["LapNumber"], errors="coerce")).fillna(1)
    elif "stint_lap" in out.columns:
        lap_num = pd.Series(pd.to_numeric(out["stint_lap"], errors="coerce")).fillna(1)
    else:
        lap_num = pd.Series(1, index=out.index)
    
    # Fuel remaining in kg (Starts at ~105kg, burns ~1.85kg/lap)
    out["fuel_remaining_kg"] = np.clip(105.0 - (1.85 * lap_num), 3.0, 105.0)
    out["fuel_weight_delta_s"] = out["fuel_remaining_kg"] * 0.033

    # ERS battery estimate (proxy 0.0 to 1.0)
    out["ers_battery_pct"] = 0.85 - 0.10 * np.sin(lap_num / 3.0)

    # Mechanical thermal stress
    track_temp = _get_numeric_series(out, "track_temp_c", 30.0)
    out["engine_thermal_stress"] = (track_temp / 35.0) * (1.0 + 0.1 * (lap_num / total_laps))

    return out
