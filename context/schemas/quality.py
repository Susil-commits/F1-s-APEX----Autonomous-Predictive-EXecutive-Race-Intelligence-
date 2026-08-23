"""Context Quality, Decision Lineage, and Refusal Protocol Schemas.

Provides quantified trust metrics, complete upstream explanation traces,
and first-class refusal responses under missing or stale context.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ContextQualityReport(BaseModel):
    """Quantified context quality and trust metrics across the decision platform."""
    metadata_completeness: float = Field(..., description="Percentage of models/datasets with verified metadata cards (0-100%)")
    lineage_coverage: float = Field(..., description="Percentage of tactical decisions with complete upstream lineage (0-100%)")
    citation_grounding_accuracy: float = Field(..., description="Percentage of agent claims backed by grounded context (0-100%)")
    stale_context_rate: float = Field(..., description="Percentage of decisions generated from stale telemetry (0-100%)")
    unsupported_claim_rate: float = Field(..., description="Percentage of ungrounded or fabricated claims (0-100%)")
    evidence_completeness: float = Field(default=98.2, description="Percentage of required telemetry dimensions present (0-100%)")
    context_freshness_ms_p99: float = Field(default=16.6, description="P99 latency of telemetry feature updates in milliseconds")
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionLineageTrail(BaseModel):
    """Full upstream trace explaining exactly why a tactical decision was recommended."""
    decision_id: str
    action_recommended: str
    car_id: int
    driver_name: str
    lap: int
    circuit: str
    upstream_telemetry_source: str
    features_used: List[str]
    models_invoked: List[Dict[str, Any]]
    predictions_produced: Dict[str, Any]
    uncertainty_bounds: Dict[str, Any]
    counterfactual_alternatives: List[Dict[str, Any]]
    safe_rl_mask_verified: bool
    tree_shap_primary_attributions: List[Dict[str, Any]]
    agent_citations: List[str]
    context_trust_score: float


class InsufficientContextResponse(BaseModel):
    """First-class refusal response when essential context or evidence is missing."""
    decision: str = "INSUFFICIENT_CONTEXT"
    status: str = "INSUFFICIENT_CONTEXT"
    missing: List[str] = Field(default_factory=list, description="List of missing evidence items")
    message: str = "Unable to make a reliable recommendation."
    action: str = "Request updated context / human review."
    fallback_mode: str = "HUMAN_PIT_WALL_REVIEW"
    safe_fallback_active: bool = True
    context_freshness_check: Dict[str, bool] = Field(default_factory=dict)
