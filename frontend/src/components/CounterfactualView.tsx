import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { GitCompare, Award, CheckCircle, AlertTriangle, Play, Sparkles, FastForward } from 'lucide-react';
import { StrategyAction } from '../types/race';

const FORKABLE_ACTIONS = [
  'PIT_SOFT',
  'PIT_MEDIUM',
  'PIT_HARD',
  'PIT_INTER',
  'PIT_WET',
  'PUSH',
  'CONSERVE',
];

export const CounterfactualView: React.FC = () => {
  const { raceState } = useRaceStore();
  const [selectedForkAction, setSelectedForkAction] = useState<string>('PIT_MEDIUM');
  const [forkResult, setForkResult] = useState<any | null>(null);
  const [isForking, setIsForking] = useState<boolean>(false);

  if (!raceState?.active_decision?.counterfactual_summary?.alternatives) return null;

  const cf = raceState.active_decision.counterfactual_summary;

  const handleForkTimeline = async () => {
    setIsForking(true);
    try {
      const res = await fetch('/api/strategy/fork-counterfactual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          proposed_action: selectedForkAction,
          rollout_laps: 5,
          state_payload: raceState,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setForkResult(data);
      }
    } catch (err) {
      console.error('Fork counterfactual error:', err);
    } finally {
      setIsForking(false);
    }
  };

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col h-full border border-apex-border shadow-2xl">
      {/* Title */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Counterfactual "What-If" Analysis
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-400 font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
          {cf.rollout_laps}-Lap Forward Rollout
        </span>
      </div>

      {/* Alternatives Table */}
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left font-mono text-[11px]">
          <thead>
            <tr className="border-b border-slate-800 text-[9.5px] uppercase font-bold text-slate-400">
              <th className="pb-2">Candidate Option</th>
              <th className="pb-2 text-center">Proj Pos</th>
              <th className="pb-2 text-right">Proj Gap</th>
              <th className="pb-2 text-right">Proj Wear</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {cf.alternatives.map((alt: any, idx: number) => {
              const isWinner = alt.strategy === cf.best_strategy;
              return (
                <tr
                  key={idx}
                  className={`transition-colors ${
                    isWinner
                      ? 'bg-emerald-950/40 text-emerald-300 font-bold'
                      : 'text-slate-300 hover:bg-slate-800/30'
                  }`}
                >
                  <td className="py-2 flex items-center gap-1.5 truncate">
                    {isWinner && <Award className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                    <span className="truncate">{alt.strategy}</span>
                  </td>
                  <td className="py-2 text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-black ${
                        isWinner
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm shadow-emerald-500/20'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      P{alt.projected_position}
                    </span>
                  </td>
                  <td className="py-2 text-right text-slate-300 font-bold">
                    +{alt.projected_gap_to_leader.toFixed(1)}s
                  </td>
                  <td className="py-2 text-right">
                    <span
                      className={`${
                        alt.projected_tyre_wear_pct > 75
                          ? 'text-rose-400 font-bold glow-red'
                          : alt.projected_tyre_wear_pct > 50
                          ? 'text-amber-400 font-semibold'
                          : 'text-emerald-400 font-medium'
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

      {/* Timeline Forking Sub-Panel */}
      <div className="mt-3 pt-2.5 border-t border-slate-800 flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <FastForward className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[10.5px] font-bold text-slate-300 font-sans">Fork Action:</span>
          </div>

          <div className="flex items-center gap-1.5">
            <select
              value={selectedForkAction}
              onChange={(e) => setSelectedForkAction(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-cyan-300 font-mono text-[10px] rounded px-2 py-1 focus:outline-none"
            >
              {FORKABLE_ACTIONS.map((act) => (
                <option key={act} value={act}>
                  {act}
                </option>
              ))}
            </select>

            <button
              onClick={handleForkTimeline}
              disabled={isForking}
              className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-[10px] font-bold transition-all disabled:opacity-50"
            >
              {isForking ? 'Simulating...' : 'Simulate 5 Laps'}
            </button>
          </div>
        </div>

        {/* Forking Outcome Result */}
        {forkResult && (
          <div className="p-2 rounded bg-slate-900/90 border border-cyan-800/60 font-mono text-[10.5px] flex items-center justify-between animate-fade-in">
            <div>
              <span className="text-slate-400 text-[9px] block font-sans">ALT POSITION</span>
              <span className="font-black text-cyan-300">P{forkResult.final_alternate_position}</span>
            </div>
            <div>
              <span className="text-slate-400 text-[9px] block font-sans">TIME DELTA</span>
              <span
                className={`font-black ${
                  forkResult.time_delta_advantage_s > 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {forkResult.time_delta_advantage_s > 0 ? `-${forkResult.time_delta_advantage_s}s faster` : `+${Math.abs(forkResult.time_delta_advantage_s)}s slower`}
              </span>
            </div>
            <div>
              <span className="text-slate-400 text-[9px] block font-sans">VERDICT</span>
              <span
                className={`font-bold px-1.5 py-0.5 rounded text-[9px] ${
                  forkResult.verdict === 'FAVORS_PROPOSED'
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {forkResult.verdict}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
