"""Unit tests for the Redis L2 hot-cache tier, write-through/read-through round-trips, and graceful degradation."""
from typing import Any, cast
import pytest
import json
import redis.asyncio as aioredis
from unittest.mock import AsyncMock, MagicMock

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import RaceState, DecisionExplanation, StrategyAction
from backend.app.twin.store import RaceStore, REDIS_HOT_KEY_PREFIX, REDIS_HOT_TTL_SECONDS


@pytest.mark.asyncio
async def test_redis_write_through_and_read_through_roundtrip():
    """Verify that save_state writes through to Redis and a separate worker read-through restores state."""
    # Simulated Redis storage backend
    redis_storage = {}

    class AsyncMockRedisClient:
        async def ping(self):
            return True

        async def set(self, key, value, ex=None):
            redis_storage[key] = {"value": value, "ex": ex}

        async def get(self, key):
            entry = redis_storage.get(key)
            return entry["value"] if entry else None

    mock_client = cast(Any, AsyncMockRedisClient())

    # 1. Worker A: initializes simulation and writes through to Redis
    worker_a_store = RaceStore()
    worker_a_store._async_redis = mock_client
    worker_a_store._redis_available = True

    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.step()

    await worker_a_store.save_state(state)

    # Assert Redis keys were populated with correct TTL
    hot_state_key = f"{REDIS_HOT_KEY_PREFIX}:{state.race_id}:hot_state"
    latest_id_key = f"{REDIS_HOT_KEY_PREFIX}:latest_active_id"

    assert hot_state_key in redis_storage
    assert latest_id_key in redis_storage
    assert redis_storage[hot_state_key]["ex"] == REDIS_HOT_TTL_SECONDS
    assert redis_storage[latest_id_key]["value"] == state.race_id

    # 2. Worker B: independent instance with empty in-memory cache
    worker_b_store = RaceStore()
    worker_b_store._async_redis = mock_client
    worker_b_store._redis_available = True

    assert state.race_id not in worker_b_store.active_races

    # Read-through from Redis
    restored_state = await worker_b_store.get_hot_state(state.race_id)

    assert restored_state is not None
    assert restored_state.race_id == state.race_id
    assert restored_state.current_lap == state.current_lap
    # Assert local L1 memory is now populated
    assert state.race_id in worker_b_store.active_races


@pytest.mark.asyncio
async def test_redis_decision_logging_write_through():
    """Verify that log_decision writes the decision explanation to Redis."""
    redis_storage = {}

    class AsyncMockRedisClient:
        async def ping(self):
            return True

        async def set(self, key, value, ex=None):
            redis_storage[key] = {"value": value, "ex": ex}

    mock_client = cast(Any, AsyncMockRedisClient())

    store_instance = RaceStore()
    store_instance._async_redis = mock_client
    store_instance._redis_available = True

    decision = DecisionExplanation(
        recommendation=StrategyAction.PIT_HARD,
        rule_engine_action=StrategyAction.PIT_HARD,
        confidence_score=0.94,
        urgency="HIGH",
        primary_factors=["TYRE_DEGRADATION_ELEVATED"],
        expected_time_delta_s=-1.25,
    )

    await store_instance.log_decision("race_test_123", lap=18, decision=decision)

    dec_key = f"{REDIS_HOT_KEY_PREFIX}:race_test_123:latest_decision"
    assert dec_key in redis_storage
    assert redis_storage[dec_key]["ex"] == REDIS_HOT_TTL_SECONDS

    parsed = json.loads(redis_storage[dec_key]["value"])
    assert parsed["race_id"] == "race_test_123"
    assert parsed["lap"] == 18
    assert parsed["decision"]["recommendation"] == "PIT_HARD"


@pytest.mark.asyncio
async def test_redis_unreachable_graceful_degradation(monkeypatch):
    """Verify that when Redis is completely unreachable (connection error/timeout), the store falls back to in-memory tier."""
    broken_store = RaceStore(redis_url="redis://127.0.0.1:9999/0")

    async def mock_raising_get_redis():
        raise aioredis.ConnectionError("Could not connect to Redis: connection refused")

    monkeypatch.setattr(broken_store, "get_async_redis", mock_raising_get_redis)

    sim = RaceSimulator(track_name="silverstone", seed=99)
    state = sim.step()

    # save_state must not raise
    await broken_store.save_state(state)
    assert broken_store.get_state(state.race_id) is not None

    # get_hot_state must not raise and return the in-memory state
    retrieved = await broken_store.get_hot_state(state.race_id)
    assert retrieved is not None
    assert retrieved.race_id == state.race_id

    # log_decision must not raise
    decision = DecisionExplanation(
        recommendation=StrategyAction.MAINTAIN,
        rule_engine_action=StrategyAction.MAINTAIN,
        confidence_score=0.88,
        urgency="LOW",
    )
    await broken_store.log_decision(state.race_id, lap=1, decision=decision)
    assert len(broken_store.get_decision_history(state.race_id)) == 1


@pytest.mark.asyncio
async def test_redis_runtime_write_failure_graceful_degradation():
    """Verify that runtime Redis communication errors during set/get do not crash caller."""
    class FailingRedisClient:
        async def ping(self):
            return True

        async def set(self, key, value, ex=None):
            raise aioredis.TimeoutError("Redis socket timeout during write")

        async def get(self, key):
            raise aioredis.ConnectionError("Redis connection dropped during read")

    store_instance = RaceStore()
    store_instance._async_redis = cast(Any, FailingRedisClient())
    store_instance._redis_available = True

    sim = RaceSimulator(track_name="silverstone", seed=55)
    state = sim.step()

    # save_state survives write failure
    await store_instance.save_state(state)
    assert store_instance.get_state(state.race_id) is not None

    # get_hot_state survives read failure
    res = await store_instance.get_hot_state(state.race_id)
    assert res is not None
    assert res.race_id == state.race_id


@pytest.mark.asyncio
async def test_redis_lazy_initialization_marks_unavailable_on_error():
    """Verify that a failure during from_url / ping marks _redis_available = False to fail fast."""
    store_instance = RaceStore(redis_url="redis://invalid-host-that-does-not-exist:6379/0")
    assert store_instance._redis_available is True
    assert store_instance._async_redis is None

    client = await store_instance.get_async_redis()
    assert client is None
    assert store_instance._redis_available is False

    # Subsequent call immediately returns None without re-attempting connection
    client_again = await store_instance.get_async_redis()
    assert client_again is None
