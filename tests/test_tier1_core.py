"""Top-level test suite for APEX Tier 1 Core Baseline."""
import pytest
from httpx import ASGITransport, AsyncClient

from core.api.main import app as core_app
from core.features.feature_builder import PRE_RACE_FEATURE_NAMES, PreRaceFeatureBuilder
from core.training.evaluate import evaluate_model_temporal
from core.training.train import train_finishing_position_model


def test_core_features_dimension_and_bounds():
    vec, feat_dict = PreRaceFeatureBuilder.extract_features(
        grid_position=1,
        quali_delta_s=0.0,
        rolling_avg_finish=2.0,
        circuit_starts=10,
        constructor_pts_share=0.3,
        circuit_id="silverstone",
        rain_prob=0.0,
    )
    assert len(vec) == 9
    assert all(0.0 <= x <= 1.0 for x in vec)


def test_core_baseline_training_pipeline():
    artifact = train_finishing_position_model(random_seed=42)
    assert artifact["version"] == "core-v1.0.0"
    rep = evaluate_model_temporal(artifact, n_test_samples=50)
    assert rep["status"] in ("PASS", "WARN")


@pytest.mark.asyncio
async def test_core_predict_rest_api():
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/core/predict",
            json={"race_id": "monza", "driver_id": "NOR", "grid_position": 2},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["driver_id"] == "NOR"
        assert 1 <= data["predicted_position"] <= 20
        assert data["model_version"] == "core-v1.0.0"
