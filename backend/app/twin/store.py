"""Digital Twin state store and persistence layer with async SQLAlchemy and Redis hot caching."""
from typing import Dict, List, Optional, Any
import os
import json
import logging
import asyncio
from datetime import datetime, timezone
import redis.asyncio as aioredis
from sqlalchemy import select

from backend.app.simulator.models import RaceState, DecisionExplanation
from backend.app.twin.database import get_db_session, init_db
from backend.app.twin.db_models import (
    RaceSessionModel,
    TelemetryTickModel,
    DecisionLogModel,
    BenchmarkRunModel,
)

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOT_KEY_PREFIX = "apex:race"
REDIS_HOT_TTL_SECONDS = 3600


class RaceStore:
    """
    Hybrid Write-Through Store:
    - High-frequency hot cache in memory and Redis (sub-ms reads for active tick state)
    - Persistent historical archive in SQLAlchemy (PostgreSQL / SQLite)
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.active_races: Dict[str, RaceState] = {}
        self.tick_history: Dict[str, List[Dict[str, Any]]] = {}
        self.decision_history: Dict[str, List[Dict[str, Any]]] = {}
        self.benchmark_runs: List[Dict[str, Any]] = []
        self._db_initialized: bool = False
        self.redis_url = redis_url or REDIS_URL
        self._redis_client: Optional[aioredis.Redis] = None
        self._redis_available: bool = True

    async def get_redis_client(self) -> Optional[aioredis.Redis]:
        """Lazy initialization of async Redis client connection."""
        if not self._redis_available:
            return None
        if self._redis_client is None:
            try:
                self._redis_client = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                )
                await self._redis_client.ping()
                logger.info(f"[RaceStore] Connected to Redis hot cache at {self.redis_url}")
            except Exception as e:
                logger.debug(f"[RaceStore] Redis unavailable at {self.redis_url} ({e}). Using in-memory hot store.")
                self._redis_available = False
                self._redis_client = None
        return self._redis_client

    async def ensure_db_ready(self):
        """Initializes database tables if not already done."""
        if not self._db_initialized:
            try:
                await init_db()
                self._db_initialized = True
            except Exception as e:
                logger.warning(f"[RaceStore] DB initialization deferred: {e}")

    def save_state(self, state: RaceState):
        """Saves the current tick state to in-memory hot store, Redis cache, and tick history."""
        self.active_races[state.race_id] = state
        if state.race_id not in self.tick_history:
            self.tick_history[state.race_id] = []
        dump = state.model_dump()
        self.tick_history[state.race_id].append(dump)

        # Trigger async persistence & Redis caching in background task if loop is running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.persist_tick_async(state))
                asyncio.create_task(self.cache_hot_state_redis(state))
        except RuntimeError:
            pass

    async def cache_hot_state_redis(self, state: RaceState):
        """Caches the latest tick snapshot in Redis for high-throughput sub-ms access."""
        try:
            client = await self.get_redis_client()
            if client:
                key = f"{REDIS_HOT_KEY_PREFIX}:{state.race_id}:hot_state"
                payload = state.model_dump_json()
                await client.set(key, payload, ex=REDIS_HOT_TTL_SECONDS)
                await client.set("apex:active_race_id", state.race_id, ex=REDIS_HOT_TTL_SECONDS)
        except Exception as e:
            logger.debug(f"[RaceStore] Redis cache write skipped: {e}")

    async def get_hot_state(self, race_id: str) -> Optional[RaceState]:
        """
        Retrieves the active state for a given race ID, querying Redis first
        with automatic fallback to in-memory store.
        """
        try:
            client = await self.get_redis_client()
            if client:
                key = f"{REDIS_HOT_KEY_PREFIX}:{race_id}:hot_state"
                raw = await client.get(key)
                if raw:
                    return RaceState.model_validate_json(raw)
        except Exception:
            pass
        return self.active_races.get(race_id)

    async def persist_tick_async(self, state: RaceState):
        """Persists race session and tick snapshot asynchronously to database."""
        try:
            await self.ensure_db_ready()
            async with get_db_session() as session:
                # Upsert RaceSession
                db_session = await session.get(RaceSessionModel, state.race_id)
                now = datetime.now(timezone.utc)
                if not db_session:
                    db_session = RaceSessionModel(
                        race_id=state.race_id,
                        track_name=state.track.name if hasattr(state.track, "name") else "silverstone",
                        total_laps=state.total_laps,
                        current_lap=state.current_lap,
                        is_finished=state.is_finished,
                        winner_car_id=state.winner_car_id,
                        created_at=now,
                    )
                    session.add(db_session)
                else:
                    db_session.current_lap = state.current_lap
                    db_session.is_finished = state.is_finished
                    db_session.winner_car_id = state.winner_car_id
                    db_session.updated_at = now

                # Insert TelemetryTick snapshot (every lap or state change)
                tick_entry = TelemetryTickModel(
                    race_id=state.race_id,
                    lap=state.current_lap,
                    tick_index=len(self.tick_history.get(state.race_id, [])),
                    track_condition=state.weather.condition if hasattr(state.weather, "condition") else "DRY",
                    safety_car=state.safety_car,
                    state_payload=state.model_dump(),
                    timestamp=now,
                )
                session.add(tick_entry)
        except Exception as e:
            # Silent fallback to memory store if database is offline
            pass

    def get_state(self, race_id: str) -> Optional[RaceState]:
        """Retrieves the active state for a given race ID from memory."""
        return self.active_races.get(race_id)

    def log_decision(self, race_id: str, lap: int, decision: DecisionExplanation):
        """Logs a strategic decision explanation to hot memory and persists to database."""
        if race_id not in self.decision_history:
            self.decision_history[race_id] = []
        entry = {
            "race_id": race_id,
            "lap": lap,
            "decision": decision.model_dump(),
        }
        self.decision_history[race_id].append(entry)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.persist_decision_async(race_id, lap, decision))
        except RuntimeError:
            pass

    async def persist_decision_async(self, race_id: str, lap: int, decision: DecisionExplanation):
        """Persists decision log to database."""
        try:
            await self.ensure_db_ready()
            async with get_db_session() as session:
                log_entry = DecisionLogModel(
                    race_id=race_id,
                    lap=lap,
                    recommendation=str(decision.recommendation),
                    confidence_score=decision.confidence_score,
                    urgency=decision.urgency,
                    rule_action=str(decision.rule_engine_action) if decision.rule_engine_action else None,
                    dqn_action=str(decision.dqn_action) if decision.dqn_action else None,
                    q_value_margin=decision.q_value_margin,
                    tyre_cliff_risk=decision.tyre_cliff_risk,
                    explanation_payload=decision.model_dump(),
                    timestamp=datetime.now(timezone.utc),
                )
                session.add(log_entry)
        except Exception:
            pass

    def get_decision_history(self, race_id: str) -> List[Dict[str, Any]]:
        """Retrieves all decision logs for a race."""
        return self.decision_history.get(race_id, [])

    async def get_persisted_session_ticks(self, race_id: str) -> List[Dict[str, Any]]:
        """Queries historical telemetry ticks from database for cross-session replay."""
        try:
            await self.ensure_db_ready()
            async with get_db_session() as session:
                stmt = select(TelemetryTickModel).where(TelemetryTickModel.race_id == race_id).order_by(TelemetryTickModel.tick_index)
                result = await session.execute(stmt)
                ticks = result.scalars().all()
                if ticks:
                    return [t.state_payload for t in ticks]
        except Exception:
            pass
        return self.tick_history.get(race_id, [])

    async def list_persisted_sessions(self) -> List[Dict[str, Any]]:
        """Lists all recorded race sessions in database."""
        try:
            await self.ensure_db_ready()
            async with get_db_session() as session:
                stmt = select(RaceSessionModel).order_by(RaceSessionModel.created_at.desc()).limit(20)
                result = await session.execute(stmt)
                sessions = result.scalars().all()
                return [
                    {
                        "race_id": s.race_id,
                        "track_name": s.track_name,
                        "total_laps": s.total_laps,
                        "is_finished": s.is_finished,
                        "winner_car_id": s.winner_car_id,
                        "created_at": str(s.created_at),
                    }
                    for s in sessions
                ]
        except Exception:
            pass
        return [{"race_id": r_id, "track_name": "silverstone", "total_laps": 52} for r_id in self.active_races.keys()]

    def record_benchmark(self, result: Dict[str, Any]):
        """Saves a benchmark evaluation result."""
        self.benchmark_runs.append(result)


# Singleton store instance
store = RaceStore()
