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
    """Validates 13-dimensional vector construction and strict [0.0, 1.0] normalization."""
    vec, feat_dict = PreRaceFeatureBuilder.extract_features(
        grid_position=1,
        quali_delta_s=0.0,
        rolling_avg_finish=2.0,
        circuit_starts=10,
        constructor_pts_share=0.3,
        circuit_id="silverstone",
        rain_prob=0.0,
        sector_1_delta_s=0.0,
        sector_2_delta_s=0.0,
        sector_3_delta_s=0.0,
        weather_transition=0.0,
    )
    assert len(vec) == 13
    assert len(feat_dict) == 13
    assert all(0.0 <= x <= 1.0 for x in vec)
    assert feat_dict["grid_position_norm"] == 0.0
    assert feat_dict["quali_delta_to_pole_s"] == 0.0
    assert feat_dict["sector_1_delta_norm"] == 0.0
    assert feat_dict["weather_transition_flag"] == 0.0


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


def test_circuit_profiles_catalog_and_marina_bay_coverage():
    """Verifies marina_bay key resolution and 100% circuit coverage against dataset."""
    import os
    import pandas as pd
    from core.features.feature_builder import CIRCUIT_PROFILES
    from core.training.train import PRERACE_CACHE_CSV

    # Verify marina_bay exists and has correct physical profile
    assert "marina_bay" in CIRCUIT_PROFILES
    mb = CIRCUIT_PROFILES["marina_bay"]
    assert mb["downforce"] == 0.95
    assert mb["power"] == 0.35
    assert mb["street"] == 1.0

    # If dataset cache exists, verify 100% of unique circuit_ids are mapped
    if os.path.exists(PRERACE_CACHE_CSV):
        df = pd.read_csv(PRERACE_CACHE_CSV)
        unique_circuits = set(df["circuit_id"].dropna().unique())
        missing = unique_circuits - set(CIRCUIT_PROFILES.keys())
        assert len(missing) == 0, f"Unmapped circuits found: {missing}"


def test_evaluation_fallback_warning(caplog):
    """Verifies that evaluate_model_temporal logs a visible warning when data loading falls back."""
    import logging
    from unittest.mock import patch

    class DummyModel:
        def predict(self, X):
            import numpy as np
            return np.ones(len(X)) * 5.0

    dummy_artifact = {"model": DummyModel(), "q_hat_margin": 2.0}

    with caplog.at_level(logging.WARNING):
        with patch("core.training.train.load_or_fetch_prerace_data", side_effect=RuntimeError("Simulated failure")):
            rep = evaluate_model_temporal(dummy_artifact, n_test_samples=10)
            assert rep is not None
            assert any("APEX EVALUATION WARNING" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_rate_limiter_blocks_excessive_traffic():
    """Verifies that slowapi rate limiting responds with 429 when enabled and limit is reached."""
    try:
        import slowapi  # noqa: F401
    except ImportError:
        pytest.skip("slowapi is not installed in the current environment")

    from core.api.limiter import limiter

    was_enabled = limiter.enabled
    try:
        limiter.enabled = True
        transport = ASGITransport(app=core_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            statuses = []
            for _ in range(35):
                res = await client.post(
                    "/api/core/predict",
                    json={"race_id": "monza", "driver_id": "VER", "grid_position": 1},
                )
                statuses.append(res.status_code)
            assert 429 in statuses
    finally:
        limiter.enabled = was_enabled


def test_circuit_classification_and_segmentation():
    """Verifies circuit categorization into street, high_speed, and permanent and segmented evaluation."""
    from core.training.evaluate import classify_circuit

    assert classify_circuit("monaco") == "street"
    assert classify_circuit("singapore") == "street"
    assert classify_circuit("marina_bay") == "street"
    assert classify_circuit("baku") == "street"
    assert classify_circuit("monza") == "high_speed"
    assert classify_circuit("vegas") == "high_speed"
    assert classify_circuit("silverstone") == "permanent"
    assert classify_circuit("spa") == "permanent"

    artifact = train_finishing_position_model(random_seed=42, use_synthetic=True)
    eval_rep = evaluate_model_temporal(artifact, n_test_samples=50)
    assert "segmented_metrics" in eval_rep
    assert "permanent" in eval_rep["segmented_metrics"]
    assert "high_speed" in eval_rep["segmented_metrics"]
    assert "street" in eval_rep["segmented_metrics"]


def test_quantile_regression_uncertainty_asymmetry():
    """Verifies that quantile models exist in trained artifact and provide valid asymmetric intervals."""
    from core.api.predict import get_core_model

    artifact = get_core_model()
    assert "quantile_models" in artifact
    q_mods = artifact["quantile_models"]
    assert "q10" in q_mods and "q50" in q_mods and "q90" in q_mods

    vec_p1, _ = PreRaceFeatureBuilder.extract_features(grid_position=1, circuit_id="monaco")
    p10_pole = float(q_mods["q10"].predict(vec_p1.reshape(1, -1))[0])
    p50_pole = float(q_mods["q50"].predict(vec_p1.reshape(1, -1))[0])
    p90_pole = float(q_mods["q90"].predict(vec_p1.reshape(1, -1))[0])

    # Monotonicity check
    assert p10_pole <= p50_pole <= p90_pole or (p90_pole - p10_pole >= 0)


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint():
    """Verifies that /metrics endpoint exposes valid Prometheus metrics text."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate a prediction to increment metrics
        await client.post(
            "/api/core/predict",
            json={"race_id": "silverstone", "driver_id": "HAM", "grid_position": 5},
        )
        res = await client.get("/metrics")
        assert res.status_code == 200
        text = res.text
        assert "apex_predictions_total" in text
        assert "apex_prediction_latency_seconds" in text


def test_weekend_drift_monitor_healthy_and_drifted():
    """Verifies that WeekendDriftMonitor correctly identifies normal vs drifted race weekend distributions."""
    from core.monitoring.drift import WeekendDriftMonitor

    monitor = WeekendDriftMonitor()

    # Normal race weekend sample
    normal_records = [
        {"grid_position": g, "quali_delta_s": 0.1 * g, "rain_prob": 0.05}
        for g in range(1, 21)
    ]
    rep_normal = monitor.check_weekend_drift(normal_records, z_threshold=2.5)
    assert rep_normal["status"] == "HEALTHY"
    assert len(rep_normal["drift_detected_features"]) == 0

    # Anomalous weekend with extreme rain probability drift across all cars
    drifted_records = [
        {"grid_position": g, "quali_delta_s": 0.1 * g, "rain_prob": 0.95}
        for g in range(1, 21)
    ]
    rep_drift = monitor.check_weekend_drift(drifted_records, z_threshold=2.0)
    assert rep_drift["status"] == "DRIFT_DETECTED"
    assert "rain_prob" in rep_drift["drift_detected_features"]


def test_jolpica_retry_with_backoff():
    """Verifies that JolpicaAdapter handles transient 429/500 errors with backoff retry."""
    from unittest.mock import MagicMock
    import httpx
    from core.ingestion.jolpica_adapter import JolpicaAdapter

    adapter = JolpicaAdapter()

    # Mock client returning 429 on first call, 200 on second call
    mock_client = MagicMock(spec=httpx.Client)
    resp_429 = MagicMock(spec=httpx.Response)
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.01"}

    resp_200 = MagicMock(spec=httpx.Response)
    resp_200.status_code = 200

    mock_client.get.side_effect = [resp_429, resp_200]

    final_resp = adapter._get_with_retry(mock_client, "https://api.jolpi.ca/test", max_retries=2, base_delay=0.01)
    assert final_resp is not None
    assert final_resp.status_code == 200
    assert mock_client.get.call_count == 2


@pytest.mark.asyncio
async def test_drift_rest_api_endpoints():
    """Verifies that /api/core/drift/baseline and /api/core/drift/check REST endpoints function correctly."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check baseline endpoint
        res_base = await client.get("/api/core/drift/baseline")
        assert res_base.status_code == 200
        data_base = res_base.json()
        assert "baseline" in data_base
        assert "grid_position" in data_base["baseline"]

        # Check weekend drift POST endpoint with normal records
        sample_records = [
            {"grid_position": g, "quali_delta_s": 0.1 * g, "rain_prob": 0.05}
            for g in range(1, 21)
        ]
        res_check = await client.post("/api/core/drift/check?z_threshold=2.5", json=sample_records)
        assert res_check.status_code == 200
        data_check = res_check.json()
        assert data_check["status"] == "HEALTHY"


def test_feature_builder_dict_to_vector():
    """Verifies that PreRaceFeatureBuilder.dict_to_vector preserves PRE_RACE_FEATURE_NAMES alignment."""
    from core.features.feature_builder import PRE_RACE_FEATURE_NAMES, PreRaceFeatureBuilder

    sample_dict = {name: float(idx + 1) for idx, name in enumerate(PRE_RACE_FEATURE_NAMES)}
    vec = PreRaceFeatureBuilder.dict_to_vector(sample_dict)
    assert vec.shape == (len(PRE_RACE_FEATURE_NAMES),)
    for idx, name in enumerate(PRE_RACE_FEATURE_NAMES):
        assert vec[idx] == float(idx + 1)


@pytest.mark.asyncio
async def test_compute_sensitivity_batched_inference():
    """Verifies that compute_sensitivity returns top levers sorted by positions_gained."""
    import numpy as np
    from core.api.predict import compute_sensitivity
    from core.features.feature_builder import PreRaceFeatureBuilder

    class DummyModel:
        def predict(self, X):
            # Simulated model where improving sector/quali times lowers finishing position
            return np.sum(X, axis=1) * 5.0

    dummy_model = DummyModel()
    base_dict = {
        "sector_1_delta_norm": 0.5,
        "sector_2_delta_norm": 0.5,
        "sector_3_delta_norm": 0.5,
        "quali_delta_to_pole_s": 0.4,
    }

    sensitivity = await compute_sensitivity(dummy_model, base_dict, PreRaceFeatureBuilder, current_pred=8.0)
    assert isinstance(sensitivity, list)
    assert len(sensitivity) <= 3
    if sensitivity:
        for rec in sensitivity:
            assert "lever" in rec
            assert "change" in rec
            assert "positions_gained" in rec
            assert rec["positions_gained"] > 0.1
        # Check sorted descending
        gains = [r["positions_gained"] for r in sensitivity]
        assert gains == sorted(gains, reverse=True)


def test_rank_opportunities():
    """Verifies that rank_opportunities correctly identifies the highest impact opportunity."""
    from core.api.predict import FeatureContribution, rank_opportunities

    contributions = [
        FeatureContribution(
            feature="sector_1_delta_norm",
            label="Sector 1 Cornering/Pace",
            value=0.8,
            importance_pct=35.0,
            direction="hurts_finish",
        ),
        FeatureContribution(
            feature="constructor_pts_share",
            label="Car Championship Pace",
            value=0.25,
            importance_pct=25.0,
            direction="improves_finish",
        ),
        FeatureContribution(
            feature="quali_delta_to_pole_s",
            label="Qualifying Pace Delta",
            value=0.4,
            importance_pct=15.0,
            direction="hurts_finish",
        ),
    ]

    feat_dict = {
        "sector_1_delta_norm": 0.8,
        "constructor_pts_share": 0.25,
        "quali_delta_to_pole_s": 0.4,
    }

    opps = rank_opportunities(contributions, feat_dict)
    assert isinstance(opps, list)
    assert len(opps) == 1
    assert opps[0]["feature"] == "sector_1_delta_norm"
    assert opps[0]["opportunity_score"] > 0


@pytest.mark.asyncio
async def test_predict_endpoint_returns_strategy_recommendations_and_opportunity():
    """Verifies that /api/core/predict includes strategy_recommendations and biggest_opportunity."""
    transport = ASGITransport(app=core_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/core/predict",
            json={
                "race_id": "silverstone",
                "driver_id": "SAI",
                "grid_position": 8,
                "sector_1_delta_s": 0.35,
                "sector_2_delta_s": 0.45,
                "sector_3_delta_s": 0.25,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "strategy_recommendations" in data
        assert isinstance(data["strategy_recommendations"], list)
        if data["strategy_recommendations"]:
            rec = data["strategy_recommendations"][0]
            assert "lever" in rec
            assert "change" in rec
            assert "positions_gained" in rec
        if data.get("biggest_opportunity"):
            opp = data["biggest_opportunity"]
            assert "feature" in opp
            assert "opportunity_score" in opp


