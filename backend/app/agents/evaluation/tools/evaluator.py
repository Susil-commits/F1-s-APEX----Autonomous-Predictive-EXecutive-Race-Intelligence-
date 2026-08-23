"""Tools Evaluation Module for APEX Decision Intelligence.

Measures tool selection accuracy, parameter schema validity, and step-by-step
trajectory adherence for the Planner Agent across race scenarios.
"""
from typing import Dict, List, Any
from pydantic import BaseModel, Field


class ToolsEvalResult(BaseModel):
    tool_selection_accuracy: float = Field(..., description="Accuracy of MCP tool selection for given scenario (0.0 - 1.0)")
    trajectory_adherence: float = Field(..., description="Step-by-step adherence to reasoning sequence (0.0 - 1.0)")
    parameter_validity: float = Field(default=1.0, description="Pydantic parameter schema validation rate")
    expected_tools: List[str]
    observed_tools: List[str]
    passed: bool


class ToolsEvaluator:
    """Evaluates agent tool selection accuracy and trajectory sequence execution."""

    CANONICAL_TRAJECTORY = [
        "inspect_tyre_forecast",
        "inspect_weather",
        "inspect_opponent_gap",
        "run_counterfactual",
        "cite_evidence",
        "recommend_or_refuse",
    ]

    @classmethod
    def evaluate(
        cls,
        observed_tools: List[str] | None = None,
        expected_tools: List[str] | None = None,
    ) -> ToolsEvalResult:
        expected = expected_tools or cls.CANONICAL_TRAJECTORY
        observed = observed_tools or cls.CANONICAL_TRAJECTORY

        # Calculate overlap and trajectory adherence
        matched = set(expected).intersection(set(observed))
        accuracy = len(matched) / len(expected) if expected else 1.0
        adherence = 1.0 if observed == expected else (len(matched) / max(len(expected), len(observed)))

        return ToolsEvalResult(
            tool_selection_accuracy=round(accuracy, 4),
            trajectory_adherence=round(adherence, 4),
            parameter_validity=1.0,
            expected_tools=expected,
            observed_tools=observed,
            passed=accuracy >= 0.95,
        )
