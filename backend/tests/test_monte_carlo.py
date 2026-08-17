"""Unit tests for backend Monte Carlo stochastic simulation engine."""
from backend.app.simulator.engine import RaceSimulator
from backend.app.strategy.monte_carlo import MonteCarloEngine


def test_monte_carlo_simulation_runs():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.get_state()
    
    result = MonteCarloEngine.run_simulation(state=state, num_rollouts=400)
    assert "total_rollouts" in result
    assert result["total_rollouts"] == 400
    assert "recommended_strategy" in result
    assert "confidence_pct" in result
    assert "strategies" in result
    assert len(result["strategies"]) == 4


def test_monte_carlo_probability_validity():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.get_state()
    
    result = MonteCarloEngine.run_simulation(state=state, num_rollouts=400)
    for strat in result["strategies"]:
        assert 0.0 <= strat["win_probability_pct"] <= 100.0
        assert 0.0 <= strat["podium_probability_pct"] <= 100.0
        assert 0.0 <= strat["points_probability_pct"] <= 100.0
        assert strat["best_case_pos"] <= strat["worst_case_pos"]
        assert strat["variance_s"] >= 0.0
