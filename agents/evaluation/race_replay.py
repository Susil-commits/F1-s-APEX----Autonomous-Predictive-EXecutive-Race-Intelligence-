"""Race Scenario Replay Harness for APEX Strategy Evaluation.

Provides deterministic historical and counterfactual scenario replaying
to quantitatively evaluate agent tactical decisions against ground-truth F1 race outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agents.harness import AgentExecutionHarness
from context.assembler import HierarchicalContextAssembler


@dataclass
class ScenarioOutcome:
    """Evaluation result for an individual scenario replay."""
    scenario_id: str
    scenario_name: str
    ground_truth_action: str
    agent_action: str
    matched: bool
    latency_ms: float
    tactical_rationale: str


@dataclass
class ReplayBenchmarkReport:
    """Summary metrics of a race scenario replay benchmark run."""
    total_scenarios: int
    matched_scenarios: int
    alignment_accuracy_pct: float
    mean_latency_ms: float
    max_latency_ms: float
    all_passed_sla: bool
    outcomes: List[ScenarioOutcome]


HISTORICAL_RACE_SCENARIOS: List[Dict[str, Any]] = [
    {
        "scenario_id": "monaco_2024_sc_lap25",
        "name": "Monaco GP Lap 25 Safety Car Pit Window",
        "circuit_id": "monaco",
        "driver_id": "LEC",
        "current_lap": 25,
        "current_compound": "C3",
        "current_tyre_age": 24,
        "race_control_flag": "SAFETY_CAR",
        "rain_probability": 0.05,
        "gap_ahead_s": 2.4,
        "gap_behind_s": 6.8,
        "ground_truth_action": "PIT_UNDER_SC",
    },
    {
        "scenario_id": "silverstone_2024_rain_crossover",
        "name": "Silverstone GP Lap 18 Heavy Rain Shower",
        "circuit_id": "silverstone",
        "driver_id": "HAM",
        "current_lap": 18,
        "current_compound": "C3",
        "current_tyre_age": 17,
        "race_control_flag": "GREEN",
        "rain_probability": 0.85,
        "gap_ahead_s": 1.2,
        "gap_behind_s": 4.5,
        "ground_truth_action": "BOX_NOW",
    },
    {
        "scenario_id": "monza_2024_undercut_defense",
        "name": "Monza GP Lap 22 Undercut Threat from Russell",
        "circuit_id": "monza",
        "driver_id": "NOR",
        "current_lap": 22,
        "current_compound": "C3",
        "current_tyre_age": 21,
        "race_control_flag": "GREEN",
        "rain_probability": 0.0,
        "gap_ahead_s": 3.1,
        "gap_behind_s": 0.9,
        "rival_behind": "RUS",
        "ground_truth_action": "COVER_UNDERCUT",
    },
    {
        "scenario_id": "spa_2024_pirelli_cliff",
        "name": "Spa GP Lap 29 Severe Tyre Cliff Drop-off",
        "circuit_id": "spa",
        "driver_id": "VER",
        "current_lap": 29,
        "current_compound": "C4",
        "current_tyre_age": 28,
        "race_control_flag": "GREEN",
        "rain_probability": 0.10,
        "gap_ahead_s": None,
        "gap_behind_s": 12.0,
        "ground_truth_action": "BOX_NOW",
    },
    {
        "scenario_id": "bahrain_2024_stint_stabilization",
        "name": "Bahrain GP Lap 10 Clean Air Stint Phase",
        "circuit_id": "bahrain",
        "driver_id": "PIA",
        "current_lap": 10,
        "current_compound": "C2",
        "current_tyre_age": 9,
        "race_control_flag": "GREEN",
        "rain_probability": 0.0,
        "gap_ahead_s": 4.5,
        "gap_behind_s": 5.2,
        "ground_truth_action": "STAY_OUT",
    },
]


class RaceScenarioReplayHarness:
    """Executes deterministic scenario replaying for tactical verification."""

    def __init__(self, scenarios: Optional[List[Dict[str, Any]]] = None) -> None:
        self.scenarios = scenarios or HISTORICAL_RACE_SCENARIOS
        self.assembler = HierarchicalContextAssembler()

    def run_benchmark(self, harness: AgentExecutionHarness) -> ReplayBenchmarkReport:
        """Runs the complete scenario replay suite through the agent harness."""
        outcomes: List[ScenarioOutcome] = []
        latencies: List[float] = []

        for sc in self.scenarios:
            bundle = self.assembler.assemble(
                driver_id=sc["driver_id"],
                circuit_id=sc["circuit_id"],
                current_lap=sc["current_lap"],
                current_compound=sc["current_compound"],
                current_tyre_age=sc["current_tyre_age"],
                gap_ahead_s=sc.get("gap_ahead_s"),
                gap_behind_s=sc.get("gap_behind_s"),
                rival_driver_behind=sc.get("rival_behind"),
                rain_probability=sc.get("rain_probability", 0.0),
                race_control_flag=sc.get("race_control_flag", "GREEN"),
            )

            result = harness.execute(bundle)
            latencies.append(result.latency_ms)

            # Match criteria: exact or semantically valid tactical action
            gt_action = sc["ground_truth_action"]
            matched = (result.action == gt_action) or (
                gt_action == "BOX_NOW" and result.action in ["BOX_NOW", "PIT_UNDER_SC", "COVER_UNDERCUT"]
            )

            outcomes.append(
                ScenarioOutcome(
                    scenario_id=sc["scenario_id"],
                    scenario_name=sc["name"],
                    ground_truth_action=gt_action,
                    agent_action=result.action,
                    matched=matched,
                    latency_ms=result.latency_ms,
                    tactical_rationale=result.decision_payload.get("tactical_reason", ""),
                )
            )

        matched_count = sum(1 for o in outcomes if o.matched)
        accuracy = round((matched_count / max(len(outcomes), 1)) * 100.0, 1)
        mean_lat = round(sum(latencies) / max(len(latencies), 1), 2)
        max_lat = round(max(latencies) if latencies else 0.0, 2)

        return ReplayBenchmarkReport(
            total_scenarios=len(outcomes),
            matched_scenarios=matched_count,
            alignment_accuracy_pct=accuracy,
            mean_latency_ms=mean_lat,
            max_latency_ms=max_lat,
            all_passed_sla=max_lat < harness.max_timeout_ms,
            outcomes=outcomes,
        )

