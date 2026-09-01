"""Jolpica / Ergast API Loader for historical race results, pit stops, and championship standings."""
from __future__ import annotations

import logging
from typing import Any, cast

import httpx
import pandas as pd

from .raw_storage import RawStorageManager

logger = logging.getLogger(__name__)

BASE_JOLPICA_URL = "https://api.jolpi.ca/ergast/f1"


class JolpicaDataLoader:
    """Fetches and normalizes historical F1 season, race, pit stop, and standings data from Jolpica API."""

    def __init__(self, storage_manager: RawStorageManager | None = None):
        self.storage = storage_manager or RawStorageManager()

    def fetch_season_races(self, year: int) -> pd.DataFrame:
        """Fetches the race calendar and circuit identifiers for a given season."""
        ident = f"season_races_{year}"
        cached = self.storage.load_raw_table("jolpica", ident)
        if cached is not None:
            return cached

        url = f"{BASE_JOLPICA_URL}/{year}.json"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
                    records = []
                    for r in races:
                        records.append({
                            "season": int(r.get("season", year)),
                            "round": int(r.get("round", 0)),
                            "race_name": r.get("raceName", ""),
                            "circuit_id": r.get("Circuit", {}).get("circuitId", ""),
                            "circuit_name": r.get("Circuit", {}).get("circuitName", ""),
                            "country": r.get("Circuit", {}).get("Location", {}).get("country", ""),
                            "date": r.get("date", ""),
                        })
                    df = pd.DataFrame(records)
                    self.storage.save_raw_table(df, "jolpica", ident, {"year": year, "source": "jolpica"})
                    return df
        except Exception as e:
            logger.warning(f"[JolpicaDataLoader] Failed to fetch season {year}: {e}")

        # Fallback empty dataframe
        return pd.DataFrame([], columns=cast(Any, ["season", "round", "race_name", "circuit_id", "circuit_name", "country", "date"]))

    def fetch_race_pitstops(self, year: int, round_num: int) -> pd.DataFrame:
        """Fetches historical pit stop durations and laps for a given Grand Prix."""
        ident = f"pitstops_{year}_round_{round_num}"
        cached = self.storage.load_raw_table("jolpica", ident)
        if cached is not None:
            return cached

        url = f"{BASE_JOLPICA_URL}/{year}/{round_num}/pitstops.json?limit=100"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
                    if races and "PitStops" in races[0]:
                        records = []
                        for p in races[0]["PitStops"]:
                            records.append({
                                "season": year,
                                "round": round_num,
                                "driver_id": p.get("driverId", ""),
                                "lap": int(p.get("lap", 0)),
                                "stop": int(p.get("stop", 1)),
                                "duration_s": float(p.get("duration", 0.0)) if p.get("duration") else 0.0,
                                "time": p.get("time", ""),
                            })
                        df = pd.DataFrame(records)
                        self.storage.save_raw_table(df, "jolpica", ident, {"year": year, "round": round_num})
                        return df
        except Exception as e:
            logger.warning(f"[JolpicaDataLoader] Failed to fetch pitstops for {year} R{round_num}: {e}")

        return pd.DataFrame([], columns=cast(Any, ["season", "round", "driver_id", "lap", "stop", "duration_s", "time"]))
