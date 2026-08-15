import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import { Users, Gauge, Activity, TrendingDown, Zap, Disc } from 'lucide-react';
import { CarState } from '../types/race';

export const DualDriverTelemetryOverlay: React.FC = () => {
  const { raceState } = useRaceStore();
  const [rivalId, setRivalId] = useState<string>('ver_01');

  if (!raceState) return null;

  const { cars, track } = raceState;
  const playerCar = cars.find((c) => c.is_player) || cars[0];
  const rivalCar = cars.find((c) => c.car_id === rivalId) || cars[1] || cars[0];

  // Synthetic 10-point circuit telemetry trace for dual comparison
  const telemetryTraces = [
    { waypoint: 'T1 In', apexSpeed: 285, rivalSpeed: 282, apexThrottle: 100, rivalThrottle: 98 },
    { waypoint: 'T1 Apex', apexSpeed: 110, rivalSpeed: 114, apexThrottle: 35, rivalThrottle: 40 },
    { waypoint: 'T2 Exit', apexSpeed: 210, rivalSpeed: 205, apexThrottle: 90, rivalThrottle: 85 },
    { waypoint: 'Straight 1', apexSpeed: 318, rivalSpeed: 322, apexThrottle: 100, rivalThrottle: 100 },
    { waypoint: 'T4 Apex', apexSpeed: 95, rivalSpeed: 92, apexThrottle: 20, rivalThrottle: 15 },
    { waypoint: 'T6 High-Speed', apexSpeed: 260, rivalSpeed: 255, apexThrottle: 95, rivalThrottle: 90 },
    { waypoint: 'Straight 2', apexSpeed: 325, rivalSpeed: 328, apexThrottle: 100, rivalThrottle: 100 },
    { waypoint: 'Chicane Entry', apexSpeed: 140, rivalSpeed: 138, apexThrottle: 40, rivalThrottle: 45 },
    { waypoint: 'Final Corner', apexSpeed: 185, rivalSpeed: 182, apexThrottle: 85, rivalThrottle: 80 },
    { waypoint: 'Pit Straight', apexSpeed: 310, rivalSpeed: 312, apexThrottle: 100, rivalThrottle: 100 },
  ];

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header & Rival Selector */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Users className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Dual-Driver Comparative Telemetry Overlay
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              Overlaying real-time chassis pace, apex velocities, and tyre wear against rivals
            </p>
          </div>
        </div>

        {/* Rival Selector Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500 font-sans font-bold">Compare vs:</span>
          <select
            value={rivalId}
            onChange={(e) => setRivalId(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-sans font-semibold focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            {cars
              .filter((c) => !c.is_player)
              .map((c) => (
                <option key={c.car_id} value={c.car_id}>
                  P{c.position} #{c.car_number} {c.driver_name} ({c.team_name})
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* Driver Faceoff Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* APEX Car Profile */}
        <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/30 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase font-sans font-black text-apex-cyan">APEX (You)</span>
            <span className="text-xs font-bold text-white">P{playerCar.position}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center text-xs">
            <div className="bg-slate-900/80 p-1.5 rounded">
              <span className="text-[9px] text-slate-500 block">Tyre Wear</span>
              <span className="font-black text-cyan-400">{playerCar.tyre_wear_pct.toFixed(1)}%</span>
            </div>
            <div className="bg-slate-900/80 p-1.5 rounded">
              <span className="text-[9px] text-slate-500 block">Last Lap</span>
              <span className="font-black text-slate-200">
                {playerCar.last_lap_time_s ? `${playerCar.last_lap_time_s.toFixed(2)}s` : '--.--'}
              </span>
            </div>
          </div>
        </div>

        {/* Rival Car Profile */}
        <div className="p-3 rounded-xl bg-yellow-950/20 border border-yellow-500/30 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase font-sans font-black text-yellow-400">
              {rivalCar.driver_name}
            </span>
            <span className="text-xs font-bold text-white">P{rivalCar.position}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center text-xs">
            <div className="bg-slate-900/80 p-1.5 rounded">
              <span className="text-[9px] text-slate-500 block">Tyre Wear</span>
              <span className="font-black text-yellow-400">{rivalCar.tyre_wear_pct.toFixed(1)}%</span>
            </div>
            <div className="bg-slate-900/80 p-1.5 rounded">
              <span className="text-[9px] text-slate-500 block">Last Lap</span>
              <span className="font-black text-slate-200">
                {rivalCar.last_lap_time_s ? `${rivalCar.last_lap_time_s.toFixed(2)}s` : '--.--'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Overlaid Speed Trace Chart */}
      <div className="mb-2">
        <div className="flex items-center justify-between text-[11px] font-sans font-bold text-slate-300 mb-1">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-cyan-300">
              <span className="w-3 h-0.5 bg-cyan-400 inline-block" /> APEX Speed (km/h)
            </span>
            <span className="flex items-center gap-1.5 text-yellow-300">
              <span className="w-3 h-0.5 bg-yellow-400 inline-block" /> {rivalCar.driver_name} Speed (km/h)
            </span>
          </div>
          <span className="text-slate-500">Circuit Waypoint Velocity</span>
        </div>

        <div className="w-full h-48 bg-slate-950/40 p-2 rounded-lg border border-slate-900">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={telemetryTraces} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="waypoint" stroke="#64748b" fontSize={9.5} tickLine={false} />
              <YAxis domain={[80, 350]} stroke="#64748b" fontSize={10} tickLine={false} />
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
                dataKey="apexSpeed"
                name="APEX Speed"
                stroke="#00f0ff"
                strokeWidth={2.5}
                dot={{ r: 2, fill: '#00f0ff' }}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="rivalSpeed"
                name={`${rivalCar.driver_name} Speed`}
                stroke="#facc15"
                strokeWidth={2}
                strokeDasharray="3 3"
                dot={{ r: 2, fill: '#facc15' }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
