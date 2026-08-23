"""Pydantic schemas and typed definitions for the APEX Race Intelligence Context Layer.

Defines entities, relations, metadata schemas, lineage graphs, and context quality metrics.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from datetime import datetime


class EntityType(str, Enum):
    RACE = "RACE"
    SESSION = "SESSION"
    DRIVER = "DRIVER"
    TEAM = "TEAM"
    TELEMETRY_STREAM = "TELEMETRY_STREAM"
    FEATURE_SET = "FEATURE_SET"
    DATASET_ASSET = "DATASET_ASSET"
    MODEL_ASSET = "MODEL_ASSET"
    PREDICTION_NODE = "PREDICTION_NODE"
    STRATEGY_NODE = "STRATEGY_NODE"
    COUNTERFACTUAL_NODE = "COUNTERFACTUAL_NODE"
    SAFE_RL_GUARDRAIL = "SAFE_RL_GUARDRAIL"
    DECISION_NODE = "DECISION_NODE"
    OUTCOME_NODE = "OUTCOME_NODE"
    WEATHER_SOURCE = "WEATHER_SOURCE"
    MCP_TOOL = "MCP_TOOL"


class RelationType(str, Enum):
    HAS_SESSION = "has_session"
    HAS_DRIVER = "has_driver"
    HAS_STRATEGY = "has_strategy"
    PRODUCES = "produces"
    OBSERVED_DURING = "observed_during"
    EXTRACTED_FROM = "extracted_from"
    USED_BY = "used_by"
    TRAINED_ON = "trained_on"
    EVALUATED_ON = "evaluated_on"
    INFORMS = "informs"
    EVALUATED_BY = "evaluated_by"
    VERIFIED_BY = "verified_by"
    INVOKED_BY = "invoked_by"
    LEADS_TO = "leads_to"
    EXPLAINS = "explains"


class ProvenanceMetadata(BaseModel):
    """Immutable provenance stamp attached to predictions, decisions, and feature sets."""
    dataset_version: str = Field(..., description="Version of training/telemetry dataset (e.g. fastf1_2018_2024_v1.0)")
    feature_schema_version: str = Field(..., description="Schema version of extracted features (e.g. race_features_v3)")
    model_version: str = Field(..., description="Registered model version (e.g. tyre_degradation_xgb_v1.4)")
    timestamp_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    source: str = Field(..., description="Primary telemetry source (e.g. fastf1_live_telemetry_60hz)")
    lineage_id: str = Field(..., description="Deterministic SHA-256 traceable hash")
    owner: str = Field(default="apex-decision-intelligence", description="Asset owner")
    status: str = Field(default="validated", description="Validation status: validated | experimental | deprecated")


class ContextNode(BaseModel):
    """A node in the APEX Race Intelligence Context Graph."""
    id: str = Field(..., description="Unique entity identifier (e.g. model:tyre_xgb_v1.4, stream:telemetry_car_4)")
    name: str = Field(..., description="Human-readable entity name")
    entity_type: EntityType = Field(..., description="Categorical entity type")
    description: str = Field(..., description="Entity description or business purpose")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")
    provenance: Optional[ProvenanceMetadata] = Field(default=None, description="Attached provenance record")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ContextEdge(BaseModel):
    """A directed edge in the APEX Race Intelligence Context Graph."""
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relation_type: RelationType = Field(..., description="Semantic relation")
    weight: float = Field(default=1.0, description="Edge weight / confidence score")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadata properties on relation")


class ContextGraphSchema(BaseModel):
    """Complete serialized representation of the Race Intelligence Context Graph."""
    graph_id: str = Field(default="apex-race-context-graph-v1")
    nodes: List[ContextNode] = Field(default_factory=list)
    edges: List[ContextEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ModelMetadataCard(BaseModel):
    """Formal Model Card containing governance, training lineage, and evaluation metrics."""
    model_id: str
    name: str
    version: str
    algorithm_family: str
    training_dataset: str
    feature_schema: str
    owner: str
    training_circuits: List[str]
    evaluation_dataset: str
    metrics: Dict[str, float]  # e.g. {"mae": 0.3597, "rmse": 0.5312, "r2": 0.8342, "pearson_r": 0.9166, "cliff_accuracy": 0.8843}
    inference_latency_ms_p99: float
    input_features: List[str]
    output_dimension: str
    status: str = "validated"
    created_at: str
    sha256_hash: str


class DatasetMetadataCard(BaseModel):
    """Formal Dataset Card containing ingestion sources, schema versions, and validation records."""
    dataset_id: str
    name: str
    version: str
    source_apis: List[str]  # e.g. ["FastF1", "Jolpica API"]
    total_laps: int
    circuits_covered: List[str]
    seasons_covered: List[int]
    schema_fields: List[str]
    data_quality_score: float
    status: str = "validated"
    created_at: str


class ContextQualityReport(BaseModel):
    """Quantified context quality and trust metrics across the decision platform."""
    metadata_completeness: float = Field(..., description="Percentage of models/datasets with verified metadata cards (0-100%)")
    lineage_coverage: float = Field(..., description="Percentage of tactical decisions with complete upstream lineage (0-100%)")
    citation_grounding_accuracy: float = Field(..., description="Percentage of agent claims backed by grounded context (0-100%)")
    stale_context_rate: float = Field(..., description="Percentage of decisions generated from stale telemetry (0-100%)")
    unsupported_claim_rate: float = Field(..., description="Percentage of ungrounded or fabricated claims (0-100%)")
    context_freshness_ms_p99: float = Field(..., description="P99 latency of telemetry feature updates in milliseconds")
    timestamp_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


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
