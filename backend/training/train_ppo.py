"""Training pipeline for PPO reinforcement learning strategy agent."""
from __future__ import annotations

import os
import argparse
import logging
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor

from backend.app.strategy.gym_env import ApexRaceGymEnv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "ppo")


def train_ppo(
    total_timesteps: int = 25000,
    track_name: str = "silverstone",
    seed: int = 42,
    output_dir: str = MODELS_DIR,
) -> str:
    """Trains a PPO policy on the APEX Gym environment."""
    os.makedirs(output_dir, exist_ok=True)

    env = Monitor(ApexRaceGymEnv(track_name=track_name, seed=seed))
    eval_env = Monitor(ApexRaceGymEnv(track_name=track_name, seed=seed + 100))

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=output_dir,
        log_path=output_dir,
        eval_freq=5000,
        n_eval_episodes=5,
        deterministic=True,
        render=False,
    )

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        seed=seed,
    )

    logger.info(f"[PPO Train] Commencing PPO training for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps, callback=eval_callback)

    final_path = os.path.join(output_dir, "apex_ppo.zip")
    model.save(final_path)
    logger.info(f"[PPO Train] Successfully saved trained PPO model to {final_path}")
    return final_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PPO Agent on APEX Race Environment")
    parser.add_argument("--timesteps", type=int, default=20000, help="Total training timesteps")
    parser.add_argument("--track", type=str, default="silverstone", help="Track name")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = parser.parse_args()

    train_ppo(total_timesteps=args.timesteps, track_name=args.track, seed=args.seed)
