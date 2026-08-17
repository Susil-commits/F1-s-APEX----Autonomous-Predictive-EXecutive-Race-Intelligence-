"""Data models and Pydantic schemas for the APEX race simulator and digital twin."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TyreCompound(str, Enum):
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


class DrivingMode(str, Enum):
    PUSH = "PUSH"        # High pace (+0.8s gain), +50% tyre degradation, +20% fuel burn
    NORMAL = "NORMAL"    # Standard baseline pace and wear
    CONSERVE = "CONSERVE"# Slower pace (-0.6s loss), -40% tyre degradation, -25% fuel burn


class StrategyAction(str, Enum):
    MAINTAIN = "MAINTAIN"          # Continue current strategy & driving mode
    PUSH = "PUSH"                  # Switch to PUSH mode
    CONSERVE = "CONSERVE"          # Switch to CONSERVE mode
    PIT_SOFT = "PIT_SOFT"          # Box this lap for Soft tyres
    PIT_MEDIUM = "PIT_MEDIUM"      # Box this lap for Medium tyres
    PIT_HARD = "PIT_HARD"          # Box this lap for Hard tyres
    PIT_INTER = "PIT_INTER"        # Box this lap for Intermediate tyres
    PIT_WET = "PIT_WET"            # Box this lap for Wet tyres
    ENERGY_DEPLOY = "ENERGY_DEPLOY" # Maximum ERS battery discharge
    ENERGY_HARVEST = "ENERGY_HARVEST"# Aggressive ERS harvesting
    ATTACK = "ATTACK"              # Tactical aggressive overtake attempt
    DEFEND = "DEFEND"              # Defensive positioning


class TrackCondition(str, Enum):
    DRY = "DRY"
    DAMP = "DAMP"
    WET = "WET"


class SafetyCarStatus(str, Enum):
    NONE = "NONE"
    VSC = "VSC"           # Virtual Safety Car (~35% delta time reduction, ~10s pit advantage)
    SAFETY_CAR = "SAFETY_CAR"  # Physical Safety Car (~60% delta time reduction, ~12s pit advantage)
    RED_FLAG = "RED_FLAG" # Session suspended


class TrackConfig(BaseModel):
    name: str = "Silverstone Circuit"
    country: str = "Great Britain"
    total_laps: int = 52
    lap_distance_km: float = 5.891
    base_lap_time_s: float = 88.50  # 1:28.500 baseline lap time
    pit_lane_delta_s: float = 21.50 # Time lost driving through pit lane & stationary stop
    vsc_pit_advantage_s: float = 9.5
    sc_pit_advantage_s: float = 12.0
    tyre_wear_factor: float = 1.0   # Circuit abrasion multiplier
    rain_probability_base: float = 0.15 # Baseline probability of rain onset


class DriverState(BaseModel):
    driver_name: str
    team_name: str
    pace_bias_s: float = 0.0
    consistency: float = 0.90
    tyre_management: float = 0.88
    aggression: float = 0.85
    defence_strength: float = 0.88
    fatigue_index: float = 0.0
    mistake_probability: float = 0.02


class TyreState(BaseModel):
    compound: TyreCompound = TyreCompound.MEDIUM
    age_laps: int = 0
    wear_pct: float = 0.0
    cliff_reached: bool = False
    cliff_probability: float = 0.0
    remaining_useful_laps: int = 25
    thermal_stress_index: float = 1.0
    predicted_lap_loss_s: float = 0.0


class VehicleHealthState(BaseModel):
    overall_health_score: float = 100.0
    is_anomalous: bool = False
    engine_temp_c: float = 105.0
    oil_temp_c: float = 110.0
    brake_temp_c: float = 620.0
    battery_voltage_v: float = 780.0
    cooling_efficiency: float = 0.95
    failure_probability: float = 0.01
    active_alarms: List[str] = Field(default_factory=list)


class OpponentState(BaseModel):
    car_id: str
    driver_name: str
    position: int
    gap_front_s: float = 0.0
    gap_rear_s: float = 0.0
    pit_next_2_laps_prob: float = 0.10
    attack_probability: float = 0.15
    defence_probability: float = 0.20
    expected_pace_delta_s: float = 0.0
    strategy_intent: str = "STINT_EXTEND"


class RiskState(BaseModel):
    overall_risk_score: float = 0.15 # 0.0 to 1.0
    dnf_risk: float = 0.01
    tyre_blowout_risk: float = 0.02
    weather_transition_risk: float = 0.05
    traffic_undercut_risk: float = 0.10
    mechanical_failure_risk: float = 0.01
    strategy_vulnerability_risk: float = 0.08


class StrategyState(BaseModel):
    planned_stops: int = 1
    current_stint: int = 1
    pit_window_start: int = 20
    pit_window_end: int = 28
    is_optimal_window: bool = False
    projected_finish_position: float = 1.0
    win_probability: float = 0.50
    podium_probability: float = 0.85


class CarState(BaseModel):
    car_id: str
    driver_name: str
    team_name: str
    car_number: int
    is_player: bool = False
    
    # Position and timing
    position: int = 1
    current_lap: int = 1
    lap_progress_pct: float = 0.0     # 0.0 - 100.0% within current lap
    last_lap_time_s: Optional[float] = None
    best_lap_time_s: Optional[float] = None
    total_race_time_s: float = 0.0
    gap_to_leader_s: float = 0.0
    gap_to_car_ahead_s: float = 0.0
    gap_to_car_behind_s: float = 0.0
    
    # Physics & consumables
    tyre_compound: TyreCompound = TyreCompound.MEDIUM
    tyre_age_laps: int = 0
    tyre_wear_pct: float = 0.0        # 0.0 (fresh) to 100.0 (punctured/blown)
    tyre_cliff_reached: bool = False
    fuel_kg: float = 105.0            # Fuel remaining in kg
    fuel_burn_per_lap_kg: float = 1.85
    driving_mode: DrivingMode = DrivingMode.NORMAL
    
    # Pit info
    in_pit: bool = False
    pit_count: int = 0
    laps_since_last_pit: int = 0
    pit_stop_queued_compound: Optional[TyreCompound] = None
    
    # Status
    is_dnf: bool = False
    dnf_reason: Optional[str] = None

    # Sub-states
    driver_state: Optional[DriverState] = None
    tyre_state: Optional[TyreState] = None
    health_state: Optional[VehicleHealthState] = None
    risk_state: Optional[RiskState] = None


class WeatherState(BaseModel):
    condition: TrackCondition = TrackCondition.DRY
    rain_intensity: float = 0.0       # 0.0 (bone dry) to 1.0 (torrential downpour)
    track_temp_c: float = 32.5
    air_temp_c: float = 24.0
    rain_probability_next_5_laps: float = 0.05
    drying_rate_per_lap: float = 0.08
    track_wetness: float = 0.0
    grip_multiplier: float = 1.0


class RaceEvent(BaseModel):
    lap: int
    timestamp_s: float
    event_type: str                  # e.g., "PIT_STOP", "OVERTAKE", "SAFETY_CAR", "WEATHER_CHANGE", "DNF"
    message: str
    car_id: Optional[str] = None


class DecisionExplanation(BaseModel):
    recommendation: StrategyAction
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)
    urgency: str = "MEDIUM"          # LOW, MEDIUM, HIGH, CRITICAL
    primary_factors: List[str] = Field(default_factory=list)
    rule_engine_action: StrategyAction
    dqn_action: Optional[StrategyAction] = None
    ppo_action: Optional[StrategyAction] = None
    q_value_margin: Optional[float] = None
    tyre_cliff_risk: str = "LOW"
    pit_window_status: str = "OPTIMAL" # EARLY, OPTIMAL, LATE, MISSED
    expected_time_delta_s: float = 0.0 # Expected net time gain/loss vs maintaining
    counterfactual_summary: Dict[str, Any] = Field(default_factory=dict)
    commentary: Optional[str] = None
    risk_score: float = 0.15
    alternative_actions: List[Dict[str, Any]] = Field(default_factory=list)


class RaceState(BaseModel):
    race_id: str
    seed: int
    track: TrackConfig
    current_lap: int = 1
    total_laps: int = 52
    tick: int = 0
    race_time_s: float = 0.0
    
    safety_car: SafetyCarStatus = SafetyCarStatus.NONE
    safety_car_laps_remaining: int = 0
    
    weather: WeatherState = Field(default_factory=WeatherState)
    cars: List[CarState] = Field(default_factory=list)
    events_log: List[RaceEvent] = Field(default_factory=list)
    
    active_decision: Optional[DecisionExplanation] = None
    is_finished: bool = False
    winner_car_id: Optional[str] = None

    # Historical and Digital Twin Context
    opponents: List[OpponentState] = Field(default_factory=list)
    global_risk: Optional[RiskState] = None
    strategy: Optional[StrategyState] = None
    decision_history: List[Dict[str, Any]] = Field(default_factory=list)
