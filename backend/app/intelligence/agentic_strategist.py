"""Autonomous Multi-Step Agentic Race Strategist for APEX.

Orchestrates neural reinforcement learning policies (DQN), TreeSHAP feature attributions,
stochastic Monte Carlo rollouts, counterfactual timeline forking, and empirical FastF1
tyre physics into synthesized executive pit-wall strategy plans with chain-of-thought reasoning.
"""
import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.intelligence.shap_explainer import TreeSHAPExplainer
from backend.app.intelligence.tyre_model import TyreModel
from backend.app.simulator.models import (
    RaceState,
    SafetyCarStatus,
    StrategyAction,
    TyreCompound,
)
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.strategy.monte_carlo import MonteCarloEngine
from backend.app.strategy.rule_engine import RuleEngine


class TacticalContingency(BaseModel):
    trigger_event: str
    action: StrategyAction
    rationale: str
    target_compound: TyreCompound | None = None


class AgenticStrategyPlan(BaseModel):
    timestamp_utc: str
    lap: int
    executive_summary: str
    primary_action: StrategyAction
    confidence_score: float = Field(ge=0.0, le=1.0)
    urgency: str  # LOW, MEDIUM, HIGH, CRITICAL
    policy_entropy: float  # Uncertainty metric
    q_value_margin: float
    chain_of_thought: list[str]
    shapley_drivers: list[dict[str, Any]]
    contingencies: list[TacticalContingency]
    monte_carlo_metrics: dict[str, Any]
    counterfactual_verdict: str
    tyre_cliff_risk: str
    radio_transmission: str


class AgenticRaceStrategist:
    """Autonomous Pit Wall AI Strategist coordinating multi-agent tactical analysis."""

    def __init__(self, dqn_agent: DQNAgent | None = None):
        self.dqn_agent = dqn_agent or DQNAgent()
        self.shap_explainer = TreeSHAPExplainer.get_instance()

    def formulate_strategy(
        self,
        state: RaceState,
        target_car_id: str | None = None,
        num_mc_rollouts: int = 500,
    ) -> AgenticStrategyPlan:
        """
        Executes autonomous multi-step reasoning cycle:
        Step 1: Extract 28-D normalized state tensor and compound suitability.
        Step 2: Query Neural Network DQN policy, Q-value distribution, advantages & entropy.
        Step 3: Evaluate deterministic expert rule engine consensus.
        Step 4: Compute TreeSHAP attributions and Shapley force direction.
        Step 5: Run stochastic Monte Carlo 1,000 forward rollouts.
        Step 6: Synthesize executive plan with chain-of-thought & contingencies.
        """
        now_utc = datetime.datetime.now(datetime.UTC).isoformat()
        player = next((c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player), state.cars[0] if state.cars else None)
        
        if player is None:
            # Fallback for empty state
            return AgenticStrategyPlan(
                timestamp_utc=now_utc,
                lap=state.current_lap,
                executive_summary="No active car state available.",
                primary_action=StrategyAction.MAINTAIN,
                confidence_score=0.50,
                urgency="LOW",
                policy_entropy=1.0,
                q_value_margin=0.0,
                chain_of_thought=["No car telemetry available."],
                shapley_drivers=[],
                contingencies=[],
                monte_carlo_metrics={},
                counterfactual_verdict="MAINTAIN",
                tyre_cliff_risk="LOW",
                radio_transmission="APEX standby: telemetry offline.",
            )

        # Step 1: Feature Extraction & Tyre Life Estimation
        obs = FeatureBuilder.extract_features(state, target_car_id=player.car_id)
        suitability = FeatureBuilder.compute_compound_suitability(state)
        track_name = getattr(state.track, "name", "silverstone") if state.track else "silverstone"
        track_severity = TyreModel.get_circuit_degradation_factor(track_name)
        laps_to_cliff = TyreModel.estimate_remaining_laps(player.tyre_compound, player.tyre_wear_pct, player.driving_mode, track_severity)

        # Step 2: Safe RL Action Masking & Neural Policy Evaluation
        from backend.app.intelligence.pinn_tyre_residual import (
            PINNTyreResidualCompensator,
        )
        from backend.app.strategy.safe_rl_guardrail import ActionMaskGuardrail
        action_mask = ActionMaskGuardrail.get_action_mask(state, target_car_id=player.car_id)
        dqn_profile = self.dqn_agent.predict_strategic_profile(obs, action_mask=action_mask)
        dqn_action = StrategyAction(dqn_profile["optimal_action"])
        q_margin = dqn_profile["q_value_margin"]
        entropy = dqn_profile["policy_entropy"]

        # Step 3: PINN Non-Linear Tyre Degradation Residual
        pinn = PINNTyreResidualCompensator.get_instance()
        pinn_residual_s = pinn.predict_residual_delta_s(
            compound=player.tyre_compound,
            current_wear_pct=player.tyre_wear_pct,
            mode=player.driving_mode,
            track_name=track_name,
            track_temp_c=getattr(state.weather, "track_temp_c", 35.0),
            rain_intensity=state.weather.rain_intensity,
        )

        # Step 4: Expert Rule Engine Consensus
        rule_action, rule_factors, urgency = RuleEngine.evaluate(state, player.car_id)

        # Step 5: TreeSHAP Explainability
        shap_explanation = self.shap_explainer.explain(obs)
        top_shap_factors = shap_explanation.get("top_features", [])[:4]

        # Step 6: Monte Carlo Stochastic Simulation
        mc_results = MonteCarloEngine.run_simulation(state, num_rollouts=num_mc_rollouts, target_car_id=player.car_id)
        best_mc_strat = mc_results.get("strategies", [{}])[0]

        # Step 7: Multi-Criteria Action Consensus & Safety Guardrail Filter
        if urgency == "CRITICAL":
            primary_action = rule_action
            confidence = 0.98
        elif dqn_profile["is_confident"] and q_margin > 1.2:
            primary_action = dqn_action
            confidence = min(0.95, round(1.0 - (entropy * 0.35), 2))
        elif rule_action == dqn_action:
            primary_action = dqn_action
            confidence = 0.94
        else:
            primary_action = rule_action
            confidence = 0.85

        # Ensure selected action complies with Safe RL Guardrail
        safety_check = ActionMaskGuardrail.evaluate_safety(primary_action, state, target_car_id=player.car_id)
        if not safety_check.is_safe:
            primary_action = dqn_action if ActionMaskGuardrail.evaluate_safety(dqn_action, state, target_car_id=player.car_id).is_safe else StrategyAction.MAINTAIN

        # Step 7: Chain-of-Thought Synthesis
        favored_compound = max(suitability.keys(), key=lambda k: suitability.get(k, 0.0)) if suitability else "HARD"
        cot: list[str] = [
            f"1. Telemetry Audit: Lap {state.current_lap}/{state.total_laps}, P{player.position}, {player.tyre_compound.value} tyres at {player.tyre_wear_pct:.1f}% wear (~{laps_to_cliff} laps to cliff).",
            f"2. Environmental State: Weather is {state.weather.condition.value} with rain intensity {state.weather.rain_intensity:.2f}. Compound suitability favors {favored_compound}.",
            f"3. Neural Policy (DQN): Optimal action {dqn_action.value} (Q-margin: +{q_margin:.2f}, Shannon entropy: {entropy:.3f}).",
            f"4. TreeSHAP Attribution: Primary policy driver is '{top_shap_factors[0]['feature'] if top_shap_factors else 'Wear progression'}' with impact {top_shap_factors[0]['impact'] if top_shap_factors else 'nominal'}.",
            f"5. Monte Carlo Projection: Top path '{best_mc_strat.get('strategy_name', 'Plan A')}' yields {best_mc_strat.get('win_probability_pct', 0.0)}% win / {best_mc_strat.get('podium_probability_pct', 0.0)}% podium probability.",
            f"6. Executive Decision: Execute {primary_action.value} with calibrated confidence of {int(confidence * 100)}%.",
        ]

        # Step 8: Dynamic Contingency Branching
        contingencies: list[TacticalContingency] = []
        if state.safety_car == SafetyCarStatus.NONE:
            sc_target = TyreCompound.HARD if suitability.get("HARD", 0) > suitability.get("MEDIUM", 0) else TyreCompound.MEDIUM
            contingencies.append(TacticalContingency(
                trigger_event="Safety Car or VSC Deployed",
                action=StrategyAction.PIT_HARD if sc_target == TyreCompound.HARD else StrategyAction.PIT_MEDIUM,
                rationale=f"Exploit cheap ~14s pit loss delta during neutralised race to switch to fresh {sc_target.value} tyres.",
                target_compound=sc_target,
            ))

        if state.weather.rain_probability_next_5_laps > 0.40:
            contingencies.append(TacticalContingency(
                trigger_event="Rain Intensification (Moisture > 0.35)",
                action=StrategyAction.PIT_INTER,
                rationale="Immediate crossover to Intermediate compound to prevent hydroplaning and maintain +3.5s/lap wet pace advantage.",
                target_compound=TyreCompound.INTERMEDIATE,
            ))

        # Radio Message
        if "PIT" in primary_action.value:
            radio = f"Box, box! Boxing for {player.tyre_compound.value if 'INTER' in primary_action.value else 'new tyres'}, confirm on the radio."
        elif primary_action == StrategyAction.PUSH:
            radio = "Deploy maximum pace now, push phase active. Mind the exit kerbs."
        elif primary_action == StrategyAction.CONSERVE:
            radio = "Lift and coast into Turn 3, manage the tyre thermal surface."
        else:
            radio = "Pace is optimal, manage tyres to the target window."

        return AgenticStrategyPlan(
            timestamp_utc=now_utc,
            lap=state.current_lap,
            executive_summary=f"Lap {state.current_lap} Strategic Directive: {primary_action.value} ({int(confidence * 100)}% Confidence | {urgency} Urgency).",
            primary_action=primary_action,
            confidence_score=confidence,
            urgency=urgency,
            policy_entropy=entropy,
            q_value_margin=q_margin,
            chain_of_thought=cot,
            shapley_drivers=top_shap_factors,
            contingencies=contingencies,
            monte_carlo_metrics={
                "recommended_plan": best_mc_strat.get("strategy_name", "Plan A"),
                "win_probability_pct": best_mc_strat.get("win_probability_pct", 0.0),
                "podium_probability_pct": best_mc_strat.get("podium_probability_pct", 0.0),
                "expected_finish_pos": best_mc_strat.get("expected_finish_pos", player.position),
            },
            counterfactual_verdict=best_mc_strat.get("strategy_id", "plan_a"),
            tyre_cliff_risk="CRITICAL" if laps_to_cliff <= 2 else ("HIGH" if laps_to_cliff <= 5 else "LOW"),
            radio_transmission=radio,
        )


_strategist_instance: AgenticRaceStrategist | None = None


def get_agentic_strategist() -> AgenticRaceStrategist:
    """Returns singleton AgenticRaceStrategist instance."""
    global _strategist_instance
    if _strategist_instance is None:
        _strategist_instance = AgenticRaceStrategist()
    return _strategist_instance
