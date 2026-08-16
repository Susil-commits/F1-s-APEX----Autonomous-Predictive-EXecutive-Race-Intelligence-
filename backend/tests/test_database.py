"""Unit tests for SQLAlchemy async database models and persistent RaceStore."""
import pytest
from backend.app.simulator.engine import RaceSimulator
from backend.app.twin.database import init_db, get_db_session
from backend.app.twin.db_models import RaceSessionModel, TelemetryTickModel
from backend.app.twin.store import store
from sqlalchemy import select


@pytest.mark.asyncio
async def test_database_initialization():
    await init_db()
    async with get_db_session() as session:
        result = await session.execute(select(RaceSessionModel))
        assert result is not None


@pytest.mark.asyncio
async def test_race_store_async_persistence():
    sim = RaceSimulator(track_name="silverstone", seed=999)
    state = sim.step()
    
    # Save to store
    store.save_state(state)
    assert store.get_state(state.race_id) is not None
    
    # Test async tick persistence
    await store.persist_tick_async(state)
    ticks = await store.get_persisted_session_ticks(state.race_id)
    assert len(ticks) >= 1
    assert ticks[0]["race_id"] == state.race_id


@pytest.mark.asyncio
async def test_list_persisted_sessions():
    sim = RaceSimulator(track_name="silverstone", seed=888)
    state = sim.step()
    await store.persist_tick_async(state)

    sessions = await store.list_persisted_sessions()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1


@pytest.mark.asyncio
async def test_race_store_redis_hot_cache_fallback():
    """Tests that get_hot_state seamlessly falls back to in-memory store when Redis is unavailable or offline."""
    from backend.app.twin.store import RaceStore
    custom_store = RaceStore(redis_url="redis://non_existent_redis_host:6379/0")
    sim = RaceSimulator(track_name="silverstone", seed=777)
    state = sim.step()

    # Save state
    custom_store.save_state(state)

    # get_hot_state should return valid state despite Redis being offline
    retrieved_state = await custom_store.get_hot_state(state.race_id)
    assert retrieved_state is not None
    assert retrieved_state.race_id == state.race_id
    assert retrieved_state.current_lap == state.current_lap

