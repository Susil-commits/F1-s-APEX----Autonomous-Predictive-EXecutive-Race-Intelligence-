"""Tests for APEX Race Intelligence Context Graph, lineage traversal, and metadata models."""
import pytest
from backend.app.context.schemas import (
    ContextNode,
    ContextEdge,
    EntityType,
    RelationType,
    ProvenanceMetadata,
)
from backend.app.context.lineage.graph import (
    RaceContextGraph,
    build_default_race_context_graph,
)
from backend.app.context.metadata.model_metadata import (
    MODEL_REGISTRY,
    get_model_metadata,
    list_all_model_metadata,
)
from backend.app.context.metadata.dataset_metadata import (
    DATASET_REGISTRY,
    get_dataset_metadata,
    list_all_dataset_metadata,
)
from backend.app.context.retrieval.context_retriever import (
    ContextRetriever,
    context_retriever,
)


def test_model_metadata_registry():
    """Verify all production models have complete, validated metadata cards."""
    models = list_all_model_metadata()
    assert len(models) >= 5

    xgb = get_model_metadata("tyre_degradation_xgb")
    assert xgb is not None
    assert xgb.version == "v1.4"
    assert xgb.metrics["r2"] > 0.80
    assert xgb.metrics["mae"] < 0.40
    assert xgb.status == "validated"
    assert len(xgb.training_circuits) >= 5
    assert len(xgb.input_features) >= 5


def test_dataset_metadata_registry():
    """Verify dataset registry contains FastF1 gold corpus and held-out evaluation splits."""
    datasets = list_all_dataset_metadata()
    assert len(datasets) >= 3

    gold = get_dataset_metadata("fastf1_2018_2024_gold")
    assert gold is not None
    assert gold.total_laps >= 6000
    assert "FastF1 Python API" in gold.source_apis
    assert gold.data_quality_score > 95.0


def test_race_context_graph_construction():
    """Verify that the default RaceContextGraph builds properly with all entity types and relationships."""
    graph = build_default_race_context_graph(
        circuit_name="Silverstone",
        session_name="Grand Prix Race",
        car_id=4,
        driver_name="Lando Norris",
        lap=32,
    )

    assert len(graph.nodes) >= 10
    assert len(graph.edges) >= 10

    # Check key node presence
    assert graph.get_node("race:silverstone_2023") is not None
    assert graph.get_node("driver:car_4") is not None
    assert graph.get_node("model:tyre_degradation_xgb_v1.4") is not None
    assert graph.get_node("decision:box_lap_32_car_4") is not None


def test_upstream_lineage_traversal():
    """Verify upstream lineage traversal finds telemetry, features, and model assets from a decision."""
    graph = build_default_race_context_graph()
    decision_id = "decision:box_lap_32_car_4"

    upstream_nodes = graph.get_upstream_lineage(decision_id, max_depth=5)
    assert len(upstream_nodes) > 0

    node_types = {n.entity_type for n in upstream_nodes}
    assert EntityType.SAFE_RL_GUARDRAIL in node_types or EntityType.COUNTERFACTUAL_NODE in node_types


def test_decision_lineage_trail_trace():
    """Verify trace_decision_lineage outputs complete verifiable DecisionLineageTrail."""
    graph = build_default_race_context_graph()
    decision_id = "decision:box_lap_32_car_4"

    trail = graph.trace_decision_lineage(decision_id)
    assert trail is not None
    assert trail.decision_id == decision_id
    assert trail.action_recommended == "BOX_THIS_LAP"
    assert trail.context_trust_score >= 0.90
    assert len(trail.models_invoked) >= 1
    assert len(trail.counterfactual_alternatives) >= 2
    assert len(trail.tree_shap_primary_attributions) >= 3


def test_context_retriever_queries():
    """Verify context retriever provides grounded summaries for Planner Agent."""
    retriever = ContextRetriever()
    agent_ctx = retriever.query_context_for_agent(car_id=4, lap=32)

    assert "models_in_context" in agent_ctx
    assert "data_sources" in agent_ctx
    assert "counterfactual_branches" in agent_ctx
    assert "tree_shap_attributions" in agent_ctx
    assert agent_ctx["context_trust_score"] >= 0.90


def test_prediction_provenance_record():
    """Verify every prediction carries full provenance (model, dataset, schema, session, CI bounds)."""
    retriever = ContextRetriever()
    prov = retriever.get_prediction_provenance("pred_1042")

    assert prov is not None
    assert prov.prediction_id == "pred_1042"
    assert prov.model == "tyre_degradation_xgb"
    assert prov.dataset_version in ("fastf1_v2", "fastf1_heldout_v2")
    assert prov.dataset == prov.dataset_version
    assert prov.feature_schema == "race_features_v3"
    assert prov.source_session in ("2026_hungary_race", "2026_Hungary_R")
    assert prov.confidence_interval.lower in (0.31, 0.32)
    assert prov.confidence_interval.upper == 0.61


@pytest.mark.asyncio
async def test_ask_apex_provenance_and_lineage_answers():
    """Verify Ask APEX answers provenance and decision lineage questions with grounded evidence."""
    from backend.app.intelligence.race_qa import answer_race_question

    # 1. Model Provenance query
    ans_model = await answer_race_question("Which model generated this prediction?")
    assert "tyre_degradation_xgb" in ans_model["answer"] or "XGBoost" in ans_model["answer"]

    # 2. Dataset Provenance query
    ans_data = await answer_race_question("What data trained it?")
    assert "fastf1" in ans_data["answer"].lower() or "gold" in ans_data["answer"].lower()

    # 3. Feature Schema query
    ans_feat = await answer_race_question("What feature set produced this?")
    assert "race_features_v3" in ans_feat["answer"]

    # 4. Session Provenance query
    ans_session = await answer_race_question("Which race/session supplied the evidence?")
    assert "2026_hungary_race" in ans_session["answer"] or "Silverstone" in ans_session["answer"]


def test_insufficient_context_behavior():
    """Verify APEX refuses to hallucinate and outputs INSUFFICIENT CONTEXT on missing/stale data."""
    retriever = ContextRetriever()

    # Scenario: Missing telemetry and stale weather
    bad_state = {
        "telemetry_available": False,
        "weather_stale": True,
        "opponent_missing": True,
        "model_unavailable": True,
        "counterfactual_timeout": True,
        "conflicting_models": True,
        "driver_id": 999,
    }

    report = retriever.validate_context_readiness(bad_state)
    assert report.decision == "INSUFFICIENT_CONTEXT"
    assert report.status == "INSUFFICIENT_CONTEXT"
    assert len(report.missing) >= 6
    assert "weather forecast" in report.message.lower() or "tyre state" in report.message.lower()
    assert report.action == "Request updated context / human review."
    assert report.safe_fallback_active is True

