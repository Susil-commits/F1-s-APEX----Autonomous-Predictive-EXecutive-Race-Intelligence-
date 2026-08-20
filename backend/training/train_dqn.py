"""Enterprise-grade DQN Training Pipeline for APEX Strategy Engine."""
import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from backend.app.strategy.gym_env import ApexRaceGymEnv


class EpisodeRewardLogger(BaseCallback):
    """Logs episode rewards and lengths during DQN policy training."""

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
        self.episode_rewards: list[float] = []
        self.episode_lengths: list[int] = []

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if "episode" in info:
                self.episode_rewards.append(info["episode"]["r"])
                self.episode_lengths.append(info["episode"]["l"])
        return True


def train(
    total_timesteps: int = 150000,
    save_dir: str = "backend/models",
    plot_path: str = "backend/models/training_rewards.png",
    distill: bool = False,
):
    """Trains a high-performance DQN policy with evaluation callbacks and artifact logging."""
    os.makedirs(save_dir, exist_ok=True)
    model_save_path = os.path.join(save_dir, "apex_dqn.zip")

    print("[APEX DQN] Initializing training & evaluation environments...")

    def make_train_env():
        env = ApexRaceGymEnv(track_name="silverstone")
        return Monitor(env)

    def make_eval_env():
        env = ApexRaceGymEnv(track_name="silverstone")
        return Monitor(env)

    train_env = DummyVecEnv([make_train_env])
    eval_env = DummyVecEnv([make_eval_env])

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=save_dir,
        log_path=save_dir,
        eval_freq=max(2000, total_timesteps // 25),
        n_eval_episodes=5,
        deterministic=True,
        render=False,
        verbose=1,
    )

    reward_logger = EpisodeRewardLogger()

    print("[APEX DQN] Creating DQN Agent with Prioritized Exploration & 50k Replay Buffer...")
    model = DQN(
        policy="MlpPolicy",
        env=train_env,
        learning_rate=3e-4,
        buffer_size=50000,
        learning_starts=2000,
        batch_size=128,
        tau=0.02,
        gamma=0.99,
        train_freq=4,
        gradient_steps=2,
        target_update_interval=500,
        exploration_fraction=0.35,
        exploration_initial_eps=1.0,
        exploration_final_eps=0.03,
        policy_kwargs={"net_arch": [128, 128, 64]},
        verbose=1,
    )

    print(f"[APEX DQN] Starting training for {total_timesteps} timesteps...")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, reward_logger],
        progress_bar=False,
    )

    # Save final model
    print(f"[APEX DQN] Saving trained policy to {model_save_path}...")
    model.save(model_save_path)

    # Check if best_model.zip exists and update apex_dqn.zip if superior
    best_model_path = os.path.join(save_dir, "best_model.zip")
    if os.path.exists(best_model_path):
        import shutil
        shutil.copy(best_model_path, model_save_path)
        print("[APEX DQN] Synced apex_dqn.zip with best evaluation checkpoint.")

    # Export training curves plot
    if len(reward_logger.episode_rewards) > 0:
        try:
            plt.figure(figsize=(10, 5), dpi=150)
            episodes = np.arange(1, len(reward_logger.episode_rewards) + 1)
            raw_rewards = np.array(reward_logger.episode_rewards)

            # Compute rolling moving average
            window = max(1, min(20, len(raw_rewards) // 5))
            moving_avg = np.convolve(raw_rewards, np.ones(window) / window, mode="valid")

            plt.plot(episodes, raw_rewards, alpha=0.3, color="#00d2be", label="Episode Reward")
            plt.plot(
                episodes[window - 1:],
                moving_avg,
                color="#e10600",
                linewidth=2.0,
                label=f"Rolling Average ({window} eps)",
            )
            plt.title("APEX Deep Q-Network Policy Training Reward Convergence", fontsize=12, fontweight="bold")
            plt.xlabel("Episode Number", fontsize=10)
            plt.ylabel("Cumulative Episode Reward", fontsize=10)
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.legend()
            plt.tight_layout()
            plt.savefig(plot_path)
            plt.close()
            print(f"[APEX DQN] Training reward curve saved to {plot_path}")
        except Exception as e:
            print(f"[APEX DQN] Warning: Could not generate training plot: {e}")

    print("[APEX DQN] Training completed successfully!")

    if distill:
        print("[APEX DQN] Triggering automatic surrogate distillation pipeline...")
        from backend.training.distill_dqn_surrogate import run_distillation
        run_distillation(dqn_model_path=model_save_path)
    else:
        print("[APEX DQN] Note: To update TreeSHAP surrogate explainers, run: python -m backend.training.distill_dqn_surrogate (or pass --distill)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train APEX DQN Agent")
    parser.add_argument("--steps", type=int, default=80000, help="Total training timesteps")
    parser.add_argument("--distill", action="store_true", help="Automatically run surrogate distillation pipeline after training")
    args = parser.parse_args()
    train(total_timesteps=args.steps, distill=args.distill)

