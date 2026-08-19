"""Optuna Bayesian Hyperparameter Optimization Pipeline for APEX DQN Policy.

Conducts systematic multi-trial parameter sweeps across network architectures,
learning rates, replay buffer capacities, exploration schedules, and discount factors.
Evaluates candidates against the standardized APEX multi-circuit benchmark suite.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import optuna
from stable_baselines3 import DQN
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.strategy.gym_env import ApexRaceGymEnv
from benchmarks.run_benchmarks import BenchmarkSuite

# Suppress Optuna noisy info logs by default
optuna.logging.set_verbosity(optuna.logging.WARNING)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("APEX_HPO")

BEST_HPARAMS_PATH = Path(__file__).resolve().parent / "best_hyperparameters.json"
HPO_PLOT_PATH = Path(__file__).resolve().parent.parent / "models" / "hpo_search_results.png"


def create_env(track_name: str = "silverstone"):
    """Creates a monitored APEX Gymnasium environment."""
    return Monitor(ApexRaceGymEnv(track_name=track_name))


def evaluate_candidate_policy(
    model: DQN,
    tracks: list[str] | None = None,
    races_per_track: int = 1,
) -> dict[str, float]:
    """Evaluates a trained policy across circuits and computes aggregate performance metrics."""
    if tracks is None:
        tracks = ["silverstone", "monza", "spa"]

    win_rates = []
    podium_rates = []
    gaps = []
    blown_tyres = []

    for track in tracks:
        suite = BenchmarkSuite(num_races=races_per_track, track_name=track)
        results = suite.evaluate_track()
        dqn_m = results["policies"].get("dqn", {})
        win_rates.append(dqn_m.get("win_rate_pct", 0.0))
        podium_rates.append(dqn_m.get("podium_rate_pct", 0.0))
        gaps.append(dqn_m.get("avg_gap_to_winner_s", 50.0))
        blown_tyres.append(dqn_m.get("avg_blown_tyre_laps", 10.0))

    avg_win = float(np.mean(win_rates)) if win_rates else 0.0
    avg_podium = float(np.mean(podium_rates)) if podium_rates else 0.0
    avg_gap = float(np.mean(gaps)) if gaps else 50.0
    avg_blown = float(np.mean(blown_tyres)) if blown_tyres else 10.0

    # Composite objective score: Rewards wins/podiums, penalizes gap and blown tyres
    composite_score = (avg_win * 0.5) + (avg_podium * 0.3) - (min(avg_gap, 20.0) * 1.5) - (avg_blown * 5.0)

    return {
        "composite_score": round(composite_score, 2),
        "avg_win_rate_pct": round(avg_win, 1),
        "avg_podium_rate_pct": round(avg_podium, 1),
        "avg_gap_to_winner_s": round(avg_gap, 2),
        "avg_blown_tyres": round(avg_blown, 2),
    }


def objective(trial: optuna.Trial, steps_per_trial: int = 15000) -> float:
    """Optuna objective function for training and scoring a DQN policy trial."""
    # 1. Hyperparameter Sampling
    learning_rate = trial.suggest_float("learning_rate", 1e-4, 1e-3, log=True)
    buffer_size = trial.suggest_categorical("buffer_size", [20000, 50000, 80000])
    batch_size = trial.suggest_categorical("batch_size", [64, 128, 256])
    gamma = trial.suggest_float("gamma", 0.95, 0.995)
    tau = trial.suggest_float("tau", 0.01, 0.05)
    exploration_fraction = trial.suggest_float("exploration_fraction", 0.20, 0.45)
    arch_choice = trial.suggest_categorical("net_arch", ["64_64", "128_128", "128_128_64"])

    arch_map = {
        "64_64": [64, 64],
        "128_128": [128, 128],
        "128_128_64": [128, 128, 64],
    }
    net_arch = arch_map[arch_choice]

    # 2. Build Environment & Model
    train_env = DummyVecEnv([lambda: create_env("silverstone")])
    model = DQN(
        policy="MlpPolicy",
        env=train_env,
        learning_rate=learning_rate,
        buffer_size=buffer_size,
        learning_starts=1000,
        batch_size=batch_size,
        tau=tau,
        gamma=gamma,
        train_freq=4,
        gradient_steps=2,
        target_update_interval=500,
        exploration_fraction=exploration_fraction,
        exploration_initial_eps=1.0,
        exploration_final_eps=0.03,
        policy_kwargs=dict(net_arch=net_arch),
        verbose=0,
    )

    # 3. Train policy for trial duration
    model.learn(total_timesteps=steps_per_trial, progress_bar=False)

    # 4. Evaluate on multi-circuit benchmark
    metrics = evaluate_candidate_policy(model, tracks=["silverstone", "monza"], races_per_track=1)

    trial.set_user_attr("win_rate_pct", metrics["avg_win_rate_pct"])
    trial.set_user_attr("podium_rate_pct", metrics["avg_podium_rate_pct"])
    trial.set_user_attr("avg_gap_s", metrics["avg_gap_to_winner_s"])
    trial.set_user_attr("avg_blown_tyres", metrics["avg_blown_tyres"])

    logger.info(
        f"Trial {trial.number:02d} | Score: {metrics['composite_score']:6.2f} | "
        f"Win%: {metrics['avg_win_rate_pct']:5.1f}% | Podium%: {metrics['avg_podium_rate_pct']:5.1f}% | "
        f"LR: {learning_rate:.2e} | Arch: {arch_choice}"
    )

    return metrics["composite_score"]


def run_hpo_sweep(
    n_trials: int = 15,
    steps_per_trial: int = 15000,
    output_json: Path = BEST_HPARAMS_PATH,
    plot_path: Path = HPO_PLOT_PATH,
) -> dict[str, Any]:
    """Runs full Bayesian HPO sweep, saves best config, and generates visualization."""
    logger.info("=" * 80)
    logger.info(f"Starting APEX Optuna Hyperparameter Optimization ({n_trials} trials, {steps_per_trial} steps/trial)")
    logger.info("=" * 80)

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler, study_name="apex_dqn_tuning")

    study.optimize(lambda t: objective(t, steps_per_trial=steps_per_trial), n_trials=n_trials)

    best_trial = study.best_trial
    logger.info("=" * 80)
    logger.info(f"🏆 Best Trial #{best_trial.number} achieved Composite Score: {best_trial.value:.2f}")
    logger.info(f"Optimal Parameters: {best_trial.params}")
    logger.info("=" * 80)

    best_payload = {
        "study_name": "apex_dqn_tuning",
        "total_trials": n_trials,
        "steps_per_trial": steps_per_trial,
        "best_trial_number": best_trial.number,
        "best_composite_score": best_trial.value,
        "best_parameters": best_trial.params,
        "best_metrics": {
            "win_rate_pct": best_trial.user_attrs.get("win_rate_pct", 0.0),
            "podium_rate_pct": best_trial.user_attrs.get("podium_rate_pct", 0.0),
            "avg_gap_s": best_trial.user_attrs.get("avg_gap_s", 0.0),
            "avg_blown_tyres": best_trial.user_attrs.get("avg_blown_tyres", 0.0),
        },
    }

    # Save to best_hyperparameters.json
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(best_payload, f, indent=2)
    logger.info(f"Saved optimal configuration to {output_json}")

    # Generate visualization plot
    try:
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        trial_numbers = [t.number for t in study.trials]
        trial_values = [t.value for t in study.trials]
        best_so_far = np.maximum.accumulate(trial_values)

        plt.figure(figsize=(10, 5), dpi=150)
        plt.scatter(trial_numbers, trial_values, color="#00d2be", alpha=0.7, s=60, label="Trial Score")
        plt.plot(trial_numbers, best_so_far, color="#e10600", linewidth=2.5, label="Pareto Best Objective Score")
        plt.title("APEX Bayesian Hyperparameter Search Convergence (Optuna TPE)", fontsize=12, fontweight="bold")
        plt.xlabel("Trial Number", fontsize=10)
        plt.ylabel("Multi-Circuit Benchmark Score", fontsize=10)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()
        logger.info(f"Saved optimization history plot to {plot_path}")
    except Exception as e:
        logger.warning(f"Could not generate HPO plot: {e}")

    return best_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tune APEX DQN Hyperparameters using Optuna")
    parser.add_argument("--trials", type=int, default=10, help="Number of Optuna search trials")
    parser.add_argument("--steps", type=int, default=8000, help="Training timesteps per trial")
    args = parser.parse_args()

    run_hpo_sweep(n_trials=args.trials, steps_per_trial=args.steps)
