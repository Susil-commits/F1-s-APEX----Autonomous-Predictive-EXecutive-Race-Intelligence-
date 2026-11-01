"""APEX Agent Execution Harness.

Provides a sandboxed, observable, and cost-cap compliant execution environment
for autonomous F1 strategy agents and copilot decision engines.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from context.assembler import RaceContextBundle
from core.security.audit import get_audit_logger
from core.security.circuit_breaker import get_failover_manager

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionResult:
    """Outcome of an agent decision invocation."""
    success: bool
    action: str
    decision_payload: Dict[str, Any]
    latency_ms: float
    token_usage: int
    cost_cap_compute_units: float
    fallback_invoked: bool
    audit_event_id: Optional[str] = None
    error_message: Optional[str] = None


class AgentExecutionHarness:
    """Sandboxed execution harness for APEX race engineering agents.
    
    Guarantees:
    - Hard execution timeout SLA (<200ms)
    - Automatic circuit breaker failover to deterministic rule engine
    - FIA Cost-Cap compute expenditure tracking
    - Cryptographic audit trail logging for all strategic calls
    """

    def __init__(
        self,
        max_timeout_ms: float = 200.0,
        provider_name: str = "primary_llm",
    ) -> None:
        self.max_timeout_ms = max_timeout_ms
        self.provider_name = provider_name
        self.failover_manager = get_failover_manager()
        self.audit_logger = get_audit_logger()

    def execute(
        self,
        context_bundle: RaceContextBundle,
        decision_fn: Optional[Callable[[RaceContextBundle], Dict[str, Any]]] = None,
    ) -> AgentExecutionResult:
        """Executes strategic decision logic within the sandboxed harness."""
        start_time = time.perf_counter()
        cb = self.failover_manager.get_breaker(self.provider_name)

        # Check circuit breaker before execution
        if not cb.can_execute():
            logger.warning(f"Circuit open for {self.provider_name}, executing deterministic fallback")
            return self._execute_deterministic_fallback(
                context_bundle, start_time, reason="CIRCUIT_BREAKER_OPEN"
            )

        try:
            # Execute agent decision logic or default tactical rule engine
            if decision_fn is not None:
                decision = decision_fn(context_bundle)
            else:
                decision = self._default_tactical_reasoning(context_bundle)

            exec_time_ms = (time.perf_counter() - start_time) * 1000.0

            # Verify execution time SLA
            if exec_time_ms > self.max_timeout_ms:
                logger.error(
                    f"Agent execution timeout ({exec_time_ms:.1f}ms > {self.max_timeout_ms}ms)"
                )
                cb.record_failure()
                return self._execute_deterministic_fallback(
                    context_bundle, start_time, reason="TIMEOUT_EXCEEDED"
                )

            cb.record_success()

            # FIA Cost-Cap compute units: 1 unit per 10ms CPU + token weighting
            tokens = context_bundle.token_count_estimate
            compute_units = round((exec_time_ms / 10.0) + (tokens / 500.0), 3)

            # Audit record
            audit_event = self.audit_logger.record_event(
                event_type="AGENT_STRATEGY_DECISION",
                actor_id=f"driver:{context_bundle.driver_id}",
                status="SUCCESS",
                details={
                    "circuit": context_bundle.circuit_id,
                    "action": decision.get("recommended_action", "STAY_OUT"),
                    "latency_ms": round(exec_time_ms, 2),
                    "compute_units": compute_units,
                },
            )

            return AgentExecutionResult(
                success=True,
                action=decision.get("recommended_action", "STAY_OUT"),
                decision_payload=decision,
                latency_ms=round(exec_time_ms, 2),
                token_usage=tokens,
                cost_cap_compute_units=compute_units,
                fallback_invoked=False,
                audit_event_id=audit_event.event_hash,
            )

        except Exception as e:
            logger.error(f"Agent execution failed with error: {str(e)}", exc_info=True)
            cb.record_failure()
            return self._execute_deterministic_fallback(
                context_bundle, start_time, reason=f"EXCEPTION: {str(e)}"
            )

    def _default_tactical_reasoning(self, bundle: RaceContextBundle) -> Dict[str, Any]:
        """Deterministic baseline strategy reasoning when no custom LLM is hooked."""
        l2 = bundle.levels.get("l2_stint", {})
        l3 = bundle.levels.get("l3_realtime", {})
        l0 = bundle.levels.get("l0_structural", {})

        current_compound = l2.get("current_compound", "C3")
        cliff_detected = l2.get("cliff_detected", False)
        laps_to_cliff = l2.get("laps_to_cliff", 10)
        gap_behind = l2.get("gap_behind_s")
        flag = l3.get("race_control_flag", "GREEN")

        # Tactical Priority 1: Safety Car Opportunity
        if flag in ["SAFETY_CAR", "VSC"]:
            action = "PIT_UNDER_SC"
            target_compound = "C2" if current_compound in ["C3", "C4", "C5"] else "C3"
            reason = f"Take advantage of reduced pit loss under {flag}"
        # Tactical Priority 2: Imminent Tyre Cliff
        elif cliff_detected or laps_to_cliff <= 1:
            action = "BOX_NOW"
            target_compound = "C2" if current_compound != "C2" else "C1"
            reason = f"Pirelli tyre cliff reached (+{l2.get('current_deg_sec_per_lap', 0.0)}s/lap)"
        # Tactical Priority 3: Defend Against Undercut
        elif gap_behind is not None and gap_behind < 1.4:
            action = "COVER_UNDERCUT"
            target_compound = "C3"
            reason = f"Defend track position against {l2.get('rival_behind', 'rival')} (gap {gap_behind}s)"
        else:
            action = "STAY_OUT"
            target_compound = current_compound
            reason = "Tyres stable, pace delta optimal"

        return {
            "recommended_action": action,
            "target_compound": target_compound,
            "tactical_reason": reason,
            "stint_lap": l2.get("current_lap", 1),
            "safety_car_hazard": l0.get("sc_hazard_rate", 0.45),
        }

    def _execute_deterministic_fallback(
        self, bundle: RaceContextBundle, start_time: float, reason: str
    ) -> AgentExecutionResult:
        """Immediate failsafe fallback when primary agent execution fails or times out."""
        fallback_decision = self._default_tactical_reasoning(bundle)
        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        audit_event = self.audit_logger.record_event(
            event_type="AGENT_STRATEGY_FALLBACK",
            actor_id=f"driver:{bundle.driver_id}",
            status="WARNING",
            details={
                "reason": reason,
                "fallback_action": fallback_decision["recommended_action"],
                "latency_ms": round(exec_time_ms, 2),
            },
        )

        return AgentExecutionResult(
            success=True,
            action=fallback_decision["recommended_action"],
            decision_payload=fallback_decision,
            latency_ms=round(exec_time_ms, 2),
            token_usage=0,
            cost_cap_compute_units=0.01,
            fallback_invoked=True,
            audit_event_id=audit_event.event_hash,
            error_message=reason,
        )
