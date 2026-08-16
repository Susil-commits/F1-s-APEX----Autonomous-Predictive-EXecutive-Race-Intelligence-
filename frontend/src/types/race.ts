export type TyreCompound = 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET';
export type DrivingMode = 'PUSH' | 'NORMAL' | 'CONSERVE';
export type StrategyAction = 'MAINTAIN' | 'PUSH' | 'CONSERVE' | 'PIT_SOFT' | 'PIT_MEDIUM' | 'PIT_HARD' | 'PIT_INTER' | 'PIT_WET';
export type TrackCondition = 'DRY' | 'DAMP' | 'WET';
export type SafetyCarStatus = 'NONE' | 'VSC' | 'SAFETY_CAR';

export interface TrackConfig {
  name: string;
  country: string;
  total_laps: number;
  lap_distance_km: number;
  base_lap_time_s: number;
  pit_lane_delta_s: number;
  vsc_pit_advantage_s: number;
  sc_pit_advantage_s: number;
  tyre_wear_factor: number;
  rain_probability_base: number;
}

export interface CarState {
  car_id: string;
  driver_name: string;
  team_name: string;
  car_number: number;
  is_player: boolean;
  position: number;
  current_lap: number;
  lap_progress_pct: number;
  last_lap_time_s: number | null;
  best_lap_time_s: number | null;
  total_race_time_s: number;
  gap_to_leader_s: number;
  gap_to_car_ahead_s: number;
  gap_to_car_behind_s: number;
  tyre_compound: TyreCompound;
  tyre_age_laps: number;
  tyre_wear_pct: number;
  tyre_cliff_reached: boolean;
  fuel_kg: number;
  fuel_burn_per_lap_kg: number;
  driving_mode: DrivingMode;
  in_pit: boolean;
  pit_count: number;
  laps_since_last_pit: number;
  is_dnf: boolean;
  dnf_reason: string | null;
}

export interface WeatherState {
  condition: TrackCondition;
  rain_intensity: number;
  track_temp_c: number;
  air_temp_c: number;
  rain_probability_next_5_laps: number;
  drying_rate_per_lap: number;
}

export interface RaceEvent {
  lap: number;
  timestamp_s: number;
  event_type: string;
  message: string;
  car_id?: string;
}

export interface CounterfactualOption {
  strategy: string;
  action: StrategyAction;
  projected_position: number;
  projected_gap_to_leader: number;
  projected_tyre_wear_pct: number;
  projected_compound: TyreCompound;
  cliff_reached: boolean;
}

export interface CounterfactualSummary {
  rollout_laps: number;
  best_strategy: string;
  best_action: StrategyAction;
  alternatives: CounterfactualOption[];
}

export interface DecisionExplanation {
  recommendation: StrategyAction;
  confidence_score: number;
  urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  primary_factors: string[];
  rule_engine_action: StrategyAction;
  dqn_action: StrategyAction | null;
  q_value_margin: number | null;
  tyre_cliff_risk: string;
  pit_window_status: string;
  expected_time_delta_s: number;
  counterfactual_summary: CounterfactualSummary;
  commentary?: string;
}

export interface RaceState {
  race_id: string;
  seed: number;
  track: TrackConfig;
  current_lap: number;
  total_laps: number;
  tick: number;
  race_time_s: number;
  safety_car: SafetyCarStatus;
  safety_car_laps_remaining: number;
  weather: WeatherState;
  cars: CarState[];
  events_log: RaceEvent[];
  active_decision: DecisionExplanation | null;
  is_finished: boolean;
  winner_car_id: string | null;
}
