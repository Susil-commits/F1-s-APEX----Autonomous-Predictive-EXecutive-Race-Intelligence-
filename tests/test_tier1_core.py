"""Top-level test suite for APEX Tier 1 Core Baseline.

Covers:
- Pre-race feature extraction and boundary constraints
- Model training, benchmark, and temporal holdout evaluation
- API endpoints: root, health, drivers, races
- Prediction happy path and conformal interval invariants
- Edge case rejection: invalid driver_id (400), out-of-range grid (422)
- Input robustness: rain_probability auto-clamping, unknown race_id fallback
- High-concurrency thread safety without cache corruption
- Explainability / feature attribution structure
"""
import asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from core.api.main import app as core_app
from core.features.feature_builder import PRE_RACE_FEATURE_NAMES, PreRaceFeatureBuilder
from core.training.evaluate import evaluate_model_temporal
from core.training.train import train_finishing_position_model


def test_core_features_dimension_and_bounds():
    """Validates 9-dimensional vector construction and strict [0.0, 1.0] normalization."""
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
    assert len(feat_dict) == 9
    assert all(0.0 <= x <= 1.0 for x in vec)
    assert feat_dict["grid_position_norm"] == 0.0
    assert feat_dict["quali_delta_to_pole_s"] == 0.0


def test_core_baseline_training_pipeline():
    """Verifies that model training produces valid conformal bands and PASS/WARN status."""
    artifact = train_finishing_position_model(random_seed=42)
    assert artifact["version"] == "core-v1.0.0"
    assert "model" in artifact
    assert "q_hat_margin" in artifact
    rep = evaluate_model_temporal(artifact, n_test_samples=50)
    assert rep["status"] in ("PASS", "WARN")
    assert "metrics" in rep
    assert 0.0 <= rep["metrics"]["empirical_coverage"] <= 1.0


@pytest.mark.asyncio
async def test_core_predict_rest_api_happy_path():
    """Tests standard successful prediction payload returning finishing position and metadata."""
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
        assert data["team_name"] == "McLaren"
        assert 0.0 <= data["win_probability_pct"] <= 100.0
        assert 0.0 <= data["podium_probability_pct"] <= 100.0


@pytest.mark.asyncio
async def test_predict_invalid_driver_id_rejected_400():
    """Verifies that empty, numeric, or invalid-length driver IDs return HTTP 400 with a clear message."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for bad_id in ["", "123", "INVALID", "NO", "NORRIS"]:
            res = await client.post(
                "/api/core/predict",
                json={"race_id": "silverstone", "driver_id": bad_id, "grid_position": 1},
            )
            assert res.status_code == 400, f"Expected 400 for driver_id='{bad_id}', got {res.status_code}"
            assert "Invalid driver_id" in res.json().get("detail", "")


@pytest.mark.asyncio
async def test_predict_grid_position_out_of_range_rejected():
    """Verifies that grid position < 1 or > 20 is rejected as unprocessable entity (HTTP 422)."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for bad_grid in [0, 21, -5, 100]:
            res = await client.post(
                "/api/core/predict",
                json={"race_id": "silverstone", "driver_id": "VER", "grid_position": bad_grid},
            )
            assert res.status_code == 422, f"Expected 422 for grid_position={bad_grid}, got {res.status_code}"


@pytest.mark.asyncio
async def test_predict_rain_probability_clamped_bounds():
    """Verifies that rain probability values outside [0.0, 1.0] are safely clamped without crashing."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Rain > 1.0 should be clamped to 1.0
        res_high = await client.post(
            "/api/core/predict",
            json={"race_id": "spa", "driver_id": "HAM", "rain_probability": 1.75},
        )
        assert res_high.status_code == 200
        data_high = res_high.json()
        rain_contrib_high = next((c for c in data_high["feature_contributions"] if c["feature"] == "race_rain_prob"), None)
        if rain_contrib_high:
            assert rain_contrib_high["value"] == 1.0

        # Rain < 0.0 should be clamped to 0.0
        res_low = await client.post(
            "/api/core/predict",
            json={"race_id": "spa", "driver_id": "HAM", "rain_probability": -0.5},
        )
        assert res_low.status_code == 200
        data_low = res_low.json()
        rain_contrib_low = next((c for c in data_low["feature_contributions"] if c["feature"] == "race_rain_prob"), None)
        if rain_contrib_low:
            assert rain_contrib_low["value"] == 0.0


@pytest.mark.asyncio
async def test_predict_unknown_race_id_graceful_fallback():
    """Verifies that an unknown circuit ID falls back to neutral circuit priors without failing."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/core/predict",
            json={"race_id": "nonexistent_gp_venue", "driver_id": "LEC", "grid_position": 4},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["race_id"] == "nonexistent_gp_venue"
        assert 1 <= data["predicted_position"] <= 20


@pytest.mark.asyncio
async def test_predict_concurrent_requests_no_race_condition():
    """Verifies that concurrent requests execute safely without model cache corruption or race conditions."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payloads = [
            {"race_id": "silverstone", "driver_id": "VER", "grid_position": 1},
            {"race_id": "monza", "driver_id": "NOR", "grid_position": 2},
            {"race_id": "spa", "driver_id": "LEC", "grid_position": 3},
            {"race_id": "monaco", "driver_id": "HAM", "grid_position": 4},
            {"race_id": "bahrain", "driver_id": "PIA", "grid_position": 5},
        ] * 4  # 20 concurrent requests

        tasks = [client.post("/api/core/predict", json=p) for p in payloads]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)
        assert all(1 <= r.json()["predicted_position"] <= 20 for r in responses)
        assert all(r.json()["model_version"] == "core-v1.0.0" for r in responses)


@pytest.mark.asyncio
async def test_api_health_and_root_endpoints():
    """Tests GET / and GET /api/health for expected status and response keys."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        root_res = await client.get("/")
        assert root_res.status_code == 200
        assert root_res.json()["status"] == "ready"

        health_res = await client.get("/api/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_driver_and_race_roster_endpoints():
    """Tests GET /api/core/drivers and GET /api/core/races for catalog completeness."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        driver_res = await client.get("/api/core/drivers")
        assert driver_res.status_code == 200
        drivers = driver_res.json()["drivers"]
        assert len(drivers) >= 20
        assert any(d["code"] == "VER" for d in drivers)
        assert any(d["code"] == "NOR" for d in drivers)

        race_res = await client.get("/api/core/races")
        assert race_res.status_code == 200
        races = race_res.json()["races"]
        assert len(races) > 0


@pytest.mark.asyncio
async def test_conformal_interval_invariants():
    """Tests mathematical invariants of the 90% split-conformal confidence interval."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for driver in ["VER", "NOR", "LEC", "SAR"]:
            res = await client.post(
                "/api/core/predict",
                json={"race_id": "silverstone", "driver_id": driver},
            )
            assert res.status_code == 200
            data = res.json()
            ci = data["confidence_interval"]
            pred = data["predicted_position"]
            assert len(ci) == 2
            lower, upper = ci[0], ci[1]
            assert 1 <= lower <= 20
            assert 1 <= upper <= 20
            assert lower <= upper
            # Predicted finish must fall within or on the boundary of the conformal interval
            assert lower <= pred <= upper


@pytest.mark.asyncio
async def test_feature_attribution_structure_and_ordering():
    """Tests that feature attributions are structured, sorted descending by importance, and normalized."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/core/predict",
            json={"race_id": "monza", "driver_id": "VER", "grid_position": 1},
        )
        assert res.status_code == 200
        data = res.json()
        contributions = data["feature_contributions"]
        assert len(contributions) > 0
        for item in contributions:
            assert "feature" in item
            assert "label" in item
            assert "value" in item
            assert "importance_pct" in item
            assert item["direction"] in ("improves_finish", "hurts_finish", "neutral")

        # Must be ordered descending by importance percentage
        importances = [c["importance_pct"] for c in contributions]
        assert importances == sorted(importances, reverse=True)
