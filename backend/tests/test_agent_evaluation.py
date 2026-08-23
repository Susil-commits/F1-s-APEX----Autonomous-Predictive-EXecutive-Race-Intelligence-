"""Tests for APEX Agent Evaluation Suite, citation grounding, and insufficient evidence handling."""
import pytest
from backend.app.agents.evaluation.eval_suite import ContextAgentEvaluator


def test_agent_decision_grounding_eval():
    """Verify evaluator validates grounded claims and flags ungrounded claims."""
    evaluator = ContextAgentEvaluator()

    valid_payload = {
        "claims": ["Tyre degradation estimated by XGBoost at +0.48s/lap", "FastF1 telemetry confirms 31 laps"],
        "citations": ["Tyre Degradation XGBoost Model Card v1.4", "FastF1 Telemetry Session: Silverstone 2023"],
    }
    res_valid = evaluator.evaluate_decision_grounding(valid_payload)
    assert res_valid["grounded"] is True
    assert res_valid["grounding_score"] == 1.0
    assert len(res_valid["unsupported_claims"]) == 0

    hallucinated_payload = {
        "claims": ["Tyre degradation estimated by XGBoost at +0.48s/lap", "Secret alien tyre compound fitted"],
        "citations": ["Tyre Degradation XGBoost Model Card v1.4"],
    }
    res_invalid = evaluator.evaluate_decision_grounding(hallucinated_payload)
    assert res_invalid["grounded"] is False
    assert res_invalid["grounding_score"] == 0.5
    assert len(res_invalid["unsupported_claims"]) == 1


def test_insufficient_evidence_safe_refusal():
    """Verify that the agent refuses to hallucinate when telemetry or weather streams are missing."""
    evaluator = ContextAgentEvaluator()

    # Case 1: Missing telemetry
    res_missing_tel = evaluator.evaluate_insufficient_evidence_handling(
        scenario="Telemetry Loss",
        available_state={},
    )
    assert res_missing_tel["passed"] is True
    assert res_missing_tel["response"]["decision"] == "INSUFFICIENT_EVIDENCE"
    assert res_missing_tel["response"]["status"] == "REFUSED_TO_HALLUCINATE"
    assert "telemetry_tyre_wear" in res_missing_tel["response"]["missing_context"]

    # Case 2: Complete state
    res_complete = evaluator.evaluate_insufficient_evidence_handling(
        scenario="Green Flag Pit Window",
        available_state={"tyre_age_laps": 31, "wear_pct": 68.4, "weather_rain_prob": 0.72},
    )
    assert res_complete["passed"] is True
    assert res_complete["response"]["decision"] == "PROCEED"


def test_full_agent_evaluation_suite():
    """Verify that the comprehensive evaluation report passes all SLA targets."""
    evaluator = ContextAgentEvaluator()
    report = evaluator.run_comprehensive_evaluation()

    assert report.overall_pass_rate_pct == 100.0
    assert report.insufficient_evidence_tests_passed is True
    assert len(report.metrics) >= 6

    # Verify key SLA metric values
    metric_map = {m.eval_name: m.measured_value for m in report.metrics}
    assert metric_map["Citation Grounding Accuracy"] >= 95.0
    assert metric_map["Unsupported Claim Rate (Hallucination)"] == 0.0
    assert metric_map["Tool Failure & Timeout Recovery"] == 100.0
    assert metric_map["Agent Decision Latency (p99)"] < 100.0
