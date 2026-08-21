import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { ShieldCheck, Flame, Zap, Activity, Cpu, CheckCircle2, Sparkles } from 'lucide-react';
import confetti from 'canvas-confetti';

export const CarbonCompositeAutoclave: React.FC = () => {
  const [autoclaveTempC, setAutoclaveTempC] = useState<number>(180);
  const [autoclavePressureBar, setAutoclavePressureBar] = useState<number>(7.0);
  const [isCuring, setIsCuring] = useState<boolean>(false);
  const [sledTestRan, setSledTestRan] = useState<boolean>(false);

  const handleRunCrashTest = () => {
    setSledTestRan(true);
    confetti({ particleCount: 45, spread: 55 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              CARBON COMPOSITE AUTOCLAVE & FIA CRASH STRUCTURE SLED RIG
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Pre-preg carbon curing (180°C / 7 bar), resin polymerization & FIA 50G monocoque crash impact sled testing
            </span>
          </div>
        </div>

        <button
          onClick={handleRunCrashTest}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-rose-600/20"
        >
          <Zap className="w-4 h-4" />
          <span>Execute FIA 50G Crash Test</span>
        </button>
      </div>

      {/* Primary Autoclave KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">AUTOCLAVE CURING TEMP</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-rose-400">{autoclaveTempC}°C</span>
          </div>
          <span className="text-[10px] text-slate-400">Epoxy Glass Transition</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">CHAMBER PRESSURE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">{autoclavePressureBar}</span>
            <span className="text-xs text-slate-400">BAR</span>
          </div>
          <span className="text-[10px] text-slate-400">Zero Void Compaction</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">RESIN CROSS-LINKING</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-emerald-400">98.4%</span>
          </div>
          <span className="text-[10px] text-slate-400">Full Polymerization</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">PEAK SLED DECELERATION</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-amber-400">{sledTestRan ? '48.2G' : '0.0G'}</span>
          </div>
          <span className="text-[10px] text-slate-400">FIA Limit: &lt; 60G Peak</span>
        </div>
      </div>

      {/* Interactive Controls & Sled Deceleration Trace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Autoclave Parameters (Left 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            AUTOCLAVE THERMAL CYCLE CONTROLS
          </span>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Curing Dwell Temperature:</span>
              <span className="font-bold text-rose-400">{autoclaveTempC}°C</span>
            </div>
            <input
              type="range"
              min={120}
              max={220}
              step={5}
              value={autoclaveTempC}
              onChange={(e) => setAutoclaveTempC(Number(e.target.value))}
              className="accent-rose-500 cursor-pointer"
            />
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Nitrogen Consolidation Pressure:</span>
              <span className="font-bold text-apex-cyan">{autoclavePressureBar} Bar</span>
            </div>
            <input
              type="range"
              min={3.0}
              max={10.0}
              step={0.5}
              value={autoclavePressureBar}
              onChange={(e) => setAutoclavePressureBar(Number(e.target.value))}
              className="accent-cyan-400 cursor-pointer"
            />
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>Monocoque Material Specification:</strong> Toray M46J ultra-high-modulus carbon pre-preg weave with aluminum honeycomb core matrix.
          </div>
        </div>

        {/* Crash Sled Impact Pulse Diagram (Right 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-2">
          <div className="flex justify-between items-center">
            <span className="font-bold text-slate-300 uppercase">
              FIA NOSECONE 50G SLED DECELERATION PULSE
            </span>
            <span className="text-emerald-400 font-bold">15 M/S IMPACT</span>
          </div>

          <div className="relative w-full h-44 rounded-lg overflow-hidden bg-black/90 border border-slate-800 p-3">
            <svg viewBox="0 0 500 160" className="w-full h-full">
              {/* Baseline */}
              <line x1="30" y1="140" x2="470" y2="140" stroke="#334155" strokeWidth="1" />
              <text x="40" y="155" fill="#64748b" fontSize="8" fontFamily="monospace">0 ms (Contact)</text>
              <text x="240" y="155" fill="#64748b" fontSize="8" fontFamily="monospace">25 ms (Peak Decel)</text>
              <text x="420" y="155" fill="#64748b" fontSize="8" fontFamily="monospace">60 ms</text>

              {/* Deceleration Curve */}
              {sledTestRan ? (
                <path
                  d="M 40 140 Q 180 130 220 30 Q 250 25 280 40 Q 380 130 470 140"
                  fill="none"
                  stroke="#22c55e"
                  strokeWidth="3"
                />
              ) : (
                <line x1="40" y1="140" x2="470" y2="140" stroke="#475569" strokeWidth="2" strokeDasharray="3 3" />
              )}

              {sledTestRan && (
                <text x="255" y="20" fill="#22c55e" fontSize="9" fontFamily="monospace" fontWeight="bold">
                  Peak: 48.2G (Passed FIA Article 13)
                </text>
              )}
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
