"""AI-vs-AI Championship Tournament Engine: Simulates multi-race championships between diverse AI strategy archetypes."""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import SafetyCarStatus, StrategyAction, TrackCondition
from backend.app.strategy.hybrid_decision_engine import hybrid_decision_aggregator

logger = logging.getLogger(__name__)

POINTS_SYSTEM = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1] # F1 Official Points


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

    @classmethod
    def run_championship(
        cls,
        total_races: int = 100,
        seed: int = 42,
    ) -> dict[str, Any]:
        """
        Executes N championship rounds, tracking standings and points progression.
        """
        rng = np.random.default_rng(seed)
        standings: dict[str, TeamStanding] = {
            t["name"]: TeamStanding(team_name=t["name"], archetype=t["archetype"]) for t in cls.AI_TEAMS
        }
        all_finishes: dict[str, list[int]] = {t["name"]: [] for t in cls.AI_TEAMS}

        for r_i in range(total_races):
            track_name = cls.TRACKS[r_i % len(cls.TRACKS)]
            race_seed = seed + r_i * 79
            sim = RaceSimulator(track_name=track_name, seed=race_seed, grid_size=10, enable_dynamic_weather=True)

            curr_action = StrategyAction.MAINTAIN
            while not sim.is_finished:
                # Re-evaluate strategy upon events (SC, wetness) or every 2 laps
                state = sim.get_state()
                if sim.current_lap % 2 == 0 or state.safety_car != SafetyCarStatus.NONE or state.weather.condition != TrackCondition.DRY:
                    apex_dec = hybrid_decision_aggregator.evaluate_decision(state, num_mc_rollouts=45)
                    curr_action = apex_dec.recommendation
                sim.step(player_action=curr_action)

            # Record race finish results
            final_cars = sim.cars
            for t in cls.AI_TEAMS:
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
