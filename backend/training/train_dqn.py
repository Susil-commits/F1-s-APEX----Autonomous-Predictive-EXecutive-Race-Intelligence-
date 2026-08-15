"""Training script for APEX DQN strategy policy."""
import os
import sys
import argparse
from stable_baselines3 import DQN

from backend.app.strategy.gym_env import ApexRaceGymEnv


def train(total_timesteps: int = 15000, save_dir: str = "backend/models"):
    """Trains a DQN policy on the APEX Gymnasium environment."""
    os.makedirs(save_dir, exist_ok=True)
    model_save_path = os.path.join(save_dir, "apex_dqn.zip")

    print(f"[APEX] Initializing Gymnasium environment...")
    env = ApexRaceGymEnv(track_name="silverstone")

    print(f"[APEX] Creating DQN Agent (MlpPolicy, buffer_size=8000, lr=1e-3)...")
    model = DQN(
        policy="MlpPolicy",
        env=env,
        learning_rate=1e-3,
        buffer_size=8000,
        learning_starts=300,
        batch_size=64,
        tau=0.05,
        gamma=0.98,
        train_freq=4,
        gradient_steps=1,
        target_update_interval=200,
        exploration_fraction=0.25,
        exploration_initial_eps=1.0,
        exploration_final_eps=0.05,
        verbose=0,
    )

    print(f"[APEX] Starting DQN training for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps, progress_bar=False)

    print(f"[APEX] Saving trained policy to {model_save_path}...")
    model.save(model_save_path)
    print(f"[APEX] Training completed successfully! Checkpoint saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train APEX DQN Agent")
    parser.add_argument("--steps", type=int, default=10000, help="Total training timesteps")
    args = parser.parse_args()
    train(total_timesteps=args.steps)
