import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Activity, CloudRain, Sun, ShieldAlert, Flag, Radio, Wifi, WifiOff } from 'lucide-react';

export const Header: React.FC = () => {
  const { raceState, connected, isRunning } = useRaceStore();

  if (!raceState) return null;

  const { track, current_lap, total_laps, race_time_s, weather, safety_car } = raceState;

  // Format race clock
  const minutes = Math.floor(race_time_s / 60);
  const seconds = (race_time_s % 60).toFixed(1);
  const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.padStart(4, '0')}`;

  const isRain = weather.condition === 'WET' || weather.condition === 'DAMP';

  return (
    <header className="w-full glass-panel border-b border-apex-border px-6 py-3 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50">
      {/* Brand & Track Info */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="w-5 h-5 text-black stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-wider text-white">APEX</span>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-cyan-500/20 text-apex-cyan border border-cyan-500/30">
                RACE INTEL
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Digital Twin & Strategy Engine</p>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-700/60 hidden sm:block" />

        {/* Track Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-md bg-slate-800/60 border border-slate-700/50 text-xs">
          <Flag className="w-3.5 h-3.5 text-apex-cyan" />
          <span className="font-semibold text-slate-200">{track.name}</span>
          <span className="text-slate-400">({track.country})</span>
        </div>
      </div>

      {/* Center Live Session Telemetry */}
      <div className="flex items-center gap-4 text-xs font-mono">
        {/* Lap Progress */}
        <div className="flex flex-col items-center px-4 py-1 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-sans">Lap</span>
          <span className="text-base font-bold text-apex-cyan">
            {current_lap} <span className="text-xs text-slate-500">/ {total_laps}</span>
          </span>
        </div>

        {/* Race Time */}
        <div className="flex flex-col items-center px-4 py-1 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-sans">Elapsed</span>
          <span className="text-base font-bold text-slate-200">{formattedTime}</span>
        </div>

        {/* Safety Car Status */}
        {safety_car !== 'NONE' ? (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-yellow-500/20 border border-yellow-500/50 text-apex-yellow animate-pulse font-sans font-bold">
            <ShieldAlert className="w-4 h-4" />
            <span>{safety_car === 'SAFETY_CAR' ? 'SAFETY CAR' : 'VSC ACTIVE'}</span>
          </div>
        ) : (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-sans font-medium text-[11px]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span>TRACK CLEAR</span>
          </div>
        )}

        {/* Weather Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-900/80 border border-slate-800">
          {isRain ? (
            <CloudRain className="w-4 h-4 text-cyan-400 animate-bounce" />
          ) : (
            <Sun className="w-4 h-4 text-amber-400" />
          )}
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-semibold">
              {weather.condition}
            </span>
            <span className="text-[10px] text-slate-300 font-mono">
              Rain: {(weather.rain_intensity * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Right Connection & Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900/60 border border-slate-800 text-[11px]">
          {connected ? (
            <Wifi className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-rose-400" />
          )}
          <span className={connected ? 'text-emerald-400' : 'text-rose-400 font-semibold'}>
            {connected ? 'LIVE TWIN' : 'OFFLINE'}
          </span>
        </div>

        {isRunning && (
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-bold uppercase tracking-wider animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            REC
          </div>
        )}
      </div>
    </header>
  );
};
