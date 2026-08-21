/**
 * Client-Side Edge Strategy Predictor & Fast Physics Inference Engine.
 *
 * Runs locally on the client to evaluate tyre cliff probabilities,
 * projected pit windows, and counterfactual rollouts with 0ms server latency.
 */

import { TyreCompound, DrivingMode, CarState, TrackConfig, WeatherState } from '../types/race';

export interface EdgePredictionResult {
  estimatedCliffLap: number;
  remainingUsefulLaps: number;
  cliffRiskPct: number;
  optimalPitWindow: { start: number; end: number };
  undercutAdvantageSeconds: number;
  fastestCompoundForWeather: TyreCompound;
  projectedStintPaceDelta: number;
}

export class ClientEdgePredictor {
  private static COMPOUND_BASE_WEAR: Record<TyreCompound, number> = {
    SOFT: 3.4,
    MEDIUM: 2.1,
    HARD: 1.35,
    INTERMEDIATE: 2.4,
    WET: 2.2,
  };

  private static COMPOUND_CLIFF_THRESHOLD: Record<TyreCompound, number> = {
    SOFT: 75.0,
    MEDIUM: 80.0,
    HARD: 85.0,
    INTERMEDIATE: 75.0,
    WET: 75.0,
  };

  /**
   * Evaluates instantaneous tyre degradation and pit window.
   */
  public static evaluateCar(
    car: CarState,
    track: TrackConfig,
    weather: WeatherState
  ): EdgePredictionResult {
    const compound = car.tyre_compound;
    const baseWear = this.COMPOUND_BASE_WEAR[compound] || 2.1;
    const cliffThreshold = this.COMPOUND_CLIFF_THRESHOLD[compound] || 80.0;

    const modeMultiplier =
      car.driving_mode === 'PUSH' ? 1.45 : car.driving_mode === 'CONSERVE' ? 0.65 : 1.0;
    const trackFactor = track.tyre_wear_factor || 1.0;

    const effectiveWearPerLap = baseWear * modeMultiplier * trackFactor;
    const remainingWearCapacity = Math.max(0, cliffThreshold - car.tyre_wear_pct);
    const remainingUsefulLaps = Math.max(1, Math.round(remainingWearCapacity / effectiveWearPerLap));

    const estimatedCliffLap = car.current_lap + remainingUsefulLaps;
    const cliffRiskPct = Math.min(100, Math.round((car.tyre_wear_pct / cliffThreshold) * 100));

    // Optimal pit window calculation
    const windowStart = Math.max(car.current_lap + 1, estimatedCliffLap - 4);
    const windowEnd = Math.min(track.total_laps, estimatedCliffLap + 1);

    // Weather compound recommendation
    let bestCompound: TyreCompound = 'MEDIUM';
    if (weather.rain_intensity > 0.55) {
      bestCompound = 'WET';
    } else if (weather.rain_intensity >= 0.15) {
      bestCompound = 'INTERMEDIATE';
    } else if (car.current_lap > track.total_laps - 15) {
      bestCompound = 'SOFT';
    } else {
      bestCompound = 'HARD';
    }

    // Undercut calculation
    const freshTyrePaceDelta = 1.65; // ~1.65s pace advantage on fresh rubber
    const inOutLapLoss = track.pit_lane_delta_s;
    const undercutAdvantageSeconds = Number(
      Math.max(0, freshTyrePaceDelta * 2.0 - (car.gap_to_car_ahead_s || 0)).toFixed(2)
    );

    return {
      estimatedCliffLap,
      remainingUsefulLaps,
      cliffRiskPct,
      optimalPitWindow: { start: windowStart, end: windowEnd },
      undercutAdvantageSeconds,
      fastestCompoundForWeather: bestCompound,
      projectedStintPaceDelta: Number((car.tyre_wear_pct * 0.025).toFixed(3)),
    };
  }
}
