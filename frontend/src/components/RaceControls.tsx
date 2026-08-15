import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { useRaceSocket } from '../hooks/useRaceSocket';
import {
  Play,
  Pause,
  StepForward,
  RotateCcw,
  ShieldAlert,
  CloudRain,
  Flame,
  Settings,
} from 'lucide-react';

const TRACK_OPTIONS = [
  { id: 'silverstone', name: 'Silverstone (GB)' },
  { id: 'monza', name: 'Monza (IT)' },
  { id: 'spa', name: 'Spa-Francorchamps (BE)' },
  { id: 'monaco', name: 'Monaco (MC)' },
  { id: 'interlagos', name: 'Interlagos (BR)' },
];

export const RaceControls: React.FC = () => {
  const { isRunning, simSpeed, raceState } = useRaceStore();
  const { play, pause, step, setSimulationSpeed, injectIncident, initRace } = useRaceSocket();

  const [selectedTrack, setSelectedTrack] = useState('silverstone');
  const [seed, setSeed] = useState(42);

  const handleNewRace = () => {
    initRace(selectedTrack, Number(seed));
  };

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 border border-apex-border shadow-2xl">
      {/* Playback Controls */}
      <div className="flex items-center gap-2">
        {isRunning ? (
          <button
            onClick={pause}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-amber-500/20"
          >
            <Pause className="w-4 h-4 fill-current" />
            <span>Pause</span>
          </button>
        ) : (
          <button
            onClick={play}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-emerald-500/20"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Simulate Race</span>
          </button>
        )}

        <button
          onClick={step}
          disabled={isRunning}
          className="flex items-center gap-1 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
        >
          <StepForward className="w-4 h-4" />
          <span>Step 1 Lap</span>
        </button>

        {/* Speed Multiplier */}
        <div className="flex items-center bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-mono ml-2">
          {[1.0, 2.0, 5.0, 10.0].map((s) => (
            <button
              key={s}
              onClick={() => setSimulationSpeed(s)}
              className={`px-2.5 py-1 rounded transition-all ${
                simSpeed === s
                  ? 'bg-apex-cyan text-black font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Incident Injectors */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold hidden md:inline">
          Inject Chaos:
        </span>
        <button
          onClick={() => injectIncident('SAFETY_CAR')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-yellow-950/50 hover:bg-yellow-900 text-yellow-400 border border-yellow-800/60 text-xs font-bold transition-all"
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Safety Car</span>
        </button>
        <button
          onClick={() => injectIncident('VSC')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-950/50 hover:bg-amber-900 text-amber-300 border border-amber-800/60 text-xs font-bold transition-all"
        >
          <Flame className="w-3.5 h-3.5" />
          <span>VSC</span>
        </button>
        <button
          onClick={() => injectIncident('RAIN')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/50 hover:bg-cyan-900 text-cyan-300 border border-cyan-800/60 text-xs font-bold transition-all"
        >
          <CloudRain className="w-3.5 h-3.5" />
          <span>Sudden Rain</span>
        </button>
      </div>

      {/* Track & Seed Config */}
      <div className="flex items-center gap-2">
        <select
          value={selectedTrack}
          onChange={(e) => setSelectedTrack(e.target.value)}
          className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-apex-cyan"
        >
          {TRACK_OPTIONS.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>

        <button
          onClick={handleNewRace}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Race</span>
        </button>
      </div>
    </div>
  );
};
