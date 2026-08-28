"""Model Context Protocol (MCP) Server for APEX Race Intelligence.

Exposes APEX race digital twin telemetry, TreeSHAP decision explanations,
grounded decision history RAG, counterfactual timeline forking, Monte Carlo simulations,
and scenario injection as official Model Context Protocol (MCP) tools.
Usable directly from Claude Desktop, Claude Code, Antigravity, or any MCP client.
"""

import asyncio
import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.intelligence.race_qa import answer_race_question
from backend.app.intelligence.shap_explainer import TreeSHAPExplainer
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import SafetyCarStatus, TrackCondition
from backend.app.strategy.counterfactual import CounterfactualChecker
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.strategy.monte_carlo import MonteCarloEngine

# Initialize the MCP Server instance
mcp = MCPServer("apex-race-intelligence")

# Shared in-memory active simulator reference for MCP calls
_mcp_sim: RaceSimulator | None = None


def get_or_create_sim(track_name: str = "silverstone", seed: int = 42) -> RaceSimulator:
    """Gets or initializes the active digital twin simulation instance."""
    global _mcp_sim
    if _mcp_sim is None:
        _mcp_sim = RaceSimulator(track_name=track_name, seed=seed, enable_dynamic_weather=True)
        _mcp_sim.step()
    return _mcp_sim


@mcp.tool()
def get_race_state(track_name: str = "silverstone") -> str:
    """Returns the current live telemetry and strategic state of the APEX race digital twin.
    
    Includes lap count, weather conditions, safety car status, driver standings,
    player tyre wear %, tyre compound, gap to leader, and current RL strategy decision.
    """
    sim = get_or_create_sim(track_name=track_name)
    state = sim.get_state()
    player = sim.get_player_car()
    leader = sim.cars[0] if sim.cars else None

    summary = {
        "race_id": state.race_id,
        "track": {
            "name": sim.track.name,
            "total_laps": sim.track.total_laps,
            "lap_distance_km": sim.track.lap_distance_km,
        },
        "current_lap": state.current_lap,
        "is_finished": state.is_finished,
        "weather": {
            "condition": state.weather.condition.value,
            "rain_intensity": round(state.weather.rain_intensity, 2),
            "track_temp_c": round(state.weather.track_temp_c, 1),
            "air_temp_c": round(state.weather.air_temp_c, 1),
            "rain_probability_next_5_laps": round(state.weather.rain_probability_next_5_laps, 2),
        },
        "safety_car": {
            "status": state.safety_car.value,
            "laps_remaining": state.safety_car_laps_remaining,
        },
        "leader": {
            "driver": leader.driver_name if leader else "Unknown",
            "team": leader.team_name if leader else "Unknown",
            "lap_time_s": round(leader.last_lap_time_s, 3) if leader and leader.last_lap_time_s is not None else 0.0,
        },
        "player_car": {
            "car_id": player.car_id if player else "None",
            "driver": player.driver_name if player else "None",
            "position": player.position if player else 0,
            "tyre_compound": player.tyre_compound.value if player else "None",
            "tyre_wear_pct": round(player.tyre_wear_pct, 1) if player else 0.0,
            "tyre_age_laps": player.tyre_age_laps if player else 0,
            "gap_to_leader_s": round(player.gap_to_leader_s, 2) if player else 0.0,
            "pit_count": player.pit_count if player else 0,
            "cliff_reached": player.tyre_cliff_reached if player else False,
        },
        "standings_top5": [
            {
                "pos": c.position,
                "driver": c.driver_name,
                "compound": c.tyre_compound.value,
                "gap_s": round(c.gap_to_leader_s, 2),
                "wear_pct": round(c.tyre_wear_pct, 1),
            }
            for c in sorted(sim.cars, key=lambda x: x.position)[:5]
        ],
    }
    return json.dumps(summary, indent=2)


@mcp.tool()
def explain_last_decision(car_id: str | None = None) -> str:
    """Computes exact TreeSHAP feature attributions and natural-language explanations for the active decision.
    
    Decomposes the DQN strategy policy into additive Shapley values, highlighting the top factors
    (e.g., tyre degradation rate, weather forecast, gap to leader, pit window timing).
    """

    sim = get_or_create_sim()
    state = sim.get_state()
    features = FeatureBuilder.extract_features(state, target_car_id=car_id)

    explainer = TreeSHAPExplainer.get_instance()
    explanation = explainer.explain(features)

    player = sim.get_player_car()
    dqn_agent = DQNAgent()
    dqn_action, q_margin = dqn_agent.predict_action(features)

    top_feats = explanation.get("top_features", [])
    primary_factors = [f["feature"].replace("_", " ").title() for f in top_feats[:3]]

    detailed_attributions = [
        {
            "feature": f["feature"],
            "feature_value": f["feature_value"],
            "attribution_phi": f["shap_value"],
            "direction": "FAVORS_ACTION" if f["shap_value"] > 0 else "DISFAVORS_ACTION",
            "abs_magnitude": f["abs_magnitude"],
        }
        for f in top_feats
    ]

    confidence = min(0.98, max(0.65, 0.75 + q_margin * 0.15))
    urgency = "HIGH" if (player and (player.tyre_cliff_reached or player.tyre_wear_pct > 75.0)) else ("MEDIUM" if q_margin > 0.5 else "LOW")
    action_name = dqn_action.value if hasattr(dqn_action, "value") else str(dqn_action)

    result = {
        "race_id": state.race_id,
        "lap": state.current_lap,
        "target_car": player.driver_name if player else "Player",
        "recommended_action": action_name,
        "confidence_score": round(confidence, 2),
        "urgency": urgency,
        "base_expected_value": explanation.get("base_value", 0.0),
        "primary_driving_factors": primary_factors,
        "detailed_shap_attributions": detailed_attributions,
        "plain_language_rationale": (
            f"On Lap {state.current_lap}, recommended {action_name} "
            f"with {int(confidence * 100)}% confidence ({urgency} urgency). "
            f"Primary factor: {primary_factors[0] if primary_factors else 'Stint window management'}."
        ),
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def ask_race_history(question: str, race_id: str | None = None, top_k: int = 5) -> str:
    """Answers natural language questions about historical race strategy decisions grounded in persisted database logs.
    
    Uses dense sentence embeddings (all-MiniLM-L6-v2) and cosine similarity retrieval over
    decision log records, returning grounded answers with verifiable source citations.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        raw_result = loop.run_until_complete(answer_race_question(query=question, race_id=race_id, top_k=top_k))
    else:
        raw_result = loop.run_until_complete(answer_race_question(query=question, race_id=race_id, top_k=top_k))

    formatted = {
        "question": question,
        "answer": raw_result.get("answer", "No answer found."),
        "model_used": raw_result.get("model_used", "deterministic_grounded_fallback"),
        "retrieved_count": raw_result.get("retrieved_count", 0),
        "sources": raw_result.get("sources", []),
    }
    return json.dumps(formatted, indent=2)


@mcp.tool()
def preview_pit_strategy(proposed_action: str = "PIT_SOFT", rollout_laps: int = 5) -> str:
    """Forks a counterfactual simulation from the current race state to evaluate an alternative pit action.
    
    Simulates N future laps under the proposed directive vs the baseline policy, projecting
    track position delta, lap time differences, tyre degradation trajectory, and overall tactical advantage.
    """
    sim = get_or_create_sim()
    state = sim.get_state()

    result = CounterfactualChecker.fork_timeline(
        historical_state=state,
        proposed_action=proposed_action,
        rollout_laps=rollout_laps,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def evaluate_monte_carlo(rollouts: int = 500, target_car_id: str | None = None) -> str:
    """Executes stochastic Monte Carlo forward simulations across candidate strategy paths.
    
    Models dynamic weather transitions, safety car probability, and opponent tyre degradation over
    hundreds of stochastic rollouts, returning win probabilities and finish position distributions.
    """
    sim = get_or_create_sim()
    state = sim.get_state()

    results = MonteCarloEngine.run_simulation(
        state=state,
        num_rollouts=min(rollouts, 2000),
        target_car_id=target_car_id,
    )
    return json.dumps(results, indent=2)


@mcp.tool()
def trigger_scenario(scenario_type: str, intensity: float = 0.8, laps: int = 4) -> str:
    """Injects live race incidents and weather phenomena directly into the digital twin simulation.
    
    Supported scenario types:
    - TORRENTIAL_RAIN / DAMP_TRACK / DRY_TRACK
    - SAFETY_CAR / VSC / GREEN_FLAG
    - PUNCTURE (sudden tyre damage cliff)
    - CLEAR_HAZARDS
    """
    sim = get_or_create_sim()
    scen = scenario_type.upper()

    if scen in ("TORRENTIAL_RAIN", "RAIN", "WET"):
        sim.inject_weather(TrackCondition.WET, rain_intensity=intensity or 0.85)
    elif scen in ("DAMP_TRACK", "DAMP", "LIGHT_RAIN"):
        sim.inject_weather(TrackCondition.DAMP, rain_intensity=intensity or 0.35)
    elif scen in ("DRY_TRACK", "DRY"):
        sim.inject_weather(TrackCondition.DRY, rain_intensity=0.0)
    elif scen in ("SAFETY_CAR", "FULL_SC", "SC"):
        sim.inject_safety_car(SafetyCarStatus.SAFETY_CAR, laps=laps or 4)
    elif scen in ("VSC", "VIRTUAL_SAFETY_CAR"):
        sim.inject_safety_car(SafetyCarStatus.VSC, laps=laps or 3)
    elif scen in ("GREEN_FLAG", "CLEAR_SC"):
        sim.inject_safety_car(SafetyCarStatus.NONE, laps=0)
    elif scen in ("PUNCTURE", "TYRE_DAMAGE", "CLIFF"):
        player = sim.get_player_car()
        car_id = player.car_id if player else "car_04"
        sim.inject_puncture(car_id=car_id, wear_delta=50.0)
    elif scen in ("CLEAR_HAZARDS", "RESET_WEATHER"):
        sim.clear_hazards()
    else:
        return json.dumps({"error": f"Unknown scenario type '{scenario_type}'"}, indent=2)

    state = sim.get_state()
    return json.dumps({
        "status": "scenario_applied",
        "scenario": scen,
        "lap": state.current_lap,
        "track_condition": state.weather.condition.value,
        "rain_intensity": state.weather.rain_intensity,
        "safety_car": state.safety_car.value,
    }, indent=2)


@mcp.tool()
def get_agentic_strategy_plan(track_name: str = "silverstone", target_car_id: str | None = None) -> str:
    """Executes multi-step Agentic Race Strategist reasoning with chain-of-thought and contingencies.
    
    Synthesizes Neural RL (DQN) policy, TreeSHAP force attributions, Monte Carlo 1,000-rollout
    probabilities, FastF1 tyre degradation curves, and tactical contingency plans into an
    actionable executive pit-wall strategy dossier.
    """
    sim = get_or_create_sim(track_name=track_name)
    state = sim.get_state()
    from backend.app.intelligence.agentic_strategist import get_agentic_strategist
    strategist = get_agentic_strategist()
    plan = strategist.formulate_strategy(state=state, target_car_id=target_car_id)
    return plan.model_dump_json(indent=2)


@mcp.tool()
def check_model_health() -> str:
    """Audits the APEX Model Registry, verifies SHA-256 weight hashes, and reports model drift status.
    
    Checks live integrity across all 8 models (DQN, PPO, FastF1 Tyre Model, PINN Residuals,
    TreeSHAP Surrogates, Isolation Forest Vehicle Health, and Dense Embeddings). Returns
    per-model status, benchmark performance targets, file checksums, and drift flags.
    """
    from backend.app.intelligence.model_registry import ModelRegistry
    report = ModelRegistry.verify_all_models()
    return json.dumps(report, indent=2)


@mcp.tool()
def get_sim_to_real_divergence_audit() -> str:
    """Audits APEX Sim-to-Real tactical divergence against real historical F1 Grand Prix pit-wall decisions.
    
    Returns counterfactual delta time advantages, AI tactical agreement rates, and blunder prevention
    metrics across real-world historical decision points (e.g. Silverstone 2022, Monaco 2022, Zandvoort 2023).
    """
    from pathlib import Path
    report_path = Path(__file__).resolve().parent.parent.parent / "eval" / "sim_to_real_divergence_report.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            return f.read()

    # Generate fresh divergence audit if report does not exist
    from backend.eval.historical_replay_eval import audit_historical_decisions
    report = audit_historical_decisions(output_path=report_path)
    return json.dumps(report, indent=2)


@mcp.tool()
def get_driver_state(car_id: str | None = None) -> str:
    """Returns detailed telemetry, driving mode, tyre wear, and biometric pressure state for a driver."""
    sim = get_or_create_sim()
    car = next((c for c in sim.cars if c.car_id == car_id or (car_id is None and c.is_player)), sim.cars[0] if sim.cars else None)
    if not car:
        return json.dumps({"error": f"Driver {car_id} not found"}, indent=2)
    return json.dumps({
        "car_id": car.car_id,
        "driver_name": car.driver_name,
        "team_name": car.team_name,
        "position": car.position,
        "tyre_compound": car.tyre_compound.value,
        "tyre_age_laps": car.tyre_age_laps,
        "tyre_wear_pct": round(car.tyre_wear_pct, 1),
        "driving_mode": car.driving_mode.value,
        "gap_to_leader_s": round(car.gap_to_leader_s, 2),
        "last_lap_time_s": round(car.last_lap_time_s, 3) if car.last_lap_time_s else 0.0,
        "cliff_reached": car.tyre_cliff_reached,
        "pit_count": car.pit_count,
    }, indent=2)


@mcp.tool()
def get_tyre_forecast(car_id: str | None = None, laps_ahead: int = 10) -> str:
    """Forecasts tyre degradation, remaining useful life (RUL), and cliff breach probabilities."""
    sim = get_or_create_sim()
    car = next((c for c in sim.cars if c.car_id == car_id or (car_id is None and c.is_player)), sim.cars[0] if sim.cars else None)
    if not car:
        return json.dumps({"error": f"Driver {car_id} not found"}, indent=2)
    from backend.app.intelligence.tyre_model import TyreModel
    rul = TyreModel.predict_remaining_useful_life(car.tyre_compound, car.tyre_wear_pct, car.tyre_age_laps, car.driving_mode)
    pit_win = TyreModel.calculate_pit_window(car, sim.track, sim.weather)
    return json.dumps({
        "car_id": car.car_id,
        "current_compound": car.tyre_compound.value,
        "current_wear_pct": round(car.tyre_wear_pct, 1),
        "laps_remaining_to_cliff": rul.get("estimated_laps_remaining", 0),
        "cliff_probability": rul.get("cliff_probability", 0.0),
        "pit_window": pit_win,
        "projected_degradation_laps_ahead": [
            {
                "lap": sim.current_lap + i,
                "projected_wear_pct": min(100.0, round(car.tyre_wear_pct + i * 2.4, 1)),
                "projected_delta_s": round(0.15 + (i * 0.12), 2),
            }
            for i in range(1, laps_ahead + 1)
        ],
    }, indent=2)


@mcp.tool()
def get_weather_forecast() -> str:
    """Returns predictive multi-lap rain probabilities, track wetness index, and tyre crossover thresholds."""
    sim = get_or_create_sim()
    from backend.app.intelligence.weather_model import WeatherPredictor
    probs = WeatherPredictor.predict_rain_probabilities(sim.weather)
    return json.dumps({
        "current_condition": sim.weather.condition.value,
        "rain_intensity": round(sim.weather.rain_intensity, 2),
        "track_temp_c": round(sim.weather.track_temp_c, 1),
        "air_temp_c": round(sim.weather.air_temp_c, 1),
        "forecast_rain_probabilities": probs,
    }, indent=2)


@mcp.tool()
def get_opponent_strategy() -> str:
    """Analyzes all rival cars, predicting pit window probabilities, undercut threats, and strategic intent."""
    sim = get_or_create_sim()
    player = sim.get_player_car()
    from backend.app.intelligence.opponent_model import OpponentIntelligenceEngine
    opponents = OpponentIntelligenceEngine.predict_all_opponents(
        sim.cars, player.car_id if player else None, sim.track, sim.weather, sim.current_lap
    )
    return json.dumps({
        "current_lap": sim.current_lap,
        "total_opponents_analyzed": len(opponents),
        "opponents": [op.model_dump() for op in opponents],
    }, indent=2)


@mcp.tool()
def run_counterfactual(proposed_action: str = "PIT_NOW", rollout_laps: int = 5) -> str:
    """Forks alternative counterfactual simulation to evaluate what happens if we pit now vs stay out."""
    sim = get_or_create_sim()
    state = sim.get_state()
    result = CounterfactualChecker.fork_timeline(
        historical_state=state,
        proposed_action=proposed_action,
        rollout_laps=rollout_laps,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def explain_strategy(car_id: str | None = None) -> str:
    """Computes exact TreeSHAP force attributions and plain-language explanation for current race decision."""
    return explain_last_decision(car_id=car_id)


@mcp.tool()
def get_strategy_history(race_id: str | None = None) -> str:
    """Retrieves full decision explanation history and audit trail from database."""
    from backend.app.twin.store import store
    sim = get_or_create_sim()
    target_race_id = race_id or sim.get_state().race_id
    decisions = store.get_decision_history(target_race_id)
    return json.dumps({
        "race_id": target_race_id,
        "decision_count": len(decisions),
        "decisions": decisions,
    }, indent=2)


@mcp.tool()
def get_model_prediction(car_id: str | None = None) -> str:
    """Returns real-time 28-dimensional feature vector and multi-model prediction suite output."""
    sim = get_or_create_sim()
    state = sim.get_state()
    features = FeatureBuilder.extract_features(state, target_car_id=car_id)
    dqn_agent = DQNAgent()
    dqn_action, q_margin = dqn_agent.predict_action(features)
    from backend.app.strategy.hybrid_decision_engine import hybrid_decision_aggregator
    hybrid_dec = hybrid_decision_aggregator.evaluate_decision(state, target_car_id=car_id)
    return json.dumps({
        "race_id": state.race_id,
        "lap": state.current_lap,
        "feature_vector_dim": len(features),
        "dqn_action": dqn_action.value if hasattr(dqn_action, "value") else str(dqn_action),
        "q_value_margin": round(q_margin, 3),
        "hybrid_recommendation": hybrid_dec.recommendation.value,
        "confidence_score": hybrid_dec.confidence_score,
        "primary_factors": hybrid_dec.primary_factors,
    }, indent=2)


@mcp.tool()
def get_system_ablation_study() -> str:
    """Returns the 9-configuration System Ablation study (FULL vs NO_RL vs NO_WEATHER vs NO_SAFETY, etc.)."""
    from backend.eval.ablation_runner import AblationRunner
    try:
        report = AblationRunner.run(total_races=3, seed=42)
        return json.dumps(report, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_model_metadata(model_key: str = "tyre_degradation_xgb") -> str:
    """Returns the formal governance card, training dataset, feature schema, and held-out metrics for a model."""
    from backend.app.context.metadata.model_metadata import get_model_metadata, list_all_model_metadata
    if model_key == "all":
        return json.dumps([m.model_dump() for m in list_all_model_metadata()], indent=2)
    card = get_model_metadata(model_key)
    if not card:
        return json.dumps({"error": f"Model '{model_key}' not found in registry"}, indent=2)
    return json.dumps(card.model_dump(), indent=2)


@mcp.tool()
def get_decision_lineage(decision_id: str = "decision:box_lap_32_car_4") -> str:
    """Traces upstream telemetry, feature sets, predictive models, uncertainty bounds, and safe RL masks for a decision."""
    from backend.app.context.retrieval.context_retriever import context_retriever
    trail = context_retriever.get_decision_evidence(decision_id)
    if not trail:
        return json.dumps({"error": f"Lineage trail for '{decision_id}' not found"}, indent=2)
    return json.dumps(trail.model_dump(), indent=2)


@mcp.tool()
def get_prediction_provenance(prediction_id: str = "pred_1042") -> str:
    """Answers: Which model generated this? What data trained it? What feature schema was used?
    
    Returns structured provenance metadata attached to any prediction in APEX, including model name,
    version, training dataset, feature schema, session ID, and calibrated 95% confidence intervals.
    """
    from backend.app.context.retrieval.context_retriever import context_retriever
    record = context_retriever.get_prediction_provenance(prediction_id)
    if not record:
        return json.dumps({"error": f"Prediction provenance for '{prediction_id}' not found"}, indent=2)
    return json.dumps(record.model_dump() if hasattr(record, "model_dump") else record.dict(), indent=2)


@mcp.tool()
def check_context_readiness(
    telemetry_available: bool = True,
    weather_stale: bool = False,
    opponent_missing: bool = False,
    model_unavailable: bool = False,
    counterfactual_timeout: bool = False,
    conflicting_models: bool = False,
    driver_id: int = 4,
) -> str:
    """Validates real-time context completeness, fresh weather streams, opponent states, and model health.
    
    Enforces the zero-hallucination 'INSUFFICIENT CONTEXT' protocol if any essential context is missing or stale.
    """
    from backend.app.context.retrieval.context_retriever import context_retriever
    state_payload = {
        "telemetry_available": telemetry_available,
        "weather_stale": weather_stale,
        "opponent_missing": opponent_missing,
        "model_unavailable": model_unavailable,
        "counterfactual_timeout": counterfactual_timeout,
        "conflicting_models": conflicting_models,
        "driver_id": driver_id,
        "tyre_wear_pct": 45.0 if telemetry_available else None,
        "weather_condition": "DRY" if not weather_stale else None,
    }
    result = context_retriever.validate_context_readiness(state_payload)
    if hasattr(result, "model_dump"):
        return json.dumps(result.model_dump(), indent=2)
    elif hasattr(result, "dict"):
        return json.dumps(result.dict(), indent=2)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_context_quality() -> str:
    """Returns real-time context completeness, lineage coverage, citation grounding, and trust metrics."""
    from context.evaluation.quality_metrics import context_quality_engine
    return json.dumps(context_quality_engine.compute_quality_report().model_dump(), indent=2)


@mcp.tool()
def get_decision_lineage(decision_id: str = "decision:box_lap_32_car_4") -> str:
    """Returns the full 7-stage upstream decision lineage trail for any tactical decision.
    
    Includes telemetry sources, 28-D features, invoked models, predictions, counterfactuals, and guardrails.
    """
    from context.retrieval.context_retriever import context_retriever
    trail = context_retriever.get_decision_evidence(decision_id)
    if not trail:
        return json.dumps({"error": f"Lineage for decision '{decision_id}' not found."}, indent=2)
    return json.dumps(trail.model_dump(), indent=2)


@mcp.tool()
def get_context_graph() -> str:
    """Returns the complete serialized 14-entity APEX Race Intelligence Context Graph DAG."""
    from context.lineage.tracer import lineage_tracer
    graph = lineage_tracer.get_graph()
    return json.dumps(graph.to_schema().model_dump(), indent=2)


@mcp.tool()
def get_model_metadata_card(model_id: str = "tyre_degradation_xgb") -> str:
    """Returns the formal model governance card, training dataset lineage, and held-out metrics."""
    from context.metadata.model_metadata import get_model_metadata
    card = get_model_metadata(model_id)
    if not card:
        return json.dumps({"error": f"Model '{model_id}' not found in registry."}, indent=2)
    return json.dumps(card.model_dump(), indent=2)


@mcp.tool()
def get_dataset_metadata_card(dataset_id: str = "fastf1_2018_2024_gold") -> str:
    """Returns the formal dataset ingestion card, circuit coverage, schema fields, and quality score."""
    from context.metadata.dataset_metadata import get_dataset_metadata
    card = get_dataset_metadata(dataset_id)
    if not card:
        return json.dumps({"error": f"Dataset '{dataset_id}' not found in registry."}, indent=2)
    return json.dumps(card.model_dump(), indent=2)


@mcp.tool()
def explain_recommendation_lineage(decision_id: str = "decision:box_lap_32_car_4") -> str:
    """Answers 'Why did APEX recommend this strategy?' with natural-language verifiable context lineage."""
    from context.retrieval.context_retriever import context_retriever
    return context_retriever.explain_recommendation(decision_id)


@mcp.tool()
def get_system_metrics() -> str:
    """Returns a real-time observability snapshot of APEX Prometheus telemetry and health counters."""
    try:
        from prometheus_client import REGISTRY, generate_latest
        raw_metrics = generate_latest(REGISTRY).decode("utf-8")

        lines = [line for line in raw_metrics.splitlines() if line.startswith("apex_")]
        parsed_metrics: dict[str, Any] = {}
        for line in lines:
            if " " in line:
                key, val = line.rsplit(" ", 1)
                try:
                    parsed_metrics[key] = float(val) if "." in val else int(val)
                except ValueError:
                    parsed_metrics[key] = val

        return json.dumps({
            "status": "HEALTHY",
            "apex_metrics": parsed_metrics,
            "raw_metric_count": len(lines),
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)}, indent=2)


@mcp.tool()
def run_langgraph_orchestrator(
    query: str = "Should we pit this lap?",
    race_id: str | None = None,
    target_car_id: str | None = None,
) -> str:
    """Executes the 10-node LangGraph StateGraph Autonomous Orchestrator with conditional risk branching.
    
    Traverses: Intent -> Metadata -> Telemetry -> Anomaly -> Tactical Ranking -> Risk Branch -> Tools -> Reasoning -> Safe RL -> Response.
    """
    from agents.agent_loop.orchestrator import run_orchestrator
    result = run_orchestrator(query=query, race_id=race_id, target_car_id=target_car_id)
    return json.dumps(result, indent=2)


@mcp.tool()
def query_hybrid_rag(
    question: str,
    race_id: str | None = None,
    top_k: int = 5,
) -> str:
    """Queries APEX historical decision logs using FAISS dense vector inner-product search fused with BM25 via RRF."""
    from backend.app.intelligence.hybrid_mission_rag import hybrid_rag_engine
    results = hybrid_rag_engine.search(query=question, race_id=race_id, top_k=top_k)
    return json.dumps({
        "query": question,
        "retrieval_method": "FAISS_IndexFlatIP + BM25_Okapi (RRF Fusion)",
        "results_count": len(results),
        "documents": [
            {
                "lap": r[0].get("lap"),
                "directive": r[0].get("recommendation"),
                "confidence": r[0].get("confidence_score"),
                "urgency": r[0].get("urgency"),
                "rrf_score": r[1],
                "explanation": r[0].get("explanation_payload", {}),
            }
            for r in results
        ],
    }, indent=2)


@mcp.tool()
def get_circuit_lora_adapters() -> str:
    """Returns available circuit-specific Parameter-Efficient LoRA adapters (Monaco, Monza, Spa, Silverstone) and evaluation metrics."""
    from pathlib import Path
    report_file = Path(__file__).resolve().parent.parent.parent / "eval" / "circuit_lora_benchmark_report.json"
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return f.read()
    from backend.training.circuit_lora_benchmark import run_multi_circuit_lora_benchmark
    return json.dumps(run_multi_circuit_lora_benchmark(save_report=False), indent=2)


if __name__ == "__main__":
    # Standard stdio MCP server execution
    mcp.run()



