"""Synthetic Data Factory: Large-scale scenario generator for imitation, supervised, and RL training."""
from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np
import pandas as pd

from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import SafetyCarStatus, TrackCondition
from backend.app.strategy.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

TRACK_POOL = ["silverstone", "monza", "spa", "monaco", "interlagos", "bahrain"]


class SyntheticDataFactory:
    """Generates thousands of diverse, physically valid race state-action-reward-outcome trajectories."""

    @classmethod
    def generate_scenario_dataset(
        cls,
        n_races: int = 20,
        output_csv: str | None = None,
        seed: int = 42,
    ) -> pd.DataFrame:
        """
        Runs simulated races across randomized tracks, weather regimes, and incident profiles,
        recording (state_features, expert_action, reward, next_state, outcome_position).
        """
        rng = np.random.default_rng(seed)
        records: list[dict[str, Any]] = []

        for r_idx in range(n_races):
            track = rng.choice(TRACK_POOL)
            race_seed = seed + r_idx * 137
            sim = RaceSimulator(track_name=track, seed=race_seed, enable_dynamic_weather=True)

            # Random incident injection chance
            inject_sc = rng.uniform() < 0.35
            sc_lap = rng.integers(10, 35) if inject_sc else -1

            inject_rain = rng.uniform() < 0.25
            rain_lap = rng.integers(8, 30) if inject_rain else -1

            step_count = 0
            while not sim.is_finished and step_count < 200:
                step_count += 1
                curr_lap = sim.current_lap

                if curr_lap == sc_lap:
                    sim.inject_safety_car(SafetyCarStatus.SAFETY_CAR, laps=4)
                    sc_lap = -1 # Disarm

                if curr_lap == rain_lap:
                    sim.inject_weather(TrackCondition.WET, rain_intensity=0.80)
                    rain_lap = -1

                state = sim.get_state()
                features = FeatureBuilder.extract_features(state)
                rec_action, _, _ = RuleEngine.evaluate(state)

                prev_player = sim.get_player_car()
                prev_pos = prev_player.position if prev_player else 1

                # Step simulation with expert rule
                next_state = sim.step(player_action=rec_action)
                next_player = sim.get_player_car()
                next_pos = next_player.position if next_player else 1

                reward = float(prev_pos - next_pos) * 3.0
                if next_state.is_finished:
                    reward += 100.0 if next_pos == 1 else (50.0 if next_pos <= 3 else 10.0)

                row = {
                    "race_idx": r_idx,
                    "track": track,
                    "lap": curr_lap,
                    "action": rec_action.value,
                    "reward": round(reward, 2),
                    "position": next_pos,
                    "tyre_wear_pct": round(next_player.tyre_wear_pct, 1) if next_player else 0.0,
                    "track_condition": next_state.weather.condition.value,
                }
                # Attach feature dimensions
                for f_i, f_val in enumerate(features):
                    row[f"feat_{f_i}"] = round(float(f_val), 4)

                records.append(row)

        df = pd.DataFrame(records)
        if output_csv:
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            df.to_csv(output_csv, index=False)
            logger.info(f"[SyntheticDataFactory] Generated {len(df)} samples across {n_races} races -> {output_csv}")

        return df
