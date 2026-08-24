"""Unit and integration tests for RL vs Non-RL Strategy Benchmark."""
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.simulator.engine import RaceSimulator
from backend.eval.rl_vs_non_rl_benchmark import (
    DQNController,
    HeuristicController,
    RuleBasedController,
    SupervisedPolicyController,
    run_rl_vs_non_rl_benchmark,
)


def test_controllers_action_selection():
    """Verifies that all 4 strategy controllers return valid actions for a race state."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.get_state()

    rule_ctrl = RuleBasedController()
    heur_ctrl = HeuristicController()
    sup_ctrl = SupervisedPolicyController()
    dqn_ctrl = DQNController()

    act_rule = rule_ctrl.select_action(state)
    act_heur = heur_ctrl.select_action(state)
    act_sup = sup_ctrl.select_action(state)
    act_dqn = dqn_ctrl.select_action(state)

    assert hasattr(act_rule, "value")
    assert hasattr(act_heur, "value")
    assert hasattr(act_sup, "value")
    assert hasattr(act_dqn, "value")


def test_rl_benchmark_runner_execution():
    """Runs a fast 2-race benchmark and verifies result payload schema."""
    report = run_rl_vs_non_rl_benchmark(num_races=2, save_plots=False)

    assert report["status"] == "PASS"
    assert "summary_table" in report
    assert len(report["summary_table"]) >= 4

    # Verify presence of metrics in each controller summary
    for row in report["summary_table"]:
        assert "average_reward" in row
        assert "average_position" in row
        assert "win_rate_pct" in row
        assert "pit_efficiency_pct" in row
        assert "tire_cliff_avoidance_pct" in row
        assert "total_constraint_violations" in row
        assert "decision_stability_score" in row


@pytest.mark.asyncio
async def test_rl_benchmark_api_endpoint():
    """Tests the GET /api/evaluation/rl-vs-non-rl endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/evaluation/rl-vs-non-rl")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PASS"
        assert "summary_table" in data
        assert "key_findings" in data
