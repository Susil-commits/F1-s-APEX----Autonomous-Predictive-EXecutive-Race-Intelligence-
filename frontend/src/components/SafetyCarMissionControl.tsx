import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { ShieldAlert, AlertTriangle, Play, RotateCcw, Zap, Flag, Timer, CheckCircle2 } from 'lucide-react';
import confetti from 'canvas-confetti';

export const SafetyCarMissionControl: React.FC = () => {
  const { raceState, setRaceState } = useRaceStore();
  const [activeScMode, setActiveScMode] = useState<'NONE' | 'VSC' | 'SC' | 'RED_FLAG'>('NONE');
  const [lappedCarsCanOvertake, setLappedCarsCanOvertake] = useState<boolean>(false);

  const handleDeploy = (mode: 'NONE' | 'VSC' | 'SC' | 'RED_FLAG') => {
    setActiveScMode(mode);
    if (raceState) {
      const mappedStatus = mode === 'SC' ? 'SAFETY_CAR' : mode === 'VSC' ? 'VSC' : 'NONE';
      setRaceState({
        ...raceState,
        safety_car: mappedStatus,
      });
    }

    if (mode === 'SC' || mode === 'RED_FLAG') {
      confetti({ particleCount: 40, spread: 50 });
    }
  };

  const handleUnlapLappedCars = () => {
    setLappedCarsCanOvertake(true);
    confetti({ particleCount: 30, spread: 40 });
  };

  // Pit Window Delta savings
  const greenFlagPitLossS = 21.5;
  const scPitLossS = 11.2;
  const vscPitLossS = 14.8;
  const currentPitLossS =
    activeScMode === 'SC' ? scPitLossS : activeScMode === 'VSC' ? vscPitLossS : greenFlagPitLossS;
  const deltaSavingsS = (greenFlagPitLossS - currentPitLossS).toFixed(1);

  return (
    <div className="w-full rounded-2xl bg-slate-950 border border-slate-800 p-4 flex flex-col gap-4 shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="font-bold text-white text-sm">
              FIA SAFETY CAR & VSC DEPLOYMENT MISSION CONTROL
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Race director safety car intervention, speed delta pacing & pit window delta bonus calculation
            </span>
          </div>
        </div>

        {/* Current SC Status Badge */}
        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-xl text-xs font-mono font-bold border ${
              activeScMode === 'RED_FLAG'
                ? 'bg-rose-600 text-white border-rose-500 animate-pulse'
                : activeScMode === 'SC'
                ? 'bg-amber-500 text-black border-amber-400 font-black animate-pulse'
                : activeScMode === 'VSC'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
            }`}
          >
            {activeScMode === 'NONE' ? 'TRACK STATUS: GREEN FLAG' : `TRACK STATUS: ${activeScMode}`}
          </span>
        </div>
      </div>

      {/* Deployment Action Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Button 1: Green Flag */}
        <button
          onClick={() => handleDeploy('NONE')}
          className={`p-4 rounded-xl border flex flex-col items-center gap-1.5 transition-all active:scale-95 ${
            activeScMode === 'NONE'
              ? 'bg-emerald-950/80 border-emerald-500 shadow-md shadow-emerald-500/20'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <Flag className="w-6 h-6 text-emerald-400" />
          <span className="font-mono text-xs font-bold text-white uppercase">GREEN FLAG (RACING)</span>
          <span className="text-[10px] font-mono text-slate-400">Standard 100% pace</span>
        </button>

        {/* Button 2: VSC */}
        <button
          onClick={() => handleDeploy('VSC')}
          className={`p-4 rounded-xl border flex flex-col items-center gap-1.5 transition-all active:scale-95 ${
            activeScMode === 'VSC'
              ? 'bg-amber-950/80 border-amber-500 shadow-md shadow-amber-500/20'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <AlertTriangle className="w-6 h-6 text-amber-400" />
          <span className="font-mono text-xs font-bold text-white uppercase">VIRTUAL SAFETY CAR (VSC)</span>
          <span className="text-[10px] font-mono text-slate-400">40% speed delta pacing</span>
        </button>

        {/* Button 3: Full Safety Car */}
        <button
          onClick={() => handleDeploy('SC')}
          className={`p-4 rounded-xl border flex flex-col items-center gap-1.5 transition-all active:scale-95 ${
            activeScMode === 'SC'
              ? 'bg-amber-500 text-black border-amber-300 shadow-lg shadow-amber-500/30'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <ShieldAlert className="w-6 h-6 text-amber-950" />
          <span className="font-mono text-xs font-bold uppercase">FULL SAFETY CAR (SC)</span>
          <span className="text-[10px] font-mono opacity-80">Bernd Mayländer Aston/Mercedes</span>
        </button>

        {/* Button 4: Red Flag */}
        <button
          onClick={() => handleDeploy('RED_FLAG')}
          className={`p-4 rounded-xl border flex flex-col items-center gap-1.5 transition-all active:scale-95 ${
            activeScMode === 'RED_FLAG'
              ? 'bg-rose-600 text-white border-rose-400 shadow-lg shadow-rose-600/30'
              : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <Flag className="w-6 h-6 text-white" />
          <span className="font-mono text-xs font-bold uppercase">RED FLAG (SUSPEND)</span>
          <span className="text-[10px] font-mono opacity-80">All cars enter pit lane</span>
        </button>
      </div>

      {/* Strategy Delta Savings & Lapped Car Procedures */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Pit Stop Delta Loss Card (Left 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <span className="font-bold text-slate-300 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <Timer className="w-4 h-4 text-amber-400" />
            PIT WINDOW TIME LOSS ANALYSIS
          </span>

          <div className="flex justify-between items-baseline">
            <span className="text-slate-400">Current Pit Loss Time:</span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-black text-white">{currentPitLossS}</span>
              <span className="text-xs text-slate-400">SECONDS</span>
            </div>
          </div>

          <div className="flex justify-between items-baseline">
            <span className="text-slate-400">Strategy Delta Savings vs Green Flag:</span>
            <span className="text-lg font-bold text-emerald-400">+{deltaSavingsS}s Saved</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
            <strong>Strategy Call:</strong> {activeScMode === 'SC' ? 'CHEAP PIT STOP! Double stack box box window open.' : activeScMode === 'VSC' ? 'Moderate pit time advantage. Box if tire wear > 50%.' : 'Standard green flag pit loss applies.'}
          </div>
        </div>

        {/* Lapped Car Protocol Card (Right 6 cols) */}
        <div className="lg:col-span-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between gap-3">
          <span className="font-bold text-slate-300 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <Zap className="w-4 h-4 text-apex-cyan" />
            FIA RESTART UNLAPPING PROTOCOL
          </span>

          <div className="flex flex-col gap-1 text-slate-300">
            <span>Safety Car In This Lap: <strong className="text-amber-400">{activeScMode === 'SC' ? 'YES' : 'STANDBY'}</strong></span>
            <span>Lapped Cars Status: <strong className={lappedCarsCanOvertake ? 'text-emerald-400' : 'text-slate-400'}>{lappedCarsCanOvertake ? 'LAPPED CARS MAY NOW OVERTAKE' : 'HELD IN QUEUE'}</strong></span>
          </div>

          <button
            onClick={handleUnlapLappedCars}
            disabled={activeScMode !== 'SC' || lappedCarsCanOvertake}
            className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-black font-mono text-xs font-bold transition-all active:scale-95 shadow-md shadow-cyan-500/20"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>AUTHORIZE LAPPED CARS OVERTAKE (SC RESTART)</span>
          </button>
        </div>
      </div>
    </div>
  );
};
