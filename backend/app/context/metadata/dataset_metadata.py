"""Dataset Metadata Registry for APEX Decision Intelligence.

Provides governance cards, source tracking, schema definitions, and quality metrics
for all telemetry, weather, and evaluation datasets used in APEX.
"""
from typing import Dict, List, Optional
from backend.app.context.schemas import DatasetMetadataCard


DATASET_REGISTRY: Dict[str, DatasetMetadataCard] = {
    "fastf1_2018_2024_gold": DatasetMetadataCard(
        dataset_id="dataset:fastf1_2018_2024_gold_v1.0",
        name="FastF1 Official Grand Prix Telemetry Gold Corpus",
        version="v1.0",
        source_apis=["FastF1 Python API", "Official F1 Live Timing Feed"],
        total_laps=6999,
        circuits_covered=[
            "Silverstone", "Spa-Francorchamps", "Monza", "Suzuka",
            "Circuit de Barcelona-Catalunya", "Red Bull Ring", "Interlagos", "Zandvoort"
        ],
        seasons_covered=[2018, 2019, 2020, 2021, 2022, 2023, 2024],
        schema_fields=[
            "session_id", "lap_number", "driver_number", "compound", "tyre_age_laps",
            "lap_time_seconds", "s1_seconds", "s2_seconds", "s3_seconds", "track_temp_c",
            "air_temp_c", "humidity_pct", "rainfall", "speed_i1", "speed_i2", "speed_fl",
            "stint", "pit_in_time", "pit_out_time", "is_accurate"
        ],
        data_quality_score=99.2,
        status="validated",
        created_at="2024-02-01T00:00:00Z",
    ),

    "jolpica_ergast_historical": DatasetMetadataCard(
        dataset_id="dataset:jolpica_ergast_historical_v1.0",
        name="Jolpica / Ergast F1 Historical Race Records & Pit Loss Baselines",
        version="v1.0",
        source_apis=["Jolpica F1 API", "Ergast Developer API"],
        total_laps=18450,
        circuits_covered=[
            "Monaco", "Silverstone", "Spa", "Monza", "Hungaroring", "Suzuka", "Interlagos", "Marina Bay"
        ],
        seasons_covered=[2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        schema_fields=[
            "season", "round", "circuit_id", "pit_stop_duration_s", "pit_lane_loss_delta_s",
            "driver_id", "grid_position", "finish_position", "status", "points"
        ],
        data_quality_score=99.5,
        status="validated",
        created_at="2024-02-15T00:00:00Z",
    ),

    "f1_weather_barometric_historical": DatasetMetadataCard(
        dataset_id="dataset:f1_weather_barometric_historical_v2.0",
        name="High-Frequency Barometric Doppler & Radar Dataset",
        version="v2.0",
        source_apis=["FIA Track Meteorology Stations", "Open-Meteo Historic High-Res"],
        total_laps=12500,
        circuits_covered=["Silverstone", "Spa", "Zandvoort", "Interlagos", "Monaco", "Montreal"],
        seasons_covered=[2019, 2020, 2021, 2022, 2023, 2024],
        schema_fields=[
            "timestamp_utc", "circuit", "air_temp_c", "track_temp_c", "pressure_hpa",
            "rain_intensity_mm_hr", "radar_reflectivity_dbz", "track_wetness_index", "drying_rate"
        ],
        data_quality_score=98.7,
        status="validated",
        created_at="2024-03-20T00:00:00Z",
    ),

    "strategy_history_undercuts": DatasetMetadataCard(
        dataset_id="dataset:strategy_history_undercuts_v1.0",
        name="Strategy History & Undercut Replay Archive",
        version="v1.0",
        source_apis=["APEX Strategy Replay Engine", "FastF1 Sector Database"],
        total_laps=8200,
        circuits_covered=["Silverstone", "Monaco", "Spa", "Zandvoort", "Hungaroring"],
        seasons_covered=[2019, 2020, 2021, 2022, 2023, 2024],
        schema_fields=[
            "race_id", "in_lap", "out_lap", "delta_to_rival_s", "undercut_success_flag",
            "compound_fitted", "stint_length", "traffic_rejoin_margin_s"
        ],
        data_quality_score=99.1,
        status="validated",
        created_at="2024-03-25T00:00:00Z",
    ),

    "live_telemetry_stream_60hz": DatasetMetadataCard(
        dataset_id="dataset:live_telemetry_stream_60hz_v1.0",
        name="Live 60Hz High-Frequency Telemetry Ingestion Stream",
        version="v1.0",
        source_apis=["FastF1 Live Telemetry Stream", "APEX CAN-Bus Bridge"],
        total_laps=1400,
        circuits_covered=["Silverstone 2023", "Spa 2023", "Zandvoort 2023"],
        seasons_covered=[2023, 2024],
        schema_fields=[
            "car_id", "timestamp_ms", "speed_kmh", "throttle_pct", "brake_pct",
            "gear", "steer_deg", "drs_status", "tyre_surface_temp_c", "tyre_core_temp_c"
        ],
        data_quality_score=99.8,
        status="validated",
        created_at="2024-04-01T00:00:00Z",
    ),

    "heldout_1400_fastf1_laps": DatasetMetadataCard(
        dataset_id="dataset:heldout_1400_fastf1_laps_v1.0",
        name="Held-Out FastF1 Telemetry Evaluation Split (Zero-Leakage)",
        version="v1.0",
        source_apis=["FastF1 Official 2023-2024 Sessions"],
        total_laps=1400,
        circuits_covered=[
            "Silverstone 2023", "Spa-Francorchamps 2023", "Monza 2023", "Zandvoort 2023"
        ],
        seasons_covered=[2023, 2024],
        schema_fields=[
            "lap_number", "compound", "tyre_age_laps", "lap_time_bleed_actual_s",
            "thermal_cliff_flag", "track_temp_c", "fuel_burn_kg", "rejoin_traffic_gap_s"
        ],
        data_quality_score=100.0,
        status="validated",
        created_at="2024-03-01T00:00:00Z",
    ),
}


def get_dataset_metadata(dataset_key: str) -> Optional[DatasetMetadataCard]:
    """Retrieve dataset card by key or dataset_id."""
    for key, card in DATASET_REGISTRY.items():
        if key == dataset_key or card.dataset_id == dataset_key:
            return card
    return None


def list_all_dataset_metadata() -> List[DatasetMetadataCard]:
    """List all registered dataset cards."""
    return list(DATASET_REGISTRY.values())
