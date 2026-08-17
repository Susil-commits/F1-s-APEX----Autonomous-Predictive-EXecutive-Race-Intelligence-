import React from 'react';
import { useRaceStore } from '../store/raceStore';
import { Users, Target, Shield, AlertTriangle } from 'lucide-react';
import { UndercutThreatMatrix } from './UndercutThreatMatrix';
import { PitStrategyIsochroneMatrix } from './PitStrategyIsochroneMatrix';

export const OpponentIntelligenceView: React.FC = () => {
  const { raceState } = useRaceStore();
  if (!raceState) return null;

  const opponents = raceState.opponents || [];

  return (
    <div className="flex flex-col gap-4 p-2 font-mono">
      <div className="flex items-center justify-between bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-sans">Opponent Tactics & Undercut Intelligence</h2>
            <p className="text-xs text-slate-400">Tactical pit window modeling, attack likelihood, and strategy intent prediction</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-xs rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
            {raceState.cars.length} Cars Tracked
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800">
          <h3 className="text-xs font-bold text-slate-300 font-sans mb-3">Undercut Threat Matrix</h3>
          <UndercutThreatMatrix />
        </div>

        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800">
          <h3 className="text-xs font-bold text-slate-300 font-sans mb-3">Pit Strategy Isochrone Windows</h3>
          <PitStrategyIsochroneMatrix />
        </div>
      </div>

      {opponents.length > 0 && (
        <div className="bg-slate-950/90 p-4 rounded-xl border border-slate-800 flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-300 font-sans">Rival Strategy Intent Predictions</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="p-2">POS</th>
                  <th className="p-2">DRIVER</th>
                  <th className="p-2">INTENT</th>
                  <th className="p-2">PIT PROB (1-2 LAPS)</th>
                  <th className="p-2">ATTACK PROB</th>
                  <th className="p-2">PACE DELTA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {opponents.map((op) => (
                  <tr key={op.car_id} className="hover:bg-slate-900/40">
                    <td className="p-2 font-bold text-cyan-400">P{op.position}</td>
                    <td className="p-2 font-bold text-white font-sans">{op.driver_name}</td>
                    <td className="p-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        op.strategy_intent === 'UNDERCUT_THREAT' ? 'bg-red-500/20 text-red-400' :
                        op.strategy_intent === 'BOX_IMMINENT' ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {op.strategy_intent}
                      </span>
                    </td>
                    <td className="p-2">{(op.pit_next_2_laps_prob * 100).toFixed(0)}%</td>
                    <td className="p-2">{(op.attack_probability * 100).toFixed(0)}%</td>
                    <td className="p-2 font-mono text-slate-300">{op.expected_pace_delta_s > 0 ? `+${op.expected_pace_delta_s.toFixed(2)}s` : `${op.expected_pace_delta_s.toFixed(2)}s`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
