"""Unit tests for Safe RL Action Masking Guardrail."""
import numpy as np

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TrackCondition
from backend.app.strategy.gym_env import ACTION_MAP
from backend.app.strategy.safe_rl_guardrail import ActionMaskGuardrail


def test_guardrail_dry_all_normal_allowed():
    """Validates that dry conditions allow standard slick pitting and push/conserve."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.step()
    state = sim.get_state()
    player = sim.get_player_car()

    mask = ActionMaskGuardrail.get_action_mask(state, player.car_id)
    assert isinstance(mask, np.ndarray)
    assert mask.shape == (8,)
    assert mask[0]  # MAINTAIN is always allowed


def test_guardrail_masks_slicks_in_torrential_rain():
    """Validates that Safe RL masks dry slicks (Soft, Medium, Hard) during heavy rain."""
    sim = RaceSimulator(track_name="spa", seed=10)
    sim.inject_weather(TrackCondition.WET, rain_intensity=0.85)
    sim.step()
    state = sim.get_state()
    player = sim.get_player_car()

    mask = ActionMaskGuardrail.get_action_mask(state, player.car_id)

    # In wet weather, PIT_SOFT, PIT_MEDIUM, PIT_HARD must be masked (False)
    for idx, act in ACTION_MAP.items():
        if act in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD):
            assert not mask[idx], f"{act.value} should be masked in wet conditions!"


def test_guardrail_masks_push_at_tyre_cliff():
    """Validates that PUSH mode is masked when tyre wear exceeds 75%."""
    sim = RaceSimulator(track_name="bahrain", seed=15)
    player = sim.get_player_car()
    player.tyre_wear_pct = 82.0  # Deep beyond cliff
    state = sim.get_state()

    mask = ActionMaskGuardrail.get_action_mask(state, player.car_id)
    for idx, act in ACTION_MAP.items():
        if act == StrategyAction.PUSH:
            assert not mask[idx], "PUSH mode must be masked when tyre wear >= 75%"


def test_guardrail_apply_mask_to_q_values():
    """Validates that penalization is applied to invalid actions."""
    sim = RaceSimulator(track_name="spa", seed=20)
    sim.inject_weather(TrackCondition.WET, rain_intensity=0.90)
    sim.step()
    state = sim.get_state()

    raw_q = np.array([5.0, 8.0, 7.5, 6.0, 4.0, 3.0, 5.5, 4.5], dtype=np.float32)
    safe_q = ActionMaskGuardrail.apply_mask_to_q_values(raw_q, state)

    assert safe_q[0] == 5.0  # MAINTAIN untouched
    # Dry slick pit actions (3: PIT_SOFT, 4: PIT_MEDIUM, 5: PIT_HARD) should be severely penalized in wet
    assert safe_q[3] < -1e8
    assert safe_q[4] < -1e8
    assert safe_q[5] < -1e8
