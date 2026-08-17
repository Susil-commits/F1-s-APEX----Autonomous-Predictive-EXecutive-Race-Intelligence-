"""Safe Reinforcement Learning (Safe RL) Action Masking Guardrail for APEX.

Enforces physical, regulatory, and environmental safety constraints on neural policy action spaces.
Applies dynamic action masking M(s) in {0, 1}^8 to prevent illegal or hazardous strategic decisions
(e.g., dry slicks during torrential rain, double-pitting in pit lane, or push mode at 80% wear cliff).
"""
import numpy as np
from pydantic import BaseModel

from backend.app.simulator.models import (
    RaceState,
    StrategyAction,
    TrackCondition,
)
from backend.app.strategy.gym_env import ACTION_MAP


class GuardrailEvaluation(BaseModel):
    is_safe: bool
    action_mask: list[bool]  # 8-element mask for ACTION_MAP
    masked_actions: list[str]
    allowed_actions: list[str]
    violations: list[str]


class ActionMaskGuardrail:
    """Computes dynamic safety action masks to guarantee Safe RL execution."""

    @classmethod
    def get_action_mask(cls, state: RaceState, target_car_id: str | None = None) -> np.ndarray:
        """
        Computes 8-D boolean mask array for ACTION_MAP.
        Returns: np.ndarray of dtype bool and shape (8,)
        """
        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0] if state.cars else None)
        mask = np.ones(len(ACTION_MAP), dtype=bool)

        if player is None or player.is_dnf:
            return mask

        is_in_pit = player.in_pit or player.pit_stop_queued_compound is not None
        is_wet = state.weather.condition == TrackCondition.WET or state.weather.rain_intensity > 0.40
        is_damp = state.weather.condition == TrackCondition.DAMP or (0.10 <= state.weather.rain_intensity <= 0.40)
        is_dry = state.weather.condition == TrackCondition.DRY and state.weather.rain_intensity < 0.10
        wear = player.tyre_wear_pct
        laps_remaining = max(1, state.total_laps - state.current_lap)

        for idx, action in ACTION_MAP.items():
            # Constraint 1: In Pit Lane
            if is_in_pit and action in (
                StrategyAction.PIT_SOFT,
                StrategyAction.PIT_MEDIUM,
                StrategyAction.PIT_HARD,
                StrategyAction.PIT_INTER,
                StrategyAction.PIT_WET,
            ):
                mask[idx] = False

            # Constraint 2: Weather Incompatibility (Dry slicks in torrential rain)
            if is_wet and action in (
                StrategyAction.PIT_SOFT,
                StrategyAction.PIT_MEDIUM,
                StrategyAction.PIT_HARD,
            ):
                mask[idx] = False

            # Constraint 3: Weather Incompatibility (Full wets on bone dry track)
            if is_dry and action == StrategyAction.PIT_WET and state.weather.rain_probability_next_5_laps < 0.30:
                mask[idx] = False

            # Constraint 4: Extreme Tyre Wear Push Danger (Risk of catastrophic delamination > 75%)
            if wear >= 75.0 and action == StrategyAction.PUSH:
                mask[idx] = False

            # Constraint 5: Final Lap Pit Stop Avoidance (Pitting with 1 lap left when tyres are intact)
            if laps_remaining <= 1 and wear < 65.0 and "PIT" in action.value:
                mask[idx] = False

        # Fallback: Ensure at least MAINTAIN is allowed
        if not np.any(mask):
            mask[0] = True

        return mask

    @classmethod
    def apply_mask_to_q_values(
        cls,
        q_values: np.ndarray,
        state: RaceState,
        target_car_id: str | None = None,
        mask_penalty: float = -1e9,
    ) -> np.ndarray:
        """
        Applies boolean safety mask to Q-values, penalizing invalid actions to -infinity.
        """
        mask = cls.get_action_mask(state, target_car_id=target_car_id)
        safe_q = q_values.copy()
        safe_q[~mask] = mask_penalty
        return safe_q

    @classmethod
    def evaluate_safety(
        cls,
        proposed_action: StrategyAction,
        state: RaceState,
        target_car_id: str | None = None,
    ) -> GuardrailEvaluation:
        """
        Validates whether a specific proposed strategic action complies with all safety rules.
        """
        mask = cls.get_action_mask(state, target_car_id=target_car_id)
        action_names = [ACTION_MAP[i].value for i in range(len(ACTION_MAP))]
        allowed = [action_names[i] for i in range(len(ACTION_MAP)) if mask[i]]
        masked = [action_names[i] for i in range(len(ACTION_MAP)) if not mask[i]]

        is_safe = proposed_action.value in allowed
        violations = []
        if not is_safe:
            violations.append(f"Action '{proposed_action.value}' is masked due to physical/environmental constraints.")

        return GuardrailEvaluation(
            is_safe=is_safe,
            action_mask=mask.tolist(),
            masked_actions=masked,
            allowed_actions=allowed,
            violations=violations,
        )
