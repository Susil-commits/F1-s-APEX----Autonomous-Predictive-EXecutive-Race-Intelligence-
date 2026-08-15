import React, { useState } from 'react';
import { useRaceStore } from '../store/raceStore';
import { Layers, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { TyreCompound } from '../types/race';

export const PitStrategyIsochroneMatrix: React.FC = () => {
  const { raceState } = useRaceStore();
  const [selectedCell, setSelectedCell] = useState<{ lap: number; compound: TyreCompound } | null>(
    null
  );

  if (!raceState) return null;

  const totalLaps = raceState.track.total_laps;
  const pitLaps = [14, 18, 22, 26, 30, 34, 38];
  const compounds: TyreCompound[] = ['SOFT', 'MEDIUM', 'HARD'];

  // Global optimal pit stop: Lap 22 on MEDIUM
  const optimalLap = 22;
  const optimalCompound: TyreCompound = 'MEDIUM';

  const calculateCellDelta = (lap: number, comp: TyreCompound): number => {
    const lapDiff = Math.abs(lap - optimalLap);
    const compPenalty = comp === 'MEDIUM' ? 0 : comp === 'HARD' ? 1.4 : 3.8;
    const wearPenalty = lap > 28 ? (lap - 28) * 0.9 : 0;
    return parseFloat((lapDiff * 0.35 + compPenalty + wearPenalty).toFixed(1));
  };

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Layers className="w-5 h-5 text-apex-cyan animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Multi-Lap Pit Strategy Isochrone Surface
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              2D parameter surface mapping total race time delta across pit stop laps & fitted compounds
            </p>
          </div>
        </div>

        <span className="text-[10px] text-emerald-300 bg-emerald-950/60 px-2.5 py-1 rounded border border-emerald-800/60 font-bold flex items-center gap-1">
          <Sparkles className="w-3 h-3" /> Global Minimum Valley
        </span>
      </div>

      {/* Isochrone Matrix Table */}
      <div className="overflow-x-auto mb-3">
        <table className="w-full text-center font-mono text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400">
              <th className="py-2 text-left w-24">Fitted Compound</th>
              {pitLaps.map((lap) => (
                <th key={lap} className="py-2">
                  Lap {lap}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {compounds.map((comp) => (
              <tr key={comp}>
                <td className="py-2.5 text-left font-sans font-bold text-slate-300 text-xs">
                  {comp}
                </td>
                {pitLaps.map((lap) => {
                  const delta = calculateCellDelta(lap, comp);
                  const isOptimal = lap === optimalLap && comp === optimalCompound;
                  const isSelected =
                    selectedCell?.lap === lap && selectedCell?.compound === comp;

                  // Color gradient
                  let cellBg = 'bg-emerald-950/30 text-emerald-300 border-emerald-500/30';
                  if (isOptimal) {
                    cellBg = 'bg-cyan-500 text-black font-black shadow-lg shadow-cyan-500/50 border-white';
                  } else if (delta > 6.0) {
                    cellBg = 'bg-rose-950/30 text-rose-400 border-rose-800/40';
                  } else if (delta > 3.0) {
                    cellBg = 'bg-amber-950/30 text-amber-300 border-amber-800/40';
                  }

                  return (
                    <td key={lap} className="py-1.5 px-1">
                      <button
                        onClick={() => setSelectedCell({ lap, compound: comp })}
                        className={`w-full py-1.5 px-2 rounded-lg border text-center font-bold text-xs transition-all active:scale-95 ${cellBg} ${
                          isSelected && !isOptimal ? 'ring-2 ring-cyan-400' : ''
                        }`}
                      >
                        {isOptimal ? 'OPTIMAL' : `+${delta}s`}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Selected Cell Info / Rationale */}
      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] font-sans text-slate-300 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>
            Global Minimum: <strong>Lap 22 on MEDIUM tyres</strong> minimizes degradation penalty and avoids traffic dirty air.
          </span>
        </div>
        {selectedCell && (
          <span className="font-mono text-amber-400 font-bold">
            Inspecting: Lap {selectedCell.lap} on {selectedCell.compound} (+{calculateCellDelta(selectedCell.lap, selectedCell.compound)}s)
          </span>
        )}
      </div>
    </div>
  );
};
