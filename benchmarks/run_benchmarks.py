"""Automated benchmark comparison suite across circuits: Random vs Rule-Based vs Trained DQN."""
import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TyreCompound, TrackCondition
from backend.app.simulator.track import list_available_tracks
from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.strategy.rule_engine import RuleEngine
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.twin.database import get_db_session, init_db
from backend.app.twin.db_models import BenchmarkRunModel

DEFAULT_BENCHMARK_JSON = os.path.join(os.path.dirname(__file__), "latest_benchmark_results.json")


class BenchmarkSuite:
    """Evaluates multiple strategy policies across identical deterministic race seeds and circuits."""

    def __init__(self, num_races: int = 10, track_name: str = "silverstone"):
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
                if self.dqn_agent.model is None:
                    action, _, _ = RuleEngine.evaluate(state, player.car_id)
            else:
                action = StrategyAction.MAINTAIN

            if action in (
                StrategyAction.PIT_SOFT,
                StrategyAction.PIT_MEDIUM,
                StrategyAction.PIT_HARD,
                StrategyAction.PIT_INTER,
                StrategyAction.PIT_WET,
            ):
                total_pit_stops += 1

            if player.tyre_cliff_reached and player.tyre_wear_pct > 80.0:
                blown_tyre_laps += 1

            sim.step(player_action=action)

        player_final = sim.get_player_car()

        return {
            "seed": seed,
            "policy": policy_type,
            "final_position": player_final.position,
            "is_win": player_final.position == 1,
            "is_podium": player_final.position <= 3,
            "total_time_s": round(player_final.total_race_time_s, 2),
            "gap_to_winner_s": round(player_final.gap_to_leader_s, 2),
            "pit_stops": player_final.pit_count,
            "blown_tyre_laps": blown_tyre_laps,
        }

    def evaluate_track(self) -> Dict[str, Any]:
        """Runs comparative benchmark on this track across all policies."""
        policies = ["random", "rule_based", "dqn"]
        seeds = [1000 + i * 47 for i in range(self.num_races)]
        results_by_policy: Dict[str, List[Dict[str, Any]]] = {p: [] for p in policies}

        for seed in seeds:
            for policy in policies:
                res = self.run_race_with_policy(seed=seed, policy_type=policy)
                results_by_policy[policy].append(res)

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

        return {"track_name": self.track_name, "num_races": self.num_races, "policies": summary}


def run_multi_circuit_benchmark(
    tracks: Optional[List[str]] = None,
    races_per_track: int = 5,
    save_json: bool = True,
) -> Dict[str, Any]:
    """Runs end-to-end evaluation across all circuits and computes aggregate grand totals."""
    if tracks is None:
        tracks = ["silverstone", "monza", "spa", "monaco", "interlagos"]

    track_results = []
    policy_names = ["random", "rule_based", "dqn"]
    overall_aggregates = {
        p: {
            "avg_position": [],
            "win_rate_pct": [],
            "podium_rate_pct": [],
            "avg_gap_to_winner_s": [],
            "avg_blown_tyre_laps": [],
            "avg_pit_stops": [],
        }
        for p in policy_names
    }

    print(f"[APEX Benchmark] Starting multi-circuit evaluation across {len(tracks)} circuits ({races_per_track} races/track)...")

    for track in tracks:
        suite = BenchmarkSuite(num_races=races_per_track, track_name=track)
        res = suite.evaluate_track()
        track_results.append(res)

        for p in policy_names:
            pol_stats = res["policies"][p]
            overall_aggregates[p]["avg_position"].append(pol_stats["avg_position"])
            overall_aggregates[p]["win_rate_pct"].append(pol_stats["win_rate_pct"])
            overall_aggregates[p]["podium_rate_pct"].append(pol_stats["podium_rate_pct"])
            overall_aggregates[p]["avg_gap_to_winner_s"].append(pol_stats["avg_gap_to_winner_s"])
            overall_aggregates[p]["avg_blown_tyre_laps"].append(pol_stats["avg_blown_tyre_laps"])
            overall_aggregates[p]["avg_pit_stops"].append(pol_stats["avg_pit_stops"])

    # Compute overall averages
    final_overall = {}
    for p in policy_names:
        final_overall[p] = {
            "avg_position": round(float(np.mean(overall_aggregates[p]["avg_position"])), 2),
            "win_rate_pct": round(float(np.mean(overall_aggregates[p]["win_rate_pct"])), 1),
            "podium_rate_pct": round(float(np.mean(overall_aggregates[p]["podium_rate_pct"])), 1),
            "avg_gap_to_winner_s": round(float(np.mean(overall_aggregates[p]["avg_gap_to_winner_s"])), 2),
            "avg_blown_tyre_laps": round(float(np.mean(overall_aggregates[p]["avg_blown_tyre_laps"])), 2),
            "avg_pit_stops": round(float(np.mean(overall_aggregates[p]["avg_pit_stops"])), 1),
        }

    output_payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_tracks": len(tracks),
        "races_per_track": races_per_track,
        "total_races_evaluated": len(tracks) * races_per_track * len(policy_names),
        "overall_summary": final_overall,
        "circuit_breakdown": track_results,
    }

    if save_json:
        os.makedirs(os.path.dirname(DEFAULT_BENCHMARK_JSON), exist_ok=True)
        with open(DEFAULT_BENCHMARK_JSON, "w") as f:
            json.dump(output_payload, f, indent=2)
        print(f"[APEX Benchmark] Exported multi-circuit benchmark results to {DEFAULT_BENCHMARK_JSON}")

    return output_payload


def print_summary_table(summary_payload: Dict[str, Any]):
    """Prints a formatted ASCII evaluation matrix."""
    header = f"{'Policy':<18} | {'Avg Pos':<9} | {'Win %':<7} | {'Podium %':<9} | {'Avg Gap to P1':<14} | {'Blown Tyre Laps':<15} | {'Avg Pits':<8}"
    sep = "=" * len(header)
    print("\n" + sep)
    print(f"APEX MULTI-CIRCUIT STRATEGY EVALUATION BENCHMARK ({summary_payload.get('total_tracks', 5)} TRACKS)")
    print(sep)
    print(header)
    print("-" * len(header))
    for pol, stats in summary_payload.get("overall_summary", {}).items():
        name = pol.replace("_", " ").upper()
        print(f"{name:<18} | {stats['avg_position']:<9} | {stats['win_rate_pct']:<7}% | {stats['podium_rate_pct']:<9}% | +{stats['avg_gap_to_winner_s']:<13}s | {stats['avg_blown_tyre_laps']:<15} | {stats['avg_pit_stops']:<8}")
    print(sep + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run APEX Multi-Circuit Strategy Benchmarks")
    parser.add_argument("--races-per-track", type=int, default=5, help="Number of seeded races per track")
    args = parser.parse_args()

    results = run_multi_circuit_benchmark(races_per_track=args.races_per_track)
    print_summary_table(results)
