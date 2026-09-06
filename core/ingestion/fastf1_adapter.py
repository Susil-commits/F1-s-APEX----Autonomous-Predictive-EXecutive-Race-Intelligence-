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

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "fastf1_cache")


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

    def get_qualifying_sector_deltas(self, year: int, circuit: str) -> pd.DataFrame:
        """Retrieves per-driver qualifying sector times and deltas to pole.
        
        Point-in-time safe: strictly extracts sector times from qualifying session prior to race start.
        Returns DataFrame with columns:
        ['DriverNumber', 'Abbreviation', 'sector_1_delta_s', 'sector_2_delta_s', 'sector_3_delta_s']
        """
        try:
            quali = self.load_race_session(year, circuit, session_type="Q")
            laps = getattr(quali, "laps", None)
            if laps is None or laps.empty:
                return pd.DataFrame()

            quick_laps = laps.pick_quicklaps() if hasattr(laps, "pick_quicklaps") else laps
            pole_lap = quick_laps.pick_fastest() if hasattr(quick_laps, "pick_fastest") else None
            if pole_lap is None or pole_lap.empty:
                return pd.DataFrame()

            pole_s1 = pole_lap["Sector1Time"].total_seconds() if pd.notnull(pole_lap.get("Sector1Time")) else 0.0
            pole_s2 = pole_lap["Sector2Time"].total_seconds() if pd.notnull(pole_lap.get("Sector2Time")) else 0.0
            pole_s3 = pole_lap["Sector3Time"].total_seconds() if pd.notnull(pole_lap.get("Sector3Time")) else 0.0

            rows = []
            for driver in quick_laps["Driver"].unique():
                d_laps = quick_laps.pick_driver(driver) if hasattr(quick_laps, "pick_driver") else quick_laps[quick_laps["Driver"] == driver]
                d_lap = d_laps.pick_fastest() if hasattr(d_laps, "pick_fastest") else d_laps.iloc[0] if len(d_laps) > 0 else None
                if d_lap is not None and not d_lap.empty:
                    s1 = d_lap["Sector1Time"].total_seconds() if pd.notnull(d_lap.get("Sector1Time")) else pole_s1
                    s2 = d_lap["Sector2Time"].total_seconds() if pd.notnull(d_lap.get("Sector2Time")) else pole_s2
                    s3 = d_lap["Sector3Time"].total_seconds() if pd.notnull(d_lap.get("Sector3Time")) else pole_s3
                    rows.append({
                        "Abbreviation": str(driver),
                        "DriverNumber": str(d_lap.get("DriverNumber", "")),
                        "sector_1_delta_s": max(0.0, float(s1 - pole_s1)),
                        "sector_2_delta_s": max(0.0, float(s2 - pole_s2)),
                        "sector_3_delta_s": max(0.0, float(s3 - pole_s3)),
                    })
            return pd.DataFrame(rows)
        except Exception as e:
            logger.warning(f"[FastF1Adapter] Could not load sector deltas for {year} {circuit}: {e}")
            return pd.DataFrame()

