"""Explainability Layer for APEX decision intelligence."""
from typing import Any

from backend.app.intelligence.tyre_model import TyreModel
from backend.app.simulator.models import DecisionExplanation, RaceState, StrategyAction
from backend.app.strategy.counterfactual import CounterfactualChecker
from backend.app.strategy.rule_engine import RuleEngine


class ExplainabilityEngine:
    """Produces structured, transparent decision explanations for every strategic recommendation."""

    @classmethod
    def generate_explanation(
        cls,
        sim: Any,
        dqn_action: StrategyAction | None = None,
        q_value_margin: float | None = None,
        include_counterfactual: bool = True,
        dqn_agent: Any | None = None,
    ) -> DecisionExplanation:
        """Generates comprehensive explanation schema."""
        state: RaceState = sim.get_state()
        player = sim.get_player_car()

        # 1. Rule Engine Evaluation
        rule_action, factors, urgency = RuleEngine.evaluate(state, player.car_id)

        # 2. Tyre Window Assessment
        pit_window = TyreModel.calculate_pit_window(player, state.track, state.weather)

        # 3. Counterfactual Rollout
        counterfactual_summary = {}
        if include_counterfactual:
            counterfactual_summary = CounterfactualChecker.evaluate_alternatives(sim, rollout_laps=4)

        # 4. Uncertainty Quantification from Neural Policy
        uncertainty_info = {}
        try:
            from backend.app.intelligence.feature_builder import FeatureBuilder
            from backend.app.strategy.dqn_agent import DQNAgent

            obs = FeatureBuilder.extract_features(state, target_car_id=player.car_id if player else None)
            agent = dqn_agent or DQNAgent()
            uncertainty_info = agent.compute_uncertainty_quantification(obs, num_samples=10)
        except Exception:
            pass

        # 5. Final Recommendation synthesis (Rule Engine + DQN consensus)
        final_action = dqn_action if (dqn_action and q_value_margin and q_value_margin > 1.2) else rule_action

        # Confidence calculation
        confidence = 0.88
        if urgency == "CRITICAL":
            confidence = 0.98
        elif urgency == "HIGH":
            confidence = 0.92
        elif dqn_action and dqn_action == rule_action:
            confidence = 0.95

        return DecisionExplanation(
            recommendation=final_action,
            confidence_score=confidence,
            urgency=urgency,
            primary_factors=factors,
            rule_engine_action=rule_action,
            dqn_action=dqn_action,
            q_value_margin=q_value_margin,
            tyre_cliff_risk=pit_window["cliff_risk"],
            pit_window_status=pit_window["status"],
            expected_time_delta_s=round(pit_window["predicted_loss_s"], 2),
            counterfactual_summary=counterfactual_summary,
            uncertainty_quantification=uncertainty_info,
        )
