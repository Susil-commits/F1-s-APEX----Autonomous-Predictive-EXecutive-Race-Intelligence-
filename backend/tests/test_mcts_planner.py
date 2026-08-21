"""Unit tests for AlphaZero-style Monte Carlo Tree Search (MCTS) Strategy Planner."""
import pytest
from backend.app.simulator.engine import RaceSimulator
from backend.app.strategy.mcts_planner import MCTSStrategyPlanner, MCTSNodeData
from backend.app.simulator.models import StrategyAction


def test_mcts_planner_initialization():
    planner = MCTSStrategyPlanner(c_puct=1.414, rollout_depth=4)
    assert planner.c_puct == 1.414
    assert planner.rollout_depth == 4


def test_mcts_planner_search():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.get_state()

    planner = MCTSStrategyPlanner(c_puct=1.414, rollout_depth=3)
    best_action, tree, summary = planner.search(state, num_simulations=30)

    assert isinstance(best_action, StrategyAction)
    assert isinstance(tree, MCTSNodeData)
    assert summary["simulations_executed"] == 30
    assert summary["explored_branches"] > 0
    assert "win_probability_pct" in summary
    assert tree.node_id.startswith("node_")
    assert len(tree.children) > 0


def test_new_tracks_loading():
    for track_key in ["suzuka", "cota", "singapore", "redbullring"]:
        sim = RaceSimulator(track_name=track_key, seed=42)
        state = sim.get_state()
        assert state.track.name is not None
        assert state.track.total_laps > 0
        assert len(state.cars) > 0


def test_aerodynamics_and_ers_dynamics():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.step()
    state = sim.get_state()

    player = sim.get_player_car()
    assert player is not None
    assert 0.0 <= player.ers_battery_soc_pct <= 100.0
    assert player.speed_kmh > 200.0
    assert isinstance(player.in_dirty_air, bool)
