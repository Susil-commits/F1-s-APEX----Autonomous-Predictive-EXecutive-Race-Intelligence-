import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Trophy, TrendingUp, TrendingDown, Minus, ShieldCheck, Flag } from 'lucide-react';
import { CarState } from '../types/race';

const F1_POINTS_MAP = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1];

const BASE_CHAMPIONSHIP_POINTS: Record<string, number> = {
  ver_01: 275,
  nor_04: 250,
  lec_16: 220,
  pia_81: 195,
  apex_01: 210,
  ham_44: 160,
  rus_63: 155,
  sai_55: 145,
  alo_14: 70,
  alb_23: 28,
};

export const ChampionshipStandings: React.FC = () => {
  const { raceState } = useRaceStore();

  if (!raceState) return null;

  const { cars } = raceState;

  // Find fastest lap holder for +1 bonus point
  let fastestLapCarId: string | null = null;
  let minLapTime: number | null = null;
  cars.forEach((c) => {
    if (c.best_lap_time_s) {
      if (minLapTime === null || c.best_lap_time_s < minLapTime) {
        minLapTime = c.best_lap_time_s;
        fastestLapCarId = c.car_id;
      }
    }
  });

  // Calculate live virtual points
  const liveStandings = cars.map((car) => {
    const basePts = BASE_CHAMPIONSHIP_POINTS[car.car_id] || 100;
    const racePts = F1_POINTS_MAP[car.position - 1] || 0;
    const bonusFastest = car.car_id === fastestLapCarId && car.position <= 10 ? 1 : 0;
    const totalPts = basePts + racePts + bonusFastest;

    return {
      ...car,
      racePts,
      bonusFastest,
      totalPts,
    };
  });

  // Sort by total championship points
  liveStandings.sort((a, b) => b.totalPts - a.totalPts);

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Trophy className="w-5 h-5 text-yellow-400 animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Live World Championship Standings
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              Dynamic Drivers' Championship classification factoring live race points & fastest lap
            </p>
          </div>
        </div>

        <span className="text-[10px] text-yellow-300 bg-yellow-950/60 px-2.5 py-1 rounded border border-yellow-800/60 font-bold">
          FIA Live Standings
        </span>
      </div>

      {/* Standings Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-[11px]">
          <thead>
            <tr className="border-b border-slate-800 text-[9.5px] uppercase font-bold text-slate-400">
              <th className="pb-2 text-center w-8">Pos</th>
              <th className="pb-2">Driver</th>
              <th className="pb-2">Team</th>
              <th className="pb-2 text-center">Track Pos</th>
              <th className="pb-2 text-right">Race Pts</th>
              <th className="pb-2 text-right font-black text-white">Total Pts</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {liveStandings.map((driver, idx) => {
              const rank = idx + 1;
              const isPlayer = driver.is_player;

              return (
                <tr
                  key={driver.car_id}
                  className={`transition-colors ${
                    isPlayer
                      ? 'bg-cyan-950/30 font-bold text-cyan-200'
                      : 'text-slate-300 hover:bg-slate-800/40'
                  }`}
                >
                  <td className="py-2 text-center font-bold">
                    <span
                      className={`inline-block w-5 h-5 rounded text-center leading-5 text-[10px] font-black ${
                        rank === 1
                          ? 'bg-yellow-500 text-black'
                          : rank <= 3
                          ? 'bg-slate-700 text-white'
                          : 'text-slate-400'
                      }`}
                    >
                      {rank}
                    </span>
                  </td>
                  <td className="py-2 font-sans font-bold flex items-center gap-1.5 truncate">
                    <span className={isPlayer ? 'text-apex-cyan' : 'text-slate-200'}>
                      {driver.driver_name}
                    </span>
                    {driver.bonusFastest === 1 && (
                      <span className="text-[8px] font-mono uppercase px-1 py-0.2 rounded bg-purple-950 text-purple-300 border border-purple-800 font-bold">
                        +1 FL
                      </span>
                    )}
                  </td>
                  <td className="py-2 text-slate-400 truncate text-[10px]">{driver.team_name}</td>
                  <td className="py-2 text-center">
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-bold">
                      P{driver.position}
                    </span>
                  </td>
                  <td className="py-2 text-right text-emerald-400 font-bold">
                    +{driver.racePts + driver.bonusFastest}
                  </td>
                  <td className="py-2 text-right font-black text-white text-xs">
                    {driver.totalPts}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
