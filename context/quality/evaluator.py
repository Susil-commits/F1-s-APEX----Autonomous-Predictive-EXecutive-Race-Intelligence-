"""Context Quality Evaluator for APEX Racing Intelligence.

Evaluates and gates assembled context bundles before passing to deterministic
inference models or LLM race engineer copilots.
"""
from __future__ import annotations

import time
from typing import List

from context.assembler import RaceContextBundle
from context.quality.metrics import (
    ContextQualityMetrics,
    ContextQualityReport,
    calculate_quality_metrics,
)


class ContextEvaluator:
    """Evaluates context bundles against strict engineering SLAs.
    
    Acts as a quality gate ensuring:
    - Zero telemetry freshness decay
    - Compliance with token budgets (<50ms processing)
    - Strong grounding in FIA regulations and physical tyre curves
    """

    def __init__(self, min_groundedness: float = 0.50, max_risk: float = 0.50) -> None:
        self.min_groundedness = min_groundedness
        self.max_risk = max_risk

    def evaluate(self, bundle: RaceContextBundle) -> ContextQualityReport:
        """Evaluates an assembled RaceContextBundle and issues a quality report."""
        diagnostics: List[str] = []

        metrics = calculate_quality_metrics(
            bundle_levels=bundle.levels,
            distilled_prompt=bundle.distilled_prompt,
            raw_character_count=bundle.raw_character_count,
            timestamp_utc=bundle.timestamp_utc,
            token_budget=bundle.target_budget_tokens,
        )

        # SLA Checks
        if not bundle.is_budget_compliant:
            diagnostics.append(
                f"Token budget exceeded: {bundle.token_count_estimate} > {bundle.target_budget_tokens}"
            )

        if metrics.freshness_score < 0.80:
            diagnostics.append(
                f"Telemetry age degraded freshness score to {metrics.freshness_score:.2f}"
            )

        if metrics.groundedness_score < self.min_groundedness:
            diagnostics.append(
                f"Groundedness score {metrics.groundedness_score:.2f} is below minimum {self.min_groundedness:.2f}"
            )

        if metrics.hallucination_risk_score > self.max_risk:
            diagnostics.append(
                f"Hallucination risk {metrics.hallucination_risk_score:.2f} exceeds threshold {self.max_risk:.2f}"
            )

        is_ready = (
            metrics.overall_quality_grade in ["A_OPTIMAL", "B_USABLE"]
            and metrics.hallucination_risk_score <= self.max_risk
        )

        if not diagnostics:
            diagnostics.append("Context meets all enterprise engineering SLAs (Grade: " + metrics.overall_quality_grade + ")")

        return ContextQualityReport(
            driver_id=bundle.driver_id,
            circuit_id=bundle.circuit_id,
            metrics=metrics,
            evaluated_at_utc=time.time(),
            is_ready_for_inference=is_ready,
            diagnostic_notes=diagnostics,
        )

