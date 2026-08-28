"""APEX Agent Domain MCP Tools for LangChain & LangGraph Orchestration."""
from __future__ import annotations

import json
from typing import Any, Optional

try:
    from langchain_core.tools import tool
except ImportError:
    try:
        from langchain.tools import tool
    except ImportError:
        def tool(*args, **kwargs):  # type: ignore
            def decorator(func):
                return func
            return decorator

from backend.app.mcp_server.server import (
    check_context_readiness,
    explain_last_decision,
    get_decision_lineage,
    get_driver_state,
    get_model_metadata,
    get_opponent_strategy,
    get_prediction_provenance,
    get_race_state,
    get_tyre_forecast,
    get_weather_forecast,
    preview_pit_strategy,
    run_counterfactual,
)


@tool
def get_race_telemetry_tool(track_name: str = "silverstone") -> str:
    """Returns current live telemetry, driver standings, tyre wear, and safety car status."""
    return get_race_state(track_name=track_name)


@tool
def explain_decision_attributions_tool(car_id: Optional[str] = None) -> str:
    """Computes exact TreeSHAP feature attributions and plain-language rationale for the active strategy decision."""
    return explain_last_decision(car_id=car_id)


@tool
def run_counterfactual_simulation_tool(proposed_action: str = "PIT_HARD", rollout_laps: int = 5) -> str:
    """Forks a counterfactual race timeline to evaluate candidate strategy actions vs baseline policy."""
    return run_counterfactual(proposed_action=proposed_action, rollout_laps=rollout_laps)


@tool
def get_tyre_degradation_forecast_tool(car_id: Optional[str] = None, laps_ahead: int = 10) -> str:
    """Forecasts tyre degradation trajectory, remaining useful life (RUL), and cliff breach probabilities."""
    return get_tyre_forecast(car_id=car_id, laps_ahead=laps_ahead)


@tool
def get_weather_forecast_tool() -> str:
    """Returns multi-lap predictive precipitation radar, wetness index, and tyre crossover thresholds."""
    return get_weather_forecast()


@tool
def get_opponent_intelligence_tool() -> str:
    """Analyzes all rival cars, predicting pit window probabilities and undercut threats."""
    return get_opponent_strategy()


@tool
def get_model_governance_card_tool(model_key: str = "tyre_degradation_xgb") -> str:
    """Returns formal model governance card, training dataset lineage, and held-out validation metrics."""
    return get_model_metadata(model_key=model_key)


@tool
def get_decision_lineage_tool(decision_id: str = "decision:box_lap_32_car_4") -> str:
    """Traces 10-stage upstream telemetry, feature sets, predictive models, and safe RL masks for a decision."""
    return get_decision_lineage(decision_id=decision_id)


@tool
def check_context_readiness_tool(
    telemetry_available: bool = True,
    weather_stale: bool = False,
    opponent_missing: bool = False,
) -> str:
    """Validates real-time context completeness and triggers refusal protocol under missing data."""
    return check_context_readiness(
        telemetry_available=telemetry_available,
        weather_stale=weather_stale,
        opponent_missing=opponent_missing,
    )


APEX_MCP_TOOLS = [
    get_race_telemetry_tool,
    explain_decision_attributions_tool,
    run_counterfactual_simulation_tool,
    get_tyre_degradation_forecast_tool,
    get_weather_forecast_tool,
    get_opponent_intelligence_tool,
    get_model_governance_card_tool,
    get_decision_lineage_tool,
    check_context_readiness_tool,
]
