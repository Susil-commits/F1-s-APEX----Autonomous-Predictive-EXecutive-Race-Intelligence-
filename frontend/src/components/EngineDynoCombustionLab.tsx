import React, { useState, useMemo } from 'react';
import { useRaceStore } from '../store/raceStore';
import { hybridAudio } from '../utils/hybridEngineAudio';
import { Flame, Zap, Activity, Cpu, Sliders, Volume2, VolumeX, CheckCircle2 } from 'lucide-react';

export const EngineDynoCombustionLab: React.FC = () => {
  const { raceState } = useRaceStore();

  const [dynoRpm, setDynoRpm] = useState<number>(10500);
  const [throttlePct, setThrottlePct] = useState<number>(85);
  const [audioActive, setAudioActive] = useState<boolean>(false);

  // Power & Combustion Calculations
  const dynoMetrics = useMemo(() => {
    // ICE Power = ~820 BHP at 11,500 RPM + 160 BHP MGU-K electric boost = ~1020 BHP
    const icePowerBhp = Math.round(750 * (throttlePct / 100) * (dynoRpm / 12000));
    const mgukPowerBhp = Math.round(160 * (throttlePct / 100));
    const totalBhp = icePowerBhp + mgukPowerBhp;

    // Peak Cylinder Pressure (bar)
    const peakPressureBar = Number((180 + (throttlePct / 100) * 130).toFixed(1));
    const knockMarginDeg = Number((12.5 - (throttlePct / 100) * 4.2).toFixed(1));
    const mguhShaftRpm = Math.round(40000 + (throttlePct / 100) * 85000);
    const thermalEfficiencyPct = Number((48.0 + (dynoRpm / 12000) * 6.2).toFixed(1));

    return {
      totalBhp,
      icePowerBhp,
      mgukPowerBhp,
      peakPressureBar,
      knockMarginDeg,
      mguhShaftRpm,
      thermalEfficiencyPct,
    };
  }, [dynoRpm, throttlePct]);

  const toggleDynoAudio = () => {
    if (audioActive) {
      hybridAudio.stop();
      setAudioActive(false);
    } else {
      hybridAudio.start();
      hybridAudio.updateEngineTelemetry(dynoRpm, throttlePct, false);
      setAudioActive(true);
    }
  };

  const handleRpmChange = (rpm: number) => {
    setDynoRpm(rpm);
    if (audioActive) {
      hybridAudio.updateEngineTelemetry(rpm, throttlePct, false);
    }
  };

  const handleThrottleChange = (thr: number) => {
    setThrottlePct(thr);
    if (audioActive) {
      hybridAudio.updateEngineTelemetry(dynoRpm, thr, false);
    }
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-rose-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              ENGINE DYNO & 100% SUSTAINABLE E-FUEL COMBUSTION ANALYZER
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Cylinder peak pressure (P-theta), knock margins, MGU-H turbo spool & 54.2% thermal efficiency
            </span>
          </div>
        </div>

        {/* Audio Toggle */}
        <button
          onClick={toggleDynoAudio}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono font-bold transition-all active:scale-95 ${
            audioActive
              ? 'bg-rose-500 text-black border-rose-400 shadow-md shadow-rose-500/20'
              : 'bg-slate-900 text-slate-300 border-slate-800 hover:text-white'
          }`}
        >
          {audioActive ? <Volume2 className="w-4 h-4 animate-bounce" /> : <VolumeX className="w-4 h-4" />}
          <span>{audioActive ? 'DYNO AUDIO ACTIVE' : 'START DYNO AUDIO'}</span>
        </button>
      </div>

      {/* Primary Dyno KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">TOTAL HYBRID OUTPUT</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-rose-400">{dynoMetrics.totalBhp}</span>
            <span className="text-xs font-mono text-slate-400">BHP</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            ICE: {dynoMetrics.icePowerBhp} + MGU-K: {dynoMetrics.mgukPowerBhp} BHP
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">PEAK CYLINDER PRESSURE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-apex-cyan">
              {dynoMetrics.peakPressureBar}
            </span>
            <span className="text-xs font-mono text-slate-400">BAR</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">P-theta Chamber Peak</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">THERMAL EFFICIENCY</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-emerald-400">
              {dynoMetrics.thermalEfficiencyPct}%
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">World Benchmark &gt; 50%</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] font-mono text-slate-400 uppercase">MGU-H TURBO SHAFT</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black font-mono text-purple-400">
              {dynoMetrics.mguhShaftRpm.toLocaleString()}
            </span>
            <span className="text-xs font-mono text-slate-400">RPM</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Max Limit: 125k RPM</span>
        </div>
      </div>

      {/* Dyno Controls & Combustion Chamber Diagram */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Controls (Left 5 cols) */}
        <div className="lg:col-span-5 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3.5 font-mono text-xs">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            DYNO THROTTLE & ENGINE MAP CONTROLS
          </span>

          {/* RPM Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Engine Speed:</span>
              <span className="font-bold text-rose-400">{dynoRpm} RPM</span>
            </div>
            <input
              type="range"
              min={4000}
              max={12500}
              step={100}
              value={dynoRpm}
              onChange={(e) => handleRpmChange(Number(e.target.value))}
              className="accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Throttle Application Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Throttle Position:</span>
              <span className="font-bold text-apex-cyan">{throttlePct}%</span>
            </div>
            <input
              type="range"
              min={10}
              max={100}
              value={throttlePct}
              onChange={(e) => handleThrottleChange(Number(e.target.value))}
              className="accent-cyan-400 cursor-pointer"
            />
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>100% Sustainable Fuel Blend:</strong> 102 RON Advanced E-Fuel. Ignition knock safety margin: <strong className="text-emerald-400">+{dynoMetrics.knockMarginDeg}° advance</strong>. Zero pre-ignition knocking detected.
          </div>
        </div>

        {/* Cylinder Pressure Indicator Curve Diagram (Right 7 cols) */}
        <div className="lg:col-span-7 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-2">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="font-bold text-slate-300 uppercase">
              CYLINDER PRESSURE INDICATOR DIAGRAM (P - THETA CRANK ANGLE)
            </span>
            <span className="text-rose-400 font-bold">100% E-FUEL BURN</span>
          </div>

          <div className="relative w-full h-56 rounded-lg overflow-hidden bg-black/90 border border-slate-800 p-3">
            <svg viewBox="0 0 500 200" className="w-full h-full">
              {/* Grid Lines */}
              <line x1="40" y1="180" x2="470" y2="180" stroke="#334155" strokeWidth="1" />
              <text x="50" y="195" fill="#64748b" fontSize="9" fontFamily="monospace">
                -180° BDC
              </text>
              <text x="240" y="195" fill="#f59e0b" fontSize="9" fontFamily="monospace">
                0° TDC (Ignition)
              </text>
              <text x="430" y="195" fill="#64748b" fontSize="9" fontFamily="monospace">
                +180° BDC
              </text>

              {/* Dynamic Combustion Curve */}
              <path
                d={`M 40 170 Q 180 160 220 100 Q 250 ${180 - (dynoMetrics.peakPressureBar / 320) * 150} 280 110 Q 380 160 470 170`}
                fill="none"
                stroke="#f43f5e"
                strokeWidth="3.5"
              />

              {/* Peak Tag */}
              <circle cx="250" cy={180 - (dynoMetrics.peakPressureBar / 320) * 150} r="4" fill="#00f0ff" />
              <text
                x="260"
                y={180 - (dynoMetrics.peakPressureBar / 320) * 150 - 5}
                fill="#00f0ff"
                fontSize="10"
                fontFamily="monospace"
                fontWeight="bold"
              >
                {dynoMetrics.peakPressureBar} bar @ +12° ATDC
              </text>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
