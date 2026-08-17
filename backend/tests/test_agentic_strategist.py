"""Unit tests for the Autonomous Multi-Step Agentic Race Strategist."""
import pytest
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TrackCondition, SafetyCarStatus
from backend.app.intelligence.agentic_strategist import (
    AgenticRaceStrategist,
    AgenticStrategyPlan,
    get_agentic_strategist,
)


def test_agentic_strategist_singleton():
    """Verify singleton accessor."""
    s1 = get_agentic_strategist()
    s2 = get_agentic_strategist()
    assert s1 is s2


def test_formulate_strategy_dry_conditions():
    """Verify autonomous plan formulation in standard dry conditions."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(5):
        sim.step()

    state = sim.get_state()
    strategist = get_agentic_strategist()
    plan: AgenticStrategyPlan = strategist.formulate_strategy(state, num_mc_rollouts=100)

    assert isinstance(plan, AgenticStrategyPlan)
    assert plan.lap == 5
    assert plan.primary_action in [a for a in StrategyAction]
    assert 0.0 <= plan.confidence_score <= 1.0
    assert 0.0 <= plan.policy_entropy <= 1.0
    assert len(plan.chain_of_thought) >= 5
    assert len(plan.contingencies) >= 1
    assert "win_probability_pct" in plan.monte_carlo_metrics


def test_formulate_strategy_wet_weather_contingency():
    """Verify agentic strategist branches into wet tyre contingencies during rain."""
    sim = RaceSimulator(track_name="spa", seed=101)
    sim.inject_weather(TrackCondition.WET, rain_intensity=0.80)
    for _ in range(4):
        sim.step()

    state = sim.get_state()
    strategist = get_agentic_strategist()
    plan = strategist.formulate_strategy(state, num_mc_rollouts=100)

    assert plan.primary_action in (StrategyAction.PIT_INTER, StrategyAction.PIT_WET, StrategyAction.CONSERVE, StrategyAction.MAINTAIN)
    # Check that chain of thought notes wet condition
    cot_text = " ".join(plan.chain_of_thought)
    assert "WET" in cot_text or "Intermediate" in cot_text or "rain" in cot_text.lower()


def test_formulate_strategy_safety_car_opportunism():
    """Verify agent adapts to Safety Car window deployment."""
    sim = RaceSimulator(track_name="monza", seed=77)
    sim.inject_safety_car(SafetyCarStatus.SAFETY_CAR, laps=4)
    for _ in range(3):
        sim.step()

    state = sim.get_state()
    strategist = get_agentic_strategist()
    plan = strategist.formulate_strategy(state, num_mc_rollouts=100)

    assert plan.confidence_score >= 0.70
    assert len(plan.radio_transmission) > 0
