"""Digital Twin state store and persistence layer."""
from typing import Dict, List, Optional, Any
import json
from backend.app.simulator.models import RaceState, DecisionExplanation


class RaceStore:
    """Hybrid in-memory and persistent store for race states and decision logs."""

    def __init__(self):
        self.active_races: Dict[str, RaceState] = {}
        self.tick_history: Dict[str, List[Dict[str, Any]]] = {}
        self.decision_history: Dict[str, List[Dict[str, Any]]] = {}
        self.benchmark_runs: List[Dict[str, Any]] = []

    def save_state(self, state: RaceState):
        """Saves the current tick state to hot store and tick history."""
        self.active_races[state.race_id] = state
        if state.race_id not in self.tick_history:
            self.tick_history[state.race_id] = []
        self.tick_history[state.race_id].append(state.model_dump())

    def get_state(self, race_id: str) -> Optional[RaceState]:
        """Retrieves the active state for a given race ID."""
        return self.active_races.get(race_id)

    def log_decision(self, race_id: str, lap: int, decision: DecisionExplanation):
        """Logs a strategic decision explanation."""
        if race_id not in self.decision_history:
            self.decision_history[race_id] = []
        self.decision_history[race_id].append({
            "race_id": race_id,
            "lap": lap,
            "decision": decision.model_dump(),
        })

    def get_decision_history(self, race_id: str) -> List[Dict[str, Any]]:
        """Retrieves all decision logs for a race."""
        return self.decision_history.get(race_id, [])

    def record_benchmark(self, result: Dict[str, Any]):
        """Saves a benchmark evaluation result."""
        self.benchmark_runs.append(result)


# Singleton store instance
store = RaceStore()
