import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Sliders, Activity, ShieldAlert, Wind, Zap, CheckCircle2 } from 'lucide-react';

export const ChassisSuspensionLab: React.FC = () => {
  const { raceState } = useRaceStore();

  const [frontSuspensionType, setFrontSuspensionType] = useState<'PUSHROD' | 'PULLROD'>('PUSHROD');
  const [frontRideHeightMm, setFrontRideHeightMm] = useState<number>(22);
  const [rearRideHeightMm, setRearRideHeightMm] = useState<number>(55);
  const [heaveStiffnessNmm, setHeaveStiffnessNmm] = useState<number>(140);
  const [arbStiffnessIndex, setArbStiffnessIndex] = useState<number>(7);

  // Dynamic calculations: High-speed heave compression at 300 km/h
  const highSpeedFrontDeflectionMm = useMemo(() => {
    // 1500kg aero downforce at 300 km/h = ~14,700 N load
    const loadN = 8200; // Front axle portion
    return Number((loadN / (heaveStiffnessNmm * 10)).toFixed(1));
  }, [heaveStiffnessNmm]);

  const dynamicFrontRideHeight = Math.max(0, frontRideHeightMm - highSpeedFrontDeflectionMm);
  const isBottoming = dynamicFrontRideHeight < 5.0;
  const isPorpoisingRisk = dynamicFrontRideHeight < 8.0 && rearRideHeightMm > 50;

  // Ground Effect Downforce Suction (N)
  const groundEffectDownforceN = useMemo(() => {
    const baseDownforce = 12500;
    // Lower front ride height increases suction until aerodynamic stall
    if (dynamicFrontRideHeight < 4.0) {
      return 8500; // Flow separation / stall
    }
    const groundEffectMultiplier = 1.0 + (30 - dynamicFrontRideHeight) * 0.035;
    return Math.round(baseDownforce * groundEffectMultiplier);
  }, [dynamicFrontRideHeight]);

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              CHASSIS SUSPENSION KINEMATICS & GROUND-EFFECT VENTURI LAB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Pushrod vs pullrod geometry, dynamic ride heights, heave spring compression & porpoising frequency
            </span>
          </div>
        </div>

        {/* Geometry Switcher */}
        <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setFrontSuspensionType('PUSHROD')}
            className={`px-3 py-1 rounded-lg transition-all ${
              frontSuspensionType === 'PUSHROD' ? 'bg-amber-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Pushrod Front
          </button>
          <button
            onClick={() => setFrontSuspensionType('PULLROD')}
            className={`px-3 py-1 rounded-lg transition-all ${
              frontSuspensionType === 'PULLROD' ? 'bg-amber-500 text-black font-bold' : 'text-slate-400'
            }`}
          >
            Pullrod Front
          </button>
        </div>
      </div>

      {/* Primary Suspension KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">DYNAMIC FRONT RIDE HEIGHT</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black font-mono ${dynamicFrontRideHeight < 8.0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {dynamicFrontRideHeight.toFixed(1)}
            </span>
            <span className="text-xs font-mono text-slate-400">MM @ 300 KM/H</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Static: {frontRideHeightMm} mm</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">UNDERBODY SUCTION FORCE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-apex-cyan">
              {groundEffectDownforceN}
            </span>
            <span className="text-xs font-mono text-slate-400">N</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Venturi Ground Effect</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">HEAVE COMPRESSION</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-purple-400">
              -{highSpeedFrontDeflectionMm}
            </span>
            <span className="text-xs font-mono text-slate-400">MM</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Aero Load Travel</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">PORPOISING RISK</span>
          <div className="flex items-center gap-2 mt-1">
            {isBottoming ? (
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
                BOTTOMING CRITICAL
              </span>
            ) : isPorpoisingRisk ? (
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                6.2 HZ OSCILLATION
              </span>
            ) : (
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                AERO STABLE
              </span>
            )}
          </div>
          <span className="text-[10px] font-mono text-slate-400">Floor Seal Integrity</span>
        </div>
      </div>

      {/* Interactive Suspension Tuner & Venturi Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Sliders (Left 5 cols) */}
        <div className="lg:col-span-5 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3.5 font-mono text-xs">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            SUSPENSION TUNING PARAMETERS
          </span>

          {/* Front Static Ride Height */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Front Static Ride Height:</span>
              <span className="font-bold text-white">{frontRideHeightMm} mm</span>
            </div>
            <input
              type="range"
              min={15}
              max={45}
              value={frontRideHeightMm}
              onChange={(e) => setFrontRideHeightMm(Number(e.target.value))}
              className="accent-amber-500 cursor-pointer"
            />
          </div>

          {/* Rear Static Ride Height */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Rear Static Ride Height:</span>
              <span className="font-bold text-white">{rearRideHeightMm} mm</span>
            </div>
            <input
              type="range"
              min={35}
              max={85}
              value={rearRideHeightMm}
              onChange={(e) => setRearRideHeightMm(Number(e.target.value))}
              className="accent-cyan-400 cursor-pointer"
            />
          </div>

          {/* Heave Spring Stiffness */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Heave Spring Rate:</span>
              <span className="font-bold text-white">{heaveStiffnessNmm} N/mm</span>
            </div>
            <input
              type="range"
              min={80}
              max={220}
              step={10}
              value={heaveStiffnessNmm}
              onChange={(e) => setHeaveStiffnessNmm(Number(e.target.value))}
              className="accent-purple-400 cursor-pointer"
            />
          </div>

          {/* Anti-Roll Bar */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Anti-Roll Bar (ARB) Setting:</span>
              <span className="font-bold text-white">Blade #{arbStiffnessIndex}</span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={arbStiffnessIndex}
              onChange={(e) => setArbStiffnessIndex(Number(e.target.value))}
              className="accent-pink-400 cursor-pointer"
            />
          </div>
        </div>

        {/* Venturi Underfloor Suction Pressure Diagram (Right 7 cols) */}
        <div className="lg:col-span-7 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-2">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="font-bold text-slate-300 uppercase">
              VENTURI TUNNEL UNDERFLOOR PRESSURE COEFFICIENT (CP PROFILE)
            </span>
            <span className="text-apex-cyan font-bold">CFD GROUND EFFECT</span>
          </div>

          <div className="relative w-full h-56 rounded-lg overflow-hidden bg-black/80 border border-slate-800 p-3">
            <svg viewBox="0 0 500 200" className="w-full h-full">
              {/* Ground Plane */}
              <line x1="20" y1="180" x2="480" y2="180" stroke="#475569" strokeWidth="3" />
              <text x="30" y="195" fill="#64748b" fontSize="9" fontFamily="monospace">
                Track Tarmac Surface
              </text>

              {/* Venturi Underfloor Contour */}
              <path
                d={`M 30 ${180 - frontRideHeightMm * 1.5} Q 220 ${180 - dynamicFrontRideHeight * 2.2} 470 ${180 - rearRideHeightMm * 1.5}`}
                fill="none"
                stroke="#00f0ff"
                strokeWidth="4"
              />

              {/* Suction Gradient Arrows */}
              <line x1="220" y1="60" x2="220" y2={180 - dynamicFrontRideHeight * 2.2 - 6} stroke="#ec4899" strokeWidth="2.5" />
              <text x="230" y="80" fill="#ec4899" fontSize="10" fontFamily="monospace" fontWeight="bold">
                Max Suction Throat (-Cp 4.2)
              </text>

              {/* Chassis Floor Label */}
              <text x="320" y={180 - rearRideHeightMm * 1.5 - 12} fill="#00f0ff" fontSize="9" fontFamily="monospace">
                Rear Diffuser Expansion
              </text>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
