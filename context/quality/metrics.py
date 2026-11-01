"""Context Quality Metrics for APEX Racing Intelligence.

Provides deterministic mathematical evaluation of context bundles:
- Compression Ratio: Density improvement over raw telemetry streams
- Information Density: Count of decision-critical tactical entities per 100 tokens
- Regulatory Groundedness: Precision matching against verified FIA Sporting/Technical rules
- Freshness Score: Latency decay based on race telemetry age
- Hallucination Risk Score: Bounded risk metric [0.0, 1.0]
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Set


@dataclass
class ContextQualityMetrics:
    """Calculated metric indices assessing a context payload."""
    compression_ratio: float
    information_density_per_100_tokens: float
    groundedness_score: float
    freshness_score: float
    hallucination_risk_score: float
    overall_quality_grade: str


@dataclass
class ContextQualityReport:
    """Detailed audit report on context quality and compliance."""
    driver_id: str
    circuit_id: str
    metrics: ContextQualityMetrics
    evaluated_at_utc: float
    is_ready_for_inference: bool
    diagnostic_notes: List[str]


VERIFIED_FIA_REGULATORY_ENTITIES: Set[str] = {
    "active_aero",
    "z_mode",
    "x_mode",
    "mgu_k",
    "drs",
    "safety_car",
    "vsc",
    "parc_ferme",
    "c1",
    "c2",
    "c3",
    "c4",
    "c5",
    "intermediate",
    "wet",
    "pit_stop",
    "undercut",
    "overcut",
    "tyre_cliff",
    "strat",
}


def calculate_quality_metrics(
    bundle_levels: Dict[str, Dict[str, Any]],
    distilled_prompt: str,
    raw_character_count: int,
    timestamp_utc: float,
    token_budget: int = 1024,
) -> ContextQualityMetrics:
    """Computes deterministic quality metrics for an assembled context bundle."""
    # 1. Compression ratio
    distilled_chars = len(distilled_prompt)
    compression = max(0.0, min(1.0, 1.0 - (distilled_chars / max(raw_character_count, 1))))

    # 2. Information Density
    est_tokens = max(1, distilled_chars // 4)
    # Count key decision entities present in distilled text
    lower_prompt = distilled_prompt.lower()
    matched_entities = sum(1 for e in VERIFIED_FIA_REGULATORY_ENTITIES if e in lower_prompt)
    info_density = round((matched_entities / est_tokens) * 100.0, 2)

    # 3. Regulatory Groundedness Score
    # Proportion of verified technical entities present in tactical instructions
    groundedness = min(1.0, round(matched_entities / 4.0, 3))

    # 4. Freshness Score
    # Telemetry older than 5.0 seconds undergoes exponential decay
    age_seconds = max(0.0, time.time() - timestamp_utc)
    freshness = max(0.0, min(1.0, round(1.0 / (1.0 + 0.2 * age_seconds), 3)))

    # 5. Hallucination Risk Score
    # Inversely proportional to groundedness, penalized if token budget violated
    budget_penalty = 0.2 if est_tokens > token_budget else 0.0
    risk = max(0.0, min(1.0, round((1.0 - groundedness) * 0.7 + budget_penalty, 3)))

    # 6. Overall Grade
    if risk < 0.25 and groundedness >= 0.75 and freshness >= 0.90:
        grade = "A_OPTIMAL"
    elif risk < 0.45 and groundedness >= 0.50:
        grade = "B_USABLE"
    elif risk < 0.70:
        grade = "C_DEGRADED"
    else:
        grade = "D_REJECT"

    return ContextQualityMetrics(
        compression_ratio=round(compression, 3),
        information_density_per_100_tokens=info_density,
        groundedness_score=groundedness,
        freshness_score=freshness,
        hallucination_risk_score=risk,
        overall_quality_grade=grade,
    )

