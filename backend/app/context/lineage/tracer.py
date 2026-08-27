"""Context Lineage Tracer delegator for backend.app.context.lineage.tracer.

Traces full provenance chains from raw telemetry signals to executive strategy recommendations.
"""

from context.lineage.tracer import (
    LineageTracer,
    lineage_tracer,
)

__all__ = [
    "LineageTracer",
    "lineage_tracer",
]
