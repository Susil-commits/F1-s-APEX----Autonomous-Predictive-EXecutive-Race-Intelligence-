"""Typed Context Entity definitions and Graph primitives for the APEX Context Layer.

Defines all 14 Core Context Entities:
  1. Race
  2. Session
  3. Driver
  4. Team
  5. TelemetryStream
  6. FeatureSet
  7. Model
  8. Prediction
  9. StrategyCandidate
  10. Counterfactual
  11. Decision
  12. Outcome
  13. WeatherSource
  14. Tool

Along with categorical EntityType, RelationType, ContextNode, ContextEdge, and ContextGraphSchema.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EntityType(str, Enum):
    """Categorical types for all entities in the APEX Race Intelligence Context Graph."""
    RACE = "Race"
    SESSION = "Session"
    DRIVER = "Driver"
    TEAM = "Team"
    TELEMETRY_STREAM = "TelemetryStream"
    FEATURE_SET = "FeatureSet"
    MODEL = "Model"
    MODEL_ASSET = "ModelAsset"
    PREDICTION = "Prediction"
    PREDICTION_NODE = "PredictionNode"
    STRATEGY_CANDIDATE = "StrategyCandidate"
    STRATEGY_NODE = "StrategyNode"
    COUNTERFACTUAL = "Counterfactual"
    COUNTERFACTUAL_NODE = "CounterfactualNode"
    DECISION = "Decision"
    DECISION_NODE = "DecisionNode"
    OUTCOME = "Outcome"
    OUTCOME_NODE = "OutcomeNode"
    WEATHER_SOURCE = "WeatherSource"
    TOOL = "Tool"
    SAFE_RL_GUARDRAIL = "SafeRLGuardrail"
    DATASET_ASSET = "DatasetAsset"


class RelationType(str, Enum):
    """Semantic relationship types between nodes in the Context DAG."""
    # Core 7 Linear Lineage Chain
    # Telemetry -> FeatureSet -> Model -> Prediction -> StrategyCandidate -> Counterfactual -> Decision -> Outcome
    EXTRACTED_FROM = "extracted_from"      # Telemetry -> FeatureSet
    CONSUMED_BY = "consumed_by"            # FeatureSet -> Model
    USED_BY = "used_by"                    # FeatureSet -> Model
    PRODUCES = "produces"                  # Model -> Prediction, Decision -> Outcome
    INFORMS = "informs"                    # Prediction -> StrategyCandidate
    EVALUATED_BY = "evaluated_by"          # StrategyCandidate -> Counterfactual
    EVALUATED_ON = "evaluated_on"          # Model -> Dataset
    LEADS_TO = "leads_to"                  # Counterfactual -> Decision, Decision -> Outcome
    VERIFIED_BY = "verified_by"            # Counterfactual / Decision -> Tool / Guardrail

    # Structural & Domain Relations
    HAS_SESSION = "has_session"            # Race -> Session
    HAS_DRIVER = "has_driver"              # Session / Team -> Driver
    EMPLOYS = "employs"                    # Team -> Driver
    OBSERVED_DURING = "observed_during"    # Telemetry / Weather -> Session
    FEEDS = "feeds"                        # WeatherSource -> FeatureSet
    INVOKED_BY = "invoked_by"              # Tool -> Decision
    TRAINED_ON = "trained_on"              # Model -> Dataset
    EXPLAINS = "explains"                  # Tool / SHAP -> Decision


# ============================================================================
# 14 Concrete Entity Schemas
# ============================================================================

class RaceEntity(BaseModel):
    """Grand Prix event entity representing circuit, season, round, and race parameters."""
    id: str = Field(..., description="Unique race ID (e.g. race:silverstone_2024)")
    name: str = Field(..., description="Official Grand Prix name")
    circuit: str = Field(..., description="Circuit name (e.g. Silverstone, Spa, Monza)")
    year: int = Field(default=2024, description="Championship season year")
    round_number: Optional[int] = Field(default=None, description="Season round number")
    total_laps: int = Field(default=52, description="Scheduled total race laps")
    lap_distance_km: float = Field(default=5.891, description="Single lap distance in kilometers")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionEntity(BaseModel):
    """Specific on-track session (Race, FP1, FP2, FP3, Qualifying, Sprint)."""
    id: str = Field(..., description="Unique session ID (e.g. session:silverstone_2024_race)")
    race_id: str = Field(..., description="Parent race ID")
    session_type: str = Field(default="Race", description="Session classification: Race | Qualifying | Practice")
    track_status: str = Field(default="Green", description="Live flag status: Green | Yellow | SC | VSC | Red")
    current_lap: int = Field(default=1, description="Current session progress lap")
    start_time_utc: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DriverEntity(BaseModel):
    """F1 Driver competing in the grand prix with behavioral and performance attributes."""
    id: str = Field(..., description="Unique driver ID (e.g. driver:car_4)")
    car_id: int = Field(..., description="Permanent car race number (e.g. 4 for Norris)")
    driver_name: str = Field(..., description="Full driver name")
    driver_code: str = Field(default="NOR", description="3-letter broadcast identifier")
    team_name: str = Field(default="McLaren", description="Constructor affiliation")
    grid_position: int = Field(default=1, description="Starting grid position")
    current_position: int = Field(default=1, description="Current live race track position")
    tyre_compound: str = Field(default="MEDIUM", description="Currently fitted tyre compound")
    tyre_age_laps: int = Field(default=0, description="Laps run on current tyre set")
    tyre_wear_pct: float = Field(default=0.0, description="Estimated tyre wear percentage")


class TeamEntity(BaseModel):
    """Constructor / Racing team entity with operational baselines and pit crew efficiency."""
    id: str = Field(..., description="Unique team ID (e.g. team:mclaren)")
    name: str = Field(..., description="Constructor name")
    pit_crew_avg_stop_s: float = Field(default=2.45, description="Historical average stationary pit stop time")
    headquarters: Optional[str] = Field(default=None)
    engine_supplier: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TelemetryStreamEntity(BaseModel):
    """High-frequency vehicle sensor and telemetry ingestion stream."""
    id: str = Field(..., description="Unique telemetry stream ID (e.g. stream:fastf1_car_4_lap_32)")
    car_id: int = Field(..., description="Car ID transmitting sensor feed")
    sampling_frequency_hz: float = Field(default=60.0, description="Sensor sampling frequency (e.g. 60Hz)")
    source_url: str = Field(default="fastf1_live_telemetry_60hz", description="Primary telemetry broker or bus")
    channels: List[str] = Field(default_factory=lambda: [
        "speed_kmh", "throttle_pct", "brake_pct", "gear", "steer_deg",
        "tyre_surface_temp_c", "tyre_core_temp_c", "drs_status", "ers_deploy_kw"
    ])
    quality_score: float = Field(default=99.8, description="Data stream quality and freshness score (0-100%)")
    packet_loss_rate_pct: float = Field(default=0.01, description="Sensor stream packet loss rate")


class FeatureSetEntity(BaseModel):
    """Normalized multi-dimensional feature vector engineered from raw telemetry."""
    id: str = Field(..., description="Unique feature set ID (e.g. features:car_4_lap_32)")
    schema_version: str = Field(default="race_features_v3", description="Registered feature store schema")
    dimensionality: int = Field(default=28, description="Number of feature dimensions (e.g. 28-D)")
    feature_names: List[str] = Field(default_factory=lambda: [
        "stint_lap", "tyre_age_laps", "tyre_wear_pct", "track_temp_c", "air_temp_c",
        "rain_probability_pct", "gap_to_car_behind_s", "gap_to_car_ahead_s",
        "dirty_air_wake_pct", "fuel_load_kg", "drs_active", "undercut_threat_flag"
    ])
    extraction_latency_ms: float = Field(default=0.0245, description="P99 feature extraction latency SLA")
    values: Dict[str, Any] = Field(default_factory=dict, description="Concrete extracted feature values")


class ModelEntity(BaseModel):
    """Machine learning, reinforcement learning, physics-informed, or statistical model asset."""
    id: str = Field(..., description="Unique model identifier (e.g. model:tyre_degradation_xgb_v1.4)")
    name: str = Field(..., description="Human-readable model name")
    version: str = Field(..., description="Semantic version string")
    algorithm_family: str = Field(..., description="Model family: XGBoost | PINN | DQN | PPO | MCTS | Radar")
    training_dataset: str = Field(..., description="Version of training dataset asset")
    feature_schema: str = Field(default="race_features_v3", description="Required input feature schema")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Held-out evaluation metrics (R², MAE, Brier)")
    inference_latency_ms_p99: float = Field(default=0.012, description="P99 inference execution latency")
    status: str = Field(default="validated", description="Deployment status: validated | experimental | deprecated")


class PredictionEntity(BaseModel):
    """Point estimate and calibrated uncertainty forecast generated by an APEX model."""
    id: str = Field(..., description="Unique prediction ID (e.g. pred:tyre_deg_car_4_lap_32)")
    model_id: str = Field(..., description="Producing model identifier")
    target_variable: str = Field(..., description="Target name (e.g. lap_time_degradation_s, rain_onset_probability)")
    predicted_value: float = Field(..., description="Predicted scalar value")
    confidence_interval_95: List[float] = Field(default_factory=list, description="95% confidence bounds [lower, upper]")
    unit: str = Field(default="s/lap", description="Measurement unit")
    cliff_probability_pct: Optional[float] = Field(default=None, description="Thermal degradation cliff probability")
    laps_to_cliff: Optional[int] = Field(default=None, description="Estimated laps until catastrophic pace drop")


class StrategyCandidateEntity(BaseModel):
    """Candidate pit window and tactical action evaluated by APEX intelligence."""
    id: str = Field(..., description="Unique candidate ID (e.g. strategy:candidate_box_lap_32)")
    action: str = Field(..., description="Tactical action: PIT_NOW | PIT_PLUS_2 | STAY_OUT | PUSH | CONSERVE")
    target_compound: Optional[str] = Field(default="HARD", description="Target tyre compound to fit")
    stint_target_laps: int = Field(default=20, description="Target stint length in laps")
    traffic_rejoin_gap_s: float = Field(default=4.1, description="Predicted buffer to nearest traffic on pit exit")
    undercut_protection_flag: bool = Field(default=True, description="Whether action defends against rival undercut")


class CounterfactualEntity(BaseModel):
    """Stochastic counterfactual rollout distribution comparing alternative strategy paths."""
    id: str = Field(..., description="Unique counterfactual ID (e.g. cf:rollout_lap_32)")
    total_rollouts: int = Field(default=1000, description="Number of Monte Carlo simulations executed")
    branches: List[Dict[str, Any]] = Field(default_factory=lambda: [
        {"action": "PIT_NOW", "p1_win_pct": 67.4, "utility_mean": 0.82, "utility_uncertainty": 0.11},
        {"action": "PIT_PLUS_2", "p1_win_pct": 59.1, "utility_mean": 0.71, "utility_uncertainty": 0.15},
        {"action": "STAY_OUT", "p1_win_pct": 41.0, "utility_mean": 0.63, "utility_uncertainty": 0.20},
    ])
    expected_finish_positions: Dict[str, float] = Field(default_factory=dict)
    risk_variance: float = Field(default=0.08, description="Outcome variance under stochastic race dynamics")


class DecisionEntity(BaseModel):
    """Executive tactical race directive recommended by APEX strategy agents."""
    id: str = Field(..., description="Unique decision ID (e.g. decision:box_lap_32_car_4)")
    car_id: int = Field(..., description="Target car ID")
    lap: int = Field(..., description="Lap on which decision is issued")
    action_recommended: str = Field(..., description="Executive action (e.g. BOX_THIS_LAP)")
    target_compound: str = Field(default="HARD", description="Compound to fit on pit stop")
    confidence_score: float = Field(default=0.81, description="Calibrated confidence score (0.0 to 1.0)")
    urgency: str = Field(default="HIGH", description="Urgency: LOW | MEDIUM | HIGH | CRITICAL")
    reason: str = Field(..., description="Human-readable tactical justification")
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OutcomeEntity(BaseModel):
    """Empirical post-decision race outcome, position delta, and delta verification."""
    id: str = Field(..., description="Unique outcome ID (e.g. outcome:finish_car_4)")
    decision_id: str = Field(..., description="Governing decision ID")
    actual_finish_position: int = Field(default=1, description="Recorded finish position")
    points_awarded: int = Field(default=25, description="Championship points gained")
    pit_stop_delta_vs_stay_out_s: float = Field(default=14.8, description="Net time saved vs counterfactual baseline")
    objective_met: bool = Field(default=True, description="Whether tactical race objective was achieved")


class WeatherSourceEntity(BaseModel):
    """Doppler radar, barometric weather station, and meteorological forecast stream."""
    id: str = Field(..., description="Unique weather source ID (e.g. weather:silverstone_doppler_radar)")
    station_name: str = Field(..., description="Meteorological station or radar feed identifier")
    sampling_frequency_hz: float = Field(default=1.0, description="Weather sensor update rate (Hz)")
    rain_probability_next_5_laps: float = Field(default=0.72, description="Forecast rain probability in next 5 laps")
    track_wetness_index: float = Field(default=0.35, description="Surface wetness index (0.0=dry, 1.0=flooded)")
    track_temp_c: float = Field(default=38.5, description="Current track surface temperature")
    air_temp_c: float = Field(default=24.0, description="Ambient air temperature")


class ToolEntity(BaseModel):
    """Analytical, explainability, or guardrail tool invoked in the APEX decision pipeline."""
    id: str = Field(..., description="Unique tool identifier (e.g. tool:safe_rl_action_mask_v2)")
    name: str = Field(..., description="Tool name (e.g. Safe RL Action Mask, TreeSHAP Explainer, Monte Carlo Engine)")
    tool_type: str = Field(..., description="Tool classification: Guardrail | Explainability | Simulation | RAG")
    constraints_enforced: List[str] = Field(default_factory=list, description="Physical or sporting regulations enforced")
    status: str = Field(default="ACTIVE", description="Execution status")


# ============================================================================
# Graph Node and Edge Primitives
# ============================================================================

class ContextNode(BaseModel):
    """A generic node in the APEX Race Intelligence Context Graph."""
    id: str = Field(..., description="Unique entity identifier (e.g. model:tyre_xgb_v1.4, stream:telemetry_car_4)")
    name: str = Field(..., description="Human-readable entity name")
    entity_type: EntityType = Field(..., description="Categorical entity type")
    description: str = Field(default="", description="Entity description or business purpose")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")
    provenance: Optional[Any] = Field(default=None, description="Attached provenance metadata")
    prediction_provenance: Optional[Any] = Field(default=None, description="Attached prediction provenance")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ContextEdge(BaseModel):
    """A directed edge modeling semantic relationships in the Context Graph."""
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relation_type: RelationType = Field(..., description="Semantic relation")
    weight: float = Field(default=1.0, description="Edge weight / confidence score")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadata properties on relation")


class ContextGraphSchema(BaseModel):
    """Complete serialized schema representation of the Race Intelligence Context Graph."""
    graph_id: str = Field(default="apex-race-context-graph-v1")
    nodes: List[ContextNode] = Field(default_factory=list)
    edges: List[ContextEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
