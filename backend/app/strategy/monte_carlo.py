"""Vectorized Stochastic Monte Carlo Decision Intelligence Engine.

Simulates hundreds to tens of thousands of stochastic futures evaluating 9 candidate tactical actions:
- PIT_NOW
- PIT_NEXT_LAP
- PIT_PLUS_2
- STAY_OUT
- PUSH
- NORMAL
- CONSERVE
- ATTACK
- DEFEND

Generates full outcome distributions, finish histograms, win/podium probabilities, DNF risk, and confidence intervals.
"""
from __future__ import annotations

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from backend.app.simulator.models import RaceState, StrategyAction, TyreCompound, DrivingMode
from backend.app.intelligence.tyre_model import TyreModel
from backend.app.intelligence.weather_model import WeatherPredictor

logger = logging.getLogger(__name__)

CANDIDATE_ACTIONS = [
    "PIT_NOW",
    "PIT_NEXT_LAP",
    "PIT_PLUS_2",
    "STAY_OUT",
    "PUSH",
    "NORMAL",
    "CONSERVE",
    "ATTACK",
    "DEFEND",
]


class MonteCarloEngine:
    """High-performance vectorized Monte Carlo decision evaluator."""

    @classmethod
    def evaluate_candidates(
        cls,
        state: RaceState,
        num_rollouts_per_action: int = 200,
        target_car_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs parallel vectorized rollouts across all 9 candidate strategic actions.
        """
        start_time = time.perf_counter()

        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0] if state.cars else None)
        if player is None:
            return {"error": "No target car available for Monte Carlo rollout"}

        laps_remaining = max(1, state.total_laps - state.current_lap)
        total_cars = len(state.cars)
        current_pos = player.position
        current_wear = player.tyre_wear_pct
        current_age = player.tyre_age_laps

        base_lap_time = getattr(state.track, "base_lap_time_s", 88.5) if hasattr(state, "track") and state.track else 88.5
        track_name = getattr(state.track, "name", "silverstone").lower()
        track_severity = TyreModel.get_circuit_degradation_factor(track_name)
        wetness = WeatherPredictor.calculate_track_wetness(state.weather)

        # Baseline pit loss parameters
        green_pit_loss = state.track.pit_lane_delta_s if hasattr(state.track, "pit_lane_delta_s") else 21.5
        sc_pit_loss = max(10.0, green_pit_loss - (state.track.sc_pit_advantage_s if hasattr(state.track, "sc_pit_advantage_s") else 12.0))
        vsc_pit_loss = max(12.0, green_pit_loss - (state.track.vsc_pit_advantage_s if hasattr(state.track, "vsc_pit_advantage_s") else 9.5))

        sc_status = str(state.safety_car.value if hasattr(state.safety_car, "value") else state.safety_car)
        is_sc = sc_status == "SAFETY_CAR"
        is_vsc = sc_status == "VSC"

        results: List[Dict[str, Any]] = []
        n_rollouts = max(1, num_rollouts_per_action)

        rng = np.random.default_rng(state.current_lap * 101 + current_pos * 17)

        for action_name in CANDIDATE_ACTIONS:
            # Configure strategic action parameters
            pace_bias = 0.0
            deg_multiplier = 1.0 * track_severity
            stops = 0
            immediate_pit_lap = None
            dnf_prob_base = 0.005

            if action_name == "PIT_NOW":
                stops = 1
                immediate_pit_lap = state.current_lap
                pace_bias = -0.55 # Fresh tyre advantage
                deg_multiplier = 0.85
            elif action_name == "PIT_NEXT_LAP":
                stops = 1
                immediate_pit_lap = state.current_lap + 1
                pace_bias = -0.45
            elif action_name == "PIT_PLUS_2":
                stops = 1
                immediate_pit_lap = state.current_lap + 2
                pace_bias = -0.35
            elif action_name == "STAY_OUT":
                stops = 0
                pace_bias = 0.05
                deg_multiplier = 1.15
            elif action_name == "PUSH":
                pace_bias = -0.40 # High pace gain
                deg_multiplier = 1.50 # Accelerated tyre degradation
                dnf_prob_base = 0.015
            elif action_name == "CONSERVE":
                pace_bias = 0.35 # Slower pace
                deg_multiplier = 0.65 # Preserves tyres
                dnf_prob_base = 0.002
            elif action_name == "ATTACK":
                pace_bias = -0.50
                deg_multiplier = 1.40
                dnf_prob_base = 0.020 # Collision risk during attack
            elif action_name == "DEFEND":
                pace_bias = 0.20
                deg_multiplier = 1.10
                dnf_prob_base = 0.008
            else: # NORMAL
                pace_bias = 0.0
                deg_multiplier = 1.0

            # Vectorized stochastic pace noise generation: shape (n_rollouts, laps_remaining)
            white_noise = rng.normal(0.0, 0.25, size=(n_rollouts, laps_remaining))
            pace_noise = np.zeros((n_rollouts, laps_remaining))
            pace_noise[:, 0] = white_noise[:, 0]
            for t in range(1, laps_remaining):
                pace_noise[:, t] = 0.65 * pace_noise[:, t - 1] + np.sqrt(1.0 - 0.65**2) * white_noise[:, t]

            # Vectorized cumulative pace delta
            lap_pace_deltas = pace_noise + (pace_bias * track_severity)

            # Tyre wear progression across rollout horizon
            accumulated_wear = current_wear
            if immediate_pit_lap is not None:
                accumulated_wear = 0.0 # Fresh set after pit
            
            wear_penalty_per_lap = np.clip((accumulated_wear - 60.0) * 0.04 * deg_multiplier, 0.0, 4.0)
            total_time_deltas = np.sum(lap_pace_deltas, axis=1) + (wear_penalty_per_lap * laps_remaining)

            # Pit stop time loss
            if stops > 0:
                effective_pit_loss = sc_pit_loss if is_sc else (vsc_pit_loss if is_vsc else green_pit_loss)
                total_time_deltas += effective_pit_loss

            # Stochastic DNF simulation
            dnf_mask = rng.uniform(0.0, 1.0, size=n_rollouts) < (dnf_prob_base * laps_remaining)
            
            # Position projection mapping (density ~3.5s/position)
            projected_positions = np.clip(current_pos + np.round(total_time_deltas / 3.5), 1, total_cars).astype(int)
            projected_positions[dnf_mask] = total_cars # DNFs placed last

            # Outcome distribution metrics
            wins = int(np.sum(projected_positions == 1))
            podiums = int(np.sum(projected_positions <= 3))
            p4_plus = int(np.sum(projected_positions >= 4))
            dnfs = int(np.sum(dnf_mask))

            win_prob = round(wins / n_rollouts, 3)
            podium_prob = round(podiums / n_rollouts, 3)
            p4_prob = round(p4_plus / n_rollouts, 3)
            dnf_prob = round(dnfs / n_rollouts, 3)
            exp_finish = round(float(np.mean(projected_positions[~dnf_mask])) if np.sum(~dnf_mask) > 0 else float(total_cars), 2)

            # Position distribution histogram (P1 through P10)
            pos_dist: Dict[str, int] = {}
            for p in range(1, min(11, total_cars + 1)):
                pos_dist[f"P{p}"] = int(np.sum(projected_positions == p))

            # Risk scores
            tyre_risk = round(float(np.clip((current_wear + 10.0 * deg_multiplier) / 100.0, 0.0, 1.0)), 2)
            weather_risk = round(float(np.clip(wetness * 1.2 if "PIT" not in action_name and wetness > 0.3 else 0.05, 0.0, 1.0)), 2)

            results.append({
                "action": action_name,
                "win_probability": win_prob,
                "podium_probability": podium_prob,
                "p4_plus_probability": p4_prob,
                "dnf_probability": dnf_prob,
                "expected_finish": exp_finish,
                "position_distribution": pos_dist,
                "pit_loss_s": round(green_pit_loss if stops > 0 else 0.0, 1),
                "tyre_risk": tyre_risk,
                "weather_risk": weather_risk,
                "confidence": round(max(0.60, 1.0 - (float(np.std(total_time_deltas)) / 15.0)), 2),
            })

        # Rank candidates: lowest expected finish, highest win probability
        results.sort(key=lambda r: (r["expected_finish"], -r["win_probability"]))

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "total_rollouts": n_rollouts * len(CANDIDATE_ACTIONS),
            "rollouts_per_action": n_rollouts,
            "elapsed_ms": elapsed_ms,
            "best_action": results[0]["action"],
            "best_expected_finish": results[0]["expected_finish"],
            "best_win_probability": results[0]["win_probability"],
            "candidates": results,
        }

    @classmethod
    def run_simulation(
        cls,
        state: RaceState,
        num_rollouts: int = 1000,
        target_car_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes stochastic forward simulations across candidate strategic profiles.
        Maintains backward compatibility with legacy 4-plan schema.
        """
        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0] if state.cars else None)
        if player is None:
            return {"error": "No car state available for Monte Carlo rollout"}

        laps_remaining = max(1, state.total_laps - state.current_lap)
        current_pos = player.position
        current_wear = player.tyre_wear_pct
        current_age = player.tyre_age_laps

        base_lap_time = getattr(state.track, "base_lap_time_s", 89.5) if hasattr(state, "track") and state.track else 89.5
        track_name = getattr(state.track, "track_id", "silverstone") if hasattr(state, "track") and state.track else "silverstone"
        track_severity = TyreModel.get_circuit_degradation_factor(track_name)

        green_pit_loss = 21.5
        sc_pit_loss = 14.0
        vsc_pit_loss = 12.0

        strategies = [
            {
                "id": "plan_a_med_hard",
                "name": "Plan A: Medium -> Hard (1-Stop)",
                "pit_lap": min(state.total_laps, state.current_lap + max(3, int(24 / track_severity) - current_age)),
                "compound": "HARD",
                "stops": 1,
                "pace_bias": 0.0,
                "deg_factor": 1.0 * track_severity,
            },
            {
                "id": "plan_b_soft_med",
                "name": "Plan B: Soft -> Medium -> Soft (2-Stop)",
                "pit_lap": min(state.total_laps, state.current_lap + max(2, int(14 / track_severity) - current_age)),
                "compound": "MEDIUM",
                "stops": 2,
                "pace_bias": -0.42,
                "deg_factor": 1.35 * track_severity,
            },
            {
                "id": "plan_c_hard_one_stop",
                "name": "Plan C: Overcut Hard Extended",
                "pit_lap": min(state.total_laps, state.current_lap + max(5, int(32 / track_severity) - current_age)),
                "compound": "HARD",
                "stops": 1,
                "pace_bias": 0.18,
                "deg_factor": 0.85 * track_severity,
            },
            {
                "id": "plan_d_aggressive_push",
                "name": "Plan D: Maximum Attack 2-Stop Softs",
                "pit_lap": min(state.total_laps, state.current_lap + max(2, int(11 / track_severity) - current_age)),
                "compound": "SOFT",
                "stops": 2,
                "pace_bias": -0.70,
                "deg_factor": 1.65 * track_severity,
            },
        ]

        rollouts_per_strategy = max(1, num_rollouts // len(strategies))
        results: List[Dict[str, Any]] = []

        np.random.seed(state.current_lap * 37 + player.position + 13)

        for strat in strategies:
            finishing_positions = []
            race_times = []
            pit_window_sc_advantages = []
            pace_bias = float(strat["pace_bias"])
            stops = int(strat["stops"])
            pit_lap = int(strat["pit_lap"])
            deg_factor = float(strat["deg_factor"])

            for _ in range(rollouts_per_strategy):
                white_noise = np.random.normal(0.0, 0.28, size=laps_remaining)
                pace_noise = np.zeros(laps_remaining)
                pace_noise[0] = white_noise[0]
                for t in range(1, laps_remaining):
                    pace_noise[t] = 0.65 * pace_noise[t - 1] + np.sqrt(1.0 - 0.65**2) * white_noise[t]

                sc_prob = np.random.uniform(0.0, 1.0)
                sc_occurred = sc_prob < 0.22
                vsc_occurred = not sc_occurred and sc_prob < 0.35

                total_delta = float(np.sum(pace_noise)) + (pace_bias * laps_remaining)

                if sc_occurred:
                    effective_pit_loss = sc_pit_loss
                    pit_window_sc_advantages.append(True)
                elif vsc_occurred:
                    effective_pit_loss = vsc_pit_loss
                    pit_window_sc_advantages.append(True)
                else:
                    effective_pit_loss = green_pit_loss
                    pit_window_sc_advantages.append(False)

                total_delta += stops * effective_pit_loss

                wear_penalty = 0.0
                stint_length = max(1, pit_lap - state.current_lap)
                if current_wear > 65.0 and stint_length > 4:
                    wear_penalty += (current_wear - 65.0) * 0.25 * deg_factor

                total_delta += wear_penalty
                simulated_time = (laps_remaining * base_lap_time) + total_delta
                race_times.append(simulated_time)

                pos_delta = int(np.round(total_delta / 3.8))
                sim_pos = max(1, min(len(state.cars), current_pos + pos_delta))
                finishing_positions.append(sim_pos)

            finishing_positions_arr = np.array(finishing_positions)
            race_times_arr = np.array(race_times)

            p1_count = int(np.sum(finishing_positions_arr == 1))
            podium_count = int(np.sum(finishing_positions_arr <= 3))
            p_points = int(np.sum(finishing_positions_arr <= 10))

            results.append({
                "strategy_id": str(strat["id"]),
                "strategy_name": str(strat["name"]),
                "optimal_pit_lap": pit_lap,
                "target_compound": str(strat["compound"]),
                "stops": stops,
                "win_probability_pct": round((p1_count / rollouts_per_strategy) * 100.0, 1),
                "podium_probability_pct": round((podium_count / rollouts_per_strategy) * 100.0, 1),
                "points_probability_pct": round((p_points / rollouts_per_strategy) * 100.0, 1),
                "expected_finish_pos": round(float(np.mean(finishing_positions_arr)), 2),
                "best_case_pos": int(np.min(finishing_positions_arr)),
                "worst_case_pos": int(np.max(finishing_positions_arr)),
                "expected_race_time_s": round(float(np.mean(race_times_arr)), 2),
                "variance_s": round(float(np.std(race_times_arr)), 2),
                "p95_var_time_s": round(float(np.percentile(race_times_arr, 95)), 2),
                "safety_car_upside_pct": round(float(np.mean(pit_window_sc_advantages)) * 100.0, 1),
                "rollouts": rollouts_per_strategy,
            })

        results.sort(key=lambda s: (-s["win_probability_pct"], s["expected_finish_pos"]))
        recommended = results[0]

        return {
            "total_rollouts": num_rollouts,
            "current_lap": state.current_lap,
            "laps_remaining": laps_remaining,
            "target_car_id": player.car_id,
            "track_id": track_name,
            "track_severity_multiplier": track_severity,
            "recommended_strategy": recommended["strategy_name"],
            "recommended_pit_lap": recommended["optimal_pit_lap"],
            "confidence_pct": recommended["win_probability_pct"],
            "strategies": results,
        }
