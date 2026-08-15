"""REST API endpoints for APEX race intelligence."""
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.api.websocket import manager
from backend.app.simulator.models import StrategyAction
from backend.app.simulator.track import list_available_tracks, TRACKS


router = APIRouter(prefix="/api")


class InitRaceRequest(BaseModel):
    track_name: str = "silverstone"
    seed: int = 42


class ActionRequest(BaseModel):
    action: StrategyAction


class SpeedRequest(BaseModel):
    speed: float


class InjectRequest(BaseModel):
    event: str  # SAFETY_CAR, VSC, RAIN


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "APEX Race Intelligence API"}


@router.get("/tracks")
async def get_tracks():
    return {
        "tracks": [
            {
                "id": k,
                "name": v.name,
                "country": v.country,
                "total_laps": v.total_laps,
                "lap_distance_km": v.lap_distance_km,
                "base_lap_time_s": v.base_lap_time_s,
            }
            for k, v in TRACKS.items()
        ]
    }


@router.post("/race/init")
async def init_race(req: InitRaceRequest):
    manager.stop_loop()
    state = manager.init_race(track_name=req.track_name, seed=req.seed)
    await manager.broadcast({
        "type": "STATE_UPDATE",
        "state": state.model_dump(),
        "is_running": False,
        "sim_speed": manager.sim_speed,
    })
    return {"status": "initialized", "state": state}


@router.post("/race/play")
async def play_race():
    if not manager.is_running:
        asyncio.create_task(manager.start_loop())
    return {"status": "playing", "speed": manager.sim_speed}


@router.post("/race/pause")
async def pause_race():
    manager.stop_loop()
    return {"status": "paused"}


@router.post("/race/step")
async def step_race():
    manager.stop_loop()
    state = manager.step_once()
    if state:
        await manager.broadcast({
            "type": "STATE_UPDATE",
            "state": state.model_dump(),
            "is_running": False,
            "sim_speed": manager.sim_speed,
        })
        return {"status": "stepped", "state": state}
    return {"status": "no_active_race"}


@router.post("/race/speed")
async def set_speed(req: SpeedRequest):
    manager.set_speed(req.speed)
    await manager.broadcast({
        "type": "SPEED_CHANGED",
        "sim_speed": manager.sim_speed,
    })
    return {"status": "speed_updated", "speed": manager.sim_speed}


@router.post("/race/action")
async def apply_action(req: ActionRequest):
    manager.queue_action(req.action)
    return {"status": "action_queued", "action": req.action}


@router.post("/race/inject")
async def inject_event(req: InjectRequest):
    manager.inject_incident(req.event)
    if manager.sim:
        state = manager.sim.get_state()
        await manager.broadcast({
            "type": "EVENT_INJECTED",
            "event": req.event,
            "state": state.model_dump(),
        })
    return {"status": "event_injected", "event": req.event}


@router.get("/race/state")
async def get_current_state():
    if not manager.sim:
        manager.init_race()
    return manager.sim.get_state()
