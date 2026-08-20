"""Lightweight counterfactual forward-rollout comparator and timeline forking engine.

Provides deterministic timeline forking, multi-lap scenario projection, undercut/overcut
threat analysis, and delta-T advantage calculations across strategic action candidates.
"""
from typing import Any, TypedDict

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import RaceState, StrategyAction


class CandidateOption(TypedDict):
    name: str
    action: StrategyAction


class CounterfactualChecker:
    """Simulates multiple candidate strategies forward N laps to compare expected outcomes."""

    @classmethod
    def evaluate_alternatives(
        cls,
        sim: RaceSimulator,
        rollout_laps: int = 4,
    ) -> dict[str, Any]:
        """
        Executes fast forward rollouts of candidate actions and compares projected positions and times.
        """
        candidates: list[CandidateOption] = [
            {"name": "Maintain Current Stint", "action": StrategyAction.MAINTAIN},
            {"name": "Box Now (Hard Tyres)", "action": StrategyAction.PIT_HARD},
            {"name": "Box Now (Medium Tyres)", "action": StrategyAction.PIT_MEDIUM},
            {"name": "Switch to PUSH Pace", "action": StrategyAction.PUSH},
            {"name": "Switch to CONSERVE Mode", "action": StrategyAction.CONSERVE},
        ]

        results = []
        for cand in candidates:
            sim_clone = sim.clone()
            sim_clone.step(player_action=cand["action"])

            for _ in range(rollout_laps - 1):
                if sim_clone.is_finished:
                    break
                sim_clone.step(player_action=StrategyAction.MAINTAIN)

            clone_player = sim_clone.get_player_car()

            # Estimate tyre cliff risk probability
            cliff_risk_pct = 95.0 if clone_player.tyre_cliff_reached else min(100.0, max(0.0, (clone_player.tyre_wear_pct - 50.0) * 2.5))

            results.append({
                "strategy": cand["name"],
                "action": cand["action"].value,
                "projected_position": clone_player.position,
                "projected_gap_to_leader": round(clone_player.gap_to_leader_s, 2),
                "projected_tyre_wear_pct": round(clone_player.tyre_wear_pct, 1),
                "projected_compound": clone_player.tyre_compound.value,
                "cliff_reached": clone_player.tyre_cliff_reached,
                "cliff_risk_pct": round(float(cliff_risk_pct), 1),
            })

        # Rank by finishing position ascending, tie-break by gap to leader
        results.sort(key=lambda r: (r["projected_position"], r["projected_gap_to_leader"]))

        best_option = results[0]
        return {
            "rollout_laps": rollout_laps,
            "best_strategy": best_option["strategy"],
            "best_action": best_option["action"],
            "alternatives": results,
        }

    @classmethod
    def fork_timeline(
        cls,
        historical_state: RaceState,
        proposed_action: str | StrategyAction,
        rollout_laps: int = 5,
    ) -> dict[str, Any]:
        """
        Forks from a historical state and compares forward timeline under proposed action vs baseline.
        """
        if isinstance(proposed_action, str):
            try:
                action_enum = StrategyAction(proposed_action.upper().replace("STRATEGYACTION.", ""))
            except ValueError:
                action_enum = StrategyAction.MAINTAIN
        else:
            action_enum = proposed_action

        # Base simulator (maintaining)
        base_sim = RaceSimulator.from_state(historical_state)
        base_trajectory = []
        for _ in range(rollout_laps):
            if base_sim.is_finished:
                break
            base_sim.step(player_action=StrategyAction.MAINTAIN)
            p = base_sim.get_player_car()
            base_trajectory.append({
                "lap": base_sim.current_lap,
                "position": p.position,
                "gap_to_leader_s": round(p.gap_to_leader_s, 2),
                "tyre_wear_pct": round(p.tyre_wear_pct, 1),
                "tyre_compound": p.tyre_compound.value,
                "cliff_reached": p.tyre_cliff_reached,
            })

        # Alternate simulator (proposed action on first lap, then maintain)
        alt_sim = RaceSimulator.from_state(historical_state)
        alt_trajectory = []
        alt_sim.step(player_action=action_enum)
        p_alt = alt_sim.get_player_car()
        alt_trajectory.append({
            "lap": alt_sim.current_lap,
            "position": p_alt.position,
            "gap_to_leader_s": round(p_alt.gap_to_leader_s, 2),
            "tyre_wear_pct": round(p_alt.tyre_wear_pct, 1),
            "tyre_compound": p_alt.tyre_compound.value,
            "cliff_reached": p_alt.tyre_cliff_reached,
        })

        for _ in range(rollout_laps - 1):
            if alt_sim.is_finished:
                break
            alt_sim.step(player_action=StrategyAction.MAINTAIN)
            p_alt = alt_sim.get_player_car()
            alt_trajectory.append({
                "lap": alt_sim.current_lap,
                "position": p_alt.position,
                "gap_to_leader_s": round(p_alt.gap_to_leader_s, 2),
                "tyre_wear_pct": round(p_alt.tyre_wear_pct, 1),
                "tyre_compound": p_alt.tyre_compound.value,
                "cliff_reached": p_alt.tyre_cliff_reached,
            })

        final_base = base_trajectory[-1] if base_trajectory else {}
        final_alt = alt_trajectory[-1] if alt_trajectory else {}

        time_delta_advantage = round(
            final_base.get("gap_to_leader_s", 0.0) - final_alt.get("gap_to_leader_s", 0.0), 2
        )
        pos_advantage = final_base.get("position", 1) - final_alt.get("position", 1)

        verdict = "FAVORS_PROPOSED" if (pos_advantage > 0 or (pos_advantage == 0 and time_delta_advantage > 0)) else "FAVORS_BASELINE"

        # Calculate undercut threat success probability if pitting
        is_pit_action = "PIT" in action_enum.value
        undercut_probability_pct = 0.0
        if is_pit_action:
            fresh_tyre_delta = 1.25  # seconds faster on fresh rubber
            gap_ahead = float(historical_state.cars[0].gap_to_car_ahead_s) if historical_state.cars else 2.5
            undercut_probability_pct = min(100.0, max(10.0, round((fresh_tyre_delta * rollout_laps / max(1.0, gap_ahead)) * 50.0, 1)))

        return {
            "historical_lap": historical_state.current_lap,
            "proposed_action": action_enum.value,
            "rollout_laps": rollout_laps,
            "verdict": verdict,
            "time_delta_advantage_s": time_delta_advantage,
            "positions_gained": pos_advantage,
            "undercut_success_probability_pct": undercut_probability_pct,
            "final_alternate_position": final_alt.get("position", 1),
            "final_baseline_position": final_base.get("position", 1),
            "alternate_timeline": alt_trajectory,
            "baseline_timeline": base_trajectory,
        }
