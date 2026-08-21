import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Activity, Gauge, Zap, CheckCircle2, RotateCw, Sparkles } from 'lucide-react';
import confetti from 'canvas-confetti';

interface GearRatio {
  gear: number;
  ratio: number;
  maxKmh: number;
}

const GEAR_RATIOS: GearRatio[] = [
  { gear: 1, ratio: 2.85, maxKmh: 115 },
  { gear: 2, ratio: 2.20, maxKmh: 152 },
  { gear: 3, ratio: 1.75, maxKmh: 195 },
  { gear: 4, ratio: 1.42, maxKmh: 238 },
  { gear: 5, ratio: 1.18, maxKmh: 280 },
  { gear: 6, ratio: 1.00, maxKmh: 315 },
  { gear: 7, ratio: 0.86, maxKmh: 342 },
  { gear: 8, ratio: 0.74, maxKmh: 368 },
];

export const GearboxShiftDynamicsLab: React.FC = () => {
  const [currentGear, setCurrentGear] = useState<number>(6);
  const [shiftActuatorPressureBar, setShiftActuatorPressureBar] = useState<number>(45.0);
  const [gearboxOilTempC, setGearboxOilTempC] = useState<number>(114.5);

  const handleUpshift = () => {
    setCurrentGear((prev) => Math.min(8, prev + 1));
    confetti({ particleCount: 30, spread: 45 });
  };

  const handleDownshift = () => {
    setCurrentGear((prev) => Math.max(1, prev - 1));
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <RotateCw className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              SEAMLESS SHIFT GEARBOX BARREL & DOG RING ENGAGEMENT LAB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Zero-torque-loss seamless barrel rotation (2ms shift), pneumatic shift rail (45 bar) & 8-speed gear ratios
            </span>
          </div>
        </div>

        {/* Gear Controls */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={handleDownshift}
            disabled={currentGear === 1}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 disabled:opacity-30 text-white font-bold transition-all active:scale-95"
          >
            Downshift (Paddle L)
          </button>
          <span className="px-3 py-1.5 rounded-xl bg-cyan-500 text-black font-black text-sm">
            GEAR {currentGear}
          </span>
          <button
            onClick={handleUpshift}
            disabled={currentGear === 8}
            className="px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-30 text-black font-bold transition-all active:scale-95"
          >
            Upshift (Paddle R)
          </button>
        </div>
      </div>

      {/* Primary Gearbox KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">TORQUE HANDOVER TIME</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-emerald-400">0.002</span>
            <span className="text-xs text-slate-400">SEC (2 MS)</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-bold">100% Uninterrupted Drive</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">PNEUMATIC RAIL PRESSURE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">{shiftActuatorPressureBar}</span>
            <span className="text-xs text-slate-400">BAR</span>
          </div>
          <span className="text-[10px] text-slate-400">Actuator Shift Sled</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">GEARBOX OIL TEMP</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-amber-400">{gearboxOilTempC}°C</span>
          </div>
          <span className="text-[10px] text-slate-400">Target Range: 105 - 125°C</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">DOG RING ENGAGEMENT</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-purple-400">97.8%</span>
          </div>
          <span className="text-[10px] text-slate-400">Chamfer Face Health</span>
        </div>
      </div>

      {/* 8-Speed Ratio Ladder & Shift Diagram */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2.5 font-mono text-xs">
        {GEAR_RATIOS.map((g) => (
          <div
            key={g.gear}
            className={`p-3 rounded-xl border flex flex-col justify-between gap-2 transition-all ${
              currentGear === g.gear
                ? 'bg-slate-900 border-cyan-400 shadow-md shadow-cyan-500/20 scale-[1.02]'
                : 'bg-slate-900/50 border-slate-800'
            }`}
          >
            <div className="flex justify-between items-center">
              <span className="font-bold text-white">G{g.gear}</span>
              {currentGear === g.gear && <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />}
            </div>

            <div className="flex flex-col text-[11px]">
              <span className="text-slate-400">Ratio: <strong className="text-white">{g.ratio.toFixed(2)}</strong></span>
              <span className="text-slate-400">Max: <strong className="text-amber-400">{g.maxKmh} km/h</strong></span>
            </div>

            <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                style={{ width: `${(g.maxKmh / 370) * 100}%` }}
                className={`h-full ${currentGear === g.gear ? 'bg-cyan-400' : 'bg-slate-700'}`}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
