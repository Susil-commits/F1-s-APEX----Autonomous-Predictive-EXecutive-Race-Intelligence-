"""WebSocket live streaming and multi-session race control loop."""
import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from backend.app.intelligence.commentary_generator import generate_commentary
from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import (
    RaceState,
    SafetyCarStatus,
    StrategyAction,
    TrackCondition,
)
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.strategy.explainability import ExplainabilityEngine
from backend.app.twin.store import store

logger = logging.getLogger(__name__)


class RaceSession:
    """Encapsulates state, active connections, and simulation loop for a single race session."""

    def __init__(
        self,
        session_id: str = "default",
        track_name: str = "silverstone",
        seed: int = 42,
    ):
        self.session_id = session_id
        self.track_name = track_name
        self.seed = seed
        self.sim: RaceSimulator | None = RaceSimulator(track_name=track_name, seed=seed)
        self.active_connections: set[WebSocket] = set()
        self.is_running: bool = False
        self.sim_speed: float = 1.0
        self.loop_task: asyncio.Task | None = None
        self._queued_player_action: StrategyAction | None = None


class ConnectionManager:
    """Manages active client WebSocket connections and multi-session race loop broadcasting."""

    def __init__(self):
        self.sessions: dict[str, RaceSession] = {}
        self.dqn_agent = DQNAgent()
        # Initialize default session for baseline compatibility
        self._default_session_id = "default"
        self._get_or_create_session(self._default_session_id)

    def _get_or_create_session(
        self,
        session_id: str = "default",
        track_name: str = "silverstone",
        seed: int = 42,
    ) -> RaceSession:
        """Retrieves an existing session or creates a new isolated one."""
        sid = session_id or self._default_session_id
        if sid not in self.sessions:
            self.sessions[sid] = RaceSession(
                session_id=sid,
                track_name=track_name,
                seed=seed,
            )
        return self.sessions[sid]

    # --- Backward compatibility properties mapping to default session ---
    @property
    def sim(self) -> RaceSimulator | None:
        session = self.sessions.get(self._default_session_id)
        return session.sim if session else None

    @sim.setter
    def sim(self, value: RaceSimulator | None):
        session = self._get_or_create_session(self._default_session_id)
        session.sim = value

    @property
    def active_connections(self) -> set[WebSocket]:
        session = self.sessions.get(self._default_session_id)
        return session.active_connections if session else set()

    @property
    def is_running(self) -> bool:
        session = self.sessions.get(self._default_session_id)
        return session.is_running if session else False

    @is_running.setter
    def is_running(self, value: bool):
        session = self._get_or_create_session(self._default_session_id)
        session.is_running = value

    @property
    def sim_speed(self) -> float:
        session = self.sessions.get(self._default_session_id)
        return session.sim_speed if session else 1.0

    @sim_speed.setter
    def sim_speed(self, value: float):
        session = self._get_or_create_session(self._default_session_id)
        session.sim_speed = value

    # --- Multi-session connection and broadcast methods ---
    async def connect(self, websocket: WebSocket, session_id: str = "default"):
        await websocket.accept()
        session = self._get_or_create_session(session_id)
        session.active_connections.add(websocket)

        # Send current state immediately on connect
        if session.sim:
            state = session.sim.get_state()
            await websocket.send_text(json.dumps({
                "type": "STATE_UPDATE",
                "session_id": session.session_id,
                "state": state.model_dump(),
                "is_running": session.is_running,
                "sim_speed": session.sim_speed,
            }))

    def disconnect(self, websocket: WebSocket, session_id: str = "default"):
        sid = session_id or self._default_session_id
        session = self.sessions.get(sid)
        if session:
            session.active_connections.discard(websocket)
            # If a non-default session has no active connections, clean it up
            if sid != self._default_session_id and len(session.active_connections) == 0:
                if session.loop_task and not session.loop_task.done():
                    session.loop_task.cancel()
                self.sessions.pop(sid, None)
        else:
            # Fallback scan across all sessions
            for s in list(self.sessions.values()):
                s.active_connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any], session_id: str = "default"):
        session = self.sessions.get(session_id or self._default_session_id)
        if not session or not session.active_connections:
            return
        payload = json.dumps(message)
        dead = []
        for connection in list(session.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for d in dead:
            session.active_connections.discard(d)

    async def init_race(
        self,
        track_name: str = "silverstone",
        seed: int = 42,
        session_id: str = "default",
    ) -> RaceState:
        """Initializes a new race session."""
        session = self._get_or_create_session(session_id, track_name=track_name, seed=seed)
        session.sim = RaceSimulator(track_name=track_name, seed=seed)
        session.track_name = track_name
        session.seed = seed

        # Process initial state & explanation
        state = session.sim.step()
        await self._enrich_state(state, sim=session.sim)
        await store.save_state(state)
        return state

    def queue_action(self, action: StrategyAction, session_id: str = "default"):
        """Queues a strategy action for the player car in the specified session."""
        session = self._get_or_create_session(session_id)
        session._queued_player_action = action

    async def step_once(self, session_id: str = "default", include_counterfactual: bool = False) -> RaceState | None:
        """Manually triggers a single simulation step for a session."""
        session = self._get_or_create_session(session_id)
        if not session or not session.sim or session.sim.is_finished:
            return session.sim.get_state() if (session and session.sim) else None

        action = session._queued_player_action
        session._queued_player_action = None

        state = session.sim.step(player_action=action)
        try:
            from backend.app.api.metrics import APEX_LAPS_SIMULATED
            APEX_LAPS_SIMULATED.inc()
        except Exception:
            pass

        await self._enrich_state(state, sim=session.sim, include_counterfactual=include_counterfactual)
        await store.save_state(state)
        return state

    async def _enrich_state(self, state: RaceState, sim: RaceSimulator | None = None, include_counterfactual: bool = False):
        """Runs intelligence & RL pipeline and attaches explainability to state."""
        import time
        start_t = time.perf_counter()

        target_sim = sim or self.sim
        obs = FeatureBuilder.extract_features(state)
        dqn_action, q_margin = self.dqn_agent.predict_action(obs)

        # Trigger counterfactual rollouts when explicitly requested or during safety car
        should_run_counterfactual = (
            include_counterfactual
            or (target_sim is not None and target_sim.safety_car.value != "NONE")
        )

        explanation = ExplainabilityEngine.generate_explanation(
            sim=target_sim,
            dqn_action=dqn_action,
            q_value_margin=q_margin,
            include_counterfactual=should_run_counterfactual,
            dqn_agent=self.dqn_agent,
        )
        # Generate and attach LLM / persona radio commentary line
        try:
            explanation.commentary = generate_commentary(
                explanation=explanation,
                current_lap=state.current_lap,
                persona="apex_core",
            )
        except Exception:
            pass

        state.active_decision = explanation
        await store.log_decision(state.race_id, state.current_lap, explanation)

        try:
            from backend.app.api.metrics import APEX_DECISION_LATENCY
            duration = time.perf_counter() - start_t
            APEX_DECISION_LATENCY.observe(duration)
        except Exception:
            pass

    async def start_loop(self, session_id: str = "default"):
        """Starts background async loop ticking the race for a specific session."""
        session = self._get_or_create_session(session_id)
        if session.is_running:
            return
        session.is_running = True
        if session.sim is None:
            await self.init_race(session_id=session.session_id)

        while session.is_running and session.sim and not session.sim.is_finished:
            state = await self.step_once(session_id=session.session_id)
            if state:
                await self.broadcast(
                    {
                        "type": "STATE_UPDATE",
                        "session_id": session.session_id,
                        "state": state.model_dump(),
                        "is_running": session.is_running,
                        "sim_speed": session.sim_speed,
                    },
                    session_id=session.session_id,
                )

            # Calculate sleep based on sim_speed (1.0s / sim_speed)
            delay = max(0.05, 1.0 / max(0.1, session.sim_speed))
            await asyncio.sleep(delay)

        if session.sim and session.sim.is_finished:
            session.is_running = False
            await self.broadcast(
                {
                    "type": "RACE_FINISHED",
                    "session_id": session.session_id,
                    "state": session.sim.get_state().model_dump(),
                },
                session_id=session.session_id,
            )

    def stop_loop(self, session_id: str = "default"):
        """Pauses the simulation loop for the specified session."""
        session = self.sessions.get(session_id or self._default_session_id)
        if session:
            session.is_running = False

    def set_speed(self, speed: float, session_id: str = "default"):
        """Adjusts the simulation speed multiplier for the specified session."""
        session = self._get_or_create_session(session_id)
        session.sim_speed = max(0.2, min(20.0, speed))

    def inject_incident(self, incident_type: str, session_id: str = "default"):
        """Manually triggers Safety Car or Weather change for dynamic strategy testing."""
        session = self.sessions.get(session_id or self._default_session_id)
        if not session or not session.sim:
            return
        if incident_type == "SAFETY_CAR":
            session.sim.safety_car = SafetyCarStatus.SAFETY_CAR
            session.sim.safety_car_laps_remaining = 4
            session.sim._log_event(session.sim.current_lap, "SAFETY_CAR", "RACE CONTROL: Physical Safety Car deployed!")
        elif incident_type == "VSC":
            session.sim.safety_car = SafetyCarStatus.VSC
            session.sim.safety_car_laps_remaining = 3
            session.sim._log_event(session.sim.current_lap, "VSC", "RACE CONTROL: Virtual Safety Car (VSC) deployed!")
        elif incident_type == "RAIN":
            session.sim.weather.condition = TrackCondition.WET
            session.sim.weather.rain_intensity = 0.80
            session.sim._log_event(session.sim.current_lap, "WEATHER", "WEATHER ALERT: Sudden heavy downpour hit the track!")


manager = ConnectionManager()
