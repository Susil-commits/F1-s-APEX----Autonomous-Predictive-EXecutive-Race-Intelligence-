"""WebSocket live streaming and race control loop."""
import asyncio
import json
from typing import Set, Optional
from fastapi import WebSocket, WebSocketDisconnect

from backend.app.simulator.engine import RaceSimulator
from backend.app.simulator.models import RaceState, StrategyAction, SafetyCarStatus, TrackCondition
from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.strategy.dqn_agent import DQNAgent
from backend.app.strategy.explainability import ExplainabilityEngine
from backend.app.twin.store import store


class ConnectionManager:
    """Manages active client WebSocket connections and race loop broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.sim: Optional[RaceSimulator] = None
        self.dqn_agent = DQNAgent()
        self.is_running = False
        self.sim_speed = 1.0  # 1.0x, 2.0x, 5.0x, etc.
        self.loop_task: Optional[asyncio.Task] = None
        self._queued_player_action: Optional[StrategyAction] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Send current state immediately on connect
        if self.sim:
            state = self.sim.get_state()
            await websocket.send_text(json.dumps({
                "type": "STATE_UPDATE",
                "state": state.model_dump(),
                "is_running": self.is_running,
                "sim_speed": self.sim_speed,
            }))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)

    def init_race(self, track_name: str = "silverstone", seed: int = 42) -> RaceState:
        """Initializes a new race session."""
        self.sim = RaceSimulator(track_name=track_name, seed=seed)
        # Process initial state & explanation
        state = self.sim.step()
        self._enrich_state(state)
        store.save_state(state)
        return state

    def queue_action(self, action: StrategyAction):
        """Queues a strategy action for the player car."""
        self._queued_player_action = action

    def step_once(self) -> RaceState:
        """Advances the simulation by exactly one lap tick."""
        if not self.sim or self.sim.is_finished:
            return self.sim.get_state() if self.sim else None

        action = self._queued_player_action
        self._queued_player_action = None

        state = self.sim.step(player_action=action)
        self._enrich_state(state)
        store.save_state(state)
        return state

    def _enrich_state(self, state: RaceState):
        """Runs intelligence & RL pipeline and attaches explainability to state."""
        obs = FeatureBuilder.extract_features(state)
        dqn_action, q_margin = self.dqn_agent.predict_action(obs)

        explanation = ExplainabilityEngine.generate_explanation(
            sim=self.sim,
            dqn_action=dqn_action,
            q_value_margin=q_margin,
            include_counterfactual=True,
        )
        state.active_decision = explanation
        store.log_decision(state.race_id, state.current_lap, explanation)

    async def start_loop(self):
        """Starts background async loop ticking the race."""
        if self.is_running:
            return
        self.is_running = True
        if self.sim is None:
            self.init_race()

        while self.is_running and self.sim and not self.sim.is_finished:
            state = self.step_once()
            await self.broadcast({
                "type": "STATE_UPDATE",
                "state": state.model_dump(),
                "is_running": self.is_running,
                "sim_speed": self.sim_speed,
            })

            # Calculate sleep based on sim_speed (1.0s / sim_speed)
            delay = max(0.05, 1.0 / max(0.1, self.sim_speed))
            await asyncio.sleep(delay)

        if self.sim and self.sim.is_finished:
            self.is_running = False
            await self.broadcast({
                "type": "RACE_FINISHED",
                "state": self.sim.get_state().model_dump(),
            })

    def stop_loop(self):
        """Pauses the simulation loop."""
        self.is_running = False

    def set_speed(self, speed: float):
        """Adjusts the simulation speed multiplier."""
        self.sim_speed = max(0.2, min(20.0, speed))

    def inject_incident(self, incident_type: str):
        """Manually triggers Safety Car or Weather change for dynamic strategy testing."""
        if not self.sim:
            return
        if incident_type == "SAFETY_CAR":
            self.sim.safety_car = SafetyCarStatus.SAFETY_CAR
            self.sim.safety_car_laps_remaining = 4
            self.sim._log_event(self.sim.current_lap, "SAFETY_CAR", "RACE CONTROL: Physical Safety Car deployed!")
        elif incident_type == "VSC":
            self.sim.safety_car = SafetyCarStatus.VSC
            self.sim.safety_car_laps_remaining = 3
            self.sim._log_event(self.sim.current_lap, "VSC", "RACE CONTROL: Virtual Safety Car (VSC) deployed!")
        elif incident_type == "RAIN":
            self.sim.weather.condition = TrackCondition.WET
            self.sim.weather.rain_intensity = 0.80
            self.sim._log_event(self.sim.current_lap, "WEATHER", "WEATHER ALERT: Sudden heavy downpour hit the track!")


manager = ConnectionManager()
