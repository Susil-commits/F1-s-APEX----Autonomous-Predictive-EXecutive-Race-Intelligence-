import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { CloudRain, Sun, Droplets, Wind, Thermometer, Radio } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts';

export const WeatherDopplerRadar: React.FC = () => {
  const { raceState } = useRaceStore();

  if (!raceState) return null;

  const { weather, current_lap, total_laps, track } = raceState;
  const isRain = weather.condition === 'WET' || weather.condition === 'DAMP';

  // Generate 10-lap forward forecast data
  const forecastData = Array.from({ length: 10 }).map((_, idx) => {
    const forecastLap = current_lap + idx + 1;
    let rainProb = weather.rain_probability_next_5_laps;
    if (weather.condition === 'WET') {
      rainProb = Math.max(0.1, 0.85 - idx * 0.08);
    } else if (weather.condition === 'DAMP') {
      rainProb = Math.max(0.05, 0.45 - idx * 0.04);
    } else {
      rainProb = Math.min(0.95, track.rain_probability_base + (idx > 4 ? 0.15 : 0));
    }

    return {
      lap: `Lap ${forecastLap}`,
      lapNum: forecastLap,
      rainProb: Math.round(rainProb * 100),
      interThreshold: 35,
      wetThreshold: 70,
    };
  });

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <CloudRain className="w-4 h-4 text-cyan-400 animate-pulse" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Doppler Weather Radar & Rain Horizon
          </h3>
        </div>
        <span className="text-[10px] text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/50 font-bold">
          10-Lap Markov Forecast
        </span>
      </div>

      {/* Weather Stats Bar */}
      <div className="grid grid-cols-3 gap-2 text-center mb-3">
        <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[9px] uppercase font-sans text-slate-500 block font-semibold">
            Track State
          </span>
          <span
            className={`text-sm font-black uppercase ${
              isRain ? 'text-cyan-400 glow-cyan' : 'text-amber-400'
            }`}
          >
            {weather.condition}
          </span>
        </div>

        <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[9px] uppercase font-sans text-slate-500 block font-semibold">
            Track Temp
          </span>
          <span className="text-sm font-black text-amber-300">
            {weather.track_temp_c.toFixed(1)}°C
          </span>
        </div>

        <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[9px] uppercase font-sans text-slate-500 block font-semibold">
            Current Rain
          </span>
          <span className="text-sm font-black text-cyan-400">
            {(weather.rain_intensity * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* 10-Lap Rain Probability Chart */}
      <div className="w-full h-36 mb-2">
        <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1 font-sans">
          <span>Precipitation Risk Probability (%)</span>
          <span className="text-cyan-400 font-mono">Inter Crossover: 35%</span>
        </div>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={forecastData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="lap" stroke="#475569" fontSize={9} tickLine={false} />
            <YAxis domain={[0, 100]} stroke="#475569" fontSize={9} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '6px',
                fontSize: '11px',
                color: '#f8fafc',
              }}
            />
            <ReferenceLine y={35} stroke="#10b981" strokeDasharray="2 2" />
            <ReferenceLine y={70} stroke="#3b82f6" strokeDasharray="2 2" />
            <Area
              type="monotone"
              dataKey="rainProb"
              name="Rain Risk (%)"
              stroke="#00f0ff"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#rainGrad)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Radar Advisory */}
      <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] font-sans text-slate-300 flex items-center justify-between">
        <span>Strategic Tyre Advisory:</span>
        <span className="font-bold text-cyan-400 font-mono">
          {weather.condition === 'WET'
            ? 'Box for INTERMEDIATE / WET tyres'
            : weather.rain_probability_next_5_laps > 0.4
            ? 'Prepare Intermediates in pit lane'
            : 'Nominal Slick Dry Compounds (S/M/H)'}
        </span>
      </div>
    </div>
  );
};
