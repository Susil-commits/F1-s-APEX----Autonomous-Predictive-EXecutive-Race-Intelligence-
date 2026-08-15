import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { GitCompare, Award, CheckCircle } from 'lucide-react';

export const CounterfactualView: React.FC = () => {
  const { raceState } = useRaceStore();

  if (!raceState?.active_decision?.counterfactual_summary?.alternatives) return null;

  const cf = raceState.active_decision.counterfactual_summary;

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col h-full border border-apex-border shadow-2xl">
      {/* Title */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-200">
            Counterfactual "What-If" Analysis
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-400">
          {cf.rollout_laps}-Lap Forward Rollout
        </span>
      </div>

      {/* Alternatives Table */}
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left font-mono text-[11px]">
          <thead>
            <tr className="border-b border-slate-800 text-[10px] uppercase font-semibold text-slate-500">
              <th className="pb-1.5">Candidate Strategy</th>
              <th className="pb-1.5 text-center">Proj Pos</th>
              <th className="pb-1.5 text-right">Proj Gap</th>
              <th className="pb-1.5 text-right">Proj Wear</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {cf.alternatives.map((alt, idx) => {
              const isWinner = alt.strategy === cf.best_strategy;
              return (
                <tr
                  key={idx}
                  className={`transition-colors ${
                    isWinner ? 'bg-emerald-950/30 text-emerald-300 font-semibold' : 'text-slate-300'
                  }`}
                >
                  <td className="py-2 flex items-center gap-1.5 truncate">
                    {isWinner && <Award className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                    <span className="truncate">{alt.strategy}</span>
                  </td>
                  <td className="py-2 text-center">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        isWinner
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      P{alt.projected_position}
                    </span>
                  </td>
                  <td className="py-2 text-right text-slate-300">
                    +{alt.projected_gap_to_leader.toFixed(1)}s
                  </td>
                  <td className="py-2 text-right">
                    <span
                      className={`${
                        alt.projected_tyre_wear_pct > 75
                          ? 'text-rose-400 font-bold'
                          : alt.projected_tyre_wear_pct > 50
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      {alt.projected_tyre_wear_pct.toFixed(0)}%
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] font-sans">
        <span className="text-slate-400 flex items-center gap-1">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Optimal simulated path:
        </span>
        <span className="font-bold text-emerald-400 font-mono">{cf.best_strategy}</span>
      </div>
    </div>
  );
};
