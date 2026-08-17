import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { CloudRain, Droplets, Sun, Wind, Compass, AlertCircle } from 'lucide-react';
import { WeatherDopplerRadar } from './WeatherDopplerRadar';

export const WeatherIntelligenceView: React.FC = () => {
  const { raceState } = useRaceStore();
  if (!raceState) return null;

  const { weather, track } = raceState;
  const isWet = weather.condition === 'WET';
  const isDamp = weather.condition === 'DAMP';

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
            <CloudRain className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">Dynamic Weather & Track Grip Intelligence</h2>
            <p className="text-xs text-slate-400">Micro-climate radar and dynamic compound crossover forecasting</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 text-xs rounded border font-bold ${isWet ? 'bg-blue-500/20 text-blue-300 border-blue-500/40' : isDamp ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'}`}>
            CONDITION: {weather.condition}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><Droplets className="w-3.5 h-3.5 text-blue-400" /> TRACK WETNESS INDEX</span>
          <span className="text-xl font-bold text-cyan-400 font-sans">
            {((weather.track_wetness || (isWet ? 0.85 : isDamp ? 0.45 : 0.05)) * 100).toFixed(0)}%
          </span>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
            <div className="bg-gradient-to-r from-cyan-400 to-blue-600 h-full rounded-full" style={{ width: `${(weather.track_wetness || (isWet ? 0.85 : isDamp ? 0.45 : 0.05)) * 100}%` }} />
          </div>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><Sun className="w-3.5 h-3.5 text-amber-400" /> TRACK TEMPERATURE</span>
          <span className="text-xl font-bold text-amber-400 font-sans">{(weather.track_temp_c || 35.0).toFixed(1)}°C</span>
          <span className="text-[10px] text-slate-500">Air: {(weather.air_temp_c || 22.0).toFixed(1)}°C</span>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><Wind className="w-3.5 h-3.5 text-slate-400" /> 5-LAP RAIN FORECAST</span>
          <span className="text-xl font-bold text-purple-400 font-sans">
            {(weather.rain_probability_next_5_laps * 100).toFixed(0)}%
          </span>
          <span className="text-[10px] text-slate-500">Peak Precipitation</span>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col gap-1">
          <span className="text-[11px] text-slate-400 flex items-center gap-1"><Compass className="w-3.5 h-3.5 text-emerald-400" /> GRIP MULTIPLIER</span>
          <span className="text-xl font-bold text-emerald-400 font-sans">
            {(weather.grip_multiplier || (isWet ? 0.72 : isDamp ? 0.88 : 1.0)).toFixed(2)}x
          </span>
          <span className="text-[10px] text-slate-500">Effective Surface Friction</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800">
          <h3 className="text-xs font-bold text-slate-300 font-sans mb-3">Live Doppler Precipitation Radar</h3>
          <WeatherDopplerRadar />
        </div>

        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-300 font-sans">Compound Crossover Matrix</h3>
          <div className="flex flex-col gap-2.5 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-200">Slick (Soft/Med/Hard)</span>
                <p className="text-[11px] text-slate-400">Optimal when track wetness &lt; 20%</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${!isWet && !isDamp ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                {!isWet && !isDamp ? 'OPTIMAL' : 'SLOWER'}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-emerald-400">Intermediate (Green)</span>
                <p className="text-[11px] text-slate-400">Crossover active between 20% - 60% wetness</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${isDamp ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                {isDamp ? 'OPTIMAL' : 'STANDBY'}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-blue-400">Full Wet (Blue)</span>
                <p className="text-[11px] text-slate-400">Optimal when standing water &gt; 60%</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${isWet ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-800 text-slate-500'}`}>
                {isWet ? 'OPTIMAL' : 'STANDBY'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
