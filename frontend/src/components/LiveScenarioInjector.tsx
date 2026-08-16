import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  CloudRain,
  CloudDrizzle,
  Sun,
  ShieldAlert,
  AlertTriangle,
  Flame,
  RotateCcw,
  Zap,
  CheckCircle2,
} from 'lucide-react';

export const LiveScenarioInjector: React.FC = () => {
  const { raceState } = useRaceStore();
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [lastFeedback, setLastFeedback] = useState<string | null>(null);

  const injectScenario = async (scenarioType: string, extra: Record<string, any> = {}) => {
    setLoadingScenario(scenarioType);
    try {
      const res = await fetch('/api/simulator/inject-scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_type: scenarioType, ...extra }),
      });
      if (res.ok) {
        const data = await res.json();
        setLastFeedback(`Applied: ${data.scenario} on Lap ${data.lap}`);
        setTimeout(() => setLastFeedback(null), 3500);
      }
    } catch (err) {
      console.error('Scenario injection failed:', err);
    } finally {
      setLoadingScenario(null);
    }
  };

  if (!raceState) return null;

  const isWet = raceState.weather.condition === 'WET';
  const isDamp = raceState.weather.condition === 'DAMP';
  const isSC = raceState.safety_car === 'SAFETY_CAR';
  const isVSC = raceState.safety_car === 'VSC';

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400 animate-pulse" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Pit-Wall Scenario & Hazard Injector
          </h3>
        </div>
        <span className="text-[9.5px] bg-amber-950/60 text-amber-300 border border-amber-800/60 px-2 py-0.5 rounded font-bold">
          LIVE STRESS-TEST
        </span>
      </div>

      {/* Active State Badges */}
      <div className="grid grid-cols-2 gap-2 mb-3 font-sans text-[11px]">
        <div className="bg-slate-900/80 border border-slate-800 p-2 rounded-lg flex items-center justify-between">
          <span className="text-slate-400">Track Status</span>
          <span
            className={`font-black font-mono text-xs px-2 py-0.5 rounded ${
              isWet
                ? 'bg-blue-950 text-blue-300 border border-blue-700'
                : isDamp
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700'
                : 'bg-emerald-950 text-emerald-300 border border-emerald-700'
            }`}
          >
            {raceState.weather.condition} ({Math.round(raceState.weather.rain_intensity * 100)}%)
          </span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-2 rounded-lg flex items-center justify-between">
          <span className="text-slate-400">Flags / Safety</span>
          <span
            className={`font-black font-mono text-xs px-2 py-0.5 rounded ${
              isSC
                ? 'bg-amber-950 text-amber-300 border border-amber-700 animate-pulse'
                : isVSC
                ? 'bg-orange-950 text-orange-300 border border-orange-700'
                : 'bg-slate-800 text-slate-300'
            }`}
          >
            {raceState.safety_car === 'NONE' ? 'GREEN FLAG' : raceState.safety_car}
          </span>
        </div>
      </div>

      {/* Feedback Toast */}
      {lastFeedback && (
        <div className="mb-2.5 px-3 py-1.5 rounded bg-emerald-950/80 border border-emerald-700/80 text-emerald-300 text-[11px] font-mono flex items-center gap-1.5 animate-fade-in">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>{lastFeedback}</span>
        </div>
      )}

      {/* Hazard Trigger Buttons Grid */}
      <div className="grid grid-cols-3 gap-2">
        {/* Torrential Rain */}
        <button
          onClick={() => injectScenario('TORRENTIAL_RAIN', { intensity: 0.9 })}
          disabled={loadingScenario !== null}
          className="flex flex-col items-center justify-center p-2 rounded-lg bg-blue-950/40 hover:bg-blue-900/60 border border-blue-800/60 text-blue-200 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
        >
          <CloudRain className="w-4 h-4 mb-1 text-blue-400" />
          <span className="font-bold text-[10px]">Flash Rain</span>
          <span className="text-[8.5px] text-blue-400/80 font-sans">90% Wet</span>
        </button>

        {/* Damp Track */}
        <button
          onClick={() => injectScenario('DAMP_TRACK', { intensity: 0.35 })}
          disabled={loadingScenario !== null}
          className="flex flex-col items-center justify-center p-2 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-800/60 text-cyan-200 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
        >
          <CloudDrizzle className="w-4 h-4 mb-1 text-cyan-400" />
          <span className="font-bold text-[10px]">Light Rain</span>
          <span className="text-[8.5px] text-cyan-400/80 font-sans">Damp Track</span>
        </button>

        {/* Dry Track */}
        <button
          onClick={() => injectScenario('DRY_TRACK')}
          disabled={loadingScenario !== null}
          className="flex flex-col items-center justify-center p-2 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-800/60 text-emerald-200 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
        >
          <Sun className="w-4 h-4 mb-1 text-amber-400" />
          <span className="font-bold text-[10px]">Dry Circuit</span>
          <span className="text-[8.5px] text-emerald-400/80 font-sans">Clear Line</span>
        </button>

        {/* Full Safety Car */}
        <button
          onClick={() => injectScenario('SAFETY_CAR', { laps: 4 })}
          disabled={loadingScenario !== null}
          className="flex flex-col items-center justify-center p-2 rounded-lg bg-amber-950/40 hover:bg-amber-900/60 border border-amber-800/60 text-amber-200 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
        >
          <ShieldAlert className="w-4 h-4 mb-1 text-amber-400" />
          <span className="font-bold text-[10px]">Deploy SC</span>
          <span className="text-[8.5px] text-amber-400/80 font-sans">4 Laps SC</span>
        </button>

        {/* VSC */}
        <button
          onClick={() => injectScenario('VSC', { laps: 3 })}
          disabled={loadingScenario !== null}
          className="flex flex-col items-center justify-center p-2 rounded-lg bg-orange-950/40 hover:bg-orange-900/60 border border-orange-800/60 text-orange-200 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
        >
          <AlertTriangle className="w-4 h-4 mb-1 text-orange-400" />
          <span className="font-bold text-[10px]">Deploy VSC</span>
          <span className="text-[8.5px] text-orange-400/80 font-sans">Delta Pace</span>
        </button>

        {/* Puncture / Cliff */}
        <button
          onClick={() => injectScenario('PUNCTURE', { wear_delta: 50.0 })}
          disabled={loadingScenario !== null}
          className="flex flex-col items-center justify-center p-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/60 text-rose-200 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50"
        >
          <Flame className="w-4 h-4 mb-1 text-rose-400" />
          <span className="font-bold text-[10px]">Puncture / Cliff</span>
          <span className="text-[8.5px] text-rose-400/80 font-sans">+50% Wear</span>
        </button>
      </div>

      {/* Reset Button */}
      <button
        onClick={() => injectScenario('CLEAR_HAZARDS')}
        disabled={loadingScenario !== null}
        className="mt-3 w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 font-bold transition-all text-[10.5px]"
      >
        <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
        <span>Clear Hazards & Reset Green Flag</span>
      </button>
    </div>
  );
};
