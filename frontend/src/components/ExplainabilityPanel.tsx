import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Brain, CheckCircle2, Cpu, FileText, Activity, ShieldAlert, Sparkles } from 'lucide-react';

export const ExplainabilityPanel: React.FC = () => {
  const { raceState } = useRaceStore();

  if (!raceState || !raceState.active_decision) return null;

  const decision = raceState.active_decision;

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col h-full border border-apex-border shadow-2xl">
      {/* Title */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Explainability & Decision Trail
          </h3>
        </div>
        <span className="text-[10px] font-mono text-purple-300 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-800/50 font-bold">
          State ➔ Model ➔ Decision
        </span>
      </div>

      {/* Primary Factors */}
      <div className="mb-3">
        <span className="text-[10px] uppercase font-mono font-bold text-slate-400 block mb-2 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-slate-400" /> Dominant Strategic Drivers
        </span>
        <div className="space-y-1.5 font-sans text-xs">
          {decision.primary_factors.map((factor, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 p-2 rounded-lg bg-slate-900/70 border border-slate-800/80 text-slate-200"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
              <span className="leading-snug text-[11.5px]">{factor}</span>
            </div>
          ))}
        </div>

        {decision.commentary && (
          <div className="mt-2.5 p-2 rounded-lg bg-purple-950/30 border border-purple-800/50 flex items-start gap-2">
            <Sparkles className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
            <div className="text-[11px] font-sans">
              <span className="font-mono text-[9px] uppercase tracking-wider text-purple-300 font-bold block">
                Radio Translation (LLM Transcriber)
              </span>
              <span className="text-purple-100 italic">"{decision.commentary}"</span>
            </div>
          </div>
        )}
      </div>

      {/* Intelligence Consensus Comparison */}
      <div className="grid grid-cols-2 gap-2 mt-auto pt-2 border-t border-slate-800/80 font-mono text-[11px]">
        {/* Rule Engine */}
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 uppercase font-sans mb-1 font-semibold">
            <Cpu className="w-3 h-3 text-cyan-400" /> Rule Engine Baseline
          </div>
          <span className="font-bold text-slate-200 block truncate">
            {decision.rule_engine_action}
          </span>
        </div>

        {/* DQN RL Agent */}
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 uppercase font-sans mb-1 font-semibold">
            <Brain className="w-3 h-3 text-purple-400" /> DQN Policy Consensus
          </div>
          <span className="font-bold text-purple-300 block truncate">
            {decision.dqn_action || decision.rule_engine_action}
          </span>
        </div>
      </div>

      {/* Tyre Cliff & Window Status */}
      <div className="grid grid-cols-2 gap-2 mt-2 font-mono text-[11px]">
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] text-slate-400 uppercase font-sans block font-semibold">
            Pit Window
          </span>
          <span className="font-bold text-amber-300">{decision.pit_window_status}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className="text-[9.5px] text-slate-400 uppercase font-sans block font-semibold">
            Cliff Risk Level
          </span>
          <span
            className={`font-bold ${
              decision.tyre_cliff_risk === 'CRITICAL'
                ? 'text-rose-400 glow-red'
                : decision.tyre_cliff_risk === 'HIGH'
                ? 'text-amber-400'
                : 'text-emerald-400'
            }`}
          >
            {decision.tyre_cliff_risk}
          </span>
        </div>
      </div>
    </div>
  );
};
