import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Flame, Wind, Activity, Gauge, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

export const BrakePyrometryLab: React.FC = () => {
  const [ductOpeningPct, setDuctOpeningPct] = useState<number>(65);

  // Dynamic calculations based on duct opening
  const brakeMetrics = useMemo(() => {
    // Open duct cools brakes but increases aero drag
    const frontRotorTempC = Math.round(1120 - (ductOpeningPct / 100) * 350);
    const rearRotorTempC = Math.round(820 - (ductOpeningPct / 100) * 220);
    const aeroDragPenaltyPts = Number(((ductOpeningPct / 100) * 4.5).toFixed(1));
    const biteFrictionMu = frontRotorTempC > 1050 ? 0.62 : frontRotorTempC < 400 ? 0.38 : 0.58;
    const isOxidizing = frontRotorTempC > 1000;

    return {
      frontRotorTempC,
      rearRotorTempC,
      aeroDragPenaltyPts,
      biteFrictionMu,
      isOxidizing,
    };
  }, [ductOpeningPct]);

  const handleTriggerBrakingTest = () => {
    confetti({ particleCount: 40, spread: 50 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-rose-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              BREMBO CARBON-CARBON BRAKE ROTOR PYROMETRY & DUCT AIRFLOW LAB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              1,480-hole ventilation disc drill pattern, infrared pyrometry (350°C - 1,150°C) & brake duct aero drag tradeoff
            </span>
          </div>
        </div>

        <button
          onClick={handleTriggerBrakingTest}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-rose-600/20"
        >
          <Flame className="w-4 h-4" />
          <span>Simulate Heavy Turn 1 Braking (5.5G)</span>
        </button>
      </div>

      {/* Primary Brake KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">FRONT ROTOR PYROMETRY</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black ${brakeMetrics.isOxidizing ? 'text-rose-500 animate-pulse' : 'text-amber-400'}`}>
              {brakeMetrics.frontRotorTempC}°C
            </span>
          </div>
          <span className="text-[10px] text-slate-400">{brakeMetrics.isOxidizing ? 'Thermal Oxidation Regime' : 'Optimal Braking Window'}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">REAR ROTOR PYROMETRY</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">
              {brakeMetrics.rearRotorTempC}°C
            </span>
          </div>
          <span className="text-[10px] text-slate-400">MGU-K Regen Assist</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">BRAKE BITE FRICTION (µ)</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-emerald-400">{brakeMetrics.biteFrictionMu}</span>
          </div>
          <span className="text-[10px] text-slate-400">Carbon-Carbon Friction</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">DUCT AERO DRAG LOSS</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-purple-400">+{brakeMetrics.aeroDragPenaltyPts}</span>
            <span className="text-xs text-slate-400">PTS</span>
          </div>
          <span className="text-[10px] text-slate-400">Cooling vs Aero Tradeoff</span>
        </div>
      </div>

      {/* Interactive Duct Controls & Disc Glow Shader Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Controls (Left 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            BRAKE COOLING DUCT FLAP ADJUSTMENT
          </span>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Brake Duct Flap Opening:</span>
              <span className="font-bold text-apex-cyan">{ductOpeningPct}% Open</span>
            </div>
            <input
              type="range"
              min={20}
              max={100}
              step={5}
              value={ductOpeningPct}
              onChange={(e) => setDuctOpeningPct(Number(e.target.value))}
              className="accent-cyan-400 cursor-pointer"
            />
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>Brembo Disc Spec:</strong> 355mm diameter carbon-carbon disc with 1,480 chevron radial drill ventilation holes. Caliper hydraulic line pressure: 125 Bar.
          </div>
        </div>

        {/* Disc Glow Visualization (Right 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-2">
          <div className="flex justify-between items-center">
            <span className="font-bold text-slate-300 uppercase">
              CARBON ROTOR THERMAL GLOW EMISSION
            </span>
            <span className="text-rose-500 font-bold">1,480 DRILL HOLES</span>
          </div>

          <div className="relative w-full h-40 rounded-lg overflow-hidden bg-black/90 border border-slate-800 p-3 flex items-center justify-center">
            {/* Glowing Rotor Circle */}
            <div
              style={{
                boxShadow: `0 0 ${Math.max(10, (brakeMetrics.frontRotorTempC - 600) / 15)}px rgba(239, 68, 68, 0.8)`,
              }}
              className="w-28 h-28 rounded-full border-8 border-rose-500/80 flex items-center justify-center relative animate-pulse"
            >
              <div className="w-12 h-12 rounded-full bg-slate-900 border-4 border-slate-700 flex items-center justify-center text-[10px] text-slate-400 font-bold">
                HUB
              </div>
              <span className="absolute text-[11px] font-black text-white drop-shadow-md">
                {brakeMetrics.frontRotorTempC}°C
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
