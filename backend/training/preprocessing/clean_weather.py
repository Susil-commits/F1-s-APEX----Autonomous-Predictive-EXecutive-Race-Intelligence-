"""Clean and interpolate weather telemetry time series."""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def clean_weather_dataframe(raw_weather: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes raw weather dataframe:
    - AirTemp (°C)
    - TrackTemp (°C)
    - Humidity (%)
    - Pressure (mbar)
    - Rainfall (bool / float intensity)
    - WindSpeed (m/s)
    """
    if raw_weather is None or raw_weather.empty:
        return pd.DataFrame()

    df = raw_weather.copy()

    # Time column handling
    if "Time" in df.columns:
        if hasattr(df["Time"].iloc[0], "total_seconds"):
            df["time_s"] = df["Time"].apply(lambda t: t.total_seconds() if pd.notna(t) else 0.0)
        else:
            df["time_s"] = pd.Series(pd.to_numeric(df["Time"], errors="coerce")).fillna(0.0)

    def _col_or_default(col_name: str, default_val: float) -> pd.Series:
        if col_name in df.columns:
            return pd.Series(pd.to_numeric(df[col_name], errors="coerce")).fillna(default_val)
        return pd.Series(default_val, index=df.index)

    # Standard columns
    df["air_temp_c"] = _col_or_default("AirTemp", 22.0).clip(5.0, 50.0)
    df["track_temp_c"] = _col_or_default("TrackTemp", 30.0).clip(10.0, 70.0)
    df["humidity_pct"] = _col_or_default("Humidity", 50.0).clip(0.0, 100.0)
    df["pressure_mbar"] = _col_or_default("Pressure", 1013.25).clip(900.0, 1100.0)
    
    # Rainfall flag / intensity
    if "Rainfall" in df.columns:
        df["is_raining"] = df["Rainfall"].astype(bool)
        df["rain_intensity"] = df["is_raining"].astype(float)
    else:
        df["is_raining"] = False
        df["rain_intensity"] = 0.0

    # Temperature delta
    df["track_air_delta_c"] = df["track_temp_c"] - df["air_temp_c"]

    return df.reset_index(drop=True)
