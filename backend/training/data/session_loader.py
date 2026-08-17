"""Unified Session Loader bridging FastF1, Jolpica, and synthetic scenario generation."""
from __future__ import annotations

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

from .fastf1_loader import FastF1DataLoader
from .jolpica_loader import JolpicaDataLoader
from .raw_storage import RawStorageManager

logger = logging.getLogger(__name__)


class UnifiedSessionLoader:
    """Unified session loader for orchestrating race telemetry and timing data extraction."""

    def __init__(self, raw_storage: Optional[RawStorageManager] = None, offline_only: bool = False):
        self.storage = raw_storage or RawStorageManager()
        self.offline_only = offline_only
        self.fastf1 = FastF1DataLoader(storage_manager=self.storage, offline_only=offline_only)
        self.jolpica = JolpicaDataLoader(storage_manager=self.storage)

    def load_session(
        self,
        year: int,
        circuit: str,
        session_type: str = "R",
        allow_synthetic_fallback: bool = True,
        offline_only: Optional[bool] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Loads all components of an F1 session (laps, weather, results, race control)."""
        is_offline = self.offline_only if offline_only is None else offline_only
        data = self.fastf1.load_session_raw(year, circuit, session_type, offline_only=is_offline)

        # Check if real data was successfully retrieved
        if data["laps"] is not None and not data["laps"].empty:
            return data

        if not allow_synthetic_fallback:
            raise RuntimeError(f"No real session data available for {year} {circuit} and synthetic fallback disabled.")

        logger.info(f"[UnifiedSessionLoader] Generating high-fidelity synthetic session for {year} {circuit}")
        return self._generate_synthetic_session(year, circuit)

    def _generate_synthetic_session(self, year: int, circuit: str) -> Dict[str, pd.DataFrame]:
        """Generates realistic synthetic session tables with laps, weather, and results."""
        np.random.seed(year * 100 + len(circuit))
        drivers = ["VER", "NOR", "LEC", "HAM", "RUS", "PIA", "SAI", "ALO", "PER", "TSU"]
        compounds = ["SOFT", "MEDIUM", "HARD"]
        total_laps = 52
        base_lap_s = 89.0

        records = []
        for drv_idx, drv in enumerate(drivers):
            stint = 1
            curr_compound = "MEDIUM" if drv_idx % 2 == 0 else "SOFT"
            tyre_life = 1
            cum_time = 0.0

            for lap in range(1, total_laps + 1):
                drv_pace_bias = (drv_idx - 4) * 0.12
                deg_rate = 0.07 if curr_compound == "SOFT" else (0.045 if curr_compound == "MEDIUM" else 0.03)
                wear_loss = deg_rate * (tyre_life ** 1.15)
                fuel_adv = -0.055 * lap
                noise = np.random.normal(0, 0.15)

                lap_s = base_lap_s + drv_pace_bias + wear_loss + fuel_adv + noise
                cum_time += lap_s

                is_pit = False
                if (curr_compound == "SOFT" and tyre_life >= 16) or (curr_compound == "MEDIUM" and tyre_life >= 26):
                    is_pit = True

                records.append({
                    "Driver": drv,
                    "LapNumber": lap,
                    "Stint": stint,
                    "Compound": curr_compound,
                    "TyreLife": tyre_life,
                    "LapTime": pd.Timedelta(seconds=lap_s),
                    "PitInTime": pd.Timedelta(seconds=cum_time) if is_pit else pd.NaT,
                    "PitOutTime": pd.NaT,
                    "IsAccurate": True,
                    "TrackStatus": "1",
                })

                if is_pit:
                    stint += 1
                    curr_compound = "HARD"
                    tyre_life = 1
                else:
                    tyre_life += 1

        laps_df = pd.DataFrame(records)

        weather_records = []
        for lap in range(1, total_laps + 1):
            weather_records.append({
                "Time": pd.Timedelta(seconds=lap * base_lap_s),
                "AirTemp": 23.5 + np.sin(lap / 10.0) * 0.5,
                "TrackTemp": 34.0 + np.sin(lap / 8.0) * 1.5,
                "Humidity": 45.0,
                "Pressure": 1013.2,
                "Rainfall": False,
            })
        weather_df = pd.DataFrame(weather_records)

        return {
            "laps": laps_df,
            "weather": weather_df,
            "results": pd.DataFrame({"Driver": drivers, "Position": list(range(1, len(drivers) + 1))}),
            "race_control": pd.DataFrame(),
        }
