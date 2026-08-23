"""APEX Race Intelligence Context Layer Root Package.

Exposes:
  - 14 Core Context Entities & Schemas (Race, Session, Driver, Team, TelemetryStream, FeatureSet, Model,
    Prediction, StrategyCandidate, Counterfactual, Decision, Outcome, WeatherSource, Tool)
  - 7 Linear Lineage Chain Relationships (Telemetry -> FeatureSet -> Model -> Prediction -> StrategyCandidate -> Counterfactual -> Decision -> Outcome)
  - Model & Dataset Metadata Registries & Cards
  - Directed Context Graph (RaceContextGraph) & Runtime Lineage Tracer
  - Semantic Context Retriever & Evidence Resolution Engine
  - Context Quality & Agent Grounding Evaluation Suites
"""
from context.schemas.entities import (
    EntityType,
    RelationType,
    RaceEntity,
    SessionEntity,
    DriverEntity,
    TeamEntity,
    TelemetryStreamEntity,
    FeatureSetEntity,
    ModelEntity,
    PredictionEntity,
    StrategyCandidateEntity,
    CounterfactualEntity,
    DecisionEntity,
    OutcomeEntity,
    WeatherSourceEntity,
    ToolEntity,
    ContextNode,
    ContextEdge,
    ContextGraphSchema,
)
from context.schemas.metadata import (
    ConfidenceIntervalBounds,
    PredictionProvenanceRecord,
    ProvenanceMetadata,
    ModelMetadataCard,
    DatasetMetadataCard,
)
from context.schemas.quality import (
    ContextQualityReport,
    DecisionLineageTrail,
    InsufficientContextResponse,
)
from context.metadata.model_metadata import (
    MODEL_REGISTRY,
    get_model_metadata,
    list_all_model_metadata,
)
from context.metadata.dataset_metadata import (
    DATASET_REGISTRY,
    get_dataset_metadata,
    list_all_dataset_metadata,
)
from context.lineage.graph import (
    RaceContextGraph,
    build_default_race_context_graph,
)
from context.lineage.tracer import (
    LineageTracer,
    lineage_tracer,
)
from context.retrieval.context_retriever import (
    ContextRetriever,
    context_retriever,
)
from context.evaluation.quality_metrics import (
    ContextQualityEngine,
    context_quality_engine,
)
from context.evaluation.eval_suite import (
    ContextAgentEvaluator,
    agent_evaluator,
    AgentEvalReport,
    AgentEvaluationMetric,
    AgentTrajectoryEvaluation,
    AgentTrajectoryStep,
    InsufficientEvidenceResponse,
)

__all__ = [
    # Entity Types & Relations
    "EntityType",
    "RelationType",
    "RaceEntity",
    "SessionEntity",
    "DriverEntity",
    "TeamEntity",
    "TelemetryStreamEntity",
    "FeatureSetEntity",
    "ModelEntity",
    "PredictionEntity",
    "StrategyCandidateEntity",
    "CounterfactualEntity",
    "DecisionEntity",
    "OutcomeEntity",
    "WeatherSourceEntity",
    "ToolEntity",
    "ContextNode",
    "ContextEdge",
    "ContextGraphSchema",

    # Metadata & Quality
    "ConfidenceIntervalBounds",
    "PredictionProvenanceRecord",
    "ProvenanceMetadata",
    "ModelMetadataCard",
    "DatasetMetadataCard",
    "ContextQualityReport",
    "DecisionLineageTrail",
    "InsufficientContextResponse",

    # Registries
    "MODEL_REGISTRY",
    "get_model_metadata",
    "list_all_model_metadata",
    "DATASET_REGISTRY",
    "get_dataset_metadata",
    "list_all_dataset_metadata",

    # Lineage & Graph
    "RaceContextGraph",
    "build_default_race_context_graph",
    "LineageTracer",
    "lineage_tracer",

    # Retrieval
    "ContextRetriever",
    "context_retriever",

    # Quality & Evaluation
    "ContextQualityEngine",
    "context_quality_engine",
    "ContextAgentEvaluator",
    "agent_evaluator",
    "AgentEvalReport",
    "AgentEvaluationMetric",
    "AgentTrajectoryEvaluation",
    "AgentTrajectoryStep",
    "InsufficientEvidenceResponse",
]
