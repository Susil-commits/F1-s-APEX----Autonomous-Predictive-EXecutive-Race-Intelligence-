"""Unit tests for Tier 1 Core Predictive Baseline."""
import pytest
from httpx import ASGITransport, AsyncClient

from core.api.main import app as core_app
from core.features.feature_builder import PRE_RACE_FEATURE_NAMES, PreRaceFeatureBuilder
from core.training.evaluate import evaluate_model_temporal
from core.training.train import train_finishing_position_model


def test_core_feature_builder_invariants():
    """Verifies feature builder produces valid normalized vectors with zero leakage."""
    vec, feat_dict = PreRaceFeatureBuilder.extract_features(
        grid_position=3,
        quali_delta_s=0.25,
        rolling_avg_finish=4.0,
        circuit_starts=6,
        constructor_pts_share=0.22,
        circuit_id="silverstone",
        rain_prob=0.15,
    )
    assert len(vec) == len(PRE_RACE_FEATURE_NAMES) == 9
    assert not any(v is None for v in vec)
    # Normalized invariants between 0.0 and 1.0
    for v in vec:
        assert 0.0 <= v <= 1.0
    assert "grid_position_norm" in feat_dict


def test_core_model_training_and_conformal_eval():
    """Verifies baseline training and conformal uncertainty evaluation."""
    artifact = train_finishing_position_model(random_seed=42)
    assert "model" in artifact
    assert artifact["version"] == "core-v1.0.0"
    assert artifact["q_hat_margin"] > 0.0

    eval_rep = evaluate_model_temporal(artifact, n_test_samples=100)
    assert eval_rep["metrics"]["empirical_coverage"] >= 0.80
    assert eval_rep["metrics"]["r2"] > 0.0


@pytest.mark.asyncio
async def test_core_predict_api_contract():
    """Verifies standalone Tier 1 API contract: race_id + driver_id -> prediction."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test root status
        r_root = await client.get("/")
        assert r_root.status_code == 200
        assert r_root.json()["service"] == "APEX Core V1 Predictor"

        # Test predict endpoint
        payload = {
            "race_id": "silverstone",
            "driver_id": "VER",
            "grid_position": 1,
            "rain_probability": 0.0,
        }
        res = await client.post("/api/core/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["driver_id"] == "VER"
        assert 1 <= data["predicted_position"] <= 20
        assert len(data["confidence_interval"]) == 2
        assert data["confidence_interval"][0] <= data["confidence_interval"][1]
        assert data["model_version"] == "core-v1.0.0"
        assert "data_snapshot_utc" in data
        assert len(data["feature_contributions"]) > 0
