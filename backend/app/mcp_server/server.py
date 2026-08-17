"""Model Context Protocol (MCP) Server for APEX Race Intelligence.

Exposes APEX race digital twin telemetry, TreeSHAP decision explanations,
grounded decision history RAG, counterfactual timeline forking, Monte Carlo simulations,
and scenario injection as official Model Context Protocol (MCP) tools.
Usable directly from Claude Desktop, Claude Code, Antigravity, or any MCP client.
"""

import asyncio
import json

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
            "lap_time_s": round(leader.last_lap_time_s, 3) if leader else 0.0,
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
    
    confidence = min(0.98, max(0.65, 0.75 + float(q_margin) * 0.15))
    urgency = "HIGH" if (player and (player.tyre_cliff_reached or player.tyre_wear_pct > 75.0)) else ("MEDIUM" if float(q_margin) > 0.5 else "LOW")
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


if __name__ == "__main__":
    # Standard stdio MCP server execution
    mcp.run()
