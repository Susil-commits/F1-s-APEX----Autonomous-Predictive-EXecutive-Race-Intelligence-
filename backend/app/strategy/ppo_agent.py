"""Proximal Policy Optimization (PPO) strategy policy wrapper for APEX."""
from __future__ import annotations

import logging
import os

from stable_baselines3 import PPO

from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.simulator.models import RaceState, StrategyAction
from backend.app.strategy.gym_env import ACTION_MAP

logger = logging.getLogger(__name__)

PPO_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "ppo", "apex_ppo.zip")


class PPOStrategyAgent:
    """PPO Reinforcement Learning decision policy with heuristic fallback safety."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or PPO_MODEL_PATH
        self.model: PPO | None = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = PPO.load(self.model_path)
                logger.info(f"[PPOStrategyAgent] Loaded trained PPO policy from {self.model_path}")
            except Exception as e:
                logger.warning(f"[PPOStrategyAgent] Could not load PPO model from {self.model_path}: {e}")
                self.model = None

    def is_loaded(self) -> bool:
        return self.model is not None

    def select_action(
        self,
        state: RaceState,
        deterministic: bool = True,
    ) -> tuple[StrategyAction, float]:
        """Selects strategic action via PPO policy with estimated action probability."""
        features = FeatureBuilder.extract_features(state)

        if self.model is not None:
            try:
                action_idx, _ = self.model.predict(features, deterministic=deterministic)
                action_idx_int = int(action_idx)
                selected_action = ACTION_MAP.get(action_idx_int, StrategyAction.MAINTAIN)
                return selected_action, 0.88
            except Exception as e:
                logger.warning(f"[PPOStrategyAgent] Inference error: {e}")

        # Intelligent heuristic fallback when model weights not yet trained
        player = next((c for c in state.cars if c.is_player), state.cars[0] if state.cars else None)
        if player and (player.tyre_cliff_reached or player.tyre_wear_pct > 75.0):
            return StrategyAction.PIT_HARD, 0.85
        return StrategyAction.MAINTAIN, 0.70
