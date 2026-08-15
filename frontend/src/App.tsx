import React from 'react';
import { Header } from './components/Header';
import { TimingTower } from './components/TimingTower';
import { TrackMap } from './components/TrackMap';
import { TelemetryCharts } from './components/TelemetryCharts';
import { StrategyCard } from './components/StrategyCard';
import { ExplainabilityPanel } from './components/ExplainabilityPanel';
import { CounterfactualView } from './components/CounterfactualView';
import { RaceControls } from './components/RaceControls';
import { useRaceStore } from './store/raceStore';
import { Terminal, Radio } from 'lucide-react';

export const App: React.FC = () => {
  const { raceState } = useRaceStore();

  const events = raceState?.events_log || [];

  return (
    <div className="min-h-screen bg-apex-bg text-slate-100 flex flex-col selection:bg-apex-cyan selection:text-black">
      {/* Top Mission Control Header */}
      <Header />

      {/* Main Grid Workspace */}
      <main className="flex-1 p-4 max-w-[1920px] w-full mx-auto flex flex-col gap-4">
        {/* Top Control Bar */}
        <RaceControls />

        {/* Core Mission Control 3-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 items-stretch">
          {/* Left Column: Timing Tower (4 cols) */}
          <div className="lg:col-span-4 min-h-[500px] flex flex-col">
            <TimingTower />
          </div>

          {/* Center Column: Live Track Map & Telemetry Charts (4 cols) */}
          <div className="lg:col-span-4 flex flex-col gap-4 min-h-[500px]">
            <div className="flex-1 min-h-[260px]">
              <TrackMap />
            </div>
            <div className="flex-1 min-h-[260px]">
              <TelemetryCharts />
            </div>
          </div>

          {/* Right Column: Decision Intelligence, Explainability & Counterfactuals (4 cols) */}
          <div className="lg:col-span-4 flex flex-col gap-4 min-h-[500px]">
            {/* Primary Action Call */}
            <StrategyCard />

            {/* Explainability Reasoning Tree */}
            <div className="flex-1 min-h-[220px]">
              <ExplainabilityPanel />
            </div>

            {/* What-If Counterfactual Comparisons */}
            <div className="flex-1 min-h-[200px]">
              <CounterfactualView />
            </div>
          </div>
        </div>

        {/* Bottom Live Radio & Event Log Ticker */}
        <div className="glass-panel rounded-xl p-3 border border-apex-border flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-apex-cyan font-bold uppercase tracking-wider shrink-0 px-2 py-1 rounded bg-cyan-950/60 border border-cyan-800/40">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Race Control Feed</span>
          </div>

          <div className="flex-1 overflow-x-auto whitespace-nowrap flex items-center gap-6 text-slate-300">
            {events.length > 0 ? (
              events.slice(-5).reverse().map((ev, idx) => (
                <div key={idx} className="flex items-center gap-2 shrink-0">
                  <span className="text-slate-500 font-bold">[Lap {ev.lap}]</span>
                  <span className="text-apex-cyan uppercase text-[10px] font-bold">[{ev.event_type}]</span>
                  <span>{ev.message}</span>
                </div>
              ))
            ) : (
              <span className="text-slate-500 italic">Waiting for green flag...</span>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
