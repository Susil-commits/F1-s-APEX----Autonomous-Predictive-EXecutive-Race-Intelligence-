"""FastF1 Data Loader for extracting laps, weather, telemetry, and race control events."""
from __future__ import annotations

import logging
import os

import pandas as pd

from .raw_storage import RawStorageManager

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fastf1_cache")


class FastF1DataLoader:
    """Extracts raw session components from FastF1 with disk caching and storage manifests."""

    def __init__(
        self,
        cache_dir: str | None = None,
        storage_manager: RawStorageManager | None = None,
        offline_only: bool = False,
    ):
        self.cache_dir = cache_dir or CACHE_DIR
        self.storage = storage_manager or RawStorageManager()
        self.offline_only = offline_only or (os.getenv("FASTF1_OFFLINE", "0") == "1")
        self._init_fastf1_cache()

    def _init_fastf1_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            import fastf1
            fastf1.Cache.enable_cache(self.cache_dir)
            logger.info(f"[FastF1DataLoader] FastF1 cache initialized at {self.cache_dir}")
        except Exception as e:
            logger.warning(f"[FastF1DataLoader] FastF1 cache initialization skipped: {e}")

    def load_session_raw(
        self,
        year: int,
        circuit: str,
        session_type: str = "R",
        offline_only: bool | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Loads raw laps, weather, race_control, and driver telemetry from FastF1.
        
        Returns a dictionary with dataframes for 'laps', 'weather', 'results', and 'race_control'.
        """
        session_id = f"{year}_{circuit}_{session_type}"
        is_offline = self.offline_only if offline_only is None else offline_only
        
        # Check raw storage cache first
        if self.storage.exists("laps", session_id):
            logger.info(f"[FastF1DataLoader] Loading session {session_id} from raw storage cache")
            return {
                "laps": self.storage.load_raw_table("laps", session_id) or pd.DataFrame(),
                "weather": self.storage.load_raw_table("weather", session_id) or pd.DataFrame(),
                "results": self.storage.load_raw_table("results", session_id) or pd.DataFrame(),
                "race_control": self.storage.load_raw_table("race_control", session_id) or pd.DataFrame(),
            }

        if is_offline:
            return {
                "laps": pd.DataFrame(),
                "weather": pd.DataFrame(),
                "results": pd.DataFrame(),
                "race_control": pd.DataFrame(),
            }

        try:
            import fastf1
            logger.info(f"[FastF1DataLoader] Fetching {year} {circuit} {session_type} from FastF1 API...")
            session = fastf1.get_session(year, circuit, session_type)
            session.load(laps=True, telemetry=True, weather=True, messages=True)

            laps_df = session.laps.copy() if hasattr(session, "laps") and session.laps is not None else pd.DataFrame()
            weather_df = session.weather_data.copy() if hasattr(session, "weather_data") and session.weather_data is not None else pd.DataFrame()
            results_df = session.results.copy() if hasattr(session, "results") and session.results is not None else pd.DataFrame()
            
            # Race control messages
            race_control_df = pd.DataFrame()
            if hasattr(session, "race_control_messages") and session.race_control_messages is not None:
                race_control_df = session.race_control_messages.copy()

            meta = {"year": year, "circuit": circuit, "session_type": session_type, "source": "fastf1"}
            self.storage.save_raw_table(laps_df, "laps", session_id, meta)
            self.storage.save_raw_table(weather_df, "weather", session_id, meta)
            self.storage.save_raw_table(results_df, "results", session_id, meta)
            self.storage.save_raw_table(race_control_df, "race_control", session_id, meta)

            return {
                "laps": laps_df,
                "weather": weather_df,
                "results": results_df,
                "race_control": race_control_df,
            }

        except Exception as e:
            logger.warning(f"[FastF1DataLoader] Failed to fetch {year} {circuit}: {e}")
            return {
                "laps": pd.DataFrame(),
                "weather": pd.DataFrame(),
                "results": pd.DataFrame(),
                "race_control": pd.DataFrame(),
            }
