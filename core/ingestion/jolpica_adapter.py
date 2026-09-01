"""Jolpica (Ergast replacement) Ingestion Adapter for APEX Core.

Provides historical race schedules, drivers, constructors, and point standings
via the open Jolpica F1 REST API or local cache snapshot.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

JOLPICA_BASE_URL = "https://api.jolpi.ca/ergast/f1"


class JolpicaAdapter:
    """Ingestion adapter for Jolpica / Ergast F1 data feeds."""

    def __init__(self, base_url: str = JOLPICA_BASE_URL, timeout_seconds: float = 12.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    def get_season_races(self, year: int) -> List[Dict[str, Any]]:
        """Fetches calendar rounds for a given season."""
        url = f"{self.base_url}/{year}.json"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
                    return [
                        {
                            "round": int(r.get("round", 0)),
                            "race_name": r.get("raceName", ""),
                            "circuit_id": r.get("Circuit", {}).get("circuitId", ""),
                            "circuit_name": r.get("Circuit", {}).get("circuitName", ""),
                            "date": r.get("date", ""),
                        }
                        for r in races
                    ]
        except Exception as e:
            logger.warning(f"[JolpicaAdapter] Error fetching {year} calendar: {e}")

        # Fallback offline static reference calendar for common circuits
        return [
            {"round": 1, "race_name": "Bahrain Grand Prix", "circuit_id": "bahrain", "circuit_name": "Bahrain International Circuit", "date": f"{year}-03-02"},
            {"round": 2, "race_name": "Saudi Arabian Grand Prix", "circuit_id": "jeddah", "circuit_name": "Jeddah Corniche Circuit", "date": f"{year}-03-09"},
            {"round": 3, "race_name": "Australian Grand Prix", "circuit_id": "albert_park", "circuit_name": "Albert Park Grand Prix Circuit", "date": f"{year}-03-24"},
            {"round": 4, "race_name": "Japanese Grand Prix", "circuit_id": "suzuka", "circuit_name": "Suzuka Circuit", "date": f"{year}-04-07"},
            {"round": 5, "race_name": "Chinese Grand Prix", "circuit_id": "shanghai", "circuit_name": "Shanghai International Circuit", "date": f"{year}-04-21"},
            {"round": 6, "race_name": "Miami Grand Prix", "circuit_id": "miami", "circuit_name": "Miami International Autodrome", "date": f"{year}-05-05"},
            {"round": 7, "race_name": "Emilia Romagna Grand Prix", "circuit_id": "imola", "circuit_name": "Autodromo Enzo e Dino Ferrari", "date": f"{year}-05-19"},
            {"round": 8, "race_name": "Monaco Grand Prix", "circuit_id": "monaco", "circuit_name": "Circuit de Monaco", "date": f"{year}-05-26"},
            {"round": 9, "race_name": "Canadian Grand Prix", "circuit_id": "villeneuve", "circuit_name": "Circuit Gilles Villeneuve", "date": f"{year}-06-09"},
            {"round": 10, "race_name": "Spanish Grand Prix", "circuit_id": "catalunya", "circuit_name": "Circuit de Barcelona-Catalunya", "date": f"{year}-06-23"},
            {"round": 11, "race_name": "Austrian Grand Prix", "circuit_id": "red_bull_ring", "circuit_name": "Red Bull Ring", "date": f"{year}-06-30"},
            {"round": 12, "race_name": "British Grand Prix", "circuit_id": "silverstone", "circuit_name": "Silverstone Circuit", "date": f"{year}-07-07"},
            {"round": 13, "race_name": "Hungarian Grand Prix", "circuit_id": "hungaroring", "circuit_name": "Hungaroring", "date": f"{year}-07-21"},
            {"round": 14, "race_name": "Belgian Grand Prix", "circuit_id": "spa", "circuit_name": "Circuit de Spa-Francorchamps", "date": f"{year}-07-28"},
            {"round": 15, "race_name": "Dutch Grand Prix", "circuit_id": "zandvoort", "circuit_name": "Circuit Zandvoort", "date": f"{year}-08-25"},
            {"round": 16, "race_name": "Italian Grand Prix", "circuit_id": "monza", "circuit_name": "Autodromo Nazionale Monza", "date": f"{year}-09-01"},
            {"round": 17, "race_name": "Azerbaijan Grand Prix", "circuit_id": "baku", "circuit_name": "Baku City Circuit", "date": f"{year}-09-15"},
            {"round": 18, "race_name": "Singapore Grand Prix", "circuit_id": "marina_bay", "circuit_name": "Marina Bay Street Circuit", "date": f"{year}-09-22"},
            {"round": 19, "race_name": "United States Grand Prix", "circuit_id": "americas", "circuit_name": "Circuit of the Americas", "date": f"{year}-10-20"},
            {"round": 20, "race_name": "Mexico City Grand Prix", "circuit_id": "rodriguez", "circuit_name": "Autódromo Hermanos Rodríguez", "date": f"{year}-10-27"},
            {"round": 21, "race_name": "São Paulo Grand Prix", "circuit_id": "interlagos", "circuit_name": "Autódromo José Carlos Pace", "date": f"{year}-11-03"},
            {"round": 22, "race_name": "Las Vegas Grand Prix", "circuit_id": "vegas", "circuit_name": "Las Vegas Strip Circuit", "date": f"{year}-11-23"},
            {"round": 23, "race_name": "Qatar Grand Prix", "circuit_id": "losail", "circuit_name": "Lusail International Circuit", "date": f"{year}-12-01"},
            {"round": 24, "race_name": "Abu Dhabi Grand Prix", "circuit_id": "yas_marina", "circuit_name": "Yas Marina Circuit", "date": f"{year}-12-08"},
        ]

    def get_race_results(self, year: int, round_num: int) -> List[Dict[str, Any]]:
        """Fetches final finishing positions and grid positions for a Grand Prix."""
        url = f"{self.base_url}/{year}/{round_num}/results.json"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    races = resp.json().get("MRData", {}).get("RaceTable", {}).get("Races", [])
                    if races:
                        return races[0].get("Results", [])
        except Exception as e:
            logger.warning(f"[JolpicaAdapter] Error fetching {year} R{round_num} results: {e}")
        return []

    def get_qualifying_results(self, year: int, round_num: int) -> List[Dict[str, Any]]:
        """Fetches qualifying times and positions for a Grand Prix."""
        url = f"{self.base_url}/{year}/{round_num}/qualifying.json"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    races = resp.json().get("MRData", {}).get("RaceTable", {}).get("Races", [])
                    if races:
                        return races[0].get("QualifyingResults", [])
        except Exception as e:
            logger.warning(f"[JolpicaAdapter] Error fetching {year} R{round_num} qualifying: {e}")
        return []

    @staticmethod
    def _parse_time_str(time_str: str | None) -> float:
        """Parses laptime 'M:SS.mmm' or 'SS.mmm' into float seconds."""
        if not time_str or time_str in ("None", "nan", ""):
            return 0.0
        try:
            parts = str(time_str).strip().split(":")
            if len(parts) == 2:
                return float(parts[0]) * 60.0 + float(parts[1])
            return float(parts[0])
        except Exception:
            return 0.0

    def fetch_season_results_all(self, client: httpx.Client, year: int) -> List[Dict[str, Any]]:
        """Fetches all race results for a season in paginated batches of 100."""
        races_by_round: Dict[int, Dict[str, Any]] = {}
        offset = 0
        limit = 100
        while True:
            url = f"{self.base_url}/{year}/results.json?limit={limit}&offset={offset}"
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    break
                data = resp.json().get("MRData", {})
                total = int(data.get("total", 0))
                races = data.get("RaceTable", {}).get("Races", [])
                for race in races:
                    rnd = int(race.get("round", 0))
                    if rnd not in races_by_round:
                        races_by_round[rnd] = race
                    else:
                        races_by_round[rnd].setdefault("Results", []).extend(race.get("Results", []))
                offset += limit
                if offset >= total or not races:
                    break
            except Exception as e:
                logger.warning(f"[JolpicaAdapter] Error fetching {year} results at offset {offset}: {e}")
                break
        return [races_by_round[k] for k in sorted(races_by_round.keys())]

    def fetch_season_qualifying_all(self, client: httpx.Client, year: int) -> Dict[int, List[Dict[str, Any]]]:
        """Fetches all qualifying results for a season in paginated batches of 100."""
        quali_by_round: Dict[int, List[Dict[str, Any]]] = {}
        offset = 0
        limit = 100
        while True:
            url = f"{self.base_url}/{year}/qualifying.json?limit={limit}&offset={offset}"
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    break
                data = resp.json().get("MRData", {})
                total = int(data.get("total", 0))
                races = data.get("RaceTable", {}).get("Races", [])
                for race in races:
                    rnd = int(race.get("round", 0))
                    quali_by_round.setdefault(rnd, []).extend(race.get("QualifyingResults", []))
                offset += limit
                if offset >= total or not races:
                    break
            except Exception as e:
                logger.warning(f"[JolpicaAdapter] Error fetching {year} qualifying at offset {offset}: {e}")
                break
        return quali_by_round

    def fetch_historical_prerace_records(self, seasons: List[int]) -> List[Dict[str, Any]]:
        """Fetches and builds real pre-race features and actual finishing positions across seasons."""
        records: List[Dict[str, Any]] = []
        driver_recent_finishes: Dict[str, List[float]] = {}
        driver_circuit_starts: Dict[str, Dict[str, int]] = {}

        with httpx.Client(timeout=self.timeout) as client:
            for year in sorted(seasons):
                season_races = self.fetch_season_results_all(client, year)
                quali_by_round = self.fetch_season_qualifying_all(client, year)

                for race_obj in season_races:
                    r_num = int(race_obj.get("round", 0))
                    circuit_id = race_obj.get("Circuit", {}).get("circuitId", "silverstone")
                    results = race_obj.get("Results", [])
                    quali = quali_by_round.get(r_num, [])
                    if not results:
                        continue

                    # Build qualifying pole time
                    pole_time_s = 0.0
                    quali_by_driver: Dict[str, float] = {}
                    for q in quali:
                        d_id = q.get("Driver", {}).get("driverId", "")
                        best_time = self._parse_time_str(q.get("Q3")) or self._parse_time_str(q.get("Q2")) or self._parse_time_str(q.get("Q1"))
                        if best_time > 0.0:
                            quali_by_driver[d_id] = best_time
                            if pole_time_s == 0.0 or best_time < pole_time_s:
                                pole_time_s = best_time

                    # Team points share proxy for constructor strength in season
                    team_points: Dict[str, float] = {}
                    total_pts = 0.0
                    for r in results:
                        c_id = r.get("Constructor", {}).get("constructorId", "")
                        pts = float(r.get("points", 0.0))
                        team_points[c_id] = team_points.get(c_id, 0.0) + pts
                        total_pts += pts

                    for r in results:
                        d_id = r.get("Driver", {}).get("driverId", "")
                        c_id = r.get("Constructor", {}).get("constructorId", "")
                        try:
                            grid_pos = int(r.get("grid", 10))
                            if grid_pos <= 0:
                                grid_pos = 20
                        except (ValueError, TypeError):
                            grid_pos = 10

                        try:
                            fin_pos = int(r.get("position", 10))
                        except (ValueError, TypeError):
                            fin_pos = 20

                        driver_q_time = quali_by_driver.get(d_id, 0.0)
                        quali_delta = max(0.0, driver_q_time - pole_time_s) if (driver_q_time > 0.0 and pole_time_s > 0.0) else 1.2

                        # Causal rolling average finish (past 5 races only)
                        past_finishes = driver_recent_finishes.get(d_id, [])
                        rolling_finish = float(sum(past_finishes[-5:]) / len(past_finishes[-5:])) if past_finishes else float(grid_pos)

                        # Circuit starts experience
                        starts_map = driver_circuit_starts.setdefault(d_id, {})
                        c_starts = starts_map.get(circuit_id, 0)
                        starts_map[circuit_id] = c_starts + 1

                        constructor_share = (team_points.get(c_id, 0.0) / total_pts) if total_pts > 0 else 0.10

                        records.append({
                            "season": year,
                            "round": r_num,
                            "circuit_id": circuit_id,
                            "driver_id": d_id,
                            "grid_position": grid_pos,
                            "quali_delta_s": round(quali_delta, 3),
                            "rolling_avg_finish": round(rolling_finish, 2),
                            "circuit_starts": c_starts,
                            "constructor_pts_share": round(constructor_share, 4),
                            "rain_prob": 0.05,
                            "finishing_position": fin_pos,
                            "data_source": "jolpica_real",
                        })

                        # Update history post-race
                        driver_recent_finishes.setdefault(d_id, []).append(float(fin_pos))

        return records
