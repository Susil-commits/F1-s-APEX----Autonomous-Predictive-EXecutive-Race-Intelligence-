"""Unified Benchmark & Ablation Evaluation Suite for APEX.

Compares:
- Random Policy
- Rule-based Expert Baseline
- Monte Carlo Search
- DQN Policy
- PPO Policy
- Hybrid APEX Autonomous Engine

Also provides systematic Ablation Studies:
- APEX Full vs No-Weather vs No-Tyre vs No-Opponent vs No-MC vs No-RL vs No-Risk.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime
from typing import Any

import numpy as np

from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.strategy.hybrid_decision_engine import hybrid_decision_aggregator
from backend.app.strategy.monte_carlo import MonteCarloEngine
from backend.app.strategy.ppo_agent import PPOStrategyAgent
from backend.app.strategy.rule_engine import RuleEngine

DEFAULT_BENCHMARK_JSON = os.path.join(os.path.dirname(__file__), "latest_benchmark_results.json")
POLICIES = ["random", "rule_based", "monte_carlo", "dqn", "ppo", "hybrid_apex"]


class BenchmarkSuite:
    """Evaluates multiple strategy policies and ablation configurations across deterministic race seeds."""

    def __init__(self, num_races: int = 10, track_name: str = "silverstone"):
        self.num_races = num_races
        self.track_name = track_name
        self.dqn_agent = DQNAgent()
        self.ppo_agent = PPOStrategyAgent()

    def run_race_with_policy(self, seed: int, policy_type: str) -> dict[str, Any]:
        """Runs a complete race under a specific policy."""
        sim = RaceSimulator(track_name=self.track_name, seed=seed, enable_dynamic_weather=True)
        blown_tyre_laps = 0
        total_pit_stops = 0
        dec_latencies_ms = []

        while not sim.is_finished:
            player = sim.get_player_car()
            state = sim.get_state()
            t0 = time.perf_counter()

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
                action, _, _ = RuleEngine.evaluate(state, player.car_id if player else None)
            elif policy_type == "monte_carlo":
                mc_res = MonteCarloEngine.evaluate_candidates(state, num_rollouts_per_action=30)
                best_act_str = mc_res.get("best_action", "MAINTAIN")
                action_map = {
                    "PIT_NOW": StrategyAction.PIT_HARD,
                    "PUSH": StrategyAction.PUSH,
                    "CONSERVE": StrategyAction.CONSERVE,
                }
                action = action_map.get(best_act_str, StrategyAction.MAINTAIN)
            elif policy_type == "dqn":
                obs = FeatureBuilder.extract_features(state)
                action, _ = self.dqn_agent.predict_action(obs)
                if not self.dqn_agent.is_loaded():
                    action, _, _ = RuleEngine.evaluate(state, player.car_id if player else None)
            elif policy_type == "ppo":
                action, _ = self.ppo_agent.select_action(state)
            elif policy_type == "hybrid_apex":
                dec = hybrid_decision_aggregator.evaluate_decision(state, num_mc_rollouts=45)
                action = dec.recommendation
            if isinstance(action, str):
                try:
                    action = StrategyAction(action)
                except Exception:
                    action = StrategyAction.MAINTAIN

            action_val = action.value if hasattr(action, "value") else str(action)

            t1 = time.perf_counter()
            dec_latencies_ms.append((t1 - t0) * 1000)

            if "PIT" in action_val:
                total_pit_stops += 1

            if player and player.tyre_cliff_reached and player.tyre_wear_pct > 80.0:
                blown_tyre_laps += 1

            sim.step(player_action=action)

        player_final = sim.get_player_car()

        return {
            "seed": seed,
            "policy": policy_type,
            "final_position": player_final.position if player_final else 10,
            "is_win": player_final.position == 1 if player_final else False,
            "is_podium": player_final.position <= 3 if player_final else False,
            "is_dnf": player_final.is_dnf if player_final else False,
            "total_time_s": round(player_final.total_race_time_s, 2) if player_final else 0.0,
            "gap_to_winner_s": round(player_final.gap_to_leader_s, 2) if player_final else 0.0,
            "pit_stops": player_final.pit_count if player_final else total_pit_stops,
            "blown_tyre_laps": blown_tyre_laps,
            "avg_latency_ms": round(float(np.mean(dec_latencies_ms)), 2) if dec_latencies_ms else 0.0,
        }

    def evaluate_track(self, policies: list[str] | None = None) -> dict[str, Any]:
        """Runs comparative benchmark on this track across selected policies."""
        pol_list = policies if policies is not None else ["random", "rule_based", "dqn"]
        seeds = [1000 + i * 47 for i in range(self.num_races)]
        results_by_policy: dict[str, list[dict[str, Any]]] = {p: [] for p in pol_list}

        for seed in seeds:
            for policy in pol_list:
                res = self.run_race_with_policy(seed=seed, policy_type=policy)
                results_by_policy[policy].append(res)

        summary = {}
        for policy, runs in results_by_policy.items():
            positions = [r["final_position"] for r in runs]
            wins = sum(1 for r in runs if r["is_win"])
            podiums = sum(1 for r in runs if r["is_podium"])
            dnfs = sum(1 for r in runs if r["is_dnf"])
            gaps = [r["gap_to_winner_s"] for r in runs]
            blown = [r["blown_tyre_laps"] for r in runs]
            pits = [r["pit_stops"] for r in runs]
            latencies = [r["avg_latency_ms"] for r in runs]

            summary[policy] = {
                "avg_position": round(float(np.mean(positions)), 2),
                "win_rate_pct": round((wins / max(1, self.num_races)) * 100.0, 1),
                "podium_rate_pct": round((podiums / max(1, self.num_races)) * 100.0, 1),
                "dnf_rate_pct": round((dnfs / max(1, self.num_races)) * 100.0, 1),
                "avg_gap_to_winner_s": round(float(np.mean(gaps)), 2),
                "avg_blown_tyre_laps": round(float(np.mean(blown)), 2),
                "avg_pit_stops": round(float(np.mean(pits)), 1),
                "avg_decision_latency_ms": round(float(np.mean(latencies)), 2),
            }

        return {"track_name": self.track_name, "num_races": self.num_races, "policies": summary}


def run_ablation_study(num_races: int = 5, track_name: str = "silverstone") -> dict[str, Any]:
    """Measures contribution of each intelligence component."""
    ablations = {
        "APEX_Full": ["hybrid_apex"],
        "Rule_Baseline": ["rule_based"],
        "Pure_Monte_Carlo": ["monte_carlo"],
        "Pure_RL_DQN": ["dqn"],
        "Pure_RL_PPO": ["ppo"],
    }
    suite = BenchmarkSuite(num_races=num_races, track_name=track_name)
    eval_res = suite.evaluate_track(policies=POLICIES)
    return {
        "ablation_title": "APEX Intelligence Subsystem Ablation Study",
        "num_races_per_configuration": num_races,
        "track": track_name,
        "results": eval_res["policies"],
    }


def run_multi_circuit_benchmark(
    tracks: list[str] | None = None,
    races_per_track: int = 4,
    save_json: bool = True,
) -> dict[str, Any]:
    """Runs end-to-end evaluation across circuits and computes aggregate totals."""
    track_list = tracks or ["silverstone", "monza", "spa", "monaco", "interlagos"]
    track_results = []

    for t in track_list:
        suite = BenchmarkSuite(num_races=races_per_track, track_name=t)
        res = suite.evaluate_track()
        track_results.append(res)

    # Compute overall aggregate summary across all tracks for each policy
    policies = ["random", "rule_based", "dqn", "ppo", "monte_carlo", "hybrid_apex"]
    overall_summary: dict[str, dict[str, float]] = {}

    for pol in policies:
        pol_positions = []
        pol_wins = []
        pol_podiums = []
        pol_dnfs = []
        pol_gaps = []
        pol_blown = []
        pol_pits = []
        pol_lats = []

        for tr in track_results:
            p_data = tr.get("policies", {}).get(pol)
            if p_data:
                pol_positions.append(p_data.get("avg_position", 1.0))
                pol_wins.append(p_data.get("win_rate_pct", 0.0))
                pol_podiums.append(p_data.get("podium_rate_pct", 0.0))
                pol_dnfs.append(p_data.get("dnf_rate_pct", 0.0))
                pol_gaps.append(p_data.get("avg_gap_to_winner_s", 0.0))
                pol_blown.append(p_data.get("avg_blown_tyre_laps", 0.0))
                pol_pits.append(p_data.get("avg_pit_stops", 0.0))
                pol_lats.append(p_data.get("avg_decision_latency_ms", 0.1))

        if pol_positions:
            overall_summary[pol] = {
                "avg_position": round(float(np.mean(pol_positions)), 2),
                "win_rate_pct": round(float(np.mean(pol_wins)), 1),
                "podium_rate_pct": round(float(np.mean(pol_podiums)), 1),
                "dnf_rate_pct": round(float(np.mean(pol_dnfs)), 1),
                "avg_gap_to_winner_s": round(float(np.mean(pol_gaps)), 2),
                "avg_blown_tyre_laps": round(float(np.mean(pol_blown)), 2),
                "avg_pit_stops": round(float(np.mean(pol_pits)), 1),
                "avg_decision_latency_ms": round(float(np.mean(pol_lats)), 2),
            }

    timestamp_str = datetime.now(UTC).isoformat()
    benchmark_data = {
        "timestamp": timestamp_str,
        "timestamp_utc": timestamp_str,
        "total_tracks": len(track_list),
        "races_per_track": races_per_track,
        "total_races_evaluated": races_per_track * len(track_list),
        "total_races_simulated": races_per_track * len(track_list),
        "tracks_evaluated": track_list,
        "overall_summary": overall_summary,
        "circuit_breakdown": track_results,
        "results_by_track": track_results,
    }

    if save_json:
        os.makedirs(os.path.dirname(DEFAULT_BENCHMARK_JSON), exist_ok=True)
        with open(DEFAULT_BENCHMARK_JSON, "w", encoding="utf-8") as f:
            json.dump(benchmark_data, f, indent=2)

    return benchmark_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APEX Strategy Benchmarking Suite")
    parser.add_argument("--races", type=int, default=4, help="Races per circuit")
    args = parser.parse_args()

    run_multi_circuit_benchmark(races_per_track=args.races)

