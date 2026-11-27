"""Unit tests for Monte Carlo Pit Stop Strategy Simulator & Grid Predictor."""
import pytest
from core.simulation.monte_carlo import MonteCarloRaceSimulator


def test_monte_carlo_simulation_execution():
    sim = MonteCarloRaceSimulator(random_seed=42)
    results = sim.simulate_strategy_comparison(
        circuit_id="silverstone",
        current_lap=18,
        current_pos=3,
        current_compound="C3",
        current_tyre_age=12,
        n_simulations=5000,
    )

    assert results["circuit"] == "silverstone"
    assert results["current_lap"] == 18
    assert results["simulations_count"] == 5000
    assert len(results["strategies"]) == 3
    assert results["optimal_strategy"] in [s["strategy_name"] for s in results["strategies"]]
    assert results["total_runtime_ms"] < 2000.0  # Must be fast under vectorized NumPy


def test_monte_carlo_safety_car_advantage():
    sim = MonteCarloRaceSimulator(random_seed=123)
    results = sim.simulate_strategy_comparison(
        circuit_id="monaco",  # Monaco has high SC rate (~75%)
        current_lap=25,
        current_pos=4,
        n_simulations=3000,
    )
    for s in results["strategies"]:
        assert 0.0 <= s["sc_benefit_probability_pct"] <= 100.0
        assert s["confidence_interval_90"][0] <= s["confidence_interval_90"][1]


@pytest.mark.asyncio
async def test_grid_prediction_endpoint():
    from httpx import ASGITransport, AsyncClient
    from core.api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/core/predict/grid",
            json={
                "race_id": "silverstone",
                "rain_probability": 0.10,
                "weather_transition": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_drivers"] >= 20
        assert len(data["grid_results"]) >= 20
        # Check strict monotonicity of predicted finishing order
        positions = [d["predicted_position"] for d in data["grid_results"]]
        assert positions == list(range(1, len(positions) + 1))


@pytest.mark.asyncio
async def test_pit_stop_simulation_endpoint():
    from httpx import ASGITransport, AsyncClient
    from core.api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/core/simulate/pit-stop",
            json={
                "race_id": "monza",
                "current_lap": 20,
                "current_position": 2,
                "current_compound": "C3",
                "current_tyre_age": 10,
                "simulations_count": 2000,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["optimal_strategy"]
        assert "strategies" in data


def test_circuit_registry_parity_across_all_profiles():
    """Verifies Monte Carlo laps and SC hazard rates cover every circuit in CIRCUIT_PROFILES."""
    from core.features.feature_builder import CIRCUIT_PROFILES
    from core.simulation.monte_carlo import CIRCUIT_SC_HAZARD_RATES, CIRCUIT_TOTAL_LAPS

    for cid in CIRCUIT_PROFILES:
        assert cid in CIRCUIT_TOTAL_LAPS
        assert cid in CIRCUIT_SC_HAZARD_RATES
        assert 40 <= CIRCUIT_TOTAL_LAPS[cid] <= 80
        assert 0.1 <= CIRCUIT_SC_HAZARD_RATES[cid] <= 1.0
