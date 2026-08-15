"""Track configurations and circuit database for APEX."""
from typing import Dict, List
from backend.app.simulator.models import TrackConfig


TRACKS: Dict[str, TrackConfig] = {
    "silverstone": TrackConfig(
        name="Silverstone Circuit",
        country="Great Britain",
        total_laps=52,
        lap_distance_km=5.891,
        base_lap_time_s=88.50,
        pit_lane_delta_s=21.50,
        vsc_pit_advantage_s=9.5,
        sc_pit_advantage_s=12.5,
        tyre_wear_factor=1.15,
        rain_probability_base=0.18,
    ),
    "monza": TrackConfig(
        name="Autodromo Nazionale Monza",
        country="Italy",
        total_laps=53,
        lap_distance_km=5.793,
        base_lap_time_s=81.00,
        pit_lane_delta_s=24.00,
        vsc_pit_advantage_s=10.0,
        sc_pit_advantage_s=13.0,
        tyre_wear_factor=0.85,
        rain_probability_base=0.10,
    ),
    "spa": TrackConfig(
        name="Circuit de Spa-Francorchamps",
        country="Belgium",
        total_laps=44,
        lap_distance_km=7.004,
        base_lap_time_s=104.50,
        pit_lane_delta_s=22.00,
        vsc_pit_advantage_s=9.5,
        sc_pit_advantage_s=12.5,
        tyre_wear_factor=1.25,
        rain_probability_base=0.30,
    ),
    "monaco": TrackConfig(
        name="Circuit de Monaco",
        country="Monaco",
        total_laps=78,
        lap_distance_km=3.337,
        base_lap_time_s=73.20,
        pit_lane_delta_s=19.50,
        vsc_pit_advantage_s=8.5,
        sc_pit_advantage_s=11.0,
        tyre_wear_factor=0.65,
        rain_probability_base=0.12,
    ),
    "interlagos": TrackConfig(
        name="Autódromo José Carlos Pace (Interlagos)",
        country="Brazil",
        total_laps=71,
        lap_distance_km=4.309,
        base_lap_time_s=70.50,
        pit_lane_delta_s=21.00,
        vsc_pit_advantage_s=9.0,
        sc_pit_advantage_s=12.0,
        tyre_wear_factor=1.10,
        rain_probability_base=0.25,
    ),
}


def get_track(name: str = "silverstone") -> TrackConfig:
    """Retrieve a track configuration by key (defaults to Silverstone)."""
    return TRACKS.get(name.lower(), TRACKS["silverstone"])


def list_available_tracks() -> List[str]:
    """List all available track identifiers."""
    return list(TRACKS.keys())
