import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Thermometer, Droplet, Wind, ShieldAlert, Sparkles, Zap, Heart, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

export const DriverCoolingSuitCockpit: React.FC = () => {
  const { raceState } = useRaceStore();

  const [coolingPumpActive, setCoolingPumpActive] = useState<boolean>(true);
  const [coolingFlowRateLpm, setCoolingFlowRateLpm] = useState<number>(1.2);
  const [hydrationDrankMl, setHydrationDrankMl] = useState<number>(350);

  // Thermal metrics
  const cockpitAmbientTempC = 56.4; // Extreme Qatar/Singapore ambient
  const coreBodyTempC = coolingPumpActive ? 37.8 : 39.4; // Regulated vs critical hyperthermia
  const hydrationRemainingMl = Math.max(0, 1000 - hydrationDrankMl);

  const handleDispenseDrink = () => {
    setHydrationDrankMl((prev) => Math.min(1000, prev + 100));
    confetti({ particleCount: 30, spread: 45 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Thermometer className="w-5 h-5 text-rose-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              DRIVER THERMAL HEATMAP & LIQUID COOLING SUIT COCKPIT
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Chilled circulatory vest pump telemetry, cockpit hyperthermia defense & in-helmet hydration dispenser
            </span>
          </div>
        </div>

        {/* Pump Status */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCoolingPumpActive(!coolingPumpActive)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-mono font-bold transition-all active:scale-95 flex items-center gap-1.5 ${
              coolingPumpActive
                ? 'bg-cyan-500 text-black border-cyan-400 shadow-md shadow-cyan-500/20'
                : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{coolingPumpActive ? 'CHILLED VEST PUMP: ACTIVE' : 'PUMP: OFF (HYPERTHERMIA RISK)'}</span>
          </button>
        </div>
      </div>

      {/* Primary Thermal KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">DRIVER CORE BODY TEMP</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black ${coreBodyTempC > 38.5 ? 'text-rose-400 animate-pulse' : 'text-emerald-400'}`}>
              {coreBodyTempC.toFixed(1)}°C
            </span>
          </div>
          <span className="text-[10px] text-slate-400">{coreBodyTempC > 38.5 ? 'Hyperthermia Warning' : 'Homeostasis Normal'}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">COCKPIT AMBIENT HEAT</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-rose-500">{cockpitAmbientTempC}°C</span>
          </div>
          <span className="text-[10px] text-slate-400">Radiator / Monocoque Transfer</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">VEST CHILLED FLOW RATE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">
              {coolingPumpActive ? coolingFlowRateLpm.toFixed(1) : '0.0'}
            </span>
            <span className="text-xs text-slate-400">L/MIN</span>
          </div>
          <span className="text-[10px] text-slate-400">Target Temp: 14°C Coolant</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">HYDRATION DRINK REMAINING</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-amber-400">{hydrationRemainingMl}</span>
            <span className="text-xs text-slate-400">ML</span>
          </div>
          <span className="text-[10px] text-slate-400">Electrolyte Mix Bottle</span>
        </div>
      </div>

      {/* Interactive Controls & Thermal Avatar Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Controls (Left 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            MICRO-CLIMATE THERMAL CONTROLS
          </span>

          {/* Flow Rate Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Vest Circulation Flow Rate:</span>
              <span className="font-bold text-apex-cyan">{coolingFlowRateLpm} L/min</span>
            </div>
            <input
              type="range"
              min={0.5}
              max={2.5}
              step={0.1}
              value={coolingFlowRateLpm}
              onChange={(e) => setCoolingFlowRateLpm(Number(e.target.value))}
              disabled={!coolingPumpActive}
              className="accent-cyan-400 cursor-pointer disabled:opacity-30"
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
            <div className="flex flex-col">
              <span className="font-bold text-white">In-Helmet Drink Straw:</span>
              <span className="text-[10px] text-slate-400">Dispense 100ml Isotonic Electrolytes</span>
            </div>
            <button
              onClick={handleDispenseDrink}
              disabled={hydrationRemainingMl === 0}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 disabled:opacity-30 text-black font-bold transition-all active:scale-95"
            >
              <Droplet className="w-3.5 h-3.5" />
              <span>Dispense Drink</span>
            </button>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>FIA Heat Protocol:</strong> When ambient cockpit temperature exceeds 55°C, liquid cooling suits and active monocoque air scoops are mandatory to prevent cognitive fatigue.
          </div>
        </div>

        {/* Driver Thermal Avatar Diagram (Right 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            DRIVER BODY THERMAL GRADIENT SCAN
          </span>

          <div className="relative w-full h-44 rounded-lg overflow-hidden bg-black/80 border border-slate-800 p-3 flex items-center justify-center">
            <div className="flex items-center gap-8">
              {/* Silhouette Body Diagram */}
              <div className="flex flex-col items-center gap-1 font-mono">
                <div className="w-10 h-10 rounded-full bg-amber-500/80 border border-amber-300 flex items-center justify-center text-[10px] font-bold text-black">
                  37.4°
                </div>
                <div className={`w-16 h-20 rounded-xl flex items-center justify-center text-xs font-bold text-black border ${coolingPumpActive ? 'bg-cyan-400 border-cyan-200 shadow-lg shadow-cyan-400/40' : 'bg-rose-500 border-rose-300 shadow-lg shadow-rose-500/40'}`}>
                  {coolingPumpActive ? '18°C VEST' : '39°C HOT'}
                </div>
                <div className="w-12 h-10 rounded-b-xl bg-amber-500/70 border border-amber-300 flex items-center justify-center text-[10px] font-bold text-black">
                  38.0°
                </div>
              </div>

              {/* Legend */}
              <div className="flex flex-col gap-1.5 text-[11px]">
                <span className="text-cyan-400 font-bold">■ Chilled Water Circuit (14°C)</span>
                <span className="text-amber-400 font-bold">■ Core Torso Normal (37.8°C)</span>
                <span className="text-rose-500 font-bold">■ High Heat Monocoque (56.4°C)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
