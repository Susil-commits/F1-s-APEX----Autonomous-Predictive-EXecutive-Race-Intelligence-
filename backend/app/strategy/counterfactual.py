"""Lightweight counterfactual forward-rollout comparator."""
from typing import Dict, List, Any
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TyreCompound


class CounterfactualChecker:
    """Simulates multiple candidate strategies forward N laps to compare expected outcomes."""

    @classmethod
    def evaluate_alternatives(
        cls,
        sim: RaceSimulator,
        rollout_laps: int = 4,
    ) -> Dict[str, Any]:
        """
        Executes fast forward rollouts of candidate actions and compares projected positions and times.
        """
        player = sim.get_player_car()
        candidates = [
            {"name": "Maintain Current Stint", "action": StrategyAction.MAINTAIN},
            {"name": "Box Now (Hard Tyres)", "action": StrategyAction.PIT_HARD},
            {"name": "Box Now (Medium Tyres)", "action": StrategyAction.PIT_MEDIUM},
            {"name": "Switch to PUSH Pace", "action": StrategyAction.PUSH},
            {"name": "Switch to CONSERVE Mode", "action": StrategyAction.CONSERVE},
        ]

        results = []
        for cand in candidates:
            # Deep clone the current state
            sim_clone = sim.clone()
            
            # Apply initial candidate action
            sim_clone.step(player_action=cand["action"])

            # Roll forward for remaining laps in rollout window
            for _ in range(rollout_laps - 1):
                if sim_clone.is_finished:
                    break
                sim_clone.step(player_action=StrategyAction.MAINTAIN)

            clone_player = sim_clone.get_player_car()
            results.append({
                "strategy": cand["name"],
                "action": cand["action"].value,
                "projected_position": clone_player.position,
                "projected_gap_to_leader": round(clone_player.gap_to_leader_s, 2),
                "projected_tyre_wear_pct": round(clone_player.tyre_wear_pct, 1),
                "projected_compound": clone_player.tyre_compound.value,
                "cliff_reached": clone_player.tyre_cliff_reached,
            })

        # Sort results: best position first, then lowest gap
        results.sort(key=lambda r: (r["projected_position"], r["projected_gap_to_leader"]))

        best_option = results[0]
        return {
            "rollout_laps": rollout_laps,
            "best_strategy": best_option["strategy"],
            "best_action": best_option["action"],
            "alternatives": results,
        }
