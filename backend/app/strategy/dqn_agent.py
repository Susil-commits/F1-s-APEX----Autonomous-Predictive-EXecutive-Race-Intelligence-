"""DQN Agent wrapper using Stable-Baselines3."""
import os
from typing import Optional, Tuple
import numpy as np
import torch
from stable_baselines3 import DQN

from backend.app.simulator.models import StrategyAction
from backend.app.strategy.gym_env import ACTION_MAP, ApexRaceGymEnv


MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "apex_dqn.zip")


class DQNAgent:
    """Wrapper for DQN reinforcement learning strategy policy."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_PATH
        self.model: Optional[DQN] = None
        self._load_model()

    def _load_model(self):
        """Loads trained DQN model weights if available."""
        if os.path.exists(self.model_path):
            try:
                self.model = DQN.load(self.model_path)
                print(f"[DQNAgent] Loaded trained policy checkpoint from {self.model_path}")
            except Exception as e:
                print(f"[DQNAgent] Warning: Failed to load model from {self.model_path}: {e}")
                self.model = None
        else:
            self.model = None

    def predict_action(self, obs: np.ndarray) -> Tuple[StrategyAction, float]:
        """
        Predicts the optimal strategic action and estimated Q-value margin.
        Returns: (StrategyAction, q_value_margin)
        """
        if self.model is None:
            return StrategyAction.MAINTAIN, 0.0

        action_int, _ = self.model.predict(obs, deterministic=True)
        action = ACTION_MAP.get(int(action_int), StrategyAction.MAINTAIN)

        # Estimate Q-value margin if Q-network is accessible
        q_margin = 1.0
        try:
            with torch.no_grad():
                obs_tensor = torch.as_tensor(obs).unsqueeze(0).to(self.model.device)
                q_values = self.model.q_net(obs_tensor).squeeze(0)
                sorted_q = torch.sort(q_values, descending=True).values
                if len(sorted_q) >= 2:
                    q_margin = float(sorted_q[0] - sorted_q[1])
        except Exception:
            q_margin = 1.0

        return action, round(q_margin, 2)
