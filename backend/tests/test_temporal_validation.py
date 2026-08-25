"""Unit and integration tests for APEX Temporal Validation Architecture & Anti-Leakage Suite."""
import numpy as np
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.eval.temporal_validation import (
    prepare_features_and_target,
    run_temporal_validation,
)
from backend.training.datasets.data_quality import (
    DataQualityChecker,
    IssueSeverity,
)
from backend.training.datasets.dataset_version import DatasetVersionRegistry
from backend.training.datasets.temporal_splitter import (
    TemporalSplitConfig,
    TemporalSplitter,
)
from backend.training.fetch_fastf1_data import (
    clean_session_laps,
    generate_synthetic_fallback_data,
)


def test_fixed_horizon_split_boundaries():
    """Verifies that 2018-2022 (train), 2023 (val), and 2024 (test) are strictly partitioned."""
    df = generate_synthetic_fallback_data()
    splits = TemporalSplitter.fixed_horizon_split(df)

    train_df = splits["train"]
    val_df = splits["val"]
    test_df = splits["test"]

    assert not train_df.empty
    assert not val_df.empty
    assert not test_df.empty

    # Strict season boundary checks
    assert train_df["season"].max() <= 2022
    assert (val_df["season"] == 2023).all()
    assert (test_df["season"] == 2024).all()

    # Zero overlap of session keys
    train_sessions = set(train_df["session_key"].unique())
    val_sessions = set(val_df["session_key"].unique())
    test_sessions = set(test_df["session_key"].unique())

    assert len(train_sessions.intersection(val_sessions)) == 0
    assert len(train_sessions.intersection(test_sessions)) == 0
    assert len(val_sessions.intersection(test_sessions)) == 0


def test_temporal_integrity_verification_pass_and_fail():
    """Verifies that TemporalSplitter detects chronological inversions and overlapping sessions."""
    df = generate_synthetic_fallback_data()
    splits = TemporalSplitter.fixed_horizon_split(df)

    # Valid partitions -> PASS
    report = TemporalSplitter.verify_temporal_integrity(splits["train"], splits["val"], splits["test"])
    assert report.is_valid is True
    assert report.chronological_inversions == 0
    assert len(report.overlapping_sessions) == 0

    # Inverted partitions (train season > val season) -> FAIL
    inverted_report = TemporalSplitter.verify_temporal_integrity(splits["val"], splits["train"], splits["test"])
    assert inverted_report.is_valid is False
    assert inverted_report.chronological_inversions > 0

    # Overlapping session -> FAIL
    polluted_val = pd.concat([splits["val"], splits["train"].iloc[:5]], ignore_index=True)
    overlap_report = TemporalSplitter.verify_temporal_integrity(splits["train"], polluted_val, splits["test"])
    assert overlap_report.is_valid is False
    assert len(overlap_report.overlapping_sessions) > 0


def test_walk_forward_cv_expanding_windows():
    """Verifies progressive expanding-window cross-validation fold generation."""
    df = generate_synthetic_fallback_data()
    folds = TemporalSplitter.walk_forward_cv(df)

    assert len(folds) >= 3

    prev_train_size = 0
    for fold_info, tr_df, v_df in folds:
        # Monotonically expanding training sizes
        assert len(tr_df) > prev_train_size
        prev_train_size = len(tr_df)

        # Validation season strictly follows max training season
        assert fold_info.val_seasons[0] > max(fold_info.train_seasons)

        # No session cross-contamination in fold
        tr_sess = set(tr_df["session_key"].unique())
        v_sess = set(v_df["session_key"].unique())
        assert len(tr_sess.intersection(v_sess)) == 0


def test_causal_feature_calculation_no_lookahead():
    """Verifies that driver_fastest_lap_s is strictly causal and does not leak future laps."""
    # Construct a session where driver starts slow, then sets a record lap at the very end
    raw_laps = pd.DataFrame([
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 1, "LapTime": pd.Timedelta(seconds=95.0), "Stint": 1, "TrackStatus": "1", "IsAccurate": True},
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 2, "LapTime": pd.Timedelta(seconds=94.0), "Stint": 1, "TrackStatus": "1", "IsAccurate": True},
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 3, "LapTime": pd.Timedelta(seconds=93.0), "Stint": 1, "TrackStatus": "1", "IsAccurate": True},
        {"Driver": "VER", "Compound": "SOFT", "TyreLife": 4, "LapTime": pd.Timedelta(seconds=85.0), "Stint": 1, "TrackStatus": "1", "IsAccurate": True},  # Future fast lap
    ])

    clean = clean_session_laps(raw_laps, circuit_name="Silverstone", year=2023)
    assert len(clean) == 4

    # At lap 1, baseline should NOT know about 85.0s (should be 95.0)
    assert clean.iloc[0]["driver_fastest_lap_s"] == 95.0
    # At lap 2, baseline should be 95.0
    assert clean.iloc[1]["driver_fastest_lap_s"] == 95.0
    # At lap 3, baseline should be 94.0
    assert clean.iloc[2]["driver_fastest_lap_s"] == 94.0
    # At lap 4, baseline should be 93.0
    assert clean.iloc[3]["driver_fastest_lap_s"] == 93.0


def test_data_quality_temporal_leakage_detection():
    """Verifies that DataQualityChecker catches prospective leakage columns."""
    df = generate_synthetic_fallback_data()
    report = DataQualityChecker.run(df, dataset_name="clean_multi_season", fail_on_severe=False)
    assert report.passed is True

    # Inject prospective future leakage column
    leaked_df = df.copy()
    leaked_df["future_weather_forecast"] = "RAIN"
    bad_report = DataQualityChecker.run(leaked_df, dataset_name="leaked_data", fail_on_severe=False)
    assert bad_report.passed is False
    assert any(i.check == "prospective_temporal_leakage" for i in bad_report.issues)


def test_temporal_validation_harness_end_to_end():
    """Runs the temporal validation suite and validates metrics."""
    df = generate_synthetic_fallback_data()
    report = run_temporal_validation(save_plots=False)

    assert report["status"] == "PASS"
    assert "validation_2023_metrics" in report["fixed_horizon_evaluation"]
    assert "test_2024_metrics" in report["fixed_horizon_evaluation"]
    assert report["fixed_horizon_evaluation"]["validation_2023_metrics"]["r2"] > 0.50
    assert report["fixed_horizon_evaluation"]["test_2024_metrics"]["r2"] > 0.60
    assert "model_comparison" in report
    assert len(report["model_comparison"]["models"]) == 4
    assert "prediction_calibration" in report
    assert report["prediction_calibration"]["target_coverage"] == 0.95
    assert report["temporal_integrity"]["is_valid"] is True
    assert report["temporal_integrity"]["chronological_inversions"] == 0


@pytest.mark.asyncio
async def test_temporal_validation_api_endpoint():
    """Tests the GET /api/evaluation/temporal-validation route."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/evaluation/temporal-validation")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PASS"
        assert "fixed_horizon_evaluation" in data
        assert "walk_forward_expanding_window_cv" in data
        assert "temporal_integrity" in data
        assert data["temporal_integrity"]["is_valid"] is True
