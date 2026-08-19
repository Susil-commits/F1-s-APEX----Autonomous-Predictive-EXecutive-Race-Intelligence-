"""Multi-Factor Risk Engine: Tracks DNF, tyre, weather, traffic, mechanical, pit, collision,
and strategy risks. Supports configurable risk appetite (lambda) for risk-adjusted scoring.

Spec reference: APEX_MASTER_ENGINEERING_SPEC.md §20
"""
from __future__ import annotations

import logging

import numpy as np

from backend.app.simulator.models import (
    RaceState,
    RiskState,
    SafetyCarStatus,
    TyreCompound,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default risk appetite (lambda). Risk-adjusted score = E[finish] - lambda * total_risk
# Override at call time or via environment variable APEX_RISK_LAMBDA.
# ---------------------------------------------------------------------------
DEFAULT_RISK_LAMBDA: float = 0.35  # Balanced — neither overly aggressive nor overly conservative

# Documented weight distribution for overall_risk_score composite:
# tyre(0.25) + weather(0.20) + traffic(0.15) + mechanical(0.15) + pit(0.10) + collision(0.10) + strategy(0.05)
RISK_WEIGHTS: dict[str, float] = {
    "tyre": 0.25,
    "weather": 0.20,
    "traffic": 0.15,
    "mechanical": 0.15,
    "pit": 0.10,
    "collision": 0.10,
    "strategy": 0.05,
}


class RiskEngine:
    """Calculates multi-dimensional operational risk scores and risk-adjusted expected outcomes.

    Risk vector (all components in [0.0, 1.0]):
        tyre              - tyre blowout / cliff probability
        weather           - weather transition danger (slick on wet, etc.)
        traffic           - undercut threat / dirty air DRS window
        mechanical        - vehicle health failure probability
        pit               - pit-lane loss / timing risk
        collision         - proximity / incident risk
        strategy          - mandatory compound violations, strategy lock-in risk
        dnf               - composite DNF probability

    Risk-adjusted score (configurable via lambda):
        score = expected_finish_value - lambda * total_risk_score
        Higher lambda = more risk-averse (conservative racing line)
        Lower lambda = more aggressive
    """

    @classmethod
    def evaluate_risk(
        cls,
        state: RaceState,
        target_car_id: str | None = None,
        risk_lambda: float = DEFAULT_RISK_LAMBDA,
    ) -> RiskState:
        """Computes the full composite risk profile for the target car.

        Args:
            state: Current RaceState.
            target_car_id: Car ID to evaluate; defaults to player car.
            risk_lambda: Risk appetite multiplier (higher = more risk-averse).

        Returns:
            RiskState with all risk components and risk-adjusted score.
        """
        player = next(
            (c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player),
            state.cars[0] if state.cars else None,
        )
        if player is None or player.is_dnf:
            return RiskState(overall_risk_score=1.0, dnf_risk=1.0)

        wear = player.tyre_wear_pct
        laps_left = max(1, state.total_laps - state.current_lap)

        # ------------------------------------------------------------------
        # 1. Tyre Blowout Risk
        # ------------------------------------------------------------------
        if player.tyre_cliff_reached or wear >= 88.0:
            tyre_risk = 0.95
        elif wear >= 78.0:
            tyre_risk = 0.72
        elif wear >= 65.0:
            tyre_risk = 0.38
        elif wear >= 50.0:
            tyre_risk = 0.18
        else:
            tyre_risk = max(0.02, wear / 100.0 * 0.15)

        # ------------------------------------------------------------------
        # 2. Weather Transition Risk
        # ------------------------------------------------------------------
        wetness = getattr(state.weather, "track_wetness", 0.0)
        is_slick = player.tyre_compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        is_rain_tyre = player.tyre_compound in (TyreCompound.INTERMEDIATE, TyreCompound.WET)

        if wetness > 0.45 and is_slick:
            weather_risk = 0.95   # Slicks in heavy water — critical
        elif wetness > 0.20 and is_slick:
            weather_risk = 0.62   # Slicks in damp — high
        elif wetness < 0.05 and is_rain_tyre and laps_left > 5:
            weather_risk = 0.45   # Rain tyres on bone dry — damaging
        else:
            weather_risk = float(np.clip(state.weather.rain_probability_next_5_laps * 0.55, 0.0, 0.45))

        # ------------------------------------------------------------------
        # 3. Traffic / Undercut Risk
        # ------------------------------------------------------------------
        gap_behind = player.gap_to_car_behind_s
        if 0.0 < gap_behind <= 0.8 and wear > 35.0:
            traffic_risk = 0.88   # DRS + undercut window — extreme threat
        elif 0.0 < gap_behind <= 1.5 and wear > 45.0:
            traffic_risk = 0.65   # Close undercut window
        elif 0.0 < gap_behind <= 3.0:
            traffic_risk = 0.35
        else:
            traffic_risk = 0.08

        # ------------------------------------------------------------------
        # 4. Mechanical Failure Risk
        # ------------------------------------------------------------------
        if player.health_state:
            mech_risk = float(np.clip(player.health_state.failure_probability, 0.0, 1.0))
            alarm_count = len(getattr(player.health_state, "active_alarms", []))
            if alarm_count >= 2:
                mech_risk = min(0.98, mech_risk + 0.30)
            elif alarm_count == 1:
                mech_risk = min(0.95, mech_risk + 0.15)
        else:
            mech_risk = 0.015

        # ------------------------------------------------------------------
        # 5. Pit-Lane Risk (timing, DRS loss, undercut opportunity missed)
        # ------------------------------------------------------------------
        if state.safety_car == SafetyCarStatus.SAFETY_CAR and wear > 30.0:
            pit_risk = 0.05   # SC is a safe pit window — LOW risk
        elif state.safety_car == SafetyCarStatus.VSC and wear > 30.0:
            pit_risk = 0.08   # VSC window also advantageous
        elif wear < 25.0 and laps_left > 20:
            pit_risk = 0.70   # Pitting way too early — strategic risk
        elif wear > 80.0 and laps_left > 5:
            pit_risk = 0.75   # Pitting dangerously late — blowout risk
        else:
            pit_risk = 0.15

        # ------------------------------------------------------------------
        # 6. Collision / Incident Risk
        # ------------------------------------------------------------------
        gap_ahead = player.gap_to_car_ahead_s
        if 0.0 < gap_ahead < 0.5 and player.driving_mode is not None and "PUSH" in str(player.driving_mode):
            collision_risk = 0.55   # Very close battle in push mode
        elif 0.0 < gap_ahead < 1.0:
            collision_risk = 0.30
        elif state.safety_car != SafetyCarStatus.NONE:
            collision_risk = 0.10   # SC reduces field proximity risk
        else:
            collision_risk = 0.05

        # ------------------------------------------------------------------
        # 7. Strategy Vulnerability Risk
        # ------------------------------------------------------------------
        if player.pit_count == 0 and laps_left < 12:
            strat_risk = 0.88   # Mandatory compound rule — must pit
        elif player.pit_count == 0 and laps_left < 20:
            strat_risk = 0.55   # Getting late for first stop
        elif player.tyre_age_laps > 38:
            strat_risk = 0.60   # Very old tyres
        elif player.tyre_age_laps > 28:
            strat_risk = 0.30
        else:
            strat_risk = 0.10

        # ------------------------------------------------------------------
        # 8. Composite DNF Risk
        # ------------------------------------------------------------------
        dnf_risk = float(np.clip(
            (tyre_risk * 0.35)
            + (mech_risk * 0.30)
            + (weather_risk * 0.20)
            + (collision_risk * 0.15),
            0.01, 0.99,
        ))

        # ------------------------------------------------------------------
        # Weighted overall risk score (documented weights in RISK_WEIGHTS)
        # ------------------------------------------------------------------
        component_risks = {
            "tyre": tyre_risk,
            "weather": weather_risk,
            "traffic": traffic_risk,
            "mechanical": mech_risk,
            "pit": pit_risk,
            "collision": collision_risk,
            "strategy": strat_risk,
        }
        overall_score = float(sum(
            RISK_WEIGHTS[k] * v for k, v in component_risks.items()
        ))
        overall_score = round(float(np.clip(overall_score, 0.0, 1.0)), 3)

        # ------------------------------------------------------------------
        # Risk-adjusted expected finish value
        # score = expected_finish_value - lambda * total_risk
        # ------------------------------------------------------------------
        n_cars = max(1, len(state.cars))
        finish_value = max(0.0, 1.0 - (player.position - 1) / n_cars)
        risk_adjusted_score = round(finish_value - risk_lambda * overall_score, 4)

        logger.debug(
            "[RiskEngine] car=%s lap=%d overall=%.3f dnf=%.3f tyre=%.3f weather=%.3f "
            "traffic=%.3f mech=%.3f pit=%.3f collision=%.3f strat=%.3f "
            "risk_adj=%.4f (lambda=%.2f)",
            player.car_id, state.current_lap,
            overall_score, dnf_risk, tyre_risk, weather_risk,
            traffic_risk, mech_risk, pit_risk, collision_risk, strat_risk,
            risk_adjusted_score, risk_lambda,
        )

        return RiskState(
            overall_risk_score=overall_score,
            dnf_risk=round(dnf_risk, 3),
            tyre_blowout_risk=round(tyre_risk, 3),
            weather_transition_risk=round(weather_risk, 3),
            traffic_undercut_risk=round(traffic_risk, 3),
            mechanical_failure_risk=round(mech_risk, 3),
            strategy_vulnerability_risk=round(strat_risk, 3),
        )

    @classmethod
    def risk_adjusted_score(
        cls,
        state: RaceState,
        target_car_id: str | None = None,
        risk_lambda: float = DEFAULT_RISK_LAMBDA,
    ) -> dict[str, float]:
        """Returns a structured risk-adjusted scoring dict for decision ranking.

        Formula: score = expected_finish_value - lambda * total_risk

        Args:
            state: Current RaceState.
            target_car_id: Target car.
            risk_lambda: Risk appetite. Higher = more conservative.

        Returns:
            dict with keys: expected_finish_value, total_risk, risk_adjusted_score, lambda,
                            and individual risk component values.
        """
        risk_state = cls.evaluate_risk(state, target_car_id, risk_lambda)
        player = next(
            (c for c in state.cars if (target_car_id and c.car_id == target_car_id) or c.is_player),
            state.cars[0] if state.cars else None,
        )
        n_cars = max(1, len(state.cars))
        pos = player.position if player else n_cars
        finish_value = max(0.0, 1.0 - (pos - 1) / n_cars)
        score = finish_value - risk_lambda * risk_state.overall_risk_score

        return {
            "expected_finish_value": round(finish_value, 4),
            "total_risk": risk_state.overall_risk_score,
            "risk_adjusted_score": round(score, 4),
            "lambda": risk_lambda,
            "dnf_risk": risk_state.dnf_risk,
            "tyre_risk": risk_state.tyre_blowout_risk,
            "weather_risk": risk_state.weather_transition_risk,
            "traffic_risk": risk_state.traffic_undercut_risk,
            "mech_risk": risk_state.mechanical_failure_risk,
            "strategy_risk": risk_state.strategy_vulnerability_risk,
        }
