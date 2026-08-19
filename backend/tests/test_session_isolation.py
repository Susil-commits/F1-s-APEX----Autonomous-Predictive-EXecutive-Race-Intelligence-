"""Tests for WebSocket multi-session isolation and concurrent race state independence."""
import asyncio
import pytest

from backend.app.api.websocket import ConnectionManager, RaceSession
from backend.app.simulator.models import StrategyAction


@pytest.mark.asyncio
async def test_session_isolation_independent_states():
    """Verifies that two distinct sessions operate on separate simulator instances with independent progression."""
    manager = ConnectionManager()

    # Initialize two distinct sessions on different tracks with different seeds
    state_a = await manager.init_race(track_name="silverstone", seed=42, session_id="session_alpha")
    state_b = await manager.init_race(track_name="monza", seed=99, session_id="session_beta")

    assert state_a.race_id != state_b.race_id
    assert manager.sessions["session_alpha"].track_name == "silverstone"
    assert manager.sessions["session_beta"].track_name == "monza"

    # Step session_alpha 3 times
    await manager.step_once(session_id="session_alpha")
    await manager.step_once(session_id="session_alpha")
    state_a_advanced = await manager.step_once(session_id="session_alpha")

    # Session beta should remain at lap 0 / initial state
    session_b = manager.sessions["session_beta"]
    assert state_a_advanced.current_lap > session_b.sim.current_lap


@pytest.mark.asyncio
async def test_session_isolation_speed_and_actions():
    """Verifies that speed settings and queued actions are strictly scoped to the session."""
    manager = ConnectionManager()
    await manager.init_race(session_id="session_1")
    await manager.init_race(session_id="session_2")

    manager.set_speed(5.0, session_id="session_1")
    manager.set_speed(1.0, session_id="session_2")

    assert manager.sessions["session_1"].sim_speed == 5.0
    assert manager.sessions["session_2"].sim_speed == 1.0

    manager.queue_action(StrategyAction.PIT_SOFT, session_id="session_1")
    assert manager.sessions["session_1"]._queued_player_action == StrategyAction.PIT_SOFT
    assert manager.sessions["session_2"]._queued_player_action is None


@pytest.mark.asyncio
async def test_default_session_backward_compatibility():
    """Verifies that legacy single-session calls map cleanly to the default session."""
    manager = ConnectionManager()
    state = await manager.init_race(track_name="spa", seed=10)

    assert manager.sim is not None
    assert "spa" in manager.sim.track.name.lower()
    assert manager.is_running is False
    assert manager.sim_speed == 1.0

    manager.set_speed(3.0)
    assert manager.sim_speed == 3.0
    assert manager.sessions["default"].sim_speed == 3.0
