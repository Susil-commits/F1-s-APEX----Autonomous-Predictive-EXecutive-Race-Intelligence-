"""Unit tests for the APEX Automated Evaluation Harness & Self-Healing Agent Loop."""
import json
import pytest
from pathlib import Path

from backend.eval.run_eval import (
    load_baselines,
    check_thresholds,
    run_full_evaluation,
    evaluate_shap_surrogate,
    evaluate_tyre_model_calibration,
)
from backend.app.intelligence.agent_loop import get_self_healing_agent, AgentHealingAction


def test_baseline_schema_and_thresholds():
    """Validates structure and completeness of baseline_scores.json."""
    baselines = load_baselines()
    assert "baselines" in baselines
    assert baselines["version"] == "1.0.0"
    
    expected_metrics = [
        "dqn_win_rate_pct",
        "dqn_podium_rate_pct",
        "dqn_avg_gap_to_winner_s",
        "dqn_avg_blown_tyre_laps",
        "shap_surrogate_fidelity_r2",
        "tyre_model_fastf1_r2",
        "rag_citation_precision_pct",
        "rag_refusal_accuracy_pct",
    ]
    
    for metric in expected_metrics:
        assert metric in baselines["baselines"], f"Missing metric: {metric}"
        spec = baselines["baselines"][metric]
        assert "target" in spec
        assert "description" in spec
        assert ("min_allowable" in spec) or ("max_allowable" in spec)


def test_regression_detection_logic():
    """Validates that check_thresholds accurately flags threshold breaches."""
    baselines = load_baselines()
    
    # Passing dummy metrics
    good_metrics = {
        "dqn_win_rate_pct": 95.0,
        "dqn_podium_rate_pct": 100.0,
        "dqn_avg_gap_to_winner_s": 0.1,
        "dqn_avg_blown_tyre_laps": 0.0,
        "shap_surrogate_fidelity_r2": 0.88,
        "tyre_model_fastf1_r2": 0.60,
        "rag_citation_precision_pct": 100.0,
        "rag_refusal_accuracy_pct": 100.0,
    }
    items, has_reg = check_thresholds(good_metrics, baselines)
    assert has_reg is False
    assert all(i["status"] == "PASS" for i in items)
    
    # Failing dummy metrics (win rate dropped below 80%)
    bad_metrics = {**good_metrics, "dqn_win_rate_pct": 50.0}
    items, has_reg = check_thresholds(bad_metrics, baselines)
    assert has_reg is True
    failing_item = next(i for i in items if i["metric"] == "dqn_win_rate_pct")
    assert failing_item["status"] == "REGRESSION"


def test_eval_pillars_standalone():
    """Validates individual execution of SHAP and tyre calibration pillars."""
    shap_res = evaluate_shap_surrogate()
    assert shap_res["status"] in ("PASS", "DRIFT_DETECTED")
    assert shap_res["shap_surrogate_fidelity_r2"] >= 0.70
    
    tyre_res = evaluate_tyre_model_calibration()
    assert tyre_res["status"] == "PASS"
    assert tyre_res["tyre_model_fastf1_r2"] >= 0.30


def test_eval_harness_full_run():
    """Validates end-to-end evaluation harness execution and report output."""
    report, has_reg = run_full_evaluation(verbose=False)
    
    assert report["run_id"].startswith("EVAL-APEX-")
    assert report["metrics_evaluated"] == 8
    assert report["overall_status"] == "PASS"
    assert has_reg is False
    assert len(report["results"]) == 8


def test_self_healing_agent_cycle():
    """Validates autonomous self-healing agent verification cycle."""
    agent = get_self_healing_agent()
    action = agent.check_and_heal(auto_redistill=False)
    
    assert isinstance(action, AgentHealingAction)
    assert action.status in ("HEALTHY", "HEALED", "DRIFT_FLAGGED")
    assert len(action.plain_language_debrief) > 0
