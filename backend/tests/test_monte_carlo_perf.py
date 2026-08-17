"""Performance and distribution verification tests for Vectorized Monte Carlo Engine."""
import time
import pytest
from backend.app.simulator.engine import RaceSimulator
from backend.app.strategy.monte_carlo import MonteCarloEngine


def test_monte_carlo_candidate_rollouts_and_distributions():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(15):
        sim.step()
    state = sim.get_state()

    result = MonteCarloEngine.evaluate_candidates(state, num_rollouts_per_action=100)
    assert "candidates" in result
    assert len(result["candidates"]) == 9
    assert result["best_action"] in [c["action"] for c in result["candidates"]]

    for cand in result["candidates"]:
        assert 0.0 <= cand["win_probability"] <= 1.0
        assert 0.0 <= cand["podium_probability"] <= 1.0
        assert 0.0 <= cand["dnf_probability"] <= 1.0
        assert 1.0 <= cand["expected_finish"] <= 10.0
        assert "position_distribution" in cand
        assert len(cand["position_distribution"]) > 0


@pytest.mark.parametrize("n_rollouts", [10, 100, 500, 1000])
def test_monte_carlo_latency_scaling(n_rollouts):
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(10):
        sim.step()
    state = sim.get_state()

    t0 = time.perf_counter()
    result = MonteCarloEngine.evaluate_candidates(state, num_rollouts_per_action=n_rollouts)
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000

    # 1000 rollouts per action across 9 actions (9,000 total rollouts) should execute in < 250ms on CPU
    assert latency_ms < 500.0, f"Expected <500ms for {n_rollouts} rollouts, got {latency_ms:.1f}ms"
    assert result["total_rollouts"] == n_rollouts * 9
