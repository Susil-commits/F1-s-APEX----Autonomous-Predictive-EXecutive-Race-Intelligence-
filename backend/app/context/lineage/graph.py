"""Context Graph delegator for backend.app.context.lineage.graph.

Maintains directed acyclic graphs (DAGs) representing race intelligence entities and causal relationships.
"""

from context.lineage.graph import (
    RaceContextGraph,
    build_default_race_context_graph,
)

__all__ = [
    "RaceContextGraph",
    "build_default_race_context_graph",
]
