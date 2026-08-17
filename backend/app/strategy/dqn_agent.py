"""DQN Neural Policy Agent with Safe RL Action Masking and Epistemic Uncertainty."""
import os
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
import torch
from stable_baselines3 import DQN

from backend.app.simulator.models import StrategyAction
from backend.app.strategy.gym_env import ACTION_MAP, ApexRaceGymEnv


MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "apex_dqn.zip")


class DQNAgent:
    """Wrapper for DQN reinforcement learning strategy policy with epistemic uncertainty and Safe RL action masking."""

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

    def get_q_values(self, obs: np.ndarray, action_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Extracts raw or masked Q-value vector Q(s, a) across all 8 strategic actions.
        """
        if self.model is None:
            q_vals = np.zeros(len(ACTION_MAP), dtype=np.float32)
        else:
            try:
                with torch.no_grad():
                    obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0).to(self.model.device)
                    q_tensor = self.model.q_net(obs_tensor).squeeze(0)
                    q_vals = q_tensor.cpu().numpy()
            except Exception:
                q_vals = np.zeros(len(ACTION_MAP), dtype=np.float32)

        if action_mask is not None:
            masked_q = q_vals.copy()
            masked_q[~action_mask] = -1e9
            return masked_q

        return q_vals

    def predict_action(
        self,
        obs: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
    ) -> Tuple[StrategyAction, float]:
        """
        Predicts the optimal strategic action and estimated Q-value margin.
        If action_mask is provided, invalid actions are filtered out (Safe RL).
        Returns: (StrategyAction, q_value_margin)
        """
        if self.model is None:
            return StrategyAction.MAINTAIN, 0.0

        if action_mask is not None:
            q_values = self.get_q_values(obs, action_mask=action_mask)
            best_idx = int(np.argmax(q_values))
            action = ACTION_MAP.get(best_idx, StrategyAction.MAINTAIN)
        else:
            action_int, _ = self.model.predict(obs, deterministic=True)
            action = ACTION_MAP.get(int(action_int), StrategyAction.MAINTAIN)
            q_values = self.get_q_values(obs)

        if len(q_values) >= 2:
            sorted_q = np.sort(q_values)[::-1]
            q_margin = float(sorted_q[0] - sorted_q[1]) if sorted_q[1] > -1e8 else float(sorted_q[0])
        else:
            q_margin = 1.0

        return action, round(q_margin, 2)

    def predict_action_distribution(
        self,
        obs: np.ndarray,
        temperature: float = 1.0,
        action_mask: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """
        Computes Boltzmann softmax probability distribution pi(a|s) across all 8 actions.
        """
        q_vals = self.get_q_values(obs, action_mask=action_mask)
        tau = max(0.01, temperature)
        valid_q = q_vals[q_vals > -1e8]
        max_q = np.max(valid_q) if len(valid_q) > 0 else 0.0
        shifted_q = (q_vals - max_q) / tau
        exp_q = np.exp(np.clip(shifted_q, -50.0, 50.0))
        if action_mask is not None:
            exp_q[~action_mask] = 0.0
        sum_exp = np.sum(exp_q)
        probs = (exp_q / sum_exp) if sum_exp > 0 else np.ones_like(exp_q) / len(exp_q)

        return {
            ACTION_MAP[i].value: round(float(probs[i]), 4)
            for i in range(len(ACTION_MAP))
        }

    def compute_policy_entropy(
        self,
        obs: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
    ) -> float:
        """
        Computes normalized policy Shannon entropy H(pi) in [0.0, 1.0] as uncertainty metric.
        High entropy indicates high strategic ambiguity.
        """
        probs = list(self.predict_action_distribution(obs, temperature=1.0, action_mask=action_mask).values())
        probs_arr = np.array(probs)
        probs_arr = probs_arr[probs_arr > 1e-8]
        entropy = -np.sum(probs_arr * np.log2(probs_arr))
        max_entropy = np.log2(len(ACTION_MAP))  # log2(8) = 3.0
        return round(float(entropy / max_entropy), 3)

    def compute_action_advantages(
        self,
        obs: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """
        Computes advantage A(s, a) = Q(s, a) - V(s) where V(s) is max_a Q(s, a).
        """
        q_vals = self.get_q_values(obs, action_mask=action_mask)
        valid_q = q_vals[q_vals > -1e8]
        v_s = float(np.max(valid_q)) if len(valid_q) > 0 else 0.0
        advantages = q_vals - v_s

        return {
            ACTION_MAP[i].value: round(float(advantages[i]), 3)
            for i in range(len(ACTION_MAP))
        }

    def predict_strategic_profile(
        self,
        obs: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Produces full neural policy decision profile with action probabilities, advantages, and uncertainty.
        """
        action, q_margin = self.predict_action(obs, action_mask=action_mask)
        distribution = self.predict_action_distribution(obs, action_mask=action_mask)
        advantages = self.compute_action_advantages(obs, action_mask=action_mask)
        entropy = self.compute_policy_entropy(obs, action_mask=action_mask)

        return {
            "optimal_action": action.value,
            "q_value_margin": q_margin,
            "policy_entropy": entropy,
            "is_confident": (entropy < 0.45 and q_margin > 0.5),
            "action_distribution": distribution,
            "action_advantages": advantages,
        }
