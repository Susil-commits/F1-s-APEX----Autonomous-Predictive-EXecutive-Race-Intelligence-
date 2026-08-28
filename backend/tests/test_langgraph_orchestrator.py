"""Unit & integration tests for the LangGraph StateGraph Orchestrator."""
import pytest

from agents.agent_loop.orchestrator import (
    ApexOrchestratorState,
    apex_langgraph_orchestrator,
    build_apex_orchestrator_graph,
    conditional_risk_router,
    intent_extraction_node,
    run_orchestrator,
)
from agents.tools.mcp_tools import APEX_MCP_TOOLS, get_race_telemetry_tool


def test_mcp_tools_registration():
    """Verify that domain MCP tools are properly defined and callable."""
    assert len(APEX_MCP_TOOLS) >= 8
    res = get_race_telemetry_tool.invoke({"track_name": "silverstone"})
    assert isinstance(res, str)
    assert "current_lap" in res or "race_id" in res


def test_intent_extraction_node():
    """Verify that intent node accurately categorizes distinct race queries."""
    state1 = {"query": "Should we pit for intermediate tyres?", "chain_of_thought": []}
    res1 = intent_extraction_node(state1)
    assert res1["intent"] == "PIT_STRATEGY"

    state2 = {"query": "Is there a rain cell arriving on radar?", "chain_of_thought": []}
    res2 = intent_extraction_node(state2)
    assert res2["intent"] == "WEATHER_CHECK"

    state3 = {"query": "We have a puncture risk on the front right tyre!", "chain_of_thought": []}
    res3 = intent_extraction_node(state3)
    assert res3["intent"] == "RISK_EMERGENCY"


def test_conditional_risk_router():
    """Verify conditional branching logic based on risk level."""
    state_low: ApexOrchestratorState = {"risk_level": "LOW"}
    assert conditional_risk_router(state_low) == "mcp_tool_execution_node"

    state_high: ApexOrchestratorState = {"risk_level": "HIGH"}
    assert conditional_risk_router(state_high) == "deep_risk_mitigation_node"

    state_crit: ApexOrchestratorState = {"risk_level": "CRITICAL"}
    assert conditional_risk_router(state_crit) == "deep_risk_mitigation_node"


def test_langgraph_graph_compilation():
    """Verify that the 10-node LangGraph StateGraph compiles cleanly."""
    graph = build_apex_orchestrator_graph()
    assert graph is not None


def test_end_to_end_orchestrator_execution():
    """Verify full end-to-end traversal of all 10 LangGraph nodes."""
    result = run_orchestrator(
        query="High degradation observed on medium compound. Should we box for hards this lap?",
        race_id="test_langgraph_session",
    )

    assert isinstance(result, dict)
    assert "primary_action" in result
    assert result["primary_action"] in [
        "MAINTAIN", "PUSH", "CONSERVE", "PIT_SOFT", "PIT_MEDIUM", "PIT_HARD", "PIT_INTER", "PIT_WET"
    ]
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert result["urgency"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(result["chain_of_thought"]) >= 7
    assert len(result["radio_transmission"]) > 0
    assert len(result["lineage_hash"]) == 16
    assert result["execution_status"] == "COMPLETED"
    assert "executive_dossier" in result
