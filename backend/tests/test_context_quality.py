"""Tests for APEX Context Quality Engine and trust metrics."""
import pytest
from backend.app.context.quality.quality_metrics import ContextQualityEngine


def test_context_quality_metrics_computation():
    """Verify context quality report computes completeness, lineage coverage, and grounding."""
    engine = ContextQualityEngine()
    report = engine.compute_quality_report()

    assert report.metadata_completeness >= 90.0
    assert report.lineage_coverage >= 90.0
    assert report.citation_grounding_accuracy >= 90.0
    assert report.stale_context_rate < 5.0
    assert report.unsupported_claim_rate == 0.0
    assert report.context_freshness_ms_p99 <= 20.0


def test_context_quality_update_cycle():
    """Verify recording decision evals updates running metrics."""
    engine = ContextQualityEngine()
    initial_report = engine.compute_quality_report()

    # Record 10 perfect evaluations
    for _ in range(10):
        engine.record_decision_eval(
            has_full_lineage=True,
            is_stale=False,
            grounded_claims=5,
            total_claims=5,
            unsupported_claims=0,
        )

    updated_report = engine.compute_quality_report()
    assert updated_report.unsupported_claim_rate == 0.0
    assert updated_report.citation_grounding_accuracy >= initial_report.citation_grounding_accuracy
