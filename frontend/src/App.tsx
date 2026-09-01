import React, { useState, useEffect } from 'react';
import { Header, AppMode } from './components/Header';
import { CoreMode } from './modes/core/CoreMode';
import { PitWallMode } from './modes/pitwall/PitWallMode';
import { RaceControls } from './components/RaceControls';
import { RaceTimeTravelDVR } from './components/RaceTimeTravelDVR';
import { CommandPalette } from './components/CommandPalette';
import { AIPitWallCopilot } from './components/AIPitWallCopilot';
import { PitWallConsensusModal } from './components/PitWallConsensusModal';
import { RaceHistoryQA } from './components/RaceHistoryQA';
import { PostRaceDebriefModal } from './components/PostRaceDebriefModal';
import { BenchmarkComparisonModal } from './components/BenchmarkComparisonModal';
import { ChassisSetupTuner } from './components/ChassisSetupTuner';
import { PitStopReactionSim } from './components/PitStopReactionSim';
import { ChampionshipStandings } from './components/ChampionshipStandings';
import { DriverTelemetryModal } from './components/DriverTelemetryModal';
import { RadioCommsHub } from './components/RadioCommsHub';
import { RadioWaveformVisualizer } from './components/RadioWaveformVisualizer';
import { useRaceStore } from './store/raceStore';
import {
  Command,
  Bot,
  Brain,
  BarChart2,
  Users,
  Trophy,
  X,
} from 'lucide-react';

export const App: React.FC = () => {
  const [appMode, setAppMode] = useState<AppMode>('simple');
  const { inspectedCar, showDebriefModal, setShowDebriefModal } = useRaceStore();

  const [showCopilotModal, setShowCopilotModal] = useState<boolean>(false);
  const [showConsensusModal, setShowConsensusModal] = useState<boolean>(false);
  const [showQAModal, setShowQAModal] = useState<boolean>(false);
  const [showPitSimModal, setShowPitSimModal] = useState<boolean>(false);
  const [showStandingsModal, setShowStandingsModal] = useState<boolean>(false);
  const [showAeroTunerModal, setShowAeroTunerModal] = useState<boolean>(false);
  const [showBenchmarkModal, setShowBenchmarkModal] = useState<boolean>(false);
  const [showCommandPalette, setShowCommandPalette] = useState<boolean>(false);
  const [showRadioHubModal, setShowRadioHubModal] = useState<boolean>(false);

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

  return (
    <div className="min-h-screen bg-apex-bg text-slate-100 flex flex-col selection:bg-apex-cyan selection:text-black relative">
      {/* Mission Control Header with DRS Dual-Mode Switch */}
      <Header appMode={appMode} onSelectMode={setAppMode} />

      {/* Main Container */}
      <main className="flex-1 p-4 max-w-[1920px] w-full mx-auto flex flex-col gap-4">
        {/* ========================================================================= */}
        {/* MODE 1: CORE / SIMPLE MODE (V1 BASELINE) */}
        {/* ========================================================================= */}
        {appMode === 'simple' && (
          <CoreMode onSwitchToPitWall={() => setAppMode('pitwall')} />
        )}

        {/* ========================================================================= */}
        {/* MODE 2: PIT-WALL MODE (V2 LIVE STRATEGY & DIGITAL TWIN) */}
        {/* ========================================================================= */}
        {appMode === 'pitwall' && (
          <div className="flex flex-col gap-3 flex-1">
            {/* Live Session Controls & Scrubbing */}
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

            {/* 5-Zone Pit Wall Canvas with Left-Rail Navigation */}
            <PitWallMode />
          </div>
        )}
      </main>

      {/* ========================================================================= */}
      {/* GLOBAL MODALS & UTILITY OVERLAYS */}
      {/* ========================================================================= */}

      {/* AI Pit Wall Copilot Side Drawer */}
      {showCopilotModal && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-[#0A0C11] border-l border-[#2A3042] shadow-2xl animate-slideLeft flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-[#2A3042] bg-[#10131B]">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-[#E10600]" />
              <h3 className="font-mono font-bold text-sm text-white">AI PIT WALL COPILOT</h3>
            </div>
            <button
              onClick={() => setShowCopilotModal(false)}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
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
