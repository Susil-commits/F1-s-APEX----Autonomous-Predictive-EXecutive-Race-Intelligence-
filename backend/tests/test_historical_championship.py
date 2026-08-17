"""Unit tests for Phase 9: Synthetic Data Factory, Historical Replay, and Championship Tournament."""
from backend.app.simulator.historical_replay import HistoricalRaceReplay
from backend.eval.championship import ChampionshipSimulator
from backend.training.synthetic_data_factory import SyntheticDataFactory


def test_synthetic_data_factory_generation():
    df = SyntheticDataFactory.generate_scenario_dataset(n_races=2, seed=42)
    assert not df.empty
    assert "reward" in df.columns
    assert "action" in df.columns
    assert "position" in df.columns
    assert "feat_0" in df.columns


def test_historical_race_replay_silverstone():
    replays = HistoricalRaceReplay.list_available_replays()
    assert len(replays) >= 3

    res = HistoricalRaceReplay.run_historical_replay("silverstone_2023")
    assert res["total_decisions_evaluated"] >= 2
    assert "decision_points" in res
    assert 0.0 <= res["agreement_rate_pct"] <= 100.0


def test_championship_tournament_simulation():
    # Run 3 championship races for quick verification
    champ = ChampionshipSimulator.run_championship(total_races=3, seed=42)
    assert champ["total_races"] == 3
    assert len(champ["leaderboard"]) == 5
    assert champ["champion"] is not None

    top_team = champ["leaderboard"][0]
    assert top_team["points"] >= 0
    assert 1.0 <= top_team["avg_finish"] <= 10.0
