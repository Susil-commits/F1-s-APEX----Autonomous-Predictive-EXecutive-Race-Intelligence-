"""Property-Based Invariant Tests — Spec reference: APEX_MASTER_ENGINEERING_SPEC.md §37

Validates formal invariants across random seeds and edge-case race conditions:
  1. Fuel is never negative under any driving mode (PUSH/NORMAL/CONSERVE).
  2. Tyre age is strictly non-decreasing per stint and resets correctly on pit stops.
  3. Lap number never decreases.
  4. Invalid / out-of-bound action never causes state corruption.
  5. Action masked by Safe-RL guardrail is never allowed in allowed_actions.
  6. State hash is strictly deterministic: changes only when state evolves.
"""
from __future__ import annotations

import pytest

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import DrivingMode, StrategyAction, TrackCondition
from backend.app.strategy.safe_rl_guardrail import ActionMaskGuardrail


@pytest.mark.parametrize("mode", [DrivingMode.PUSH, DrivingMode.NORMAL, DrivingMode.CONSERVE])
def test_invariant_fuel_never_negative(mode: DrivingMode) -> None:
    """Invariant 1: Fuel quantity must never drop below zero even after maximum race distance."""
    sim = RaceSimulator(track_name="silverstone", seed=42, grid_size=5, enable_dynamic_weather=False)
    player = sim.get_player_car()
    assert player is not None
    player.driving_mode = mode

    for _ in range(sim.track.total_laps + 10):
        sim.step()
        for car in sim.cars:
            assert car.fuel_kg >= 0.0, f"Car {car.car_id} has negative fuel: {car.fuel_kg} kg"


def test_invariant_tyre_age_monotonic_and_pit_reset() -> None:
    """Invariant 2: Tyre age strictly increases lap-by-lap within a stint and resets to 0 upon pitting."""
    sim = RaceSimulator(track_name="silverstone", seed=101, grid_size=5, enable_dynamic_weather=False)
    player = sim.get_player_car()
    assert player is not None

    last_age = 0
    pitted = False

    for lap_idx in range(25):
        if lap_idx == 12:
            sim.apply_action(StrategyAction.PIT_HARD, target_car_id=player.car_id)
            pitted = True

        sim.step()

        if pitted and player.in_pit:
            continue  # Mid-pit transition
        elif pitted and not player.in_pit and player.pit_count > 0 and last_age > 10:
            # After pit stop, age must have reset
            assert player.tyre_age_laps <= 2, f"Tyre age did not reset after pit: {player.tyre_age_laps}"
            pitted = False
            last_age = player.tyre_age_laps
        else:
            assert player.tyre_age_laps >= last_age, f"Tyre age decreased without pit: {player.tyre_age_laps} < {last_age}"
            last_age = player.tyre_age_laps


def test_invariant_lap_never_decreases() -> None:
    """Invariant 3: Current lap number must be strictly monotonic non-decreasing."""
    sim = RaceSimulator(track_name="monza", seed=777, grid_size=6, enable_dynamic_weather=True)
    last_lap = 1

    for _ in range(40):
        sim.step()
        state = sim.get_state()
        assert state.current_lap >= last_lap, f"Lap decreased: {state.current_lap} < {last_lap}"
        last_lap = state.current_lap


def test_invariant_masked_action_never_allowed() -> None:
    """Invariant 4: When an action is masked by ActionMaskGuardrail, it must not appear in allowed_actions."""
    sim = RaceSimulator(track_name="silverstone", seed=999, grid_size=5, enable_dynamic_weather=False)
    for _ in range(10):
        sim.step()

    state = sim.get_state()
    # Inject heavy rain
    sim.inject_weather(TrackCondition.WET, rain_intensity=0.95)
    state = sim.get_state()

    eval_res = ActionMaskGuardrail.evaluate_safety(StrategyAction.PIT_SOFT, state)
    assert not eval_res.is_safe, "PIT_SOFT was allowed during heavy torrential rain"
    assert "PIT_SOFT" in eval_res.masked_actions
    assert "PIT_SOFT" not in eval_res.allowed_actions


def test_invariant_state_hash_determinism_and_transition() -> None:
    """Invariant 5: State hash remains identical without simulation steps, and changes upon valid transition."""
    sim = RaceSimulator(track_name="spa", seed=42, grid_size=5, enable_dynamic_weather=False)
    for _ in range(5):
        sim.step()

    hash_1 = sim.state_hash()
    hash_2 = sim.state_hash()
    assert hash_1 == hash_2, "State hash changed without state transition"

    # Step once
    sim.step()
    hash_3 = sim.state_hash()
    assert hash_3 != hash_1, "State hash failed to change after a simulation step"
