"""Tests for DQNAgent epistemic uncertainty quantification and confidence bounds."""
import numpy as np
import pytest

from backend.app.simulator.engine import RaceSimulator
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.strategy.explainability import ExplainabilityEngine


def test_dqn_uncertainty_quantification_calculation():
    """Verifies that DQNAgent computes standard deviations and 90% confidence intervals."""
    agent = DQNAgent()
    obs = np.random.randn(28).astype(np.float32)

    uncertainty = agent.compute_uncertainty_quantification(obs, num_samples=10)
    assert "method" in uncertainty
    assert "epistemic_uncertainty_score" in uncertainty
    assert "action_uncertainty" in uncertainty
    assert "PIT_SOFT" in uncertainty["action_uncertainty"]

    soft_pit = uncertainty["action_uncertainty"]["PIT_SOFT"]
    assert "q_mean" in soft_pit
    assert "q_std" in soft_pit
    assert "ci_90_lower" in soft_pit
    assert "ci_90_upper" in soft_pit
    assert soft_pit["ci_90_lower"] <= soft_pit["ci_90_upper"]


def test_explainability_includes_uncertainty():
    """Verifies that ExplainabilityEngine attaches uncertainty quantification to decision explanations."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.step()

    explanation = ExplainabilityEngine.generate_explanation(sim=sim, include_counterfactual=False)
    assert explanation is not None
    assert hasattr(explanation, "uncertainty_quantification")
    assert isinstance(explanation.uncertainty_quantification, dict)
