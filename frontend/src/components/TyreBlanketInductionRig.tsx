import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Flame, Thermometer, Gauge, Zap, CheckCircle2, Sparkles } from 'lucide-react';
import confetti from 'canvas-confetti';

interface BlanketWheel {
  id: string;
  name: string;
  treadTempC: number;
  rimTempC: number;
  coldPressurePsi: number;
  hotPressurePsi: number;
  heatingActive: boolean;
}

const INITIAL_BLANKETS: BlanketWheel[] = [
  { id: 'FL', name: 'Front Left', treadTempC: 98.4, rimTempC: 68.2, coldPressurePsi: 21.5, hotPressurePsi: 24.8, heatingActive: true },
  { id: 'FR', name: 'Front Right', treadTempC: 99.1, rimTempC: 69.0, coldPressurePsi: 21.5, hotPressurePsi: 24.9, heatingActive: true },
  { id: 'RL', name: 'Rear Left', treadTempC: 97.5, rimTempC: 67.4, coldPressurePsi: 20.0, hotPressurePsi: 22.4, heatingActive: true },
  { id: 'RR', name: 'Rear Right', treadTempC: 98.0, rimTempC: 68.1, coldPressurePsi: 20.0, hotPressurePsi: 22.6, heatingActive: true },
];

export const TyreBlanketInductionRig: React.FC = () => {
  const [blankets, setBlankets] = useState<BlanketWheel[]>(INITIAL_BLANKETS);
  const [targetTreadTempC, setTargetTreadTempC] = useState<number>(100);

  const handleBoostHeat = () => {
    setBlankets((prev) =>
      prev.map((b) => ({ ...b, treadTempC: targetTreadTempC, rimTempC: 70.0 }))
    );
    confetti({ particleCount: 40, spread: 50 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-amber-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              TYRE BLANKET INDUCTION HEATING & COLD PRESSURE RIG
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              4-corner electromagnetic induction warming (100°C tread / 70°C rim) & Pirelli cold starting pressure optimizer
            </span>
          </div>
        </div>

        <button
          onClick={handleBoostHeat}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-amber-500/20"
        >
          <Sparkles className="w-4 h-4" />
          <span>Trigger 100°C Heat Boost</span>
        </button>
      </div>

      {/* Primary Blanket KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">TARGET TREAD HEAT</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-rose-400">{targetTreadTempC}°C</span>
          </div>
          <span className="text-[10px] text-slate-400">FIA Legal Max: 100°C</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">WHEEL RIM HEAT SOAK</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-amber-400">68.5°C</span>
          </div>
          <span className="text-[10px] text-slate-400">Magnesium Core Soaking</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">FRONT STARTING COLD PSI</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">21.5</span>
            <span className="text-xs text-slate-400">PSI</span>
          </div>
          <span className="text-[10px] text-slate-400">Pirelli Mandatory Minimum</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">REAR STARTING COLD PSI</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-purple-400">20.0</span>
            <span className="text-xs text-slate-400">PSI</span>
          </div>
          <span className="text-[10px] text-slate-400">Pirelli Mandatory Minimum</span>
        </div>
      </div>

      {/* 4-Corner Wheel Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
        {blankets.map((wheel) => (
          <div
            key={wheel.id}
            className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-white text-sm">{wheel.name} [{wheel.id}]</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                INDUCTION ON
              </span>
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Tread Temperature:</span>
                <strong className="text-rose-400">{wheel.treadTempC.toFixed(1)}°C</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Rim Temperature:</span>
                <strong className="text-amber-400">{wheel.rimTempC.toFixed(1)}°C</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Starting Cold PSI:</span>
                <strong className="text-apex-cyan">{wheel.coldPressurePsi} psi</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Predicted Hot PSI:</span>
                <strong className="text-emerald-400">{wheel.hotPressurePsi} psi</strong>
              </div>
            </div>

            <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                style={{ width: `${(wheel.treadTempC / 100) * 100}%` }}
                className="h-full bg-gradient-to-r from-amber-500 to-rose-500"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
