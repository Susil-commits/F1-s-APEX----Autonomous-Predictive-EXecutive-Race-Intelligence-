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
    
    # Save to store asynchronously
    await store.save_state(state)
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
    await custom_store.save_state(state)

    # get_hot_state should return valid state despite Redis being offline
    retrieved_state = await custom_store.get_hot_state(state.race_id)
    assert retrieved_state is not None
    assert retrieved_state.race_id == state.race_id
    assert retrieved_state.current_lap == state.current_lap


@pytest.mark.asyncio
async def test_race_store_multi_worker_redis_read_through(monkeypatch):
    """Tests multi-worker safe read-through: Worker B has empty memory but reads tick state from async Redis."""
    from backend.app.twin.store import RaceStore
    sim = RaceSimulator(track_name="silverstone", seed=555)
    state = sim.step()

    # Simulated in-memory Redis dict store
    redis_mock_db = {}

    class AsyncMockRedis:
        async def ping(self):
            return True

        async def set(self, key, value, ex=None):
            redis_mock_db[key] = value

        async def get(self, key):
            return redis_mock_db.get(key)

    mock_client = AsyncMockRedis()

    # Worker A: saves state asynchronously without blocking
    worker_a_store = RaceStore()
    async def mock_get_async_redis():
        return mock_client

    monkeypatch.setattr(worker_a_store, "get_async_redis", mock_get_async_redis)
    await worker_a_store.save_state(state)
    assert f"apex:race:{state.race_id}:hot_state" in redis_mock_db

    # Worker B: fresh instance with empty active_races
    worker_b_store = RaceStore()
    assert state.race_id not in worker_b_store.active_races
    monkeypatch.setattr(worker_b_store, "get_async_redis", mock_get_async_redis)

    # Worker B calls get_hot_state -> reads through Redis and populates its local active_races
    fetched = await worker_b_store.get_hot_state(state.race_id)
    assert fetched is not None
    assert fetched.race_id == state.race_id
    assert fetched.current_lap == state.current_lap
    assert state.race_id in worker_b_store.active_races


