"""Real-time lineage tracer capturing telemetry-to-decision execution paths during live race ticks."""
from typing import Dict, List, Any, Optional
import time
import hashlib
from datetime import datetime
from backend.app.context.schemas import ContextNode, ContextEdge, EntityType, RelationType, ProvenanceMetadata
from backend.app.context.lineage.graph import RaceContextGraph, build_default_race_context_graph


class LineageTracer:
    """Singleton tracer capturing and indexing lineage events as race ticks execute."""

    def __init__(self):
        self.active_graph = build_default_race_context_graph()
        self.audit_log: List[Dict[str, Any]] = []

    def record_prediction(
        self,
        model_id: str,
        car_id: int,
        lap: int,
        prediction_payload: Dict[str, Any],
    ) -> str:
        """Log a model inference prediction event into the context graph."""
        pred_id = f"pred:{model_id.replace('model:', '')}_car_{car_id}_lap_{lap}_{int(time.time()*1000)}"
        node = ContextNode(
            id=pred_id,
            name=f"Inference Output ({model_id}) Lap {lap}",
            entity_type=EntityType.PREDICTION_NODE,
            description="Live model inference event",
            properties=prediction_payload,
        )
        self.active_graph.add_node(node)
        self.active_graph.add_edge(
            ContextEdge(source_id=model_id, target_id=pred_id, relation_type=RelationType.PRODUCES)
        )
        self.audit_log.append({
            "event": "PREDICTION_RECORDED",
            "model_id": model_id,
            "pred_id": pred_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        return pred_id

    def record_decision(
        self,
        decision_id: str,
        action: str,
        car_id: int,
        lap: int,
        evidence_nodes: List[str],
        reasoning: str,
    ) -> ContextNode:
        """Log an executive decision with full links to evidence nodes."""
        node = ContextNode(
            id=decision_id,
            name=f"Tactical Action: {action}",
            entity_type=EntityType.DECISION_NODE,
            description=reasoning,
            properties={"action": action, "car_id": car_id, "lap": lap, "reasoning": reasoning},
            provenance=ProvenanceMetadata(
                dataset_version="fastf1_live_feed_v1.0",
                feature_schema_version="race_features_v3",
                model_version="apex_planner_agent_v2.0",
                source="live_race_session",
                lineage_id=hashlib.sha256(f"{decision_id}-{lap}".encode()).hexdigest()[:16],
            ),
        )
        self.active_graph.add_node(node)
        for ev_id in evidence_nodes:
            if self.active_graph.get_node(ev_id):
                self.active_graph.add_edge(
                    ContextEdge(source_id=ev_id, target_id=decision_id, relation_type=RelationType.INFORMS)
                )
        return node

    def get_graph(self) -> RaceContextGraph:
        """Return the active RaceContextGraph."""
        return self.active_graph


# Global Singleton Lineage Tracer
lineage_tracer = LineageTracer()
