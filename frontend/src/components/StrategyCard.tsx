import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { useRaceSocket } from '../hooks/useRaceSocket';
import { StrategyAction } from '../types/race';
import { Zap, AlertTriangle, CheckCircle, ShieldAlert, ArrowUpRight, Flame } from 'lucide-react';
import { audioEngine } from '../utils/audioEngine';

const ACTION_TITLES: Record<StrategyAction, string> = {
  MAINTAIN: 'MAINTAIN CURRENT STINT',
  PUSH: 'ATTACK MODE: SWITCH TO PUSH',
  CONSERVE: 'TYRE MANAGEMENT: CONSERVE',
  PIT_SOFT: 'BOX THIS LAP ➔ SOFT TYRES',
  PIT_MEDIUM: 'BOX THIS LAP ➔ MEDIUM TYRES',
  PIT_HARD: 'BOX THIS LAP ➔ HARD TYRES',
  PIT_INTER: 'BOX THIS LAP ➔ INTERMEDIATES',
  PIT_WET: 'BOX THIS LAP ➔ FULL WETS',
};

const URGENCY_BADGES: Record<string, { bg: string; text: string; border: string; icon: React.ReactNode }> = {
  CRITICAL: { bg: 'bg-rose-500/20', text: 'text-rose-400', border: 'border-rose-500/50', icon: <ShieldAlert className="w-3.5 h-3.5 text-rose-400" /> },
  HIGH: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/50', icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> },
  MEDIUM: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/50', icon: <Zap className="w-3.5 h-3.5 text-cyan-400" /> },
  LOW: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/50', icon: <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> },
};

export const StrategyCard: React.FC = () => {
  const { raceState } = useRaceStore();
  const { applyAction } = useRaceSocket();

  if (!raceState || !raceState.active_decision) return null;

  const decision = raceState.active_decision;
  const urgencyStyle = URGENCY_BADGES[decision.urgency] || URGENCY_BADGES.MEDIUM;
  const actionTitle = ACTION_TITLES[decision.recommendation] || decision.recommendation;

  const isPitCall = decision.recommendation.startsWith('PIT_');

  const handleExecute = (action: StrategyAction) => {
    audioEngine.playRadioBleep();
    applyAction(action);
  };

  return (
    <div
      className={`rounded-xl p-4 flex flex-col border shadow-2xl transition-all ${
        isPitCall
          ? 'bg-gradient-to-br from-rose-950/40 via-slate-900/90 to-slate-900/90 border-rose-500/50 shadow-rose-500/10'
          : 'glass-panel border-apex-cyan/40 shadow-cyan-500/10'
      }`}
    >
      {/* Top Banner */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-apex-cyan animate-ping" />
          <span className="text-[11px] font-black uppercase tracking-widest text-slate-200">
            APEX Decision Intelligence Call
          </span>
        </div>
        <div
          className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded border text-[10px] font-bold uppercase ${urgencyStyle.bg} ${urgencyStyle.text} ${urgencyStyle.border}`}
        >
          {urgencyStyle.icon}
          <span>{decision.urgency} URGENCY</span>
        </div>
      </div>

      {/* Main Executive Call */}
      <div className="my-2">
        <span className="text-[10px] uppercase font-mono font-bold text-slate-400 block mb-1">
          Executive Tactical Directive
        </span>
        <div className="flex items-center justify-between">
          <h2 className="text-base font-black tracking-wide text-white drop-shadow">
            {actionTitle}
          </h2>
          <span className="text-xs font-mono font-bold px-2 py-1 rounded bg-slate-800 text-apex-cyan border border-slate-700">
            {(decision.confidence_score * 100).toFixed(0)}% AI Conf.
          </span>
        </div>

        {/* Live Race Engineer Radio Commentary */}
        {decision.commentary && (
          <div className="mt-2.5 p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-800/50 flex items-start gap-2">
            <button
              onClick={() => audioEngine.speakRadioMessage(decision.commentary || '')}
              className="mt-0.5 p-1 rounded bg-cyan-900/60 hover:bg-cyan-800 text-cyan-300 transition-all active:scale-95 shrink-0"
              title="Replay Race Engineer Radio"
            >
              <Zap className="w-3.5 h-3.5" />
            </button>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-[9.5px] font-mono uppercase tracking-wider text-cyan-400 font-bold">
                  Race Engineer Radio
                </span>
                <span className="text-[9px] font-mono text-slate-400">TEAM COMMS</span>
              </div>
              <p className="text-xs font-sans text-cyan-100 italic mt-0.5 leading-snug">
                "{decision.commentary}"
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Quick Action Button */}
      <button
        onClick={() => handleExecute(decision.recommendation)}
        className="w-full mt-3 py-2.5 px-4 rounded-lg font-black text-xs uppercase tracking-wider flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 via-teal-400 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black shadow-lg shadow-cyan-500/25 transition-all active:scale-[0.98]"
      >
        <span>Confirm & Execute Strategy</span>
        <ArrowUpRight className="w-4 h-4" />
      </button>

      {/* Manual Strategy Overrides Grid */}
      <div className="mt-4 pt-3 border-t border-slate-800">
        <span className="text-[10px] uppercase font-mono text-slate-500 block mb-2 font-bold">
          Pit Wall Tactical Overrides
        </span>
        <div className="grid grid-cols-4 gap-1.5 font-mono text-[10px]">
          <button
            onClick={() => handleExecute('PUSH')}
            className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-center font-bold active:scale-95"
          >
            PUSH
          </button>
          <button
            onClick={() => handleExecute('CONSERVE')}
            className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-center font-bold active:scale-95"
          >
            CONSERVE
          </button>
          <button
            onClick={() => handleExecute('PIT_SOFT')}
            className="p-1.5 rounded bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800/60 text-center font-bold active:scale-95"
          >
            BOX SOFT
          </button>
          <button
            onClick={() => handleExecute('PIT_MEDIUM')}
            className="p-1.5 rounded bg-yellow-950/60 hover:bg-yellow-900 text-yellow-300 border border-yellow-800/60 text-center font-bold active:scale-95"
          >
            BOX MED
          </button>
          <button
            onClick={() => handleExecute('PIT_HARD')}
            className="p-1.5 rounded bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-600 text-center font-bold active:scale-95"
          >
            BOX HARD
          </button>
          <button
            onClick={() => handleExecute('PIT_INTER')}
            className="p-1.5 rounded bg-emerald-950/60 hover:bg-emerald-900 text-emerald-300 border border-emerald-800/60 text-center font-bold active:scale-95"
          >
            BOX INTER
          </button>
          <button
            onClick={() => handleExecute('PIT_WET')}
            className="p-1.5 rounded bg-blue-950/60 hover:bg-blue-900 text-blue-300 border border-blue-800/60 text-center font-bold active:scale-95"
          >
            BOX WET
          </button>
          <button
            onClick={() => handleExecute('MAINTAIN')}
            className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 text-center active:scale-95"
          >
            STAY OUT
          </button>
        </div>
      </div>
    </div>
  );
};
