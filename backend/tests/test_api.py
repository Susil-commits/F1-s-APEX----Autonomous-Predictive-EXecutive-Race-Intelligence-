"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
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
