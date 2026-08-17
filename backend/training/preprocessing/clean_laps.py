"""Clean and filter raw lap data for race intelligence feature extraction."""
from __future__ import annotations

import logging
from typing import Optional, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

COMPOUND_MAP = {
    "SOFT": "SOFT",
    "MEDIUM": "MEDIUM",
    "HARD": "HARD",
    "INTERMEDIATE": "INTERMEDIATE",
    "WET": "WET",
}


def clean_laps_dataframe(
    raw_laps: pd.DataFrame,
    circuit_name: str = "Silverstone",
    season: int = 2023,
    fuel_burn_rate_s_per_lap: float = 0.055,
) -> pd.DataFrame:
    """
    Cleans raw session lap records:
    - Filters pit in-laps and out-laps.
    - Filters non-green flag conditions (TrackStatus != '1').
    - Requires valid positive lap times and tyre life >= 1.
    - Normalizes compound names.
    - Computes driver-relative lap delta isolated from raw driver pace and corrected for fuel mass burn.
    """
    if raw_laps is None or raw_laps.empty:
        return pd.DataFrame()

    df = raw_laps.copy()

    # Drop pit laps
    if "PitInTime" in df.columns:
        df = df[df["PitInTime"].isna()]
    if "PitOutTime" in df.columns:
        df = df[df["PitOutTime"].isna()]
    if "IsAccurate" in df.columns:
        df = df[df["IsAccurate"] == True]

    # Green flag only
    if "TrackStatus" in df.columns:
        df = df[df["TrackStatus"].astype(str) == "1"]

    if "LapTime" not in df.columns or "TyreLife" not in df.columns:
        return pd.DataFrame()

    # Parse lap times
    if hasattr(df["LapTime"].iloc[0], "total_seconds"):
        df["lap_time_s"] = df["LapTime"].apply(lambda t: t.total_seconds() if pd.notna(t) else np.nan)
    else:
        df["lap_time_s"] = pd.to_numeric(df["LapTime"], errors="coerce")

    df = df[df["lap_time_s"].notna() & (df["lap_time_s"] > 30.0)]
    df["tyre_age"] = pd.Series(pd.to_numeric(df["TyreLife"], errors="coerce")).fillna(1).astype(int)
    df = df[df["tyre_age"] >= 1]

    # Normalize compounds
    if "Compound" in df.columns:
        df["compound"] = df["Compound"].astype(str).str.upper().map(lambda c: COMPOUND_MAP.get(c, "UNKNOWN"))
        df = df[df["compound"].isin(COMPOUND_MAP.values())]
    else:
        df["compound"] = "MEDIUM"

    # Driver-relative pace delta calculation
    if "Driver" in df.columns:
        driver_bests = df.groupby("Driver")["lap_time_s"].min()
        df["driver_best_s"] = df["Driver"].map(driver_bests)
        raw_delta = df["lap_time_s"] - df["driver_best_s"]
    else:
        df["Driver"] = "UNKNOWN"
        df["driver_best_s"] = df["lap_time_s"].min()
        raw_delta = df["lap_time_s"] - df["driver_best_s"]

    # Fuel correction: as laps elapse in stint, car gets lighter by ~0.055s/lap
    stint_col = df["Stint"] if "Stint" in df.columns else pd.Series(1, index=df.index)
    df["stint"] = pd.Series(pd.to_numeric(stint_col, errors="coerce")).fillna(1).astype(int)
    df["stint_lap"] = df.groupby(["Driver", "stint"]).cumcount() + 1
    df["fuel_corrected_delta"] = raw_delta + (fuel_burn_rate_s_per_lap * df["stint_lap"])
    df["lap_time_delta"] = df["fuel_corrected_delta"].clip(lower=0.0)

    # Filter extreme anomalies (>15s delta under green flag)
    df = df[(df["lap_time_delta"] >= 0.0) & (df["lap_time_delta"] <= 15.0)]

    df["circuit"] = circuit_name
    df["season"] = season
    df["data_source"] = "clean_pipeline"

    return df.reset_index(drop=True)
