"""Tests for the deterministic race simulator."""
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TyreCompound


def test_simulator_determinism():
    """Verify that two simulators initialized with the exact same seed produce identical trajectories."""
    sim1 = RaceSimulator(track_name="silverstone", seed=101)
    sim2 = RaceSimulator(track_name="silverstone", seed=101)

    for lap in range(15):
        s1 = sim1.step()
        s2 = sim2.step()
        
        # Validate current lap and race time match exactly
        assert s1.current_lap == s2.current_lap
        assert s1.race_time_s == s2.race_time_s
        assert len(s1.cars) == len(s2.cars)
        
        # Validate car positions, tyre wears, and lap times
        for c1, c2 in zip(s1.cars, s2.cars):
            assert c1.car_id == c2.car_id
            assert c1.position == c2.position
            assert c1.tyre_wear_pct == c2.tyre_wear_pct
            assert c1.last_lap_time_s == c2.last_lap_time_s


def test_simulator_player_pit_stop():
    """Verify that calling a pit stop updates tyres, resets wear, and increments pit count."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    
    # Run 5 laps
    for _ in range(5):
        sim.step()
        
    player = sim.get_player_car()
    assert player.tyre_wear_pct > 0.0
    assert player.pit_count == 0
    
    # Order pit stop for Hard tyres
    sim.step(player_action=StrategyAction.PIT_HARD)
    
    player_after = sim.get_player_car()
    assert player_after.tyre_compound == TyreCompound.HARD
    assert player_after.tyre_age_laps == 1
    assert player_after.pit_count == 1


def test_simulator_clone_independence():
    """Verify that cloning the simulator creates an independent instance suitable for rollouts."""
    sim = RaceSimulator(track_name="silverstone", seed=77)
    for _ in range(10):
        sim.step()
        
    clone = sim.clone()
    assert clone.current_lap == sim.current_lap
    
    # Advance clone with a pit stop
    clone.step(player_action=StrategyAction.PIT_SOFT)
    
    assert clone.get_player_car().tyre_compound == TyreCompound.SOFT
    assert sim.get_player_car().tyre_compound != TyreCompound.SOFT


def test_counterfactual_checker_evaluate_alternatives():
    """Verify that CounterfactualChecker correctly evaluates candidate strategies."""
    from backend.app.strategy.counterfactual import CounterfactualChecker
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(10):
        sim.step()

    eval_result = CounterfactualChecker.evaluate_alternatives(sim, rollout_laps=4)
    assert eval_result["rollout_laps"] == 4
    assert "best_strategy" in eval_result
    assert "best_action" in eval_result
    assert len(eval_result["alternatives"]) == 5
    for alt in eval_result["alternatives"]:
        assert "strategy" in alt
        assert "action" in alt
        assert "projected_position" in alt
        assert "projected_gap_to_leader" in alt

