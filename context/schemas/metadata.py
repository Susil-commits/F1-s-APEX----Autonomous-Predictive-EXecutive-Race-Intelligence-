"""Metadata Cards and Provenance Schemas for the APEX Context Layer.

Provides typed governance cards, data provenance records, and confidence bound definitions.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


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
    dataset_version: str = Field(default="fastf1_v2", description="Training / heldout dataset version (e.g. fastf1_v2)")
    dataset: Optional[str] = Field(default=None, description="Dataset alias for dataset_version")
    feature_schema: str = Field(default="race_features_v3", description="Feature schema version (e.g. race_features_v3)")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: Optional[str] = Field(default="2026_hungary_race", description="Race session identifier (e.g. 2026_hungary_race)")
    source_session: str = Field(default="2026_hungary_race", description="Race / session identifier (e.g. 2026_hungary_race)")
    session: Optional[str] = Field(default=None, description="Session alias for source_session")
    confidence_interval: ConfidenceIntervalBounds = Field(..., description="Calibrated confidence interval")
    predicted_value: Optional[float] = Field(default=None, description="Point prediction value (e.g. 0.48)")
    unit: str = Field(default="s/lap", description="Measurement unit")

    def model_post_init(self, __context: Any) -> None:
        if self.dataset is None:
            self.dataset = self.dataset_version
        elif self.dataset_version == "fastf1_v2" and self.dataset != "fastf1_v2":
            self.dataset_version = self.dataset

        if self.session_id and self.source_session == "2026_hungary_race" and self.session_id != "2026_hungary_race":
            self.source_session = self.session_id
        if self.session is None:
            self.session = self.source_session
        elif self.source_session == "2026_hungary_race" and self.session != "2026_hungary_race":
            self.source_session = self.session
        if self.session_id is None:
            self.session_id = self.source_session


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
