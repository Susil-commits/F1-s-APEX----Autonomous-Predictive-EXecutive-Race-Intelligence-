"""Digital Twin state store and persistence layer with async SQLAlchemy and hot caching."""
from typing import Dict, List, Optional, Any
import os
import json
import asyncio
from datetime import datetime
from sqlalchemy import select

from backend.app.simulator.models import RaceState, DecisionExplanation
from backend.app.twin.database import get_db_session, init_db
from backend.app.twin.db_models import (
    RaceSessionModel,
    TelemetryTickModel,
    DecisionLogModel,
    BenchmarkRunModel,
)


class RaceStore:
    """
    Hybrid Write-Through Store:
    - High-frequency hot cache in memory (and optional Redis)
    - Persistent historical archive in SQLAlchemy (PostgreSQL / SQLite)
    """

    def __init__(self):
        self.active_races: Dict[str, RaceState] = {}
        self.tick_history: Dict[str, List[Dict[str, Any]]] = {}
        self.decision_history: Dict[str, List[Dict[str, Any]]] = {}
        self.benchmark_runs: List[Dict[str, Any]] = []
        self._db_initialized: bool = False

    async def ensure_db_ready(self):
        """Initializes database tables if not already done."""
        if not self._db_initialized:
            try:
                await init_db()
                self._db_initialized = True
            except Exception as e:
                print(f"[RaceStore] Warning: DB initialization deferred: {e}")

    def save_state(self, state: RaceState):
        """Saves the current tick state to in-memory hot store and tick history."""
        self.active_races[state.race_id] = state
        if state.race_id not in self.tick_history:
            self.tick_history[state.race_id] = []
        dump = state.model_dump()
        self.tick_history[state.race_id].append(dump)

        # Trigger async persistence in background task if loop is running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.persist_tick_async(state))
        except RuntimeError:
            pass

    async def persist_tick_async(self, state: RaceState):
        """Persists race session and tick snapshot asynchronously to database."""
        try:
            await self.ensure_db_ready()
            async with get_db_session() as session:
                # Upsert RaceSession
                db_session = await session.get(RaceSessionModel, state.race_id)
                if not db_session:
                    db_session = RaceSessionModel(
                        race_id=state.race_id,
                        track_name=state.track.name if hasattr(state.track, "name") else "silverstone",
                        total_laps=state.total_laps,
                        current_lap=state.current_lap,
                        is_finished=state.is_finished,
                        winner_car_id=state.winner_car_id,
                        created_at=datetime.utcnow(),
                    )
                    session.add(db_session)
                else:
                    db_session.current_lap = state.current_lap
                    db_session.is_finished = state.is_finished
                    db_session.winner_car_id = state.winner_car_id
                    db_session.updated_at = datetime.utcnow()

                # Insert TelemetryTick snapshot (every lap or state change)
                tick_entry = TelemetryTickModel(
                    race_id=state.race_id,
                    lap=state.current_lap,
                    tick_index=len(self.tick_history.get(state.race_id, [])),
                    track_condition=state.weather.condition if hasattr(state.weather, "condition") else "DRY",
                    safety_car=state.safety_car,
                    state_payload=state.model_dump(),
                    timestamp=datetime.utcnow(),
                )
                session.add(tick_entry)
        except Exception as e:
            # Silent fallback to memory store if database is offline
            pass

    def get_state(self, race_id: str) -> Optional[RaceState]:
        """Retrieves the active state for a given race ID."""
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
                    timestamp=datetime.utcnow(),
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

