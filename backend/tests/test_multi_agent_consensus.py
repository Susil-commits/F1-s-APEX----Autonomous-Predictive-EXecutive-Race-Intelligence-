"""Pytest suite for Multi-Agent Pit Wall Consensus & Deliberation Engine."""
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.intelligence.multi_agent_consensus import (
    MultiAgentPitWallEngine,
    PitWallConsensus,
)
from backend.app.main import app
from backend.app.simulator.models import (
    CarState,
    RaceState,
    SafetyCarStatus,
    StrategyAction,
    TrackConfig,
    TyreCompound,
    WeatherState,
)


def test_multi_agent_dry_consensus_evaluation():
    engine = MultiAgentPitWallEngine.get_instance()

    car = CarState(
        car_id="CAR_01",
        driver_name="Max Verstappen",
        team_name="Red Bull Racing",
        car_number=1,
        is_player=True,
        position=1,
        current_lap=15,
        tyre_compound=TyreCompound.MEDIUM,
        tyre_age_laps=10,
        tyre_wear_pct=30.0,
    )

    state = RaceState(
        race_id="test-consensus-dry",
        seed=42,
        track=TrackConfig(name="Silverstone", total_laps=52),
        current_lap=15,
        total_laps=52,
        weather=WeatherState(rain_intensity=0.0, track_wetness=0.0),
        cars=[car],
    )

    consensus = engine.evaluate_pitwall_consensus(state)
    assert isinstance(consensus, PitWallConsensus)
    assert len(consensus.proposals) == 5
    assert len(consensus.pitwall_radio_transcript) == 5
    assert consensus.consensus_action in (StrategyAction.MAINTAIN, StrategyAction.PUSH)
    assert consensus.consensus_confidence >= 0.5


def test_multi_agent_wet_weather_consensus_override():
    engine = MultiAgentPitWallEngine.get_instance()

    car = CarState(
        car_id="CAR_01",
        driver_name="Lewis Hamilton",
        team_name="Ferrari",
        car_number=44,
        is_player=True,
        position=2,
        current_lap=25,
        tyre_compound=TyreCompound.MEDIUM,
        tyre_age_laps=15,
        tyre_wear_pct=45.0,
    )

    # Inject heavy rain
    state = RaceState(
        race_id="test-consensus-wet",
        seed=42,
        track=TrackConfig(name="Spa", total_laps=44),
        current_lap=25,
        total_laps=44,
        weather=WeatherState(rain_intensity=0.75, track_wetness=0.82),
        cars=[car],
    )

    consensus = engine.evaluate_pitwall_consensus(state)
    assert consensus.consensus_action in (StrategyAction.PIT_WET, StrategyAction.PIT_INTER)
    met_proposal = next(p for p in consensus.proposals if p.agent_id == "met_officer")
    assert met_proposal.proposed_action == StrategyAction.PIT_WET
    assert met_proposal.confidence >= 0.90


def test_multi_agent_safety_car_opportunism():
    engine = MultiAgentPitWallEngine.get_instance()

    car = CarState(
        car_id="CAR_01",
        driver_name="Lando Norris",
        team_name="McLaren",
        car_number=4,
        is_player=True,
        position=1,
        current_lap=30,
        tyre_compound=TyreCompound.MEDIUM,
        tyre_age_laps=22,
        tyre_wear_pct=58.0,
    )

    state = RaceState(
        race_id="test-consensus-sc",
        seed=42,
        track=TrackConfig(name="Monza", total_laps=53),
        current_lap=30,
        total_laps=53,
        safety_car=SafetyCarStatus.SAFETY_CAR,
        weather=WeatherState(),
        cars=[car],
    )

    consensus = engine.evaluate_pitwall_consensus(state)
    chief_proposal = next(p for p in consensus.proposals if p.agent_id == "chief_strategist")
    assert chief_proposal.proposed_action in (StrategyAction.PIT_HARD, StrategyAction.PIT_MEDIUM)


@pytest.mark.asyncio
async def test_pitwall_consensus_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/race/init", json={"track_name": "silverstone", "seed": 42})
        res = await ac.get("/api/strategy/pitwall-consensus/default")
        assert res.status_code == 200
        data = res.json()
        assert "consensus_action" in data
        assert "proposals" in data
        assert len(data["proposals"]) == 5
        assert "pitwall_radio_transcript" in data
