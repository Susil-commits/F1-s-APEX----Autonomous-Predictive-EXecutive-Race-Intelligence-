"""Rule-based expert strategy baseline for race strategy decision intelligence."""

from backend.app.intelligence.tyre_model import TyreModel
from backend.app.intelligence.weather_model import WeatherPredictor
from backend.app.simulator.models import (
    DrivingMode,
    RaceState,
    StrategyAction,
    TyreCompound,
)


class RuleEngine:
    """Deterministic, explainable rule-based strategy baseline."""

    @classmethod
    def evaluate(cls, state: RaceState, target_car_id: str | None = None) -> tuple[StrategyAction, list[str], str]:
        """
        Evaluates race state and returns:
        (recommended_action, primary_reasoning_factors, urgency_level)
        """
        car = next((c for c in state.cars if c.is_player), state.cars[0] if state.cars else None)
        if target_car_id:
            car = next((c for c in state.cars if c.car_id == target_car_id), car)

        if car is None or car.is_dnf:
            return StrategyAction.MAINTAIN, ["Car not active"], "LOW"

        if car.in_pit or car.pit_stop_queued_compound is not None:
            return StrategyAction.MAINTAIN, ["Pit stop in progress / scheduled"], "LOW"

        laps_remaining = state.total_laps - state.current_lap
        weather_eval = WeatherPredictor.evaluate_weather_risk(state.weather, car.tyre_compound)
        pit_window = TyreModel.calculate_pit_window(car, state.track, state.weather)

        factors: list[str] = []

        # ---------------------------------------------------------
        # Rule 1: Immediate Weather Emergency (Highest Priority)
        # ---------------------------------------------------------
        if weather_eval["mismatch"]:
            rec_compound = weather_eval["recommended_compound"]
            factors.append(weather_eval["reason"])
            action_map = {
                TyreCompound.WET: StrategyAction.PIT_WET,
                TyreCompound.INTERMEDIATE: StrategyAction.PIT_INTER,
                TyreCompound.HARD: StrategyAction.PIT_HARD,
                TyreCompound.MEDIUM: StrategyAction.PIT_MEDIUM,
                TyreCompound.SOFT: StrategyAction.PIT_SOFT,
            }
            return action_map.get(rec_compound, StrategyAction.PIT_HARD), factors, weather_eval["urgency"]

        # ---------------------------------------------------------
        # Rule 2: Opportunistic Safety Car / VSC Pit Stop
        # ---------------------------------------------------------
        sc_val = state.safety_car.value if hasattr(state.safety_car, "value") else str(state.safety_car)
        if sc_val in ("SAFETY_CAR", "VSC"):
            # If tyres have significant wear and we haven't pitted in last 10 laps
            if car.tyre_wear_pct > 38.0 and car.laps_since_last_pit > 8 and laps_remaining > 5:
                advantage = state.track.sc_pit_advantage_s if sc_val == "SAFETY_CAR" else state.track.vsc_pit_advantage_s
                factors.append(f"Opportunistic pit under {sc_val}: saves ~{advantage:.1f}s pit loss delta.")
                
                # Pick optimal compound for remaining race distance
                rec_compound = cls._select_dry_compound(laps_remaining)
                action_map = {
                    TyreCompound.SOFT: StrategyAction.PIT_SOFT,
                    TyreCompound.MEDIUM: StrategyAction.PIT_MEDIUM,
                    TyreCompound.HARD: StrategyAction.PIT_HARD,
                }
                return action_map.get(rec_compound, StrategyAction.PIT_HARD), factors, "HIGH"

        # ---------------------------------------------------------
        # Rule 3: Tyre Degradation Cliff Imminent
        # ---------------------------------------------------------
        if (car.tyre_cliff_reached or car.tyre_wear_pct >= 72.0) and car.laps_since_last_pit >= 8:
            factors.append(f"Tyre degradation at {car.tyre_wear_pct:.1f}% (Cliff limit: {pit_window['cliff_risk']}).")
            if laps_remaining > 3:
                rec_compound = cls._select_dry_compound(laps_remaining)
                factors.append(f"Box to avoid lap-time bleed of +{pit_window['predicted_loss_s']:.2f}s/lap.")
                action_map = {
                    TyreCompound.SOFT: StrategyAction.PIT_SOFT,
                    TyreCompound.MEDIUM: StrategyAction.PIT_MEDIUM,
                    TyreCompound.HARD: StrategyAction.PIT_HARD,
                }
                return action_map.get(rec_compound, StrategyAction.PIT_HARD), factors, "HIGH"

        # ---------------------------------------------------------
        # Rule 4: Undercut / Overtake Attack Mode (Driving Mode)
        # ---------------------------------------------------------
        if car.gap_to_car_ahead_s > 0.0 and car.gap_to_car_ahead_s < 1.2 and car.tyre_wear_pct < 60.0:
            if car.driving_mode != DrivingMode.PUSH:
                factors.append(f"Gap ahead is {car.gap_to_car_ahead_s:.2f}s (Within DRS range). Switch to PUSH for undercut/overtake.")
                return StrategyAction.PUSH, factors, "MEDIUM"

        # ---------------------------------------------------------
        # Rule 5: Tyre Life Conservation
        # ---------------------------------------------------------
        if car.tyre_wear_pct > 55.0 and car.gap_to_car_behind_s > 2.5 and car.driving_mode == DrivingMode.PUSH:
            factors.append(f"Clear gap behind ({car.gap_to_car_behind_s:.2f}s). Switch to NORMAL/CONSERVE to extend stint.")
            return StrategyAction.CONSERVE, factors, "LOW"

        # ---------------------------------------------------------
        # Default: Maintain
        # ---------------------------------------------------------
        factors.append(f"Stint on schedule (Lap {state.current_lap}/{state.total_laps}, Tyre wear {car.tyre_wear_pct:.1f}%).")
        return StrategyAction.MAINTAIN, factors, "LOW"

    @staticmethod
    def _select_dry_compound(laps_remaining: int) -> TyreCompound:
        """Selects ideal tyre compound based on remaining race laps."""
        if laps_remaining <= 14:
            return TyreCompound.SOFT
        elif laps_remaining <= 28:
            return TyreCompound.MEDIUM
        else:
            return TyreCompound.HARD
