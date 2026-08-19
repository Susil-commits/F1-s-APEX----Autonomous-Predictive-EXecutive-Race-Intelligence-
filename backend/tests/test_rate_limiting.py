"""Tests for SlowAPI rate limiting on heavy compute endpoints."""
from starlette.testclient import TestClient

from backend.app.main import app


def test_monte_carlo_rate_limiting_enforcement():
    """Verifies that rapid requests to /strategy/monte-carlo trigger HTTP 429 once the limit is exceeded."""
    client = TestClient(app)

    # Initialize a race first
    client.post("/api/race/init", json={"track_name": "silverstone", "seed": 42})

    # The rate limit on /api/strategy/monte-carlo is 15/minute
    # Firing 20 rapid requests should trigger a 429 Too Many Requests
    status_codes = []
    for _ in range(20):
        resp = client.post("/api/strategy/monte-carlo", json={"rollouts": 5})
        status_codes.append(resp.status_code)

    assert 200 in status_codes
    assert 429 in status_codes


def test_health_check_exempt_from_tight_limits():
    """Verifies that the /api/health probe remains fast and accessible under continuous polling."""
    client = TestClient(app)
    responses = [client.get("/api/health") for _ in range(10)]
    for r in responses:
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
