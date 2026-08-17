"""Unit tests for the counterfactual rollout evaluator and timeline forking engine."""
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import StrategyAction, TyreCompound
from backend.app.strategy.counterfactual import CounterfactualChecker


def test_evaluate_alternatives_basic_ranking():
    """Verify that evaluate_alternatives returns properly ranked candidate outcomes."""
    sim = RaceSimulator(track_name="silverstone", seed=101)
    for _ in range(8):
        sim.step()

    results = CounterfactualChecker.evaluate_alternatives(sim, rollout_laps=4)

    assert results["rollout_laps"] == 4
    assert "best_strategy" in results
    assert "best_action" in results
    assert len(results["alternatives"]) == 5

    # Validate sort ordering (position ascending, then gap_to_leader ascending)
    alts = results["alternatives"]
    assert alts[0]["strategy"] == results["best_strategy"]
    assert alts[0]["action"] == results["best_action"]

    for i in range(len(alts) - 1):
        curr_pos = alts[i]["projected_position"]
        next_pos = alts[i + 1]["projected_position"]
        curr_gap = alts[i]["projected_gap_to_leader"]
        next_gap = alts[i + 1]["projected_gap_to_leader"]
        assert (curr_pos < next_pos) or (curr_pos == next_pos and curr_gap <= next_gap)

    # Validate structure of individual alternative entries
    for alt in alts:
        assert isinstance(alt["strategy"], str)
        assert isinstance(alt["action"], str)
        assert isinstance(alt["projected_position"], int)
        assert isinstance(alt["projected_gap_to_leader"], float)
        assert isinstance(alt["projected_tyre_wear_pct"], float)
        assert isinstance(alt["projected_compound"], str)
        assert isinstance(alt["cliff_reached"], bool)


def test_evaluate_alternatives_rollout_horizons():
    """Verify evaluate_alternatives behaves consistently with different rollout horizons."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    for _ in range(5):
        sim.step()

    for horizon in (1, 2, 5, 8):
        res = CounterfactualChecker.evaluate_alternatives(sim, rollout_laps=horizon)
        assert res["rollout_laps"] == horizon
        assert len(res["alternatives"]) == 5


def test_evaluate_alternatives_near_race_finish():
    """Verify evaluate_alternatives handles rollouts gracefully when approaching race end."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    # Fast-forward to 1 lap before finish
    sim.current_lap = sim.track.total_laps - 1
    for car in sim.cars:
        car.current_lap = sim.current_lap

    results = CounterfactualChecker.evaluate_alternatives(sim, rollout_laps=5)
    assert len(results["alternatives"]) == 5
    assert results["best_action"] in [a.value for a in StrategyAction]


def test_fork_timeline_with_enum_action():
    """Verify timeline forking with a StrategyAction enum."""
    sim = RaceSimulator(track_name="silverstone", seed=77)
    for _ in range(12):
        sim.step()

    state = sim.get_state()
    fork_res = CounterfactualChecker.fork_timeline(
        historical_state=state,
        proposed_action=StrategyAction.PIT_HARD,
        rollout_laps=4,
    )

    assert fork_res["historical_lap"] == 12
    assert fork_res["proposed_action"] == StrategyAction.PIT_HARD.value
    assert fork_res["rollout_laps"] == 4
    assert fork_res["verdict"] in ("FAVORS_PROPOSED", "FAVORS_BASELINE")
    assert isinstance(fork_res["time_delta_advantage_s"], float)
    assert isinstance(fork_res["positions_gained"], int)
    assert len(fork_res["alternate_timeline"]) == 4
    assert len(fork_res["baseline_timeline"]) == 4

    # Verify alternate timeline tyre switched to HARD
    assert fork_res["alternate_timeline"][0]["tyre_compound"] == TyreCompound.HARD.value


def test_fork_timeline_with_string_inputs():
    """Verify timeline forking accepts various string formats."""
    sim = RaceSimulator(track_name="silverstone", seed=88)
    for _ in range(6):
        sim.step()

    state = sim.get_state()

    # Direct uppercase string
    res1 = CounterfactualChecker.fork_timeline(state, "PIT_MEDIUM", rollout_laps=3)
    assert res1["proposed_action"] == "PIT_MEDIUM"
    assert len(res1["alternate_timeline"]) == 3

    # Prefixed enum string
    res2 = CounterfactualChecker.fork_timeline(state, "StrategyAction.PUSH", rollout_laps=3)
    assert res2["proposed_action"] == "PUSH"

    # Lowercase string
    res3 = CounterfactualChecker.fork_timeline(state, "conserve", rollout_laps=3)
    assert res3["proposed_action"] == "CONSERVE"


def test_fork_timeline_invalid_action_fallback():
    """Verify invalid action strings gracefully fallback to MAINTAIN."""
    sim = RaceSimulator(track_name="silverstone", seed=99)
    for _ in range(5):
        sim.step()

    state = sim.get_state()
    res = CounterfactualChecker.fork_timeline(state, "INVALID_NON_EXISTENT_ACTION", rollout_laps=3)
    assert res["proposed_action"] == StrategyAction.MAINTAIN.value
    assert len(res["alternate_timeline"]) == 3
    assert len(res["baseline_timeline"]) == 3


def test_fork_timeline_near_race_finish():
    """Verify timeline forking handles reaching chequered flag without crashing."""
    sim = RaceSimulator(track_name="silverstone", seed=42)
    sim.current_lap = sim.track.total_laps - 1
    for car in sim.cars:
        car.current_lap = sim.current_lap

    state = sim.get_state()
    res = CounterfactualChecker.fork_timeline(state, StrategyAction.PUSH, rollout_laps=5)
    assert "verdict" in res
    assert isinstance(res["alternate_timeline"], list)
    assert isinstance(res["baseline_timeline"], list)
