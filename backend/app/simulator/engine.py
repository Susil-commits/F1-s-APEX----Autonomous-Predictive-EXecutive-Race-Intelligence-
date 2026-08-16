"""Deterministic Race Simulator Engine for APEX."""
from __future__ import annotations

import copy
import uuid
from typing import List, Dict, Optional, Tuple
import numpy as np

from backend.app.simulator.models import (
    CarState,
    RaceState,
    TrackConfig,
    WeatherState,
    TrackCondition,
    TyreCompound,
    DrivingMode,
    StrategyAction,
    SafetyCarStatus,
    RaceEvent,
)
from backend.app.simulator.car import CarPhysics
from backend.app.simulator.track import get_track


DEFAULT_DRIVERS = [
    {"car_id": "car_01", "name": "M. Verstappen", "team": "Red Bull Racing", "number": 1, "is_player": False, "pace_bias": -0.25},
    {"car_id": "car_02", "name": "L. Norris", "team": "McLaren", "number": 4, "is_player": False, "pace_bias": -0.15},
    {"car_id": "car_03", "name": "C. Leclerc", "team": "Ferrari", "number": 16, "is_player": False, "pace_bias": -0.10},
    {"car_id": "car_04", "name": "APEX AI (You)", "team": "APEX Strategy Team", "number": 44, "is_player": True, "pace_bias": -0.05},
    {"car_id": "car_05", "name": "O. Piastri", "team": "McLaren", "number": 81, "is_player": False, "pace_bias": 0.00},
    {"car_id": "car_06", "name": "G. Russell", "team": "Mercedes", "number": 63, "is_player": False, "pace_bias": 0.05},
    {"car_id": "car_07", "name": "C. Sainz", "team": "Ferrari", "number": 55, "is_player": False, "pace_bias": 0.08},
    {"car_id": "car_08", "name": "L. Hamilton", "team": "Mercedes", "number": 44, "is_player": False, "pace_bias": 0.10},
    {"car_id": "car_09", "name": "F. Alonso", "team": "Aston Martin", "number": 14, "is_player": False, "pace_bias": 0.20},
    {"car_id": "car_10", "name": "S. Perez", "team": "Red Bull Racing", "number": 11, "is_player": False, "pace_bias": 0.25},
]


class RaceSimulator:
    """Deterministic, seed-governed race simulation engine."""

    def __init__(
        self,
        track_name: str = "silverstone",
        seed: int = 42,
        grid_size: int = 10,
        enable_dynamic_weather: bool = True,
    ):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.track = get_track(track_name)
        self.race_id = f"race_{uuid.uuid4().hex[:8]}"
        self.enable_dynamic_weather = enable_dynamic_weather
        
        self.current_lap = 0
        self.tick = 0
        self.race_time_s = 0.0
        self.is_finished = False
        self.winner_car_id: Optional[str] = None
        
        self.safety_car = SafetyCarStatus.NONE
        self.safety_car_laps_remaining = 0
        
        # Initialize weather
        self.weather = WeatherState(
            condition=TrackCondition.DRY,
            rain_intensity=0.0,
            track_temp_c=32.0 + float(self.rng.normal(0, 2.0)),
            air_temp_c=23.0 + float(self.rng.normal(0, 1.5)),
            rain_probability_next_5_laps=self.track.rain_probability_base,
            drying_rate_per_lap=0.08,
        )
        
        # Initialize cars on starting grid
        self.cars: List[CarState] = []
        drivers_subset = DEFAULT_DRIVERS[:grid_size]
        for idx, d in enumerate(drivers_subset):
            # Starting tyre strategy heuristic for AI cars
            start_tyre = TyreCompound.MEDIUM if idx % 2 == 0 else TyreCompound.SOFT
            if d["is_player"]:
                start_tyre = TyreCompound.MEDIUM

            car = CarState(
                car_id=d["car_id"],
                driver_name=d["name"],
                team_name=d["team"],
                car_number=d["number"],
                is_player=d["is_player"],
                position=idx + 1,
                current_lap=1,
                lap_progress_pct=0.0,
                total_race_time_s=0.0,
                gap_to_leader_s=idx * 0.4, # 0.4s grid interval spacing
                gap_to_car_ahead_s=0.4 if idx > 0 else 0.0,
                gap_to_car_behind_s=0.4 if idx < len(drivers_subset) - 1 else 0.0,
                tyre_compound=start_tyre,
                tyre_age_laps=0,
                tyre_wear_pct=0.0,
                fuel_kg=100.0,
                fuel_burn_per_lap_kg=round(100.0 / self.track.total_laps, 2),
                driving_mode=DrivingMode.NORMAL,
                in_pit=False,
                pit_count=0,
                laps_since_last_pit=0,
            )
            self.cars.append(car)

        self.events_log: List[RaceEvent] = [
            RaceEvent(
                lap=0,
                timestamp_s=0.0,
                event_type="RACE_START",
                message=f"Lights out at {self.track.name}! {len(self.cars)} cars on the grid.",
            )
        ]

    def get_player_car(self) -> CarState:
        """Retrieve the primary player car."""
        for car in self.cars:
            if car.is_player:
                return car
        return self.cars[0]

    def apply_action(self, action: StrategyAction, target_car_id: Optional[str] = None):
        """Applies a strategic decision to the player car (or specified car)."""
        target = self.get_player_car() if target_car_id is None else next((c for c in self.cars if c.car_id == target_car_id), None)
        if not target or target.is_dnf:
            return

        if action == StrategyAction.PUSH:
            target.driving_mode = DrivingMode.PUSH
            self._log_event(target.current_lap, "STRATEGY", f"{target.driver_name} switched mode to PUSH", target.car_id)
        elif action == StrategyAction.CONSERVE:
            target.driving_mode = DrivingMode.CONSERVE
            self._log_event(target.current_lap, "STRATEGY", f"{target.driver_name} switched mode to CONSERVE", target.car_id)
        elif action == StrategyAction.MAINTAIN:
            pass # Keep current state
        elif action in (StrategyAction.PIT_SOFT, StrategyAction.PIT_MEDIUM, StrategyAction.PIT_HARD, StrategyAction.PIT_INTER, StrategyAction.PIT_WET):
            compound_map = {
                StrategyAction.PIT_SOFT: TyreCompound.SOFT,
                StrategyAction.PIT_MEDIUM: TyreCompound.MEDIUM,
                StrategyAction.PIT_HARD: TyreCompound.HARD,
                StrategyAction.PIT_INTER: TyreCompound.INTERMEDIATE,
                StrategyAction.PIT_WET: TyreCompound.WET,
            }
            target.pit_stop_queued_compound = compound_map[action]
            target.in_pit = True
            self._log_event(target.current_lap, "BOX_CALL", f"BOX BOX: {target.driver_name} scheduled to pit for {compound_map[action].value}", target.car_id)

    def step(self, player_action: Optional[StrategyAction] = None) -> RaceState:
        """Advances the simulation by 1 lap tick."""
        if self.is_finished:
            return self.get_state()

        self.current_lap += 1
        self.tick += 1

        # 1. Apply player action if provided
        if player_action is not None:
            self.apply_action(player_action)

        # 2. Update Weather dynamics
        self._update_weather()

        # 3. Update Safety Car state
        self._update_safety_car()

        # 4. Process AI Competitor pit heuristics
        self._process_ai_competitor_strategies()

        # 5. Simulate lap for every car
        lap_times: Dict[str, float] = {}
        for car in self.cars:
            if car.is_dnf:
                continue

            # Execute pit stop if queued
            if car.in_pit and car.pit_stop_queued_compound:
                old_compound = car.tyre_compound
                car.tyre_compound = car.pit_stop_queued_compound
                car.tyre_age_laps = 0
                car.tyre_wear_pct = 0.0
                car.tyre_cliff_reached = False
                car.pit_count += 1
                car.laps_since_last_pit = 0
                car.pit_stop_queued_compound = None
                self._log_event(self.current_lap, "PIT_STOP", f"{car.driver_name} pitted (Lap {self.current_lap}): Swapped {old_compound.value} -> {car.tyre_compound.value}", car.car_id)

            # Check if in dirty air (within 1.2s behind another car)
            in_traffic = car.gap_to_car_ahead_s < 1.2 and car.position > 1

            # Compute lap time
            lt = CarPhysics.calculate_lap_time(
                car=car,
                track=self.track,
                weather=self.weather,
                safety_car=self.safety_car,
                in_traffic=in_traffic,
                rng=self.rng,
            )

            # Apply driver pace bias
            driver_info = next((d for d in DEFAULT_DRIVERS if d["car_id"] == car.car_id), None)
            if driver_info:
                lt += driver_info.get("pace_bias", 0.0)

            lap_times[car.car_id] = lt
            car.last_lap_time_s = lt
            if car.best_lap_time_s is None or lt < car.best_lap_time_s:
                car.best_lap_time_s = lt

            car.total_race_time_s += lt
            car.current_lap = self.current_lap
            car.laps_since_last_pit += 1
            car.tyre_age_laps += 1

            # Update Tyre Wear & Cliff
            new_wear, cliff = CarPhysics.calculate_tyre_wear(
                compound=car.tyre_compound,
                current_wear_pct=car.tyre_wear_pct,
                mode=car.driving_mode,
                track_wear_factor=self.track.tyre_wear_factor,
                weather=self.weather,
                rng=self.rng,
            )
            car.tyre_wear_pct = new_wear
            car.tyre_cliff_reached = cliff

            # Update Fuel Burn
            mode_burn = MODE_SPECS_MULTIPLIER = 1.20 if car.driving_mode == DrivingMode.PUSH else (0.80 if car.driving_mode == DrivingMode.CONSERVE else 1.0)
            burn = car.fuel_burn_per_lap_kg * mode_burn
            car.fuel_kg = max(0.5, car.fuel_kg - burn)

            # Reset pit status after completing the lap
            car.in_pit = False

        # 6. Re-sort leaderboard and calculate gaps
        self._update_leaderboard()

        # 7. Check race completion
        if self.current_lap >= self.track.total_laps:
            self.is_finished = True
            self.winner_car_id = self.cars[0].car_id
            self._log_event(self.current_lap, "CHEQUERED_FLAG", f"Chequered flag! Winner: {self.cars[0].driver_name} ({self.cars[0].team_name})", self.winner_car_id)

        self.race_time_s = self.cars[0].total_race_time_s if self.cars else 0.0
        return self.get_state()

    def _update_weather(self):
        """Advances weather smoothly with persistent weather spells and continuous drying."""
        if not self.enable_dynamic_weather:
            return

        rand_val = float(self.rng.random())

        if self.weather.condition == TrackCondition.DRY:
            # Low probability of rain onset (~2.5% per lap)
            if rand_val < self.track.rain_probability_base * 0.15:
                self.weather.condition = TrackCondition.DAMP
                self.weather.rain_intensity = 0.30
                self._log_event(self.current_lap, "WEATHER", "Spotters report light rain falling around the circuit! Track is DAMP.")
        elif self.weather.condition == TrackCondition.DAMP:
            # If intensity was low and dry spell continues, dry out gradually
            if self.weather.rain_intensity < 0.12:
                self.weather.condition = TrackCondition.DRY
                self.weather.rain_intensity = 0.0
                self._log_event(self.current_lap, "WEATHER", "Rain has stopped. The racing line is completely dry.")
            elif rand_val < 0.08:  # 8% chance rain intensifies to full wet
                self.weather.condition = TrackCondition.WET
                self.weather.rain_intensity = 0.75
                self._log_event(self.current_lap, "WEATHER", "Heavy rain has arrived! Track condition is now WET.")
            elif rand_val > 0.65:  # Gradual drying
                self.weather.rain_intensity = max(0.0, self.weather.rain_intensity - 0.06)
        elif self.weather.condition == TrackCondition.WET:
            # Rain easing chance (~10% per lap)
            if rand_val < 0.10:
                self.weather.condition = TrackCondition.DAMP
                self.weather.rain_intensity = 0.40
                self._log_event(self.current_lap, "WEATHER", "Rain intensity easing. Track transition to DAMP.")

        # Update rain forecast for next 5 laps
        if self.weather.condition == TrackCondition.DRY:
            self.weather.rain_probability_next_5_laps = min(0.35, self.track.rain_probability_base + float(self.rng.normal(0, 0.03)))
        elif self.weather.condition == TrackCondition.DAMP:
            self.weather.rain_probability_next_5_laps = 0.60
        else:
            self.weather.rain_probability_next_5_laps = 0.85

    def _update_safety_car(self):
        """Handles Safety Car / VSC state machine."""
        if self.safety_car != SafetyCarStatus.NONE:
            self.safety_car_laps_remaining -= 1
            if self.safety_car_laps_remaining <= 0:
                old_sc = self.safety_car.value
                self.safety_car = SafetyCarStatus.NONE
                self._log_event(self.current_lap, "TRACK_CLEAR", f"{old_sc} in this lap. Track is GREEN! Racing resumes.")
        else:
            # Low random probability of incident triggering SC/VSC (~3% per lap)
            rand_incident = float(self.rng.random())
            if rand_incident < 0.015 and self.current_lap < self.track.total_laps - 4:
                self.safety_car = SafetyCarStatus.SAFETY_CAR
                self.safety_car_laps_remaining = int(self.rng.integers(3, 6))
                self._log_event(self.current_lap, "SAFETY_CAR", f"YELLOW FLAG: Physical Safety Car deployed! Incident on track.")
            elif rand_incident < 0.035 and self.current_lap < self.track.total_laps - 3:
                self.safety_car = SafetyCarStatus.VSC
                self.safety_car_laps_remaining = int(self.rng.integers(2, 4))
                self._log_event(self.current_lap, "VSC", "VSC DEPLOYED: Reduce delta time.")

    def _process_ai_competitor_strategies(self):
        """Simulates realistic strategic decisions for AI drivers."""
        for car in self.cars:
            if car.is_player or car.is_dnf:
                continue

            # Weather reactive pit stop
            if self.weather.condition == TrackCondition.WET and car.tyre_compound != TyreCompound.WET:
                car.pit_stop_queued_compound = TyreCompound.WET
                car.in_pit = True
            elif self.weather.condition == TrackCondition.DAMP and car.tyre_compound not in (TyreCompound.INTERMEDIATE, TyreCompound.WET):
                car.pit_stop_queued_compound = TyreCompound.INTERMEDIATE
                car.in_pit = True
            elif self.weather.condition == TrackCondition.DRY and car.tyre_compound in (TyreCompound.INTERMEDIATE, TyreCompound.WET):
                car.pit_stop_queued_compound = TyreCompound.HARD
                car.in_pit = True
            elif car.tyre_wear_pct > 78.0 and not car.in_pit:
                # Tyre wear pit stop
                next_compound = TyreCompound.HARD if car.tyre_compound != TyreCompound.HARD else TyreCompound.MEDIUM
                car.pit_stop_queued_compound = next_compound
                car.in_pit = True

    def _update_leaderboard(self):
        """Sorts cars by cumulative race time and re-indexes positions and gaps."""
        active_cars = [c for c in self.cars if not c.is_dnf]
        dnf_cars = [c for c in self.cars if c.is_dnf]

        active_cars.sort(key=lambda c: (c.total_race_time_s))

        leader_time = active_cars[0].total_race_time_s if active_cars else 0.0
        for idx, car in enumerate(active_cars):
            old_pos = car.position
            car.position = idx + 1
            car.gap_to_leader_s = round(car.total_race_time_s - leader_time, 3)

            if idx == 0:
                car.gap_to_car_ahead_s = 0.0
            else:
                car.gap_to_car_ahead_s = round(car.total_race_time_s - active_cars[idx - 1].total_race_time_s, 3)

            if idx < len(active_cars) - 1:
                car.gap_to_car_behind_s = round(active_cars[idx + 1].total_race_time_s - car.total_race_time_s, 3)
            else:
                car.gap_to_car_behind_s = 0.0

            # Detect overtakes
            if old_pos != car.position and self.current_lap > 1:
                if car.position < old_pos: # Gained position
                    self._log_event(self.current_lap, "OVERTAKE", f"{car.driver_name} moved up to P{car.position} (+{old_pos - car.position})", car.car_id)

        self.cars = active_cars + dnf_cars

    def _log_event(self, lap: int, event_type: str, message: str, car_id: Optional[str] = None):
        """Appends a timestamped event to the race log."""
        self.events_log.append(
            RaceEvent(
                lap=lap,
                timestamp_s=round(self.race_time_s, 2),
                event_type=event_type,
                message=message,
                car_id=car_id,
            )
        )

    def get_state(self) -> RaceState:
        """Returns the full, validated Pydantic snapshot of the current state."""
        return RaceState(
            race_id=self.race_id,
            seed=self.seed,
            track=self.track,
            current_lap=self.current_lap,
            total_laps=self.track.total_laps,
            tick=self.tick,
            race_time_s=self.race_time_s,
            safety_car=self.safety_car,
            safety_car_laps_remaining=self.safety_car_laps_remaining,
            weather=self.weather,
            cars=self.cars,
            events_log=self.events_log[-20:], # Keep recent 20 events in hot state
            is_finished=self.is_finished,
            winner_car_id=self.winner_car_id,
        )

    @classmethod
    def from_state(cls, state: RaceState) -> RaceSimulator:
        """Reconstructs an active RaceSimulator from a historical RaceState snapshot."""
        track_key = "silverstone"
        if hasattr(state, "track") and state.track:
            for k in ("silverstone", "monza", "spa", "monaco", "interlagos"):
                if k in str(state.track.name).lower():
                    track_key = k
                    break

        sim = cls(
            track_name=track_key,
            seed=state.seed if state.seed is not None else 42,
            grid_size=len(state.cars) if state.cars else 10,
        )
        sim.race_id = state.race_id
        sim.current_lap = state.current_lap
        sim.tick = state.tick
        sim.race_time_s = state.race_time_s
        sim.is_finished = state.is_finished
        sim.winner_car_id = state.winner_car_id
        sim.safety_car = state.safety_car
        sim.safety_car_laps_remaining = state.safety_car_laps_remaining
        sim.weather = copy.deepcopy(state.weather)
        sim.cars = copy.deepcopy(state.cars)
        sim.events_log = copy.deepcopy(state.events_log)
        return sim

    def inject_weather(self, condition: TrackCondition, rain_intensity: float = 0.75):
        """Forces immediate weather transition for pit-wall scenario injection."""
        self.weather.condition = condition
        self.weather.rain_intensity = float(rain_intensity)
        if condition == TrackCondition.WET:
            self.weather.rain_probability_next_5_laps = 0.90
            self._log_event(self.current_lap, "SCENARIO_INJECT", f"⚡ INJECTED: Sudden heavy torrential rain ({int(rain_intensity * 100)}% intensity)!")
        elif condition == TrackCondition.DAMP:
            self.weather.rain_probability_next_5_laps = 0.60
            self._log_event(self.current_lap, "SCENARIO_INJECT", "⚡ INJECTED: Light rainfall onset. Circuit is DAMP.")
        else:
            self.weather.rain_probability_next_5_laps = self.track.rain_probability_base
            self._log_event(self.current_lap, "SCENARIO_INJECT", "⚡ INJECTED: Track rapidly dried. DRY racing conditions.")

    def inject_safety_car(self, status: SafetyCarStatus, laps: int = 4):
        """Forces immediate Safety Car / VSC deployment for stress-testing pit reactions."""
        self.safety_car = status
        self.safety_car_laps_remaining = max(1, laps)
        if status == SafetyCarStatus.SAFETY_CAR:
            self._log_event(self.current_lap, "SCENARIO_INJECT", f"⚡ INJECTED: Full Safety Car deployed ({laps} laps duration)!")
        elif status == SafetyCarStatus.VSC:
            self._log_event(self.current_lap, "SCENARIO_INJECT", f"⚡ INJECTED: Virtual Safety Car (VSC) activated ({laps} laps duration)!")
        else:
            self.safety_car_laps_remaining = 0
            self._log_event(self.current_lap, "SCENARIO_INJECT", "⚡ INJECTED: Track is GREEN! Safety car withdrawn.")

    def inject_puncture(self, car_id: Optional[str] = None, wear_delta: float = 55.0):
        """Simulates sudden tyre puncture / acute degradation cliff for player or specified AI car."""
        target_car = self.get_player_car() if car_id is None else next((c for c in self.cars if c.car_id == car_id), self.get_player_car())
        if target_car:
            target_car.tyre_wear_pct = min(100.0, target_car.tyre_wear_pct + wear_delta)
            if target_car.tyre_wear_pct > 75.0:
                target_car.tyre_cliff_reached = True
            self._log_event(self.current_lap, "SCENARIO_INJECT", f"⚡ INJECTED: Debris damage on {target_car.driver_name}! Tyre wear jumped to {target_car.tyre_wear_pct:.1f}%.", target_car.car_id)

    def clear_hazards(self):
        """Resets active artificial hazards back to baseline clear conditions."""
        self.safety_car = SafetyCarStatus.NONE
        self.safety_car_laps_remaining = 0
        self.weather.condition = TrackCondition.DRY
        self.weather.rain_intensity = 0.0
        self.weather.rain_probability_next_5_laps = self.track.rain_probability_base
        self._log_event(self.current_lap, "SCENARIO_INJECT", "⚡ INJECTED: Reset all hazards. Circuit clear and green.")

    def clone(self) -> RaceSimulator:
        """Deep clones the simulator state for forward rollout counterfactuals."""
        return copy.deepcopy(self)

