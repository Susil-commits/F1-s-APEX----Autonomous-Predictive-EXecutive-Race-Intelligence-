import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { useRaceStore } from '../store/raceStore';
import { TrendingDown, Gauge } from 'lucide-react';

export const TelemetryCharts: React.FC = () => {
  const { telemetryHistory, raceState } = useRaceStore();

  const playerCar = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col h-full border border-apex-border shadow-2xl">
      {/* Title */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <TrendingDown className="w-4 h-4 text-apex-cyan" />
          <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-200">
            Live Telemetry & Degradation Curve
          </h3>
        </div>
        {playerCar && (
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Current Wear:</span>
            <span
              className={`font-bold ${
                playerCar.tyre_wear_pct > 75
                  ? 'text-rose-400 font-extrabold'
                  : playerCar.tyre_wear_pct > 50
                  ? 'text-amber-400'
                  : 'text-emerald-400'
              }`}
            >
              {playerCar.tyre_wear_pct.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Chart 1: Tyre Degradation vs Cliff */}
      <div className="flex-1 flex flex-col min-h-[140px] mb-2">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-0.5 bg-cyan-400 inline-block" /> Tyre Wear %
          </span>
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2 h-0.5 bg-rose-500 inline-block" /> Cliff Threshold (78%)
          </span>
        </div>

        <div className="w-full flex-1 min-h-[110px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={telemetryHistory} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
              <XAxis dataKey="lap" stroke="#475569" fontSize={10} tickLine={false} />
              <YAxis domain={[0, 100]} stroke="#475569" fontSize={10} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: '#f8fafc',
                }}
              />
              <ReferenceLine y={78} stroke="#ef4444" strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="playerTyreWear"
                name="Tyre Wear (%)"
                stroke="#00f0ff"
                strokeWidth={2.5}
                dot={{ r: 2, fill: '#00f0ff' }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: Lap Time Delta Pace vs Leader */}
      <div className="flex-1 flex flex-col min-h-[140px] pt-2 border-t border-slate-800/80">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
          <span className="flex items-center gap-1.5 text-cyan-300">
            <span className="w-2 h-0.5 bg-cyan-400 inline-block" /> APEX Pace (s)
          </span>
          <span className="flex items-center gap-1.5 text-yellow-300">
            <span className="w-2 h-0.5 bg-yellow-400 inline-block" /> P1 Leader Pace
          </span>
        </div>

        <div className="w-full flex-1 min-h-[110px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={telemetryHistory} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
              <XAxis dataKey="lap" stroke="#475569" fontSize={10} tickLine={false} />
              <YAxis domain={['auto', 'auto']} stroke="#475569" fontSize={10} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: '#f8fafc',
                }}
              />
              <Line
                type="monotone"
                dataKey="playerLapTime"
                name="APEX Lap Time"
                stroke="#00f0ff"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="leaderLapTime"
                name="Leader Lap Time"
                stroke="#facc15"
                strokeWidth={1.5}
                strokeDasharray="2 2"
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
