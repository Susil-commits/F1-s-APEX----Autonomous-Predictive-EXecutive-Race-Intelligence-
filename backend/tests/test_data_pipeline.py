"""Unit tests for Phase 1 Data Pipeline: loaders, cleaners, features, validation, and versioning."""
import os

import pandas as pd
import pytest

from backend.training.data.raw_storage import RawStorageManager
from backend.training.datasets.dataset_builder import DatasetBuilder
from backend.training.datasets.dataset_validator import (
    DatasetValidationError,
    DatasetValidator,
)
from backend.training.datasets.dataset_version import (
    DatasetVersionRegistry,
)
from backend.training.features.driver_features import compute_driver_features
from backend.training.features.opponent_features import compute_opponent_features
from backend.training.features.strategy_features import compute_strategy_features
from backend.training.features.tyre_features import compute_tyre_features
from backend.training.features.vehicle_features import compute_vehicle_features
from backend.training.features.weather_features import compute_weather_features
from backend.training.preprocessing.clean_laps import clean_laps_dataframe
from backend.training.preprocessing.clean_telemetry import (
    aggregate_lap_telemetry,
    clean_telemetry_dataframe,
)


def test_raw_storage_manager(tmp_path):
    storage = RawStorageManager(storage_dir=str(tmp_path))
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    filepath = storage.save_raw_table(df, "test_cat", "test_id", {"meta": 123})
    assert os.path.exists(filepath)
    assert storage.exists("test_cat", "test_id")
    loaded = storage.load_raw_table("test_cat", "test_id")
    assert loaded is not None
    assert len(loaded) == 3


def test_clean_laps_filtering():
    raw = pd.DataFrame([
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 1, "LapTime": pd.Timedelta(seconds=90.0), "Stint": 1, "TrackStatus": "1", "IsAccurate": True},
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 2, "LapTime": pd.Timedelta(seconds=90.5), "Stint": 1, "PitInTime": pd.Timedelta(seconds=90.0), "TrackStatus": "1", "IsAccurate": True},
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 3, "LapTime": pd.Timedelta(seconds=120.0), "Stint": 2, "TrackStatus": "4", "IsAccurate": True},
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 4, "LapTime": pd.Timedelta(seconds=91.0), "Stint": 2, "TrackStatus": "1", "IsAccurate": True},
    ])
    clean = clean_laps_dataframe(raw, "Silverstone", 2023)
    assert len(clean) == 2
    assert "lap_time_delta" in clean.columns
    assert (clean["lap_time_delta"] >= 0.0).all()


def test_clean_telemetry_aggregations():
    tel = pd.DataFrame({
        "Speed": [250, 310, 180, 80],
        "Throttle": [100, 100, 40, 0],
        "Brake": [0, 0, 0, 1],
        "RPM": [11500, 12000, 9000, 4000],
        "nGear": [7, 8, 4, 2],
        "DRS": [12, 12, 0, 0],
    })
    clean_tel = clean_telemetry_dataframe(tel)
    assert "speed_kmh" in clean_tel.columns
    summary = aggregate_lap_telemetry(clean_tel)
    assert summary["max_speed_kmh"] == 310.0
    assert summary["full_throttle_pct"] == 50.0
    assert summary["braking_time_pct"] == 25.0


def test_feature_engineering_layers():
    df = pd.DataFrame([
        {"Driver": "VER", "circuit": "Silverstone", "season": 2023, "compound": "SOFT", "tyre_age": 12, "stint": 1, "lap_time_delta": 0.45, "track_temp_c": 35.0, "air_temp_c": 24.0, "humidity_pct": 45.0, "rain_intensity": 0.0, "gap_ahead_s": 0.8, "gap_behind_s": 2.1, "LapNumber": 12},
        {"Driver": "NOR", "circuit": "Silverstone", "season": 2023, "compound": "MEDIUM", "tyre_age": 20, "stint": 1, "lap_time_delta": 0.85, "track_temp_c": 35.0, "air_temp_c": 24.0, "humidity_pct": 45.0, "rain_intensity": 0.0, "gap_ahead_s": 2.5, "gap_behind_s": 4.0, "LapNumber": 20},
    ])
    f_df = compute_tyre_features(df)
    f_df = compute_weather_features(f_df)
    f_df = compute_opponent_features(f_df)
    f_df = compute_driver_features(f_df)
    f_df = compute_vehicle_features(f_df)
    f_df = compute_strategy_features(f_df)

    assert "is_soft" in f_df.columns
    assert "track_wetness_index" in f_df.columns
    assert "in_drs_window" in f_df.columns
    assert f_df.loc[0, "in_drs_window"] == 1.0  # gap 0.8 <= 1.0
    assert "driver_pace_bias" in f_df.columns
    assert "fuel_remaining_kg" in f_df.columns
    assert "is_optimal_pit_window" in f_df.columns


def test_leak_free_dataset_splits():
    df = pd.DataFrame({
        "circuit": ["Silverstone"] * 50 + ["Monza"] * 50 + ["Spa"] * 50,
        "season": [2023] * 150,
        "stint": [1] * 150,
        "compound": ["MEDIUM"] * 150,
        "tyre_age": list(range(1, 51)) * 3,
        "lap_time_delta": [0.5] * 150,
    })
    splits = DatasetVersionRegistry.create_leak_free_splits(df)
    train_sessions = set(splits["train"]["session_key"].unique())
    val_sessions = set(splits["val"]["session_key"].unique())
    test_sessions = set(splits["test"]["session_key"].unique())

    # Strictly disjoint sets of sessions
    assert len(train_sessions.intersection(test_sessions)) == 0
    assert len(train_sessions.intersection(val_sessions)) == 0
    assert len(val_sessions.intersection(test_sessions)) == 0


def test_dataset_validator():
    valid_df = pd.DataFrame({
        "compound": ["SOFT", "MEDIUM"],
        "tyre_age": [5, 10],
        "lap_time_delta": [0.2, 0.4],
    })
    res = DatasetValidator.validate_features_dataframe(valid_df)
    assert res["is_valid"] is True

    # Negative delta invalid
    invalid_df = pd.DataFrame({
        "compound": ["SOFT"],
        "tyre_age": [5],
        "lap_time_delta": [-1.0],
    })
    with pytest.raises(DatasetValidationError):
        DatasetValidator.validate_features_dataframe(invalid_df)


def test_end_to_end_dataset_builder(tmp_path):
    storage = RawStorageManager(storage_dir=str(tmp_path / "raw"))
    registry = DatasetVersionRegistry(registry_dir=str(tmp_path / "registry"))
    builder = DatasetBuilder(
        raw_storage=storage,
        version_registry=registry,
    )
    builder.loader.offline_only = True
    builder.loader.fastf1.offline_only = True

    result = builder.build_dataset(
        sessions=[(2023, "Silverstone"), (2023, "Monza")],
        dataset_version="test_v1",
    )
    assert result["dataset_version"] == "test_v1"
    assert "splits" in result
    assert not result["full_dataset"].empty
    assert len(result["splits"]["train"]) > 0
