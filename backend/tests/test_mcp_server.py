"""Unit tests for APEX Model Context Protocol (MCP) server and tools."""
import json

from backend.app.mcp_server.server import (
    ask_race_history,
    check_model_health,
    evaluate_monte_carlo,
    explain_last_decision,
    get_agentic_strategy_plan,
    get_race_state,
    get_sim_to_real_divergence_audit,
    get_system_metrics,
    mcp,
    preview_pit_strategy,
    trigger_scenario,
)


def test_mcp_server_initialization():
    """Validates that MCP server is instantiated and all tools are registered."""
    tools = mcp._tool_manager.list_tools()
    tool_names = [t.name for t in tools]

    assert "get_race_state" in tool_names
    assert "explain_last_decision" in tool_names
    assert "ask_race_history" in tool_names
    assert "preview_pit_strategy" in tool_names
    assert "evaluate_monte_carlo" in tool_names
    assert "trigger_scenario" in tool_names
    assert "get_agentic_strategy_plan" in tool_names
    assert "check_model_health" in tool_names
    assert "get_sim_to_real_divergence_audit" in tool_names
    assert "get_system_metrics" in tool_names


def test_mcp_get_race_state():
    """Validates live telemetry snapshot structure and data types."""
    res_str = get_race_state(track_name="silverstone")
    data = json.loads(res_str)

    assert "race_id" in data
    assert "track" in data
    assert data["track"]["name"] == "Silverstone Circuit"
    assert "current_lap" in data
    assert "weather" in data
    assert "condition" in data["weather"]
    assert "safety_car" in data
    assert "player_car" in data
    assert "tyre_wear_pct" in data["player_car"]
    assert "standings_top5" in data
    assert len(data["standings_top5"]) <= 5


def test_mcp_explain_last_decision():
    """Validates TreeSHAP explainability attributions and plain language rationale."""
    res_str = explain_last_decision()
    data = json.loads(res_str)

    assert "race_id" in data
    assert "lap" in data
    assert "recommended_action" in data
    assert "confidence_score" in data
    assert "urgency" in data
    assert "detailed_shap_attributions" in data
    assert isinstance(data["detailed_shap_attributions"], list)
    assert len(data["detailed_shap_attributions"]) > 0
    assert "plain_language_rationale" in data


def test_mcp_preview_pit_strategy():
    """Validates counterfactual timeline simulation."""
    res_str = preview_pit_strategy(proposed_action="PIT_SOFT", rollout_laps=3)
    data = json.loads(res_str)

    assert "proposed_action" in data
    assert data["proposed_action"] == "PIT_SOFT"
    assert "rollout_laps" in data
    assert "baseline_timeline" in data or "baseline_trajectory" in data or "advantage" in data or "summary" in data or "delta_seconds" in data


def test_mcp_evaluate_monte_carlo():
    """Validates stochastic Monte Carlo rollout engine."""
    res_str = evaluate_monte_carlo(rollouts=100)
    data = json.loads(res_str)

    assert "total_rollouts" in data
    assert "recommended_strategy" in data
    assert "strategies" in data
    assert len(data["strategies"]) >= 2
    assert "win_probability_pct" in data["strategies"][0]


def test_mcp_trigger_scenario_safety_car():
    """Validates incident injection into active twin."""
    res_str = trigger_scenario(scenario_type="SAFETY_CAR", intensity=0.8, laps=3)
    data = json.loads(res_str)

    assert data["status"] == "scenario_applied"
    assert data["scenario"] == "SAFETY_CAR"
    assert data["safety_car"] == "SAFETY_CAR"


def test_mcp_trigger_scenario_weather():
    """Validates weather injection into active twin."""
    res_str = trigger_scenario(scenario_type="TORRENTIAL_RAIN", intensity=0.9, laps=4)
    data = json.loads(res_str)

    assert data["status"] == "scenario_applied"
    assert data["scenario"] == "TORRENTIAL_RAIN"
    assert data["track_condition"] == "WET"


def test_mcp_ask_race_history():
    """Validates grounded decision history RAG question answering."""
    res_str = ask_race_history(question="Why did we pit on lap 23?", top_k=3)
    data = json.loads(res_str)

    assert "question" in data
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "sources" in data
    assert "model_used" in data


def test_mcp_get_agentic_strategy_plan():
    """Validates agentic multi-step reasoning plan execution."""
    res_str = get_agentic_strategy_plan(track_name="silverstone")
    data = json.loads(res_str)

    assert "executive_summary" in data
    assert "primary_action" in data
    assert "chain_of_thought" in data
    assert len(data["chain_of_thought"]) >= 4
    assert "confidence_score" in data
    assert "policy_entropy" in data
    assert "shapley_drivers" in data
    assert "contingencies" in data
    assert "monte_carlo_metrics" in data


def test_mcp_check_model_health():
    """Validates Model Registry health check and SHA-256 integrity reporting."""
    res_str = check_model_health()
    data = json.loads(res_str)

    assert "audit_timestamp_utc" in data
    assert "total_models" in data
    assert data["total_models"] >= 8
    assert "models" in data
    assert "apex_dqn" in data["models"]


def test_mcp_get_sim_to_real_divergence_audit():
    """Validates sim-to-real historical divergence replay audit output."""
    res_str = get_sim_to_real_divergence_audit()
    data = json.loads(res_str)

    assert "audit_run_id" in data
    assert "case_studies" in data
    assert len(data["case_studies"]) >= 3
    assert "aggregate_metrics" in data
    assert data["status"] == "PASS"


def test_mcp_get_system_metrics():
    """Validates Prometheus runtime metrics snapshot extraction."""
    res_str = get_system_metrics()
    data = json.loads(res_str)

    assert "status" in data
    assert data["status"] == "HEALTHY"
    assert "apex_metrics" in data
    assert "raw_metric_count" in data


def test_mcp_run_langgraph_orchestrator():
    """Validates LangGraph orchestrator tool invocation via MCP."""
    from backend.app.mcp_server.server import run_langgraph_orchestrator
    res_str = run_langgraph_orchestrator(query="Check tyre wear and pit window")
    data = json.loads(res_str)

    assert "primary_action" in data
    assert "chain_of_thought" in data
    assert "execution_status" in data
    assert data["execution_status"] == "COMPLETED"


def test_mcp_query_hybrid_rag():
    """Validates FAISS + BM25 RRF hybrid retrieval tool via MCP."""
    from backend.app.mcp_server.server import query_hybrid_rag
    res_str = query_hybrid_rag(question="safety car pit stop")
    data = json.loads(res_str)

    assert "retrieval_method" in data
    assert "FAISS_IndexFlatIP + BM25_Okapi" in data["retrieval_method"]
    assert "documents" in data


