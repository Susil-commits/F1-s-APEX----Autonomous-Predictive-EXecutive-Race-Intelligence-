"""Weather and track condition feature engineering."""
from __future__ import annotations

import pandas as pd
import numpy as np


def _get_numeric_series(df: pd.DataFrame, col: str, default: float) -> pd.Series:
    if col in df.columns:
        return pd.Series(pd.to_numeric(df[col], errors="coerce")).fillna(default)
    return pd.Series(default, index=df.index)


def compute_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts weather dynamics, track wetness index, and tyre crossover indicators."""
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    track_temp = _get_numeric_series(out, "track_temp_c", 30.0)
    air_temp = _get_numeric_series(out, "air_temp_c", 22.0)
    humidity = _get_numeric_series(out, "humidity_pct", 50.0)
    rain_intensity = _get_numeric_series(out, "rain_intensity", 0.0)

    # Track wetness index (0.0 = bone dry, 1.0 = standing water)
    out["track_wetness_index"] = np.clip(rain_intensity * 0.9 + (humidity / 100.0) * 0.1, 0.0, 1.0)

    # Evaporation rate index (higher track temp + lower humidity = faster drying)
    out["drying_potential"] = np.clip((track_temp - air_temp + 10.0) / 25.0 * (1.0 - humidity / 100.0), 0.0, 1.5)

    # Crossover proximity:
    # Intermediate crossover threshold is ~0.20-0.45 track wetness
    # Full Wet crossover is > 0.65 track wetness
    out["inter_crossover_score"] = np.exp(-((out["track_wetness_index"] - 0.35) ** 2) / 0.05)
    out["wet_crossover_score"] = np.clip((out["track_wetness_index"] - 0.60) / 0.40, 0.0, 1.0)

    return out
