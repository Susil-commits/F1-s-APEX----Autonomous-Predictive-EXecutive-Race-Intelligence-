import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { TyreCompound, CarState } from '../types/race';
import { Disc, ChevronRight } from 'lucide-react';

const COMPOUND_COLORS: Record<TyreCompound, { bg: string; text: string; label: string; border: string }> = {
  SOFT: { bg: 'bg-rose-500/20', text: 'text-rose-400', label: 'S', border: 'border-rose-500/40' },
  MEDIUM: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'M', border: 'border-yellow-500/40' },
  HARD: { bg: 'bg-slate-300/20', text: 'text-slate-100', label: 'H', border: 'border-slate-300/40' },
  INTERMEDIATE: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'I', border: 'border-emerald-500/40' },
  WET: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'W', border: 'border-blue-500/40' },
};

export const TimingTower: React.FC = () => {
  const { raceState, selectedCarId, setSelectedCarId } = useRaceStore();

  if (!raceState) return null;

  const { cars } = raceState;

  // Find best overall lap time for purple sector highlight
  let overallBestLap: number | null = null;
  cars.forEach((c) => {
    if (c.best_lap_time_s) {
      if (overallBestLap === null || c.best_lap_time_s < overallBestLap) {
        overallBestLap = c.best_lap_time_s;
      }
    }
  });

  return (
    <div className="glass-panel rounded-xl overflow-hidden flex flex-col h-full border border-apex-border shadow-2xl">
      {/* Header */}
      <div className="bg-slate-900/90 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-sm bg-apex-cyan" />
          <h2 className="text-xs font-extrabold uppercase tracking-widest text-slate-200">
            Timing Tower
          </h2>
        </div>
        <span className="text-[11px] font-mono text-slate-400">{cars.length} Cars Active</span>
      </div>

      {/* Column Headers */}
      <div className="grid grid-cols-12 gap-1 px-3 py-2 text-[10px] uppercase font-mono font-semibold text-slate-500 bg-slate-950/40 border-b border-slate-800/60">
        <div className="col-span-1 text-center">Pos</div>
        <div className="col-span-4">Driver / Team</div>
        <div className="col-span-2 text-right">Interval</div>
        <div className="col-span-3 text-center">Tyre / Wear</div>
        <div className="col-span-2 text-right">Last Lap</div>
      </div>

      {/* Drivers List */}
      <div className="divide-y divide-slate-800/40 overflow-y-auto flex-1 font-mono text-xs">
        {cars.map((car: CarState) => {
          const isSelected = selectedCarId === car.car_id;
          const compoundMeta = COMPOUND_COLORS[car.tyre_compound] || COMPOUND_COLORS.MEDIUM;
          const isFastestLap = overallBestLap && car.best_lap_time_s && Math.abs(car.best_lap_time_s - overallBestLap) < 0.001;

          // Wear color gradient
          let wearColor = 'bg-emerald-500';
          let wearTextColor = 'text-emerald-400';
          if (car.tyre_wear_pct >= 75) {
            wearColor = 'bg-rose-500 animate-pulse';
            wearTextColor = 'text-rose-400 font-bold';
          } else if (car.tyre_wear_pct >= 50) {
            wearColor = 'bg-amber-500';
            wearTextColor = 'text-amber-400';
          }

          return (
            <div
              key={car.car_id}
              onClick={() => setSelectedCarId(isSelected ? null : car.car_id)}
              className={`grid grid-cols-12 gap-1 px-3 py-2 items-center transition-all cursor-pointer select-none ${
                car.is_player
                  ? 'bg-cyan-950/30 border-l-2 border-apex-cyan hover:bg-cyan-900/40'
                  : isSelected
                  ? 'bg-slate-800/60 hover:bg-slate-800/80'
                  : 'hover:bg-slate-800/30'
              }`}
            >
              {/* Position */}
              <div className="col-span-1 flex items-center justify-center font-bold text-slate-200">
                <span
                  className={`w-5 h-5 rounded flex items-center justify-center text-[11px] ${
                    car.position === 1
                      ? 'bg-yellow-500/20 text-yellow-300 font-extrabold border border-yellow-500/40'
                      : car.position <= 3
                      ? 'bg-slate-700/50 text-slate-200'
                      : 'text-slate-400'
                  }`}
                >
                  {car.position}
                </span>
              </div>

              {/* Driver & Team */}
              <div className="col-span-4 flex flex-col truncate pr-1">
                <div className="flex items-center gap-1.5 truncate">
                  <span className={`font-sans font-bold truncate text-[11px] ${car.is_player ? 'text-apex-cyan' : 'text-slate-200'}`}>
                    {car.driver_name}
                  </span>
                  {car.is_player && (
                    <span className="text-[9px] font-mono uppercase px-1 py-0.2 rounded bg-cyan-500/20 text-apex-cyan font-semibold">
                      YOU
                    </span>
                  )}
                  {car.in_pit && (
                    <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-amber-500/30 text-amber-300 font-bold animate-pulse">
                      PIT
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-slate-500 truncate font-sans">
                  {car.team_name}
                </span>
              </div>

              {/* Interval / Gap to Leader */}
              <div className="col-span-2 text-right text-[11px] text-slate-300">
                {car.position === 1 ? (
                  <span className="text-yellow-400 font-semibold text-[10px] uppercase">LEADER</span>
                ) : (
                  <span>+{car.gap_to_leader_s.toFixed(2)}s</span>
                )}
              </div>

              {/* Tyre Compound & Wear Bar */}
              <div className="col-span-3 flex flex-col items-center gap-1 px-1">
                <div className="flex items-center justify-between w-full text-[10px]">
                  <span className={`px-1 rounded border text-[9px] font-bold ${compoundMeta.bg} ${compoundMeta.text} ${compoundMeta.border}`}>
                    {compoundMeta.label} <span className="text-[8px] opacity-75">{car.tyre_age_laps}L</span>
                  </span>
                  <span className={`text-[10px] ${wearTextColor}`}>
                    {car.tyre_wear_pct.toFixed(0)}%
                  </span>
                </div>
                {/* Visual Wear Progress Bar */}
                <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${wearColor} transition-all duration-300`}
                    style={{ width: `${Math.min(100, car.tyre_wear_pct)}%` }}
                  />
                </div>
              </div>

              {/* Last Lap Time */}
              <div className="col-span-2 text-right">
                <span
                  className={`text-[11px] ${
                    isFastestLap
                      ? 'text-purple-400 font-bold glow-yellow'
                      : 'text-slate-300'
                  }`}
                >
                  {car.last_lap_time_s ? car.last_lap_time_s.toFixed(2) : '--.--'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
