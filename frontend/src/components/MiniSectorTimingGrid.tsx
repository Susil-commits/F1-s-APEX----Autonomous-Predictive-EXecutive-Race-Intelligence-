import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Gauge, Sparkles, Activity, Clock } from 'lucide-react';
import { CarState } from '../types/race';

export const MiniSectorTimingGrid: React.FC = () => {
  const { raceState, setSelectedCarId, setInspectedCar } = useRaceStore();

  if (!raceState) return null;

  const { cars } = raceState;
  const playerCar = cars.find((c) => c.is_player) || cars[0];

  // 20 mini-sectors across 3 sectors (S1: 1-7, S2: 8-14, S3: 15-20)
  const miniSectors = Array.from({ length: 20 }).map((_, idx) => {
    const num = idx + 1;
    const sector = num <= 7 ? 1 : num <= 14 ? 2 : 3;
    return { num, sector };
  });

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-400 animate-pulse" />
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
            20 Mini-Sector Micro-Timing Matrix
          </h3>
        </div>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="flex items-center gap-1 text-purple-400 font-bold">
            <span className="w-2 h-2 rounded-full bg-purple-400" /> Session Best
          </span>
          <span className="flex items-center gap-1 text-emerald-400 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-400" /> Personal Best
          </span>
          <span className="flex items-center gap-1 text-yellow-400 font-bold">
            <span className="w-2 h-2 rounded-full bg-yellow-400" /> Slower
          </span>
        </div>
      </div>

      {/* Driver Micro-Sector Rows */}
      <div className="space-y-2 overflow-x-auto">
        {cars.slice(0, 5).map((car: CarState) => {
          const isPlayer = car.is_player;

          return (
            <div
              key={car.car_id}
              onClick={() => {
                setSelectedCarId(car.car_id);
                setInspectedCar(car);
              }}
              className={`p-2 rounded-lg border transition-all cursor-pointer select-none flex items-center justify-between gap-3 ${
                isPlayer
                  ? 'bg-cyan-950/30 border-cyan-500/40 hover:bg-cyan-900/40'
                  : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60'
              }`}
            >
              {/* Driver Tag */}
              <div className="w-28 shrink-0 flex items-center gap-1.5">
                <span className="font-bold text-slate-400 text-[10px]">P{car.position}</span>
                <span className={`font-sans font-bold text-xs truncate ${isPlayer ? 'text-cyan-400' : 'text-slate-200'}`}>
                  {car.driver_name.split(' ')[1] || car.driver_name}
                </span>
              </div>

              {/* 20 Mini-Sector Blocks */}
              <div className="flex items-center gap-1 flex-1 justify-end">
                {miniSectors.map((ms) => {
                  // Deterministic seed pattern for realism based on driver & position
                  const hash = (car.position * 7 + ms.num * 13 + car.tyre_age_laps) % 10;
                  let color = 'bg-yellow-500';
                  if (car.position === 1 && (ms.num === 4 || ms.num === 11 || ms.num === 18)) {
                    color = 'bg-purple-500 shadow-sm shadow-purple-500/50';
                  } else if (hash > 4 || (isPlayer && hash > 2)) {
                    color = 'bg-emerald-500';
                  }

                  return (
                    <div
                      key={ms.num}
                      title={`Mini-Sector ${ms.num} (Sector ${ms.sector})`}
                      className={`h-4 w-2.5 sm:w-3.5 rounded-xs transition-all ${color} ${
                        ms.num === 7 || ms.num === 14 ? 'mr-1.5' : ''
                      }`}
                    />
                  );
                })}
              </div>

              {/* Last Lap Delta */}
              <div className="w-16 text-right shrink-0 text-[11px] font-bold text-slate-300">
                {car.last_lap_time_s ? `${car.last_lap_time_s.toFixed(2)}s` : '--.--'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
