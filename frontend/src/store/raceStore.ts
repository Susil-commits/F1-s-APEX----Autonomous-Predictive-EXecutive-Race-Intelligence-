import { create } from 'zustand';
import { RaceState, StrategyAction } from '../types/race';

interface TelemetryPoint {
  lap: number;
  playerTyreWear: number;
  cliffThreshold: number;
  playerLapTime: number;
  leaderLapTime: number;
  gapToLeader: number;
}

interface RaceStoreState {
  raceState: RaceState | null;
  isRunning: boolean;
  simSpeed: number;
  connected: boolean;
  telemetryHistory: TelemetryPoint[];
  selectedCarId: string | null;
  
  setRaceState: (state: RaceState) => void;
  setRunning: (running: boolean) => void;
  setSpeed: (speed: number) => void;
  setConnected: (connected: boolean) => void;
  setSelectedCarId: (carId: string | null) => void;
  resetHistory: () => void;
}

export const useRaceStore = create<RaceStoreState>((set) => ({
  raceState: null,
  isRunning: false,
  simSpeed: 1.0,
  connected: false,
  telemetryHistory: [],
  selectedCarId: null,

  setRaceState: (state) =>
    set((prev) => {
      const player = state.cars.find((c) => c.is_player) || state.cars[0];
      const leader = state.cars[0];

      let newHistory = prev.telemetryHistory;
      if (player && state.current_lap > 0) {
        const lastRecordedLap = prev.telemetryHistory.length > 0
          ? prev.telemetryHistory[prev.telemetryHistory.length - 1].lap
          : -1;

        if (state.current_lap !== lastRecordedLap) {
          const point: TelemetryPoint = {
            lap: state.current_lap,
            playerTyreWear: player.tyre_wear_pct,
            cliffThreshold: 78.0,
            playerLapTime: player.last_lap_time_s || 88.5,
            leaderLapTime: leader?.last_lap_time_s || 88.5,
            gapToLeader: player.gap_to_leader_s,
          };
          newHistory = [...prev.telemetryHistory.slice(-25), point];
        }
      }

      return {
        raceState: state,
        telemetryHistory: newHistory,
      };
    }),

  setRunning: (running) => set({ isRunning: running }),
  setSpeed: (speed) => set({ simSpeed: speed }),
  setConnected: (connected) => set({ connected }),
  setSelectedCarId: (selectedCarId) => set({ selectedCarId }),
  resetHistory: () => set({ telemetryHistory: [] }),
}));
