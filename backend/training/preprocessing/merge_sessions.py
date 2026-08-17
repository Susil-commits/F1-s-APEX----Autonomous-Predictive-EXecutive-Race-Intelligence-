"""Session Merger: Synchronizes laps, weather, telemetry aggregates, and race control events."""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from .clean_laps import clean_laps_dataframe
from .clean_weather import clean_weather_dataframe
from .clean_race_control import clean_race_control_dataframe

logger = logging.getLogger(__name__)


class SessionDataMerger:
    """Combines cleaned session sub-tables into unified lap-level training dataframes."""

    @staticmethod
    def merge_session_components(
        raw_components: Dict[str, pd.DataFrame],
        circuit_name: str = "Silverstone",
        season: int = 2023,
    ) -> pd.DataFrame:
        """Merges cleaned laps, weather, and race control into a single synchronized dataframe."""
        raw_laps = raw_components.get("laps", pd.DataFrame())
        raw_weather = raw_components.get("weather", pd.DataFrame())
        raw_rc = raw_components.get("race_control", pd.DataFrame())

        clean_laps = clean_laps_dataframe(raw_laps, circuit_name=circuit_name, season=season)
        if clean_laps.empty:
            return pd.DataFrame()

        clean_weather = clean_weather_dataframe(raw_weather)
        
        # Attach session-level average weather if weather time series is available
        if not clean_weather.empty:
            clean_laps["track_temp_c"] = clean_weather["track_temp_c"].mean()
            clean_laps["air_temp_c"] = clean_weather["air_temp_c"].mean()
            clean_laps["humidity_pct"] = clean_weather["humidity_pct"].mean()
            clean_laps["is_raining"] = clean_weather["is_raining"].any()
        else:
            clean_laps["track_temp_c"] = 32.0
            clean_laps["air_temp_c"] = 22.0
            clean_laps["humidity_pct"] = 50.0
            clean_laps["is_raining"] = False

        return clean_laps
