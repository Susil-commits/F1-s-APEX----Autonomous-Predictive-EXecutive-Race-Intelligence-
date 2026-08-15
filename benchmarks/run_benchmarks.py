"""Automated benchmark comparison suite: Random vs Rule-Based vs Trained DQN."""
import os
import sys
import numpy as np
from typing import Dict, List, Any

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TyreCompound, TrackCondition
from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.strategy.rule_engine import RuleEngine
from backend.app.strategy.dqn_agent import DQNAgent


class BenchmarkSuite:
    """Evaluates multiple strategy policies across identical deterministic race seeds."""

    def __init__(self, num_races: int = 15, track_name: str = "silverstone"):
        self.num_races = num_races
        self.track_name = track_name
        self.dqn_agent = DQNAgent()

    def run_race_with_policy(self, seed: int, policy_type: str) -> Dict[str, Any]:
        """Runs a complete race under a specific policy."""
        sim = RaceSimulator(track_name=self.track_name, seed=seed, enable_dynamic_weather=True)
        blown_tyre_laps = 0
        total_pit_stops = 0

        while not sim.is_finished:
            player = sim.get_player_car()
            state = sim.get_state()

            # Select action based on policy
            if policy_type == "random":
                # Random choice with bias to maintain to avoid endless pitting
                if np.random.rand() < 0.85:
                    action = StrategyAction.MAINTAIN
                else:
                    action = np.random.choice([
                        StrategyAction.PUSH,
                        StrategyAction.CONSERVE,
                        StrategyAction.PIT_SOFT,
                        StrategyAction.PIT_MEDIUM,
                        StrategyAction.PIT_HARD,
                    ])
            elif policy_type == "rule_based":
                action, _, _ = RuleEngine.evaluate(state, player.car_id)
            elif policy_type == "dqn":
                obs = FeatureBuilder.extract_features(state)
                action, _ = self.dqn_agent.predict_action(obs)
                # Fallback to rule engine if model is not loaded
                if self.dqn_agent.model is None:
                    action, _, _ = RuleEngine.evaluate(state, player.car_id)
            else:
                action = StrategyAction.MAINTAIN

            if action in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD, StrategyAction.PIT_INTER, StrategyAction.PIT_WET):
                total_pit_stops += 1

            if player.tyre_cliff_reached and player.tyre_wear_pct > 80.0:
                blown_tyre_laps += 1

            sim.step(player_action=action)

        player_final = sim.get_player_car()
        winner_id = sim.winner_car_id

        return {
            "seed": seed,
            "policy": policy_type,
            "final_position": player_final.position,
            "is_win": player_final.position == 1,
            "is_podium": player_final.position <= 3,
            "total_time_s": player_final.total_race_time_s,
            "gap_to_winner_s": player_final.gap_to_leader_s,
            "pit_stops": player_final.pit_count,
            "blown_tyre_laps": blown_tyre_laps,
        }

    def evaluate_all(self) -> Dict[str, Dict[str, Any]]:
        """Runs comparative benchmark across all policies."""
        policies = ["random", "rule_based", "dqn"]
        seeds = [1000 + i * 47 for i in range(self.num_races)]
        results_by_policy: Dict[str, List[Dict[str, Any]]] = {p: [] for p in policies}

        print(f"[APEX Benchmark] Evaluating {len(policies)} policies across {self.num_races} seeded races on {self.track_name}...")

        for seed in seeds:
            for policy in policies:
                res = self.run_race_with_policy(seed=seed, policy_type=policy)
                results_by_policy[policy].append(res)

        # Aggregate statistics
        summary = {}
        for policy, runs in results_by_policy.items():
            positions = [r["final_position"] for r in runs]
            wins = sum(1 for r in runs if r["is_win"])
            podiums = sum(1 for r in runs if r["is_podium"])
            gaps = [r["gap_to_winner_s"] for r in runs]
            blown = [r["blown_tyre_laps"] for r in runs]
            pits = [r["pit_stops"] for r in runs]

            summary[policy] = {
                "avg_position": round(float(np.mean(positions)), 2),
                "win_rate_pct": round((wins / self.num_races) * 100.0, 1),
                "podium_rate_pct": round((podiums / self.num_races) * 100.0, 1),
                "avg_gap_to_winner_s": round(float(np.mean(gaps)), 2),
                "avg_blown_tyre_laps": round(float(np.mean(blown)), 2),
                "avg_pit_stops": round(float(np.mean(pits)), 1),
            }

        return summary


def print_summary_table(summary: Dict[str, Dict[str, Any]]):
    """Prints a formatted ASCII evaluation matrix."""
    header = f"{'Policy':<15} | {'Avg Pos':<9} | {'Win %':<7} | {'Podium %':<9} | {'Avg Gap to P1':<14} | {'Blown Tyre Laps':<15} | {'Avg Pits':<8}"
    sep = "-" * len(header)
    print("\n" + sep)
    print("APEX STRATEGY EVALUATION BENCHMARK RESULTS")
    print(sep)
    print(header)
    print(sep)
    for pol, stats in summary.items():
        name = pol.replace("_", " ").upper()
        print(f"{name:<15} | {stats['avg_position']:<9} | {stats['win_rate_pct']:<7}% | {stats['podium_rate_pct']:<9}% | +{stats['avg_gap_to_winner_s']:<13}s | {stats['avg_blown_tyre_laps']:<15} | {stats['avg_pit_stops']:<8}")
    print(sep + "\n")


if __name__ == "__main__":
    suite = BenchmarkSuite(num_races=15, track_name="silverstone")
    metrics = suite.evaluate_all()
    print_summary_table(metrics)
