import { create } from 'zustand';
import { RaceState, CarState, StrategyAction } from '../types/race';
import { audioEngine } from '../utils/audioEngine';

export type WorkspaceTab = 'tactical' | 'telemetry' | 'explainability' | 'sandbox';

export interface TelemetryPoint {
  lap: number;
  playerTyreWear: number;
  cliffThreshold: number;
  playerLapTime: number;
  leaderLapTime: number;
  gapToLeader: number;
  fuelRemainingKg: number;
  tyreTempFL: number;
  tyreTempFR: number;
  tyreTempRL: number;
  tyreTempRR: number;
  speedKmh: number;
}

interface RaceStoreState {
  raceState: RaceState | null;
  isRunning: boolean;
  simSpeed: number;
  connected: boolean;
  isLocalTwin: boolean;
  activeTab: WorkspaceTab;
  telemetryHistory: TelemetryPoint[];
  selectedCarId: string | null;
  inspectedCar: CarState | null;
  showDebriefModal: boolean;
  audioMuted: boolean;
  voiceRadioEnabled: boolean;
  
  setRaceState: (state: RaceState) => void;
  setRunning: (running: boolean) => void;
  setSpeed: (speed: number) => void;
  setConnected: (connected: boolean) => void;
  setIsLocalTwin: (isLocal: boolean) => void;
  setActiveTab: (tab: WorkspaceTab) => void;
  setSelectedCarId: (carId: string | null) => void;
  setInspectedCar: (car: CarState | null) => void;
  setShowDebriefModal: (show: boolean) => void;
  toggleAudioMute: () => void;
  toggleVoiceRadio: () => void;
  resetHistory: () => void;
}

export const useRaceStore = create<RaceStoreState>((set, get) => ({
  raceState: null,
  isRunning: false,
  simSpeed: 1.0,
  connected: false,
  isLocalTwin: false,
  activeTab: 'tactical',
  telemetryHistory: [],
  selectedCarId: null,
  inspectedCar: null,
  showDebriefModal: false,
  audioMuted: false,
  voiceRadioEnabled: true,

  setRaceState: (state) =>
    set((prev) => {
      const player = state.cars.find((c) => c.is_player) || state.cars[0];
      const leader = state.cars[0];

      // Audio notification for high-urgency changes
      if (
        state.active_decision &&
        prev.raceState?.active_decision?.recommendation !== state.active_decision.recommendation
      ) {
        if (state.active_decision.urgency === 'CRITICAL' || state.active_decision.urgency === 'HIGH') {
          audioEngine.playBoxAlarm();
          const spoken = state.active_decision.recommendation.startsWith('PIT_')
            ? `Box box box, strategy calls for ${state.active_decision.recommendation.replace('PIT_', '')} tyres.`
            : `Strategy update: ${state.active_decision.recommendation}`;
          audioEngine.speakRadioMessage(spoken);
        }
      }

      // Safety Car audio announcement
      if (state.safety_car !== 'NONE' && prev.raceState?.safety_car === 'NONE') {
        audioEngine.playSafetyCarAlert();
        audioEngine.speakRadioMessage('Safety Car deployed. Delta positive, maintain target pace.');
      }

      // Race finish trigger
      let showModal = prev.showDebriefModal;
      if (state.is_finished && !prev.raceState?.is_finished) {
        showModal = true;
        audioEngine.speakRadioMessage('Chequered flag! Grand Prix completed.');
      }

      let newHistory = prev.telemetryHistory;
      if (player && state.current_lap >= 0) {
        const lastRecordedLap = prev.telemetryHistory.length > 0
          ? prev.telemetryHistory[prev.telemetryHistory.length - 1].lap
          : -1;

        if (state.current_lap !== lastRecordedLap) {
          const wear = player.tyre_wear_pct;
          const point: TelemetryPoint = {
            lap: state.current_lap,
            playerTyreWear: parseFloat(wear.toFixed(1)),
            cliffThreshold: 78.0,
            playerLapTime: player.last_lap_time_s || state.track.base_lap_time_s,
            leaderLapTime: leader?.last_lap_time_s || state.track.base_lap_time_s,
            gapToLeader: parseFloat(player.gap_to_leader_s.toFixed(2)),
            fuelRemainingKg: parseFloat(player.fuel_kg.toFixed(1)),
            tyreTempFL: parseFloat((85 + wear * 0.45 + (player.driving_mode === 'PUSH' ? 8 : 0)).toFixed(1)),
            tyreTempFR: parseFloat((87 + wear * 0.48 + (player.driving_mode === 'PUSH' ? 9 : 0)).toFixed(1)),
            tyreTempRL: parseFloat((92 + wear * 0.52 + (player.driving_mode === 'PUSH' ? 10 : 0)).toFixed(1)),
            tyreTempRR: parseFloat((94 + wear * 0.55 + (player.driving_mode === 'PUSH' ? 11 : 0)).toFixed(1)),
            speedKmh: player.driving_mode === 'PUSH' ? 318 : 304,
          };
          newHistory = [...prev.telemetryHistory.slice(-35), point];
        }
      }

      // Keep inspectedCar synchronized if one is selected
      const updatedInspected = prev.inspectedCar
        ? state.cars.find((c) => c.car_id === prev.inspectedCar?.car_id) || null
        : null;

      return {
        raceState: state,
        telemetryHistory: newHistory,
        inspectedCar: updatedInspected,
        showDebriefModal: showModal,
      };
    }),

  setRunning: (running) => set({ isRunning: running }),
  setSpeed: (speed) => set({ simSpeed: speed }),
  setConnected: (connected) => set({ connected }),
  setIsLocalTwin: (isLocalTwin) => set({ isLocalTwin }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setSelectedCarId: (selectedCarId) => set({ selectedCarId }),
  setInspectedCar: (inspectedCar) => set({ inspectedCar }),
  setShowDebriefModal: (showDebriefModal) => set({ showDebriefModal }),
  toggleAudioMute: () =>
    set((prev) => {
      const next = !prev.audioMuted;
      audioEngine.setMuted(next);
      return { audioMuted: next };
    }),
  toggleVoiceRadio: () =>
    set((prev) => {
      const next = !prev.voiceRadioEnabled;
      audioEngine.setVoiceEnabled(next);
      return { voiceRadioEnabled: next };
    }),
  resetHistory: () => set({ telemetryHistory: [] }),
}));
