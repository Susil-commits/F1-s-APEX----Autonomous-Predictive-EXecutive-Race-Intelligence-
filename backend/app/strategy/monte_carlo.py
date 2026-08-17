"""Backend Stochastic 1,000-Rollout Monte Carlo Strategy Engine."""
from typing import Dict, List, Any, Optional
import numpy as np

from backend.app.simulator.models import RaceState


class MonteCarloEngine:
    """Performs parallel forward stochastic simulations with pace and safety car uncertainty."""

    @staticmethod
    def run_simulation(
        state: RaceState,
        num_rollouts: int = 1000,
        target_car_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes stochastic forward simulations across candidate strategic profiles.
        """
        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0])
        laps_remaining = max(1, state.total_laps - state.current_lap)
        current_pos = player.position
        current_wear = player.tyre_wear_pct

        # Strategy candidates to compare
        strategies = [
            {"id": "plan_a_med_hard", "name": "Plan A: Medium -> Hard (1-Stop)", "pit_lap": min(state.total_laps, state.current_lap + max(3, 24 - player.tyre_age_laps)), "compound": "HARD", "pace_bias": 0.0},
            {"id": "plan_b_soft_med", "name": "Plan B: Soft -> Medium -> Soft (2-Stop)", "pit_lap": min(state.total_laps, state.current_lap + max(2, 14 - player.tyre_age_laps)), "compound": "MEDIUM", "pace_bias": -0.35},
            {"id": "plan_c_hard_one_stop", "name": "Plan C: Overcut Hard Extended", "pit_lap": min(state.total_laps, state.current_lap + max(5, 32 - player.tyre_age_laps)), "compound": "HARD", "pace_bias": 0.15},
            {"id": "plan_d_aggressive_push", "name": "Plan D: Maximum Attack 2-Stop Softs", "pit_lap": min(state.total_laps, state.current_lap + max(2, 11 - player.tyre_age_laps)), "compound": "SOFT", "pace_bias": -0.65},
        ]

        rollouts_per_strategy = max(100, num_rollouts // len(strategies))
        results: List[Dict[str, Any]] = []

        np.random.seed(state.current_lap * 37 + player.position)

        for strat in strategies:
            finishing_positions = []
            race_times = []
            
            base_lap_time = 89.5  # Approximate silverstone average
            pit_stop_loss = 21.0  # seconds
            
            for _ in range(rollouts_per_strategy):
                # Stochastic variables
                driver_pace_noise = np.random.normal(0.0, 0.38, size=laps_remaining)
                sc_prob = np.random.uniform(0.0, 1.0)
                sc_occurred = sc_prob < 0.22  # 22% historical safety car probability
                
                # Calculate simulated race time delta
                total_delta = np.sum(driver_pace_noise) + (strat["pace_bias"] * laps_remaining)
                
                # Add pit stop time
                stops = 2 if "2-Stop" in strat["name"] else 1
                if sc_occurred:
                    total_delta += stops * (pit_stop_loss * 0.6)  # Cheap safety car pit advantage
                else:
                    total_delta += stops * pit_stop_loss

                # Tyre degradation model
                if current_wear > 60.0 and strat["pit_lap"] > state.current_lap + 6:
                    total_delta += 8.5  # Blown tyre cliff delay

                simulated_time = (laps_remaining * base_lap_time) + total_delta
                race_times.append(simulated_time)

                # Stochastic finishing position estimation based on relative pace
                pos_delta = int(np.round(total_delta / 4.2))
                sim_pos = max(1, min(len(state.cars), current_pos + pos_delta))
                finishing_positions.append(sim_pos)

            finishing_positions = np.array(finishing_positions)
            race_times = np.array(race_times)

            p1_count = np.sum(finishing_positions == 1)
            podium_count = np.sum(finishing_positions <= 3)
            p_points = np.sum(finishing_positions <= 10)

            results.append({
                "strategy_id": strat["id"],
                "strategy_name": strat["name"],
                "optimal_pit_lap": strat["pit_lap"],
                "target_compound": strat["compound"],
                "win_probability_pct": round(float(p1_count / rollouts_per_strategy) * 100.0, 1),
                "podium_probability_pct": round(float(podium_count / rollouts_per_strategy) * 100.0, 1),
                "points_probability_pct": round(float(p_points / rollouts_per_strategy) * 100.0, 1),
                "expected_finish_pos": round(float(np.mean(finishing_positions)), 2),
                "best_case_pos": int(np.min(finishing_positions)),
                "worst_case_pos": int(np.max(finishing_positions)),
                "expected_race_time_s": round(float(np.mean(race_times)), 2),
                "variance_s": round(float(np.std(race_times)), 2),
                "rollouts": rollouts_per_strategy,
            })

        # Sort strategies by win probability descending
        results.sort(key=lambda s: s["win_probability_pct"], reverse=True)
        recommended = results[0]

        return {
            "total_rollouts": num_rollouts,
            "current_lap": state.current_lap,
            "laps_remaining": laps_remaining,
            "target_car_id": player.car_id,
            "recommended_strategy": recommended["strategy_name"],
            "recommended_pit_lap": recommended["optimal_pit_lap"],
            "confidence_pct": recommended["win_probability_pct"],
            "strategies": results,
        }
