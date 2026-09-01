"""FastF1 Ingestion Adapter for APEX Core.

Fetches race sessions, lap telemetry, weather conditions, and tyre stints
with persistent caching and point-in-time temporal boundaries.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "data", "fastf1_cache")


class FastF1Adapter:
    """Lightweight adapter around FastF1 for Tier 1 reproducible ingestion."""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self._cache_enabled = False

    def enable_cache(self) -> None:
        """Enables FastF1 disk cache if not already active."""
        if not self._cache_enabled:
            try:
                import fastf1
                fastf1.Cache.enable_cache(self.cache_dir)
                self._cache_enabled = True
                logger.info(f"[FastF1Adapter] Cache enabled at: {self.cache_dir}")
            except Exception as e:
                logger.warning(f"[FastF1Adapter] Failed to enable cache: {e}")

    def load_race_session(self, year: int, circuit: str, session_type: str = "R") -> Any:
        """Loads a specific session with caching."""
        self.enable_cache()
        import fastf1
        session = fastf1.get_session(year, circuit, session_type)
        session.load(laps=True, telemetry=False, weather=True, messages=False)
        return session

    def get_qualifying_grid(self, year: int, circuit: str) -> pd.DataFrame:
        """Retrieves grid starting positions strictly prior to race start.
        
        Guarantees point-in-time safety: only information available on the grid is returned.
        """
        try:
            quali = self.load_race_session(year, circuit, session_type="Q")
            results = quali.results[["DriverNumber", "BroadcastName", "Abbreviation", "TeamName", "Position"]].copy()
            results.rename(columns={"Position": "GridPosition"}, inplace=True)
            return results
        except Exception as e:
            logger.warning(f"[FastF1Adapter] Could not load qualifying for {year} {circuit}: {e}")
            return pd.DataFrame()
