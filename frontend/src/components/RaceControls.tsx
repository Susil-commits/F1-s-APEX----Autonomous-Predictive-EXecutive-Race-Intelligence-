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
  FastForward,
} from 'lucide-react';
import { CIRCUIT_DATABASE } from '../data/trackGeometries';

const TRACK_LIST = [
  { id: 'silverstone', name: 'Silverstone', country: 'Great Britain', flag: '🇬🇧' },
  { id: 'monza', name: 'Monza', country: 'Italy', flag: '🇮🇹' },
  { id: 'spa', name: 'Spa-Francorchamps', country: 'Belgium', flag: '🇧🇪' },
  { id: 'monaco', name: 'Monaco', country: 'Monaco', flag: '🇲🇨' },
  { id: 'interlagos', name: 'Interlagos', country: 'Brazil', flag: '🇧🇷' },
];

export const RaceControls: React.FC = () => {
  const { isRunning, simSpeed, raceState } = useRaceStore();
  const { play, pause, step, setSimulationSpeed, injectIncident, initRace } = useRaceSocket();

  const [selectedTrack, setSelectedTrack] = useState('silverstone');
  const [seed, setSeed] = useState(42);

  const handleTrackChange = (newTrack: string) => {
    setSelectedTrack(newTrack);
    initRace(newTrack, Number(seed));
  };

  const handleNewRace = () => {
    initRace(selectedTrack, Number(seed));
  };

  return (
    <div className="glass-panel rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 border border-apex-border shadow-2xl">
      {/* Playback Controls */}
      <div className="flex items-center gap-2">
        {isRunning ? (
          <button
            onClick={pause}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-amber-500/20 active:scale-95"
          >
            <Pause className="w-3.5 h-3.5 fill-current" />
            <span>Pause</span>
          </button>
        ) : (
          <button
            onClick={play}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-extrabold text-xs uppercase tracking-wider transition-all shadow-lg shadow-emerald-500/25 active:scale-95"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Simulate Race</span>
          </button>
        )}

        <button
          onClick={step}
          disabled={isRunning}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-xs font-semibold border border-slate-700 transition-all active:scale-95"
        >
          <StepForward className="w-3.5 h-3.5" />
          <span>Step Lap</span>
        </button>

        {/* Speed Multipliers */}
        <div className="flex items-center bg-slate-950/80 p-0.5 rounded-lg border border-slate-800 text-xs font-mono ml-1">
          {[1.0, 2.0, 5.0, 10.0, 20.0].map((s) => (
            <button
              key={s}
              onClick={() => setSimulationSpeed(s)}
              className={`px-2 py-1 rounded transition-all text-[11px] ${
                simSpeed === s
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Incident Chaos Injectors */}
      <div className="flex items-center gap-1.5">
        <span className="text-[9px] uppercase font-mono text-slate-500 font-bold hidden xl:inline">
          Inject Chaos:
        </span>
        <button
          onClick={() => injectIncident('SAFETY_CAR')}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-yellow-950/40 hover:bg-yellow-900/60 text-yellow-300 border border-yellow-700/50 text-xs font-bold transition-all active:scale-95 shadow-sm shadow-yellow-900/20"
        >
          <ShieldAlert className="w-3.5 h-3.5 text-yellow-400" />
          <span>Safety Car</span>
        </button>
        <button
          onClick={() => injectIncident('VSC')}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-amber-950/40 hover:bg-amber-900/60 text-amber-300 border border-amber-700/50 text-xs font-bold transition-all active:scale-95 shadow-sm shadow-amber-900/20"
        >
          <Flame className="w-3.5 h-3.5 text-amber-400" />
          <span>VSC</span>
        </button>
        <button
          onClick={() => injectIncident('RAIN')}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-700/50 text-xs font-bold transition-all active:scale-95 shadow-sm shadow-cyan-900/20"
        >
          <CloudRain className="w-3.5 h-3.5 text-cyan-400" />
          <span>Sudden Rain</span>
        </button>
      </div>

      {/* Track & Seed Config */}
      <div className="flex items-center gap-2">
        <select
          value={selectedTrack}
          onChange={(e) => handleTrackChange(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-apex-cyan font-medium cursor-pointer"
        >
          {TRACK_LIST.map((t) => (
            <option key={t.id} value={t.id} className="bg-slate-900 text-slate-200">
              {t.flag} {t.name} ({t.country})
            </option>
          ))}
        </select>

        <button
          onClick={handleNewRace}
          title="Reset session and digital twin"
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-all active:scale-95"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Reset</span>
        </button>
      </div>
    </div>
  );
};
