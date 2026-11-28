"""Jolpica (Ergast replacement) Ingestion Adapter for APEX Core.

Provides historical race schedules, drivers, constructors, and point standings
via the open Jolpica F1 REST API or local cache snapshot.
"""
from __future__ import annotations

import logging
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

JOLPICA_BASE_URL = "https://api.jolpi.ca/ergast/f1"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

CIRCUIT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "silverstone": (52.0786, -1.0169),
    "monza": (45.6156, 9.2811),
    "spa": (50.4372, 5.9714),
    "suzuka": (34.8431, 136.5410),
    "interlagos": (-23.7036, -46.6997),
    "catalunya": (41.5700, 2.2611),
    "imola": (44.3439, 11.7167),
    "red_bull_ring": (47.2197, 14.7647),
    "hungaroring": (47.5789, 19.2486),
    "zandvoort": (52.3888, 4.5409),
    "ricard": (43.2506, 5.7917),
    "bahrain": (26.0325, 50.5106),
    "losail": (25.4900, 51.4542),
    "yas_marina": (24.4672, 54.6031),
    "shanghai": (31.3389, 121.2200),
    "sepang": (2.7608, 101.7380),
    "americas": (30.1328, -97.6411),
    "rodriguez": (19.4042, -99.0907),
    "monaco": (43.7347, 7.4206),
    "marina_bay": (1.2914, 103.8640),
    "baku": (40.3725, 49.8533),
    "jeddah": (21.6319, 39.1044),
    "albert_park": (-37.8497, 144.9680),
    "miami": (25.9581, -80.2389),
    "vegas": (36.1147, -115.1730),
    "villeneuve": (45.5000, -73.5228),
    "madring": (40.4640, -3.6170),
}

CONSTRUCTOR_LINEAGE_ALIASES: Dict[str, str] = {
    "alfa": "sauber_audi",
    "sauber": "sauber_audi",
    "audi": "sauber_audi",
    "alphatauri": "rb_faenza",
    "rb": "rb_faenza",
    "racing_bulls": "rb_faenza",
}


class JolpicaAdapter:
    """Ingestion adapter for Jolpica / Ergast F1 data feeds."""

    @staticmethod
    def normalize_constructor_id(constructor_id: str) -> str:
        """Maps rebranded constructors (e.g. alfa->sauber->audi, alphatauri->rb) to one lineage ID."""
        cid = constructor_id.lower().strip()
        return CONSTRUCTOR_LINEAGE_ALIASES.get(cid, cid)

    def __init__(self, base_url: str = JOLPICA_BASE_URL, timeout_seconds: float = 12.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    def _get_with_retry(
        self,
        client: httpx.Client,
        url: str,
        max_retries: int = 3,
        base_delay: float = 0.5,
        backoff_factor: float = 2.0,
    ) -> Optional[httpx.Response]:
        """Performs HTTP GET with exponential backoff and jitter for transient failures and 429 rate limits."""
        for attempt in range(max_retries + 1):
            try:
                resp = client.get(url)
                if resp.status_code == 200:
                    return resp

                if resp.status_code in (429, 500, 502, 503, 504):
                    if attempt == max_retries:
                        logger.warning(
                            f"[JolpicaAdapter] HTTP {resp.status_code} for {url} after {max_retries} retries."
                        )
                        return resp

                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            delay = base_delay * (backoff_factor ** attempt)
                    else:
                        delay = base_delay * (backoff_factor ** attempt) + random.uniform(0.05, 0.25)

                    logger.info(
                        f"[JolpicaAdapter] HTTP {resp.status_code} on {url}. Retrying in {delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.warning(f"[JolpicaAdapter] Non-retryable HTTP {resp.status_code} for {url}")
                    return resp
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                if attempt == max_retries:
                    logger.warning(f"[JolpicaAdapter] Request error for {url} after {max_retries} retries: {exc}")
                    return None
                delay = base_delay * (backoff_factor ** attempt) + random.uniform(0.05, 0.25)
                logger.info(
                    f"[JolpicaAdapter] Network error ({exc}) on {url}. Retrying in {delay:.2f}s "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(delay)
        return None

    def get_season_races(self, year: int) -> List[Dict[str, Any]]:
        """Fetches calendar rounds for a given season."""
        url = f"{self.base_url}/{year}.json"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = self._get_with_retry(client, url)
                if resp and resp.status_code == 200:
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
                resp = self._get_with_retry(client, url)
                if resp and resp.status_code == 200:
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
                resp = self._get_with_retry(client, url)
                if resp and resp.status_code == 200:
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
            parts = time_str.strip().split(":")
            if len(parts) == 2:
                return float(parts[0]) * 60.0 + float(parts[1])
            return float(parts[0])
        except Exception:
            return 0.0

    def fetch_season_results_all(self, client: httpx.Client, year: int) -> List[Dict[str, Any]]:
        """Fetches all race results for a season in paginated batches of 100 with retry backoff."""
        races_by_round: Dict[int, Dict[str, Any]] = {}
        offset = 0
        limit = 100
        while True:
            url = f"{self.base_url}/{year}/results.json?limit={limit}&offset={offset}"
            try:
                resp = self._get_with_retry(client, url)
                if not resp or resp.status_code != 200:
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
        """Fetches all qualifying results for a season in paginated batches of 100 with retry backoff."""
        quali_by_round: Dict[int, List[Dict[str, Any]]] = {}
        offset = 0
        limit = 100
        while True:
            url = f"{self.base_url}/{year}/qualifying.json?limit={limit}&offset={offset}"
            try:
                resp = self._get_with_retry(client, url)
                if not resp or resp.status_code != 200:
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

    def fetch_race_rain_probability(
        self,
        client: httpx.Client,
        race_date: str,
        race_time: Optional[str],
        lat: Any,
        lon: Any,
    ) -> float:
        """Fetches historical race-day weather via Open-Meteo Archive and maps to [0.02, 0.95]."""
        if not race_date or lat is None or lon is None:
            return 0.05
        try:
            hr = int(str(race_time).split(":")[0]) if race_time and ":" in str(race_time) else 14
            resp = client.get(
                OPEN_METEO_ARCHIVE_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": race_date,
                    "end_date": race_date,
                    "hourly": "precipitation,cloud_cover",
                    "timezone": "GMT",
                },
            )
            if resp.status_code != 200:
                return 0.05
            hourly = resp.json().get("hourly", {})
            precip_list = hourly.get("precipitation") or []
            cloud_list = hourly.get("cloud_cover") or []
            if not precip_list:
                return 0.05

            lo = max(0, hr - 1)
            hi = min(len(precip_list), hr + 3)
            win_precip = sum(float(x or 0.0) for x in precip_list[lo:hi])
            day_precip = sum(float(x or 0.0) for x in precip_list)
            win_clouds = [float(x or 0.0) for x in cloud_list[lo:hi]] if cloud_list else [0.0]
            cloud_pct = sum(win_clouds) / max(1, len(win_clouds))

            precip_signal = 1.0 - math.exp(-0.65 * win_precip - 0.08 * day_precip)
            prob = 0.02 + 0.15 * (cloud_pct / 100.0) + 0.80 * precip_signal
            return round(min(0.95, max(0.02, prob)), 3)
        except Exception as exc:
            logger.debug(f"[JolpicaAdapter] Open-Meteo lookup failed for {race_date}: {exc}")
            return 0.05

    def fetch_live_circuit_weather(self, circuit_id: str) -> Dict[str, Any]:
        """Fetches live Open-Meteo forecast for a circuit, with safe seasonal fallback."""
        from core.features.feature_builder import normalize_circuit_id

        cid = normalize_circuit_id(circuit_id)
        coords = CIRCUIT_COORDINATES.get(cid)
        fallback = {
            "circuit_id": cid,
            "source": "fallback",
            "rain_probability": 0.12 if cid in ("silverstone", "spa", "interlagos", "suzuka", "sepang") else 0.08,
            "weather_transition": False,
            "air_temp_c": 23.0,
            "track_temp_c": 32.0,
        }
        if not coords:
            return fallback

        lat, lon = coords
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = self._get_with_retry(
                    client,
                    f"{OPEN_METEO_FORECAST_URL}?latitude={lat}&longitude={lon}"
                    "&current=temperature_2m,precipitation,cloud_cover"
                    "&hourly=precipitation_probability,temperature_2m"
                    "&forecast_days=2&timezone=GMT",
                )
            if not resp or resp.status_code != 200:
                return fallback
            payload = resp.json()
            current = payload.get("current", {})
            hourly = payload.get("hourly", {})
            air_temp = float(current.get("temperature_2m", 23.0))
            cloud_pct = float(current.get("cloud_cover", 25.0))
            probs = [float(p) for p in (hourly.get("precipitation_probability") or [])[:12] if p is not None]
            max_prob = max(probs) / 100.0 if probs else 0.05
            min_prob = min(probs) / 100.0 if probs else 0.05
            rain_prob = round(min(0.95, max(0.02, 0.7 * max_prob + 0.15 * (cloud_pct / 100.0))), 3)
            weather_transition = bool((max_prob - min_prob) >= 0.30 and max_prob >= 0.35)
            solar_gain = 3.0 if rain_prob >= 0.45 else max(4.0, 11.0 * (1.0 - cloud_pct / 120.0))
            return {
                "circuit_id": cid,
                "source": "open_meteo_live",
                "rain_probability": rain_prob,
                "weather_transition": weather_transition,
                "air_temp_c": round(air_temp, 1),
                "track_temp_c": round(air_temp + solar_gain, 1),
            }
        except Exception as exc:
            logger.debug(f"[JolpicaAdapter] Live Open-Meteo forecast failed for {cid}: {exc}")
            return fallback

    def fetch_historical_prerace_records(self, seasons: List[int]) -> List[Dict[str, Any]]:
        """Fetches and builds strictly causal pre-race features and actual finishing positions across seasons."""
        records: List[Dict[str, Any]] = []
        driver_recent_finishes: Dict[str, List[float]] = {}
        driver_recent_dnfs: Dict[str, List[float]] = {}
        driver_circuit_starts: Dict[str, Dict[str, int]] = {}
        constructor_recent_gains: Dict[str, List[float]] = {}
        prior_season_team_share: Dict[str, float] = {}

        with httpx.Client(timeout=self.timeout) as client:
            for year in sorted(seasons):
                season_races = self.fetch_season_results_all(client, year)
                quali_by_round = self.fetch_season_qualifying_all(client, year)
                season_team_points: Dict[str, float] = {}
                season_total_pts = 0.0

                for race_obj in season_races:
                    r_num = int(race_obj.get("round", 0))
                    circuit_info = race_obj.get("Circuit", {})
                    circuit_id = circuit_info.get("circuitId", "silverstone")
                    loc = circuit_info.get("Location", {})
                    race_rain_prob = self.fetch_race_rain_probability(
                        client=client,
                        race_date=race_obj.get("date", ""),
                        race_time=race_obj.get("time"),
                        lat=loc.get("lat"),
                        lon=loc.get("long"),
                    )
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

                    race_team_points: Dict[str, float] = {}
                    race_total_pts = 0.0
                    post_race_updates: List[tuple[str, str, float, float, float]] = []

                    for r in results:
                        d_id = r.get("Driver", {}).get("driverId", "")
                        raw_c_id = r.get("Constructor", {}).get("constructorId", "")
                        c_id = self.normalize_constructor_id(raw_c_id)
                        pts = float(r.get("points", 0.0))
                        race_team_points[c_id] = race_team_points.get(c_id, 0.0) + pts
                        race_total_pts += pts

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

                        status_str = str(r.get("status", "Finished"))
                        is_dnf = 0.0 if (status_str == "Finished" or "Lap" in status_str) else 1.0

                        driver_q_time = quali_by_driver.get(d_id, 0.0)
                        quali_delta = max(0.0, driver_q_time - pole_time_s) if (driver_q_time > 0.0 and pole_time_s > 0.0) else 1.2

                        # Strictly causal rolling average finish (past 5 races only)
                        past_finishes = driver_recent_finishes.get(d_id, [])
                        rolling_finish = (sum(past_finishes[-5:]) / len(past_finishes[-5:])) if past_finishes else float(grid_pos)

                        # Strictly causal rolling DNF rate (past 10 races)
                        past_dnfs = driver_recent_dnfs.get(d_id, [])
                        dnf_rate = (sum(past_dnfs[-10:]) / len(past_dnfs[-10:])) if past_dnfs else 0.08

                        # Strictly causal constructor qualifying-to-race position gain (past 10 entries)
                        past_gains = constructor_recent_gains.get(c_id, [])
                        c_race_gain = (sum(past_gains[-10:]) / len(past_gains[-10:])) if past_gains else 0.0

                        # Circuit starts experience prior to this race
                        starts_map = driver_circuit_starts.setdefault(d_id, {})
                        c_starts = starts_map.get(circuit_id, 0)
                        starts_map[circuit_id] = c_starts + 1

                        # Strictly causal constructor points share PRIOR to current round
                        if season_total_pts > 0.0:
                            constructor_share = season_team_points.get(c_id, 0.0) / season_total_pts
                        else:
                            constructor_share = prior_season_team_share.get(c_id, 0.10)

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
                            "rain_prob": race_rain_prob,
                            "driver_dnf_rate": round(dnf_rate, 3),
                            "constructor_race_gain": round(c_race_gain, 3),
                            "finishing_position": fin_pos,
                            "data_source": "jolpica_real",
                        })

                        post_race_updates.append((d_id, c_id, float(fin_pos), is_dnf, float(grid_pos - fin_pos)))

                    # Update all causal history strictly AFTER the race finishes
                    for d_id, c_id, fin_f, is_dnf, pos_gain in post_race_updates:
                        driver_recent_finishes.setdefault(d_id, []).append(fin_f)
                        driver_recent_dnfs.setdefault(d_id, []).append(is_dnf)
                        constructor_recent_gains.setdefault(c_id, []).append(pos_gain)

                    for c_id, r_pts in race_team_points.items():
                        season_team_points[c_id] = season_team_points.get(c_id, 0.0) + r_pts
                    season_total_pts += race_total_pts

                if season_total_pts > 0.0:
                    prior_season_team_share = {
                        c_id: pts / season_total_pts for c_id, pts in season_team_points.items()
                    }

        return records
