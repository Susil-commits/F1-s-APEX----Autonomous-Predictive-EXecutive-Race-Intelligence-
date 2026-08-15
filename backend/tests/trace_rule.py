"""Debug trace for rule based policy."""
from backend.app.simulator.engine import RaceSimulator
from backend.app.strategy.rule_engine import RuleEngine
from backend.app.simulator.models import StrategyAction

sim = RaceSimulator(seed=1000, enable_dynamic_weather=True)
while not sim.is_finished:
    player = sim.get_player_car()
    action, factors, urgency = RuleEngine.evaluate(sim.get_state(), player.car_id)
    if action in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD, StrategyAction.PIT_INTER, StrategyAction.PIT_WET):
        print(f"Lap {sim.current_lap}: Pitting for {action.value} | Wear: {player.tyre_wear_pct:.1f}% | Weather: {sim.weather.condition.value} ({sim.weather.rain_intensity:.2f}) | Factors: {factors}")
    sim.step(player_action=action)

print(f"Total pits: {sim.get_player_car().pit_count}")
