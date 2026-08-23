"""Pydantic schemas and typed definitions for the APEX Race Intelligence Context Layer.

Defines entities, relations, metadata schemas, lineage graphs, provenance records, and context quality metrics.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EntityType(str, Enum):
    RACE = "Race"
    SESSION = "Session"
    DRIVER = "Driver"
    TEAM = "Team"
    TELEMETRY_STREAM = "Telemetry Stream"
    FEATURE_SET = "Feature Set"
    DATASET_ASSET = "Dataset Asset"
    MODEL = "Model"
    MODEL_ASSET = "Model Asset"
    PREDICTION = "Prediction"
    PREDICTION_NODE = "Prediction Node"
    STRATEGY_CANDIDATE = "Strategy Candidate"
    STRATEGY_NODE = "Strategy Node"
    COUNTERFACTUAL = "Counterfactual"
    COUNTERFACTUAL_NODE = "Counterfactual Node"
    SAFE_RL_GUARDRAIL = "Safe RL Guardrail"
    DECISION = "Decision"
    DECISION_NODE = "Decision Node"
    OUTCOME = "Outcome"
    OUTCOME_NODE = "Outcome Node"
    WEATHER_SOURCE = "Weather Source"
    MCP_TOOL = "MCP Tool"


class RelationType(str, Enum):
    HAS_SESSION = "has_session"
    HAS_DRIVER = "has_driver"
    HAS_STRATEGY = "has_strategy"
    OBSERVED_DURING = "observed_during"
    PRODUCES = "produces"
    CONSUMED_BY = "consumed_by"
    USED_BY = "used_by"
    EXTRACTED_FROM = "extracted_from"
    TRAINED_ON = "trained_on"
    EVALUATED_ON = "evaluated_on"
    INFORMS = "informs"
    EVALUATED_BY = "evaluated_by"
    VERIFIED_BY = "verified_by"
    INVOKED_BY = "invoked_by"
    LEADS_TO = "leads_to"
    EXPLAINS = "explains"


class ConfidenceIntervalBounds(BaseModel):
    """Parametric or conformal confidence interval bounds."""
    lower: float = Field(..., description="Lower confidence bound (e.g. 0.32s)")
    upper: float = Field(..., description="Upper confidence bound (e.g. 0.64s)")
    confidence_level: float = Field(default=0.95, description="Nominal coverage probability (e.g. 0.95)")


class PredictionProvenanceRecord(BaseModel):
    """Structured provenance record attached to every prediction in APEX."""
    prediction_id: str = Field(..., description="Unique prediction identifier (e.g. pred_1042)")
    model: str = Field(..., description="Model name (e.g. tyre_degradation_xgb)")
    model_version: str = Field(..., description="Model version (e.g. v1.4)")
    dataset_version: str = Field(default="fastf1_heldout_v2", description="Training / heldout dataset version (e.g. fastf1_heldout_v2)")
    dataset: Optional[str] = Field(default=None, description="Dataset alias for dataset_version")
    feature_schema: str = Field(..., description="Feature schema version (e.g. race_features_v3)")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_session: str = Field(default="2026_hungary_race", description="Race / session identifier (e.g. 2026_Hungary_R)")
    session: Optional[str] = Field(default=None, description="Session alias for source_session")
    confidence_interval: ConfidenceIntervalBounds = Field(..., description="Calibrated confidence interval")
    predicted_value: Optional[float] = Field(default=None, description="Point prediction value (e.g. 0.48)")
    unit: str = Field(default="s/lap", description="Measurement unit")

    def model_post_init(self, __context: Any) -> None:
        if self.dataset is None:
            self.dataset = self.dataset_version
        elif self.dataset_version == "fastf1_heldout_v2" and self.dataset != "fastf1_heldout_v2":
            self.dataset_version = self.dataset

        if self.session is None:
            self.session = self.source_session
        elif self.source_session == "2026_hungary_race" and self.session != "2026_hungary_race":
            self.source_session = self.session


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



class ProvenanceMetadata(BaseModel):
    """Immutable provenance stamp attached to decisions, models, and feature sets."""
    dataset_version: str = Field(..., description="Version of training/telemetry dataset (e.g. fastf1_2018_2024_v1.0)")
    feature_schema_version: str = Field(..., description="Schema version of extracted features (e.g. race_features_v3)")
    model_version: str = Field(..., description="Registered model version (e.g. tyre_degradation_xgb_v1.4)")
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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
    prediction_provenance: Optional[PredictionProvenanceRecord] = Field(default=None, description="Attached prediction provenance")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    metrics: Dict[str, float]
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
    source_apis: List[str]
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
