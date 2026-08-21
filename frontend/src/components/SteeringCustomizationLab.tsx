import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Sliders, Gauge, Cpu, Zap, CheckCircle2, Layout, Sparkles } from 'lucide-react';
import confetti from 'canvas-confetti';

export const SteeringCustomizationLab: React.FC = () => {
  const { raceState } = useRaceStore();

  const [stratMode, setStratMode] = useState<number>(2); // STRAT 1-12
  const [diffEntryPct, setDiffEntryPct] = useState<number>(55);
  const [diffMidPct, setDiffMidPct] = useState<number>(62);
  const [diffExitPct, setDiffExitPct] = useState<number>(70);
  const [engineBrakingStep, setEngineBrakingStep] = useState<number>(3);
  const [oledDisplayTheme, setOledDisplayTheme] = useState<'QUALIFYING' | 'RACE_DELTA' | 'TYRE_HEAT'>('QUALIFYING');

  const handleSaveWheelProfile = () => {
    confetti({ particleCount: 45, spread: 55 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Gauge className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              DRIVER STEERING WHEEL ROTARY & PADDLE CUSTOMIZATION LAB
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Programmable rotary encoders (STRAT, Diff, EB), dual-clutch paddles & in-wheel OLED display themes
            </span>
          </div>
        </div>

        <button
          onClick={handleSaveWheelProfile}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-apex-cyan text-black font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-cyan-500/20"
        >
          <Sparkles className="w-4 h-4" />
          <span>Save Wheel Profile</span>
        </button>
      </div>

      {/* Primary Rotary Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">ENGINE MAP</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-rose-400">STRAT {stratMode}</span>
          </div>
          <span className="text-[10px] text-slate-400">Max Deployment Mode</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">DIFF ENTRY</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-amber-400">{diffEntryPct}%</span>
          </div>
          <span className="text-[10px] text-slate-400">Turn-in Lockup</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">DIFF MID</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-apex-cyan">{diffMidPct}%</span>
          </div>
          <span className="text-[10px] text-slate-400">Apex Rotation</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">DIFF EXIT</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-emerald-400">{diffExitPct}%</span>
          </div>
          <span className="text-[10px] text-slate-400">Traction Lockup</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">ENGINE BRAKING</span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-purple-400">EB #{engineBrakingStep}</span>
          </div>
          <span className="text-[10px] text-slate-400">Overrun Drag</span>
        </div>
      </div>

      {/* Interactive Rotary Knobs & OLED Themes */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Rotary Knobs (Left 7 cols) */}
        <div className="lg:col-span-7 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3 font-mono text-xs">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            ROTARY ENCODER CALIBRATION
          </span>

          {/* STRAT */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Engine Mode Dial (STRAT):</span>
              <span className="font-bold text-rose-400">STRAT {stratMode}</span>
            </div>
            <input
              type="range"
              min={1}
              max={12}
              value={stratMode}
              onChange={(e) => setStratMode(Number(e.target.value))}
              className="accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Diff Entry */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Corner Entry Differential:</span>
              <span className="font-bold text-amber-400">{diffEntryPct}% Lock</span>
            </div>
            <input
              type="range"
              min={40}
              max={80}
              value={diffEntryPct}
              onChange={(e) => setDiffEntryPct(Number(e.target.value))}
              className="accent-amber-400 cursor-pointer"
            />
          </div>

          {/* Diff Exit */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Corner Exit Differential:</span>
              <span className="font-bold text-emerald-400">{diffExitPct}% Lock</span>
            </div>
            <input
              type="range"
              min={50}
              max={95}
              value={diffExitPct}
              onChange={(e) => setDiffExitPct(Number(e.target.value))}
              className="accent-emerald-400 cursor-pointer"
            />
          </div>

          {/* Engine Braking */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Engine Braking (EB):</span>
              <span className="font-bold text-purple-400">Step {engineBrakingStep} / 5</span>
            </div>
            <input
              type="range"
              min={1}
              max={5}
              value={engineBrakingStep}
              onChange={(e) => setEngineBrakingStep(Number(e.target.value))}
              className="accent-purple-400 cursor-pointer"
            />
          </div>
        </div>

        {/* OLED Themes & Wheel Layout (Right 5 cols) */}
        <div className="lg:col-span-5 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3 font-mono text-xs">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            IN-WHEEL OLED DASH THEME
          </span>

          <div className="grid grid-cols-1 gap-2">
            {(['QUALIFYING', 'RACE_DELTA', 'TYRE_HEAT'] as const).map((theme) => (
              <button
                key={theme}
                onClick={() => setOledDisplayTheme(theme)}
                className={`p-3 rounded-xl border text-left flex items-center justify-between transition-all ${
                  oledDisplayTheme === theme
                    ? 'bg-slate-900 border-apex-cyan shadow-md shadow-cyan-500/10 text-white font-bold'
                    : 'bg-slate-900/40 border-slate-800 text-slate-400'
                }`}
              >
                <span>{theme === 'QUALIFYING' ? '⚡ Q3 PURPLE DELTA DASH' : theme === 'RACE_DELTA' ? '⏱️ STINT PACING & FUEL DELTA' : '🌡️ 4-WHEEL TYRE HEATMAP DASH'}</span>
                {oledDisplayTheme === theme && <CheckCircle2 className="w-4 h-4 text-apex-cyan" />}
              </button>
            ))}
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            Custom profile synchronizes instantly with the steering wheel digital dash unit (DDU).
          </div>
        </div>
      </div>
    </div>
  );
};
