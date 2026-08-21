import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Flag, ShieldAlert, Sliders, Zap, RotateCcw, Award, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

export const RedFlagStrategyMatrix: React.FC = () => {
  const { raceState } = useRaceStore();
  const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

  const [selectedRestartCompound, setSelectedRestartCompound] = useState<'SOFT' | 'MEDIUM' | 'HARD'>('SOFT');
  const [frontWingTrimAdjustmentDeg, setFrontWingTrimAdjustmentDeg] = useState<number>(0.5);
  const [clutchBitePointPct, setClutchBitePointPct] = useState<number>(64);
  const [isLaunchTested, setIsLaunchTested] = useState<boolean>(false);

  const handleTestLaunch = () => {
    setIsLaunchTested(true);
    confetti({ particleCount: 45, spread: 55 });
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Flag className="w-5 h-5 text-rose-500 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              EMERGENCY RED FLAG SUSPENSION & FREE TYRE CHANGE MATRIX
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Red flag pit lane tire change loophole, standing grid restart launch simulation & wing trim tuning
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-rose-500/20 text-rose-300 border border-rose-500/40 px-3 py-1.5 rounded-xl text-xs font-mono font-bold animate-pulse">
          <ShieldAlert className="w-4 h-4" />
          <span>SESSION SUSPENDED • PIT LANE PROCEDURE</span>
        </div>
      </div>

      {/* Primary Red Flag Strategy Advantage KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">TIME LOSS ON TIRE CHANGE</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-emerald-400">0.0</span>
            <span className="text-xs text-slate-400">SECONDS</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-bold">100% Free Pit Stop (Rule 57.3)</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">RESTART COMPOUND</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-rose-400">{selectedRestartCompound}</span>
          </div>
          <span className="text-[10px] text-slate-400">New Sticker Set Fitted</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">LAUNCH REACTION TIME</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-apex-cyan">0.18</span>
            <span className="text-xs text-slate-400">SECONDS</span>
          </div>
          <span className="text-[10px] text-slate-400">5 Red Lights Extinguished</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase">0-100 KM/H LAUNCH</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-black text-purple-400">2.38</span>
            <span className="text-xs text-slate-400">SECONDS</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Standing Grid Restart</span>
        </div>
      </div>

      {/* Interactive Controls & Standing Launch Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Tyre & Setup Controls (Left 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col gap-3 font-mono text-xs">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            PIT LANE RED FLAG CONFIGURATION
          </span>

          {/* Compound Selection */}
          <div className="flex flex-col gap-1.5">
            <span className="text-slate-400">Select Free Restart Tire Compound:</span>
            <div className="grid grid-cols-3 gap-2">
              {(['SOFT', 'MEDIUM', 'HARD'] as const).map((comp) => (
                <button
                  key={comp}
                  onClick={() => setSelectedRestartCompound(comp)}
                  className={`p-2.5 rounded-xl border text-center transition-all ${
                    selectedRestartCompound === comp
                      ? comp === 'SOFT'
                        ? 'bg-rose-500 text-black font-black border-rose-400'
                        : comp === 'MEDIUM'
                        ? 'bg-amber-400 text-black font-black border-amber-300'
                        : 'bg-white text-black font-black border-slate-300'
                      : 'bg-slate-900 text-slate-400 border-slate-800'
                  }`}
                >
                  {comp} (NEW)
                </button>
              ))}
            </div>
          </div>

          {/* Front Wing Flap Trim Adjustment */}
          <div className="flex flex-col gap-1 mt-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Front Wing Flap Angle Adjustment:</span>
              <span className="font-bold text-white">+{frontWingTrimAdjustmentDeg}°</span>
            </div>
            <input
              type="range"
              min={-1.5}
              max={2.0}
              step={0.1}
              value={frontWingTrimAdjustmentDeg}
              onChange={(e) => setFrontWingTrimAdjustmentDeg(Number(e.target.value))}
              className="accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Clutch Bite Point */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Clutch Bite Point Calibration:</span>
              <span className="font-bold text-apex-cyan">{clutchBitePointPct}%</span>
            </div>
            <input
              type="range"
              min={50}
              max={80}
              value={clutchBitePointPct}
              onChange={(e) => setClutchBitePointPct(Number(e.target.value))}
              className="accent-cyan-400 cursor-pointer"
            />
          </div>
        </div>

        {/* Standing Restart Launch Visualizer (Right 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3 font-mono text-xs">
          <span className="font-bold text-slate-300 uppercase border-b border-slate-800 pb-2">
            STANDING RESTART LAUNCH CONTROL DRILL
          </span>

          <div className="flex items-center justify-center gap-3 p-4 bg-black/70 rounded-xl border border-slate-800">
            {[1, 2, 3, 4, 5].map((light) => (
              <div
                key={light}
                className="w-7 h-7 rounded-full bg-rose-500 border-2 border-rose-300 shadow-lg shadow-rose-500/50 animate-pulse"
              />
            ))}
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            <strong>Launch Protocol:</strong> RPM target set to 10,800 RPM. Release secondary paddle at light extinction to reach 100 km/h in 2.38s.
          </div>

          <button
            onClick={handleTestLaunch}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-rose-600/30"
          >
            <Zap className="w-4 h-4" />
            <span>EXECUTE STANDING RESTART LAUNCH TEST</span>
          </button>
        </div>
      </div>
    </div>
  );
};
