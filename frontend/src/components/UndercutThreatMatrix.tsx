import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { ShieldAlert, ShieldCheck, Crosshair, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { CarState } from '../types/race';

export const UndercutThreatMatrix: React.FC = () => {
  const { raceState, setSelectedCarId, setInspectedCar } = useRaceStore();

  if (!raceState) return null;

  const { cars } = raceState;
  const playerCar = cars.find((c) => c.is_player) || cars[0];

  // Evaluate threat profiles for top competitors
  const competitorThreats = cars
    .filter((c) => !c.is_player)
    .slice(0, 6)
    .map((rival) => {
      const gapToPlayer = rival.position > playerCar.position
        ? rival.gap_to_leader_s - playerCar.gap_to_leader_s
        : playerCar.gap_to_leader_s - rival.gap_to_leader_s;

      const isBehind = rival.position > playerCar.position;
      const tyreAgeDiff = rival.tyre_age_laps - playerCar.tyre_age_laps;

      let threatType: 'UNDERCUT_RISK' | 'OVERCUT_CHANCE' | 'SAFE' = 'SAFE';
      let threatLevel: 'HIGH' | 'MED' | 'LOW' = 'LOW';
      let advice = 'Maintain current pace delta.';

      if (isBehind && gapToPlayer < 2.2) {
        threatType = 'UNDERCUT_RISK';
        threatLevel = gapToPlayer < 1.4 ? 'HIGH' : 'MED';
        advice = 'Cover undercut immediately or push out-of-DRS window.';
      } else if (!isBehind && gapToPlayer < 2.5 && tyreAgeDiff > 4) {
        threatType = 'OVERCUT_CHANCE';
        threatLevel = 'HIGH';
        advice = 'Stay out in clean air to overcut on fresh rubber.';
      }

      return {
        ...rival,
        gapToPlayer: Math.abs(gapToPlayer),
        isBehind,
        threatType,
        threatLevel,
        advice,
      };
    });

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col border border-apex-border shadow-2xl font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <Crosshair className="w-5 h-5 text-rose-400 animate-pulse" />
          <div>
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200">
              Competitor Undercut & Overcut Threat Radar
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans">
              Real-time vulnerability analysis assessing pit box overlap and out-lap pace deltas
            </p>
          </div>
        </div>

        <span className="text-[10px] text-rose-300 bg-rose-950/60 px-2.5 py-1 rounded border border-rose-800/60 font-bold flex items-center gap-1">
          <ShieldAlert className="w-3 h-3 text-rose-400" /> Active Threat Scan
        </span>
      </div>

      {/* Threat Rows */}
      <div className="space-y-2">
        {competitorThreats.map((rival) => {
          const isHighThreat = rival.threatLevel === 'HIGH';
          const isUndercut = rival.threatType === 'UNDERCUT_RISK';
          const isOvercut = rival.threatType === 'OVERCUT_CHANCE';

          return (
            <div
              key={rival.car_id}
              onClick={() => {
                setSelectedCarId(rival.car_id);
                setInspectedCar(rival);
              }}
              className={`p-3 rounded-lg border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                isHighThreat && isUndercut
                  ? 'bg-rose-950/30 border-rose-500/50 hover:bg-rose-900/40'
                  : isHighThreat && isOvercut
                  ? 'bg-emerald-950/30 border-emerald-500/50 hover:bg-emerald-900/40'
                  : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60'
              }`}
            >
              {/* Driver & Gap */}
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-950 flex items-center justify-center font-bold text-xs border border-slate-800 text-slate-200">
                  P{rival.position}
                </div>
                <div>
                  <span className="font-sans font-bold text-slate-100 block text-xs">
                    {rival.driver_name} ({rival.team_name})
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {rival.isBehind ? 'Behind' : 'Ahead'} by +{rival.gapToPlayer.toFixed(2)}s • Tyre: {rival.tyre_compound} ({rival.tyre_age_laps}L)
                  </span>
                </div>
              </div>

              {/* Status Badge & Tactical Directive */}
              <div className="flex items-center gap-3 justify-between sm:justify-end">
                <div className="text-right">
                  <span
                    className={`inline-flex items-center gap-1 text-[9.5px] font-bold uppercase px-2 py-0.5 rounded border ${
                      isUndercut
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : isOvercut
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {isUndercut && <ArrowDownRight className="w-3 h-3 text-rose-400" />}
                    {isOvercut && <ArrowUpRight className="w-3 h-3 text-emerald-400" />}
                    {rival.threatType.replace('_', ' ')} [{rival.threatLevel}]
                  </span>
                  <p className="text-[10px] text-slate-400 font-sans mt-0.5">{rival.advice}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
