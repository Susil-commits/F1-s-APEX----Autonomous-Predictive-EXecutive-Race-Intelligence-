import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { HeroDecisionBar } from './components/HeroDecisionBar';
import { LiveRaceStateView } from './components/LiveRaceStateView';
import { PredictionExplorerView } from './components/PredictionExplorerView';
import { CounterfactualLabView } from './components/CounterfactualLabView';
import { StrategyPolicyView } from './components/StrategyPolicyView';
import { DataLineageView } from './components/DataLineageView';
import { AgentTraceView } from './components/AgentTraceView';
import { AblationStudyView } from './components/AblationStudyView';
import { ErrorAnalysisView } from './components/ErrorAnalysisView';
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
import { LiveScenarioInjector } from './components/LiveScenarioInjector';
import { BenchmarkComparisonModal } from './components/BenchmarkComparisonModal';
import { RaceHistoryQA } from './components/RaceHistoryQA';
import { TyreIntelligenceView } from './components/TyreIntelligenceView';
import { WeatherIntelligenceView } from './components/WeatherIntelligenceView';
import { OpponentIntelligenceView } from './components/OpponentIntelligenceView';
import { DriverIntelligenceView } from './components/DriverIntelligenceView';
import { VehicleHealthView } from './components/VehicleHealthView';
import { HistoricalReplayView } from './components/HistoricalReplayView';
import { ChampionshipTournamentView } from './components/ChampionshipTournamentView';
import { SystemHealthView } from './components/SystemHealthView';
import { PitWallConsensusModal } from './components/PitWallConsensusModal';
import { MCTSVisualizer } from './components/MCTSVisualizer';
import { AerodynamicWakeRadar } from './components/AerodynamicWakeRadar';
import { TyreThermodynamicsView } from './components/TyreThermodynamicsView';
import { GhostCarTelemetryOverlay } from './components/GhostCarTelemetryOverlay';
import { SensorAnomalyDetector } from './components/SensorAnomalyDetector';
import { RadioCommsHub } from './components/RadioCommsHub';
import { CommandPalette } from './components/CommandPalette';
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
  Zap,
  BarChart2,
  Users,
  X,
  Wind,
  Command,
} from 'lucide-react';

export const App: React.FC = () => {
  const { raceState, activeTab, inspectedCar, showDebriefModal, setShowDebriefModal } =
    useRaceStore();
  const [showCopilotModal, setShowCopilotModal] = useState<boolean>(false);
  const [showConsensusModal, setShowConsensusModal] = useState<boolean>(false);
  const [showQAModal, setShowQAModal] = useState<boolean>(false);
  const [showPitSimModal, setShowPitSimModal] = useState<boolean>(false);
  const [showStandingsModal, setShowStandingsModal] = useState<boolean>(false);
  const [showAeroTunerModal, setShowAeroTunerModal] = useState<boolean>(false);
  const [showBenchmarkModal, setShowBenchmarkModal] = useState<boolean>(false);
  const [showCommandPalette, setShowCommandPalette] = useState<boolean>(false);
  const [showRadioHubModal, setShowRadioHubModal] = useState<boolean>(false);
  const [engineAudioActive, setEngineAudioActive] = useState<boolean>(false);

  // Global Ctrl+K / Cmd+K listener for Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const toggleEngineSynth = () => {
    const active = audioEngine.toggleEngineSound(11500);
    setEngineAudioActive(active);
  };

  return (
    <div className="min-h-screen bg-apex-bg text-slate-100 flex flex-col selection:bg-apex-cyan selection:text-black relative">
      {/* Top Mission Control Header */}
      <Header />

      {/* Main Workspace Container */}
      <main className="flex-1 p-4 max-w-[1920px] w-full mx-auto flex flex-col gap-4">
        {/* Top Control Bar & Time-Travel DVR Scrubber */}
        <div className="flex flex-col gap-2">
          <RaceControls />
          <RaceTimeTravelDVR />

          {/* Quick Bar Action Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setShowCommandPalette(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Command className="w-3.5 h-3.5 text-[#E10600]" />
                <span>Command Palette</span>
                <span className="text-[10px] px-1 py-0.2 rounded bg-black text-slate-400 border border-slate-800">
                  Ctrl+K
                </span>
              </button>

              <button
                onClick={() => setShowCopilotModal(!showCopilotModal)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Bot className="w-3.5 h-3.5 text-[#E10600]" />
                <span>AI Strategist Copilot</span>
              </button>

              <button
                onClick={() => setShowQAModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Brain className="w-3.5 h-3.5 text-[#E10600]" />
                <span>RAG Race Debrief</span>
              </button>

              <button
                onClick={() => setShowBenchmarkModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <BarChart2 className="w-3.5 h-3.5 text-purple-400" />
                <span>Benchmark Suite</span>
              </button>

              <button
                onClick={() => setShowConsensusModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Users className="w-3.5 h-3.5 text-emerald-400" />
                <span>5-Agent Deliberation</span>
              </button>

              <button
                onClick={() => setShowDebriefModal(true)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#12151E] hover:bg-[#1A1F2C] text-white border border-[#2A3042] font-bold transition-all active:scale-95 shadow-sm hover:border-[#E10600]"
              >
                <Trophy className="w-3.5 h-3.5 text-yellow-400" />
                <span>Podium Debrief</span>
              </button>
            </div>

            <div className="flex items-center gap-3">
              <RadioWaveformVisualizer />
            </div>
          </div>
        </div>

        {/* HERO DECISION INTELLIGENCE BAR (Prominent on Tactical & Race State) */}
        {(activeTab === 'tactical' || activeTab === 'ai_assistant' || activeTab === 'race_state') && (
          <HeroDecisionBar />
        )}

        {/* ========================================================================= */}
        {/* 10 CORE AI / ML DECISION INTELLIGENCE WORKSPACES */}
        {/* ========================================================================= */}

        {/* 1. Tactical AI Strategy Command Center */}
        {(activeTab === 'tactical' || activeTab === 'ai_assistant') && (
          <div className="flex flex-col gap-4 flex-1">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Timing Tower (Left 3 cols) */}
              <div className="lg:col-span-3">
                <TimingTower />
              </div>

              {/* Center Track Map & Telemetry (6 cols) */}
              <div className="lg:col-span-6 flex flex-col gap-4">
                <TrackMap />
                <TelemetryCharts />
              </div>

              {/* Right Strategic Insights (3 cols) */}
              <div className="lg:col-span-3 flex flex-col gap-4">
                <StrategyCard />
                <ExplainabilityPanel />
                <LiveScenarioInjector />
                <CounterfactualView />
              </div>
            </div>

            {/* Radar Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <PitRejoinRadar />
              <DriverBattleRadar />
              <WeatherDopplerRadar />
            </div>

            <UndercutThreatMatrix />
            <MiniSectorTimingGrid />
            <RaceEventLogViewer />
          </div>
        )}

        {/* 2. Live Race State & Timing */}
        {activeTab === 'race_state' && <LiveRaceStateView />}

        {/* 3. Prediction Explorer (XGBoost Flagship & Supervised Baselines) */}
        {activeTab === 'prediction_explorer' && <PredictionExplorerView />}

        {/* 4. Counterfactual Lab (What-If Simulation & Utility Intervals) */}
        {activeTab === 'counterfactual_lab' && <CounterfactualLabView />}

        {/* 5. Strategy Decision & Policy Engine (Safe RL Action Masking) */}
        {activeTab === 'strategy_policy' && <StrategyPolicyView />}

        {/* 6. Model Explainability (TreeSHAP & Pairwise Differentials) */}
        {activeTab === 'explainability' && (
          <div className="flex flex-col gap-4 flex-1">
            <SHAPFeatureWaterfall />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-6 flex flex-col gap-4">
                <StrategyCard />
                <ExplainabilityPanel />
              </div>
              <div className="lg:col-span-6 flex flex-col gap-4">
                <AIPitWallCopilot />
              </div>
            </div>
          </div>
        )}

        {/* 7. Data Quality, Lineage & Low-Latency Feature Store */}
        {activeTab === 'data_lineage' && <DataLineageView />}

        {/* 8. Agent Trace & Domain MCP Tools */}
        {activeTab === 'agent_trace' && <AgentTraceView />}

        {/* 9. System Ablation & Decision Contribution Analysis */}
        {activeTab === 'ablation_study' && <AblationStudyView />}

        {/* 10. System Monitoring, Resilience & Error Analysis */}
        {activeTab === 'error_monitoring' && <ErrorAnalysisView />}

        {/* ========================================================================= */}
        {/* AUXILIARY RESEARCH & DEEP DIVE WORKSPACES */}
        {/* ========================================================================= */}

        {activeTab === 'tyre_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <TyreIntelligenceView />
          </div>
        )}

        {activeTab === 'weather_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <WeatherIntelligenceView />
          </div>
        )}

        {activeTab === 'opponent_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <OpponentIntelligenceView />
          </div>
        )}

        {activeTab === 'driver_intel' && (
          <div className="flex flex-col gap-4 flex-1">
            <DriverIntelligenceView />
          </div>
        )}

        {activeTab === 'vehicle_health' && (
          <div className="flex flex-col gap-4 flex-1">
            <VehicleHealthView />
          </div>
        )}

        {activeTab === 'counterfactual' && (
          <div className="flex flex-col gap-4 flex-1">
            <LiveScenarioInjector />
            <StrategySandbox />
            <CounterfactualView />
            <MonteCarloStrategySim />
          </div>
        )}

        {activeTab === 'rl_training' && (
          <div className="flex flex-col gap-4 flex-1">
            <DQNPolicyVisualizer />
            <SHAPFeatureWaterfall />
            <ExplainabilityPanel />
          </div>
        )}

        {activeTab === 'telemetry' && (
          <div className="flex flex-col gap-4 flex-1">
            <GhostCarTelemetryOverlay />
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

        {activeTab === 'replays' && (
          <div className="flex flex-col gap-4 flex-1">
            <HistoricalReplayView />
          </div>
        )}

        {activeTab === 'championship' && (
          <div className="flex flex-col gap-4 flex-1">
            <ChampionshipTournamentView />
            <ChampionshipStandings />
          </div>
        )}

        {activeTab === 'system_health' && (
          <div className="flex flex-col gap-4 flex-1">
            <SystemHealthView />
          </div>
        )}
      </main>

      {/* Floating AI Pit Wall Copilot Drawer (when opened) */}
      {showCopilotModal && (
        <div className="fixed bottom-6 right-6 z-40 w-96 max-w-[calc(100vw-3rem)] shadow-2xl animate-slide-up">
          <div className="relative">
            <button
              onClick={() => setShowCopilotModal(false)}
              className="absolute top-2 right-2 z-10 p-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-4 h-4" />
            </button>
            <AIPitWallCopilot />
          </div>
        </div>
      )}

      {/* Benchmark Comparison Modal */}
      <BenchmarkComparisonModal
        isOpen={showBenchmarkModal}
        onClose={() => setShowBenchmarkModal(false)}
      />

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

      {/* Driver Pit Wall Telemetry Modal */}
      {inspectedCar && <DriverTelemetryModal />}

      {/* RAG Race History Debrief Modal */}
      {showQAModal && <RaceHistoryQA onClose={() => setShowQAModal(false)} />}

      {/* Multi-Agent Pit Wall Consensus Modal */}
      <PitWallConsensusModal
        isOpen={showConsensusModal}
        onClose={() => setShowConsensusModal(false)}
      />

      {/* Post-Race Podium & Analytics Debrief Modal */}
      {showDebriefModal && (
        <PostRaceDebriefModal onClose={() => setShowDebriefModal(false)} />
      )}

      {/* Neural Pit Radio Hub Modal */}
      {showRadioHubModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowRadioHubModal(false)}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
            <RadioCommsHub />
          </div>
        </div>
      )}

      {/* Global Command Palette (Ctrl+K) */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onOpenConsensus={() => setShowConsensusModal(true)}
        onOpenQA={() => setShowQAModal(true)}
      />
    </div>
  );
};

export default App;
