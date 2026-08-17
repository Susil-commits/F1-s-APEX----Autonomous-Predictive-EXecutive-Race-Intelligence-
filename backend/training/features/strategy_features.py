"""Strategy state, stint progression, and pit window optimization features."""
from __future__ import annotations

import pandas as pd
import numpy as np


def compute_strategy_features(df: pd.DataFrame, total_laps: int = 52) -> pd.DataFrame:
    """Extracts strategic stint markers, pit window state, and race horizon ratios."""
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    stint = pd.Series(pd.to_numeric(out["stint"], errors="coerce")).fillna(1).astype(int) if "stint" in out.columns else pd.Series(1, index=out.index)
    tyre_age = pd.Series(pd.to_numeric(out["tyre_age"], errors="coerce")).fillna(1).astype(int) if "tyre_age" in out.columns else pd.Series(1, index=out.index)
    
    if "LapNumber" in out.columns:
        lap = pd.Series(pd.to_numeric(out["LapNumber"], errors="coerce")).fillna(tyre_age).astype(int)
    else:
        lap = tyre_age

    out["stint_number"] = stint
    out["pit_count"] = np.clip(stint - 1, 0, 4)
    out["laps_remaining"] = np.clip(total_laps - lap, 0, total_laps)
    out["race_progress_ratio"] = np.clip(lap / total_laps, 0.0, 1.0)

    # Pit window indicator
    compound = out["compound"] if "compound" in out.columns else pd.Series("MEDIUM", index=out.index)
    is_soft = compound == "SOFT"
    is_med = compound == "MEDIUM"
    is_hard = compound == "HARD"

    optimal_window = (is_soft & (tyre_age >= 14) & (tyre_age <= 22)) | \
                     (is_med & (tyre_age >= 22) & (tyre_age <= 32)) | \
                     (is_hard & (tyre_age >= 32) & (tyre_age <= 44))
    out["is_optimal_pit_window"] = optimal_window.astype(float)

    return out
