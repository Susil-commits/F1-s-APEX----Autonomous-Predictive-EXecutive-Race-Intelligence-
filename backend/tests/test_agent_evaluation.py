"""Tests for APEX Agent Evaluation Suite, citation grounding, trajectory evaluation, and insufficient evidence refusal."""
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


def test_all_seven_insufficient_evidence_refusal_scenarios():
    """Verify that APEX refuses to hallucinate across all 7 edge-case scenarios:
    1. missing_telemetry
    2. stale_weather
    3. missing_opponent_state
    4. model_unavailable
    5. counterfactual_timeout
    6. conflicting_model_outputs
    7. unknown_driver
    """
    evaluator = ContextAgentEvaluator()

    # 1. Missing Telemetry
    res1 = evaluator.evaluate_insufficient_evidence_handling("missing_telemetry", {})
    assert res1["passed"] is True
    assert res1["refusal_triggered"] is True
    assert res1["response"]["decision"] == "INSUFFICIENT_EVIDENCE"
    assert res1["response"]["status"] == "REFUSED_TO_HALLUCINATE"
    assert "current tyre state" in res1["response"]["message"]
    assert res1["response"]["safe_fallback_active"] is True

    # 2. Stale Weather
    res2 = evaluator.evaluate_insufficient_evidence_handling("stale_weather", {"tyre_age_laps": 25, "weather_stale": True})
    assert res2["passed"] is True
    assert res2["refusal_triggered"] is True
    assert "latest weather forecast" in res2["response"]["message"]

    # 3. Missing Opponent State
    res3 = evaluator.evaluate_insufficient_evidence_handling("missing_opponent_state", {"tyre_age_laps": 25, "weather_rain_prob": 0.1, "opponent_missing": True})
    assert res3["passed"] is True
    assert res3["refusal_triggered"] is True
    assert "opponent gap" in res3["response"]["message"]

    # 4. Model Unavailable
    res4 = evaluator.evaluate_insufficient_evidence_handling("model_unavailable", {"tyre_age_laps": 25, "weather_rain_prob": 0.1, "model_unavailable": True})
    assert res4["passed"] is True
    assert res4["refusal_triggered"] is True
    assert "tyre_degradation_xgb" in res4["response"]["message"]

    # 5. Counterfactual Timeout
    res5 = evaluator.evaluate_insufficient_evidence_handling("counterfactual_timeout", {"tyre_age_laps": 25, "weather_rain_prob": 0.1, "counterfactual_timeout": True})
    assert res5["passed"] is True
    assert res5["refusal_triggered"] is True
    assert "counterfactual simulation" in res5["response"]["message"]

    # 6. Conflicting Model Outputs
    res6 = evaluator.evaluate_insufficient_evidence_handling("conflicting_model_outputs", {"tyre_age_laps": 25, "weather_rain_prob": 0.1, "conflicting_models": True})
    assert res6["passed"] is True
    assert res6["refusal_triggered"] is True
    assert "consensus resolution" in res6["response"]["message"]

    # 7. Unknown Driver
    res7 = evaluator.evaluate_insufficient_evidence_handling("unknown_driver", {"driver_id": 999, "unknown_driver": True})
    assert res7["passed"] is True
    assert res7["refusal_triggered"] is True
    assert "Driver #999 not on grid" in res7["response"]["message"]


def test_agent_trajectory_evaluation():
    """Verify trajectory-level evaluation checks step-by-step reasoning discipline."""
    evaluator = ContextAgentEvaluator()
    traj = evaluator.evaluate_strategy_trajectory("Should we pit this lap?")

    assert traj.passed is True
    assert traj.trajectory_adherence_pct == 100.0
    assert traj.all_steps_grounded is True
    assert "inspect_tyre_forecast" in traj.observed_trajectory
    assert "inspect_weather" in traj.observed_trajectory
    assert "inspect_opponent_gap" in traj.observed_trajectory
    assert "run_counterfactual" in traj.observed_trajectory
    assert "cite_evidence" in traj.observed_trajectory
    assert "recommend_or_refuse" in traj.observed_trajectory


def test_full_agent_evaluation_suite_comprehensive():
    """Verify that the comprehensive evaluation report passes all SLA targets."""
    evaluator = ContextAgentEvaluator()
    report = evaluator.run_comprehensive_evaluation()

    assert report.overall_pass_rate_pct == 100.0
    assert report.insufficient_evidence_tests_passed is True
    assert len(report.metrics) >= 8
    assert len(report.trajectories_evaluated) >= 1

    metric_map = {m.eval_name: m.measured_value for m in report.metrics}
    assert metric_map["Tool Selection Accuracy"] >= 95.0
    assert metric_map["Citation Grounding Accuracy"] >= 95.0
    assert metric_map["Unsupported Claim Rate (Hallucination)"] == 0.0
    assert metric_map["Missing Context Rate (Unflagged Gaps)"] == 0.0
    assert metric_map["Lineage Coverage"] >= 90.0
    assert metric_map["Evidence Completeness"] >= 95.0
    assert metric_map["Tool Failure Recovery"] == 100.0
    assert metric_map["Agent Decision Latency (p99)"] < 100.0


def test_grounding_evaluator_submodule():
    """Verify grounding/evaluator computes unsupported_claim_rate, citation_grounding, evidence_completeness."""
    from backend.app.agents.evaluation.grounding import GroundingEvaluator

    valid = GroundingEvaluator.evaluate({
        "claims": ["Tyre degradation estimated by XGBoost at +0.48s/lap", "FastF1 telemetry confirms 31 laps"],
        "citations": ["Tyre Degradation XGBoost Model Card v1.4", "FastF1 Telemetry Session: Silverstone 2023"],
    })
    assert valid.grounded is True
    assert valid.grounding_score == 1.0
    assert valid.unsupported_claim_rate == 0.0
    assert valid.evidence_completeness >= 0.95

    hallucinated = GroundingEvaluator.evaluate({
        "claims": ["Tyre degradation estimated by XGBoost at +0.48s/lap", "Fabricated mystery compound"],
        "citations": ["Tyre Degradation XGBoost Model Card v1.4"],
    })
    assert hallucinated.grounded is False
    assert hallucinated.unsupported_claim_rate == 0.5
    assert len(hallucinated.unsupported_claims) == 1


def test_context_evaluator_submodule():
    """Verify context/evaluator computes context_relevance, missing_context_detection, lineage_coverage."""
    from backend.app.agents.evaluation.context import ContextEvaluator

    # Ready state
    ready = ContextEvaluator.evaluate({"tyre_wear_pct": 50.0, "weather_condition": "DRY"})
    assert ready.context_relevance >= 0.90
    assert ready.missing_context_detected is False
    assert ready.lineage_coverage >= 0.90
    assert ready.lineage_verified is True

    # Missing context state
    missing = ContextEvaluator.evaluate({"telemetry_available": False, "weather_stale": True})
    assert missing.missing_context_detected is True
    assert len(missing.missing_elements) >= 2


def test_tools_evaluator_submodule():
    """Verify tools/evaluator computes tool_selection_accuracy and trajectory_adherence."""
    from backend.app.agents.evaluation.tools import ToolsEvaluator

    res = ToolsEvaluator.evaluate()
    assert res.passed is True
    assert res.tool_selection_accuracy == 1.0
    assert res.trajectory_adherence == 1.0
    assert res.parameter_validity == 1.0


def test_failure_evaluator_submodule():
    """Verify failure/evaluator computes tool_failure_recovery and zero-hallucination refusal."""
    from backend.app.agents.evaluation.failure import FailureEvaluator

    refusal = FailureEvaluator.evaluate_refusal({"telemetry_available": False})
    assert refusal.passed is True
    assert refusal.refusal_triggered is True
    assert refusal.safe_fallback_enforced is True

    timeout = FailureEvaluator.evaluate_tool_timeout_recovery("run_counterfactual", 100.0)
    assert timeout["recovered"] is True
    assert timeout["safe_rl_mask_enforced"] is True


def test_regression_evaluator_submodule():
    """Verify regression/evaluator computes decision_consistency, latency SLAs, and single vs multi-agent consensus."""
    from backend.app.agents.evaluation.regression import RegressionEvaluator

    reg = RegressionEvaluator.evaluate()
    assert reg.passed is True
    assert reg.decision_consistency >= 0.95
    assert reg.latency_ms_p99 < 100.0
    assert reg.latency_sla_passed is True
    assert "single_planner_agent_mcp" in reg.single_vs_multi_agent_comparison
    assert "multi_agent_committee_consensus" in reg.single_vs_multi_agent_comparison
    assert reg.single_vs_multi_agent_comparison["single_planner_agent_mcp"]["mean_latency_p99_ms"] == 42.0

