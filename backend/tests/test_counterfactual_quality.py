"""Unit and integration tests for Counterfactual Quality & Simulation Health Suite."""
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.strategy.counterfactual import CounterfactualChecker
from backend.app.strategy.counterfactual_quality import (
    CounterfactualQualityEvaluator,
    DecisionRegret,
    RolloutConsistency,
    SimulationLatency,
    StrategyStability,
    counterfactual_quality_engine,
)


def test_rollout_consistency_convergence():
    """Verifies that RolloutConsistency computes finish variance and JS convergence."""
    # 1k rollouts with high consistency (P1 and P2 finishes)
    positions = np.concatenate([np.ones(700), np.full(250, 2), np.full(50, 3)])
    consistency = CounterfactualQualityEvaluator.evaluate_rollout_consistency(positions)

    assert isinstance(consistency, RolloutConsistency)
    assert consistency.variance_finishing_position >= 0.0
    assert consistency.std_finishing_position >= 0.0
    assert consistency.rollout_completion_rate_pct >= 99.8
    assert consistency.jensen_shannon_divergence <= 0.035
    assert consistency.is_converged is True
    assert consistency.win_probability_sem_pct < 2.0


def test_strategy_stability_under_perturbations():
    """Verifies strategy stability scoring and action robustness margin."""
    candidates = [
        {"action": "PIT_NOW", "utility_mean": 0.85, "time_delta_s": -4.2, "expected_finish": 1.1},
        {"action": "PIT_PLUS_2", "utility_mean": 0.70, "time_delta_s": -1.0, "expected_finish": 1.6},
        {"action": "STAY_OUT", "utility_mean": 0.55, "time_delta_s": 5.0, "expected_finish": 2.5},
    ]

    stability = CounterfactualQualityEvaluator.evaluate_strategy_stability(
        recommended_action="PIT_NOW",
        alternative_actions=candidates,
    )

    assert isinstance(stability, StrategyStability)
    assert stability.action_flip_rate_pct < 10.0  # Decays with margin
    assert stability.stability_score_pct >= 90.0
    assert stability.noise_resilience_rating in ["HIGH", "MAXIMUM"]
    assert stability.action_robustness_margin_s >= 3.0


def test_simulation_latency_profiling():
    """Verifies sub-millisecond p50, p95, p99 profiling per 1,000 rollouts."""
    latency = CounterfactualQualityEvaluator.benchmark_simulation_latency(
        num_benchmarks=3,
        rollouts_per_benchmark=1000,
    )

    assert isinstance(latency, SimulationLatency)
    assert 0.1 <= latency.p50_latency_ms <= 50.0
    assert latency.p50_latency_ms <= latency.p95_latency_ms <= latency.p99_latency_ms
    assert latency.throughput_rollouts_per_sec > 10000
    assert latency.benchmarked_rollouts == 1000


def test_decision_regret_vs_oracle():
    """Verifies Decision Regret quantification against hindsight Oracle."""
    candidates = [
        {"action": "PIT_NOW", "label": "Pit Now", "time_delta_s": -3.8, "expected_finish": 1.2},
        {"action": "PIT_PLUS_2", "label": "Pit +2 Laps", "time_delta_s": -1.2, "expected_finish": 1.6},
        {"action": "STAY_OUT", "label": "Stay Out", "time_delta_s": 4.6, "expected_finish": 2.4},
    ]

    # Best action (Pit Now) has 0.0s regret
    regret_best, table = CounterfactualQualityEvaluator.calculate_decision_regret(
        candidates=candidates,
        chosen_action="PIT_NOW",
    )
    assert regret_best.expected_regret_s == 0.0
    assert regret_best.position_regret == 0.0
    assert regret_best.is_pareto_optimal is True

    # Sub-optimal action (Stay Out) has positive regret
    regret_sub, _ = CounterfactualQualityEvaluator.calculate_decision_regret(
        candidates=candidates,
        chosen_action="STAY_OUT",
    )
    assert regret_sub.expected_regret_s == round(4.6 - (-3.8), 2)  # 8.4s
    assert regret_sub.position_regret == 1.2
    assert regret_sub.is_pareto_optimal is False


@pytest.mark.asyncio
async def test_api_counterfactual_quality_endpoint():
    """Tests GET /api/strategy/counterfactual-quality route."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/strategy/counterfactual-quality")
        assert res.status_code == 200
        data = res.json()

        assert "rollout_consistency" in data
        assert "strategy_stability" in data
        assert "simulation_latency" in data
        assert "decision_regret" in data

        assert data["rollout_consistency"]["is_converged"] is True
        assert data["strategy_stability"]["stability_score_pct"] >= 85.0
        assert data["simulation_latency"]["p50_latency_ms"] > 0
        assert data["decision_regret"]["expected_regret_s"] == 0.0
