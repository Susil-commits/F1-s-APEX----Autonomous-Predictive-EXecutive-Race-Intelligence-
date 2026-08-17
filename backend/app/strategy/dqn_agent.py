"""DQN Neural Policy Agent with Q-Value Tensor Distribution and Uncertainty Estimation."""
import os
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
import torch
from stable_baselines3 import DQN

from backend.app.simulator.models import StrategyAction
from backend.app.strategy.gym_env import ACTION_MAP, ApexRaceGymEnv


MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "apex_dqn.zip")


class DQNAgent:
    """Wrapper for DQN reinforcement learning strategy policy with epistemic uncertainty."""

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

    def get_q_values(self, obs: np.ndarray) -> np.ndarray:
        """
        Extracts raw Q-value vector Q(s, a) across all 8 strategic actions.
        """
        if self.model is None:
            return np.zeros(len(ACTION_MAP), dtype=np.float32)

        try:
            with torch.no_grad():
                obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0).to(self.model.device)
                q_tensor = self.model.q_net(obs_tensor).squeeze(0)
                return q_tensor.cpu().numpy()
        except Exception:
            return np.zeros(len(ACTION_MAP), dtype=np.float32)

    def predict_action(self, obs: np.ndarray) -> Tuple[StrategyAction, float]:
        """
        Predicts the optimal strategic action and estimated Q-value margin.
        Returns: (StrategyAction, q_value_margin)
        """
        if self.model is None:
            return StrategyAction.MAINTAIN, 0.0

        action_int, _ = self.model.predict(obs, deterministic=True)
        action = ACTION_MAP.get(int(action_int), StrategyAction.MAINTAIN)

        q_values = self.get_q_values(obs)
        if len(q_values) >= 2:
            sorted_q = np.sort(q_values)[::-1]
            q_margin = float(sorted_q[0] - sorted_q[1])
        else:
            q_margin = 1.0

        return action, round(q_margin, 2)

    def predict_action_distribution(self, obs: np.ndarray, temperature: float = 1.0) -> Dict[str, float]:
        """
        Computes Boltzmann softmax probability distribution pi(a|s) across all 8 actions.
        """
        q_vals = self.get_q_values(obs)
        tau = max(0.01, float(temperature))
        shifted_q = (q_vals - np.max(q_vals)) / tau
        exp_q = np.exp(shifted_q)
        probs = exp_q / np.sum(exp_q)

        return {
            ACTION_MAP[i].value: round(float(probs[i]), 4)
            for i in range(len(ACTION_MAP))
        }

    def compute_policy_entropy(self, obs: np.ndarray) -> float:
        """
        Computes normalized policy Shannon entropy H(pi) in [0.0, 1.0] as uncertainty metric.
        High entropy indicates high strategic ambiguity.
        """
        probs = list(self.predict_action_distribution(obs, temperature=1.0).values())
        probs_arr = np.array(probs)
        probs_arr = probs_arr[probs_arr > 1e-8]
        entropy = -np.sum(probs_arr * np.log2(probs_arr))
        max_entropy = np.log2(len(ACTION_MAP))  # log2(8) = 3.0
        return round(float(entropy / max_entropy), 3)

    def compute_action_advantages(self, obs: np.ndarray) -> Dict[str, float]:
        """
        Computes advantage A(s, a) = Q(s, a) - V(s) where V(s) is max_a Q(s, a).
        """
        q_vals = self.get_q_values(obs)
        v_s = float(np.max(q_vals))
        advantages = q_vals - v_s

        return {
            ACTION_MAP[i].value: round(float(advantages[i]), 3)
            for i in range(len(ACTION_MAP))
        }

    def predict_strategic_profile(self, obs: np.ndarray) -> Dict[str, Any]:
        """
        Produces full neural policy decision profile with action probabilities, advantages, and uncertainty.
        """
        action, q_margin = self.predict_action(obs)
        distribution = self.predict_action_distribution(obs)
        advantages = self.compute_action_advantages(obs)
        entropy = self.compute_policy_entropy(obs)

        return {
            "optimal_action": action.value,
            "q_value_margin": q_margin,
            "policy_entropy": entropy,
            "is_confident": bool(entropy < 0.45 and q_margin > 0.5),
            "action_distribution": distribution,
            "action_advantages": advantages,
        }
