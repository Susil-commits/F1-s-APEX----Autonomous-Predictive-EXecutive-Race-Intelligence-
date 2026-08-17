"""Unit tests for the Explainability Engine and multi-modal decision intelligence."""
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import (
    DecisionExplanation,
    StrategyAction,
    TrackCondition,
)
from backend.app.strategy.explainability import ExplainabilityEngine


def test_explainability_engine_default_generation():
    """Verify that generate_explanation produces a valid DecisionExplanation schema with all required fields."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(5):
        sim.step()

    explanation = ExplainabilityEngine.generate_explanation(sim)

    assert isinstance(explanation, DecisionExplanation)
    assert isinstance(explanation.recommendation, StrategyAction)
    assert 0.0 <= explanation.confidence_score <= 1.0
    assert explanation.urgency in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert isinstance(explanation.primary_factors, list)
    assert len(explanation.primary_factors) >= 1
    assert isinstance(explanation.tyre_cliff_risk, str)
    assert isinstance(explanation.pit_window_status, str)
    assert isinstance(explanation.expected_time_delta_s, float)
    assert isinstance(explanation.counterfactual_summary, dict)
    assert "alternatives" in explanation.counterfactual_summary


def test_explainability_engine_without_counterfactual():
    """Verify that include_counterfactual=False skips forward rollouts for fast evaluation."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(3):
        sim.step()

    explanation = ExplainabilityEngine.generate_explanation(sim, include_counterfactual=False)

    assert isinstance(explanation, DecisionExplanation)
    assert explanation.counterfactual_summary == {}


def test_explainability_engine_dqn_consensus_boost():
    """Verify that agreement between DQN agent and Rule Engine yields high consensus confidence."""
    sim = RaceSimulator(track_name="silverstone", seed=42, enable_dynamic_weather=False)
    for _ in range(3):
        sim.step()

    # Get the rule engine action first
    base_explanation = ExplainabilityEngine.generate_explanation(sim, include_counterfactual=False)
    rule_action = base_explanation.rule_engine_action

    # Pass agreeing DQN action
    consensus_explanation = ExplainabilityEngine.generate_explanation(
        sim,
        dqn_action=rule_action,
        q_value_margin=0.5,
        include_counterfactual=False,
    )

    assert consensus_explanation.recommendation == rule_action
    assert consensus_explanation.confidence_score >= 0.95


def test_explainability_engine_dqn_override_with_high_margin():
    """Verify that a high Q-value margin (> 1.2) allows DQN policy to override baseline rule."""
    sim = RaceSimulator(track_name="silverstone", seed=42, enable_dynamic_weather=False)
    for _ in range(3):
        sim.step()

    # Suppose rule action is MAINTAIN, DQN proposes PUSH with high margin 1.85
    override_explanation = ExplainabilityEngine.generate_explanation(
        sim,
        dqn_action=StrategyAction.PUSH,
        q_value_margin=1.85,
        include_counterfactual=False,
    )

    assert override_explanation.recommendation == StrategyAction.PUSH
    assert override_explanation.dqn_action == StrategyAction.PUSH
    assert override_explanation.q_value_margin == 1.85


def test_explainability_engine_rule_engine_retained_on_low_margin():
    """Verify that if DQN differs but margin is low (<= 1.2), rule engine policy is retained."""
    sim = RaceSimulator(track_name="silverstone", seed=42, enable_dynamic_weather=False)
    for _ in range(3):
        sim.step()

    base_exp = ExplainabilityEngine.generate_explanation(sim, include_counterfactual=False)
    rule_action = base_exp.rule_engine_action
    diff_action = StrategyAction.CONSERVE if rule_action != StrategyAction.CONSERVE else StrategyAction.PUSH

    retained_explanation = ExplainabilityEngine.generate_explanation(
        sim,
        dqn_action=diff_action,
        q_value_margin=0.6,
        include_counterfactual=False,
    )

    # Should retain the rule action
    assert retained_explanation.recommendation == rule_action


def test_explainability_engine_critical_urgency_handling():
    """Verify that critical weather mismatch (wet track on slicks) triggers CRITICAL urgency and top confidence."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(5):
        sim.step()

    # Inject severe torrential rain on slick tyres
    sim.inject_weather(TrackCondition.WET, rain_intensity=0.85)

    explanation = ExplainabilityEngine.generate_explanation(sim, include_counterfactual=False)
    assert explanation.urgency == "CRITICAL"
    assert explanation.confidence_score == 0.98
    assert any("AQUAPLANING" in f.upper() or "WET" in f.upper() or "RAIN" in f.upper() for f in explanation.primary_factors)


def test_explainability_engine_tyre_cliff_urgency():
    """Verify that significant tyre wear after stint threshold triggers HIGH urgency and pit recommendation."""
    sim = RaceSimulator(track_name="silverstone", seed=42, enable_dynamic_weather=False)
    for _ in range(10):
        sim.step()

    # Inject tyre wear
    sim.inject_puncture(wear_delta=60.0)

    explanation = ExplainabilityEngine.generate_explanation(sim, include_counterfactual=False)
    assert explanation.urgency in ("HIGH", "CRITICAL")
    assert explanation.confidence_score >= 0.92
    assert explanation.recommendation in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD)
