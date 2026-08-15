import React, { useState } from 'react';
import { Header } from './components/Header';
import { TimingTower } from './components/TimingTower';
import { TrackMap } from './components/TrackMap';
import { TelemetryCharts } from './components/TelemetryCharts';
import { StrategyCard } from './components/StrategyCard';
import { ExplainabilityPanel } from './components/ExplainabilityPanel';
import { CounterfactualView } from './components/CounterfactualView';
import { RaceControls } from './components/RaceControls';
import { DriverTelemetryModal } from './components/DriverTelemetryModal';
import { PitRejoinRadar } from './components/PitRejoinRadar';
import { TelemetryLab } from './components/TelemetryLab';
import { StrategySandbox } from './components/StrategySandbox';
import { StintStrategyPlanner } from './components/StintStrategyPlanner';
import { DriverBattleRadar } from './components/DriverBattleRadar';
import { WeatherDopplerRadar } from './components/WeatherDopplerRadar';
import { AIPitWallCopilot } from './components/AIPitWallCopilot';
import { PostRaceDebriefModal } from './components/PostRaceDebriefModal';
import { RaceTimeTravelDVR } from './components/RaceTimeTravelDVR';
import { DQNPolicyVisualizer } from './components/DQNPolicyVisualizer';
import { DualDriverTelemetryOverlay } from './components/DualDriverTelemetryOverlay';
import { PitStopReactionSim } from './components/PitStopReactionSim';
import { MonteCarloStrategySim } from './components/MonteCarloStrategySim';
import { MiniSectorTimingGrid } from './components/MiniSectorTimingGrid';
import { ChampionshipStandings } from './components/ChampionshipStandings';
import { RadioWaveformVisualizer } from './components/RadioWaveformVisualizer';
import { ChassisSetupTuner } from './components/ChassisSetupTuner';
import { RaceEventLogViewer } from './components/RaceEventLogViewer';
import { SHAPFeatureWaterfall } from './components/SHAPFeatureWaterfall';
import { LapTimeDeltaTDecomposition } from './components/LapTimeDeltaTDecomposition';
import { PitStrategyIsochroneMatrix } from './components/PitStrategyIsochroneMatrix';
import { UndercutThreatMatrix } from './components/UndercutThreatMatrix';
import { useRaceStore } from './store/raceStore';
import { audioEngine } from './utils/audioEngine';
import {
  Radio,
  Terminal,
  Brain,
  Trophy,
  Bot,
  Timer,
  Layers,
  Dices,
  Wrench,
  FileText,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';

export const App: React.FC = () => {
  const { raceState, activeTab, inspectedCar, showDebriefModal, setShowDebriefModal } =
    useRaceStore();
  const [showCopilotModal, setShowCopilotModal] = useState<boolean>(false);
  const [showPitSimModal, setShowPitSimModal] = useState<boolean>(false);
  const [showStandingsModal, setShowStandingsModal] = useState<boolean>(false);
  const [showAeroTunerModal, setShowAeroTunerModal] = useState<boolean>(false);
  const [engineAudioActive, setEngineAudioActive] = useState<boolean>(false);

  const events = raceState?.events_log || [];

  const toggleEngineSynth = () => {
    const active = audioEngine.toggleEngineSound(11500);
    setEngineAudioActive(active);
  };

  return (
    <div className="min-h-screen bg-apex-bg text-slate-100 flex flex-col selection:bg-apex-cyan selection:text-black relative">
      {/* Top Mission Control Header */}
      <Header />

      {/* Main Grid Workspace */}
      <main className="flex-1 p-4 max-w-[1920px] w-full mx-auto flex flex-col gap-4">
        {/* Top Control Bar & Time-Travel DVR Scrubber */}
        <div className="flex flex-col gap-2">
          <RaceControls />

          {/* Time-Travel DVR Bar */}
          <RaceTimeTravelDVR />

          {/* Quick Bar Action Buttons & Radio Waveform */}
          <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setShowCopilotModal(!showCopilotModal)}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-700/50 font-bold transition-all active:scale-95 shadow-sm shadow-cyan-900/20"
              >
                <Bot className="w-3.5 h-3.5 text-cyan-400" />
                <span>AI Strategist Copilot</span>
              </button>

              <button
                onClick={() => setShowAeroTunerModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-blue-950/60 hover:bg-blue-900/80 text-blue-300 border border-blue-700/50 font-bold transition-all active:scale-95 shadow-sm shadow-blue-900/20"
              >
                <Wrench className="w-3.5 h-3.5 text-blue-400" />
                <span>Chassis Aero Tuner</span>
              </button>

              <button
                onClick={() => setShowPitSimModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-700/50 font-bold transition-all active:scale-95 shadow-sm shadow-emerald-900/20"
              >
                <Timer className="w-3.5 h-3.5 text-emerald-400" />
                <span>Pit Stop Reaction Drill</span>
              </button>

              <button
                onClick={() => setShowStandingsModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-purple-950/60 hover:bg-purple-900/80 text-purple-300 border border-purple-700/50 font-bold transition-all active:scale-95 shadow-sm shadow-purple-900/20"
              >
                <Trophy className="w-3.5 h-3.5 text-purple-400" />
                <span>Live Standings</span>
              </button>

              <button
                onClick={() => setShowDebriefModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-950/60 hover:bg-amber-900/80 text-amber-300 border border-amber-700/50 font-bold transition-all active:scale-95 shadow-sm shadow-amber-900/20"
              >
                <Trophy className="w-3.5 h-3.5 text-yellow-400" />
                <span>Podium Debrief</span>
              </button>

              <button
                onClick={toggleEngineSynth}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-[11px] font-mono font-bold transition-all active:scale-95 ${
                  engineAudioActive
                    ? 'bg-rose-500 text-black border-rose-400 shadow-sm shadow-rose-500/30'
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
                title="Toggle V6 Turbo Hybrid Audio Synthesizer"
              >
                {engineAudioActive ? <Volume2 className="w-3 h-3" /> : <VolumeX className="w-3 h-3" />}
                <span>V6 AUDIO</span>
              </button>
            </div>

            <div className="flex items-center gap-3">
              <RadioWaveformVisualizer />
            </div>
          </div>
        </div>

        {/* Tab 1: Tactical Pit Wall Workspace */}
        {activeTab === 'tactical' && (
          <div className="flex flex-col gap-4 flex-1">
            {/* Primary 3-Column Pit Wall Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
              {/* Left Column: Timing Tower (4 cols) */}
              <div className="lg:col-span-4 min-h-[500px] flex flex-col">
                <TimingTower />
              </div>

              {/* Center Column: Live Track Map & Pit Rejoin Radar (4 cols) */}
              <div className="lg:col-span-4 flex flex-col gap-4 min-h-[500px]">
                <div className="flex-1 min-h-[290px]">
                  <TrackMap />
                </div>
                <div className="min-h-[210px]">
                  <PitRejoinRadar />
                </div>
              </div>

              {/* Right Column: Decision Intelligence & Counterfactuals (4 cols) */}
              <div className="lg:col-span-4 flex flex-col gap-4 min-h-[500px]">
                <StrategyCard />
                <div className="flex-1 min-h-[210px]">
                  <ExplainabilityPanel />
                </div>
                <div className="flex-1 min-h-[200px]">
                  <CounterfactualView />
                </div>
              </div>
            </div>

            {/* Secondary Advanced Tactical Grid (Stint Planner, Battle Radar, Doppler Weather) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-4">
                <StintStrategyPlanner />
              </div>
              <div className="lg:col-span-4">
                <DriverBattleRadar />
              </div>
              <div className="lg:col-span-4">
                <WeatherDopplerRadar />
              </div>
            </div>

            {/* Competitor Undercut & Overcut Threat Radar */}
            <UndercutThreatMatrix />

            {/* Micro-Sector Timing Grid */}
            <MiniSectorTimingGrid />

            {/* Race Event Logger */}
            <RaceEventLogViewer />
          </div>
        )}

        {/* Tab 2: Telemetry & Degradation Lab */}
        {activeTab === 'telemetry' && (
          <div className="flex flex-col gap-4 flex-1">
            <TelemetryLab />
            <DualDriverTelemetryOverlay />
            <LapTimeDeltaTDecomposition />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6">
                <ChassisSetupTuner />
              </div>
              <div className="lg:col-span-6">
                <WeatherDopplerRadar />
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: AI Reasoning & Policy Center */}
        {activeTab === 'explainability' && (
          <div className="flex flex-col gap-4 flex-1">
            <SHAPFeatureWaterfall />
            <DQNPolicyVisualizer />
            <MonteCarloStrategySim />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6 flex flex-col gap-4">
                <StrategyCard />
                <ExplainabilityPanel />
                <StintStrategyPlanner />
              </div>
              <div className="lg:col-span-6 flex flex-col gap-4">
                <CounterfactualView />
                <AIPitWallCopilot />
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Strategy Sandbox */}
        {activeTab === 'sandbox' && (
          <div className="flex flex-col gap-4 flex-1">
            <StrategySandbox />
            <PitStrategyIsochroneMatrix />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6">
                <ChassisSetupTuner />
              </div>
              <div className="lg:col-span-6">
                <PitStopReactionSim />
              </div>
            </div>
            <MonteCarloStrategySim />
          </div>
        )}

        {/* Bottom Live Radio & Event Log Ticker */}
        <div className="glass-panel rounded-xl p-3 border border-apex-border flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-apex-cyan font-black uppercase tracking-wider shrink-0 px-2 py-1 rounded bg-cyan-950/60 border border-cyan-800/40">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Race Control Feed</span>
          </div>

          <div className="flex-1 overflow-x-auto whitespace-nowrap flex items-center gap-6 text-slate-300">
            {events.length > 0 ? (
              events
                .slice(-6)
                .reverse()
                .map((ev, idx) => (
                  <div key={idx} className="flex items-center gap-2 shrink-0">
                    <span className="text-slate-500 font-bold">[Lap {ev.lap}]</span>
                    <span className="text-apex-cyan uppercase text-[10px] font-bold">
                      [{ev.event_type}]
                    </span>
                    <span className="text-slate-200">{ev.message}</span>
                  </div>
                ))
            ) : (
              <span className="text-slate-500 italic">Waiting for green flag...</span>
            )}
          </div>
        </div>
      </main>

      {/* Floating AI Strategist Copilot Popup Modal */}
      {showCopilotModal && (
        <div className="fixed bottom-16 right-6 z-50 w-full max-w-lg shadow-2xl animate-fadeIn">
          <div className="relative">
            <button
              onClick={() => setShowCopilotModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-4 h-4" />
            </button>
            <AIPitWallCopilot />
          </div>
        </div>
      )}

      {/* Chassis Aero Setup Modal */}
      {showAeroTunerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowAeroTunerModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <ChassisSetupTuner />
          </div>
        </div>
      )}

      {/* Pit Stop Reaction Drill Modal */}
      {showPitSimModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-xl">
            <button
              onClick={() => setShowPitSimModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <PitStopReactionSim />
          </div>
        </div>
      )}

      {/* Live Championship Standings Modal */}
      {showStandingsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-2xl">
            <button
              onClick={() => setShowStandingsModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <ChampionshipStandings />
          </div>
        </div>
      )}

      {/* Driver Pit Wall Telemetry Modal (when clicked) */}
      {inspectedCar && <DriverTelemetryModal />}

      {/* Post-Race Podium & Analytics Debrief Modal */}
      {showDebriefModal && (
        <PostRaceDebriefModal onClose={() => setShowDebriefModal(false)} />
      )}
    </div>
  );
};

export default App;
