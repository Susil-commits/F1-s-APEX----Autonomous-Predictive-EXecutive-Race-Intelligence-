import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Wind, ShieldCheck, AlertOctagon, Sliders, CheckCircle2, Zap, Activity } from 'lucide-react';

export const AeroelasticWingFlexLab: React.FC = () => {
  const { raceState } = useRaceStore();

  const [appliedLoadN, setAppliedLoadN] = useState<number>(1000);
  const [carbonStiffnessGpa, setCarbonStiffnessGpa] = useState<number>(120);
  const [selectedWing, setSelectedWing] = useState<'REAR_MAIN_PLANE' | 'FRONT_FLAP'>('REAR_MAIN_PLANE');

  // Physics calculation: Wing Deflection under aero downforce load
  // Deflection (mm) = (F * L^3) / (3 * E * I)
  const deflectionMm = useMemo(() => {
    const beamLengthM = selectedWing === 'REAR_MAIN_PLANE' ? 0.95 : 0.85;
    const momentOfInertia = selectedWing === 'REAR_MAIN_PLANE' ? 4.2e-7 : 3.1e-7;
    const E = carbonStiffnessGpa * 1e9;
    const defM = (appliedLoadN * Math.pow(beamLengthM, 3)) / (3 * E * momentOfInertia);
    return Number((defM * 1000).toFixed(2));
  }, [appliedLoadN, carbonStiffnessGpa, selectedWing]);

  const fiaLegalLimitMm = 15.0;
  const isLegal = deflectionMm <= fiaLegalLimitMm;

  // Straight line speed delta estimated from aero drag reduction
  const dragReductionDeltaKmh = useMemo(() => {
    return Number((deflectionMm * 0.38).toFixed(1));
  }, [deflectionMm]);

  // SVG curved path calculation for bending visualizer
  const wingSvgPath = useMemo(() => {
    const startX = 50;
    const startY = 120;
    const endX = 550;
    const endY = 120;
    const maxDrop = Math.min(80, deflectionMm * 4.5);
    const ctrlX = 300;
    const ctrlY = 120 + maxDrop;
    return `M ${startX} ${startY} Q ${ctrlX} ${ctrlY} ${endX} ${endY}`;
  }, [deflectionMm]);

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Wind className="w-5 h-5 text-pink-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              AEROELASTIC WING FLEXIBILITY & FIA DEFLECTION PHYSICS LAB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              High-speed carbon fiber aero deflection, mini-DRS slot gap deformation & FIA technical legality
            </span>
          </div>
        </div>

        {/* Wing Component Selector */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setSelectedWing('REAR_MAIN_PLANE')}
            className={`px-3 py-1 rounded-lg transition-all ${
              selectedWing === 'REAR_MAIN_PLANE' ? 'bg-pink-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Rear Wing Main Plane
          </button>
          <button
            onClick={() => setSelectedWing('FRONT_FLAP')}
            className={`px-3 py-1 rounded-lg transition-all ${
              selectedWing === 'FRONT_FLAP' ? 'bg-pink-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Front Wing Upper Flap
          </button>
        </div>
      </div>

      {/* Primary Telemetry KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">MEASURED DEFLECTION</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black font-mono ${isLegal ? 'text-emerald-400' : 'text-rose-400'}`}>
              {deflectionMm}
            </span>
            <span className="text-xs font-mono text-slate-400">MM</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Limit: ≤ 15.0 mm</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">FIA LEGALITY STATUS</span>
          <div className="flex items-center gap-2 mt-1">
            {isLegal ? (
              <div className="flex items-center gap-1.5 text-emerald-400 font-mono text-sm font-bold">
                <ShieldCheck className="w-5 h-5" />
                <span>COMPLIANT</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-rose-400 font-mono text-sm font-bold animate-pulse">
                <AlertOctagon className="w-5 h-5" />
                <span>ILLEGAL FLEX</span>
              </div>
            )}
          </div>
          <span className="text-[10px] font-mono text-slate-400">Article 3.15 Technical Regs</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">APPLIED TEST LOAD</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-apex-cyan">{appliedLoadN}</span>
            <span className="text-xs font-mono text-slate-400">NEWTONS</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Standard FIA: 1000 N</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">STRAIGHT-LINE GAIN</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-amber-400">+{dragReductionDeltaKmh}</span>
            <span className="text-xs font-mono text-slate-400">KM/H</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Top speed drag shed</span>
        </div>
      </div>

      {/* Interactive Controls & Deflection Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Controls Sidebar (Left 4 cols) */}
        <div className="lg:col-span-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-4 text-xs font-mono">
          <span className="font-bold text-slate-300 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <Sliders className="w-4 h-4 text-pink-400" />
            LOAD & STIFFNESS PARAMETERS
          </span>

          {/* Applied Vertical Load Slider */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between">
              <span className="text-slate-400">Vertical Test Load:</span>
              <span className="font-bold text-white">{appliedLoadN} N</span>
            </div>
            <input
              type="range"
              min={200}
              max={1500}
              step={50}
              value={appliedLoadN}
              onChange={(e) => setAppliedLoadN(Number(e.target.value))}
              className="accent-pink-500 cursor-pointer"
            />
          </div>

          {/* Carbon Fiber Modulus Slider */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between">
              <span className="text-slate-400">Carbon Young's Modulus:</span>
              <span className="font-bold text-white">{carbonStiffnessGpa} GPa</span>
            </div>
            <input
              type="range"
              min={70}
              max={200}
              step={5}
              value={carbonStiffnessGpa}
              onChange={(e) => setCarbonStiffnessGpa(Number(e.target.value))}
              className="accent-cyan-400 cursor-pointer"
            />
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>FIA Technical Directive (TD-018):</strong> Wings must withstand 1000N vertical downforce load with ≤ 15mm deflection. Excessive flexibility to create mini-DRS airflow bleed is strictly prohibited.
          </div>
        </div>

        {/* Dynamic SVG Wing Deflection Visualizer (Right 8 cols) */}
        <div className="lg:col-span-8 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-2">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="font-bold text-slate-300 uppercase">
              CARBON WING ELEMENT DEFORMATION PROFILE (2D CROSS-SECTION)
            </span>
            <span className="text-pink-400 font-bold">LIVE STRESS CAD</span>
          </div>

          <div className="relative w-full h-56 rounded-lg overflow-hidden bg-black/80 border border-slate-800 flex items-center justify-center p-4">
            <svg viewBox="0 0 600 240" className="w-full h-full">
              {/* Reference Grid */}
              <line x1="50" y1="120" x2="550" y2="120" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />
              <text x="60" y="112" fill="#64748b" fontSize="10" fontFamily="monospace">
                0.0 mm Nominal Datum
              </text>

              {/* FIA Limit Threshold Line */}
              <line x1="50" y1={120 + 15 * 4.5} x2="550" y2={120 + 15 * 4.5} stroke="#f43f5e" strokeWidth="1" strokeDasharray="2 2" />
              <text x="60" y={120 + 15 * 4.5 + 12} fill="#f43f5e" fontSize="9" fontFamily="monospace">
                FIA 15.0 mm Max Legal Tolerance
              </text>

              {/* Bending Wing Element Path */}
              <path
                d={wingSvgPath}
                fill="none"
                stroke={isLegal ? '#ec4899' : '#f43f5e'}
                strokeWidth="8"
                strokeLinecap="round"
              />

              {/* Load Arrow Vector */}
              <line
                x1="300"
                y1="40"
                x2="300"
                y2={110 + deflectionMm * 4.5}
                stroke="#00f0ff"
                strokeWidth="3"
                markerEnd="url(#arrow)"
              />
              <text x="310" y="70" fill="#00f0ff" fontSize="11" fontFamily="monospace" fontWeight="bold">
                {appliedLoadN} N Aero Load
              </text>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
