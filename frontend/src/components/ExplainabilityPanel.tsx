import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Brain, CheckCircle2, Cpu, FileText, AlertCircle } from 'lucide-react';

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
          <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-200">
            Explainability & Decision Trail
          </h3>
        </div>
        <span className="text-[10px] font-mono text-purple-300 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-800/50">
          State ➔ Logic ➔ Decision
        </span>
      </div>

      {/* Primary Factors */}
      <div className="mb-3">
        <span className="text-[10px] uppercase font-mono font-semibold text-slate-400 block mb-1.5 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-slate-400" /> Dominant Strategic Factors
        </span>
        <div className="space-y-1.5 font-sans text-xs">
          {decision.primary_factors.map((factor, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 p-2 rounded bg-slate-900/60 border border-slate-800/80 text-slate-300"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
              <span className="leading-snug">{factor}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Intelligence Consensus Comparison */}
      <div className="grid grid-cols-2 gap-2 mt-auto pt-2 border-t border-slate-800/80 font-mono text-[11px]">
        {/* Rule Engine */}
        <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 uppercase font-sans mb-0.5">
            <Cpu className="w-3 h-3 text-cyan-400" /> Rule Engine Call
          </div>
          <span className="font-bold text-slate-200 block truncate">
            {decision.rule_engine_action}
          </span>
        </div>

        {/* DQN RL Agent */}
        <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 uppercase font-sans mb-0.5">
            <Brain className="w-3 h-3 text-purple-400" /> DQN Policy Call
          </div>
          <span className="font-bold text-purple-300 block truncate">
            {decision.dqn_action || decision.rule_engine_action}
          </span>
        </div>
      </div>

      {/* Tyre Cliff & Window Status */}
      <div className="grid grid-cols-2 gap-2 mt-2 font-mono text-[11px]">
        <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-sans block">Pit Window</span>
          <span className="font-bold text-amber-300">{decision.pit_window_status}</span>
        </div>
        <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-sans block">Cliff Risk</span>
          <span
            className={`font-bold ${
              decision.tyre_cliff_risk === 'CRITICAL'
                ? 'text-rose-400'
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
