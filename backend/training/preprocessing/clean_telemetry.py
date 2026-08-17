"""Clean and aggregate high-frequency telemetry channels into lap summary metrics."""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def clean_telemetry_dataframe(raw_telemetry: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw telemetry channels and normalizes ranges:
    - Speed (km/h)
    - Throttle (0-100%)
    - Brake (0 or True/False / 0-100%)
    - RPM (0-15000)
    - nGear (0-8)
    - DRS (0/1/False/True)
    """
    if raw_telemetry is None or raw_telemetry.empty:
        return pd.DataFrame()

    df = raw_telemetry.copy()

    # Normalization mappings
    if "Speed" in df.columns:
        df["speed_kmh"] = pd.Series(pd.to_numeric(df["Speed"], errors="coerce")).clip(0.0, 380.0)
    if "Throttle" in df.columns:
        df["throttle_pct"] = pd.Series(pd.to_numeric(df["Throttle"], errors="coerce")).clip(0.0, 100.0)
    if "Brake" in df.columns:
        # Some FastF1 telemetry encodes Brake as bool or 0/100
        df["brake_active"] = pd.Series(df["Brake"].astype(float)).clip(0.0, 1.0)
    if "RPM" in df.columns:
        df["rpm"] = pd.Series(pd.to_numeric(df["RPM"], errors="coerce")).clip(0.0, 16000.0)
    if "nGear" in df.columns:
        df["gear"] = pd.Series(pd.to_numeric(df["nGear"], errors="coerce")).fillna(0).astype(int).clip(0, 8)
    if "DRS" in df.columns:
        # DRS in FastF1 is encoded as integer flags (e.g. 10, 12, 14 = open)
        df["drs_open"] = df["DRS"].apply(lambda d: 1.0 if str(d) in ["10", "12", "14", "1", "True"] else 0.0)

    return df


def aggregate_lap_telemetry(clean_tel: pd.DataFrame) -> Dict[str, float]:
    """Computes summary lap-level telemetry features from high-frequency telemetry samples."""
    if clean_tel.empty:
        return {
            "avg_speed_kmh": 0.0,
            "max_speed_kmh": 0.0,
            "full_throttle_pct": 0.0,
            "braking_time_pct": 0.0,
            "drs_usage_pct": 0.0,
        }

    total_pts = len(clean_tel)
    avg_speed = float(clean_tel["speed_kmh"].mean()) if "speed_kmh" in clean_tel.columns else 0.0
    max_speed = float(clean_tel["speed_kmh"].max()) if "speed_kmh" in clean_tel.columns else 0.0
    full_throttle = float((clean_tel["throttle_pct"] > 95.0).sum()) / total_pts * 100.0 if "throttle_pct" in clean_tel.columns else 0.0
    braking_time = float((clean_tel["brake_active"] > 0.0).sum()) / total_pts * 100.0 if "brake_active" in clean_tel.columns else 0.0
    drs_usage = float((clean_tel["drs_open"] > 0.0).sum()) / total_pts * 100.0 if "drs_open" in clean_tel.columns else 0.0

    return {
        "avg_speed_kmh": round(avg_speed, 2),
        "max_speed_kmh": round(max_speed, 2),
        "full_throttle_pct": round(full_throttle, 2),
        "braking_time_pct": round(braking_time, 2),
        "drs_usage_pct": round(drs_usage, 2),
    }
