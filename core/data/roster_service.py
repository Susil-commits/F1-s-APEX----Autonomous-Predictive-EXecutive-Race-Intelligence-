"""APEX Dynamic Driver Roster & Profile Service.

Decouples hardcoded driver definitions from prediction and API routing.
Supports dynamic mid-season driver substitutions (e.g. reserve drivers),
live constructor point standings updates, and telemetry profile syncing.
"""
from __future__ import annotations

import copy
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ROSTER_STORAGE_FILE = os.path.join(
    os.path.dirname(__file__), "driver_roster_state.json"
)

# Canonical 2024/2025/2026 Formula 1 Driver Profiles
DEFAULT_DRIVER_ROSTER: Dict[str, Dict[str, Any]] = {
    "VER": {
        "code": "VER",
        "name": "Max Verstappen",
        "first_name": "Max",
        "last_name": "VERSTAPPEN",
        "team": "Red Bull Racing",
        "number": 1,
        "color": "#3671C6",
        "country": "🇳🇱",
        "default_grid": 1,
        "photo": "/f1/drivers/VER.webp",
        "pts_share": 0.28,
        "rolling_avg": 2.1,
        "starts": 10,
        "is_active": True,
    },
    "NOR": {
        "code": "NOR",
        "name": "Lando Norris",
        "first_name": "Lando",
        "last_name": "NORRIS",
        "team": "McLaren",
        "number": 4,
        "color": "#FF8000",
        "country": "🇬🇧",
        "default_grid": 2,
        "photo": "/f1/drivers/NOR.webp",
        "pts_share": 0.24,
        "rolling_avg": 2.8,
        "starts": 6,
        "is_active": True,
    },
    "LEC": {
        "code": "LEC",
        "name": "Charles Leclerc",
        "first_name": "Charles",
        "last_name": "LECLERC",
        "team": "Ferrari",
        "number": 16,
        "color": "#E80020",
        "country": "🇲🇨",
        "default_grid": 3,
        "photo": "/f1/drivers/LEC.webp",
        "pts_share": 0.21,
        "rolling_avg": 3.4,
        "starts": 7,
        "is_active": True,
    },
    "PIA": {
        "code": "PIA",
        "name": "Oscar Piastri",
        "first_name": "Oscar",
        "last_name": "PIASTRI",
        "team": "McLaren",
        "number": 81,
        "color": "#FF8000",
        "country": "🇦🇺",
        "default_grid": 4,
        "photo": "/f1/drivers/PIA.webp",
        "pts_share": 0.24,
        "rolling_avg": 4.1,
        "starts": 2,
        "is_active": True,
    },
    "SAI": {
        "code": "SAI",
        "name": "Carlos Sainz",
        "first_name": "Carlos",
        "last_name": "SAINZ",
        "team": "Williams",
        "number": 55,
        "color": "#64C4FF",
        "country": "🇪🇸",
        "default_grid": 8,
        "photo": "/f1/drivers/SAI.webp",
        "pts_share": 0.21,
        "rolling_avg": 4.8,
        "starts": 9,
        "is_active": True,
    },
    "HAM": {
        "code": "HAM",
        "name": "Lewis Hamilton",
        "first_name": "Lewis",
        "last_name": "HAMILTON",
        "team": "Ferrari",
        "number": 44,
        "color": "#E80020",
        "country": "🇬🇧",
        "default_grid": 5,
        "photo": "/f1/drivers/HAM.webp",
        "pts_share": 0.16,
        "rolling_avg": 5.2,
        "starts": 17,
        "is_active": True,
    },
    "RUS": {
        "code": "RUS",
        "name": "George Russell",
        "first_name": "George",
        "last_name": "RUSSELL",
        "team": "Mercedes",
        "number": 63,
        "color": "#00A19B",
        "country": "🇬🇧",
        "default_grid": 6,
        "photo": "/f1/drivers/RUS.webp",
        "pts_share": 0.16,
        "rolling_avg": 5.8,
        "starts": 6,
        "is_active": True,
    },
    "ANT": {
        "code": "ANT",
        "name": "Kimi Antonelli",
        "first_name": "Kimi",
        "last_name": "ANTONELLI",
        "team": "Mercedes",
        "number": 12,
        "color": "#00A19B",
        "country": "🇮🇹",
        "default_grid": 7,
        "photo": "/f1/drivers/ANT.webp",
        "pts_share": 0.16,
        "rolling_avg": 7.0,
        "starts": 0,
        "is_active": True,
    },
    "PER": {
        "code": "PER",
        "name": "Sergio Perez",
        "first_name": "Sergio",
        "last_name": "PEREZ",
        "team": "Red Bull Racing",
        "number": 11,
        "color": "#3671C6",
        "country": "🇲🇽",
        "default_grid": 8,
        "photo": "/f1/drivers/PER.webp",
        "pts_share": 0.28,
        "rolling_avg": 7.4,
        "starts": 13,
        "is_active": True,
    },
    "ALO": {
        "code": "ALO",
        "name": "Fernando Alonso",
        "first_name": "Fernando",
        "last_name": "ALONSO",
        "team": "Aston Martin",
        "number": 14,
        "color": "#229971",
        "country": "🇪🇸",
        "default_grid": 9,
        "photo": "/f1/drivers/ALO.webp",
        "pts_share": 0.08,
        "rolling_avg": 8.5,
        "starts": 19,
        "is_active": True,
    },
    "STR": {
        "code": "STR",
        "name": "Lance Stroll",
        "first_name": "Lance",
        "last_name": "STROLL",
        "team": "Aston Martin",
        "number": 18,
        "color": "#229971",
        "country": "🇨🇦",
        "default_grid": 10,
        "photo": "/f1/drivers/STR.webp",
        "pts_share": 0.08,
        "rolling_avg": 11.2,
        "starts": 7,
        "is_active": True,
    },
    "TSU": {
        "code": "TSU",
        "name": "Yuki Tsunoda",
        "first_name": "Yuki",
        "last_name": "TSUNODA",
        "team": "RB",
        "number": 22,
        "color": "#6692FF",
        "country": "🇯🇵",
        "default_grid": 11,
        "photo": "/f1/drivers/TSU.webp",
        "pts_share": 0.04,
        "rolling_avg": 11.8,
        "starts": 4,
        "is_active": True,
    },
    "HUL": {
        "code": "HUL",
        "name": "Nico Hulkenberg",
        "first_name": "Nico",
        "last_name": "HULKENBERG",
        "team": "Kick Sauber",
        "number": 27,
        "color": "#52E252",
        "country": "🇩🇪",
        "default_grid": 13,
        "photo": "/f1/drivers/HUL.webp",
        "pts_share": 0.03,
        "rolling_avg": 12.1,
        "starts": 11,
        "is_active": True,
    },
    "ALB": {
        "code": "ALB",
        "name": "Alexander Albon",
        "first_name": "Alexander",
        "last_name": "ALBON",
        "team": "Williams",
        "number": 23,
        "color": "#64C4FF",
        "country": "🇹🇭",
        "default_grid": 12,
        "photo": "/f1/drivers/ALB.webp",
        "pts_share": 0.02,
        "rolling_avg": 12.8,
        "starts": 5,
        "is_active": True,
    },
    "RIC": {
        "code": "RIC",
        "name": "Daniel Ricciardo",
        "first_name": "Daniel",
        "last_name": "RICCIARDO",
        "team": "RB",
        "number": 3,
        "color": "#6692FF",
        "country": "🇦🇺",
        "default_grid": 14,
        "photo": "/f1/drivers/RIC.webp",
        "pts_share": 0.04,
        "rolling_avg": 13.2,
        "starts": 12,
        "is_active": False,
    },
    "GAS": {
        "code": "GAS",
        "name": "Pierre Gasly",
        "first_name": "Pierre",
        "last_name": "GASLY",
        "team": "Alpine",
        "number": 10,
        "color": "#0093CC",
        "country": "🇫🇷",
        "default_grid": 15,
        "photo": "/f1/drivers/GAS.webp",
        "pts_share": 0.02,
        "rolling_avg": 13.9,
        "starts": 7,
        "is_active": True,
    },
    "OCO": {
        "code": "OCO",
        "name": "Esteban Ocon",
        "first_name": "Esteban",
        "last_name": "OCON",
        "team": "Alpine",
        "number": 31,
        "color": "#0093CC",
        "country": "🇫🇷",
        "default_grid": 16,
        "photo": "/f1/drivers/OCO.webp",
        "pts_share": 0.02,
        "rolling_avg": 14.1,
        "starts": 7,
        "is_active": True,
    },
    "MAG": {
        "code": "MAG",
        "name": "Kevin Magnussen",
        "first_name": "Kevin",
        "last_name": "MAGNUSSEN",
        "team": "Haas",
        "number": 20,
        "color": "#B6BABD",
        "country": "🇩🇰",
        "default_grid": 17,
        "photo": "/f1/drivers/MAG.webp",
        "pts_share": 0.03,
        "rolling_avg": 14.5,
        "starts": 8,
        "is_active": True,
    },
    "ZHO": {
        "code": "ZHO",
        "name": "Zhou Guanyu",
        "first_name": "Guanyu",
        "last_name": "ZHOU",
        "team": "Kick Sauber",
        "number": 24,
        "color": "#52E252",
        "country": "🇨🇳",
        "default_grid": 18,
        "photo": "/f1/drivers/ZHO.webp",
        "pts_share": 0.00,
        "rolling_avg": 16.8,
        "starts": 3,
        "is_active": True,
    },
    "BOT": {
        "code": "BOT",
        "name": "Valtteri Bottas",
        "first_name": "Valtteri",
        "last_name": "BOTTAS",
        "team": "Kick Sauber",
        "number": 77,
        "color": "#52E252",
        "country": "🇫🇮",
        "default_grid": 19,
        "photo": "/f1/drivers/BOT.webp",
        "pts_share": 0.00,
        "rolling_avg": 16.2,
        "starts": 11,
        "is_active": True,
    },
    "BEA": {
        "code": "BEA",
        "name": "Oliver Bearman",
        "first_name": "Oliver",
        "last_name": "BEARMAN",
        "team": "Haas",
        "number": 87,
        "color": "#B6BABD",
        "country": "🇬🇧",
        "default_grid": 14,
        "photo": "/f1/drivers/BEA.webp",
        "pts_share": 0.02,
        "rolling_avg": 11.0,
        "starts": 2,
        "is_active": True,
    },
    "LAW": {
        "code": "LAW",
        "name": "Liam Lawson",
        "first_name": "Liam",
        "last_name": "LAWSON",
        "team": "RB",
        "number": 30,
        "color": "#6692FF",
        "country": "🇳🇿",
        "default_grid": 12,
        "photo": "/f1/drivers/LAW.webp",
        "pts_share": 0.03,
        "rolling_avg": 10.5,
        "starts": 5,
        "is_active": True,
    },
    "COL": {
        "code": "COL",
        "name": "Franco Colapinto",
        "first_name": "Franco",
        "last_name": "COLAPINTO",
        "team": "Williams",
        "number": 43,
        "color": "#64C4FF",
        "country": "🇦🇷",
        "default_grid": 13,
        "photo": "/f1/drivers/COL.webp",
        "pts_share": 0.03,
        "rolling_avg": 11.5,
        "starts": 6,
        "is_active": True,
    },
}


class DriverProfile(BaseModel):
    code: str
    name: str
    first_name: str
    last_name: str
    team: str
    number: int
    color: str
    country: str
    default_grid: int = Field(ge=1, le=20)
    photo: str
    pts_share: float = Field(ge=0.0, le=1.0)
    rolling_avg: float = Field(ge=1.0, le=20.0)
    starts: int = Field(ge=0)
    is_active: bool = True


class DriverRosterService:
    """Thread-safe dynamic driver roster manager."""

    def __init__(self, persistence_file: str = ROSTER_STORAGE_FILE):
        self.persistence_file = persistence_file
        self._lock = threading.RLock()
        self._roster: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Loads state from JSON storage or initializes with defaults."""
        with self._lock:
            if os.path.exists(self.persistence_file):
                try:
                    with open(self.persistence_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and data:
                        self._roster = data
                        logger.info("Loaded %d driver profiles from persistent store", len(self._roster))
                        return
                except Exception as exc:
                    logger.warning("Failed reading roster store, falling back to defaults: %s", exc)

            self._roster = copy.deepcopy(DEFAULT_DRIVER_ROSTER)

    def _persist(self) -> None:
        """Saves current roster state to disk atomically."""
        try:
            tmp_path = f"{self.persistence_file}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._roster, f, indent=2)
            os.replace(tmp_path, self.persistence_file)
        except Exception as exc:
            logger.error("Failed persisting driver roster state: %s", exc)

    def get_driver(self, driver_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves profile for a driver code (case-insensitive)."""
        code = driver_id.upper().strip()
        with self._lock:
            driver = self._roster.get(code)
            return copy.deepcopy(driver) if driver else None

    def get_all_drivers(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Returns all drivers ordered by default grid position."""
        with self._lock:
            drivers = list(self._roster.values())
            if active_only:
                drivers = [d for d in drivers if d.get("is_active", True)]
            drivers.sort(key=lambda x: (x.get("default_grid", 20), x.get("name", "")))
            return copy.deepcopy(drivers)

    def update_driver(self, profile: DriverProfile) -> Dict[str, Any]:
        """Adds or updates a driver profile dynamically."""
        with self._lock:
            code = profile.code.upper().strip()
            self._roster[code] = profile.model_dump()
            self._persist()
            return copy.deepcopy(self._roster[code])

    def reset_to_defaults(self) -> None:
        """Resets the roster state back to canonical default F1 grid."""
        with self._lock:
            self._roster = copy.deepcopy(DEFAULT_DRIVER_ROSTER)
            self._persist()

    def sync_from_jolpica(self, year: int = 2026, timeout_seconds: float = 10.0) -> Dict[str, Any]:
        """Synchronizes active driver lineup, teams, and constructor points share from Jolpica standings."""
        import httpx

        base_url = "https://api.jolpi.ca/ergast/f1"
        with httpx.Client(timeout=timeout_seconds) as client:
            d_resp = client.get(f"{base_url}/{year}/driverStandings.json")
            c_resp = client.get(f"{base_url}/{year}/constructorStandings.json")
            d_resp.raise_for_status()
            c_resp.raise_for_status()

        d_lists = d_resp.json().get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        c_lists = c_resp.json().get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        if not d_lists:
            raise ValueError(f"No Jolpica driver standings found for season {year}")

        constructor_pts: Dict[str, float] = {}
        total_c_pts = 0.0
        if c_lists:
            for c_entry in c_lists[0].get("ConstructorStandings", []):
                c_name = c_entry.get("Constructor", {}).get("name", "")
                pts = float(c_entry.get("points", 0.0))
                constructor_pts[c_name] = pts
                total_c_pts += pts

        synced_codes = set()
        with self._lock:
            for idx, entry in enumerate(d_lists[0].get("DriverStandings", []), start=1):
                drv = entry.get("Driver", {})
                code = str(drv.get("code") or drv.get("driverId", "")[:3]).upper().strip()
                if len(code) != 3:
                    continue
                synced_codes.add(code)
                constructors = entry.get("Constructors") or [{}]
                team_name = str(constructors[-1].get("name", "F1 Competitor"))
                c_pts = constructor_pts.get(team_name, 0.0)
                pts_share = round(min(0.50, max(0.01, c_pts / total_c_pts)), 4) if total_c_pts > 0 else 0.05

                existing = self._roster.get(code, {})
                first_name = str(drv.get("givenName", existing.get("first_name", code)))
                last_name = str(drv.get("familyName", existing.get("last_name", code))).upper()
                pos_val = int(entry.get("position", idx)) if str(entry.get("position", "")).isdigit() else idx
                default_grid = min(20, max(1, pos_val))

                self._roster[code] = {
                    "code": code,
                    "name": f"{first_name} {last_name.title()}",
                    "first_name": first_name,
                    "last_name": last_name,
                    "team": team_name,
                    "number": int(drv.get("permanentNumber", existing.get("number", 0))) if str(drv.get("permanentNumber", "")).isdigit() else int(existing.get("number", 0)),
                    "color": existing.get("color", "#E10600"),
                    "country": existing.get("country", "🏁"),
                    "default_grid": default_grid,
                    "photo": existing.get("photo", f"/f1/drivers/{code}.webp"),
                    "pts_share": pts_share,
                    "rolling_avg": float(existing.get("rolling_avg", min(20.0, float(default_grid)))),
                    "starts": int(existing.get("starts", 1)),
                    "is_active": True,
                }

            for code, profile in self._roster.items():
                if code not in synced_codes:
                    profile["is_active"] = False

            self._persist()

        return {
            "year": year,
            "synced_drivers": len(synced_codes),
            "active_codes": sorted(synced_codes),
        }


_GLOBAL_ROSTER_SERVICE: Optional[DriverRosterService] = None
_SERVICE_INIT_LOCK = threading.Lock()


def get_roster_service() -> DriverRosterService:
    """Singleton factory for DriverRosterService."""
    global _GLOBAL_ROSTER_SERVICE
    if _GLOBAL_ROSTER_SERVICE is None:
        with _SERVICE_INIT_LOCK:
            if _GLOBAL_ROSTER_SERVICE is None:
                _GLOBAL_ROSTER_SERVICE = DriverRosterService()
    return _GLOBAL_ROSTER_SERVICE
