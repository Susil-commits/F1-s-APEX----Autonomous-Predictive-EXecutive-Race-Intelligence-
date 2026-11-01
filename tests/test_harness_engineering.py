"""Unit tests for APEX Harness Engineering Framework."""
import pytest
from agents.harness import AgentExecutionHarness, AgentExecutionResult
from agents.evaluation.metamorphic import MetamorphicTestHarness
from agents.evaluation.race_replay import (
    RaceScenarioReplayHarness,
    ReplayBenchmarkReport,
)
from context.assembler import HierarchicalContextAssembler


def test_agent_execution_harness_happy_path():
    assembler = HierarchicalContextAssembler()
    bundle = assembler.assemble(
        driver_id="VER",
        circuit_id="silverstone",
        current_lap=18,
        current_compound="C3",
        current_tyre_age=15,
        gap_behind_s=0.8,
    )

    harness = AgentExecutionHarness(max_timeout_ms=200.0, provider_name="happy_path_provider")
    result = harness.execute(bundle)

    assert isinstance(result, AgentExecutionResult)
    assert result.success is True
    assert result.fallback_invoked is False
    assert result.action in ["COVER_UNDERCUT", "BOX_NOW", "STAY_OUT"]
    assert result.latency_ms < 200.0
    assert result.cost_cap_compute_units > 0.0
    assert result.audit_event_id is not None


def test_agent_execution_harness_timeout_and_fallback():
    assembler = HierarchicalContextAssembler()
    bundle = assembler.assemble(
        driver_id="NOR",
        circuit_id="monza",
        current_lap=22,
    )

    # Low timeout limit: 0.001ms forces timeout fallback
    harness = AgentExecutionHarness(max_timeout_ms=0.0001, provider_name="timeout_test_provider")

    def slow_agent(_):
        import time
        time.sleep(0.005)
        return {"recommended_action": "BOX_NOW"}

    result = harness.execute(bundle, decision_fn=slow_agent)

    assert result.success is True
    assert result.fallback_invoked is True
    assert result.error_message == "TIMEOUT_EXCEEDED"
    assert result.action in ["STAY_OUT", "BOX_NOW"]


def test_race_scenario_replay_benchmark():
    replay_harness = RaceScenarioReplayHarness()
    agent_harness = AgentExecutionHarness()

    report = replay_harness.run_benchmark(agent_harness)

    assert isinstance(report, ReplayBenchmarkReport)
    assert report.total_scenarios == 5
    assert report.matched_scenarios >= 4
    assert report.alignment_accuracy_pct >= 80.0
    assert report.all_passed_sla is True
    assert report.mean_latency_ms < 50.0


def test_metamorphic_invariance_properties():
    meta = MetamorphicTestHarness()

    # 1. Monotonic tyre degradation
    deg_res = meta.test_tyre_age_monotonic_degradation("C3")
    assert deg_res.passed is True
    assert deg_res.violations_detected == 0

    # 2. Undercut gap sensitivity boundary
    undercut_res = meta.test_undercut_gap_sensitivity()
    assert undercut_res.passed is True
    assert undercut_res.violations_detected == 0

    # 3. Safety car opportunism
    sc_res = meta.test_safety_car_opportunism()
    assert sc_res.passed is True
    assert sc_res.violations_detected == 0
