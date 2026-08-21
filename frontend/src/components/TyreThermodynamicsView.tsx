import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Thermometer, Flame, Gauge, Disc, Activity, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { TyreCompound } from '../types/race';

interface WheelThermalData {
  wheelId: 'FL' | 'FR' | 'RL' | 'RR';
  name: string;
  innerTempC: number;
  centerTempC: number;
  outerTempC: number;
  carcassTempC: number;
  pressurePsi: number;
  wearPct: number;
  blisteringRiskPct: number;
}

export const TyreThermodynamicsView: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  const compound = player?.tyre_compound || 'MEDIUM';
  const wear = player?.tyre_wear_pct || 25.0;
  const isPushing = player?.driving_mode === 'PUSH';

  // Calculate 4-wheel multi-zone thermodynamic profile
  const wheels: WheelThermalData[] = [
    {
      wheelId: 'FL',
      name: 'Front Left',
      innerTempC: Math.round(98 + wear * 0.35 + (isPushing ? 8 : 0)),
      centerTempC: Math.round(94 + wear * 0.30 + (isPushing ? 6 : 0)),
      outerTempC: Math.round(89 + wear * 0.28 + (isPushing ? 5 : 0)),
      carcassTempC: Math.round(102 + wear * 0.40 + (isPushing ? 9 : 0)),
      pressurePsi: Number((23.2 + (wear * 0.02) + (isPushing ? 0.6 : 0)).toFixed(1)),
      wearPct: Math.round(wear * 1.05),
      blisteringRiskPct: Math.min(100, Math.round(wear * 0.8 + (isPushing ? 20 : 5))),
    },
    {
      wheelId: 'FR',
      name: 'Front Right',
      innerTempC: Math.round(104 + wear * 0.38 + (isPushing ? 9 : 0)),
      centerTempC: Math.round(99 + wear * 0.32 + (isPushing ? 7 : 0)),
      outerTempC: Math.round(93 + wear * 0.30 + (isPushing ? 6 : 0)),
      carcassTempC: Math.round(108 + wear * 0.42 + (isPushing ? 10 : 0)),
      pressurePsi: Number((23.6 + (wear * 0.02) + (isPushing ? 0.7 : 0)).toFixed(1)),
      wearPct: Math.round(wear * 1.12),
      blisteringRiskPct: Math.min(100, Math.round(wear * 0.9 + (isPushing ? 25 : 8))),
    },
    {
      wheelId: 'RL',
      name: 'Rear Left',
      innerTempC: Math.round(101 + wear * 0.34 + (isPushing ? 7 : 0)),
      centerTempC: Math.round(96 + wear * 0.31 + (isPushing ? 5 : 0)),
      outerTempC: Math.round(91 + wear * 0.29 + (isPushing ? 4 : 0)),
      carcassTempC: Math.round(105 + wear * 0.38 + (isPushing ? 8 : 0)),
      pressurePsi: Number((21.8 + (wear * 0.02) + (isPushing ? 0.5 : 0)).toFixed(1)),
      wearPct: Math.round(wear * 0.95),
      blisteringRiskPct: Math.min(100, Math.round(wear * 0.7 + (isPushing ? 15 : 4))),
    },
    {
      wheelId: 'RR',
      name: 'Rear Right',
      innerTempC: Math.round(106 + wear * 0.40 + (isPushing ? 10 : 0)),
      centerTempC: Math.round(102 + wear * 0.35 + (isPushing ? 8 : 0)),
      outerTempC: Math.round(96 + wear * 0.32 + (isPushing ? 6 : 0)),
      carcassTempC: Math.round(112 + wear * 0.45 + (isPushing ? 11 : 0)),
      pressurePsi: Number((22.4 + (wear * 0.02) + (isPushing ? 0.8 : 0)).toFixed(1)),
      wearPct: Math.round(wear * 1.18),
      blisteringRiskPct: Math.min(100, Math.round(wear * 1.1 + (isPushing ? 30 : 10))),
    },
  ];

  const getTempColor = (temp: number) => {
    if (temp > 115) return 'text-rose-400 bg-rose-500/20 border-rose-500/50';
    if (temp >= 95) return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/50';
    if (temp >= 85) return 'text-amber-400 bg-amber-500/20 border-amber-500/50';
    return 'text-blue-400 bg-blue-500/20 border-blue-500/50';
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Thermometer className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">MULTI-ZONE CORE & CARCASS TYRE THERMODYNAMICS</span>
            <span className="text-[11px] font-mono text-slate-400">
              Inside/Middle/Outside shoulder surface gradients, bulk carcass core heat & gas pressure
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Active Compound:</span>
          <span
            className={`px-2.5 py-1 rounded-lg font-bold ${
              compound === 'SOFT'
                ? 'bg-rose-500 text-black'
                : compound === 'MEDIUM'
                ? 'bg-amber-500 text-black'
                : compound === 'HARD'
                ? 'bg-slate-200 text-black'
                : 'bg-emerald-500 text-black'
            }`}
          >
            {compound}
          </span>
        </div>
      </div>

      {/* 4-Wheel Thermodynamic Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {wheels.map((w) => (
          <div
            key={w.wheelId}
            className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3"
          >
            {/* Wheel Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Disc className="w-4 h-4 text-slate-400" />
                <span className="font-mono font-bold text-white text-sm">
                  {w.wheelId} • {w.name}
                </span>
              </div>
              <span className="text-xs font-mono font-bold text-slate-300">{w.pressurePsi} PSI</span>
            </div>

            {/* 3-Zone Surface Heatmap (Inner, Center, Outer) */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase">
                3-ZONE TREAD TEMPERATURES
              </span>
              <div className="grid grid-cols-3 gap-1 text-center font-mono text-xs font-bold">
                <div className={`p-2 rounded-lg border flex flex-col ${getTempColor(w.innerTempC)}`}>
                  <span className="text-[9px] text-slate-400 uppercase">INNER</span>
                  <span>{w.innerTempC}°C</span>
                </div>
                <div className={`p-2 rounded-lg border flex flex-col ${getTempColor(w.centerTempC)}`}>
                  <span className="text-[9px] text-slate-400 uppercase">MID</span>
                  <span>{w.centerTempC}°C</span>
                </div>
                <div className={`p-2 rounded-lg border flex flex-col ${getTempColor(w.outerTempC)}`}>
                  <span className="text-[9px] text-slate-400 uppercase">OUTER</span>
                  <span>{w.outerTempC}°C</span>
                </div>
              </div>
            </div>

            {/* Carcass Core Heat & Blistering Risk */}
            <div className="flex flex-col gap-2 pt-1 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">Carcass Core Temp:</span>
                <span className="font-bold text-amber-300">{w.carcassTempC}°C</span>
              </div>

              <div className="flex justify-between">
                <span className="text-slate-400">Surface Wear:</span>
                <span className="font-bold text-white">{w.wearPct}%</span>
              </div>

              <div className="flex flex-col gap-1 mt-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-400">Blistering Risk:</span>
                  <span
                    className={`font-bold ${
                      w.blisteringRiskPct > 40 ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    {w.blisteringRiskPct}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full ${
                      w.blisteringRiskPct > 40
                        ? 'bg-rose-500'
                        : w.blisteringRiskPct > 20
                        ? 'bg-amber-400'
                        : 'bg-emerald-400'
                    }`}
                    style={{ width: `${w.blisteringRiskPct}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Thermodynamic Engineering Reference Bar */}
      <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-300">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span>Optimal Operating Window: <strong>95°C – 110°C</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          <span>Thermal Overheat Threshold: <strong>&gt;118°C (Blistering hazard)</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-amber-400" />
          <span>Cold Grain Window: <strong>&lt;82°C (Understeer sliding)</strong></span>
        </div>
      </div>
    </div>
  );
};
