"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_api_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_api_tracks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/tracks")
    assert response.status_code == 200
    tracks = response.json()["tracks"]
    assert len(tracks) >= 4
    track_ids = [t["id"] for t in tracks]
    assert "silverstone" in track_ids
    assert "monza" in track_ids


@pytest.mark.asyncio
async def test_api_race_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Init race
        init_res = await ac.post("/api/race/init", json={"track_name": "silverstone", "seed": 99})
        assert init_res.status_code == 200
        assert init_res.json()["status"] == "initialized"

        # Step race
        step_res = await ac.post("/api/race/step")
        assert step_res.status_code == 200
        state = step_res.json()["state"]
        assert state["current_lap"] >= 1
        assert len(state["cars"]) > 0
        assert state["active_decision"] is not None


@pytest.mark.asyncio
async def test_api_shap_comparison():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/race/init", json={"track_name": "silverstone", "seed": 42})
        response = await ac.get("/api/strategy/shap-compare?action_a=PUSH&action_b=CONSERVE")
    assert response.status_code == 200
    data = response.json()
    assert data["action_a"] == "PUSH"
    assert data["action_b"] == "CONSERVE"
    assert "delta_q" in data
    assert "top_differential_features" in data
    assert "action_rankings" in data
    assert len(data["action_rankings"]) == 8


@pytest.mark.asyncio
async def test_api_scenario_injection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/race/init", json={"track_name": "silverstone", "seed": 42})

        # Test rain injection
        rain_res = await ac.post("/api/simulator/inject-scenario", json={"scenario_type": "TORRENTIAL_RAIN", "intensity": 0.85})
        assert rain_res.status_code == 200
        assert rain_res.json()["condition"] == "WET"

        # Test safety car injection
        sc_res = await ac.post("/api/simulator/inject-scenario", json={"scenario_type": "SAFETY_CAR", "laps": 3})
        assert sc_res.status_code == 200
        assert sc_res.json()["safety_car"] == "SAFETY_CAR"

        # Test puncture injection
        punc_res = await ac.post("/api/simulator/inject-scenario", json={"scenario_type": "PUNCTURE", "wear_delta": 40.0})
        assert punc_res.status_code == 200


@pytest.mark.asyncio
async def test_api_fork_counterfactual():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/race/init", json={"track_name": "silverstone", "seed": 42})
        response = await ac.post("/api/strategy/fork-counterfactual", json={"proposed_action": "PIT_SOFT", "rollout_laps": 4})
    assert response.status_code == 200
    data = response.json()
    assert "proposed_action" in data
    assert "alternate_timeline" in data
    assert "baseline_timeline" in data
    assert len(data["alternate_timeline"]) == 4


@pytest.mark.asyncio
async def test_api_latest_benchmarks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/benchmarks/latest")
    assert response.status_code == 200
    data = response.json()
    assert "overall_summary" in data
    assert "circuit_breakdown" in data
    assert "dqn" in data["overall_summary"]


@pytest.mark.asyncio
async def test_api_race_ask():
    # Initialize race first so decisions exist
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        init_res = await ac.post("/api/race/init", json={"track_name": "silverstone", "seed": 42})
        assert init_res.status_code == 200

        # Query RAG
        ask_res = await ac.post("/api/race/ask", json={"question": "Why did we maintain position on lap 1?"})
        assert ask_res.status_code == 200
        ask_data = ask_res.json()
        assert "answer" in ask_data
        assert "sources" in ask_data
        assert len(ask_data["sources"]) > 0


@pytest.mark.asyncio
async def test_api_tyre_model_meta():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/intelligence/tyre-model")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_api_race_export():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Initialize session
        init_res = await ac.post("/api/race/init", json={"track_name": "silverstone", "seed": 42})
        assert init_res.status_code == 200
        race_id = init_res.json()["state"]["race_id"]

        # Export debrief
        export_res = await ac.get(f"/api/race/export/{race_id}")
        assert export_res.status_code == 200
        export_data = export_res.json()
        assert "markdown_report" in export_data
        assert "decisions" in export_data
        assert "APEX Race Intelligence Debrief Report" in export_data["markdown_report"]


@pytest.mark.asyncio
async def test_api_context_and_prediction_provenance_endpoints():
    """Verify REST API context endpoints including prediction provenance, graph, models, and quality."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Prediction Provenance
        pred_res = await ac.get("/api/context/prediction/pred_1042")
        assert pred_res.status_code == 200
        pred_data = pred_res.json()
        assert pred_data["prediction_id"] == "pred_1042"
        assert pred_data["model"] == "tyre_degradation_xgb"
        assert pred_data["model_version"] == "v1.4"
        assert pred_data["dataset_version"] == "fastf1_v2"
        assert pred_data["feature_schema"] == "race_features_v3"
        assert pred_data["session_id"] == "2026_hungary_race"
        assert pred_data["confidence_interval"]["lower"] == 0.31
        assert pred_data["confidence_interval"]["upper"] == 0.61

        # 2. Context Models
        models_res = await ac.get("/api/context/models")
        assert models_res.status_code == 200
        assert len(models_res.json()) >= 5

        # 3. Context Datasets
        datasets_res = await ac.get("/api/context/datasets")
        assert datasets_res.status_code == 200
        assert len(datasets_res.json()) >= 3

        # 4. Context Quality
        quality_res = await ac.get("/api/context/quality")
        assert quality_res.status_code == 200
        assert "metadata_completeness" in quality_res.json()

        # 5. Agent Evaluation Report
        eval_res = await ac.get("/api/agents/eval-report")
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert eval_data["overall_pass_rate_pct"] == 100.0
        assert len(eval_data["architecture_comparison"]) >= 2

