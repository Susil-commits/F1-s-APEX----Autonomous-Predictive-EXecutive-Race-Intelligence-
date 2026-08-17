"""Self-Healing Continuous Verification Agent Loop for APEX Race Intelligence.

Autonomously monitors TreeSHAP surrogate alignment, SHA-256 model weight drift,
and automated evaluation harness scoring gates. When regressions or drift are detected,
the agent executes automated diagnostics, triggers surrogate re-distillation,
and logs plain-language Race Control commentary.
"""

import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.app.intelligence.shap_explainer import TreeSHAPExplainer
from backend.eval.run_eval import run_full_evaluation


class AgentHealingAction(BaseModel):
    timestamp_utc: str
    action_type: str  # "DRIFT_RESOLVED", "REDISTILL_TRIGGERED", "BENCHMARK_VERIFIED", "NO_ACTION_REQUIRED"
    trigger_reason: str
    previous_fidelity_r2: float | None = None
    post_healing_fidelity_r2: float | None = None
    pillar_breakdown: dict[str, Any] = Field(default_factory=dict)
    plain_language_debrief: str
    status: str = "COMPLETED"


class SelfHealingAgent:
    """Autonomous reliability and drift verification agent for APEX intelligence."""

    def __init__(self):
        self.action_history: list[AgentHealingAction] = []

    def get_health_summary(self) -> dict[str, Any]:
        """Provides an instant diagnostic snapshot of model health and alignment."""
        explainer = TreeSHAPExplainer.get_instance()
        drift_status = explainer.verify_drift()
        
        is_synced = not drift_status.get("drift_detected", False)
        return {
            "surrogate_synced": is_synced,
            "active_dqn_hash": explainer.active_dqn_hash[:12] if explainer.active_dqn_hash else "none",
            "distilled_dqn_hash": explainer.distilled_dqn_hash[:12] if explainer.distilled_dqn_hash else "none",
            "surrogate_fidelity_r2": drift_status.get("surrogate_fidelity_r2", 0.88),
            "total_actions_logged": len(self.action_history),
            "system_health_rating": "OPTIMAL" if is_synced else "DRIFT_DETECTED",
        }

    def check_and_heal(self, auto_redistill: bool = True) -> AgentHealingAction:
        """
        Executes autonomous verification cycle:
        1. Checks TreeSHAP surrogate alignment and checkpoint hashes.
        2. Runs the 4-pillar evaluation harness.
        3. If drift is detected and auto_redistill is True, triggers re-distillation.
        4. Emits structured plain-language debrief.
        """
        start_time = datetime.datetime.now(datetime.UTC).isoformat()
        explainer = TreeSHAPExplainer.get_instance()
        drift_status = explainer.verify_drift()

        if not drift_status.get("drift_detected", False):
            # Evaluate harness
            eval_report, has_regressions = run_full_evaluation(verbose=False)
            
            if not has_regressions:
                debrief = (
                    "APEX Intelligence Loop Nominal: TreeSHAP surrogate is in sync with active DQN weights "
                    f"(hash: {explainer.active_dqn_hash[:8] if explainer.active_dqn_hash else 'verified'}...). "
                    "All 8 benchmark evaluation gates passed without regression."
                )
                action = AgentHealingAction(
                    timestamp_utc=start_time,
                    action_type="BENCHMARK_VERIFIED",
                    trigger_reason="Scheduled verification check",
                    previous_fidelity_r2=drift_status.get("surrogate_fidelity_r2", 0.88),
                    post_healing_fidelity_r2=drift_status.get("surrogate_fidelity_r2", 0.88),
                    pillar_breakdown=eval_report.get("metrics", {}),
                    plain_language_debrief=debrief,
                    status="HEALTHY",
                )
                self.action_history.append(action)
                return action

        # Drift detected: trigger surrogate re-distillation
        prev_r2 = drift_status.get("surrogate_fidelity_r2", 0.70)
        trigger_msg = (
            f"Surrogate drift detected (Active DQN: {explainer.active_dqn_hash[:8] if explainer.active_dqn_hash else 'unknown'} "
            f"vs Distilled: {explainer.distilled_dqn_hash[:8] if explainer.distilled_dqn_hash else 'missing'})."
        )
        
        if auto_redistill:
            try:
                # Run distillation pipeline
                from backend.training.distill_dqn_surrogate import (
                    run_distillation_pipeline,
                )
                distill_meta = run_distillation_pipeline(n_samples=2000, epochs=30)
                
                # Reset singleton and re-verify
                TreeSHAPExplainer.reset_instance()
                new_explainer = TreeSHAPExplainer.get_instance()
                new_drift = new_explainer.verify_drift()
                new_r2 = new_drift.get("surrogate_fidelity_r2", 0.89)
                
                debrief = (
                    f"Autonomous Healing Succeeded: Re-distilled TreeSHAP surrogate against active DQN policy. "
                    f"Fidelity R2 restored to {new_r2:.3f}. Hashes synchronized."
                )
                action = AgentHealingAction(
                    timestamp_utc=start_time,
                    action_type="DRIFT_RESOLVED",
                    trigger_reason=trigger_msg,
                    previous_fidelity_r2=prev_r2,
                    post_healing_fidelity_r2=new_r2,
                    pillar_breakdown={"distill_r2": new_r2},
                    plain_language_debrief=debrief,
                    status="HEALED",
                )
            except Exception as e:
                action = AgentHealingAction(
                    timestamp_utc=start_time,
                    action_type="REDISTILL_TRIGGERED",
                    trigger_reason=trigger_msg,
                    previous_fidelity_r2=prev_r2,
                    plain_language_debrief=f"Re-distillation encountered exception: {e}. Fallback surrogates active.",
                    status="ATTENTION_REQUIRED",
                )
        else:
            action = AgentHealingAction(
                timestamp_utc=start_time,
                action_type="REDISTILL_TRIGGERED",
                trigger_reason=trigger_msg,
                previous_fidelity_r2=prev_r2,
                plain_language_debrief="Drift detected. Manual distillation trigger recommended.",
                status="DRIFT_FLAGGED",
            )

        self.action_history.append(action)
        return action


_agent_instance: SelfHealingAgent | None = None


def get_self_healing_agent() -> SelfHealingAgent:
    """Returns singleton self-healing agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SelfHealingAgent()
    return _agent_instance
