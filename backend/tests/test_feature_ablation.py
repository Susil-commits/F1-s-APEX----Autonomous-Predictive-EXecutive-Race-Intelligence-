"""Unit and integration tests for APEX Feature Ablation Study Harness."""
import numpy as np
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.eval.feature_ablation_runner import (
    FEATURE_GROUPS,
    build_full_feature_dataframe,
    extract_feature_matrix,
    run_feature_ablation_study,
    train_and_score,
)
from backend.training.fetch_fastf1_data import generate_synthetic_fallback_data


def test_feature_dataframe_enrichment():
    """Verifies that build_full_feature_dataframe attaches all required multi-domain feature columns."""
    df = generate_synthetic_fallback_data()
    enriched = build_full_feature_dataframe(df)

    assert not enriched.empty
    assert "compound_rate" in enriched.columns
    assert "track_wetness_index" in enriched.columns
    assert "driver_causal_base_pace" in enriched.columns
    assert "fuel_remaining_kg" in enriched.columns
    assert "in_drs_window" in enriched.columns


def test_feature_group_extraction_and_training():
    """Verifies that extract_feature_matrix and train_and_score execute accurately on subset features."""
    df = generate_synthetic_fallback_data()
    enriched = build_full_feature_dataframe(df)

    # 1. Full Features
    tire_cols = FEATURE_GROUPS["tire"]
    X, y = extract_feature_matrix(enriched, tire_cols)
    assert X.shape[1] == len(tire_cols)
    assert len(X) == len(enriched)

    # Train / Test split
    split_idx = int(0.70 * len(X))
    metrics = train_and_score(X[:split_idx], y[:split_idx], X[split_idx:], y[split_idx:])

    assert "r2" in metrics
    assert "mae" in metrics
    assert "rmse" in metrics
    assert metrics["mae"] > 0.0


def test_ablation_study_end_to_end():
    """Executes the full feature ablation study and verifies consistency across all 9 configurations."""
    df = generate_synthetic_fallback_data()
    report = run_feature_ablation_study(save_plots=False)

    assert report["status"] == "PASS"
    results = report["ablation_results"]
    assert len(results) >= 8

    # Find full model and mean baseline
    full_m = next((r for r in results if r["config_id"] == "full_model"), None)
    base_m = next((r for r in results if r["config_id"] == "baseline_mean"), None)
    no_drv_m = next((r for r in results if r["config_id"] == "remove_driver"), None)

    assert full_m is not None
    assert base_m is not None
    assert no_drv_m is not None

    # Full model R2 must be higher than mean baseline
    assert full_m["metrics"]["r2"] > base_m["metrics"]["r2"]
    # Full model MAE must be lower than mean baseline
    assert full_m["metrics"]["mae"] < base_m["metrics"]["mae"]
    # Full model must outperform driver-less model
    assert full_m["metrics"]["r2"] > no_drv_m["metrics"]["r2"]

    # Verify ranking structure
    rankings = report["feature_importance_rankings"]
    assert len(rankings) >= 4
    assert all("relative_importance_pct" in rk for rk in rankings)


@pytest.mark.asyncio
async def test_ablation_study_api_endpoint():
    """Tests the GET /api/evaluation/ablation-study route."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/evaluation/ablation-study")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PASS"
        assert "ablation_results" in data
        assert "feature_importance_rankings" in data
        assert "summary_table" in data
        assert len(data["summary_table"]) >= 7
