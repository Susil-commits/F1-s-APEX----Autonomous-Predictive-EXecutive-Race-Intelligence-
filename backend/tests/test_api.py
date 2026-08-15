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
