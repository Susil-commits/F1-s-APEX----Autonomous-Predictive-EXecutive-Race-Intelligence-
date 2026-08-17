"""Unit tests for APEX Rule-Based Expert Strategy Engine."""
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import (
    SafetyCarStatus,
    StrategyAction,
    TrackCondition,
    TyreCompound,
)
from backend.app.strategy.rule_engine import RuleEngine


def test_rule_engine_rain_switch_to_intermediate():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.weather.condition = TrackCondition.DAMP
    sim.weather.rain_intensity = 0.35
    state = sim.get_state()
    player = sim.get_player_car()
    player.tyre_compound = TyreCompound.MEDIUM

    action, factors, urgency = RuleEngine.evaluate(state, player.car_id)
    assert action == StrategyAction.PIT_INTER
    assert urgency in ("HIGH", "CRITICAL")
    assert any("slip" in f.lower() or "intermediate" in f.lower() or "crossover" in f.lower() or "track" in f.lower() for f in factors)


def test_rule_engine_rain_switch_to_wet():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.weather.condition = TrackCondition.WET
    sim.weather.rain_intensity = 0.75
    state = sim.get_state()
    player = sim.get_player_car()
    player.tyre_compound = TyreCompound.MEDIUM

    action, factors, urgency = RuleEngine.evaluate(state, player.car_id)
    assert action == StrategyAction.PIT_WET
    assert urgency == "CRITICAL"


def test_rule_engine_tyre_cliff_trigger():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    player = sim.get_player_car()
    player.tyre_wear_pct = 82.0
    player.tyre_cliff_reached = True
    player.laps_since_last_pit = 15  # Satisfies stint distance threshold
    state = sim.get_state()

    action, factors, urgency = RuleEngine.evaluate(state, player.car_id)
    assert action in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD)
    assert urgency == "HIGH"
    assert any("cliff" in f.lower() or "wear" in f.lower() or "degradation" in f.lower() for f in factors)


def test_rule_engine_safety_car_opportunistic_pit():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.safety_car = SafetyCarStatus.SAFETY_CAR
    player = sim.get_player_car()
    player.tyre_wear_pct = 55.0
    player.laps_since_last_pit = 12  # Eligible window for cheap pit
    state = sim.get_state()

    action, factors, urgency = RuleEngine.evaluate(state, player.car_id)
    assert action in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD)
    assert any("safety" in f.lower() or "sc" in f.lower() or "opportunistic" in f.lower() for f in factors)

