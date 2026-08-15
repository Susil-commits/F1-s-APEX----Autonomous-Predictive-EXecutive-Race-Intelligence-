import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Layers, CheckCircle2, Clock, Zap, Disc } from 'lucide-react';
import { TyreCompound } from '../types/race';

const COMPOUND_COLORS: Record<TyreCompound, { bg: string; text: string; label: string; border: string }> = {
  SOFT: { bg: 'bg-rose-500', text: 'text-white', label: 'SOFT', border: 'border-rose-400' },
  MEDIUM: { bg: 'bg-yellow-500', text: 'text-black', label: 'MEDIUM', border: 'border-yellow-400' },
  HARD: { bg: 'bg-slate-300', text: 'text-black', label: 'HARD', border: 'border-white' },
  INTERMEDIATE: { bg: 'bg-emerald-500', text: 'text-black', label: 'INTER', border: 'border-emerald-400' },
  WET: { bg: 'bg-blue-500', text: 'text-white', label: 'WET', border: 'border-blue-400' },
};

export const StintStrategyPlanner: React.FC = () => {
  const { raceState } = useRaceStore();

  if (!raceState) return null;

  const { current_lap, total_laps, track } = raceState;
  const playerCar = raceState.cars.find((c) => c.is_player) || raceState.cars[0];

  // Dynamic strategy stints
  const strategies = [
    {
      id: 'strat_1stop_med_hard',
      name: 'Plan A: 1-Stop Standard (Optimal)',
      isRecommended: true,
      stints: [
        { compound: 'MEDIUM' as TyreCompound, startLap: 1, endLap: Math.round(total_laps * 0.42) },
        { compound: 'HARD' as TyreCompound, startLap: Math.round(total_laps * 0.42) + 1, endLap: total_laps },
      ],
      pitWindow: { start: Math.round(total_laps * 0.38), end: Math.round(total_laps * 0.46) },
      projectedDeltaS: 0.0,
    },
    {
      id: 'strat_2stop_soft_med_soft',
      name: 'Plan B: 2-Stop Attack Pace',
      isRecommended: false,
      stints: [
        { compound: 'SOFT' as TyreCompound, startLap: 1, endLap: Math.round(total_laps * 0.28) },
        { compound: 'MEDIUM' as TyreCompound, startLap: Math.round(total_laps * 0.28) + 1, endLap: Math.round(total_laps * 0.65) },
        { compound: 'SOFT' as TyreCompound, startLap: Math.round(total_laps * 0.65) + 1, endLap: total_laps },
      ],
      pitWindow: { start: Math.round(total_laps * 0.25), end: Math.round(total_laps * 0.31) },
      projectedDeltaS: +3.8,
    },
    {
      id: 'strat_1stop_hard_med',
      name: 'Plan C: Overcut Inverted (Hard ➔ Medium)',
      isRecommended: false,
      stints: [
        { compound: 'HARD' as TyreCompound, startLap: 1, endLap: Math.round(total_laps * 0.58) },
        { compound: 'MEDIUM' as TyreCompound, startLap: Math.round(total_laps * 0.58) + 1, endLap: total_laps },
      ],
      pitWindow: { start: Math.round(total_laps * 0.54), end: Math.round(total_laps * 0.62) },
      projectedDeltaS: +1.4,
    },
  ];

  const currentLapPct = Math.min(100, Math.max(0, (current_lap / total_laps) * 100));

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col border border-apex-border shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-apex-cyan" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            Stint Strategy Gantt Matrix
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-400 font-bold">
          Total Distance: {total_laps} Laps
        </span>
      </div>

      {/* Strategy Bars */}
      <div className="space-y-4">
        {strategies.map((strat) => {
          return (
            <div key={strat.id} className="flex flex-col gap-1.5 font-mono text-xs">
              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-1.5">
                  {strat.isRecommended && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  )}
                  <span
                    className={`font-sans font-bold ${
                      strat.isRecommended ? 'text-emerald-300' : 'text-slate-300'
                    }`}
                  >
                    {strat.name}
                  </span>
                </div>
                <span
                  className={`text-[10px] ${
                    strat.projectedDeltaS === 0 ? 'text-emerald-400 font-bold' : 'text-slate-400'
                  }`}
                >
                  {strat.projectedDeltaS === 0 ? 'FASTEST' : `+${strat.projectedDeltaS}s`}
                </span>
              </div>

              {/* Gantt Bar Container */}
              <div className="relative w-full h-7 bg-slate-950 rounded-lg border border-slate-800 flex overflow-hidden select-none">
                {/* Stints Segments */}
                {strat.stints.map((stint, idx) => {
                  const stintLength = stint.endLap - stint.startLap + 1;
                  const stintPct = (stintLength / total_laps) * 100;
                  const cMeta = COMPOUND_COLORS[stint.compound] || COMPOUND_COLORS.MEDIUM;

                  return (
                    <div
                      key={idx}
                      style={{ width: `${stintPct}%` }}
                      className={`h-full ${cMeta.bg} ${cMeta.text} flex items-center justify-center font-bold text-[10px] border-r border-black/30 truncate px-1`}
                    >
                      <span className="truncate">
                        {cMeta.label} ({stint.startLap}-{stint.endLap}L)
                      </span>
                    </div>
                  );
                })}

                {/* Optimal Pit Window Box Highlight */}
                <div
                  style={{
                    left: `${(strat.pitWindow.start / total_laps) * 100}%`,
                    width: `${((strat.pitWindow.end - strat.pitWindow.start) / total_laps) * 100}%`,
                  }}
                  className="absolute inset-y-0 border-2 border-dashed border-cyan-400 bg-cyan-400/20 pointer-events-none z-10"
                  title={`Pit Window: Lap ${strat.pitWindow.start} - ${strat.pitWindow.end}`}
                />

                {/* Live Current Lap Marker */}
                <div
                  style={{ left: `${currentLapPct}%` }}
                  className="absolute top-0 bottom-0 w-1 bg-white shadow-lg shadow-white z-20 pointer-events-none"
                />
              </div>

              {/* Window metadata */}
              <div className="flex justify-between text-[9px] text-slate-500 px-1">
                <span>Start</span>
                <span className="text-cyan-400/80 font-bold">
                  Pit Window: Laps {strat.pitWindow.start}-{strat.pitWindow.end}
                </span>
                <span>Lap {total_laps}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
