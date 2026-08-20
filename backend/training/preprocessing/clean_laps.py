"""Clean and filter raw lap data for race intelligence feature extraction."""
from __future__ import annotations

import logging

import pandas as pd

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

    records = []
    for _, row in raw_laps.iterrows():
        # Drop pit laps
        pit_in = str(row.get("PitInTime", ""))
        pit_out = str(row.get("PitOutTime", ""))
        if pit_in not in ("", "nan", "NaT", "None") or pit_out not in ("", "nan", "NaT", "None"):
            continue
        if "IsAccurate" in row and not bool(row["IsAccurate"]):
            continue
        if "TrackStatus" in row and str(row["TrackStatus"]).strip() != "1":
            continue

        lap_time = row.get("LapTime")
        if lap_time is None or str(lap_time) in ("", "nan", "NaT", "None"):
            continue

        lap_s = 0.0
        if hasattr(lap_time, "total_seconds"):
            try:
                lap_s = float(getattr(lap_time, "total_seconds")())
            except Exception:
                continue
        else:
            try:
                lap_s = float(str(lap_time))
            except (ValueError, TypeError):
                continue

        if lap_s <= 30.0:
            continue

        tyre_life = row.get("TyreLife", 1)
        try:
            tyre_age = int(float(str(tyre_life)))
        except (ValueError, TypeError):
            tyre_age = 1

        if tyre_age < 1:
            continue

        raw_comp = str(row.get("Compound", "MEDIUM")).upper()
        comp = COMPOUND_MAP.get(raw_comp, "UNKNOWN")
        if comp not in COMPOUND_MAP:
            continue

        driver = str(row.get("Driver", "UNKNOWN"))
        try:
            stint = int(float(str(row.get("Stint", 1))))
        except (ValueError, TypeError):
            stint = 1

        records.append({
            "Driver": driver,
            "Compound": raw_comp,
            "compound": comp,
            "tyre_age": tyre_age,
            "stint": stint,
            "lap_time_s": lap_s,
        })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Driver-relative pace delta calculation
    driver_bests = df.groupby("Driver")["lap_time_s"].min().to_dict()
    df["driver_best_s"] = df["Driver"].apply(lambda d: driver_bests.get(str(d), 90.0))
    raw_delta = df["lap_time_s"] - df["driver_best_s"]

    # Fuel correction: as laps elapse in stint, car gets lighter by ~0.055s/lap
    df["stint_lap"] = df.groupby(["Driver", "stint"]).cumcount() + 1
    df["fuel_corrected_delta"] = raw_delta + (fuel_burn_rate_s_per_lap * df["stint_lap"])
    df["lap_time_delta"] = df["fuel_corrected_delta"].clip(lower=0.0)

    # Filter extreme anomalies (>15s delta under green flag)
    df = df[(df["lap_time_delta"] >= 0.0) & (df["lap_time_delta"] <= 15.0)]

    df["circuit"] = circuit_name
    df["season"] = season
    df["data_source"] = "clean_pipeline"

    return pd.DataFrame(df.reset_index(drop=True))
