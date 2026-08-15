import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Swords, Wind, Zap, Shield, AlertTriangle, Crosshair, ArrowRight } from 'lucide-react';
import { CarState } from '../types/race';

export const DriverBattleRadar: React.FC = () => {
  const { raceState, selectedCarId, setSelectedCarId, setInspectedCar } = useRaceStore();

  if (!raceState) return null;

  const { cars } = raceState;
  const playerCar = cars.find((c) => c.is_player) || cars[0];

  // Find target rival: either selectedCarId or car directly ahead
  let rivalCar = cars.find((c) => c.car_id === selectedCarId && c.car_id !== playerCar.car_id);
  if (!rivalCar) {
    const playerIdx = cars.findIndex((c) => c.car_id === playerCar.car_id);
    rivalCar = playerIdx > 0 ? cars[playerIdx - 1] : cars[1] || cars[0];
  }

  const gapToRival = Math.abs(playerCar.total_race_time_s - rivalCar.total_race_time_s);
  const isAhead = playerCar.position < rivalCar.position;
  const isDrsAvailable = gapToRival <= 1.0;
  const overtakeProbPct = isAhead
    ? Math.max(10, Math.round(90 - gapToRival * 15))
    : isDrsAvailable
    ? Math.min(95, Math.round(82 - gapToRival * 20 + (playerCar.driving_mode === 'PUSH' ? 10 : 0)))
    : Math.max(15, Math.round(45 - gapToRival * 8));

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Swords className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Head-to-Head Battle Radar
          </h3>
        </div>
        <span className="text-[10px] text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/50 font-bold">
          {isAhead ? 'DEFENDING POSITION' : 'ATTACKING RIVAL'}
        </span>
      </div>

      {/* Driver vs Rival Faceoff Card */}
      <div className="grid grid-cols-11 gap-2 items-center p-3 rounded-lg bg-slate-900/90 border border-slate-800 mb-3">
        {/* APEX (Left 5 cols) */}
        <div className="col-span-5 flex flex-col">
          <span className="text-[9.5px] uppercase font-sans font-bold text-apex-cyan">APEX (You)</span>
          <span className="text-sm font-black text-white truncate">P{playerCar.position} #{playerCar.car_number}</span>
          <span className="text-[10px] text-slate-400 font-mono">{playerCar.tyre_compound} ({playerCar.tyre_wear_pct.toFixed(0)}% W)</span>
        </div>

        {/* VS / Gap Center (1 col) */}
        <div className="col-span-1 flex flex-col items-center justify-center">
          <span className="text-[10px] font-black text-amber-400">VS</span>
        </div>

        {/* Rival (Right 5 cols) */}
        <div className="col-span-5 flex flex-col text-right">
          <span className="text-[9.5px] uppercase font-sans font-bold text-slate-400 truncate">
            {rivalCar.driver_name}
          </span>
          <span className="text-sm font-black text-white truncate">P{rivalCar.position} #{rivalCar.car_number}</span>
          <span className="text-[10px] text-slate-400 font-mono">{rivalCar.tyre_compound} ({rivalCar.tyre_wear_pct.toFixed(0)}% W)</span>
        </div>
      </div>

      {/* Key Tactical Battle Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center mb-3">
        {/* Delta Interval */}
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
          <span className="text-[9px] uppercase font-sans text-slate-500 block font-semibold">Gap Interval</span>
          <span className="text-lg font-black text-amber-300">{gapToRival.toFixed(2)}s</span>
        </div>

        {/* DRS Status */}
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
          <span className="text-[9px] uppercase font-sans text-slate-500 block font-semibold">DRS Status</span>
          <span
            className={`text-sm font-black uppercase mt-0.5 block ${
              isDrsAvailable ? 'text-emerald-400 glow-green' : 'text-slate-400'
            }`}
          >
            {isDrsAvailable ? 'ENABLED (<1.0s)' : 'OUT OF RANGE'}
          </span>
        </div>

        {/* Slipstream Speed Delta */}
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
          <span className="text-[9px] uppercase font-sans text-slate-500 block font-semibold">Slipstream</span>
          <span className="text-lg font-black text-cyan-400">
            {isDrsAvailable ? '+14.2 km/h' : '+2.5 km/h'}
          </span>
        </div>

        {/* Overtake Probability */}
        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
          <span className="text-[9px] uppercase font-sans text-slate-500 block font-semibold">Overtake Odds</span>
          <span className="text-lg font-black text-emerald-400">{overtakeProbPct}%</span>
        </div>
      </div>

      {/* AI Tactical Directive */}
      <div className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/80 text-[11px] font-sans flex items-start gap-2 text-slate-300">
        <Crosshair className="w-4 h-4 text-apex-cyan shrink-0 mt-0.5" />
        <p>
          {isAhead
            ? `Defend inside line into heavy braking zone. Rival is ${gapToRival.toFixed(2)}s behind on ${rivalCar.tyre_compound} tyres.`
            : isDrsAvailable
            ? `DRS flap open on main straight! High battery deployment (+ERS) recommended to complete pass into Turn 1.`
            : `Close gap to under 1.00s to unlock DRS slipstream assistance.`}
        </p>
      </div>
    </div>
  );
};
