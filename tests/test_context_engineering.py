"""Unit tests for APEX Context Engineering Framework."""
import pytest
from context.assembler import (
    ContextLevel,
    HierarchicalContextAssembler,
    RaceContextBundle,
)
from context.quality import (
    ContextEvaluator,
    ContextQualityMetrics,
    calculate_quality_metrics,
)


def test_hierarchical_context_assembly_all_levels():
    assembler = HierarchicalContextAssembler(default_token_budget=512)
    bundle = assembler.assemble(
        driver_id="NOR",
        circuit_id="silverstone",
        current_lap=18,
        current_compound="C3",
        current_tyre_age=16,
        gap_ahead_s=1.8,
        gap_behind_s=0.9,
        rival_driver_ahead="VER",
        rival_driver_behind="RUS",
        track_temp_c=32.5,
        rain_probability=0.20,
        race_control_flag="GREEN",
        active_aero_mode="Z_MODE",
    )

    assert isinstance(bundle, RaceContextBundle)
    assert bundle.driver_id == "NOR"
    assert bundle.circuit_id == "silverstone"
    assert len(bundle.levels) == 4
    assert ContextLevel.L0_STRUCTURAL.value in bundle.levels
    assert ContextLevel.L1_SESSION.value in bundle.levels
    assert ContextLevel.L2_STINT.value in bundle.levels
    assert ContextLevel.L3_REALTIME.value in bundle.levels

    # Verify L2 stint computation
    l2 = bundle.levels[ContextLevel.L2_STINT.value]
    assert l2["current_compound"] == "C3"
    assert l2["tyre_age_laps"] == 16
    assert l2["current_deg_sec_per_lap"] > 0.0

    # Verify active alerts triggered (undercut threat from RUS at 0.9s)
    assert "UNDERCUT_THREAT_REAR" in bundle.active_flags
    assert bundle.is_budget_compliant
    assert bundle.token_count_estimate <= 512
    assert bundle.compression_ratio > 0.50


def test_context_token_budget_pruning():
    assembler = HierarchicalContextAssembler(default_token_budget=30)
    bundle = assembler.assemble(
        driver_id="VER",
        circuit_id="monaco",
        current_lap=25,
        token_budget=30,  # Extreme tight budget
    )
    assert bundle.is_budget_compliant
    assert bundle.token_count_estimate <= 30
    assert len(bundle.distilled_prompt) <= 30 * 4


def test_context_quality_metrics_calculation():
    assembler = HierarchicalContextAssembler()
    bundle = assembler.assemble(
        driver_id="HAM",
        circuit_id="monza",
        current_lap=20,
        current_compound="C3",
        current_tyre_age=18,
        race_control_flag="SAFETY_CAR",
    )

    metrics = calculate_quality_metrics(
        bundle_levels=bundle.levels,
        distilled_prompt=bundle.distilled_prompt,
        raw_character_count=bundle.raw_character_count,
        timestamp_utc=bundle.timestamp_utc,
        token_budget=bundle.target_budget_tokens,
    )

    assert isinstance(metrics, ContextQualityMetrics)
    assert 0.0 <= metrics.compression_ratio <= 1.0
    assert metrics.information_density_per_100_tokens > 0.0
    assert metrics.groundedness_score >= 0.50
    assert metrics.freshness_score >= 0.90
    assert metrics.hallucination_risk_score <= 0.50
    assert metrics.overall_quality_grade in ["A_OPTIMAL", "B_USABLE"]


def test_context_evaluator_gating():
    assembler = HierarchicalContextAssembler()
    bundle = assembler.assemble(
        driver_id="LEC",
        circuit_id="spa",
        current_lap=15,
        current_compound="C2",
        current_tyre_age=10,
    )

    evaluator = ContextEvaluator(min_groundedness=0.40, max_risk=0.50)
    report = evaluator.evaluate(bundle)

    assert report.driver_id == "LEC"
    assert report.circuit_id == "spa"
    assert report.is_ready_for_inference is True
    assert len(report.diagnostic_notes) >= 1

