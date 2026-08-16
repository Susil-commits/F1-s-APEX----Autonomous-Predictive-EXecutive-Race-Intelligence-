"""Unit tests for LLM Race Engineer Commentary Generator and fact verification."""
from unittest.mock import patch, MagicMock
import pytest

from backend.app.simulator.models import DecisionExplanation, StrategyAction
from backend.app.intelligence.commentary_generator import (
    CommentaryGenerator,
    generate_commentary,
)


@pytest.fixture
def sample_decision():
    return DecisionExplanation(
        recommendation=StrategyAction.PIT_SOFT,
        confidence_score=0.94,
        urgency="CRITICAL",
        primary_factors=["Tyre degradation cliff reached at 78%", "Pace deficit +1.8s/lap"],
        rule_engine_action=StrategyAction.PIT_SOFT,
        dqn_action=StrategyAction.PIT_SOFT,
        tyre_cliff_risk="CRITICAL",
        pit_window_status="OPTIMAL",
        expected_time_delta_s=1.8,
    )


def test_commentary_persona_fallbacks(sample_decision):
    """Verifies that persona-specific template fallbacks produce distinct authentic lines."""
    bono_line = CommentaryGenerator.get_template_fallback(sample_decision, persona="bono")
    gp_line = CommentaryGenerator.get_template_fallback(sample_decision, persona="gp")
    xavi_line = CommentaryGenerator.get_template_fallback(sample_decision, persona="xavi")
    guenther_line = CommentaryGenerator.get_template_fallback(sample_decision, persona="guenther")
    hugh_line = CommentaryGenerator.get_template_fallback(sample_decision, persona="hugh_bird")
    ricky_line = CommentaryGenerator.get_template_fallback(sample_decision, persona="ricky")
    apex_line = CommentaryGenerator.get_template_fallback(sample_decision, persona="apex_core")

    assert "hammer time" in bono_line.lower() or "box" in bono_line.lower()
    assert "max" in gp_line.lower() or "pit confirm" in gp_line.lower()
    assert "box" in xavi_line.lower() or "plan a" in xavi_line.lower()
    assert "rockstars" in guenther_line.lower() or "gene" in guenther_line.lower()
    assert "checo" in hugh_line.lower() or "box" in hugh_line.lower()
    assert "carlos" in ricky_line.lower() or "smooth operator" in ricky_line.lower() or "box" in ricky_line.lower()
    assert "box" in apex_line.lower()


def test_fact_consistency_checker(sample_decision):
    """Tests the zero-hallucination fact consistency validator."""
    # Consistent commentary (contains facts from sample_decision or benign radio words)
    valid_text = "Box box this lap for Softs. 94% confidence call due to tyre cliff."
    assert CommentaryGenerator.is_fact_consistent(valid_text, sample_decision) is True

    # Hallucinated commentary (contains invented numbers like 89% or 45 laps)
    hallucinated_text = "Box this lap, you are losing 14.8 seconds to car 55 on lap 48."
    assert CommentaryGenerator.is_fact_consistent(hallucinated_text, sample_decision) is False


def test_commentary_generator_fallback_on_llm_exception(sample_decision):
    """Verifies graceful fallback when Ollama is offline or times out."""
    gen = CommentaryGenerator()

    # Even with Ollama unavailable/offline, generation must never throw or return empty
    line = gen.generate(sample_decision, current_lap=23, persona="bono", force_refresh=True)
    assert line is not None
    assert len(line) > 5
    assert len(line.split()) <= 25, "Commentary must remain concise under radio constraints"


def test_commentary_debouncing(sample_decision):
    """Verifies that generator reuses cached output when strategic directive is unchanged."""
    gen = CommentaryGenerator()

    line_1 = gen.generate(sample_decision, current_lap=10, force_refresh=True)
    line_2 = gen.generate(sample_decision, current_lap=11, force_refresh=False)
    assert line_1 == line_2

    # If action changes, new commentary should generate
    updated_decision = DecisionExplanation(
        recommendation=StrategyAction.PUSH,
        confidence_score=0.91,
        urgency="HIGH",
        primary_factors=["Clear track air ahead", "Tyre delta advantage"],
        rule_engine_action=StrategyAction.PUSH,
    )
    line_3 = gen.generate(updated_decision, current_lap=12, force_refresh=False)
    assert line_3 != line_1
