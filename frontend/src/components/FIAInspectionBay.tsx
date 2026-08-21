import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { ShieldCheck, AlertOctagon, Scale, Droplets, Layers, CheckCircle2, Award, FileText } from 'lucide-react';
import confetti from 'canvas-confetti';

export const FIAInspectionBay: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  // Scrutineering Measurement States
  const [plankFrontMm, setPlankFrontMm] = useState<number>(9.4);
  const [plankMidMm, setPlankMidMm] = useState<number>(9.2);
  const [plankRearMm, setPlankRearMm] = useState<number>(9.1);

  const [drsGapMm, setDrsGapMm] = useState<number>(84.2);
  const [vehicleWeightKg, setVehicleWeightKg] = useState<number>(799.4);
  const [fuelSampleLiters, setFuelSampleLiters] = useState<number>(1.35);

  const isPlankLegal = plankFrontMm >= 9.0 && plankMidMm >= 9.0 && plankRearMm >= 9.0;
  const isDrsLegal = drsGapMm <= 85.0 && drsGapMm >= 10.0;
  const isWeightLegal = vehicleWeightKg >= 798.0;
  const isFuelLegal = fuelSampleLiters >= 1.0;

  const isAllLegal = isPlankLegal && isDrsLegal && isWeightLegal && isFuelLegal;

  const triggerCertificate = () => {
    if (isAllLegal) {
      confetti({ particleCount: 50, spread: 60 });
    }
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              FIA TECHNICAL INSPECTION & SCRUTINEERING BAY (POST-SESSION RIG)
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Official Technical Delegate compliance checks: Plank wear, DRS slot gap, weighbridge & fuel sample
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Scrutineered Car:</span>
          <span className="font-bold text-white px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            {player?.driver_name || 'Car #1'}
          </span>
        </div>
      </div>

      {/* 4 Technical Inspection Stations */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Station 1: Plank Skid Block Thickness */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between gap-3">
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase font-bold flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-amber-400" /> 1. PLANK SKID WEAR
              </span>
              <span
                className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                  isPlankLegal ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}
              >
                {isPlankLegal ? 'LEGAL' : 'FAIL'}
              </span>
            </div>

            <div className="flex flex-col gap-1 mt-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">Front Skid Hole:</span>
                <span className={plankFrontMm < 9.0 ? 'text-rose-400 font-bold' : 'text-white'}>
                  {plankFrontMm.toFixed(1)} mm
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Mid Skid Hole:</span>
                <span className={plankMidMm < 9.0 ? 'text-rose-400 font-bold' : 'text-white'}>
                  {plankMidMm.toFixed(1)} mm
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Rear Skid Hole:</span>
                <span className={plankRearMm < 9.0 ? 'text-rose-400 font-bold' : 'text-white'}>
                  {plankRearMm.toFixed(1)} mm
                </span>
              </div>
            </div>
          </div>

          <div className="text-[10px] font-mono text-slate-500 border-t border-slate-800 pt-2">
            Min Limit: ≥ 9.0 mm (Article 3.5.9)
          </div>
        </div>

        {/* Station 2: DRS Go/No-Go Slot Gap */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between gap-3">
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase font-bold flex items-center gap-1">
                <Award className="w-3.5 h-3.5 text-apex-cyan" /> 2. DRS SLOT GAUGE
              </span>
              <span
                className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                  isDrsLegal ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}
              >
                {isDrsLegal ? 'LEGAL' : 'FAIL'}
              </span>
            </div>

            <div className="flex items-baseline gap-1 mt-2">
              <span className={`text-3xl font-black font-mono ${isDrsLegal ? 'text-apex-cyan' : 'text-rose-400'}`}>
                {drsGapMm.toFixed(1)}
              </span>
              <span className="text-xs font-mono text-slate-400">MM</span>
            </div>
            <span className="text-xs font-mono text-slate-400">Ball Gauge: 85.0 mm</span>
          </div>

          <div className="text-[10px] font-mono text-slate-500 border-t border-slate-800 pt-2">
            Max Limit: ≤ 85.0 mm Open Gap
          </div>
        </div>

        {/* Station 3: FIA Weighbridge Scale */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between gap-3">
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase font-bold flex items-center gap-1">
                <Scale className="w-3.5 h-3.5 text-purple-400" /> 3. FIA WEIGHBRIDGE
              </span>
              <span
                className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                  isWeightLegal ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}
              >
                {isWeightLegal ? 'LEGAL' : 'FAIL'}
              </span>
            </div>

            <div className="flex items-baseline gap-1 mt-2">
              <span className={`text-3xl font-black font-mono ${isWeightLegal ? 'text-purple-400' : 'text-rose-400'}`}>
                {vehicleWeightKg.toFixed(1)}
              </span>
              <span className="text-xs font-mono text-slate-400">KG</span>
            </div>
            <span className="text-xs font-mono text-slate-400">With Driver & Ballast</span>
          </div>

          <div className="text-[10px] font-mono text-slate-500 border-t border-slate-800 pt-2">
            Min Limit: ≥ 798.0 kg (Article 4.1)
          </div>
        </div>

        {/* Station 4: Fuel Sample Rig */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between gap-3">
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase font-bold flex items-center gap-1">
                <Droplets className="w-3.5 h-3.5 text-pink-400" /> 4. FUEL SAMPLE RIG
              </span>
              <span
                className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                  isFuelLegal ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}
              >
                {isFuelLegal ? 'LEGAL' : 'FAIL'}
              </span>
            </div>

            <div className="flex items-baseline gap-1 mt-2">
              <span className={`text-3xl font-black font-mono ${isFuelLegal ? 'text-pink-400' : 'text-rose-400'}`}>
                {fuelSampleLiters.toFixed(2)}
              </span>
              <span className="text-xs font-mono text-slate-400">LITERS</span>
            </div>
            <span className="text-xs font-mono text-slate-400">Physical Fuel Extracted</span>
          </div>

          <div className="text-[10px] font-mono text-slate-500 border-t border-slate-800 pt-2">
            Min Sample: ≥ 1.0 L (Article 6.5.2)
          </div>
        </div>
      </div>

      {/* Official FIA Technical Delegate Certificate */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${isAllLegal ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'}`}>
            <FileText className="w-6 h-6" />
          </div>
          <div className="flex flex-col font-mono">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white">FIA TECHNICAL DELEGATE PASSPORT</span>
              <span className={`text-xs px-2 py-0.5 rounded font-bold ${isAllLegal ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
                {isAllLegal ? 'PASSED TECHNICAL SCRUTINEERING' : 'DISQUALIFICATION BREACH'}
              </span>
            </div>
            <span className="text-xs text-slate-400">
              Inspector: Jo Bauer (FIA Technical Delegate) • Session: Race Classification Confirmed
            </span>
          </div>
        </div>

        <button
          onClick={triggerCertificate}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-black font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-emerald-500/20"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>Stamp Official Certificate</span>
        </button>
      </div>
    </div>
  );
};
