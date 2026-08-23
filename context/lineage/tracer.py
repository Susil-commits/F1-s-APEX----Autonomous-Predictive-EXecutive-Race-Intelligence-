"""Context Lineage Tracer for APEX Decision Intelligence.

Continuously captures runtime telemetry, model predictions, counterfactual branches,
and safe RL validations into a persistent, queryable RaceContextGraph.
"""
from typing import Dict, Any, Optional
from context.lineage.graph import RaceContextGraph, build_default_race_context_graph
from context.schemas.entities import (
    ContextNode,
    ContextEdge,
    EntityType,
    RelationType,
)
from context.schemas.quality import DecisionLineageTrail


class LineageTracer:
    """Manages dynamic context graph state across race simulation and live telemetry ticks."""

    def __init__(self, circuit_name: str = "Silverstone", driver_name: str = "Lando Norris"):
        self.circuit_name = circuit_name
        self.driver_name = driver_name
        self._graph: RaceContextGraph = build_default_race_context_graph(
            circuit_name=circuit_name,
            driver_name=driver_name,
        )

    def get_graph(self) -> RaceContextGraph:
        """Fetch active in-memory RaceContextGraph."""
        return self._graph

    def reset_for_race(self, circuit_name: str, driver_name: str = "Lando Norris", car_id: int = 4) -> RaceContextGraph:
        """Initialize fresh context graph for a new race session."""
        self.circuit_name = circuit_name
        self.driver_name = driver_name
        self._graph = build_default_race_context_graph(
            circuit_name=circuit_name,
            driver_name=driver_name,
            car_id=car_id,
        )
        return self._graph

    def trace_decision(self, decision_id: str) -> Optional[DecisionLineageTrail]:
        """Generate verifiable decision lineage trail."""
        return self._graph.trace_decision_lineage(decision_id)


# Global Singleton Lineage Tracer
lineage_tracer = LineageTracer()
