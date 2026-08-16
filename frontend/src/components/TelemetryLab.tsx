import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from 'recharts';
import { useRaceStore } from '../store/raceStore';
import { TrendingDown, Gauge, Flame, Fuel, Zap, Activity, Layers } from 'lucide-react';

export const TelemetryLab: React.FC = () => {
  const { telemetryHistory, raceState } = useRaceStore();
  const [selectedChart, setSelectedChart] = useState<'wear' | 'pace' | 'thermals' | 'fuel'>('wear');

  const playerCar = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Top Telemetry Header & Metric Switcher */}
      <div className="glass-panel rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 border border-apex-border shadow-2xl">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-black shadow-lg shadow-cyan-500/20">
            <Gauge className="w-4 h-4 text-black stroke-[2.5]" />
          </div>
          <div>
            <h2 className="text-sm font-black uppercase tracking-wider text-white">
              Telemetry & Physics Laboratory
            </h2>
            <p className="text-xs text-slate-400">
              High-frequency multi-channel telemetry streams & thermal degradation curves
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setSelectedChart('wear')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded transition-all ${
              selectedChart === 'wear'
                ? 'bg-cyan-500 text-black font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <TrendingDown className="w-3.5 h-3.5" />
            <span>Tyre Degradation</span>
          </button>

          <button
            onClick={() => setSelectedChart('pace')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded transition-all ${
              selectedChart === 'pace'
                ? 'bg-cyan-500 text-black font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Pace Delta vs P1</span>
          </button>

          <button
            onClick={() => setSelectedChart('thermals')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded transition-all ${
              selectedChart === 'thermals'
                ? 'bg-cyan-500 text-black font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>4-Wheel Thermals</span>
          </button>

          <button
            onClick={() => setSelectedChart('fuel')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded transition-all ${
              selectedChart === 'fuel'
                ? 'bg-cyan-500 text-black font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Fuel className="w-3.5 h-3.5" />
            <span>Fuel Mass Burn</span>
          </button>
        </div>
      </div>

      {/* Main Big Chart Area */}
      <div className="glass-panel rounded-xl p-5 border border-apex-border shadow-2xl min-h-[380px] flex flex-col">
        {selectedChart === 'wear' && (
          <div className="flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5 text-cyan-300 font-bold">
                  <span className="w-3 h-0.5 bg-cyan-400" /> APEX Tyre Wear %
                </span>
                <span className="flex items-center gap-1.5 text-rose-400 font-bold">
                  <span className="w-3 h-0.5 bg-rose-500" /> Cliff Threshold (78%)
                </span>
              </div>
              <span className="text-slate-400">Non-linear exponential wear model</span>
            </div>

            <div className="w-full flex-1 min-h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={telemetryHistory} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="wearGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="lap" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#475569" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f8fafc',
                    }}
                  />
                  <ReferenceLine y={78} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'CLIFF 78%', fill: '#ef4444', fontSize: 10 }} />
                  <Area
                    type="monotone"
                    dataKey="playerTyreWear"
                    name="Tyre Wear (%)"
                    stroke="#00f0ff"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#wearGrad)"
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {selectedChart === 'pace' && (
          <div className="flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5 text-cyan-300 font-bold">
                  <span className="w-3 h-0.5 bg-cyan-400" /> APEX Lap Time (s)
                </span>
                <span className="flex items-center gap-1.5 text-yellow-400 font-bold">
                  <span className="w-3 h-0.5 bg-yellow-400" /> Leader Lap Time (s)
                </span>
              </div>
              <span className="text-slate-400">Pace differential per lap</span>
            </div>

            <div className="w-full flex-1 min-h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryHistory} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
                  <XAxis dataKey="lap" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis domain={['auto', 'auto']} stroke="#475569" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f8fafc',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="playerLapTime"
                    name="APEX Lap Time"
                    stroke="#00f0ff"
                    strokeWidth={2.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="leaderLapTime"
                    name="Leader Lap Time"
                    stroke="#facc15"
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {selectedChart === 'thermals' && (
          <div className="flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <div className="flex items-center gap-4">
                <span className="text-cyan-400 font-bold">FL Temp (°C)</span>
                <span className="text-blue-400 font-bold">FR Temp (°C)</span>
                <span className="text-amber-400 font-bold">RL Temp (°C)</span>
                <span className="text-rose-400 font-bold">RR Temp (°C)</span>
              </div>
              <span className="text-slate-400">Target Thermal Window: 90°C - 110°C</span>
            </div>

            <div className="w-full flex-1 min-h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryHistory} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
                  <XAxis dataKey="lap" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis domain={[75, 125]} stroke="#475569" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f8fafc',
                    }}
                  />
                  <ReferenceLine y={105} stroke="#eab308" strokeDasharray="2 2" />
                  <Line type="monotone" dataKey="tyreTempFL" name="FL Temp (°C)" stroke="#00f0ff" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="tyreTempFR" name="FR Temp (°C)" stroke="#60a5fa" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="tyreTempRL" name="RL Temp (°C)" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="tyreTempRR" name="RR Temp (°C)" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {selectedChart === 'fuel' && (
          <div className="flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3 text-xs font-mono">
              <span className="text-amber-400 font-bold">Fuel Mass Remaining (kg)</span>
              <span className="text-slate-400">Nominal 105kg starting fuel allocation</span>
            </div>

            <div className="w-full flex-1 min-h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryHistory} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
                  <XAxis dataKey="lap" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 110]} stroke="#475569" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f8fafc',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="fuelRemainingKg"
                    name="Fuel (kg)"
                    stroke="#f59e0b"
                    strokeWidth={2.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        <div className="glass-panel rounded-xl p-4 border border-apex-border">
          <span className="text-[10px] uppercase font-sans font-bold text-slate-400 block mb-1">
            Tyre Degradation Rate
          </span>
          <span className="text-xl font-black text-apex-cyan">
            {playerCar ? `${(playerCar.tyre_wear_pct / Math.max(1, playerCar.tyre_age_laps)).toFixed(2)}% / lap` : '--'}
          </span>
          <p className="text-[11px] text-slate-500 mt-1">
            Current compound: {playerCar?.tyre_compound}
          </p>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-apex-border">
          <span className="text-[10px] uppercase font-sans font-bold text-slate-400 block mb-1">
            Estimated Cliff Arrival
          </span>
          <span className="text-xl font-black text-amber-400">
            {playerCar && playerCar.tyre_wear_pct < 78
              ? `Lap ${raceState ? raceState.current_lap + Math.ceil((78 - playerCar.tyre_wear_pct) / 2.6) : '--'}`
              : 'CLIFF REACHED'}
          </span>
          <p className="text-[11px] text-slate-500 mt-1">
            Critical threshold at 78% tyre wear
          </p>
        </div>

        <div className="glass-panel rounded-xl p-4 border border-apex-border">
          <span className="text-[10px] uppercase font-sans font-bold text-slate-400 block mb-1">
            Fuel Delta to Target
          </span>
          <span className="text-xl font-black text-emerald-400">+0.32 kg</span>
          <p className="text-[11px] text-slate-500 mt-1">
            Lift and coast delta nominal
          </p>
        </div>
      </div>

      {/* 4-Corner Live Thermal & Carcass Matrix */}
      <div className="glass-panel rounded-xl p-4 border border-apex-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold uppercase font-mono text-white">4-Corner Thermal & Carcass Gradient</span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">Real-Time Core vs Surface Temp</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
          {(() => {
            const latest = telemetryHistory[telemetryHistory.length - 1];
            const baseWear = playerCar?.tyre_wear_pct || 22;
            const corners = [
              { corner: 'Front Left (FL)', temp: latest?.tyreTempFL || 102.4, wear: baseWear * 1.05, color: '#00f0ff' },
              { corner: 'Front Right (FR)', temp: latest?.tyreTempFR || 104.1, wear: baseWear * 1.08, color: '#60a5fa' },
              { corner: 'Rear Left (RL)', temp: latest?.tyreTempRL || 98.6, wear: baseWear * 0.95, color: '#f59e0b' },
              { corner: 'Rear Right (RR)', temp: latest?.tyreTempRR || 99.2, wear: baseWear * 0.96, color: '#ef4444' },
            ];
            return corners.map((t) => (
              <div key={t.corner} className="bg-slate-950/80 p-3 rounded-lg border border-slate-800 flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-sans font-bold">{t.corner}</span>
                <div className="flex items-baseline justify-between my-1">
                  <span className="text-lg font-black" style={{ color: t.color }}>{t.temp.toFixed(1)}°C</span>
                  <span className="text-[10px] text-slate-400">{t.wear.toFixed(0)}% wear</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, t.wear)}%`,
                      backgroundColor: t.wear > 78 ? '#ef4444' : t.wear > 50 ? '#f59e0b' : '#10b981',
                    }}
                  />
                </div>
              </div>
            ));
          })()}
        </div>
      </div>
    </div>
  );
};
