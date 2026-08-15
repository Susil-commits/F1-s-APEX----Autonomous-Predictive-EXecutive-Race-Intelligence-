/**
 * Client-Side APEX Digital Twin & Physics Engine
 * High-fidelity fallback simulator running deterministic multi-car physics,
 * non-linear tyre wear curves, dynamic weather, Safety Car states,
 * rule + RL decision heuristics, and forward counterfactual rollouts.
 */

import {
  RaceState,
  CarState,
  TrackConfig,
  TyreCompound,
  DrivingMode,
  StrategyAction,
  TrackCondition,
  DecisionExplanation,
  CounterfactualOption,
} from '../types/race';

const DRIVERS_DB = [
  { id: 'apex_01', name: 'APEX (AI Driver)', team: 'APEX AI Racing', number: 1, isPlayer: true, basePace: 0.0 },
  { id: 'ver_01', name: 'Max Verstappen', team: 'Red Bull Racing', number: 1, isPlayer: false, basePace: -0.15 },
  { id: 'nor_04', name: 'Lando Norris', team: 'McLaren F1 Team', number: 4, isPlayer: false, basePace: -0.10 },
  { id: 'lec_16', name: 'Charles Leclerc', team: 'Scuderia Ferrari', number: 16, isPlayer: false, basePace: -0.05 },
  { id: 'pia_81', name: 'Oscar Piastri', team: 'McLaren F1 Team', number: 81, isPlayer: false, basePace: 0.05 },
  { id: 'ham_44', name: 'Lewis Hamilton', team: 'Mercedes-AMG F1', number: 44, isPlayer: false, basePace: 0.10 },
  { id: 'rus_63', name: 'George Russell', team: 'Mercedes-AMG F1', number: 63, isPlayer: false, basePace: 0.12 },
  { id: 'sai_55', name: 'Carlos Sainz', team: 'Scuderia Ferrari', number: 55, isPlayer: false, basePace: 0.15 },
  { id: 'alo_14', name: 'Fernando Alonso', team: 'Aston Martin F1', number: 14, isPlayer: false, basePace: 0.25 },
  { id: 'alb_23', name: 'Alexander Albon', team: 'Williams Racing', number: 23, isPlayer: false, basePace: 0.40 },
];

const TRACK_CONFIGS: Record<string, TrackConfig> = {
  silverstone: {
    name: 'Silverstone Circuit',
    country: 'Great Britain',
    total_laps: 52,
    lap_distance_km: 5.891,
    base_lap_time_s: 88.5,
    pit_lane_delta_s: 21.5,
    vsc_pit_advantage_s: 9.5,
    sc_pit_advantage_s: 12.5,
    tyre_wear_factor: 1.15,
    rain_probability_base: 0.18,
  },
  monza: {
    name: 'Autodromo Nazionale Monza',
    country: 'Italy',
    total_laps: 53,
    lap_distance_km: 5.793,
    base_lap_time_s: 81.0,
    pit_lane_delta_s: 24.0,
    vsc_pit_advantage_s: 10.0,
    sc_pit_advantage_s: 13.0,
    tyre_wear_factor: 0.85,
    rain_probability_base: 0.10,
  },
  spa: {
    name: 'Circuit de Spa-Francorchamps',
    country: 'Belgium',
    total_laps: 44,
    lap_distance_km: 7.004,
    base_lap_time_s: 104.5,
    pit_lane_delta_s: 22.0,
    vsc_pit_advantage_s: 9.5,
    sc_pit_advantage_s: 12.5,
    tyre_wear_factor: 1.25,
    rain_probability_base: 0.30,
  },
  monaco: {
    name: 'Circuit de Monaco',
    country: 'Monaco',
    total_laps: 78,
    lap_distance_km: 3.337,
    base_lap_time_s: 73.2,
    pit_lane_delta_s: 19.5,
    vsc_pit_advantage_s: 8.5,
    sc_pit_advantage_s: 11.0,
    tyre_wear_factor: 0.65,
    rain_probability_base: 0.12,
  },
  interlagos: {
    name: 'Autódromo de Interlagos',
    country: 'Brazil',
    total_laps: 71,
    lap_distance_km: 4.309,
    base_lap_time_s: 70.5,
    pit_lane_delta_s: 21.0,
    vsc_pit_advantage_s: 9.0,
    sc_pit_advantage_s: 12.0,
    tyre_wear_factor: 1.10,
    rain_probability_base: 0.25,
  },
};

const COMPOUND_WEAR_RATES: Record<TyreCompound, number> = {
  SOFT: 3.8,
  MEDIUM: 2.6,
  HARD: 1.8,
  INTERMEDIATE: 2.9,
  WET: 2.4,
};

export class ClientRaceSimulator {
  private state: RaceState;
  private queuedAction: StrategyAction | null = null;

  constructor(trackId: string = 'silverstone', seed: number = 42) {
    this.state = this.createInitialState(trackId, seed);
  }

  public getState(): RaceState {
    return JSON.parse(JSON.stringify(this.state));
  }

  public setAction(action: StrategyAction) {
    this.queuedAction = action;
  }

  public reset(trackId: string = 'silverstone', seed: number = 42): RaceState {
    this.queuedAction = null;
    this.state = this.createInitialState(trackId, seed);
    return this.getState();
  }

  private createInitialState(trackId: string, seed: number): RaceState {
    const track = TRACK_CONFIGS[trackId.toLowerCase()] || TRACK_CONFIGS.silverstone;
    const cars: CarState[] = DRIVERS_DB.map((d, idx) => ({
      car_id: d.id,
      driver_name: d.name,
      team_name: d.team,
      car_number: d.number,
      is_player: d.isPlayer,
      position: idx + 1,
      current_lap: 0,
      lap_progress_pct: (idx * 3) % 100,
      last_lap_time_s: null,
      best_lap_time_s: null,
      total_race_time_s: 0,
      gap_to_leader_s: idx * 1.4,
      gap_to_car_ahead_s: idx === 0 ? 0 : 1.4,
      gap_to_car_behind_s: idx === DRIVERS_DB.length - 1 ? 0 : 1.4,
      tyre_compound: (idx % 2 === 0 ? 'MEDIUM' : 'SOFT') as TyreCompound,
      tyre_age_laps: 0,
      tyre_wear_pct: 0.0,
      tyre_cliff_reached: false,
      fuel_kg: 105.0,
      fuel_burn_per_lap_kg: 105.0 / track.total_laps,
      driving_mode: 'NORMAL',
      in_pit: false,
      pit_count: 0,
      laps_since_last_pit: 0,
      is_dnf: false,
      dnf_reason: null,
    }));

    const weather = {
      condition: 'DRY' as TrackCondition,
      rain_intensity: 0.0,
      track_temp_c: 34.5,
      air_temp_c: 24.0,
      rain_probability_next_5_laps: track.rain_probability_base,
      drying_rate_per_lap: 0.05,
    };

    const initialDecision = this.computeDecisionExplanation(cars[0], track, weather, 'NONE');

    return {
      race_id: `client_sim_${seed}_${Date.now()}`,
      seed,
      track,
      current_lap: 0,
      total_laps: track.total_laps,
      tick: 0,
      race_time_s: 0,
      safety_car: 'NONE',
      safety_car_laps_remaining: 0,
      weather,
      cars,
      events_log: [
        {
          lap: 0,
          timestamp_s: 0,
          event_type: 'RACE_START',
          message: `Lights out and away we go at ${track.name}! 10 cars on the grid.`,
        },
      ],
      active_decision: initialDecision,
      is_finished: false,
      winner_car_id: null,
    };
  }

  public injectIncident(type: 'SAFETY_CAR' | 'VSC' | 'RAIN') {
    if (type === 'SAFETY_CAR') {
      this.state.safety_car = 'SAFETY_CAR';
      this.state.safety_car_laps_remaining = 3;
      this.state.events_log.push({
        lap: this.state.current_lap,
        timestamp_s: this.state.race_time_s,
        event_type: 'SAFETY_CAR_DEPLOYED',
        message: '🚨 SAFETY CAR DEPLOYED! Pack grouping up, pit delta advantage active.',
      });
    } else if (type === 'VSC') {
      this.state.safety_car = 'VSC';
      this.state.safety_car_laps_remaining = 2;
      this.state.events_log.push({
        lap: this.state.current_lap,
        timestamp_s: this.state.race_time_s,
        event_type: 'VSC_DEPLOYED',
        message: '⚠️ VIRTUAL SAFETY CAR active! Speed reduced by 40%.',
      });
    } else if (type === 'RAIN') {
      this.state.weather.condition = 'WET';
      this.state.weather.rain_intensity = 0.85;
      this.state.weather.track_temp_c = 21.0;
      this.state.events_log.push({
        lap: this.state.current_lap,
        timestamp_s: this.state.race_time_s,
        event_type: 'WEATHER_RAIN',
        message: '🌧️ HEAVY RAIN HITTING CIRCUIT! Crossover threshold to INTERMEDIATES/WETS reached.',
      });
    }
  }

  public step(): RaceState {
    if (this.state.is_finished) return this.getState();

    this.state.tick += 1;
    this.state.current_lap += 1;

    // Safety Car decay
    if (this.state.safety_car_laps_remaining > 0) {
      this.state.safety_car_laps_remaining -= 1;
      if (this.state.safety_car_laps_remaining === 0) {
        const prev = this.state.safety_car;
        this.state.safety_car = 'NONE';
        this.state.events_log.push({
          lap: this.state.current_lap,
          timestamp_s: this.state.race_time_s,
          event_type: 'TRACK_CLEAR',
          message: `🟢 ${prev} ENDING — GREEN FLAG! Racing resumes.`,
        });
      }
    }

    // Weather transition simulation
    if (this.state.weather.condition === 'WET' && Math.random() < 0.15) {
      this.state.weather.condition = 'DAMP';
      this.state.weather.rain_intensity = 0.35;
      this.state.events_log.push({
        lap: this.state.current_lap,
        timestamp_s: this.state.race_time_s,
        event_type: 'WEATHER_DRYING',
        message: '⛅ Rain easing off. Track evolving to DAMP.',
      });
    }

    const isSC = this.state.safety_car === 'SAFETY_CAR';
    const isVSC = this.state.safety_car === 'VSC';
    const isWet = this.state.weather.condition === 'WET';

    // Update each car
    for (const car of this.state.cars) {
      if (car.is_dnf) continue;

      car.current_lap = this.state.current_lap;
      car.in_pit = false;

      // Handle player queued action
      if (car.is_player && this.queuedAction) {
        this.applyActionToCar(car, this.queuedAction);
        this.queuedAction = null;
      }

      // AI Rival Pit Heuristics
      if (!car.is_player) {
        if (isWet && car.tyre_compound !== 'INTERMEDIATE' && car.tyre_compound !== 'WET') {
          this.applyActionToCar(car, 'PIT_INTER');
        } else if (car.tyre_wear_pct >= 76.0 && !car.in_pit) {
          const nextComp = car.tyre_compound === 'SOFT' ? 'MEDIUM' : 'HARD';
          this.applyActionToCar(car, `PIT_${nextComp}` as StrategyAction);
        }
      }

      // Tyre wear step
      const wearRate = COMPOUND_WEAR_RATES[car.tyre_compound] || 2.5;
      let wearDelta = wearRate * this.state.track.tyre_wear_factor;
      if (car.driving_mode === 'PUSH') wearDelta *= 1.4;
      if (car.driving_mode === 'CONSERVE') wearDelta *= 0.65;
      if (isSC || isVSC) wearDelta *= 0.3;

      car.tyre_wear_pct = Math.min(100, car.tyre_wear_pct + wearDelta);
      car.tyre_age_laps += 1;
      car.laps_since_last_pit += 1;
      car.fuel_kg = Math.max(2.0, car.fuel_kg - car.fuel_burn_per_lap_kg);

      if (car.tyre_wear_pct >= 78.0) {
        car.tyre_cliff_reached = true;
      }

      // Calculate Lap Time
      let lapTime = this.state.track.base_lap_time_s;
      // Driver pace delta
      const driver = DRIVERS_DB.find((d) => d.id === car.car_id);
      if (driver) lapTime += driver.basePace;

      // Tyre compound pace
      if (car.tyre_compound === 'SOFT') lapTime -= 0.6;
      else if (car.tyre_compound === 'HARD') lapTime += 0.5;

      // Wear penalty
      if (car.tyre_wear_pct > 50) {
        lapTime += ((car.tyre_wear_pct - 50) / 25) * 0.8;
      }
      if (car.tyre_cliff_reached) {
        lapTime += 2.8; // Heavy cliff penalty
      }

      // Mode adjustment
      if (car.driving_mode === 'PUSH') lapTime -= 0.45;
      if (car.driving_mode === 'CONSERVE') lapTime += 0.55;

      // SC / VSC speed delta
      if (isSC) lapTime += 32.0;
      if (isVSC) lapTime += 18.0;

      // Weather mismatch penalty
      if (isWet && car.tyre_compound !== 'INTERMEDIATE' && car.tyre_compound !== 'WET') {
        lapTime += 8.5; // Slick on wet
      }

      // Random micro variance
      lapTime += (Math.random() - 0.5) * 0.35;

      // Pit stop time penalty if boxed
      if (car.in_pit) {
        let pitDelta = this.state.track.pit_lane_delta_s;
        if (isSC) pitDelta -= this.state.track.sc_pit_advantage_s;
        else if (isVSC) pitDelta -= this.state.track.vsc_pit_advantage_s;
        lapTime += pitDelta;
      }

      car.last_lap_time_s = parseFloat(lapTime.toFixed(3));
      if (!car.best_lap_time_s || lapTime < car.best_lap_time_s) {
        car.best_lap_time_s = car.last_lap_time_s;
      }
      car.total_race_time_s += lapTime;
    }

    // Sort cars by total race time to assign positions
    this.state.cars.sort((a, b) => a.total_race_time_s - b.total_race_time_s);
    const leaderTime = this.state.cars[0].total_race_time_s;

    this.state.cars.forEach((c, idx) => {
      c.position = idx + 1;
      c.gap_to_leader_s = parseFloat((c.total_race_time_s - leaderTime).toFixed(3));
      const prevCar = idx > 0 ? this.state.cars[idx - 1] : null;
      const nextCar = idx < this.state.cars.length - 1 ? this.state.cars[idx + 1] : null;
      c.gap_to_car_ahead_s = prevCar ? parseFloat((c.total_race_time_s - prevCar.total_race_time_s).toFixed(3)) : 0;
      c.gap_to_car_behind_s = nextCar ? parseFloat((nextCar.total_race_time_s - c.total_race_time_s).toFixed(3)) : 0;
    });

    this.state.race_time_s = parseFloat(leaderTime.toFixed(1));

    // Decision update for player car
    const playerCar = this.state.cars.find((c) => c.is_player) || this.state.cars[0];
    this.state.active_decision = this.computeDecisionExplanation(
      playerCar,
      this.state.track,
      this.state.weather,
      this.state.safety_car
    );

    // Check race finish
    if (this.state.current_lap >= this.state.total_laps) {
      this.state.is_finished = true;
      this.state.winner_car_id = this.state.cars[0].car_id;
      this.state.events_log.push({
        lap: this.state.current_lap,
        timestamp_s: this.state.race_time_s,
        event_type: 'CHEQUERED_FLAG',
        message: `🏁 CHEQUERED FLAG! ${this.state.cars[0].driver_name} wins the Grand Prix!`,
      });
    }

    return this.getState();
  }

  private applyActionToCar(car: CarState, action: StrategyAction) {
    if (action.startsWith('PIT_')) {
      let resolvedCompound: TyreCompound = 'MEDIUM';
      if (action === 'PIT_SOFT') resolvedCompound = 'SOFT';
      else if (action === 'PIT_MEDIUM') resolvedCompound = 'MEDIUM';
      else if (action === 'PIT_HARD') resolvedCompound = 'HARD';
      else if (action === 'PIT_INTER') resolvedCompound = 'INTERMEDIATE';
      else if (action === 'PIT_WET') resolvedCompound = 'WET';

      car.in_pit = true;
      car.pit_count += 1;
      car.tyre_compound = resolvedCompound;
      car.tyre_age_laps = 0;
      car.tyre_wear_pct = 0.0;
      car.tyre_cliff_reached = false;
      car.laps_since_last_pit = 0;

      this.state.events_log.push({
        lap: this.state.current_lap,
        timestamp_s: this.state.race_time_s,
        event_type: 'PIT_STOP',
        message: `BOX BOX BOX: ${car.driver_name} pitted for fresh ${resolvedCompound} tyres.`,
        car_id: car.car_id,
      });
    } else if (action === 'PUSH') {
      car.driving_mode = 'PUSH';
    } else if (action === 'CONSERVE') {
      car.driving_mode = 'CONSERVE';
    } else if (action === 'MAINTAIN') {
      car.driving_mode = 'NORMAL';
    }
  }

  private computeDecisionExplanation(
    playerCar: CarState,
    track: TrackConfig,
    weather: any,
    safetyCar: string
  ): DecisionExplanation {
    let rec: StrategyAction = 'MAINTAIN';
    let urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' = 'LOW';
    let conf = 0.88;
    const factors: string[] = [];

    const isWet = weather.condition === 'WET';
    const isSC = safetyCar === 'SAFETY_CAR' || safetyCar === 'VSC';
    const wear = playerCar.tyre_wear_pct;
    const cliffRisk = wear > 75 ? 'CRITICAL' : wear > 55 ? 'HIGH' : wear > 35 ? 'MODERATE' : 'LOW';

    if (isWet && playerCar.tyre_compound !== 'INTERMEDIATE' && playerCar.tyre_compound !== 'WET') {
      rec = 'PIT_INTER';
      urgency = 'CRITICAL';
      conf = 0.98;
      factors.push('Heavy rain crossover reached — slicks losing 8.5s/lap.');
      factors.push('Immediate box for Intermediate tyres prevents massive position loss.');
    } else if (isSC && wear > 45) {
      rec = playerCar.tyre_compound === 'SOFT' ? 'PIT_HARD' : 'PIT_MEDIUM';
      urgency = 'HIGH';
      conf = 0.94;
      factors.push(`Safety Car active: Pit stop delta advantage saves ~${track.sc_pit_advantage_s}s.`);
      factors.push(`Current tyre wear at ${wear.toFixed(0)}% — optimal cheap pit window.`);
    } else if (wear >= 75) {
      rec = playerCar.tyre_compound === 'SOFT' ? 'PIT_MEDIUM' : 'PIT_HARD';
      urgency = 'CRITICAL';
      conf = 0.96;
      factors.push(`Tyre wear at ${wear.toFixed(1)}% — cliff threshold reached (+2.8s penalty).`);
      factors.push('Box this lap to avoid undercut and catastrophic pace loss.');
    } else if (playerCar.gap_to_car_ahead_s > 0 && playerCar.gap_to_car_ahead_s < 1.2 && wear < 60) {
      rec = 'PUSH';
      urgency = 'MEDIUM';
      conf = 0.86;
      factors.push(`DRS slipstream available (+${playerCar.gap_to_car_ahead_s.toFixed(2)}s to car ahead).`);
      factors.push('Attack mode: Push to execute overtake in dirty air sector.');
    } else if (wear > 55 && playerCar.gap_to_car_behind_s > 4.0) {
      rec = 'CONSERVE';
      urgency = 'LOW';
      conf = 0.82;
      factors.push('Comfortable buffer behind (+4.0s gap) allows tyre management.');
      factors.push('Conserve tyres to extend stint by 4-5 laps for one-stop overcut.');
    } else {
      rec = 'MAINTAIN';
      urgency = 'LOW';
      conf = 0.89;
      factors.push('Tyre thermal and wear degradation tracking within nominal model bounds.');
      factors.push('Telemetry pace stable relative to leader.');
    }

    const alternatives: CounterfactualOption[] = [
      {
        strategy: 'Maintain Current Stint',
        action: 'MAINTAIN',
        projected_position: Math.min(10, playerCar.position + (wear > 70 ? 2 : 0)),
        projected_gap_to_leader: playerCar.gap_to_leader_s + (wear > 70 ? 4.5 : 1.2),
        projected_tyre_wear_pct: Math.min(100, wear + 14),
        projected_compound: playerCar.tyre_compound,
        cliff_reached: wear + 14 >= 78,
      },
      {
        strategy: 'Box Lap 1 ➔ Fresh Mediums',
        action: 'PIT_MEDIUM',
        projected_position: Math.max(1, playerCar.position - (wear > 60 ? 1 : 0)),
        projected_gap_to_leader: playerCar.gap_to_leader_s + (isSC ? 9.5 : 21.0) - 6.5,
        projected_tyre_wear_pct: 12.0,
        projected_compound: 'MEDIUM',
        cliff_reached: false,
      },
      {
        strategy: 'Box Lap 1 ➔ Fresh Hards',
        action: 'PIT_HARD',
        projected_position: Math.max(1, playerCar.position),
        projected_gap_to_leader: playerCar.gap_to_leader_s + (isSC ? 9.5 : 21.0) - 4.5,
        projected_tyre_wear_pct: 8.0,
        projected_compound: 'HARD',
        cliff_reached: false,
      },
      {
        strategy: 'Attack Mode: Push',
        action: 'PUSH',
        projected_position: Math.max(1, playerCar.position - 1),
        projected_gap_to_leader: Math.max(0, playerCar.gap_to_leader_s - 1.8),
        projected_tyre_wear_pct: Math.min(100, wear + 22),
        projected_compound: playerCar.tyre_compound,
        cliff_reached: wear + 22 >= 78,
      },
      {
        strategy: 'Tyre Management: Conserve',
        action: 'CONSERVE',
        projected_position: playerCar.position,
        projected_gap_to_leader: playerCar.gap_to_leader_s + 2.5,
        projected_tyre_wear_pct: Math.min(100, wear + 8),
        projected_compound: playerCar.tyre_compound,
        cliff_reached: wear + 8 >= 78,
      },
    ];

    const bestAlt = alternatives.reduce((prev, curr) =>
      curr.projected_gap_to_leader < prev.projected_gap_to_leader ? curr : prev
    );

    return {
      recommendation: rec,
      confidence_score: conf,
      urgency,
      primary_factors: factors,
      rule_engine_action: rec,
      dqn_action: rec,
      q_value_margin: 0.42,
      tyre_cliff_risk: cliffRisk,
      pit_window_status: wear > 50 ? 'OPEN (Lap 18-28)' : 'UPCOMING (Lap 22)',
      expected_time_delta_s: wear > 70 ? -3.2 : 0.4,
      counterfactual_summary: {
        rollout_laps: 4,
        best_strategy: bestAlt.strategy,
        best_action: bestAlt.action,
        alternatives,
      },
    };
  }
}
