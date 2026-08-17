import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { UserCheck, ShieldAlert, Award, Activity } from 'lucide-react';
import { DriverBattleRadar } from './DriverBattleRadar';

export const DriverIntelligenceView: React.FC = () => {
  const { raceState } = useRaceStore();
  if (!raceState) return null;

  const player = raceState.cars.find((c) => c.is_player) || raceState.cars[0];
  const rival = raceState.cars.find((c) => c.position === (player.position === 1 ? 2 : player.position - 1)) || raceState.cars[1];

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">Driver Behavioral Analytics & Pressure Modeling</h2>
            <p className="text-xs text-slate-400">Fatigue curves, consistency tracking, and mistake probabilities under tactical pressure</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800">
          <h3 className="text-xs font-bold text-slate-300 font-sans mb-3">Head-to-Head Driver Battle Radar</h3>
          <DriverBattleRadar />
        </div>

        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-300 font-sans">Grid Driver Behavioral Matrix</h3>
          <div className="space-y-2 overflow-y-auto max-h-[380px] pr-1">
            {raceState.cars.map((car) => {
              const drv = car.driver_state;
              return (
                <div key={car.car_id} className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-cyan-400 w-6">P{car.position}</span>
                    <div>
                      <span className="font-bold text-white font-sans">{car.driver_name}</span>
                      <p className="text-[10px] text-slate-500">{car.team_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="text-slate-400">Aggression: <b className="text-amber-400">{((drv?.aggression || 0.8) * 100).toFixed(0)}%</b></span>
                    <span className="text-slate-400">Defence: <b className="text-blue-400">{((drv?.defence_strength || 0.8) * 100).toFixed(0)}%</b></span>
                    <span className="text-slate-400">Mistake Risk: <b className="text-red-400">{((drv?.mistake_probability || 0.02) * 100).toFixed(1)}%</b></span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
