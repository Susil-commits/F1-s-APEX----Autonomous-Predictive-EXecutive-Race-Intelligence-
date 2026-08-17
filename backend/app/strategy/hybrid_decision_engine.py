"""Hybrid Decision Engine: Synthesizes Rule Engine, Predictive ML Models, Monte Carlo, RL, Emergency Brain, and Risk Engine."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple

from backend.app.simulator.models import (
    RaceState,
    StrategyAction,
    CarState,
    DecisionExplanation,
    TyreCompound,
    DrivingMode,
    TrackCondition,
)
from backend.app.strategy.rule_engine import RuleEngine
from backend.app.strategy.monte_carlo import MonteCarloEngine
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.strategy.ppo_agent import PPOStrategyAgent
from backend.app.strategy.safe_rl_guardrail import ActionMaskGuardrail
from backend.app.intelligence.tyre_model import TyreModel
from backend.app.intelligence.weather_model import WeatherPredictor
from backend.app.intelligence.opponent_model import OpponentIntelligenceEngine
from backend.app.intelligence.driver_model import DriverIntelligenceEngine
from backend.app.intelligence.vehicle_health_model import VehicleHealthIntelligence

logger = logging.getLogger(__name__)


class HybridDecisionAggregator:
    """Multi-tier AI Decision Aggregator for autonomous race operations."""

    def __init__(self):
        self.dqn = DQNAgent()
        self.ppo = PPOStrategyAgent()

    def evaluate_decision(
        self,
        state: RaceState,
        target_car_id: Optional[str] = None,
        num_mc_rollouts: int = 150,
    ) -> DecisionExplanation:
        """
        Synthesizes expert rules, multi-model predictions, Monte Carlo distributions, and RL policies.
        """
        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0] if state.cars else None)
        if player is None or player.is_dnf:
            return DecisionExplanation(
                recommendation=StrategyAction.MAINTAIN,
                confidence_score=0.99,
                urgency="LOW",
                primary_factors=["Car not active or DNF"],
                rule_engine_action=StrategyAction.MAINTAIN,
            )

        # 1. Rule Engine Baseline Evaluation
        rule_action, rule_factors, rule_urgency = RuleEngine.evaluate(state, target_car_id=player.car_id)

        # 2. Predictive Models Evaluation
        weather_eval = WeatherPredictor.evaluate_weather_risk(state.weather, player.tyre_compound)
        tyre_rul = TyreModel.predict_remaining_useful_life(player.tyre_compound, player.tyre_wear_pct, player.tyre_age_laps, player.driving_mode)
        pit_window = TyreModel.calculate_pit_window(player, state.track, state.weather)

        # Opponent undercut / box intent
        opponents = OpponentIntelligenceEngine.predict_all_opponents(state.cars, player.car_id, state.track, state.weather, state.current_lap)
        undercut_threat = any(op.strategy_intent == "UNDERCUT_THREAT" and op.pit_next_1_lap_prob > 0.60 for op in opponents)

        # 3. RL Policy Actions (DQN & PPO)
        from backend.app.intelligence.feature_builder import FeatureBuilder
        obs = FeatureBuilder.extract_features(state, target_car_id=player.car_id)
        dqn_action, q_margin = self.dqn.predict_action(obs)
        ppo_action, ppo_conf = self.ppo.select_action(state)

        # 4. Stochastic Monte Carlo Candidate Rollouts
        mc_results = MonteCarloEngine.evaluate_candidates(state, num_rollouts_per_action=max(30, num_mc_rollouts // 9), target_car_id=player.car_id)
        mc_candidates = mc_results.get("candidates", [])
        best_mc_cand = mc_candidates[0] if mc_candidates else None
        best_mc_action_str = mc_results.get("best_action", "MAINTAIN")

        # Map MC action string to StrategyAction enum
        action_name_map = {
            "PIT_NOW": StrategyAction.PIT_HARD if player.tyre_compound != TyreCompound.HARD else StrategyAction.PIT_MEDIUM,
            "PIT_NEXT_LAP": StrategyAction.MAINTAIN,
            "PIT_PLUS_2": StrategyAction.MAINTAIN,
            "STAY_OUT": StrategyAction.MAINTAIN,
            "PUSH": StrategyAction.PUSH,
            "NORMAL": StrategyAction.MAINTAIN,
            "CONSERVE": StrategyAction.CONSERVE,
            "ATTACK": StrategyAction.PUSH,
            "DEFEND": StrategyAction.CONSERVE,
        }
        if weather_eval["mismatch"]:
            action_name_map["PIT_NOW"] = StrategyAction.PIT_WET if state.weather.condition == TrackCondition.WET else StrategyAction.PIT_INTER

        mc_action = action_name_map.get(best_mc_action_str, rule_action)

        # 5. Guardrail Supervised Selection
        # If immediate weather emergency or tyre cliff, expert rule has priority override
        primary_reasons = list(rule_factors)
        if weather_eval["mismatch"]:
            selected_action = rule_action
            urgency = "CRITICAL"
            confidence = 0.96
            primary_reasons = [weather_eval["reason"], "Weather transition takes absolute strategic priority."]
        elif player.tyre_cliff_reached or player.tyre_wear_pct >= 76.0:
            selected_action = rule_action
            urgency = "HIGH"
            confidence = 0.92
            primary_reasons = [f"Tyre degradation at {player.tyre_wear_pct:.1f}% exceeds cliff limit.", "Severe lap time bleed of +2.5s/lap imminent."]
        elif undercut_threat and player.tyre_wear_pct > 40.0:
            selected_action = StrategyAction.PIT_HARD if player.tyre_compound != TyreCompound.HARD else StrategyAction.PIT_MEDIUM
            urgency = "HIGH"
            confidence = 0.88
            primary_reasons = ["Rival in undercut window expected to pit. Box now to defend track position."]
        else:
            # Under standard green flag conditions, select the best safe Monte Carlo / RL recommendation
            guard_eval = ActionMaskGuardrail.evaluate_safety(
                proposed_action=mc_action,
                state=state,
                target_car_id=player.car_id,
            )
            selected_action = mc_action if guard_eval.is_safe else rule_action
            urgency = rule_urgency
            confidence = round(float(best_mc_cand["confidence"]) if best_mc_cand else 0.85, 2)
            if best_mc_cand:
                primary_reasons.append(f"Monte Carlo projected expected finish: P{best_mc_cand['expected_finish']} (Win prob: {int(best_mc_cand['win_probability']*100)}%).")

        # Compile formatted alternative candidate table
        alternatives = []
        for c in mc_candidates[:4]:
            alternatives.append({
                "action": c["action"],
                "expected_finish": c["expected_finish"],
                "win_probability_pct": round(c["win_probability"] * 100.0, 1),
                "podium_probability_pct": round(c["podium_probability"] * 100.0, 1),
                "risk_score": round((c["tyre_risk"] + c["weather_risk"]) / 2.0, 2),
            })

        overall_risk = round(float(tyre_rul["cliff_probability"] * 0.4 + weather_eval["rain_prob_5_laps"] * 0.3 + (0.3 if undercut_threat else 0.05)), 2)

        return DecisionExplanation(
            recommendation=selected_action,
            confidence_score=confidence,
            urgency=urgency,
            primary_factors=primary_reasons,
            rule_engine_action=rule_action,
            dqn_action=dqn_action,
            ppo_action=ppo_action,
            q_value_margin=q_margin,
            tyre_cliff_risk=pit_window.get("cliff_risk", "LOW"),
            pit_window_status=pit_window.get("status", "OPTIMAL"),
            expected_time_delta_s=round(pit_window.get("predicted_loss_s", 0.0), 2),
            counterfactual_summary=mc_results,
            risk_score=overall_risk,
            alternative_actions=alternatives,
        )


hybrid_decision_aggregator = HybridDecisionAggregator()
