"""Proximal Policy Optimization (PPO) strategy policy wrapper and inference engine for APEX.

Spec reference: APEX_MASTER_ENGINEERING_SPEC.md §16 (Gate F)

Provides:
- Value function estimation V(s)
- Full action probability distribution across all 8 strategic actions
- Action masking integration via ActionMaskGuardrail
- Policy entropy & uncertainty estimation
- Calibrated heuristic fallback when weights are uninitialized
"""
from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np

try:
    import torch
    from stable_baselines3 import PPO
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    PPO = Any  # type: ignore

from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.simulator.models import RaceState, StrategyAction, TrackCondition, TyreCompound
from backend.app.strategy.gym_env import ACTION_MAP
from backend.app.strategy.safe_rl_guardrail import ActionMaskGuardrail

logger = logging.getLogger(__name__)

PPO_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "ppo", "apex_ppo.zip"
)


class PPOStrategyAgent:
    """PPO Reinforcement Learning decision policy with action masking and distribution inference."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or PPO_MODEL_PATH
        self.model: Any = None
        self._load_model()

    def _load_model(self) -> None:
        if SB3_AVAILABLE and os.path.exists(self.model_path):
            try:
                self.model = PPO.load(self.model_path)
                logger.info(f"[PPOStrategyAgent] Loaded trained PPO policy from {self.model_path}")
            except Exception as e:
                logger.warning(f"[PPOStrategyAgent] Could not load PPO model from {self.model_path}: {e}")
                self.model = None
        else:
            self.model = None

    def is_loaded(self) -> bool:
        """Returns True if trained PPO neural network weights are active."""
        return self.model is not None

    def select_action(
        self,
        state: RaceState,
        deterministic: bool = True,
        apply_guardrail: bool = True,
    ) -> tuple[StrategyAction, float]:
        """Selects strategic action via PPO policy with estimated action confidence probability.

        Args:
            state: Active RaceState.
            deterministic: If True, takes argmax action; else samples from policy distribution.
            apply_guardrail: If True, masks out illegal actions via ActionMaskGuardrail.

        Returns:
            tuple of (StrategyAction, confidence_score [0.0 - 1.0])
        """
        features = FeatureBuilder.extract_features(state)
        mask = ActionMaskGuardrail.get_action_mask(state) if apply_guardrail else np.ones(len(ACTION_MAP), dtype=bool)

        if self.model is not None:
            try:
                obs_tensor = torch.as_tensor(features.reshape(1, -1), dtype=torch.float32)
                with torch.no_grad():
                    dist = self.model.policy.get_distribution(obs_tensor)
                    probs = dist.distribution.probs.cpu().numpy()[0]

                # Apply action mask to probability distribution
                masked_probs = probs * mask
                prob_sum = float(np.sum(masked_probs))
                if prob_sum > 1e-6:
                    normalized_probs = masked_probs / prob_sum
                else:
                    normalized_probs = mask.astype(float) / float(np.sum(mask))

                if deterministic:
                    action_idx = int(np.argmax(normalized_probs))
                else:
                    action_idx = int(np.random.choice(len(ACTION_MAP), p=normalized_probs))

                confidence = float(normalized_probs[action_idx])
                selected_action = ACTION_MAP.get(action_idx, StrategyAction.MAINTAIN)
                return selected_action, round(confidence, 3)

            except Exception as e:
                logger.warning(f"[PPOStrategyAgent] Inference error in policy distribution: {e}")

        # Intelligent domain heuristic fallback when model weights are uninitialized
        return self._heuristic_action(state, mask)

    def get_action_distribution(self, state: RaceState) -> dict[str, float]:
        """Computes probability distribution across all 8 discrete strategy actions."""
        features = FeatureBuilder.extract_features(state)
        mask = ActionMaskGuardrail.get_action_mask(state)

        if self.model is not None:
            try:
                obs_tensor = torch.as_tensor(features.reshape(1, -1), dtype=torch.float32)
                with torch.no_grad():
                    dist = self.model.policy.get_distribution(obs_tensor)
                    probs = dist.distribution.probs.cpu().numpy()[0]

                masked_probs = probs * mask
                prob_sum = float(np.sum(masked_probs))
                if prob_sum > 1e-6:
                    probs = masked_probs / prob_sum

                return {
                    ACTION_MAP[i].value: round(float(probs[i]), 4)
                    for i in range(len(ACTION_MAP))
                }
            except Exception:
                pass

        # Fallback distribution
        action, conf = self._heuristic_action(state, mask)
        dist = {}
        for idx, act in ACTION_MAP.items():
            if act == action:
                dist[act.value] = round(conf, 4)
            elif mask[idx]:
                dist[act.value] = round((1.0 - conf) / max(1, int(mask.sum()) - 1), 4)
            else:
                dist[act.value] = 0.0
        return dist

    def estimate_value(self, state: RaceState) -> float:
        """Estimates state value V(s) via the PPO critic/value network."""
        if self.model is not None:
            try:
                features = FeatureBuilder.extract_features(state)
                obs_tensor = torch.as_tensor(features.reshape(1, -1), dtype=torch.float32)
                with torch.no_grad():
                    value = self.model.policy.predict_values(obs_tensor).cpu().numpy()[0, 0]
                return round(float(value), 3)
            except Exception:
                pass

        player = next((c for c in state.cars if c.is_player), state.cars[0] if state.cars else None)
        if player is None or player.is_dnf:
            return -100.0

        n_cars = max(1, len(state.cars))
        pos_score = max(0.0, 100.0 - (player.position - 1) * (100.0 / n_cars))
        wear_penalty = (player.tyre_wear_pct / 100.0) * 20.0
        return round(pos_score - wear_penalty, 3)

    def _heuristic_action(
        self,
        state: RaceState,
        mask: np.ndarray,
    ) -> tuple[StrategyAction, float]:
        """Context-aware heuristic fallback guaranteeing safe valid actions."""
        player = next((c for c in state.cars if c.is_player), state.cars[0] if state.cars else None)
        if player is None or player.is_dnf:
            return StrategyAction.MAINTAIN, 0.99

        is_wet = state.weather.condition == TrackCondition.WET or state.weather.rain_intensity > 0.40
        is_damp = state.weather.condition == TrackCondition.DAMP or (0.10 <= state.weather.rain_intensity <= 0.40)
        is_slick = player.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)

        # Emergency weather pit
        if is_wet and is_slick and mask[7]:
            return StrategyAction.PIT_WET, 0.95
        if is_damp and is_slick and mask[6]:
            return StrategyAction.PIT_INTER, 0.90

        # Tyre wear cliff pit
        if (player.tyre_cliff_reached or player.tyre_wear_pct >= 75.0):
            if mask[5]:
                return StrategyAction.PIT_HARD, 0.88
            if mask[4]:
                return StrategyAction.PIT_MEDIUM, 0.85
            if mask[3]:
                return StrategyAction.PIT_SOFT, 0.80

        # High wear conserve
        if player.tyre_wear_pct > 60.0 and mask[2]:
            return StrategyAction.CONSERVE, 0.78

        # Clean air / overtake push
        if player.tyre_wear_pct < 40.0 and player.gap_to_car_ahead_s < 1.0 and mask[1]:
            return StrategyAction.PUSH, 0.75

        return StrategyAction.MAINTAIN, 0.70
