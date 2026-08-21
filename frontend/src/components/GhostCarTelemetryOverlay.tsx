import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  AreaChart,
  Area,
} from 'recharts';
import { Activity, Ghost, Zap, Timer, Flame, ChevronRight } from 'lucide-react';

export const GhostCarTelemetryOverlay: React.FC = () => {
  const { raceState } = useRaceStore();
  const [referenceMode, setReferenceMode] = useState<'pole_lap' | 'ai_optimal' | 'personal_best'>('pole_lap');

  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];
  const leader = raceState?.cars[0];

  // Generate distance-based telemetry data along lap (0% to 100%)
  const telemetryData = useMemo(() => {
    const points = [];
    const basePace = raceState?.track?.base_lap_time_s || 88.5;

    for (let pct = 0; pct <= 100; pct += 2) {
      // Speed profile modeling braking zones & straights
      const isBrakingZone = (pct >= 12 && pct <= 18) || (pct >= 42 && pct <= 48) || (pct >= 75 && pct <= 82);
      const isStraight = (pct >= 22 && pct <= 38) || (pct >= 52 && pct <= 70) || (pct >= 86 && pct <= 98);

      let ghostSpeed = 295;
      let playerSpeed = 292;

      if (isBrakingZone) {
        ghostSpeed = 115 + Math.sin(pct) * 15;
        playerSpeed = 108 + Math.cos(pct) * 12;
      } else if (isStraight) {
        ghostSpeed = 328 + (pct % 5);
        playerSpeed = 320 + (pct % 4);
      } else {
        ghostSpeed = 225 + Math.sin(pct * 0.5) * 20;
        playerSpeed = 218 + Math.cos(pct * 0.5) * 18;
      }

      // Delta time accumulation
      const deltaT = Number(((ghostSpeed - playerSpeed) * 0.015 * (pct / 100)).toFixed(3));

      // Throttle & Brake
      const ghostThrottle = isBrakingZone ? 0 : isStraight ? 100 : 75;
      const playerThrottle = isBrakingZone ? 5 : isStraight ? 98 : 68;
      const ghostBrake = isBrakingZone ? 95 : 0;
      const playerBrake = isBrakingZone ? 88 : 0;

      points.push({
        pct: `${pct}%`,
        distancePct: pct,
        playerSpeed: Math.round(playerSpeed),
        ghostSpeed: Math.round(ghostSpeed),
        deltaT,
        playerThrottle,
        ghostThrottle,
        playerBrake,
        ghostBrake,
      });
    }

    return points;
  }, [player?.last_lap_time_s, referenceMode]);

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Ghost className="w-5 h-5 text-purple-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">3D GHOST CAR TELEMETRY & DELTA-V COMPARISON</span>
            <span className="text-[11px] font-mono text-slate-400">
              Live lap speed traces, braking points, apex speeds & continuous time differential ΔT(s)
            </span>
          </div>
        </div>

        {/* Reference Selector */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400 pl-2 pr-1">Ghost Ref:</span>
          <button
            onClick={() => setReferenceMode('pole_lap')}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              referenceMode === 'pole_lap'
                ? 'bg-purple-500 text-black font-bold shadow-sm shadow-purple-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Leader / Pole Lap
          </button>
          <button
            onClick={() => setReferenceMode('ai_optimal')}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              referenceMode === 'ai_optimal'
                ? 'bg-apex-cyan text-black font-bold shadow-sm shadow-cyan-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            AI Ideal Delta
          </button>
          <button
            onClick={() => setReferenceMode('personal_best')}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              referenceMode === 'personal_best'
                ? 'bg-emerald-500 text-black font-bold shadow-sm shadow-emerald-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Session Best
          </button>
        </div>
      </div>

      {/* KPI Delta Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">NET LAP DELTA (ΔT)</span>
          <span className="text-2xl font-black font-mono text-rose-400">+0.384 s</span>
          <span className="text-[10px] font-mono text-slate-400">vs Pole Benchmark</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">APEX SPEED DIFFERENTIAL</span>
          <span className="text-2xl font-black font-mono text-apex-cyan">-6.2 KM/H</span>
          <span className="text-[10px] font-mono text-slate-400">Sector 2 High-speed Esses</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">BRAKING EFFICIENCY</span>
          <span className="text-2xl font-black font-mono text-emerald-400">96.4%</span>
          <span className="text-[10px] font-mono text-slate-400">Late brake threshold: +4m</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">THROTTLE TIME AT 100%</span>
          <span className="text-2xl font-black font-mono text-purple-400">64.8%</span>
          <span className="text-[10px] font-mono text-slate-400">Ghost Ref: 67.2%</span>
        </div>
      </div>

      {/* Speed Trace Graph */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
        <span className="text-xs font-mono text-slate-300 font-bold uppercase">
          SPEED COMPARISON TRACE (KM/H vs LAP DISTANCE %)
        </span>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={telemetryData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="pct" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={[60, 360]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '0.75rem' }}
              />
              <Legend wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Line
                type="monotone"
                dataKey="playerSpeed"
                name="You (APEX Car)"
                stroke="#00f0ff"
                strokeWidth={2.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="ghostSpeed"
                name="Ghost Reference Lap"
                stroke="#c084fc"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Delta-T Time Differential & Throttle Overlay */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Delta T Area Chart */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
          <span className="text-xs font-mono text-slate-300 font-bold uppercase">
            TIME DELTA ΔT ACCUMULATION (SECONDS)
          </span>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetryData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="pct" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '0.75rem' }}
                />
                <Area type="monotone" dataKey="deltaT" name="Time Delta ΔT (s)" stroke="#f43f5e" fill="#f43f5e22" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Throttle & Brake Trace */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
          <span className="text-xs font-mono text-slate-300 font-bold uppercase">
            THROTTLE % & BRAKE PRESSURE OVERLAY
          </span>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="pct" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '0.75rem' }}
                />
                <Line type="monotone" dataKey="playerThrottle" name="Throttle %" stroke="#22c55e" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="playerBrake" name="Brake %" stroke="#ef4444" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
