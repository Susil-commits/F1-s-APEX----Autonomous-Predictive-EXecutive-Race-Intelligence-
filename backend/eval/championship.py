"""AI-vs-AI Championship Tournament Engine: Simulates multi-race championships between 8 diverse AI strategy archetypes.

Spec reference: APEX_MASTER_ENGINEERING_SPEC.md §30 (Gate F)
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from backend.app.intelligence.risk_engine import RiskEngine
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import SafetyCarStatus, StrategyAction, TrackCondition, TyreCompound
from backend.app.strategy.hybrid_decision_engine import hybrid_decision_aggregator
from backend.app.strategy.monte_carlo import MonteCarloEngine
from backend.app.strategy.ppo_agent import PPOStrategyAgent
from backend.app.strategy.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

POINTS_SYSTEM = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]  # F1 Official Points


class TeamStanding(BaseModel):
    team_name: str
    archetype: str
    points: int = 0
    wins: int = 0
    podiums: int = 0
    top5s: int = 0
    dnfs: int = 0
    races_run: int = 0
    avg_finish: float = 0.0
    strategy_distribution: dict[str, int] = Field(default_factory=dict)


class ChampionshipSimulator:
    """Simulates 100+ race AI tournaments across multiple Grand Prix circuits."""

    TRACKS = ["silverstone", "monza", "spa", "monaco", "interlagos", "bahrain", "austria"]

    AI_TEAMS = [
        {"name": "Team Alpha (Aggressive)", "archetype": "Aggressive Attack", "car_id": "car_01"},
        {"name": "Team Beta (Conservative)", "archetype": "Conservative Safe", "car_id": "car_02"},
        {"name": "Team Gamma (Tyre-Focused)", "archetype": "Tyre Preserver", "car_id": "car_03"},
        {"name": "Team Delta (Risk-Aware)", "archetype": "Risk Defensive", "car_id": "car_05"},
        {"name": "Team APEX (Hybrid AI)", "archetype": "Autonomous Decision Intelligence", "car_id": "car_04"},
    ]

    EXPANDED_AI_TEAMS = [
        {"name": "Team APEX (Hybrid AI)", "archetype": "Autonomous Hybrid Intelligence", "car_id": "car_04"},
        {"name": "Team Alpha (Aggressive)", "archetype": "Aggressive Attack", "car_id": "car_01"},
        {"name": "Team Beta (Conservative)", "archetype": "Conservative Safe", "car_id": "car_02"},
        {"name": "Team Gamma (Tyre-Focused)", "archetype": "Tyre Preserver", "car_id": "car_03"},
        {"name": "Team Delta (Risk-Aware)", "archetype": "Risk Defensive", "car_id": "car_05"},
        {"name": "Team Epsilon (PPO Policy)", "archetype": "Neural RL Policy", "car_id": "car_06"},
        {"name": "Team Zeta (Rule-Only)", "archetype": "Expert System Baseline", "car_id": "car_07"},
        {"name": "Team Theta (Greedy MC)", "archetype": "Monte Carlo Rollout Optimizer", "car_id": "car_08"},
    ]

    @classmethod
    def run_championship(
        cls,
        total_races: int = 100,
        seed: int = 42,
        teams: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Executes N championship rounds, tracking standings and points progression."""
        rng = np.random.default_rng(seed)
        ppo_agent = PPOStrategyAgent()
        active_teams = teams or cls.AI_TEAMS


        standings: dict[str, TeamStanding] = {
            t["name"]: TeamStanding(team_name=t["name"], archetype=t["archetype"]) for t in active_teams
        }
        all_finishes: dict[str, list[int]] = {t["name"]: [] for t in active_teams}

        for r_i in range(total_races):
            track_name = cls.TRACKS[r_i % len(cls.TRACKS)]
            race_seed = seed + r_i * 79
            sim = RaceSimulator(track_name=track_name, seed=race_seed, grid_size=10, enable_dynamic_weather=True)

            while not sim.is_finished:
                state = sim.get_state()

                # Dispatch strategic decisions per team archetype
                for team in active_teams:
                    car_id = team["car_id"]
                    car = next((c for c in sim.cars if c.car_id == car_id or (car_id == "car_04" and c.is_player)), None)
                    if car is None or car.is_dnf:
                        continue

                    # Decision frequency
                    if sim.current_lap % 2 == 0 or state.safety_car != SafetyCarStatus.NONE or state.weather.condition != TrackCondition.DRY:
                        action = cls._evaluate_team_action(team["name"], state, car.car_id, ppo_agent)
                        sim.apply_action(action, target_car_id=car.car_id)

                sim.step()

            # Record race finish results
            final_cars = sim.cars
            for t in active_teams:
                car = next((c for c in final_cars if c.car_id == t["car_id"] or (t["car_id"] == "car_04" and c.is_player)), None)
                if car:
                    pos = car.position
                    st = standings[t["name"]]
                    st.races_run += 1
                    all_finishes[t["name"]].append(pos)

                    if pos <= len(POINTS_SYSTEM):
                        st.points += POINTS_SYSTEM[pos - 1]

                    if pos == 1:
                        st.wins += 1
                    if pos <= 3:
                        st.podiums += 1
                    if pos <= 5:
                        st.top5s += 1
                    if car.is_dnf:
                        st.dnfs += 1

        # Calculate average finishes
        leaderboard: list[TeamStanding] = []
        for t_name, st in standings.items():
            fin_list = all_finishes[t_name]
            st.avg_finish = round(float(np.mean(fin_list)) if fin_list else 10.0, 2)
            leaderboard.append(st)

        # Sort leaderboard by points descending, tie-break by wins
        leaderboard.sort(key=lambda s: (-s.points, -s.wins, s.avg_finish))

        return {
            "total_races": total_races,
            "seed": seed,
            "champion": leaderboard[0].team_name,
            "leaderboard": [l.model_dump() for l in leaderboard],
        }

    @classmethod
    def _evaluate_team_action(
        cls,
        team_name: str,
        state: RaceState,
        car_id: str,
        ppo_agent: PPOStrategyAgent,
    ) -> StrategyAction:
        """Evaluates archetype-specific strategy for a given team."""
        car = next((c for c in state.cars if c.car_id == car_id or (car_id == "car_04" and c.is_player)), None)
        if car is None:
            return StrategyAction.MAINTAIN

        is_wet = state.weather.condition == TrackCondition.WET or state.weather.rain_intensity > 0.40
        is_damp = state.weather.condition == TrackCondition.DAMP or (0.10 <= state.weather.rain_intensity <= 0.40)
        is_slick = car.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)

        # Universal weather safety
        if is_wet and is_slick:
            return StrategyAction.PIT_WET
        if is_damp and is_slick:
            return StrategyAction.PIT_INTER

        if "APEX" in team_name:
            dec = hybrid_decision_aggregator.evaluate_decision(state, target_car_id=car_id, num_mc_rollouts=40)
            return dec.recommendation

        elif "PPO" in team_name:
            action, _ = ppo_agent.select_action(state, deterministic=True)
            return action

        elif "Rule-Only" in team_name or "Zeta" in team_name:
            res = RuleEngine.evaluate(state, target_car_id=car_id)
            return res[0] if isinstance(res, tuple) else getattr(res, "recommendation", StrategyAction.MAINTAIN)

        elif "Greedy MC" in team_name or "Theta" in team_name:
            try:
                mc_res = MonteCarloEngine.evaluate_candidates(state, num_rollouts_per_action=100, target_car_id=car_id)
                top_act = mc_res.get("recommended_action", "MAINTAIN")
                return StrategyAction(top_act) if hasattr(StrategyAction, top_act) else StrategyAction.MAINTAIN
            except Exception:
                return StrategyAction.MAINTAIN

        elif "Risk-Aware" in team_name or "Delta" in team_name:
            risk = RiskEngine.evaluate_risk(state, target_car_id=car_id, risk_lambda=0.50)
            if risk.overall_risk_score > 0.60 or car.tyre_wear_pct > 68.0:
                return StrategyAction.PIT_HARD
            return StrategyAction.CONSERVE if risk.overall_risk_score > 0.35 else StrategyAction.MAINTAIN

        elif "Conservative" in team_name or "Beta" in team_name:
            if car.tyre_wear_pct > 65.0:
                return StrategyAction.PIT_HARD
            return StrategyAction.CONSERVE

        elif "Aggressive" in team_name or "Alpha" in team_name:
            if car.tyre_wear_pct > 78.0:
                return StrategyAction.PIT_SOFT
            return StrategyAction.PUSH

        elif "Tyre Preserver" in team_name or "Gamma" in team_name:
            if car.tyre_wear_pct > 75.0:
                return StrategyAction.PIT_MEDIUM
            return StrategyAction.CONSERVE

        return StrategyAction.MAINTAIN
