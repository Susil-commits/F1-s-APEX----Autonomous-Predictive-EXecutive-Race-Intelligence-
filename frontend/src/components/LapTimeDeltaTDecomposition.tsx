import React from 'react';
import { useRaceStore } from '../store/raceStore';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ReferenceLine,
} from 'recharts';
import { Activity, Fuel, Flame, Wind, Zap, Gauge } from 'lucide-react';

export const LapTimeDeltaTDecomposition: React.FC = () => {
  const { raceState } = useRaceStore();

  if (!raceState) return null;

  const playerCar = raceState.cars.find((c) => c.is_player) || raceState.cars[0];
  const baseLap = raceState.track.base_lap_time_s;
  const wear = playerCar.tyre_wear_pct;
  const fuelKg = playerCar.fuel_kg;
  const inDirtyAir = playerCar.gap_to_car_ahead_s > 0 && playerCar.gap_to_car_ahead_s < 1.5;
  const isPush = playerCar.driving_mode === 'PUSH';

  // Physical Delta-T Components (in seconds)
  const fuelDelta = parseFloat(((fuelKg / 105) * 2.8).toFixed(2));
  const tyreDelta = parseFloat(((wear / 100) * 1.8 + (playerCar.tyre_cliff_reached ? 2.8 : 0)).toFixed(2));
  const dirtyAirDelta = inDirtyAir ? 0.45 : 0.0;
  const ersGain = isPush ? -0.45 : -0.25;
  const drsGain = playerCar.gap_to_car_ahead_s > 0 && playerCar.gap_to_car_ahead_s < 1.0 ? -0.65 : 0.0;

  const decompositionData = [
    { component: 'Base Pace', deltaS: baseLap, isBase: true, type: 'base' },
    { component: 'Fuel Mass (+kg)', deltaS: fuelDelta, isBase: false, type: 'loss' },
    { component: 'Tyre Degradation (+s)', deltaS: tyreDelta, isBase: false, type: 'loss' },
    { component: 'Dirty Air Wake (+s)', deltaS: dirtyAirDelta, isBase: false, type: 'loss' },
    { component: 'ERS Deployment (-s)', deltaS: ersGain, isBase: false, type: 'gain' },
    { component: 'DRS Open (-s)', deltaS: drsGain, isBase: false, type: 'gain' },
  ];

  const totalCalculatedLapTime = parseFloat(
    (baseLap + fuelDelta + tyreDelta + dirtyAirDelta + ersGain + drsGain).toFixed(2)
  );

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Activity className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Lap Time Physical &Delta;T Decomposition
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              Deconstructing telemetry pace into fuel weight, tyre degradation, dirty air, and ERS deltas
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[9.5px] uppercase font-sans text-slate-500 block font-semibold">
            Modeled Lap Time
          </span>
          <span className="text-lg font-black text-white">{totalCalculatedLapTime}s</span>
        </div>
      </div>

      {/* Breakdown Bar Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mb-4 text-center">
        <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
          <div className="flex items-center justify-center gap-1 text-[9.5px] uppercase text-slate-500 mb-0.5">
            <Fuel className="w-3 h-3 text-amber-400" /> Fuel Weight
          </div>
          <span className="text-sm font-bold text-amber-400">+{fuelDelta}s</span>
        </div>

        <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
          <div className="flex items-center justify-center gap-1 text-[9.5px] uppercase text-slate-500 mb-0.5">
            <Flame className="w-3 h-3 text-rose-400" /> Tyre Wear
          </div>
          <span className="text-sm font-bold text-rose-400">+{tyreDelta}s</span>
        </div>

        <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
          <div className="flex items-center justify-center gap-1 text-[9.5px] uppercase text-slate-500 mb-0.5">
            <Wind className="w-3 h-3 text-slate-400" /> Dirty Air
          </div>
          <span className="text-sm font-bold text-slate-300">+{dirtyAirDelta}s</span>
        </div>

        <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
          <div className="flex items-center justify-center gap-1 text-[9.5px] uppercase text-slate-500 mb-0.5">
            <Zap className="w-3 h-3 text-emerald-400" /> ERS Hybrid
          </div>
          <span className="text-sm font-bold text-emerald-400">{ersGain}s</span>
        </div>

        <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
          <div className="flex items-center justify-center gap-1 text-[9.5px] uppercase text-slate-500 mb-0.5">
            <Gauge className="w-3 h-3 text-cyan-400" /> DRS Wing
          </div>
          <span className="text-sm font-bold text-cyan-400">{drsGain}s</span>
        </div>

        <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
          <span className="text-[9.5px] uppercase text-slate-500 block mb-0.5">Track Base</span>
          <span className="text-sm font-bold text-slate-200">{baseLap.toFixed(2)}s</span>
        </div>
      </div>

      {/* Waterfall Visualizer */}
      <div className="w-full h-44 bg-slate-950/40 p-2 rounded-lg border border-slate-900">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={decompositionData.filter((d) => !d.isBase)} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="component" stroke="#64748b" fontSize={9.5} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '6px',
                fontSize: '11px',
                color: '#f8fafc',
              }}
            />
            <ReferenceLine y={0} stroke="#475569" />
            <Bar dataKey="deltaS" name="Delta (s)" radius={[4, 4, 0, 0]}>
              {decompositionData
                .filter((d) => !d.isBase)
                .map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.deltaS >= 0 ? '#f59e0b' : '#10b981'}
                  />
                ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
