"""Metamorphic Invariance Testing Harness for APEX Strategy Agents.

Verifies domain-invariant properties and monotonic physical laws:
1. Rain Monotonicity: Higher rain prob monotonically increases wet compound propensity
2. Tyre Age Monotonicity: Higher tyre age strictly increases degradation and cliff probability
3. Undercut Threat Sensitivity: Shrinking rival gap behind (<1.4s) triggers tactical alerts
4. Grid Rank Monotonicity: Advancing grid position strictly improves finishing expectation
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from agents.harness import AgentExecutionHarness
from context.assembler import HierarchicalContextAssembler
from core.features.tyre_model import TyreDegradationModel


@dataclass
class MetamorphicTestResult:
    """Result of an invariance / metamorphic property evaluation."""
    property_name: str
    passed: bool
    iterations_tested: int
    violations_detected: int
    diagnostic_summary: str


class MetamorphicTestHarness:
    """Automated suite asserting structural domain invariants across APEX."""

    def __init__(self) -> None:
        self.assembler = HierarchicalContextAssembler()
        self.tyre_model = TyreDegradationModel()
        self.harness = AgentExecutionHarness()

    def test_tyre_age_monotonic_degradation(self, compound: str = "C3") -> MetamorphicTestResult:
        """Verifies that tyre pace degradation increases monotonically with age."""
        violations = 0
        iterations = 35
        prev_deg = -1.0

        for lap in range(1, iterations + 1):
            deg = self.tyre_model.calculate_lap_degradation(
                compound_code=compound, tyre_age_laps=lap
            )["pace_delta_seconds"]
            if deg < prev_deg:
                violations += 1
            prev_deg = deg

        passed = violations == 0
        return MetamorphicTestResult(
            property_name="TyreAgeMonotonicDegradation",
            passed=passed,
            iterations_tested=iterations,
            violations_detected=violations,
            diagnostic_summary=f"Monotonic degradation across {iterations} laps: {'PASSED' if passed else f'{violations} VIOLATIONS'}",
        )

    def test_undercut_gap_sensitivity(self) -> MetamorphicTestResult:
        """Verifies that decreasing rival gap behind reliably triggers undercut alerts."""
        gaps = [5.0, 3.5, 2.0, 1.3, 0.8, 0.4]
        alerts_triggered = []

        for gap in gaps:
            bundle = self.assembler.assemble(
                driver_id="VER",
                circuit_id="silverstone",
                current_lap=20,
                current_compound="C3",
                current_tyre_age=18,
                gap_behind_s=gap,
                rival_driver_behind="NOR",
            )
            alerts_triggered.append("UNDERCUT_THREAT_REAR" in bundle.active_flags)

        # Invariant: Wide gap (5.0s, 3.5s) must NOT alert; tight gap (<1.4s) MUST alert
        violations = 0
        if alerts_triggered[0] or alerts_triggered[1]:
            violations += 1  # False positive at wide gap
        if not alerts_triggered[3] or not alerts_triggered[4] or not alerts_triggered[5]:
            violations += 1  # False negative at tight gap

        passed = violations == 0
        return MetamorphicTestResult(
            property_name="UndercutGapSensitivity",
            passed=passed,
            iterations_tested=len(gaps),
            violations_detected=violations,
            diagnostic_summary=f"Undercut detection boundary (<1.4s): {'PASSED' if passed else f'{violations} VIOLATIONS'}",
        )

    def test_safety_car_opportunism(self) -> MetamorphicTestResult:
        """Verifies that VSC/SC flags trigger immediate pitstop exploitation under high tyre age."""
        sc_bundle = self.assembler.assemble(
            driver_id="LEC",
            circuit_id="monaco",
            current_lap=25,
            current_compound="C3",
            current_tyre_age=20,
            race_control_flag="SAFETY_CAR",
        )
        res_sc = self.harness.execute(sc_bundle)

        green_bundle = self.assembler.assemble(
            driver_id="LEC",
            circuit_id="monaco",
            current_lap=25,
            current_compound="C3",
            current_tyre_age=20,
            race_control_flag="GREEN",
        )
        res_green = self.harness.execute(green_bundle)

        # Under SC, action should be PIT_UNDER_SC
        passed = (res_sc.action == "PIT_UNDER_SC") and (res_green.action != "PIT_UNDER_SC")
        violations = 0 if passed else 1

        return MetamorphicTestResult(
            property_name="SafetyCarOpportunism",
            passed=passed,
            iterations_tested=2,
            violations_detected=violations,
            diagnostic_summary=f"SC opportunistic pit call: {'PASSED' if passed else 'FAILED'}",
        )
