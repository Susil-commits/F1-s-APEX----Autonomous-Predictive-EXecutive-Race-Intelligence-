import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Droplet, Activity, ShieldCheck, AlertTriangle, Sparkles, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

interface ElementSample {
  symbol: string;
  name: string;
  ppm: number;
  limitPpm: number;
  sourceComponent: string;
  status: 'OPTIMAL' | 'ELEVATED' | 'CRITICAL';
}

const OIL_ELEMENTS: ElementSample[] = [
  {
    symbol: 'Fe',
    name: 'Iron',
    ppm: 22.4,
    limitPpm: 50.0,
    sourceComponent: 'Cylinder Liners & Camshaft Lobes',
    status: 'OPTIMAL',
  },
  {
    symbol: 'Cu',
    name: 'Copper',
    ppm: 11.2,
    limitPpm: 25.0,
    sourceComponent: 'Crankshaft Main & Connecting Rod Bearings',
    status: 'OPTIMAL',
  },
  {
    symbol: 'Ti',
    name: 'Titanium',
    ppm: 4.1,
    limitPpm: 15.0,
    sourceComponent: 'Valvetrain Retainers & Connecting Rods',
    status: 'OPTIMAL',
  },
  {
    symbol: 'Al',
    name: 'Aluminum',
    ppm: 8.5,
    limitPpm: 30.0,
    sourceComponent: 'Piston Crowns & Oil Pump Casing',
    status: 'OPTIMAL',
  },
  {
    symbol: 'Si',
    name: 'Silicon',
    ppm: 7.2,
    limitPpm: 25.0,
    sourceComponent: 'Track Dust & Airbox Filter Ingestion',
    status: 'OPTIMAL',
  },
];

export const OilSpectroscopyForensics: React.FC = () => {
  const [elements, setElements] = useState<ElementSample[]>(OIL_ELEMENTS);
  const [viscosityCst, setViscosityCst] = useState<number>(8.4);
  const [fuelDilutionPct, setFuelDilutionPct] = useState<number>(1.1);

  const handleRecalibrateSpectrometer = () => {
    confetti({ particleCount: 35, spread: 50 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Droplet className="w-5 h-5 text-amber-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              ENGINE OIL CHEMICAL SPECTROSCOPY & METALLIC WEAR FORENSICS
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Inductively Coupled Plasma (ICP) atomic emission trace metal analysis (Fe, Cu, Ti, Al, Si in PPM)
            </span>
          </div>
        </div>

        <button
          onClick={handleRecalibrateSpectrometer}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-amber-500/20"
        >
          <Sparkles className="w-4 h-4" />
          <span>Calibrate Spectrometer</span>
        </button>
      </div>

      {/* Primary Oil Forensics KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">ICE HEALTH INTEGRITY</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-emerald-400">96.8%</span>
          </div>
          <span className="text-[10px] text-slate-400">Zero Bearing Spalling</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">HIGH-TEMP VISCOSITY</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-amber-400">{viscosityCst}</span>
            <span className="text-xs text-slate-400">cSt @ 100°C</span>
          </div>
          <span className="text-[10px] text-slate-400">Synthetic Ester Grade</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">FUEL DILUTION</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">{fuelDilutionPct}%</span>
          </div>
          <span className="text-[10px] text-slate-400">Piston Ring Blow-by: Low</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">OIL SAMPLE MILEAGE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-purple-400">310</span>
            <span className="text-xs text-slate-400">KM</span>
          </div>
          <span className="text-[10px] text-slate-400">Grand Prix Race Distance</span>
        </div>
      </div>

      {/* ICP Chemical Elements Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 font-mono text-xs">
        {elements.map((el) => {
          const usagePct = Math.round((el.ppm / el.limitPpm) * 100);
          return (
            <div
              key={el.symbol}
              className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-6 h-6 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 flex items-center justify-center font-black">
                    {el.symbol}
                  </span>
                  <span className="font-bold text-white">{el.name}</span>
                </div>
                <span className="text-emerald-400 font-bold text-[10px]">{el.status}</span>
              </div>

              <div className="flex items-baseline justify-between">
                <span className="text-slate-400">Concentration:</span>
                <strong className="text-white">{el.ppm} PPM</strong>
              </div>

              <div className="flex items-baseline justify-between text-[10px] text-slate-500">
                <span>FIA Limit:</span>
                <span>{el.limitPpm} PPM</span>
              </div>

              {/* Bar */}
              <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800 mt-1">
                <div
                  style={{ width: `${usagePct}%` }}
                  className={`h-full ${usagePct > 75 ? 'bg-rose-500' : usagePct > 50 ? 'bg-amber-400' : 'bg-emerald-400'}`}
                />
              </div>

              <span className="text-[9px] text-slate-400 line-clamp-1 mt-1">
                {el.sourceComponent}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
