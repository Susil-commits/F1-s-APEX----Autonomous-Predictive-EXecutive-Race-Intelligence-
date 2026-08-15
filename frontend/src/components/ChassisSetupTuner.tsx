import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Sliders, Wrench, Wind, Gauge, Shield, RotateCcw, CheckCircle } from 'lucide-react';
import { audioEngine } from '../utils/audioEngine';

export const ChassisSetupTuner: React.FC = () => {
  const { raceState } = useRaceStore();

  const [frontWing, setFrontWing] = useState<number>(34); // degrees
  const [rearWing, setRearWing] = useState<number>(38); // degrees
  const [brakeBias, setBrakeBias] = useState<number>(55.5); // % Front
  const [diffOnThrottle, setDiffOnThrottle] = useState<number>(70); // % Lock
  const [diffMidCorner, setDiffMidCorner] = useState<number>(60); // % Lock
  const [antiRollStiffness, setAntiRollStiffness] = useState<'soft' | 'balanced' | 'stiff'>('balanced');

  // Compute live aerodynamic downforce, top speed, and cornering lateral G
  const setupDynamics = useMemo(() => {
    const totalWing = frontWing + rearWing;
    const aeroFrontPct = parseFloat(((frontWing / totalWing) * 100).toFixed(1));
    const aeroRearPct = parseFloat((100 - aeroFrontPct).toFixed(1));

    // Base top speed: 355 km/h with minimum wing, 305 km/h with maximum wing
    const topSpeedKmh = Math.round(365 - (totalWing - 50) * 1.35);

    // Lateral cornering G: 3.8G to 5.2G based on wing level and roll stiffness
    const rollBonus = antiRollStiffness === 'stiff' ? 0.2 : antiRollStiffness === 'soft' ? -0.15 : 0;
    const lateralG = parseFloat((3.6 + (totalWing / 90) * 1.5 + rollBonus).toFixed(2));

    // Tyre wear rate multiplier
    const wearMultiplier = parseFloat((0.85 + (totalWing / 80) * 0.35).toFixed(2));

    // Oversteer / Understeer balance
    let handlingTendency = 'BALANCED';
    if (aeroFrontPct > 48.5) handlingTendency = 'OVERSTEER TENDENCY (SHARP TURN-IN)';
    else if (aeroFrontPct < 44.0) handlingTendency = 'UNDERSTEER TENDENCY (STABLE REAR)';

    return {
      topSpeedKmh,
      lateralG,
      aeroFrontPct,
      aeroRearPct,
      wearMultiplier,
      handlingTendency,
    };
  }, [frontWing, rearWing, brakeBias, diffOnThrottle, diffMidCorner, antiRollStiffness]);

  const handleResetDefaults = () => {
    setFrontWing(34);
    setRearWing(38);
    setBrakeBias(55.5);
    setDiffOnThrottle(70);
    setDiffMidCorner(60);
    setAntiRollStiffness('balanced');
    audioEngine.playRadioBleep();
  };

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Wrench className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Chassis Aerodynamics & Setup Balancer
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              Tune front/rear wing downforce, brake bias %, and mechanical differential lock
            </p>
          </div>
        </div>

        <button
          onClick={handleResetDefaults}
          className="flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[10.5px] font-bold transition-all active:scale-95"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Defaults</span>
        </button>
      </div>

      {/* Dynamic Results KPI Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center mb-4">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] uppercase font-sans text-slate-400 block font-semibold">
            Max Top Speed
          </span>
          <span className="text-2xl font-black text-apex-cyan glow-cyan">
            {setupDynamics.topSpeedKmh}
          </span>
          <span className="text-[10px] text-slate-500 block">km/h on Straight</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] uppercase font-sans text-slate-400 block font-semibold">
            Lateral Grip
          </span>
          <span className="text-2xl font-black text-emerald-400">
            {setupDynamics.lateralG} G
          </span>
          <span className="text-[10px] text-slate-500 block">High-Speed Apex</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] uppercase font-sans text-slate-400 block font-semibold">
            Aero Balance
          </span>
          <span className="text-xl font-black text-amber-300">
            {setupDynamics.aeroFrontPct}% F
          </span>
          <span className="text-[10px] text-slate-500 block">{setupDynamics.aeroRearPct}% Rear</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] uppercase font-sans text-slate-400 block font-semibold">
            Wear Factor
          </span>
          <span className="text-2xl font-black text-purple-400">
            {setupDynamics.wearMultiplier}x
          </span>
          <span className="text-[10px] text-slate-500 block">Degradation Rate</span>
        </div>
      </div>

      {/* Sliders Tuning Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
        {/* Front Wing Angle */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1">
            <span className="text-slate-300 font-sans font-semibold">Front Wing Flap Angle:</span>
            <span className="font-bold text-cyan-400">{frontWing}°</span>
          </div>
          <input
            type="range"
            min={20}
            max={50}
            value={frontWing}
            onChange={(e) => setFrontWing(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
          <div className="flex justify-between text-[9px] text-slate-500 mt-1">
            <span>20° (Low Drag)</span>
            <span>50° (High Downforce)</span>
          </div>
        </div>

        {/* Rear Wing Angle */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1">
            <span className="text-slate-300 font-sans font-semibold">Rear Wing Mainplane Angle:</span>
            <span className="font-bold text-cyan-400">{rearWing}°</span>
          </div>
          <input
            type="range"
            min={22}
            max={52}
            value={rearWing}
            onChange={(e) => setRearWing(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
          <div className="flex justify-between text-[9px] text-slate-500 mt-1">
            <span>22° (Monza Spec)</span>
            <span>52° (Monaco Spec)</span>
          </div>
        </div>

        {/* Brake Bias */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1">
            <span className="text-slate-300 font-sans font-semibold">Brake Pressure Bias:</span>
            <span className="font-bold text-amber-300">{brakeBias}% Front</span>
          </div>
          <input
            type="range"
            min={50.0}
            max={62.0}
            step={0.5}
            value={brakeBias}
            onChange={(e) => setBrakeBias(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
          />
          <div className="flex justify-between text-[9px] text-slate-500 mt-1">
            <span>50.0% (Rear Bias)</span>
            <span>62.0% (Front Lock Safety)</span>
          </div>
        </div>

        {/* On-Throttle Differential */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="flex items-center justify-between mb-1">
            <span className="text-slate-300 font-sans font-semibold">On-Throttle Diff Lock:</span>
            <span className="font-bold text-emerald-400">{diffOnThrottle}%</span>
          </div>
          <input
            type="range"
            min={50}
            max={100}
            value={diffOnThrottle}
            onChange={(e) => setDiffOnThrottle(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
          />
          <div className="flex justify-between text-[9px] text-slate-500 mt-1">
            <span>50% (Open Diff - Traction)</span>
            <span>100% (Locked - Max Drive)</span>
          </div>
        </div>
      </div>

      {/* Handling Assessment Badge */}
      <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-[11px] font-sans">
        <span className="text-slate-400">Chassis Balance Assessment:</span>
        <span className="font-bold text-cyan-400 font-mono">{setupDynamics.handlingTendency}</span>
      </div>
    </div>
  );
};
