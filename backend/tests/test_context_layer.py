"""Exhaustive Test Suite for the APEX Context Layer.

Validates:
  1. All 14 Context Entities (Race, Session, Driver, Team, TelemetryStream, FeatureSet, Model,
     Prediction, StrategyCandidate, Counterfactual, Decision, Outcome, WeatherSource, Tool).
  2. The 7-Stage Core Lineage Chain:
     Telemetry -> FeatureSet -> Model -> Prediction -> StrategyCandidate -> Counterfactual -> Decision -> Outcome.
  3. Upstream & Downstream Lineage Traversal.
  4. DecisionLineageTrail synthesis & Agent "Why did APEX recommend this strategy?" explanations.
  5. Model & Dataset Governance Metadata Cards and Checksums.
  6. Empirical Context Quality Metrics & Refusal Protocols under Missing Context.
"""
import pytest
from context import (
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
    RaceContextGraph,
    build_default_race_context_graph,
    LineageTracer,
    lineage_tracer,
    ContextRetriever,
    context_retriever,
    ContextQualityEngine,
    context_quality_engine,
    MODEL_REGISTRY,
    get_model_metadata,
    list_all_model_metadata,
    DATASET_REGISTRY,
    get_dataset_metadata,
    list_all_dataset_metadata,
)
from backend.app.intelligence.race_qa import answer_race_question


def test_14_context_entities_instantiation():
    """Verify all 14 context entities instantiate correctly with strongly-typed Pydantic validation."""
    # 1. Race
    race = RaceEntity(id="race:silverstone_2024", name="British Grand Prix", circuit="Silverstone", year=2024, total_laps=52)
    assert race.circuit == "Silverstone"
    assert race.total_laps == 52

    # 2. Session
    session = SessionEntity(id="session:silverstone_2024_r", race_id=race.id, session_type="Race", current_lap=32)
    assert session.session_type == "Race"
    assert session.current_lap == 32

    # 3. Driver
    driver = DriverEntity(id="driver:car_4", car_id=4, driver_name="Lando Norris", driver_code="NOR", team_name="McLaren")
    assert driver.car_id == 4
    assert driver.driver_name == "Lando Norris"

    # 4. Team
    team = TeamEntity(id="team:mclaren", name="McLaren Formula 1 Team", pit_crew_avg_stop_s=2.45)
    assert team.pit_crew_avg_stop_s == 2.45

    # 5. TelemetryStream
    stream = TelemetryStreamEntity(id="stream:car_4_lap_32", car_id=4, sampling_frequency_hz=60.0, quality_score=99.8)
    assert stream.sampling_frequency_hz == 60.0
    assert len(stream.channels) >= 5

    # 6. FeatureSet
    features = FeatureSetEntity(id="features:car_4_lap_32", schema_version="race_features_v3", dimensionality=28, extraction_latency_ms=0.0245)
    assert features.dimensionality == 28
    assert features.extraction_latency_ms < 0.10

    # 7. Model
    model = ModelEntity(
        id="model:tyre_xgb_v1.4", name="Tyre XGBoost", version="v1.4",
        algorithm_family="XGBoost", training_dataset="fastf1_gold", metrics={"r2": 0.8342}
    )
    assert model.metrics["r2"] > 0.80

    # 8. Prediction
    pred = PredictionEntity(
        id="pred:tyre_deg_32", model_id=model.id, target_variable="lap_time_bleed_s",
        predicted_value=0.48, confidence_interval_95=[0.32, 0.64], unit="s/lap"
    )
    assert pred.predicted_value == 0.48
    assert pred.confidence_interval_95 == [0.32, 0.64]

    # 9. StrategyCandidate
    candidate = StrategyCandidateEntity(id="strategy:box_32", action="PIT_NOW", target_compound="HARD", traffic_rejoin_gap_s=4.1)
    assert candidate.action == "PIT_NOW"
    assert candidate.traffic_rejoin_gap_s == 4.1

    # 10. Counterfactual
    cf = CounterfactualEntity(id="cf:rollout_32", total_rollouts=1000, risk_variance=0.08)
    assert cf.total_rollouts == 1000
    assert len(cf.branches) >= 3

    # 11. Decision
    decision = DecisionEntity(
        id="decision:box_32", car_id=4, lap=32, action_recommended="BOX_THIS_LAP",
        confidence_score=0.81, urgency="HIGH", reason="Degradation cliff near; clear rejoin buffer."
    )
    assert decision.action_recommended == "BOX_THIS_LAP"
    assert decision.confidence_score == 0.81

    # 12. Outcome
    outcome = OutcomeEntity(id="outcome:finish_car_4", decision_id=decision.id, actual_finish_position=1, points_awarded=25)
    assert outcome.actual_finish_position == 1
    assert outcome.points_awarded == 25

    # 13. WeatherSource
    weather = WeatherSourceEntity(id="weather:silverstone_radar", station_name="Silverstone Doppler Radar", rain_probability_next_5_laps=0.72)
    assert weather.rain_probability_next_5_laps == 0.72

    # 14. Tool
    tool = ToolEntity(id="tool:safe_rl_mask", name="Safe RL Guardrail", tool_type="Guardrail", constraints_enforced=["MANDATORY_2_COMPOUND"])
    assert tool.tool_type == "Guardrail"


def test_7_stage_core_lineage_chain():
    """Verify the 7-stage linear lineage chain connects and traverses end-to-end:
    Telemetry -> FeatureSet -> Model -> Prediction -> StrategyCandidate -> Counterfactual -> Decision -> Outcome.
    """
    graph = RaceContextGraph("test-lineage-chain")

    # Add 8 nodes
    graph.add_node(ContextNode(id="telemetry:1", name="60Hz Telemetry", entity_type=EntityType.TELEMETRY_STREAM))
    graph.add_node(ContextNode(id="features:1", name="28-D Features", entity_type=EntityType.FEATURE_SET))
    graph.add_node(ContextNode(id="model:1", name="XGBoost Tyre ML", entity_type=EntityType.MODEL))
    graph.add_node(ContextNode(id="pred:1", name="Degradation Forecast", entity_type=EntityType.PREDICTION))
    graph.add_node(ContextNode(id="candidate:1", name="Undercut Window", entity_type=EntityType.STRATEGY_CANDIDATE))
    graph.add_node(ContextNode(id="counterfactual:1", name="Monte Carlo 1k Rollouts", entity_type=EntityType.COUNTERFACTUAL))
    graph.add_node(ContextNode(id="decision:1", name="BOX THIS LAP", entity_type=EntityType.DECISION))
    graph.add_node(ContextNode(id="outcome:1", name="P1 Race Victory", entity_type=EntityType.OUTCOME))

    # Connect the explicit 7-stage chain
    graph.build_lineage_chain(
        telemetry_id="telemetry:1",
        features_id="features:1",
        model_id="model:1",
        prediction_id="pred:1",
        candidate_id="candidate:1",
        counterfactual_id="counterfactual:1",
        decision_id="decision:1",
        outcome_id="outcome:1",
    )

    # 1. Test Upstream Lineage Traversal from Decision (should reach Telemetry)
    upstream = graph.get_upstream_lineage("decision:1", max_depth=10)
    upstream_ids = {n.id for n in upstream}
    assert "counterfactual:1" in upstream_ids
    assert "candidate:1" in upstream_ids
    assert "pred:1" in upstream_ids
    assert "model:1" in upstream_ids
    assert "features:1" in upstream_ids
    assert "telemetry:1" in upstream_ids

    # 2. Test Downstream Impact Traversal from Telemetry (should reach Decision and Outcome)
    downstream = graph.get_downstream_impact("telemetry:1", max_depth=10)
    downstream_ids = {n.id for n in downstream}
    assert "features:1" in downstream_ids
    assert "model:1" in downstream_ids
    assert "pred:1" in downstream_ids
    assert "candidate:1" in downstream_ids
    assert "counterfactual:1" in downstream_ids
    assert "decision:1" in downstream_ids
    assert "outcome:1" in downstream_ids


def test_explain_recommendation_why_did_apex_recommend():
    """Verify ContextRetriever.explain_recommendation produces exact structured lineage response."""
    retriever = ContextRetriever()
    explanation = retriever.explain_recommendation("decision:box_lap_32_car_4")

    assert "RECOMMENDATION" in explanation
    assert "Pit now" in explanation
    assert "PREDICTION" in explanation
    assert "UNCERTAINTY" in explanation
    assert "COUNTERFACTUALS" in explanation
    assert "MODELS" in explanation
    assert "DATA" in explanation
    assert "LINEAGE" in explanation
    assert "Telemetry" in explanation
    assert "Features" in explanation
    assert "Decision" in explanation


@pytest.mark.asyncio
async def test_agent_why_did_apex_recommend_strategy():
    """Verify that asking 'Why did APEX recommend this strategy?' returns full context lineage."""
    res = await answer_race_question("Why did APEX recommend this strategy?")

    assert "answer" in res
    ans = res["answer"]
    assert "RECOMMENDATION" in ans or "lineage" in ans.lower()
    assert "Pit now" in ans or "box" in ans.lower()
    assert "LINEAGE" in ans or "telemetry" in ans.lower()


@pytest.mark.asyncio
async def test_agent_provenance_questions():
    """Verify Ask APEX answers the 4 key provenance questions."""
    # 1. Which model generated this?
    res1 = await answer_race_question("Which model generated this prediction?")
    assert "tyre_degradation_xgb" in res1["answer"]
    assert "v1.4" in res1["answer"]

    # 2. Which dataset produced it?
    res2 = await answer_race_question("Which dataset produced it?")
    assert "fastf1" in res2["answer"].lower()

    # 3. Which feature version was used?
    res3 = await answer_race_question("Which feature version was used?")
    assert "race_features_v3" in res3["answer"]

    # 4. Which race/session was the source?
    res4 = await answer_race_question("Which race/session was the source of evidence?")
    assert "2026_hungary_race" in res4["answer"] or "session" in res4["answer"].lower()


def test_model_and_dataset_registries():
    """Verify model and dataset metadata cards have full governance metadata."""
    models = list_all_model_metadata()
    assert len(models) >= 5

    xgb = get_model_metadata("tyre_degradation_xgb")
    assert xgb is not None
    assert xgb.version == "v1.4"
    assert xgb.metrics["r2"] > 0.80
    assert xgb.sha256_hash is not None

    datasets = list_all_dataset_metadata()
    assert len(datasets) >= 3

    gold = get_dataset_metadata("fastf1_2018_2024_gold")
    assert gold is not None
    assert gold.data_quality_score >= 95.0


def test_context_quality_metrics_engine():
    """Verify context quality report computes all 5 trust dimensions."""
    engine = ContextQualityEngine()
    report = engine.compute_quality_report()

    assert 0.0 <= report.metadata_completeness <= 100.0
    assert 0.0 <= report.lineage_coverage <= 100.0
    assert 0.0 <= report.citation_grounding_accuracy <= 100.0
    assert 0.0 <= report.stale_context_rate <= 100.0
    assert 0.0 <= report.unsupported_claim_rate <= 100.0
    assert report.context_freshness_ms_p99 < 50.0


def test_context_readiness_and_refusal_protocol():
    """Verify that missing context triggers structured refusal."""
    retriever = ContextRetriever()
    bad_state = {
        "telemetry_available": False,
        "weather_stale": True,
        "opponent_missing": True,
    }
    res = retriever.validate_context_readiness(bad_state)
    assert res.decision == "INSUFFICIENT_CONTEXT"
    assert res.safe_fallback_active is True
    assert len(res.missing) >= 2
